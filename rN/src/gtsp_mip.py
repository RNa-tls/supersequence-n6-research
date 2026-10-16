#!/usr/bin/env python3
"""Round N -- exact MIP for PATH COVERS of a subset of trails in the single-opening option model.

Each selected trail picks one option o (entry, exit, cut); a cover by exactly C directed paths;
arc o -> o' (different trails) costs e = w(exit(o), entry(o')) - cut(o') - 1 >= 0 when e <= EMAX
(enumerated exactly), otherwise a trail-level 'else' arc of cost EMAX + 1 (a LOWER bound on the
true e).  Path starts cost START_COST * [cut = 2] (the [c0 = 2] term, only for C = 1 words).
Subtours: Gavish-Graves single-commodity flow at trail level (exact).
Returns optimum (exact as a lower bound of the true model; equal to it when the optimal solution
uses no else arc with true e > EMAX + 1, which is checked)."""
import sys, os, json, time, itertools
from collections import defaultdict
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import options as OP

def excess_arcs(opts, ids, emax):
    """all (a, b, e) with a, b in ids (different trails) and e <= emax"""
    tr = np.array([opts[i]["t"] for i in ids])
    W = OP.weight_block([opts[i]["exit"] for i in ids], [opts[j]["entry"] for j in ids]).astype(np.int16)
    cut = np.array([opts[j]["cut"] for j in ids], np.int16)
    E = W - cut[None, :] - 1
    E[tr[:, None] == tr[None, :]] = 99
    a, b = np.nonzero(E <= emax)
    return [(ids[i], ids[j], int(E[i, j])) for i, j in zip(a, b)], E

