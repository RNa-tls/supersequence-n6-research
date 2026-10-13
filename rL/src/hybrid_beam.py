#!/usr/bin/env python3
"""Round L -- beam search for the hybrid relinking GTSP (heuristic: finds routes, proves nothing).

Same model as hybrid_relink.py: clusters = closed trails of the input word's chain set, node = cut
edge (entry perm; exit = its predecessor in the cyclic sequence), boundary arc weight w; the cost of
entering node b after node a is w(exit(a), entry(b)) - cut(b).  L = const + sum costs - cut(first).
Arcs with excess w - cut - 1 <= EXC only.  Beam over partial paths (set of visited clusters, last
node), keeping the BEAM cheapest per depth; every complete path is rebuilt and measured.
usage: hybrid_beam.py WORD [EXC] [BEAM] [--both]"""
import sys, os, json, time, itertools
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hybrid_relink as H

def main():
    path = sys.argv[1]; EXC = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    BEAM = int(sys.argv[3]) if len(sys.argv) > 3 else 20000
    BOTH = "--both" in sys.argv
    t0 = time.time()
    seqs, L0, K, alt = H.closed_trails(path)
    T = len(seqs)
    const = 8 + sum(9 * (len(s) // 8) for s in seqs) + K
    nodes = []; nid = {}; versions = []
    for ti, s in enumerate(seqs):
        vs = [s] + ([alt[ti]] if BOTH and alt[ti] is not None else [])
        for s_ in vs:
            vi = len(versions); versions.append((ti, s_))
            for i in range(len(s_)):
                nid.setdefault(s_[i], []).append(len(nodes))
                nodes.append((ti, s_[i], s_[i - 1], H.wt(s_[i - 1], s_[i]), vi, i))
    succ = defaultdict(list)
    for a, (ta, entry, exitp, ca, va, ia) in enumerate(nodes):
        u = exitp
        for w_ in range(2, 5 + EXC):
            for perm in itertools.permutations(u[:w_]):
                v = u[w_:] + perm
                if H.wt(u, v) != w_: continue
                for b in nid.get(v, []):
                    if nodes[b][0] == ta: continue
                    c = w_ - nodes[b][3]
                    if c - 1 <= EXC: succ[a].append((c, b))
    for a in succ: succ[a].sort()
    print(json.dumps(dict(nodes=len(nodes), arcs=sum(len(v) for v in succ.values()), build_sec=round(time.time() - t0, 1))), flush=True)
    # beam: state = (cost, last node, visited mask, path tuple)
    beam = [(-nodes[a][3], a, 1 << nodes[a][0], (a,)) for a in range(len(nodes)) if succ[a]]
    beam.sort(); beam = beam[:BEAM * 4]
    best = None
    for depth in range(1, T):
        nxt = {}
        for cost, a, mask, pth in beam:
            for c, b in succ[a]:
                tb = nodes[b][0]
                if mask >> tb & 1: continue
                key = (b, mask | (1 << tb))
                nc = cost + c
                if key not in nxt or nxt[key][0] > nc: nxt[key] = (nc, b, mask | (1 << tb), pth + (b,))
        beam = sorted(nxt.values())[:BEAM]
        if not beam: break
        print(json.dumps(dict(depth=depth + 1, states=len(nxt), best_cost=beam[0][0], L_lower_if_ideal_rest=const + beam[0][0] + (T - depth - 1),
                              sec=round(time.time() - t0, 1))), flush=True)
    full = [st for st in beam if bin(st[2]).count("1") == T]
    if not full: print(json.dumps(dict(result="no complete path in beam"))); return
    cost, a, mask, pth = full[0]
    route = []
    for j in pth:
        ti, entry, exitp, c, vi, i0 = nodes[j]
        s_ = versions[vi][1]; route += s_[i0:] + s_[:i0]
    assert len(route) == 40320 and len(set(route)) == 40320
    Lm = 8 + sum(H.wt(route[i], route[i + 1]) for i in range(len(route) - 1))
    cuts = {str(k): sum(1 for j in pth if nodes[j][3] == k) for k in (1, 2, 3)}
    res = dict(predicted=const + cost, measured=Lm, cut_weights=cuts, exc=EXC, beam=BEAM, both=BOTH, sec=round(time.time() - t0, 1))
    if Lm <= 46186:
        word = list(route[0])
        for p_, q_ in zip(route, route[1:]):
            c = H.wt(p_, q_); word += list(q_[8 - c:])
        tag = os.path.basename(path).replace("superperm8_", "").replace(".txt", "")
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"hybrid_beam_{Lm}_from_{tag}_exc{EXC}_beam{BEAM}{'_both' if BOTH else ''}.txt")
        open(out, "w").write("".join(str(c + 1) for c in word) + "\n"); res["file"] = out
    print(json.dumps(res), flush=True)

if __name__ == "__main__":
    main()
