#!/usr/bin/env python3
"""Neighbourhood repair with the exact S-cut hypertree solver (htcut) for kernel extensions of the
verified 5906 structure.  Blocks of the base forest at incidence distance > d from the conflict set
(blocks no longer candidates or touching newly visible classes) are fixed to 1; everything else free.
Fixing only restricts the search: COMPLETION found is a genuine completion (independently checked);
INFEASIBLE under fixing proves nothing about the kernel (reported as such)."""
import sys, os, json, time
from collections import deque
from ortools.sat.python import cp_model
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import lns5905 as L
from candcore import analyse
from hypertree import hyperedges, is_spanning_tree
from htcut import comp_cuts
from flowsat import verify

W, n = L.W, L.n


def run(rows, d, tl, workers=4):
    A = analyse(W, rows); U = A["U"]; H = hyperedges(W, A)
    P = len(U) // (n - 2); cand = sorted(H)
    vis_new = set(range(W.C)) - set(U)
    conflict = {b for b in L.pay0 if b not in H or any(c in vis_new for c in W.bcls[b])}
    byc = {}
    for b in L.pay0:
        for c in W.bcls[b]: byc.setdefault(c, []).append(b)
    dist = {b: 0 for b in conflict}; q = deque(conflict)
    while q:
        b = q.popleft()
        if dist[b] >= d: continue
        for c in W.bcls[b]:
            for b2 in byc.get(c, []):
                if b2 not in dist: dist[b2] = dist[b] + 1; q.append(b2)
    fixed = [b for b in L.pay0 if b not in dist and b in H]
    byv = {}
    for b in cand:
        for v in H[b]: byv.setdefault(v, []).append(b)
    m = cp_model.CpModel()
    x = {b: m.NewBoolVar("") for b in cand}
    m.Add(sum(x.values()) == P)
    for u in U: m.AddBoolOr([x[b] for b in byv.get(u, [])])
    pairs = set()
    for v, bl in byv.items():
        for i in range(len(bl)):
            for j in range(i + 1, len(bl)):
                b1, b2 = sorted((bl[i], bl[j]))
                if (b1, b2) not in pairs and len(H[b1] & H[b2]) >= 2: pairs.add((b1, b2)); m.Add(x[b1] + x[b2] <= 1)
    for b in fixed: m.Add(x[b] == 1)
    t0 = time.time(); it = 0; seen = set()
    while time.time() - t0 < tl:
        it += 1
        sv = cp_model.CpSolver(); sv.parameters.num_workers = workers
        sv.parameters.max_time_in_seconds = max(1, tl - (time.time() - t0))
        st = sv.Solve(m)
        if st == cp_model.INFEASIBLE: return "INFEASIBLE_UNDER_FIXING", None, dict(fixed=len(fixed), it=it)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return "UNKNOWN", None, dict(fixed=len(fixed), it=it)
        X = [b for b in cand if sv.Value(x[b])]
        new = [S for S in comp_cuts(H, X, n) if S not in seen]
        if not new:
            ok, why = is_spanning_tree(H, X, U)
            return ("COMPLETION" if ok else "BUG"), X, dict(fixed=len(fixed), it=it, sec=round(time.time() - t0, 1))
        for S in new:
            seen.add(S); m.Add(sum(x[b] for b in cand if H[b] <= S) <= (len(S) - 1) // (n - 2))
        m.ClearHints()
        for b in cand: m.AddHint(x[b], 1 if b in X else 0)
    return "UNKNOWN_TIME", None, dict(fixed=len(fixed), it=it)


if __name__ == "__main__":
    tl = float(sys.argv[1]); ds = [int(a) for a in sys.argv[2].split(",")]
    exts = L.extensions()
    for e in exts:
        rows = L.build_rows(e)
        for d in ds:
            t0 = time.time(); st, X, info = run(rows, d, tl)
            line = dict(ext=(e[0], [y if isinstance(y, int) else y[1] for y in e[1]]), d=d, status=st,
                        sec=round(time.time() - t0, 1), **info)
            if X:
                ok, why = verify(W, rows, X, n); line.update(forest_check=ok)
                k = len(rows); G = sum(n - 1 - r[1] for r in rows)
                json.dump(dict(n=n, score=k - G, rows=[[list(r[0]), r[1], list(r[2])] for r in rows], payload=X),
                          open(os.path.join(HERE, "..", "certs", "candidate_5905_completion.json"), "w"))
            print(json.dumps(line), flush=True)
            if X or st == "UNKNOWN_TIME": break
        if X: break
