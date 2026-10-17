#!/usr/bin/env python3
"""Round O (sections 8-12) -- ORDER-HULL LP for the single-opening model.

The opening/linking LP of Round M/N with the subtour constraints replaced by the exact trail-order
hull: the trail-level arc vector z (z_tu = sum of option arcs t -> u, else arcs included) must be a
convex combination of incidence vectors of genuine Hamiltonian trail ORDERS:
    z = sum_pi lam_pi z^pi,   first(t) = sum_pi lam_pi [pi_1 = t],  last(t) likewise,  sum lam = 1.
Every inequality valid for the order polytope (subtour, comb, transitivity / linear-ordering,
precedence, position constraints, ...) is implied, so this is the strongest bound any trail-level
order cut can give.  Columns lam_pi are priced EXACTLY by a 30-node ATSP-path MIP (Gavish-Graves
flow); option arcs with e = 2 are priced; mode 'ohcc' also replaces the C1/C2 internals by exact
cover columns (Round N CC-LP), mode 'oh' keeps all trails free (arc model).
Wentges smoothing; at every step a valid Lagrangian bound L(y) = b^T y + group corrections (the H-path
group minimum comes from the exact pricing MIP, the cover minimum from the exact subset DP).
usage: oh_lp.py FAMILY.json E.npy AUDIT.json MODE OUT.json [alpha] [max_iter]"""
import sys, os, json, time, random
import numpy as np
import highspy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "rN", "src"))
import options as OP
import cc_lp as CC

EMAX = 2; ELSE_COST = 3.0; TOL = 1e-7; INF = 1e9


