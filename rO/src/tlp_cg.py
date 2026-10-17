#!/usr/bin/env python3
"""Round O -- TRIPLE-CONSISTENT order LP with column-and-row generation over ALL trail orders.

Model (see tlp.py):  q^b_{a,o,c} (trail b, option o, predecessor a, successor c; a = S first, c = E last),
option arcs y (e <= 2), else links (eout/ein, cost 3), order columns lam_pi.  Rows exist only for
the triples / adjacent pairs of orders already in the pool; an order with new triples brings its rows.

Full dual vector.  Master rows carry the master duals; for a missing triple row the implied dual
    U(a,b,c) = min_{o in b} [ cost(a,o) + DR2(a,o) + DR3(o,c) ]
(the largest value keeping all its q columns at nonnegative reduced cost), missing pair rows get 0.
Then every column group except the orders has nonnegative reduced cost, and the Lagrangian bound is
    L = min( u_conv , min over ALL orders pi of  sum_{consecutive triples abc of pi} U(a,b,c) ) + (tiny corrections),
i.e. F(pi) >= sum_i U(pi_{i-1}, pi_i, pi_{i+1}) for every order, and the minimum over orders is an exact
30-node quadratic (triple-cost) ATSP-path problem solved by MIP (its dual bound is used, so L is valid).
usage: tlp_cg.py FAMILY.json E.npy AUDIT.json SEED_POOL.json OUT.json [max_iter]"""
import sys, os, json, time, random
import numpy as np
import highspy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "rN", "src"))
import options as OP

S, EN = 30, 31
TOL = 1e-7


