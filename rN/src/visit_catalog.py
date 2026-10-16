#!/usr/bin/env python3
"""Round N (sections 4, 5) -- exact SINGLE-VISIT catalog of a trail: for every entry run y and exit
run x of one trail-version, kappa(y, x) = min over Hamiltonian paths of the trail's runs from y to x of
sum (w - 2) minus (k_T - 1)   (= internal cost in chain units: extra word chains + sum_{non-F}(w - 3)).
kappa = 0 exactly for the link openings; single-piece F-step openings have kappa = 1.
All transitions inside the trail are allowed (rotations, wrap-around F-steps, skips, alternative
joins, splits).  Exact MIP with lazy SECs over the run set (all arcs enumerated: no else arcs).
By the trail automorphism group (run shifts d with g(st[k]) = st[k+d]) only orbit representatives of
(y, x) pairs are solved.
usage: visit_catalog.py FAMILY.json TRAIL VERSION OUT.json [KMAX]"""
import sys, os, json, time, itertools
from collections import defaultdict
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import options as OP

n = 8
def last(p): return p[-1:] + p[:-1]

def automorphism_shifts(st):
    m = len(st); idx = {p: k for k, p in enumerate(st)}; shifts = []
    for g in itertools.permutations(range(n)):
        img = tuple(g[x] for x in st[0])
        if img not in idx: continue
        d = idx[img]
        if all(tuple(g[x] for x in st[k]) == st[(k + d) % m] for k in range(m)): shifts.append(d)
    return sorted(set(shifts))

def main():
    import highspy
    fam = json.load(open(sys.argv[1])); t = int(sys.argv[2]); v = int(sys.argv[3]); out = sys.argv[4]
    KMAX = int(sys.argv[5]) if len(sys.argv) > 5 else 99
    s = fam["trails"][t]["versions"][v]
    st = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]
    m = len(st)
    W = OP.weight_block([last(p) for p in st], st).astype(np.int64)
    np.fill_diagonal(W, 99)
    kT = sum(1 for k in range(m) if W[k - 1, k] == 3)
    shifts = automorphism_shifts(st)
    arcs = [(i, j) for i in range(m) for j in range(m) if i != j]
    NA = len(arcs)
    outa = defaultdict(list); ina = defaultdict(list)
    for k, (i, j) in enumerate(arcs): outa[i].append(k); ina[j].append(k)
    def solve(y, x):
        h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("mip_rel_gap", 0.0); h.setOptionValue("threads", 1)
        lp = highspy.HighsLp(); lp.num_col_ = NA
        lp.col_cost_ = np.array([float(W[i, j] - 2) for (i, j) in arcs]); lp.col_lower_ = np.zeros(NA); lp.col_upper_ = np.ones(NA)
        rows = []
        for r in range(m):
            rows.append((outa[r], 0.0 if r == x else 1.0)); rows.append((ina[r], 0.0 if r == y else 1.0))
        lp.num_row_ = len(rows)
        lp.row_lower_ = np.array([b for _, b in rows]); lp.row_upper_ = np.array([b for _, b in rows])
        st_ = [0]; ix = []
        for idx, _ in rows: ix += idx; st_.append(len(ix))
        lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
        lp.a_matrix_.start_ = np.array(st_, dtype=np.int32); lp.a_matrix_.index_ = np.array(ix, dtype=np.int32); lp.a_matrix_.value_ = np.ones(len(ix))
        lp.integrality_ = [highspy.HighsVarType.kInteger] * NA
        h.passModel(lp)
        rounds = 0
        while True:
            rounds += 1
            h.run()
            sol = np.array(h.getSolution().col_value)
            succ = {i: j for k, (i, j) in enumerate(arcs) if sol[k] > 0.5}
            seen = {y}; p = y
            while p in succ: p = succ[p]; seen.add(p)
            if len(seen) == m:
                return int(round(h.getInfo().objective_function_value)), rounds
            left = set(range(m)) - seen
            while left:
                a = left.pop(); cyc = [a]; b = succ.get(a)
                while b is not None and b in left: cyc.append(b); left.discard(b); b = succ.get(b)
                S = set(cyc); idx = [k for k, (i, j) in enumerate(arcs) if i in S and j not in S]
                h.addRow(1.0, highspy.kHighsInf, len(idx), np.array(idx, dtype=np.int32), np.ones(len(idx)))
    t0 = time.time(); table = {}; reps = {}
    for y in range(m):
        for x in range(m):
            if x == y: continue
            key = min(((y + d) % m, (x + d) % m) for d in shifts)
            reps.setdefault(key, []).append((y, x))
    for key in sorted(reps):
        c, r = solve(*key)
        for (y, x) in reps[key]: table[(y, x)] = c - (kT - 1)
    from collections import Counter
    hist = Counter(table.values())
    # single-piece options: link cut at edge k (entry k, exit k-1): kappa 0; F-step: kappa 1
    sp_ok = all(table[(k, (k - 1) % m)] == (0 if W[k - 1, k] == 3 else 1) for k in range(m))
    res = dict(trail=t, version=v, runs=m, k_T=kT, aut_shifts=len(shifts), classes=len(reps), kappa_hist=dict(sorted(hist.items())),
               single_piece_consistent=sp_ok, sec=round(time.time() - t0, 1),
               table={"%d,%d" % k: val for k, val in table.items()})
    json.dump(res, open(out, "w"))
    res.pop("table"); print(json.dumps(res))

if __name__ == "__main__":
    main()
