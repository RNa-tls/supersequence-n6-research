#!/usr/bin/env python3
"""Round N (section 6) -- the ZERO-EXCESS graph G0 at the level of chain ENTRY NODES.

Chain identity (rN report section 1):  J - 48 = sum_{non-F transitions} (w - 3) + (q - 768),
q = number of word chains.  A family chain K is traversed as one word chain iff it is entered at a
node (K, i) and left at its exit: for a FULL chain (closed F-cycle of 7 runs) any i = 1..7, exit
K_{i-1} (cyclic); for a SHORT chain only i = 1, exit = its last run.  G0 = arcs (K,i) -> (K',i') with
w(exit(K,i), K'_{i'}) = 3.  Reports: G0 arc classes, zero-cost intra-trail reachability from every
entry node (longest zero-cost path inside the trail, by DFS over chains), and whether a zero-cost
Hamiltonian path of the whole trail starts at a non-standard entry.
usage: g0_chain.py FAMILY.json [VERS]"""
import sys, os, json, time
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from famstruct import Fam

def build(fm):
    nodes = []; nid = {}
    for c, ch in enumerate(fm.chains):
        L = len(ch["runs"])
        for i in (range(1, 8) if ch["full"] else [1]):
            nid[(c, i)] = len(nodes); nodes.append((c, i))
    def exit_run(c, i):
        ch = fm.chains[c]
        if ch["full"]: return ch["runs"][(i - 2) % 7]
        return ch["runs"][-1]
    entry_node = {}
    for (c, i), k in nid.items(): entry_node[fm.chains[c]["runs"][i - 1]] = k
    adj = [[] for _ in nodes]
    for k, (c, i) in enumerate(nodes):
        x = exit_run(c, i)
        for r in fm.succ_w(x, 3):
            j = entry_node.get(r)
            if j is not None and nodes[j][0] != c: adj[k].append(j)
    return nodes, nid, adj, exit_run

def main():
    vers = [int(ch) for ch in sys.argv[2]] if len(sys.argv) > 2 else None
    fm = Fam(sys.argv[1], vers); t0 = time.time()
    nodes, nid, adj, exit_run = build(fm)
    trail = lambda k: fm.chains[nodes[k][0]]["trail"]
    cls = Counter()
    for k in range(len(nodes)):
        for j in adj[k]:
            same = trail(k) == trail(j)
            std = nodes[k][1] == 1 and nodes[j][1] == 1
            cls[("intra" if same else "inter") + ("-std" if std else "-rot")] += 1
    print(json.dumps(dict(nodes=len(nodes), g0_arcs=sum(map(len, adj)), classes=dict(cls))), flush=True)
    # zero-cost intra-trail paths: DFS over chains of the trail (each chain once), longest path from each node
    res = {}
    for t in range(fm.T):
        tn = [k for k in range(len(nodes)) if trail(k) == t]
        nch = len(fm.trail_chains[t])
        best_from = {}
        ham_nonstd = []
        sys.setrecursionlimit(100000)
        for s in tn:
            # iterative DFS with chain-used set; cap the work
            best = 0; stack = [(s, frozenset([nodes[s][0]]), 1)]; steps = 0; ham = False
            while stack and steps < 200000:
                k, used, ln = stack.pop(); steps += 1
                if ln > best: best = ln
                if ln == nch: ham = True
                for j in adj[k]:
                    if trail(j) != t or nodes[j][0] in used: continue
                    stack.append((j, used | {nodes[j][0]}, ln + 1))
            best_from[s] = (best, ham, steps)
            if ham and nodes[s][1] != 1: ham_nonstd.append(nodes[s])
        hist = Counter((nodes[s][1] if fm.chains[nodes[s][0]]["full"] else 0, best_from[s][0]) for s in tn)
        res[t] = dict(chains=nch, ham_from_nonstd=len(ham_nonstd), capped=sum(1 for s in tn if best_from[s][2] >= 200000),
                      longest_from_pos=dict(sorted(((str(p), max(b for (pp, b) in hist if pp == p)) for (p, _) in hist))))
        print(json.dumps(dict(trail=t, **res[t])), flush=True)
    print(json.dumps(dict(sec=round(time.time() - t0, 1))))

if __name__ == "__main__":
    main()