class TMaster:
    def __init__(self, fam_p, E_p):
        self.fam, self.opts = OP.load(fam_p)
        self.E = np.load(E_p).astype(np.int64)
        self.T = np.array([o["t"] for o in self.opts]); self.cut = np.array([o["cut"] for o in self.opts])
        self.NO = len(self.opts); self.NT = 30
        self.topts = [np.nonzero(self.T == t)[0] for t in range(self.NT)]
        self.startc = (self.cut == 2).astype(float)
        self.tri = {}; self.pairs = {}; self.r2 = {}; self.r3 = {}; self.r4 = {}
        self.pool = []; self.pool_set = set(); self.lam_col = {}
        self.kind = []; self.payload = []
        h = self.h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("threads", 2)
        h.addRow(1.0, 1.0, 0, np.array([], np.int32), np.array([], float))       # R5 convexity
        self.r5 = 0; self.nrow = 1

    def _add_rows(self, n):
        self.h.addRows(n, np.zeros(n), np.zeros(n), 0, np.zeros(n, np.int32), np.array([], np.int32), np.array([], float))
        r0 = self.nrow; self.nrow += n; return r0

    def add_orders(self, orders):
        new_orders = [tuple(int(t) for t in p) for p in orders if tuple(int(t) for t in p) not in self.pool_set]
        if not new_orders: return 0
        new_tri = []; new_pairs = []
        for p in new_orders:
            for i, b in enumerate(p):
                a = p[i - 1] if i else S; c = p[i + 1] if i + 1 < len(p) else EN
                if (a, b, c) not in self.tri and (a, b, c) not in new_tri: new_tri.append((a, b, c))
                if a != S and (a, b) not in self.pairs and (a, b) not in new_pairs: new_pairs.append((a, b))
        # rows
        if new_tri:
            r0 = self._add_rows(len(new_tri))
            for k, t in enumerate(new_tri): self.tri[t] = r0 + k
        for (a, b) in new_pairs:
            nb = len(self.topts[b]); na = len(self.topts[a])
            r0 = self._add_rows(nb + na + 1)
            self.r2[(a, b)] = r0 + np.arange(nb); self.r3[(a, b)] = r0 + nb + np.arange(na); self.r4[(a, b)] = r0 + nb + na
            self.pairs[(a, b)] = len(self.pairs)
        # columns
        costs = []; starts = [0]; idx = []; val = []
        def col(cost, rows, vals, kind, payload):
            costs.append(cost); idx.extend(int(r) for r in rows); val.extend(vals); starts.append(len(idx))
            self.kind.append(kind); self.payload.append(payload)
        for p in new_orders:
            rows = [self.tri[(p[i - 1] if i else S, p[i], p[i + 1] if i + 1 < len(p) else EN)] for i in range(len(p))]
            self.lam_col[p] = len(self.kind)
            col(0.0, rows + [self.r5], [-1.0] * len(rows) + [1.0], "lam", p)
            self.pool.append(p); self.pool_set.add(p)
        for (a, b, c) in new_tri:
            Ob = self.topts[b]; ti = self.tri[(a, b, c)]
            R2 = self.r2[(a, b)] if a != S else None; R3 = self.r3[(b, c)] if c != EN else None
            for j, o in enumerate(Ob):
                rows = [ti]; vals = [1.0]
                if R2 is not None: rows.append(R2[j]); vals.append(-1.0)
                if R3 is not None: rows.append(R3[j]); vals.append(-1.0)
                col(float(self.startc[o]) if a == S else 0.0, rows, vals, "q", (a, b, c, int(o)))
        for (a, b) in new_pairs:
            Oa = self.topts[a]; Ob = self.topts[b]; sub = self.E[np.ix_(Oa, Ob)]
            ii, jj = np.nonzero(sub <= 2)
            R2 = self.r2[(a, b)]; R3 = self.r3[(a, b)]; R4 = self.r4[(a, b)]
            for i_, j_ in zip(ii, jj):
                col(float(sub[i_, j_]), [R2[j_], R3[i_]], [1.0, 1.0], "y", (int(Oa[i_]), int(Ob[j_])))
            for i_ in range(len(Oa)): col(3.0, [R3[i_], R4], [1.0, 1.0], "eout", (a, b, int(Oa[i_])))
            for j_ in range(len(Ob)): col(0.0, [R2[j_], R4], [1.0, -1.0], "ein", (a, b, int(Ob[j_])))
        n = len(costs)
        self.h.addCols(n, np.array(costs), np.zeros(n), np.full(n, highspy.kHighsInf), len(idx),
                       np.array(starts[:-1], np.int32), np.array(idx, np.int32), np.array(val, float))
        return len(new_orders)

    def solve(self, ipm=False):
        if ipm: self.h.setOptionValue("solver", "ipm"); self.h.setOptionValue("run_crossover", "off")
        else: self.h.setOptionValue("solver", "choose"); self.h.setOptionValue("run_crossover", "on")
        t0 = time.time(); self.h.run()
        st = self.h.modelStatusToString(self.h.getModelStatus()); sol = self.h.getSolution()
        self.x = np.array(sol.col_value); self.y = np.array(sol.row_dual); self.obj = self.h.getInfo().objective_function_value
        return st, time.time() - t0

    # ------------------------------------------------------------ full dual and triple potential
    def full_duals(self):
        """master duals mapped into the FULL model (fixed dimension); missing rows: pairs 0, triples implied"""
        NT, NO = self.NT, self.NO; y = self.y
        DR2, DR3, DR4 = self.default_duals()
        for (a, b), rows in self.r2.items(): DR2[a, self.topts[b]] = y[rows]
        for (a, b), rows in self.r3.items(): DR3[self.topts[a], b] = y[rows]
        for (a, b), r in self.r4.items(): DR4[a, b] = y[r]
        Uimp = self.implied_U(DR2, DR3)
        U = Uimp.copy()
        for (a, b, c), r in self.tri.items(): U[a, b, c] = min(y[r], Uimp[a, b, c])
        return U, DR2, DR3, DR4, float(y[self.r5])

    def default_duals(self):
        """feasible split of every link for pairs not in the pool: DR3(o,b) = rowmin/2, DR2(a,o') = colmin/2
        of the capped excess min(e, 3) (sum <= min(e,3) for every option pair); DR4(a,b) = 3 - max DR3 = max DR2 bound"""
        if not hasattr(self, "_defaults"):
            NT, NO = self.NT, self.NO; Ec = np.minimum(self.E, 3)
            rowmin = np.zeros((NO, NT)); colmin = np.zeros((NT, NO))
            for t in range(NT):
                Ot = self.topts[t]
                rowmin[:, t] = Ec[:, Ot].min(1); colmin[t, :] = Ec[Ot, :].min(0)
            DR3 = 0.5 * rowmin; DR2 = 0.5 * colmin
            for t in range(NT): DR3[self.topts[t], t] = 0.0; DR2[t, self.topts[t]] = 0.0
            DR4 = np.zeros((NT, NT))
            for a in range(NT):
                for b in range(NT):
                    if a != b: DR4[a, b] = DR2[a, self.topts[b]].max()     # ein: DR2 - DR4 <= 0; eout: DR3 + DR4 <= 3 holds since rowmin/2 + colmin/2 <= 3
            self._defaults = (DR2, DR3, DR4)
        D2, D3, D4 = self._defaults
        return D2.copy(), D3.copy(), D4.copy()

    def implied_U(self, DR2, DR3):
        NT = self.NT; U = np.zeros((31, NT, 32))
        for b in range(NT):
            Ob = self.topts[b]
            Lft = np.vstack([DR2[:, Ob], self.startc[Ob][None, :]])
            Rgt = np.hstack([DR3[Ob, :], np.zeros((len(Ob), 1))])
            ub = (Lft[:, :, None] + Rgt[None, :, :]).min(1)
            U[:, b, :NT] = ub[:, :NT]; U[:, b, EN] = ub[:, NT]
        return U

    def load_group(self, path):
        g = np.load(path); self.operm = g["operm"]; self.tperm = g["tperm"]

    def symmetrize(self, U, D2, D3, D4):
        """average a full dual over the symmetry group (feasibility and the bound are preserved/improved)"""
        Us = np.zeros_like(U); D2s = np.zeros_like(D2); D3s = np.zeros_like(D3); D4s = np.zeros_like(D4)
        for P, tp in zip(self.operm, self.tperm):
            ta = np.concatenate([tp, [S]]); tc = np.concatenate([tp, [S, EN]])
            Us += U[np.ix_(ta, tp, tc)]; D2s += D2[np.ix_(tp, P)]; D3s += D3[np.ix_(P, tp)]; D4s += D4[np.ix_(tp, tp)]
        k = float(len(self.operm))
        return Us / k, D2s / k, D3s / k, D4s / k

    def q_corrections(self, U, DR2, DR3):
        """per trail b the q columns sum to 1: correction min(0, min_{a,o,c} rc(q))"""
        Uimp = self.implied_U(DR2, DR3); c = 0.0; NT = self.NT
        for b in range(NT):
            A = [a for a in list(range(NT)) + [S] if a != b]; C = [x for x in list(range(NT)) + [EN] if x != b]
            sub = Uimp[np.ix_(A, [b], C)][:, 0, :] - U[np.ix_(A, [b], C)][:, 0, :]
            for i, a in enumerate(A):
                for j, cc in enumerate(C):
                    if a == cc: sub[i, j] = 0.0
            c += min(0.0, float(sub.min()))
        return c

    def other_corrections(self, DR2, DR3, DR4):
        """exact group corrections for y / eout / ein columns of the full model (all pairs)"""
        T = self.T; c = 0.0
        a_, b_ = np.nonzero(self.E <= 2); ok = T[a_] != T[b_]; a_ = a_[ok]; b_ = b_[ok]
        rc = self.E[a_, b_] - DR2[T[a_], b_] - DR3[a_, T[b_]]
        g = np.zeros(self.NO); np.minimum.at(g, a_, rc); c += g.sum()
        rco = 3.0 - DR3 - DR4[T][:, :]                                        # eout_{o,b}: (NO, NT)
        rco[np.arange(self.NO), T] = 0.0; c += np.minimum(0, rco.min(1)).sum()
        rci = -DR2.T + DR4[:, T].T                                              # ein_{a,o'}: (NO, NT) over a
        rci[np.arange(self.NO), T] = 0.0; c += np.minimum(0, rci.min(1)).sum()
        return c

    # ------------------------------------------------------------ pricing (triple-cost ATSP path)
    @staticmethod
    def path_cost(p, U):
        n = len(p); v = 0.0
        for i in range(n):
            v += U[p[i - 1] if i else S, p[i], p[i + 1] if i + 1 < n else EN]
        return v

    def local_search(self, p, U, rounds=4):
        p = list(p); best = self.path_cost(p, U); n = len(p)
        for _ in range(rounds):
            imp = False
            for L in (1, 2, 3, 4):
                for i in range(n - L + 1):
                    seg = p[i:i + L]; rest = p[:i] + p[i + L:]
                    for j in range(len(rest) + 1):
                        if j == i: continue
                        for sg in (seg, seg[::-1]) if L > 1 else (seg,):
                            cand = rest[:j] + sg + rest[j:]; v = self.path_cost(cand, U)
                            if v < best - 1e-12: best = v; p = cand; imp = True; break
                        if imp: break
                    if imp: break
                if imp: break
            if not imp: break
        return best, p

    def exact_qtsp(self, U, time_limit=300.0):
        NT = self.NT; nodesA = list(range(NT)) + [S]; nodesC = list(range(NT)) + [EN]
        arcs = [(a, b) for a in nodesA for b in nodesC if a != b and not (a == S and b == EN)]
        aid = {e: k for k, e in enumerate(arcs)}; NA = len(arcs)
        tris = [(a, b, c) for b in range(NT) for a in nodesA for c in nodesC if a != b and c != b and a != c]
        NTr = len(tris); cx = 0; cw = NA; cg = NA + NTr; real = [(a, b) for (a, b) in arcs if a < NT and b < NT]
        gid = {e: cg + k for k, e in enumerate(real)}; ncol = cg + len(real)
        cost = np.zeros(ncol)
        for k, (a, b, c) in enumerate(tris): cost[cw + k] = U[a, b, c]
        lower = np.zeros(ncol); upper = np.ones(ncol); upper[cg:] = NT - 1
        rows = []
        for b in range(NT):
            rows.append(([aid[(a, b)] for a in nodesA if a != b], None, 1.0, 1.0))
            rows.append(([aid[(b, c)] for c in nodesC if c != b], None, 1.0, 1.0))
        rows.append(([aid[(S, b)] for b in range(NT)], None, 1.0, 1.0))
        rows.append(([aid[(a, EN)] for a in range(NT)], None, 1.0, 1.0))
        byab = {}; bybc = {}
        for k, (a, b, c) in enumerate(tris): byab.setdefault((a, b), []).append(cw + k); bybc.setdefault((b, c), []).append(cw + k)
        R = []
        for (a, b), ws in byab.items(): R.append((ws + [aid[(a, b)]], [1.0] * len(ws) + [-1.0], 0.0, 0.0))
        for (b, c), ws in bybc.items(): R.append((ws + [aid[(b, c)]], [1.0] * len(ws) + [-1.0], 0.0, 0.0))
        for b in range(NT):    # GG flow: start node gets NT units, each node keeps one
            inn = [gid[(a, b)] for a in range(NT) if a != b]; out = [gid[(b, c)] for c in range(NT) if c != b]
            R.append((inn + [aid[(S, b)]] + out, [1.0] * len(inn) + [float(NT)] + [-1.0] * len(out), 1.0, 1.0))
        for (a, b), g in gid.items(): R.append(([g, aid[(a, b)]], [1.0, -(NT - 1.0)], -highspy.kHighsInf, 0.0))
        allrows = [(r[0], [1.0] * len(r[0]), r[2], r[3]) for r in rows] + R
        h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("mip_rel_gap", 0.0); h.setOptionValue("time_limit", time_limit)
        lp = highspy.HighsLp(); lp.num_col_ = ncol; lp.num_row_ = len(allrows)
        lp.col_cost_ = cost; lp.col_lower_ = lower; lp.col_upper_ = upper
        lp.row_lower_ = np.array([r[2] for r in allrows]); lp.row_upper_ = np.array([r[3] for r in allrows])
        st = [0]; ix = []; vl = []
        for r in allrows: ix += r[0]; vl += r[1]; st.append(len(ix))
        lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
        lp.a_matrix_.start_ = np.array(st, np.int32); lp.a_matrix_.index_ = np.array(ix, np.int32); lp.a_matrix_.value_ = np.array(vl)
        # only the arc variables need integrality: for an integral path the triple variables are forced
        lp.integrality_ = [highspy.HighsVarType.kInteger] * NA + [highspy.HighsVarType.kContinuous] * (ncol - NA)
        h.passModel(lp); h.run()
        status = h.modelStatusToString(h.getModelStatus()); info = h.getInfo()
        sol = np.array(h.getSolution().col_value)
        succ = {a: b for (a, b) in arcs if sol[aid[(a, b)]] > 0.5}
        p = []; x = succ.get(S)
        while x is not None and x != EN and len(p) <= NT: p.append(x); x = succ.get(x)
        val = self.path_cost(p, U) if len(p) == NT else None
        return val, p, info.mip_dual_bound, status


