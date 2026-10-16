#!/usr/bin/env python3
"""Round N (sections 13, 17) -- EXACT run-level re-optimisation of a WINDOW of a word.

Given a word of the family and a contiguous window of its pieces, the window's trails are re-solved
as a Hamiltonian path over ALL their runs (both versions per trail, every opening pattern: any number
of pieces, rotations, wrap-around F-steps, alternative joins) between the fixed run before the window
(source) and the fixed run after it (sink).  Objective = sum of (w - 2) over all transitions of the
window including the two connecting ones (the window's exact contribution to J).
Transitions with w > WMAX are represented by trail-level aggregated 'else' arcs of cost WMAX - 1
(a lower bound), so the optimum is a valid LOWER bound on the window cost; a solution that uses no
else arc is a concrete re-routing whose cost is exact (checked by rebuilding the word).
Subtours: lazy run-set SECs (exact).
usage: rl_window.py WORD FAMILY.json [KMAX] [WMAX] [TIME]"""
import sys, os, json, time, math
from collections import defaultdict
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import options as OP

n = 8
def last(p): return p[-1:] + p[:-1]
def wt(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n

def word_runs(path):
    text = "".join(ch for ch in open(path).read() if not ch.isspace())
    al = sorted(set(text)); w = [al.index(c) for c in text]
    seen = set(); route = []
    for i in range(len(w) - n + 1):
        p = tuple(w[i:i + n])
        if len(set(p)) == n and p not in seen: seen.add(p); route.append(p)
    assert len(route) == math.factorial(n)
    return route[0::n]

def family_index(fam):
    where = {}; cyc = {}
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]):
            ss = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]
            cyc[(t, v)] = ss
            for k, p in enumerate(ss): where.setdefault(p, []).append((t, v, k))
    return where, cyc

def pieces_of(st, where, cyc):
    pos = []
    vsel = {}
    for s in st:
        c = where[s]; t = c[0][0]
        vsel.setdefault(t, set(x[1] for x in c)); vsel[t] &= set(x[1] for x in c)
    vsel = {t: min(v) for t, v in vsel.items()}
    for s in st:
        t = where[s][0][0]; k = [x[2] for x in where[s] if x[1] == vsel[t]][0]; pos.append((t, vsel[t], k))
    pcs = []; cur = [0]
    for b in range(1, len(st)):
        (t0, v0, k0), (t1, v1, k1) = pos[b - 1], pos[b]
        if t0 == t1 and k1 == (k0 + 1) % len(cyc[(t0, v0)]): cur.append(b)
        else: pcs.append(cur); cur = [b]
    pcs.append(cur)
    return pos, pcs, vsel

def solve_window(fam, trails, src, snk, wmax=5, time_limit=600, threads=2, verbose=False):
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
    a, b = np.nonzero((W <= wmax) & ok); arcs = list(zip(a.tolist(), b.tolist()))
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
    cost = np.zeros(ncol); cost[cx:cx + NA] = acost; cost[ce:ce + NE] = wmax - 1
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
            res = dict(status=status, obj=info.objective_function_value, bound=info.mip_dual_bound, rounds=rounds, else_arcs=nelse,
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
            return dict(status="no cycle found (else pairing)", obj=info.objective_function_value, bound=info.mip_dual_bound, rounds=rounds,
                        else_arcs=nelse, complete=False, sec=round(time.time() - t0, 1))
        if rounds >= 400 or time.time() - t0 > time_limit:
            return dict(status="round/time limit", obj=info.objective_function_value, bound=info.mip_dual_bound, rounds=rounds,
                        else_arcs=nelse, complete=False, sec=round(time.time() - t0, 1))
        if verbose: print(json.dumps(dict(round=rounds, obj=info.objective_function_value, cycles=ncyc)), flush=True)

def main():
    word, famp = sys.argv[1], sys.argv[2]
    KMAX = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    WMAX = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    TL = float(sys.argv[5]) if len(sys.argv) > 5 else 300
    only_phi = (len(sys.argv) > 6 and sys.argv[6] == "phi")
    with_A = (len(sys.argv) > 6 and sys.argv[6] == "A")
    fam = json.load(open(famp))
    st = word_runs(word); where, cyc = family_index(fam)
    pos, pcs, vsel = pieces_of(st, where, cyc)
    tw = [wt(last(a), b) for a, b in zip(st, st[1:])]
    P = len(pcs)
    print(json.dumps(dict(word=word, pieces=P, J=sum(w - 2 for w in tw) - 719)), flush=True)
    for k in range(1, KMAX + 1):
        for i in range(0, P - k + 1):
            blk = pcs[i:i + k]
            trails = [pos[b[0]][0] for b in blk]
            if len(set(trails)) != k: continue
            if only_phi and any(len(cyc[(t, 0)]) > 42 for t in trails): continue
            if with_A and not any(len(cyc[(t, 0)]) > 42 for t in trails): continue
            lo = blk[0][0]; hi = blk[-1][-1]
            src = st[lo - 1] if lo > 0 else None; snk = st[hi + 1] if hi + 1 < len(st) else None
            cur = sum(w - 2 for w in tw[max(lo - 1, 0):hi + (1 if snk is not None else 0)])
            r = solve_window(fam, trails, src, snk, wmax=WMAX, time_limit=TL)
            out = dict(k=k, i=i, trails=trails, current=cur, opt=r.get("obj"), bound=r.get("bound"), status=r["status"],
                       complete=r.get("complete"), else_arcs=r.get("else_arcs"), sec=r["sec"])
            if r.get("obj") is not None and r["obj"] < cur - 1e-6: out["IMPROVEMENT"] = cur - r["obj"]
            print(json.dumps(out), flush=True)

if __name__ == "__main__":
    main()
