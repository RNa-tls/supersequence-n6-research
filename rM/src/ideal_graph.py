#!/usr/bin/env python3
"""Round M (sections 5, 8, 18) -- the global endpoint graph of the single-opening model.

Nodes: every opening option o = (trail, version, cut edge) with entry(o), exit(o), cut(o).
Arc o -> o' (different trails) with EXCESS e = w(exit(o), entry(o')) - cut(o') - 1 >= -2.
For a single-opening word with pieces p_0..p_29:  J = 77 + [cut(p_0) = 2] + sum_k e(p_{k-1} -> p_k).
Reported: the number of arcs with e = -2..2 (exact enumeration of all w <= 5 successors), the
out-degree distribution of IDEAL arcs (e <= 0), and the LONGEST chain of ideal arcs through
pairwise different trails (exhaustive DFS; every ideal chain is a path of consistent openings,
since a trail is entered and left at the same option).
usage: ideal_graph.py FAMILY.json [EMAX_FOR_CHAINS]"""
import sys, os, json, itertools, time
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trail_order_exact as TOE

def main():
    fam = json.load(open(sys.argv[1])); EMAX = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    t0 = time.time()
    layers, const = TOE.load_layers(fam)
    nodes = []; by_entry = defaultdict(list)
    for t, L in enumerate(layers):
        for o in L:
            by_entry[o[0]].append(len(nodes)); nodes.append((t,) + o)
    ecount = Counter(); adj = [[] for _ in nodes]
    for a, (t, entry, ex, cut, v, k) in enumerate(nodes):
        for w in range(2, 6):
            for perm in itertools.permutations(ex[:w]):
                y = ex[w:] + perm
                if TOE.wt(ex, y) != w: continue
                for b in by_entry.get(y, []):
                    tb = nodes[b][0]
                    if tb == t: continue
                    e = w - nodes[b][3] - 1
                    ecount[e] += 1
                    if e <= EMAX: adj[a].append(b)
    deg = Counter(len(x) for x in adj)
    # longest chain of e <= EMAX arcs through distinct trails (DFS, exact)
    best = [0, None]; calls = [0]
    sys.setrecursionlimit(10000)
    def dfs(a, used, length, path):
        calls[0] += 1
        if length > best[0]: best[0] = length; best[1] = list(path)
        for b in adj[a]:
            tb = nodes[b][0]
            if used >> tb & 1: continue
            path.append(b); dfs(b, used | (1 << tb), length + 1, path); path.pop()
    for a in range(len(nodes)):
        if adj[a]: dfs(a, 1 << nodes[a][0], 1, [a])
    chain = [dict(trail=nodes[b][0], version=nodes[b][4], edge=nodes[b][5], cut=nodes[b][3]) for b in best[1]] if best[1] else []
    res = dict(nodes=len(nodes), arcs_by_excess=dict(sorted(ecount.items())), emax=EMAX,
               out_degree_hist=dict(sorted(deg.items())), longest_chain_trails=best[0], chain=chain,
               dfs_calls=calls[0], sec=round(time.time() - t0, 1))
    print(json.dumps(res))

if __name__ == "__main__":
    main()
