#!/usr/bin/env python3
"""Short Berge cycles among candidate blocks of the root-contracted hypergraph:
2-cycles: |N(B) & N(B')| >= 2.  3-cycles: B1,B2,B3 with three DISTINCT pairwise shared vertices.
4-cycles: B1..B4 cyclically sharing distinct vertices v12, v23, v34, v41 (non-consecutive pairs may
share anything).  Each yields a valid cut sum x <= |C| - 1.  Statistics for a kernel."""
import sys, os, itertools, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candcore import analyse, kernel_rows
from complete import World
from hypertree import hyperedges

def short_cycles(H, max_len=4):
    cand = sorted(H); byv = {}
    for b in cand:
        for v in H[b]: byv.setdefault(v, []).append(b)
    nb = {b: {} for b in cand}                       # neighbour -> shared vertices
    for v, bl in byv.items():
        for b1 in bl:
            for b2 in bl:
                if b1 != b2: nb[b1].setdefault(b2, set()).add(v)
    two = {frozenset((a, b)) for a in cand for b, sv in nb[a].items() if len(sv) >= 2}
    three = set()
    for a in cand:
        for b in nb[a]:
            if b <= a: continue
            for c in nb[a]:
                if c <= b or c not in nb[b]: continue
                # distinct representatives
                for va in nb[a][b]:
                    ok = False
                    for vb in nb[b][c]:
                        if vb == va: continue
                        for vc in nb[c][a]:
                            if vc != va and vc != vb: ok = True; break
                        if ok: break
                    if ok: three.add(frozenset((a, b, c))); break
    four = set()
    if max_len >= 4:
        for a in cand:
            for b in nb[a]:
                if b <= a: continue
                for c in nb[b]:
                    if c == a or c <= a: continue
                    for d in nb[c]:
                        if d in (a, b) or d <= a or a not in nb[d]: continue
                        S = frozenset((a, b, c, d))
                        if S in four: continue
                        if any(frozenset(p) in two for p in itertools.combinations(S, 2)): continue
                        # need distinct connecting vertices along a-b-c-d-a
                        for v1 in nb[a][b]:
                            done = False
                            for v2 in nb[b][c]:
                                if v2 == v1: continue
                                for v3 in nb[c][d]:
                                    if v3 in (v1, v2): continue
                                    for v4 in nb[d][a]:
                                        if v4 not in (v1, v2, v3): four.add(S); done = True; break
                                    if done: break
                                if done: break
                            if done: break
    return two, three, four

if __name__ == "__main__":
    n = int(sys.argv[1]); W = World(n)
    for spec in sys.argv[2:]:
        A = analyse(W, kernel_rows(n, spec)); H = hyperedges(W, A)
        t0 = time.time(); two, three, four = short_cycles(H)
        print(json.dumps(dict(n=n, kernel=spec[:40], cand=len(H), two=len(two), three=len(three), four=len(four), sec=round(time.time()-t0,1))), flush=True)
