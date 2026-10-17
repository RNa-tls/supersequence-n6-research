#!/usr/bin/env python3
"""Round O (section 18) -- selective refinement of a window MIP.
Same model as rN/src/rl_window.py (run-level Hamiltonian path of the window's trails between the fixed
source and sink runs, all versions, all opening patterns), but the threshold WMAX is per trail PAIR:
transitions t -> u with w <= WM[t, u] are explicit run arcs, larger ones are the trail-level 'else'
lower-bound arc of cost WM[t, u] - 1.  Starting from WM = 5 everywhere, the pairs whose else arcs the
optimum uses are refined (WM += 1) until the optimum is complete (no else arc) or its bound reaches
the current value.  Same-trail jumps keep w <= wmax_same (the Round N model restriction).
usage (repo root): window_refine.py K I TIME_LIMIT_PER_SOLVE TOTAL_CAP OUT.json"""
import sys, os, json, time
import numpy as np
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rN", "src"))
import options as OP
import rl_window as RW
from rl_window import last, wt

def solve_window_pairs(fam, trails, src, snk, WM, wmax_same=5, time_limit=600, threads=2, verbose=False):
    """min sum (w-2) of a path src -> (all runs of trails, versions free) -> snk; src/snk are perms or None"""
    import highspy
    runs = []
    for t in trails:
        for v, s in enumerate(fam["trails"][t]["versions"]):
            for k in range(len(s) // 8): runs.append((tuple(int(c) for c in s[8 * k:8 * k + 8]), t, v))
    R = len(runs)
    tl = sorted(set(trails)); T = len(tl); tp = {t: i for i, t in enumerate(tl)}
    W = OP.weight_block([last(r[0]) for r in runs], [r[0] for r in runs]).astype(np.int16)
    tr = np.array([r[1] for r in runs]); ve = np.array([r[2] for r in runs])
    ok = (tr[:, None] != tr[None, :]) | (ve[:, None] == ve[None, :]); np.fill_diagonal(ok, False)
    tix = np.array([tp[r[1]] for r in runs]); lim = WM[tix[:, None], tix[None, :]].copy(); lim[tr[:, None] == tr[None, :]] = wmax_same
    a, b = np.nonzero((W <= lim) & ok); arcs = list(zip(a.tolist(), b.tolist()))
    acost = [int(W[i, j]) - 2 for i, j in arcs]
    # source / sink arcs (all runs, exact weights; no else needed)
    SRC = R; SNK = R + 1
    if src is not None:
        for i in range(R): arcs.append((SRC, i)); acost.append(wt(last(src), runs[i][0]) - 2)
    if snk is not None:
        for i in range(R): arcs.append((i, SNK)); acost.append(wt(last(runs[i][0]), snk) - 2)
    NA = len(arcs)
    tpairs = [(i, j) for i in range(T) for j in range(T) if i != j]; NE = len(tpairs)
    cx = 0; cs = NA; ct = cs + R; cu = ct + R; ch = cu + 2 * T; cr = ch + R; ce = cr + R; ncol = ce + NE
    cost = np.zeros(ncol); cost[cx:cx + NA] = acost
    for k, (ti, tj) in enumerate(tpairs): cost[ce + k] = WM[ti, tj] - 1
    rows = []
    outa = defaultdict(list); ina = defaultdict(list)
    for k, (i, j) in enumerate(arcs): outa[i].append(k); ina[j].append(k)
    for i in range(R):
        u = cu + 2 * tp[runs[i][1]] + runs[i][2]
        so = [ct + i] if snk is None else []; si = [cs + i] if src is None else []
        rows.append(([cx + k for k in outa[i]] + so + [ch + i, u], [1.0] * (len(outa[i]) + len(so) + 1) + [-1.0], 0.0, 0.0))
        rows.append(([cx + k for k in ina[i]] + si + [cr + i, u], [1.0] * (len(ina[i]) + len(si) + 1) + [-1.0], 0.0, 0.0))
    for t in range(T): rows.append(([cu + 2 * t, cu + 2 * t + 1], [1.0, 1.0], 1.0, 1.0))
    if src is not None: rows.append(([cx + k for k in outa[SRC]], [1.0] * len(outa[SRC]), 1.0, 1.0))
    else: rows.append(([cs + i for i in range(R)], [1.0] * R, 1.0, 1.0))
    if snk is not None: rows.append(([cx + k for k in ina[SNK]], [1.0] * len(ina[SNK]), 1.0, 1.0))
    else: rows.append(([ct + i for i in range(R)], [1.0] * R, 1.0, 1.0))
    eidx = {p: ce + k for k, p in enumerate(tpairs)}
    for t in tl:
        rr = [i for i in range(R) if runs[i][1] == t]
        rows.append(([ch + i for i in rr] + [eidx[(tp[t], tp[u2])] for u2 in tl if u2 != t], [1.0] * len(rr) + [-1.0] * (T - 1), 0.0, 0.0))
        rows.append(([cr + i for i in rr] + [eidx[(tp[u2], tp[t])] for u2 in tl if u2 != t], [1.0] * len(rr) + [-1.0] * (T - 1), 0.0, 0.0))
    h = highspy.Highs(); h.setOptionValue("output_flag", verbose); h.setOptionValue("mip_rel_gap", 0.0); h.setOptionValue("threads", threads)
    lp = highspy.HighsLp(); lp.num_col_ = ncol; lp.num_row_ = len(rows)
    lp.col_cost_ = cost; lp.col_lower_ = np.zeros(ncol); lp.col_upper_ = np.ones(ncol)
    lp.row_lower_ = np.array([r[2] for r in rows]); lp.row_upper_ = np.array([r[3] for r in rows])
    st = [0]; ix = []; vl = []
    for r in rows: ix += r[0]; vl += r[1]; st.append(len(ix))
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.start_ = np.array(st, dtype=np.int32); lp.a_matrix_.index_ = np.array(ix, dtype=np.int32); lp.a_matrix_.value_ = np.array(vl)
    lp.integrality_ = [highspy.HighsVarType.kInteger] * ncol
    h.passModel(lp)
    def add_sec(S, uvar=None):
        Sset = set(S)
        idx = [cx + k for k, (i, j) in enumerate(arcs) if i in Sset and j not in Sset] + [ch + i for i in S] + ([ct + i for i in S] if snk is None else [])
        if uvar is None: h.addRow(1.0, highspy.kHighsInf, len(idx), np.array(idx, dtype=np.int32), np.ones(len(idx)))
        else: h.addRow(0.0, highspy.kHighsInf, len(idx) + 1, np.array(idx + [uvar], dtype=np.int32), np.array([1.0] * len(idx) + [-1.0]))
    nxt = {i: j for (i, j) in arcs if i < R and j < R and W[i, j] == 2}
    for i in range(R):
        cyc = [i]; j = nxt.get(i)
        while j is not None and j != i and len(cyc) < 8: cyc.append(j); j = nxt.get(j)
        if j == i and min(cyc) == i: add_sec(cyc, cu + 2 * tp[runs[i][1]] + runs[i][2])
    for t in tl:
        for v in (0, 1): add_sec([i for i in range(R) if runs[i][1] == t and runs[i][2] == v], cu + 2 * tp[t] + v)
    t0 = time.time(); rounds = 0
    while True:
        rounds += 1
        h.setOptionValue("time_limit", max(1.0, time_limit - (time.time() - t0)))
        h.run()
        info = h.getInfo(); status = h.modelStatusToString(h.getModelStatus())
        if not info.primal_solution_status:
            return dict(status=status, obj=None, bound=info.mip_dual_bound, rounds=rounds, sec=round(time.time() - t0, 1))
        sol = np.array(h.getSolution().col_value)
        succ = {i: j for k, (i, j) in enumerate(arcs) if sol[cx + k] > 0.5}
        nelse = int(round(sol[ce:ce + NE].sum()))
        used = [i for i in range(R) if sol[cu + 2 * tp[runs[i][1]] + runs[i][2]] > 0.5]
        # resolve aggregated else arcs to concrete run pairs (any pairing; only used to find true cycles)
        lnk = dict(succ)
        if nelse:
            outs = [i for i in range(R) if sol[ch + i] > 0.5]; ins = defaultdict(list)
            for i in range(R):
                if sol[cr + i] > 0.5: ins[runs[i][1]].append(i)
            need = defaultdict(int)
            for (ti, tj), c in eidx.items(): need[(tl[ti], tl[tj])] += int(round(sol[c]))
            for i in outs:
                for (ta, tb), m in list(need.items()):
                    if ta == runs[i][1] and m > 0 and ins[tb]:
                        lnk[i] = ins[tb].pop(); need[(ta, tb)] -= 1; break
        start = succ.get(SRC) if src is not None else [i for i in range(R) if sol[cs + i] > 0.5][0]
        path = []; x = start; seen = set()
        while x is not None and x < R and x not in seen:
            path.append(x); seen.add(x); x = lnk.get(x)
        rest = [i for i in used if i not in seen]
        if not rest or status != "Optimal":
            used_pairs = [(tl[ti], tl[tj]) for (ti, tj), c in eidx.items() if sol[c] > 0.5]
            res = dict(status=status, obj=info.objective_function_value, bound=info.mip_dual_bound, rounds=rounds, else_arcs=nelse, used_pairs=used_pairs,
                       complete=(not rest and nelse == 0), sec=round(time.time() - t0, 1))
            if not rest and nelse == 0: res["path"] = [runs[i][0] for i in path]; res["versions"] = {int(runs[i][1]): int(runs[i][2]) for i in path}
            return res
        left = set(rest); ncyc = 0
        while left:
            x = left.pop(); cyc = [x]; y = lnk.get(x)
            while y is not None and y in left: cyc.append(y); left.discard(y); y = lnk.get(y)
            if (y == x or (y is not None and y in cyc)) and all(succ.get(z) == lnk.get(z) for z in cyc):
                add_sec(cyc); ncyc += 1
        if ncyc == 0:
            used_pairs = [(tl[ti], tl[tj]) for (ti, tj), c in eidx.items() if sol[c] > 0.5]
            return dict(status="no cycle found (else pairing)", used_pairs=used_pairs, obj=info.objective_function_value, bound=info.mip_dual_bound, rounds=rounds,
                        else_arcs=nelse, complete=False, sec=round(time.time() - t0, 1))
        if rounds >= 400 or time.time() - t0 > time_limit:
            used_pairs = [(tl[ti], tl[tj]) for (ti, tj), c in eidx.items() if sol[c] > 0.5]
            return dict(status="round/time limit", used_pairs=used_pairs, obj=info.objective_function_value, bound=info.mip_dual_bound, rounds=rounds,
                        else_arcs=nelse, complete=False, sec=round(time.time() - t0, 1))
        if verbose: print(json.dumps(dict(round=rounds, obj=info.objective_function_value, cycles=ncyc)), flush=True)


def main():
    k, i, tl_solve, cap, out = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
    fam = json.load(open("rM/certs/family_46187.json"))
    st = RW.word_runs("rL/records/superperm8_46185.txt"); where, cyc = RW.family_index(fam)
    pos, pcs, vsel = RW.pieces_of(st, where, cyc)
    tw = [wt(last(a), b) for a, b in zip(st, st[1:])]
    blk = pcs[i:i + k]; trails = [pos[b[0]][0] for b in blk]
    lo = blk[0][0]; hi = blk[-1][-1]; src, snk = st[lo - 1], st[hi + 1]
    cur = sum(w - 2 for w in tw[lo - 1:hi + 1])
    tl = sorted(set(trails)); tp = {t: j for j, t in enumerate(tl)}
    WM = np.full((len(tl), len(tl)), 5, int)
    t0 = time.time(); log = []
    while time.time() - t0 < cap:
        r = solve_window_pairs(fam, trails, src, snk, WM, time_limit=tl_solve)
        rec = dict(obj=r.get("obj"), bound=r.get("bound"), status=r["status"], complete=r.get("complete"), else_arcs=r.get("else_arcs"),
                   used_pairs=r.get("used_pairs"), refined=[[int(tl[a]), int(tl[b]), int(WM[a, b])] for a in range(len(tl)) for b in range(len(tl)) if WM[a, b] > 5],
                   sec=r["sec"], t=round(time.time() - t0, 1))
        log.append(rec); print(json.dumps(rec), flush=True)
        if r.get("bound") is not None and r["bound"] >= cur - 1e-6 and r["status"] in ("Optimal", "no cycle found (else pairing)"):
            verdict = "non-improvable (bound = current)"; break
        if r.get("complete") and r.get("obj") is not None:
            verdict = "exact optimum %s" % r["obj"]; break
        up = r.get("used_pairs") or []
        if not up: verdict = "stopped: no else pair to refine (status %s)" % r["status"]; break
        for (a, b) in up: WM[tp[a], tp[b]] = min(8, WM[tp[a], tp[b]] + 1)
    else:
        verdict = "cap reached"
    json.dump(dict(k=k, i=i, trails=trails, current=cur, verdict=verdict, log=log), open(out, "w"), indent=1)
    print(json.dumps(dict(verdict=verdict, current=cur)))


if __name__ == "__main__":
    main()