def exact_qtsp_dfj(self, U, time_limit=300.0, max_rounds=60):
    """exact triple-cost ATSP path: MIP with degree + triple-linking constraints and iteratively added
    DFJ subtour cuts (sum of arcs inside S <= |S| - 1 for every cycle found).  Returns
    (value, path, valid_lower_bound, status); the lower bound is the last MIP dual bound (each round is a
    relaxation of the exact problem)."""
    NT = self.NT; nodesA = list(range(NT)) + [S]; nodesC = list(range(NT)) + [EN]
    arcs = [(a, b) for a in nodesA for b in nodesC if a != b and not (a == S and b == EN)]
    aid = {e: k for k, e in enumerate(arcs)}; NA = len(arcs)
    tris = [(a, b, c) for b in range(NT) for a in nodesA for c in nodesC if a != b and c != b and a != c]
    cw = NA; ncol = NA + len(tris)
    cost = np.zeros(ncol)
    for k, (a, b, c) in enumerate(tris): cost[cw + k] = U[a, b, c]
    rows = []
    for b in range(NT):
        rows.append(([aid[(a, b)] for a in nodesA if a != b], 1.0, 1.0))
        rows.append(([aid[(b, c)] for c in nodesC if c != b], 1.0, 1.0))
    rows.append(([aid[(S, b)] for b in range(NT)], 1.0, 1.0))
    rows.append(([aid[(a, EN)] for a in range(NT)], 1.0, 1.0))
    byab = {}; bybc = {}
    for k, (a, b, c) in enumerate(tris): byab.setdefault((a, b), []).append(cw + k); bybc.setdefault((b, c), []).append(cw + k)
    lin = []
    for (a, b), ws in byab.items(): lin.append((ws + [aid[(a, b)]], [1.0] * len(ws) + [-1.0]))
    for (b, c), ws in bybc.items(): lin.append((ws + [aid[(b, c)]], [1.0] * len(ws) + [-1.0]))
    h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("mip_rel_gap", 0.0)
    lp = highspy.HighsLp(); lp.num_col_ = ncol; lp.num_row_ = len(rows) + len(lin)
    lp.col_cost_ = cost; lp.col_lower_ = np.zeros(ncol); lp.col_upper_ = np.ones(ncol)
    allr = [(r[0], [1.0] * len(r[0]), r[1], r[2]) for r in rows] + [(l[0], l[1], 0.0, 0.0) for l in lin]
    lp.row_lower_ = np.array([r[2] for r in allr]); lp.row_upper_ = np.array([r[3] for r in allr])
    st = [0]; ix = []; vl = []
    for r in allr: ix += r[0]; vl += r[1]; st.append(len(ix))
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.start_ = np.array(st, np.int32); lp.a_matrix_.index_ = np.array(ix, np.int32); lp.a_matrix_.value_ = np.array(vl)
    lp.integrality_ = [highspy.HighsVarType.kInteger] * NA + [highspy.HighsVarType.kContinuous] * (ncol - NA)
    h.passModel(lp)
    t0 = time.time(); bound = -1e18; status = "?"
    for rnd in range(max_rounds):
        h.setOptionValue("time_limit", max(1.0, time_limit - (time.time() - t0)))
        h.run(); status = h.modelStatusToString(h.getModelStatus()); info = h.getInfo()
        bound = info.mip_dual_bound
        sol = np.array(h.getSolution().col_value)
        succ = {a: b for (a, b) in arcs if sol[aid[(a, b)]] > 0.5}
        p = []; x = succ.get(S); seen = set()
        while x is not None and x != EN and x not in seen: p.append(x); seen.add(x); x = succ.get(x)
        if len(p) == NT: return self.path_cost(p, U), p, bound, status
        if status != "Optimal": return None, p, bound, status
        rest = [t for t in range(NT) if t not in seen]; left = set(rest); cuts = 0
        while left:
            t = left.pop(); cyc = [t]; x = succ.get(t)
            while x is not None and x in left: cyc.append(x); left.discard(x); x = succ.get(x)
            idx = [aid[(u, v)] for u in cyc for v in cyc if u != v]
            h.addRow(-highspy.kHighsInf, float(len(cyc) - 1), len(idx), np.array(idx, np.int32), np.ones(len(idx))); cuts += 1
        if cuts == 0: return None, p, bound, "stuck"
    return None, p, bound, "round limit"

