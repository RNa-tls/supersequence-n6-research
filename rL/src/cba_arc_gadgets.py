#!/usr/bin/env python3
"""Round L (section 25) -- multi-arc hole gadgets built from the CBA splits of an r = 0 word.

Facts used (checked by split_gadgets.py / this script): in the 46187-type words the only splits whose
kept part saves length in place are the 'CBA splits': run i (start s) followed by a CBA join keeps
only s (w(s, next) = 2) and frees the 7-arc B_i = R s .. R^7 s; in-place change -1, internal -1,
so every freed arc carries -2 and must be re-inserted.  A slot is a join x -> y (weight c) of the
route, or the new join s_i -> next of a split class.  Inserting a path of m freed arcs into a slot
changes the length by  w(x,B1) + sum w(B_t end, B_t+1 start) + w(Bm end, y) - c - 2m.
This script enumerates every slot with every path of m <= 3 distinct arcs (exhaustive, with an exact
lower-bound prune) and reports the best total change per m.  A negative value would be a shorter word;
any candidate is rebuilt and measured from scratch.
usage: cba_arc_gadgets.py WORD [MMAX]"""
import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import split_gadgets as G

def main():
    path = sys.argv[1]; MMAX = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    t0 = time.time()
    w = G.load(path); S = G.runs_of(w); M = len(S); n = 8; L0 = len(w)
    E = [G.R(s, 7) for s in S]
    J = [G.wt(E[i], S[i + 1]) for i in range(M - 1)]
    cba = [i for i in range(1, M - 1) if G.wt(S[i], S[i + 1]) == 2 and J[i] == 3]
    arcs = [(G.R(S[i], 1), G.R(S[i], 7)) for i in cba]          # (start perm, end perm)
    A = len(arcs)
    slots = [(E[j], S[j + 1], J[j], ("join", j)) for j in range(M - 1)]
    # (slots on the new joins s_i -> next of split classes need a coupled move; not included here)
    W12 = np.array([[G.wt(arcs[u][1], arcs[v][0]) if u != v else 99 for v in range(A)] for u in range(A)])
    best = {m: (None, 10**9) for m in range(1, MMAX + 1)}
    cnt = {m: 0 for m in range(1, MMAX + 1)}
    for (x, y, c, tag) in slots:
        wx = np.array([G.wt(x, arcs[u][0]) for u in range(A)])
        wy = np.array([G.wt(arcs[u][1], y) for u in range(A)])
        own = None
        if tag[0] == "join":
            j = tag[1]
            # arcs from the two runs touching this join cannot be inserted here (they are its endpoints)
            own = {k for k, i in enumerate(cba) if i in (j, j + 1)}
        else:
            own = {k for k, i in enumerate(cba) if i == tag[1]}
        ok = [u for u in range(A) if u not in own]
        # m = 1
        for u in ok:
            d = wx[u] + wy[u] - c - 2; cnt[1] += 1
            if d < best[1][1]: best[1] = ((tag, [cba[u]]), int(d))
        if MMAX >= 2:
            for u in ok:
                for v in ok:
                    if u == v: continue
                    d = wx[u] + W12[u, v] + wy[v] - c - 4; cnt[2] += 1
                    if d < best[2][1]: best[2] = ((tag, [cba[u], cba[v]]), int(d))
        if MMAX >= 3:
            lb_first = min(wx[u] for u in ok) if ok else 99
            for u in ok:
                for v in ok:
                    if v == u: continue
                    part = wx[u] + W12[u, v]
                    if part + 4 - c - 6 >= best[3][1]: continue
                    for z in ok:
                        if z in (u, v): continue
                        d = part + W12[v, z] + wy[z] - c - 6; cnt[3] += 1
                        if d < best[3][1]: best[3] = ((tag, [cba[u], cba[v], cba[z]]), int(d))
    # independent verification of the best candidate of each m by rebuilding the route
    ver = {}
    for m, (g, d) in best.items():
        if g is None: continue
        tag, cls = g
        runs = []
        split = set(cls)
        ins_after = None
        for t in range(M):
            if t in split: runs.append([S[t]])
            else: runs.append([G.R(S[t], k) for k in range(n)])
            if tag[0] == "join" and t == tag[1]:
                for i in cls: runs.append([G.R(S[i], k) for k in range(1, n)])
            if tag[0] == "cba" and t == tag[1]:
                for i in cls: runs.append([G.R(S[i], k) for k in range(1, n)])
        route = [p for r in runs for p in r]
        assert len(route) == 40320 and len(set(route)) == 40320
        ver[m] = dict(predicted=L0 + d, measured=G.route_len(route), slot=list(tag), classes=cls)
    print(json.dumps(dict(file=os.path.basename(path), L=L0, cba_splits=A, slots=len(slots),
                          evaluated=cnt, best={m: v for m, v in ver.items()}, sec=round(time.time() - t0, 1))))

if __name__ == "__main__":
    main()