class OHMaster:
    def __init__(self, fam_path, E_path, mode="oh"):
        self.fam, self.opts = OP.load(fam_path)
        self.E = np.load(E_path)
        self.mode = mode
        T = self.T = np.array([o["t"] for o in self.opts]); NO = self.NO = len(self.opts)
        NT = self.NT = int(T.max()) + 1
        self.cut = np.array([o["cut"] for o in self.opts])
        self.topts = [np.nonzero(T == t)[0] for t in range(NT)]
        self.key = {(o["t"], o["v"], o["k"]): i for i, o in enumerate(self.opts)}
        comp = np.zeros(NT, int)
        if mode == "ohcc": comp[CC.C1] = 1; comp[CC.C2] = 2
        self.comp = comp
        self.comps = {1: CC.C1, 2: CC.C2} if mode == "ohcc" else {}
        self.multi = 8
        self.allowed_tt = ~((comp[:, None] == comp[None, :]) & (comp[:, None] > 0)) & ~np.eye(NT, dtype=bool)
        r = 0
        self.in_row = np.arange(NO) + r; r += NO
        self.out_row = np.arange(NO) + r; r += NO
        self.sel_row = {}
        for t in range(NT):
            if comp[t] == 0: self.sel_row[t] = r; r += 1
        self.eo_row = np.arange(NT) + r; r += NT
        self.ei_row = np.arange(NT) + r; r += NT
        self.conv_row = {}
        for X in self.comps: self.conv_row[X] = r; r += 1
        self.pair_row = np.full((NT, NT), -1, int)
        for t in range(NT):
            for u in range(NT):
                if t != u: self.pair_row[t, u] = r; r += 1
        self.first_row = np.arange(NT) + r; r += NT
        self.last_row = np.arange(NT) + r; r += NT
        self.lam_row = r; r += 1
        self.nrow = r
        lo = np.zeros(r); up = np.zeros(r)
        for rr in list(self.sel_row.values()) + list(self.conv_row.values()) + [self.lam_row]: lo[rr] = up[rr] = 1.0
        self.kind = []; self.payload = []; self.cover_sigs = set(); self.path_sigs = set()
        cols = []
        def add(kind, payload, cost, rows, vals):
            self.kind.append(kind); self.payload.append(payload); cols.append((cost, rows, vals))
        for t in range(NT):
            for u in range(NT):
                if self.allowed_tt[t, u]: add("else", (t, u), ELSE_COST, [self.eo_row[t], self.ei_row[u], self.pair_row[t, u]], [-1.0, -1.0, 1.0])
        for o in range(NO):
            t = T[o]
            add("eout", o, 0.0, [self.out_row[o], self.eo_row[t]], [1.0, 1.0])
            add("ein", o, 0.0, [self.in_row[o], self.ei_row[t]], [1.0, 1.0])
            add("s", o, float(3 - self.cut[o]), [self.in_row[o], self.first_row[t]], [1.0, 1.0])
            add("t", o, 0.0, [self.out_row[o], self.last_row[t]], [1.0, 1.0])
            if comp[t] == 0: add("z", o, 0.0, [self.sel_row[t], self.in_row[o], self.out_row[o]], [1.0, -1.0, -1.0])
        a, b = np.nonzero(self.E <= EMAX)
        ok = self.allowed_tt[T[a], T[b]]; a = a[ok]; b = b[ok]; e = self.E[a, b].astype(int)
        self.all_a = a; self.all_b = b; self.all_e = e.astype(float)
        self.pool_a = a[e == 2]; self.pool_b = b[e == 2]; self.in_pool = np.zeros(len(self.pool_a), bool)
        for x, y, ee in zip(a[e <= 1], b[e <= 1], e[e <= 1]):
            add("arc", (int(x), int(y)), float(ee), [self.out_row[x], self.in_row[y], self.pair_row[T[x], T[y]]], [1.0, 1.0, 1.0])
        h = self.h = highspy.Highs(); h.setOptionValue("output_flag", False)
        h.setOptionValue("solver", "simplex"); h.setOptionValue("threads", 2)
        lp = highspy.HighsLp(); lp.num_col_ = len(cols); lp.num_row_ = self.nrow
        lp.col_cost_ = np.array([c[0] for c in cols]); lp.col_lower_ = np.zeros(len(cols)); lp.col_upper_ = np.full(len(cols), highspy.kHighsInf)
        lp.row_lower_ = lo; lp.row_upper_ = up
        st = [0]; ix = []; vl = []
        for c in cols: ix += list(c[1]); vl += list(c[2]); st.append(len(ix))
        lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
        lp.a_matrix_.start_ = np.array(st, np.int32); lp.a_matrix_.index_ = np.array(ix, np.int32); lp.a_matrix_.value_ = np.array(vl, float)
        h.passModel(lp)

    def ncol(self): return len(self.kind)

    def add_cols(self, items):
        if not items: return
        st = [0]; ix = []; vl = []; costs = []
        for kind, payload, cost, rows, vals in items:
            ix += list(rows); vl += list(vals); st.append(len(ix)); costs.append(cost)
            self.kind.append(kind); self.payload.append(payload)
        n = len(items)
        self.h.addCols(n, np.array(costs, float), np.zeros(n), np.full(n, highspy.kHighsInf), len(ix),
                       np.array(st[:-1], np.int32), np.array(ix, np.int32), np.array(vl, float))

    def path_column(self, pi):
        rows = [self.pair_row[a, b] for a, b in zip(pi, pi[1:])] + [self.first_row[pi[0]], self.last_row[pi[-1]], self.lam_row]
        vals = [-1.0] * (len(pi) - 1) + [-1.0, -1.0, 1.0]
        return ("path", tuple(int(t) for t in pi), 0.0, rows, vals)

    def cover_column(self, X, paths):
        E = self.E; T = self.T; cost = 0.0; tarcs = []
        for p in paths:
            for o, o2 in zip(p, p[1:]): cost += float(E[o, o2]); tarcs.append((int(T[o]), int(T[o2])))
        rows = [self.conv_row[X]] + [self.in_row[p[0]] for p in paths] + [self.out_row[p[-1]] for p in paths] + [self.pair_row[t, u] for t, u in tarcs]
        vals = [1.0] + [-1.0] * (2 * len(paths)) + [1.0] * len(tarcs)
        sig = (X, tuple(sorted(tuple(int(o) for o in p) for p in paths)))
        return sig, ("cover", dict(X=X, paths=[[int(o) for o in p] for p in paths], tarcs=tarcs), cost, rows, vals)

    def solve(self):
        t0 = time.time(); self.h.run()
        status = self.h.modelStatusToString(self.h.getModelStatus())
        sol = self.h.getSolution()
        self.x = np.array(sol.col_value); self.y = np.array(sol.row_dual)
        self.obj = self.h.getInfo().objective_function_value
        return status, time.time() - t0

    # ---------------- duals seen by the trail level
    def mu(self, y):
        M = np.zeros((self.NT, self.NT))
        msk = self.pair_row >= 0
        M[msk] = y[self.pair_row[msk]]
        return M

    # ---------------- H-path pricing
    def path_value(self, pi, M, nf, nl):
        return nf[pi[0]] + nl[pi[-1]] + sum(M[a, b] for a, b in zip(pi, pi[1:]))

    def local_search(self, pi, M, nf, nl, rnd, rounds=3):
        pi = list(pi); best = self.path_value(pi, M, nf, nl); n = len(pi)
        for _ in range(rounds):
            improved = False
            for L in (1, 2, 3):
                for i in range(n - L + 1):
                    seg = pi[i:i + L]; rest = pi[:i] + pi[i + L:]
                    for j in range(len(rest) + 1):
                        if j == i: continue
                        cand = rest[:j] + seg + rest[j:]
                        v = self.path_value(cand, M, nf, nl)
                        if v < best - 1e-12: best = v; pi = cand; improved = True; break
                    if improved: break
                if improved: break
            if not improved: break
        return best, pi

    def exact_path(self, M, nf, nl, time_limit=60.0):
        NT = self.NT
        pairs = [(t, u) for t in range(NT) for u in range(NT) if t != u]; P = len(pairs)
        cx = 0; cs = P; ce = cs + NT; cg = ce + NT; ncol = cg + P
        cost = np.zeros(ncol)
        for k, (t, u) in enumerate(pairs): cost[cx + k] = M[t, u]
        cost[cs:cs + NT] = nf; cost[ce:ce + NT] = nl
        lower = np.zeros(ncol); upper = np.ones(ncol); upper[cg:cg + P] = NT - 1
        rows = []
        outp = {t: [] for t in range(NT)}; inp = {t: [] for t in range(NT)}
        for k, (t, u) in enumerate(pairs): outp[t].append(k); inp[u].append(k)
        for t in range(NT):
            rows.append(([cx + k for k in outp[t]] + [ce + t], [1.0] * (len(outp[t]) + 1), 1.0, 1.0))
            rows.append(([cx + k for k in inp[t]] + [cs + t], [1.0] * (len(inp[t]) + 1), 1.0, 1.0))
            rows.append(([cg + k for k in inp[t]] + [cs + t] + [cg + k for k in outp[t]], [1.0] * len(inp[t]) + [float(NT)] + [-1.0] * len(outp[t]), 1.0, 1.0))
        rows.append(([cs + t for t in range(NT)], [1.0] * NT, 1.0, 1.0))
        rows.append(([ce + t for t in range(NT)], [1.0] * NT, 1.0, 1.0))
        for k in range(P): rows.append(([cg + k, cx + k], [1.0, -(NT - 1.0)], -highspy.kHighsInf, 0.0))
        h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("mip_rel_gap", 0.0)
        h.setOptionValue("time_limit", time_limit)
        lp = highspy.HighsLp(); lp.num_col_ = ncol; lp.num_row_ = len(rows)
        lp.col_cost_ = cost; lp.col_lower_ = lower; lp.col_upper_ = upper
        lp.row_lower_ = np.array([r[2] for r in rows]); lp.row_upper_ = np.array([r[3] for r in rows])
        st = [0]; ix = []; vl = []
        for r in rows: ix += r[0]; vl += r[1]; st.append(len(ix))
        lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
        lp.a_matrix_.start_ = np.array(st, np.int32); lp.a_matrix_.index_ = np.array(ix, np.int32); lp.a_matrix_.value_ = np.array(vl)
        lp.integrality_ = [highspy.HighsVarType.kInteger] * (cg) + [highspy.HighsVarType.kContinuous] * P
        h.passModel(lp); h.run()
        st_ = h.modelStatusToString(h.getModelStatus()); info = h.getInfo()
        sol = np.array(h.getSolution().col_value)
        start = [t for t in range(NT) if sol[cs + t] > 0.5][0]
        succ = {pairs[k][0]: pairs[k][1] for k in range(P) if sol[cx + k] > 0.5}
        pi = [start]
        while pi[-1] in succ and len(pi) <= NT: pi.append(succ[pi[-1]])
        assert len(pi) == NT and len(set(pi)) == NT, (st_, pi)
        return self.path_value(pi, M, nf, nl), pi, info.mip_dual_bound, st_

    def price_paths(self, y, pool, rnd, n_heur=12):
        M = self.mu(y); nf = y[self.first_row]; nl = y[self.last_row]; alpha = y[self.lam_row]
        found = {}
        for pi in pool[:n_heur]:
            v, q = self.local_search(pi, M, nf, nl, rnd)
            if v - alpha < -TOL: found[tuple(q)] = v - alpha
        v, q, bound, st = self.exact_path(M, nf, nl)
        exact_min = min(v, bound) - alpha     # valid lower bound of the H-path group (bound <= optimum)
        if v - alpha < -TOL: found[tuple(q)] = v - alpha
        return found, exact_min, (v - alpha), q

    # ---------------- arcs
    def price_arcs(self, y, M, limit=40000):
        free = ~self.in_pool
        a = self.pool_a[free]; b = self.pool_b[free]
        rc = 2.0 - y[self.out_row[a]] - y[self.in_row[b]] - M[self.T[a], self.T[b]]
        neg = np.nonzero(rc < -TOL)[0]
        if len(neg) > limit: neg = neg[np.argsort(rc[neg])[:limit]]
        idx = np.nonzero(free)[0][neg]; self.in_pool[idx] = True
        T = self.T
        return [("arc", (int(x), int(z)), 2.0, [self.out_row[x], self.in_row[z], self.pair_row[T[x], T[z]]], [1.0, 1.0, 1.0])
                for x, z in zip(self.pool_a[idx], self.pool_b[idx])]

    # ---------------- Lagrangian bound
    def lagrangian(self, y, path_min, cover_min):
        T = self.T; M = self.mu(y); NO = self.NO
        b = sum(y[rr] for rr in self.sel_row.values()) + sum(y[rr] for rr in self.conv_row.values()) + y[self.lam_row]
        corr = {}
        d = self.all_e - y[self.out_row[self.all_a]] - y[self.in_row[self.all_b]] - M[T[self.all_a], T[self.all_b]]
        g = np.zeros(NO); np.minimum.at(g, self.all_a, d); corr["arc"] = g.sum()
        tt = np.array([(t, u) for t in range(self.NT) for u in range(self.NT) if self.allowed_tt[t, u]])
        de = ELSE_COST + y[self.eo_row[tt[:, 0]]] + y[self.ei_row[tt[:, 1]]] - M[tt[:, 0], tt[:, 1]]
        ge = np.zeros(self.NT); np.minimum.at(ge, tt[:, 0], de); corr["else"] = ge.sum()
        corr["eout"] = np.minimum(0, -y[self.out_row] - y[self.eo_row[T]]).sum()
        corr["ein"] = np.minimum(0, -y[self.in_row] - y[self.ei_row[T]]).sum()
        corr["s"] = min(0.0, ((3 - self.cut) - y[self.in_row] - y[self.first_row[T]]).min())
        corr["t"] = min(0.0, (-y[self.out_row] - y[self.last_row[T]]).min())
        cz = 0.0
        for t, rr in self.sel_row.items():
            oo = self.topts[t]; cz += min(0.0, (-y[rr] + y[self.in_row[oo]] + y[self.out_row[oo]]).min())
        corr["z"] = cz
        corr["cover"] = sum(min(0.0, v) for v in cover_min.values())
        corr["path"] = min(0.0, path_min)
        return b + sum(corr.values()), corr


