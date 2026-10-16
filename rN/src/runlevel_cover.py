#!/usr/bin/env python3
"""Round N -- EXACT run-level path covers of a set of trails of the family (ALL opening patterns:
any number of pieces per trail, rotations, wrap-around F-steps, alternative w = 3 joins), with a
free version per trail (all runs of a trail use the same version).

Cost of a path cover with C paths = sum over its transitions of (w - 2)  (the run-level J terms).
Equivalently, in chain units: cost = sum_{non-F} (w - 3) + (q - #family chains) + (#family chains - C).
Arcs with w <= WMAX are enumerated; all other transitions are represented by one aggregated
'else' arc per ordered TRAIL pair with cost WMAX + 1 - 2 (a lower bound), so the optimum is a valid
LOWER bound, and exact when the solution's else arcs have true w = WMAX + 1 (reported).
Subtours: Gavish-Graves flow over the run-copy graph (exact)."""
import sys, os, json, time
from collections import defaultdict
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import options as OP

def last(p): return p[-1:] + p[:-1]

def build_runs(fam, trails):
    runs = []                                  # (start, trail, version)
    for t in trails:
        for v, s in enumerate(fam["trails"][t]["versions"]):
            for k in range(len(s) // 8):
                runs.append((tuple(int(c) for c in s[8 * k:8 * k + 8]), t, v))
    return runs

def solve_lazy(fam, trails, C=1, wmax=4, time_limit=600, threads=4, verbose=False, max_rounds=200, relax=False, use_else=True):
    """run-level path cover with lazy SECs on run sets.  With use_else, every transition of weight > wmax
    is represented by trail-level aggregated else arcs of cost wmax - 1 (a lower bound), so the optimum is
    a valid LOWER bound for all covers; SECs count every else-out of a set as leaving it (valid, weaker)."""
    import highspy
    runs = build_runs(fam, trails); R = len(runs)
    W = OP.weight_block([last(r[0]) for r in runs], [r[0] for r in runs]).astype(np.int16)
    tr = np.array([r[1] for r in runs]); ve = np.array([r[2] for r in runs])
    ok = (tr[:, None] != tr[None, :]) | (ve[:, None] == ve[None, :]); np.fill_diagonal(ok, False)
    a, b = np.nonzero((W <= wmax) & ok); arcs = list(zip(a.tolist(), b.tolist())); NA = len(arcs)
    tl = sorted(set(trails)); T = len(tl); tp = {t: i for i, t in enumerate(tl)}
    tpairs = [(i, j) for i in range(T) for j in range(T) if i != j] if use_else else []
    NE = len(tpairs)
    cx = 0; cs = NA; ct = cs + R; cu = ct + R; ch = cu + 2 * T; cr = ch + R; ce = cr + R; ncol = ce + NE
    if not use_else: ncol = ch
    cost = np.zeros(ncol)
    for k, (i, j) in enumerate(arcs): cost[cx + k] = W[i, j] - 2
    if use_else: cost[ce:ce + NE] = wmax + 1 - 2
    rows = []
    outa = defaultdict(list); ina = defaultdict(list)
    for k, (i, j) in enumerate(arcs): outa[i].append(k); ina[j].append(k)
    for i in range(R):
        u = cu + 2 * tp[runs[i][1]] + runs[i][2]
        ex_o = [ch + i] if use_else else []; ex_i = [cr + i] if use_else else []
        rows.append(([cx + k for k in outa[i]] + [ct + i] + ex_o + [u], [1.0] * (len(outa[i]) + 1 + len(ex_o)) + [-1.0], 0.0, 0.0))
        rows.append(([cx + k for k in ina[i]] + [cs + i] + ex_i + [u], [1.0] * (len(ina[i]) + 1 + len(ex_i)) + [-1.0], 0.0, 0.0))
    for t in range(T): rows.append(([cu + 2 * t, cu + 2 * t + 1], [1.0, 1.0], 1.0, 1.0))
    if use_else:
        eidx = {p: ce + k for k, p in enumerate(tpairs)}
        for t in tl:
            rr = [i for i in range(R) if runs[i][1] == t]
            rows.append(([ch + i for i in rr] + [eidx[(tp[t], tp[u2])] for u2 in tl if u2 != t], [1.0] * len(rr) + [-1.0] * (T - 1), 0.0, 0.0))
            rows.append(([cr + i for i in rr] + [eidx[(tp[u2], tp[t])] for u2 in tl if u2 != t], [1.0] * len(rr) + [-1.0] * (T - 1), 0.0, 0.0))
    rows.append(([cs + i for i in range(R)], [1.0] * R, float(C), float(C)))
    rows.append(([ct + i for i in range(R)], [1.0] * R, float(C), float(C)))
    h = highspy.Highs(); h.setOptionValue("output_flag", verbose); h.setOptionValue("mip_rel_gap", 0.0)
    h.setOptionValue("threads", threads)
    lp = highspy.HighsLp(); lp.num_col_ = ncol; lp.num_row_ = len(rows)
    lp.col_cost_ = cost; lp.col_lower_ = np.zeros(ncol); lp.col_upper_ = np.ones(ncol)
    lp.row_lower_ = np.array([r[2] for r in rows]); lp.row_upper_ = np.array([r[3] for r in rows])
    st = [0]; ix = []; vl = []
    for r in rows: ix += r[0]; vl += r[1]; st.append(len(ix))
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.start_ = np.array(st, dtype=np.int32); lp.a_matrix_.index_ = np.array(ix, dtype=np.int32); lp.a_matrix_.value_ = np.array(vl)
    if not relax: lp.integrality_ = [highspy.HighsVarType.kInteger] * ncol
    h.passModel(lp)
    # initial SECs: every F-cycle (7 runs of one version) and every trail-version run set
    def add_sec(S):
        Sset = set(S); idx = [cx + k for k, (i, j) in enumerate(arcs) if i in Sset and j not in Sset] + [ct + i for i in S] + ([ch + i for i in S] if use_else else [])
        h.addRow(1.0, highspy.kHighsInf, len(idx), np.array(idx, dtype=np.int32), np.ones(len(idx)))
    def add_sec_v(S, u):      # sum out + ends >= u_{T,v}   (S = run set of one trail-version or subset)
        Sset = set(S); idx = [cx + k for k, (i, j) in enumerate(arcs) if i in Sset and j not in Sset] + [ct + i for i in S] + ([ch + i for i in S] if use_else else [])
        h.addRow(0.0, highspy.kHighsInf, len(idx) + 1, np.array(idx + [u], dtype=np.int32), np.array([1.0] * len(idx) + [-1.0]))
    t0 = time.time(); rounds = 0
    nxt = {}
    for k, (i, j) in enumerate(arcs):
        if W[i, j] == 2: nxt[i] = j
    for i in range(R):                         # F-cycles
        cyc = [i]; j = nxt.get(i)
        while j is not None and j != i and len(cyc) < 8: cyc.append(j); j = nxt.get(j)
        if j == i and min(cyc) == i: add_sec_v(cyc, cu + 2 * tp[runs[i][1]] + runs[i][2])
    for t in tl:
        for v in (0, 1):
            add_sec_v([i for i in range(R) if runs[i][1] == t and runs[i][2] == v], cu + 2 * tp[t] + v)
    while True:
        rounds += 1
        h.setOptionValue("time_limit", max(1.0, time_limit - (time.time() - t0)))
        h.run()
        info = h.getInfo(); status = h.modelStatusToString(h.getModelStatus())
        if not info.primal_solution_status or relax:
            return dict(status=status, obj=info.objective_function_value, bound=info.mip_dual_bound if not relax else None,
                        rounds=rounds, runs=R, arcs=NA, sec=round(time.time() - t0, 1))
        sol = np.array(h.getSolution().col_value)
        succ = {i: j for k, (i, j) in enumerate(arcs) if sol[cx + k] > 0.5}
        nelse = int(round(sum(sol[ce:ce + NE]))) if use_else else 0
        if use_else and nelse:
            # else arcs: resolve to concrete run pairs greedily for cycle detection (any pairing is a valid relaxation)
            outs = [i for i in range(R) if sol[ch + i] > 0.5]; ins = [i for i in range(R) if sol[cr + i] > 0.5]
            pool = defaultdict(list)
            for i in ins: pool[runs[i][1]].append(i)
            for (ti, tj), c in eidx.items():
                m = int(round(sol[c]))
                for _ in range(m):
                    src = [i for i in outs if runs[i][1] == tl[ti] and i not in succ]
                    if src and pool[tl[tj]]: succ[src[0]] = pool[tl[tj]].pop()
        used = [i for i in range(R) if sol[cu + 2 * tp[runs[i][1]] + runs[i][2]] > 0.5]
        starts = [i for i in range(R) if sol[cs + i] > 0.5]
        seen = set()
        for s in starts:
            x = s
            while x is not None and x not in seen: seen.add(x); x = succ.get(x)
        rest = [i for i in used if i not in seen]
        if not rest or status != "Optimal":
            return dict(status=status, obj=info.objective_function_value, bound=info.mip_dual_bound, rounds=rounds, runs=R, arcs=NA, else_arcs=nelse,
                        sec=round(time.time() - t0, 1), weights=dict(sorted({int(w): int(c) for w, c in zip(*np.unique([W[i, j] for i, j in succ.items()], return_counts=True))}.items())))
        left = set(rest); ncyc = 0
        while left:
            x = left.pop(); cyc = [x]; y = succ.get(x)
            while y is not None and y in left: cyc.append(y); left.discard(y); y = succ.get(y)
            add_sec(cyc); ncyc += 1
        if verbose: print(json.dumps(dict(round=rounds, obj=info.objective_function_value, cycles=ncyc)), flush=True)
        if rounds >= max_rounds:
            return dict(status="round limit", obj=info.objective_function_value, rounds=rounds, sec=round(time.time() - t0, 1))