def solve(opts, trails, emax=2, C=1, start_cost=1.0, time_limit=600, threads=4, verbose=False, cutoff=None, extra=None, relax=False, solver=None, crossover=False, start_costs=None, end_costs=None, free_starts=0, free_ends=0, free_start_fcut=1.0, no_subtour=False):
    import highspy
    tset = sorted(trails); T = len(tset); tpos = {t: i for i, t in enumerate(tset)}
    ids = [i for i, o in enumerate(opts) if o["t"] in tpos]
    arcs, E = excess_arcs(opts, ids, emax)
    NO = len(ids); oi = {o: k for k, o in enumerate(ids)}; NA = len(arcs)
    pairs = [(i, j) for i in range(T) for j in range(T) if i != j]; NF = len(pairs)
    cy = 0; cz = cy + NO; ch = cz + NA; cr = ch + NO; cs = cr + NO; ct = cs + NO; cf = ct + NO; cx = cf + NF; cg = cx + NF; cgd = cg + NF; cs2 = cgd + T; ct2 = cs2 + NO; ncol = ct2 + NO
    cost = np.zeros(ncol)
    for k, (a, b, e) in enumerate(arcs): cost[cz + k] = e
    for k, o in enumerate(ids): cost[cs + k] = start_cost * (3 - opts[o]["cut"])
    if start_costs is not None:
        for k, o in enumerate(ids): cost[cs + k] += start_costs.get(o, 0.0)
    if end_costs is not None:
        for k, o in enumerate(ids): cost[ct + k] += end_costs.get(o, 0.0)
    for k, o in enumerate(ids): cost[cs2 + k] = free_start_fcut * (3 - opts[o]["cut"])
    cost[cf:cf + NF] = emax + 1
    lower = np.zeros(ncol); upper = np.ones(ncol); upper[cg:cg + NF] = T; upper[cgd:cgd + T] = T
    integ = np.zeros(ncol, dtype=bool); integ[cy:cy + NO] = True; integ[cz:cz + NA] = True; integ[cf:cf + NF] = True; integ[cx:cx + NF] = True
    integ[cs:cs + NO] = True; integ[ct:ct + NO] = True; integ[cs2:cs2 + NO] = True; integ[ct2:ct2 + NO] = True
    rows = []
    to = defaultdict(list)
    for k, o in enumerate(ids): to[tpos[opts[o]["t"]]].append(k)
    outa = defaultdict(list); ina = defaultdict(list)
    for k, (a, b, e) in enumerate(arcs): outa[oi[a]].append(cz + k); ina[oi[b]].append(cz + k)
    for t in range(T): rows.append(([cy + k for k in to[t]], [1.0] * len(to[t]), 1.0, 1.0))
    for k in range(NO):
        idx = outa[k] + [ch + k, ct + k, ct2 + k]; rows.append((idx + [cy + k], [1.0] * len(idx) + [-1.0], 0.0, 0.0))
        idx = ina[k] + [cr + k, cs + k, cs2 + k]; rows.append((idx + [cy + k], [1.0] * len(idx) + [-1.0], 0.0, 0.0))
    fidx = {p: cf + i for i, p in enumerate(pairs)}; xidx = {p: cx + i for i, p in enumerate(pairs)}; gidx = {p: cg + i for i, p in enumerate(pairs)}
    for t in range(T):
        rows.append(([ch + k for k in to[t]] + [fidx[(t, u)] for u in range(T) if u != t], [1.0] * len(to[t]) + [-1.0] * (T - 1), 0.0, 0.0))
        rows.append(([cr + k for k in to[t]] + [fidx[(u, t)] for u in range(T) if u != t], [1.0] * len(to[t]) + [-1.0] * (T - 1), 0.0, 0.0))
    rows.append(([cs + k for k in range(NO)] + [cs2 + k for k in range(NO)], [1.0] * (2 * NO), float(C), float(C)))
    rows.append(([ct + k for k in range(NO)] + [ct2 + k for k in range(NO)], [1.0] * (2 * NO), float(C), float(C)))
    rows.append(([cs2 + k for k in range(NO)], [1.0] * NO, float(free_starts), float(free_starts)))
    rows.append(([ct2 + k for k in range(NO)], [1.0] * NO, float(free_ends), float(free_ends)))
    bypair = defaultdict(list)
    for k, (a, b, e) in enumerate(arcs): bypair[(tpos[opts[a]["t"]], tpos[opts[b]["t"]])].append(cz + k)
    for p in pairs:
        idx = bypair[p] + [fidx[p], xidx[p]]; rows.append((idx, [1.0] * (len(idx) - 1) + [-1.0], 0.0, 0.0))
    # GG flow: depot sends T units into path starts; each trail consumes one
    for t in (range(T) if not no_subtour else []):
        idx = [gidx[(u, t)] for u in range(T) if u != t] + [cgd + t] + [gidx[(t, u)] for u in range(T) if u != t]
        rows.append((idx, [1.0] * (T - 1) + [1.0] + [-1.0] * (T - 1), 1.0, 1.0))
        rows.append(([cgd + t] + [cs + k for k in to[t]] + [cs2 + k for k in to[t]], [1.0] + [-float(T)] * (2 * len(to[t])), -highspy.kHighsInf, 0.0))
    if not no_subtour:
        rows.append(([cgd + t for t in range(T)], [1.0] * T, float(T), float(T)))
        for p in pairs: rows.append(([gidx[p], xidx[p]], [1.0, -(T - 1.0)], -highspy.kHighsInf, 0.0))
    if extra: rows += extra(dict(ids=ids, oi=oi, arcs=arcs, cz=cz, cy=cy, cs=cs, ct=ct, tpos=tpos, to=to, fidx=fidx, tset=tset, emax=emax, opts=opts))
    h = highspy.Highs(); h.setOptionValue("output_flag", verbose); h.setOptionValue("mip_rel_gap", 0.0)
    h.setOptionValue("threads", threads); h.setOptionValue("time_limit", float(time_limit))
    if cutoff is not None: h.setOptionValue("objective_bound", float(cutoff))
    if solver: h.setOptionValue("solver", solver)
    if relax and solver == "ipm" and not crossover: h.setOptionValue("run_crossover", "off")
    lp = highspy.HighsLp(); lp.num_col_ = ncol; lp.num_row_ = len(rows)
    lp.col_cost_ = cost; lp.col_lower_ = lower; lp.col_upper_ = upper
    lp.row_lower_ = np.array([r[2] for r in rows]); lp.row_upper_ = np.array([r[3] for r in rows])
    st = [0]; ix = []; vl = []
    for r in rows: ix += r[0]; vl += r[1]; st.append(len(ix))
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.start_ = np.array(st, dtype=np.int32); lp.a_matrix_.index_ = np.array(ix, dtype=np.int32); lp.a_matrix_.value_ = np.array(vl)
    if not relax: lp.integrality_ = [highspy.HighsVarType.kInteger if integ[c] else highspy.HighsVarType.kContinuous for c in range(ncol)]
    h.passModel(lp); t0 = time.time(); h.run()
    info = h.getInfo(); status = h.modelStatusToString(h.getModelStatus())
    sol = np.array(h.getSolution().col_value) if info.primal_solution_status else None
    out = dict(trails=T, options=NO, arcs=NA, C=C, emax=emax, status=status, obj=info.objective_function_value if sol is not None else None,
               bound=info.mip_dual_bound, sec=round(time.time() - t0, 1))
    if relax and sol is not None:
        hs = h.getSolution()
        out.update(_sol=sol, _arcs=arcs, _ids=ids, _fidx=fidx, _tset=tset, _cols=dict(cy=cy, cz=cz, ch=ch, cr=cr, cs=cs, ct=ct, cf=cf, cx=cx, cg=cg, cgd=cgd),
                   _col_dual=np.array(hs.col_dual), _row_dual=np.array(hs.row_dual), _rows=rows, _cost=cost, _ncol=ncol)
    if sol is not None and not relax:
        chosen = {opts[ids[k]]["t"]: ids[k] for k in range(NO) if sol[cy + k] > 0.5}
        succ = {}
        for k, (a, b, e) in enumerate(arcs):
            if sol[cz + k] > 0.5: succ[opts[a]["t"]] = (opts[b]["t"], e)
        for (i, j), c in fidx.items():
            if sol[c] > 0.5:
                a = chosen[tset[i]]; b = chosen[tset[j]]
                succ[tset[i]] = (tset[j], int(E[ids.index(a), ids.index(b)]))
        starts = [opts[ids[k]]["t"] for k in range(NO) if sol[cs + k] > 0.5 or sol[cs2 + k] > 0.5]
        paths = []
        for s in starts:
            p = [s]
            while p[-1] in succ: p.append(succ[p[-1]][0])
            paths.append(p)
        true_cost = sum(e for (_, e) in succ.values()) + sum(start_cost * (3 - opts[chosen[s]]["cut"]) for s in starts)
        out["endpoints"] = dict(starts=[int(ids[k]) for k in range(NO) if sol[cs + k] > 0.5], free_starts=[int(ids[k]) for k in range(NO) if sol[cs2 + k] > 0.5],
                                ends=[int(ids[k]) for k in range(NO) if sol[ct + k] > 0.5], free_ends=[int(ids[k]) for k in range(NO) if sol[ct2 + k] > 0.5])
        out.update(paths=paths, true_cost=true_cost, chosen={int(t): (opts[o]["v"], opts[o]["k"]) for t, o in chosen.items()})
    return out