def main():
    fam_p, E_p, audit_p, mode, out_p = sys.argv[1:6]
    alpha = float(sys.argv[6]) if len(sys.argv) > 6 else 0.7
    max_iter = int(sys.argv[7]) if len(sys.argv) > 7 else 2000
    t0 = time.time(); rnd = random.Random(11)
    m = OHMaster(fam_p, E_p, mode)
    d = json.load(open(audit_p))
    seq = [m.key[(r["trail"], r["version"], r["start"])] for r in d["table"]]
    order = [r["trail"] for r in d["table"]]
    items = [m.path_column(order)]; m.path_sigs.add(tuple(order))
    if mode == "ohcc":
        seqT = [int(m.T[o]) for o in seq]
        for X, trails in m.comps.items():
            segs = []; cur = []
            for o in seq:
                if m.T[o] in trails: cur.append(int(o))
                elif cur: segs.append(cur); cur = []
            if cur: segs.append(cur)
            sig, it = m.cover_column(X, segs); m.cover_sigs.add(sig); items.append(it)
            ref = {int(m.T[o]): int(o) for o in seq}
            for t in trails:
                for o in m.topts[t]:
                    sig, it = m.cover_column(X, [[int(o)] if u == t else [ref[u]] for u in trails])
                    if sig not in m.cover_sigs: m.cover_sigs.add(sig); items.append(it)
    m.add_cols(items)
    print(json.dumps(dict(event="built", mode=mode, cols=m.ncol(), rows=m.nrow, sec=round(time.time() - t0, 1))), flush=True)
    center = None; Lbest = -1e18; best_y = None; hist = []
    for it in range(max_iter):
        status, dt = m.solve(); yin = m.y.copy(); z = m.obj
        if center is None: center = yin.copy()
        pool = [m.payload[j] for j in range(m.ncol()) if m.kind[j] == "path" and m.x[j] > 1e-9]
        pool = sorted(pool, key=lambda p: rnd.random())
        a = alpha; new = []; npr = 0
        while True:
            ys = a * center + (1 - a) * yin; npr += 1
            Mi = m.mu(yin); Ms = m.mu(ys)
            found, pmin, pbest, pq = m.price_paths(ys, pool + [tuple(order)], rnd)
            cmin = {}
            for X in m.comps:
                res = CC.Master.price_component(m, X, Ms, ys)
                cmin[X] = min(r[1] for r in res)
                for r, rc, paths in res:
                    sig, item = m.cover_column(X, paths)
                    rin = CC.Master.rc_of_cover(m, X, paths, Mi, yin)
                    if rin < -TOL and sig not in m.cover_sigs: m.cover_sigs.add(sig); new.append(item)
            L, corr = m.lagrangian(ys, pmin, cmin)
            if L > Lbest: Lbest = L; center = ys.copy(); best_y = ys.copy()
            nfi = yin[m.first_row]; nli = yin[m.last_row]
            for pi in found:
                if pi in m.path_sigs: continue
                if m.path_value(list(pi), Mi, nfi, nli) - yin[m.lam_row] < -TOL:
                    m.path_sigs.add(pi); new.append(m.path_column(list(pi)))
            m.y = yin
            new += m.price_arcs(yin, Mi)
            if new or a == 0: break
            a = 0.0 if a < 0.1 else a / 2
        rec = dict(it=it, status=status, lp=round(z, 6), L=round(Lbest, 6), gap=round(z - Lbest, 6), alpha_used=a, pricings=npr,
                   added=len(new), path_rc=round(pbest, 4), cover_rc={str(k): round(v, 4) for k, v in cmin.items()},
                   paths=sum(1 for k in m.kind if k == "path"), cols=m.ncol(), solve_s=round(dt, 1), t=round(time.time() - t0, 1))
        print(json.dumps(rec), flush=True); hist.append(rec)
        if it % 10 == 9 or not new:
            lam = [(m.payload[j], float(m.x[j])) for j in range(m.ncol()) if m.kind[j] == "path" and m.x[j] > 1e-9]
            cov = [dict(X=m.payload[j]["X"], paths=m.payload[j]["paths"], x=float(m.x[j])) for j in range(m.ncol()) if m.kind[j] == "cover" and m.x[j] > 1e-9]
            json.dump(dict(mode=mode, it=it, lp=z, Lbest=Lbest, lambda_paths=[dict(order=list(p), lam=v) for p, v in lam], covers=cov,
                           converged=not new, history=hist), open(out_p, "w"))
            np.savez_compressed(out_p.replace(".json", "_duals.npz"), y_best=best_y, y_last=m.y)
        if not new:
            print(json.dumps(dict(event="converged", lp=z, L=Lbest)), flush=True); break
        m.add_cols(new)


if __name__ == "__main__":
    main()