TMaster.exact_qtsp_dfj = exact_qtsp_dfj


def main():
    fam_p, E_p, audit_p, seed_p, out = sys.argv[1:6]
    max_iter = int(sys.argv[6]) if len(sys.argv) > 6 else 500
    alpha0 = float(sys.argv[7]) if len(sys.argv) > 7 else 0.6
    ipm = (len(sys.argv) > 8 and sys.argv[8] == "ipm")
    qtsp_tl = 180.0
    sym = os.environ.get("TLP_SYM", "1") == "1"
    t0 = time.time(); rnd = random.Random(3)
    m = TMaster(fam_p, E_p)
    m.load_group(os.path.join(HERE, "..", "certs", "group_options.npz"))
    base = [r["trail"] for r in json.load(open(audit_p))["table"]]
    sd = json.load(open(seed_p))
    seed = [x["order"] for x in sd["decomposition"]] if "decomposition" in sd else sd["pool"]
    m.add_orders([base] + seed)
    print(json.dumps(dict(event="built", pool=len(m.pool), rows=m.nrow, cols=len(m.kind), sec=round(time.time() - t0, 1), ipm=ipm, alpha=alpha0)), flush=True)
    hist = []; Lbest = -1e18; center = None
    # stability centre: the default half-split duals (a valid point; its bound L0 is computed exactly)
    D2d, D3d, D4d = m.default_duals(); Ud = m.implied_U(D2d, D3d)
    if len(sys.argv) > 9:
        L0 = float(sys.argv[9])
    else:
        v0, p0, b0, s0 = m.exact_qtsp(Ud, time_limit=qtsp_tl); L0 = float(b0)
    center = (Ud, D2d, D3d, D4d, L0); Lbest = L0
    print(json.dumps(dict(event="centre", L0=L0)), flush=True)
    for it in range(max_iter):
        st, dt = m.solve(ipm)
        Ur, D2r, D3r, D4r, ucm = m.full_duals()
        if sym: Um, D2m, D3m, D4m = m.symmetrize(Ur, D2r, D3r, D4r)
        else: Um, D2m, D3m, D4m = Ur, D2r, D3r, D4r
        support = [m.payload[j] for j in range(len(m.kind)) if m.kind[j] == "lam" and m.x[j] > 1e-9]
        a = alpha0; cand = {}; npr = 0
        while True:
            npr += 1
            U = a * center[0] + (1 - a) * Um; D2 = a * center[1] + (1 - a) * D2m; D3 = a * center[2] + (1 - a) * D3m
            D4 = a * center[3] + (1 - a) * D4m; uc = a * center[4] + (1 - a) * ucm
            ex_v, ex_p, ex_b, ex_st = m.exact_qtsp_dfj(U, time_limit=qtsp_tl)
            qc = m.q_corrections(U, D2, D3); oc = m.other_corrections(D2, D3, D4)
            L = uc + min(0.0, ex_b - uc) + qc + oc
            if L > Lbest: Lbest = L; center = (U.copy(), D2.copy(), D3.copy(), D4.copy(), uc); best = dict(it=it, L=L)
            # candidate orders: negative reduced cost at the MASTER duals
            starts = support + [tuple(base)] + ([tuple(ex_p)] if ex_v is not None else []) + rnd.sample(m.pool, min(6, len(m.pool)))
            for p in starts:
                v, q = m.local_search(p, Ur)
                if v - ucm < -TOL and tuple(q) not in m.pool_set: cand[tuple(q)] = v - ucm
            if ex_v is not None and tuple(ex_p) not in m.pool_set:
                cand[tuple(ex_p)] = m.path_cost(ex_p, Ur) - ucm        # the separation optimum is always added
            if cand or a == 0: break
            a = 0.0 if a < 0.1 else a / 2
        if not cand:   # nothing at the master duals: confirm with an exact pricing at the master duals
            ev, ep, eb, es = m.exact_qtsp_dfj(Ur, time_limit=qtsp_tl)
            if ev is not None and ev - ucm < -TOL and tuple(ep) not in m.pool_set: cand[tuple(ep)] = ev - ucm
        rec = dict(it=it, status=st, lp=round(m.obj, 6), alpha=a, pricings=npr, qtsp_sep=None if ex_v is None else round(ex_v, 6), qtsp_bound=round(float(ex_b), 6),
                   q_corr=round(qc, 6), other_corr=round(float(oc), 6), L=round(float(L), 6), Lbest=round(float(Lbest), 6), new_orders=len(cand),
                   pool=len(m.pool), support=len(support), rows=m.nrow, cols=len(m.kind), solve_s=round(dt, 1), t=round(time.time() - t0, 1))
        print(json.dumps(rec), flush=True); hist.append(rec)
        if it % 5 == 4 or not cand:
            lam = [dict(order=list(m.payload[j]), lam=float(m.x[j])) for j in range(len(m.kind)) if m.kind[j] == "lam" and m.x[j] > 1e-9]
            json.dump(dict(it=it, lp=m.obj, Lbest=Lbest, lambda_orders=lam, pool=[list(p) for p in m.pool], history=hist), open(out, "w"))
            np.savez_compressed(out.replace(".json", "_center.npz"), U=center[0], DR2=center[1], DR3=center[2], DR4=center[3], uconv=center[4])
        if not cand: print(json.dumps(dict(event="converged", lp=m.obj, Lbest=Lbest)), flush=True); break
        m.add_orders(sorted(cand, key=lambda p: cand[p])[:20])


if __name__ == "__main__":
    main()
