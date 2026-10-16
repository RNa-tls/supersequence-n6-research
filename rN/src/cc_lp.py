#!/usr/bin/env python3
"""Round N (section 3) -- component-cover column generation LP (CC-LP), single-opening model.

Model = gtsp_mip's single-opening path model: every trail picks one option o (version, opening edge);
boundary o -> o' costs e = E[o, o'] (exact excess); the first option costs [cut = 2]; explicit arcs
for e <= EMAX = 2 and trail-level 'else' arcs of cost 3 (a lower bound of every e >= 3).

New: the internal structure of each phi component X in {C1, C2} is given by COVER COLUMNS.
A column K = a set of directed paths covering all 11 trails of X, one option per trail; its cost is
the exact sum of E over its internal arcs (no cap).  Linking arcs (and else arcs) inside one
component are forbidden: every word decomposes into maximal component segments, so this is still
a relaxation of the single-opening model.  Subtours: lazy DFJ cuts in(S) >= 1 on the trail-level
support (column-internal arcs included).  Pricing: exact subset DP over the 2^11 trail subsets
(paths) and a cover DP (3^11 pairs), per number of paths.  Arcs with e = 2 are priced as well.

mode 'arc' reproduces the plain arc LP (all trails free, intra-component arcs allowed).
At convergence (no negative reduced cost column or arc, no violated cut) the LP value is a valid
lower bound on [c0 = 2] + sum e, i.e. J >= 77 + ceil(LP) for single-opening words.
usage: cc_lp.py FAMILY.json E.npy WORD_AUDIT.json [cc|arc] [max_iter] [out.json]"""
import sys, os, json, time
import numpy as np
import networkx as nx
import highspy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import options as OP

C1 = [2, 3, 4, 5, 6, 7, 23, 24, 25, 26, 27]
C2 = [9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21]
AT = [1, 8, 15, 22, 28, 29]
EMAX = 2
ELSE_COST = 3.0
INF = 1e9
TOL = 1e-7


class Master:
    def __init__(self, fam_path, E_path, mode="cc"):
        self.fam, self.opts = OP.load(fam_path)
        self.E = np.load(E_path)
        self.mode = mode
        T = self.T = np.array([o["t"] for o in self.opts]); NO = self.NO = len(self.opts)
        NT = self.NT = int(T.max()) + 1
        self.cut = np.array([o["cut"] for o in self.opts])
        self.topts = [np.nonzero(T == t)[0] for t in range(NT)]
        self.key = {(o["t"], o["v"], o["k"]): i for i, o in enumerate(self.opts)}
        comp = np.zeros(NT, int)
        if mode in ("cc", "cca", "ccr"):
            comp[C1] = 1; comp[C2] = 2
        if mode == "cca":
            comp[AT] = 3
        if mode == "ccr":
            comp[AT] = 3; comp[[0, 14]] = 3
        self.comp = comp
        self.comps = {"cc": {1: C1, 2: C2}, "cca": {1: C1, 2: C2, 3: AT}, "ccr": {1: C1, 2: C2, 3: AT + [0, 14]}}.get(mode, {})
        self.allowed_tt = ~((comp[:, None] == comp[None, :]) & (comp[:, None] > 0)) & ~np.eye(NT, dtype=bool)
        # ---- rows
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
        self.s_row = r; r += 1
        self.t_row = r; r += 1
        lo = np.zeros(r); up = np.zeros(r)
        for rr in list(self.sel_row.values()) + list(self.conv_row.values()) + [self.s_row, self.t_row]: lo[rr] = up[rr] = 1.0
        self.nrow = r
        self.secs = []; self.sec_rows = []; self.sec_set = set()
        # ---- column bookkeeping
        self.kind = []; self.payload = []
        self.arc_index = {}       # (a, b) -> column
        self.arc_cols = []; self.arc_ta = []; self.arc_tb = []; self.else_cols = []; self.else_t = []; self.else_u = []
        self.s_cols = []; self.s_t = []; self.cover_cols = []
        self.cover_sigs = set()
        self.multi = 8
        cols = []                  # (cost, lb, ub, rows, vals)
        def add(kind, payload, cost, rows, vals, ub=highspy.kHighsInf):
            self._track(kind, payload); cols.append((cost, 0.0, ub, rows, vals))
        Ttt = self.allowed_tt
        # else arcs
        for t in range(NT):
            for u in range(NT):
                if Ttt[t, u]: add("else", (t, u), ELSE_COST, [self.eo_row[t], self.ei_row[u]], [-1.0, -1.0])
        for o in range(NO):
            t = T[o]
            add("eout", o, 0.0, [self.out_row[o], self.eo_row[t]], [1.0, 1.0])
            add("ein", o, 0.0, [self.in_row[o], self.ei_row[t]], [1.0, 1.0])
            add("s", o, float(3 - self.cut[o]), [self.in_row[o], self.s_row], [1.0, 1.0])
            add("t", o, 0.0, [self.out_row[o], self.t_row], [1.0, 1.0])
            if comp[t] == 0: add("z", o, 0.0, [self.sel_row[t], self.in_row[o], self.out_row[o]], [1.0, -1.0, -1.0])
        # explicit arcs e <= 1 now, e = 2 by pricing
        Ef = self.E
        a, b = np.nonzero(Ef <= EMAX)
        ok = Ttt[T[a], T[b]]
        a = a[ok]; b = b[ok]; e = Ef[a, b].astype(int)
        self.all_a = a; self.all_b = b; self.all_e = e.astype(float)
        self.pool_a = a[e == 2]; self.pool_b = b[e == 2]          # priced later
        for x, y, ee in zip(a[e <= 1], b[e <= 1], e[e <= 1]):
            add("arc", (int(x), int(y)), float(ee), [self.out_row[x], self.in_row[y]], [1.0, 1.0])
        self.in_pool = np.zeros(len(self.pool_a), bool)
        # ---- build HiGHS model (column-wise)
        h = self.h = highspy.Highs(); h.setOptionValue("output_flag", False)
        h.setOptionValue("solver", "simplex"); h.setOptionValue("threads", 2)
        lp = highspy.HighsLp(); lp.num_col_ = len(cols); lp.num_row_ = self.nrow
        lp.col_cost_ = np.array([c[0] for c in cols]); lp.col_lower_ = np.array([c[1] for c in cols]); lp.col_upper_ = np.array([c[2] for c in cols])
        lp.row_lower_ = lo; lp.row_upper_ = up
        st = [0]; ix = []; vl = []
        for c in cols: ix += list(c[3]); vl += list(c[4]); st.append(len(ix))
        lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
        lp.a_matrix_.start_ = np.array(st, np.int32); lp.a_matrix_.index_ = np.array(ix, np.int32); lp.a_matrix_.value_ = np.array(vl, float)
        h.passModel(lp)

    # ------------------------------------------------------------------ helpers
    def ncol(self): return len(self.kind)

    def sec_coef(self, kind, payload, S):
        T = self.T
        if kind == "arc":
            a, b = payload; return 1.0 if (T[a] not in S and T[b] in S) else 0.0
        if kind == "else":
            t, u = payload; return 1.0 if (t not in S and u in S) else 0.0
        if kind == "s":
            return 1.0 if T[payload] in S else 0.0
        if kind == "cover":
            return float(sum(1 for (t, u) in payload["tarcs"] if t not in S and u in S))
        return 0.0

    def _track(self, kind, payload):
        j = len(self.kind); self.kind.append(kind); self.payload.append(payload)
        T = self.T
        if kind == "arc": self.arc_index[payload] = j; self.arc_cols.append(j); self.arc_ta.append(int(T[payload[0]])); self.arc_tb.append(int(T[payload[1]]))
        elif kind == "else": self.else_cols.append(j); self.else_t.append(payload[0]); self.else_u.append(payload[1])
        elif kind == "s": self.s_cols.append(j); self.s_t.append(int(T[payload]))
        elif kind == "cover": self.cover_cols.append(j)
        return j

    def _ins_matrix(self):
        INS = np.zeros((len(self.secs), self.NT), bool)
        for i, S in enumerate(self.secs): INS[i, list(S)] = True
        return INS

    def add_cols(self, items):
        """items: list of (kind, payload, cost, rows, vals); SEC coefficients are appended here"""
        if not items: return
        INS = self._ins_matrix(); srow = np.array(self.sec_rows, np.int64)
        st = [0]; ix = []; vl = []; costs = []
        arcs = [k for k, it in enumerate(items) if it[0] == "arc"]
        extra = {}
        if len(self.secs) and arcs:
            ta = np.array([self.T[items[k][1][0]] for k in arcs]); tb = np.array([self.T[items[k][1][1]] for k in arcs])
            C = (~INS[:, ta]) & INS[:, tb]
            jj, ii = np.nonzero(C.T)
            for j, i in zip(jj, ii): extra.setdefault(arcs[j], []).append(int(srow[i]))
        for k, (kind, payload, cost, rows, vals) in enumerate(items):
            rows = list(rows); vals = list(vals)
            if kind == "arc":
                for rr in extra.get(k, []): rows.append(rr); vals.append(1.0)
            elif len(self.secs):
                for S, rr in zip(self.secs, self.sec_rows):
                    c = self.sec_coef(kind, payload, S)
                    if c: rows.append(rr); vals.append(c)
            ix += rows; vl += vals; st.append(len(ix)); costs.append(cost)
            self._track(kind, payload)
        n = len(items)
        self.h.addCols(n, np.array(costs, float), np.zeros(n), np.full(n, highspy.kHighsInf), len(ix),
                       np.array(st[:-1], np.int32), np.array(ix, np.int32), np.array(vl, float))

    def add_secs(self, sets):
        st = [0]; ix = []; vl = []; new = []
        ac = np.array(self.arc_cols); ata = np.array(self.arc_ta); atb = np.array(self.arc_tb)
        ec = np.array(self.else_cols); et = np.array(self.else_t); eu = np.array(self.else_u)
        sc = np.array(self.s_cols); stt = np.array(self.s_t)
        for S in sets:
            S = frozenset(int(t) for t in S)
            if S in self.sec_set or len(S) in (0, self.NT): continue
            self.sec_set.add(S); new.append(S)
            ins = np.zeros(self.NT, bool); ins[list(S)] = True
            cols = [ac[~ins[ata] & ins[atb]], ec[~ins[et] & ins[eu]], sc[ins[stt]]]
            for c in cols: ix += c.tolist(); vl += [1.0] * len(c)
            for j in self.cover_cols:
                c = self.sec_coef("cover", self.payload[j], S)
                if c: ix.append(j); vl.append(c)
            st.append(len(ix))
        if not new: return 0
        n = len(new)
        self.h.addRows(n, np.ones(n), np.full(n, highspy.kHighsInf), len(ix), np.array(st[:-1], np.int32), np.array(ix, np.int32), np.array(vl, float))
        for S in new: self.secs.append(S); self.sec_rows.append(self.nrow); self.nrow += 1
        return n

    def solve(self):
        t0 = time.time(); self.h.run()
        status = self.h.modelStatusToString(self.h.getModelStatus())
        sol = self.h.getSolution()
        self.x = np.array(sol.col_value); self.y = np.array(sol.row_dual); self.d = np.array(sol.col_dual)
        self.obj = self.h.getInfo().objective_function_value
        return status, time.time() - t0

    def sec_matrix(self, y=None):
        """M[t, u] = sum of duals of cuts S with t not in S, u in S"""
        y = self.y if y is None else y
        M = np.zeros((self.NT, self.NT))
        for S, rr in zip(self.secs, self.sec_rows):
            rho = y[rr]
            if abs(rho) < 1e-12: continue
            ins = np.zeros(self.NT, bool); ins[list(S)] = True
            M[np.ix_(~ins, ins)] += rho
        return M

    # ------------------------------------------------------------------ cover columns
    def cover_column(self, X, paths):
        """paths: list of lists of global options covering the trails of component X"""
        E = self.E; T = self.T
        cost = 0.0; tarcs = []
        for p in paths:
            for o, o2 in zip(p, p[1:]):
                cost += float(E[o, o2]); tarcs.append((int(T[o]), int(T[o2])))
        rows = [self.conv_row[X]] + [self.in_row[p[0]] for p in paths] + [self.out_row[p[-1]] for p in paths]
        vals = [1.0] + [-1.0] * (2 * len(paths))
        sig = (X, tuple(sorted(tuple(int(o) for o in p) for p in paths)))
        return sig, ("cover", dict(X=X, paths=[[int(o) for o in p] for p in paths], tarcs=tarcs), cost, rows, vals)

    def price_component(self, X, M, y=None):
        y = self.y if y is None else y
        trails = self.comps[X]; nt = len(trails)
        loc = np.concatenate([self.topts[t] for t in trails]); nl = len(loc)
        tl = np.concatenate([np.full(len(self.topts[t]), i) for i, t in enumerate(trails)])
        Tg = self.T[loc]
        Eh = self.E[np.ix_(loc, loc)].astype(np.float32)
        if np.abs(M).max() > 0: Eh -= M[np.ix_(Tg, Tg)].astype(np.float32)
        Eh[tl[:, None] == tl[None, :]] = INF
        din = y[self.in_row[loc]]; dout = y[self.out_row[loc]]
        alpha = y[self.conv_row[X]]
        nm = 1 << nt
        P = np.full((nm, nl), INF); Pp = np.full((nm, nl), -1, np.int32)
        P[1 << tl, np.arange(nl)] = din
        member = [np.nonzero((S >> tl) & 1)[0] for S in range(nm)]
        bst = np.concatenate([[0], np.cumsum([len(self.topts[t]) for t in trails])])   # trail i owns [bst[i], bst[i+1])
        for S in range(1, nm):
            ins = [i for i in range(nt) if (S >> i) & 1]
            if min(P[S, bst[i]:bst[i + 1]].min() for i in ins) >= INF / 2: continue
            for j in range(nt):
                if (S >> j) & 1: continue
                bj = slice(bst[j], bst[j + 1]); best = None; barg = None
                for i in ins:
                    v = P[S, bst[i]:bst[i + 1]]
                    if v.min() >= INF / 2: continue
                    Mm = v[:, None] + Eh[bst[i]:bst[i + 1], bj]
                    am = Mm.argmin(0); c = Mm[am, np.arange(Mm.shape[1])]
                    if best is None: best = c; barg = am + bst[i]
                    else:
                        w = c < best; best = np.where(w, c, best); barg = np.where(w, am + bst[i], barg)
                if best is None: continue
                S2 = S | (1 << j); cur = P[S2, bj]
                w = best < cur - 1e-12
                if w.any():
                    idx = np.arange(bst[j], bst[j + 1])[w]
                    P[S2, idx] = best[w]; Pp[S2, idx] = barg[w]
        Q = np.full(nm, INF); Qa = np.full(nm, -1)
        for S in range(1, nm):
            ii = member[S]; w = P[S, ii] + dout[ii]
            k = int(w.argmin()); Q[S] = w[k]; Qa[S] = ii[k]
        # cover DP by number of paths
        if not hasattr(self, "_pairs_cache"): self._pairs_cache = {}
        if nt in self._pairs_cache: self._pairs = self._pairs_cache[nt]
        else:
            Ss = []; Us = []
            for S in range(1, nm):
                low = S & -S; rest = S ^ low; sub = rest
                while True:
                    Ss.append(S); Us.append(sub | low)
                    if sub == 0: break
                    sub = (sub - 1) & rest
            Ss = np.array(Ss); Us = np.array(Us); order = np.argsort(Ss, kind="stable")
            Ss = Ss[order]; Us = Us[order]
            gst = np.concatenate([[0], np.nonzero(np.diff(Ss))[0] + 1])
            self._pairs = (nt, Ss, Us, gst); self._pairs_cache[nt] = self._pairs
        _, Ss, Us, gst = self._pairs
        full = nm - 1
        Cov = [None, Q.copy()]; Arg = [None, None]
        for r in range(2, nt + 1):
            prev = Cov[r - 1]; R = Ss ^ Us
            vals = np.where(R == 0, INF, Q[Us] + prev[R])
            gmin = np.minimum.reduceat(vals, gst)
            cur = np.full(nm, INF); cur[Ss[gst]] = gmin
            hit = np.nonzero(vals <= cur[Ss] + 1e-12)[0]
            _, first = np.unique(Ss[hit], return_index=True)
            arg = np.full(nm, -1); arg[Ss[hit[first]]] = hit[first]
            Cov.append(cur); Arg.append(arg)
        res = []
        def backtrack_paths(segs):
            paths = []
            for U in segs:
                j = int(Qa[U]); mask = U; path = [j]
                while Pp[mask, j] >= 0:
                    p = int(Pp[mask, j]); mask ^= (1 << int(tl[j])); j = p; path.append(j)
                assert mask == (1 << int(tl[j]))
                paths.append([int(loc[q]) for q in reversed(path)])
            return paths
        def rest_segs(S, lev):
            segs = []
            for l in range(lev, 0, -1):
                if l == 1: U = S
                else: U = int(Us[Arg[l][S]])
                segs.append(U); S ^= U
            return segs
        low = full & -full
        for r in range(1, nt + 1):
            val = Cov[r][full]
            if val >= INF / 2: continue
            if r == 1:
                res.append((1, val - alpha, backtrack_paths([full]))); continue
            # several first blocks U (containing the lowest trail), best completion each
            cands = []
            rest = full ^ low; sub = rest
            while True:
                U = sub | low
                if U != full:
                    v = Q[U] + Cov[r - 1][full ^ U]
                    if v < INF / 2: cands.append((v, U))
                if sub == 0: break
                sub = (sub - 1) & rest
            cands.sort()
            for v, U in cands[:self.multi]:
                if v - alpha >= -TOL and v != cands[0][0]: break
                res.append((r, v - alpha, backtrack_paths([U] + rest_segs(full ^ U, r - 1))))
        return res

    def rc_of_cover(self, X, paths, M, y=None):
        y = self.y if y is None else y
        E = self.E; T = self.T
        v = -y[self.conv_row[X]]
        for p in paths:
            v += y[self.in_row[p[0]]] + y[self.out_row[p[-1]]]
            for o, o2 in zip(p, p[1:]): v += float(E[o, o2]) - M[T[o], T[o2]]
        return v

    # ------------------------------------------------------------------ arcs
    def price_arcs(self, M, limit=40000):
        free = ~self.in_pool
        a = self.pool_a[free]; b = self.pool_b[free]
        rc = 2.0 - self.y[self.out_row[a]] - self.y[self.in_row[b]] - M[self.T[a], self.T[b]]
        neg = np.nonzero(rc < -TOL)[0]
        best = float(rc.min()) if len(rc) else 0.0
        if len(neg) > limit: neg = neg[np.argsort(rc[neg])[:limit]]
        idx = np.nonzero(free)[0][neg]
        self.in_pool[idx] = True
        items = [("arc", (int(x), int(z)), 2.0, [self.out_row[x], self.in_row[z]], [1.0, 1.0]) for x, z in zip(self.pool_a[idx], self.pool_b[idx])]
        return items, best, len(neg)

    # ------------------------------------------------------------------ cuts
    def separate(self):
        NT = self.NT; src = NT; cap = np.zeros((NT + 1, NT + 1)); T = self.T
        for j in np.nonzero(self.x > 1e-9)[0]:
            kind = self.kind[j]; p = self.payload[j]; v = self.x[j]
            if kind == "arc": cap[T[p[0]], T[p[1]]] += v
            elif kind == "else": cap[p[0], p[1]] += v
            elif kind == "s": cap[src, T[p]] += v
            elif kind == "cover":
                for (t, u) in p["tarcs"]: cap[t, u] += v
        G = nx.DiGraph()
        for i in range(NT + 1):
            for k in range(NT + 1):
                if cap[i, k] > 1e-9: G.add_edge(i, k, capacity=float(cap[i, k]))
        found = []
        for t in range(NT):
            if t not in G: found.append({t}); continue
            val, (reach, nonreach) = nx.minimum_cut(G, src, t)
            if val < 1 - 1e-6:
                S = {int(k) for k in nonreach if k != src}
                found.append(S)
        return found


def initial_covers(m, audit_path):
    d = json.load(open(audit_path))
    seq = [m.key[(r["trail"], r["version"], r["start"])] for r in d["table"]]
    E = m.E
    for i in range(1, len(seq)):
        assert int(E[seq[i - 1], seq[i]]) == d["table"][i]["e"], (i, int(E[seq[i - 1], seq[i]]), d["table"][i]["e"])
    out = {}
    for X, trails in m.comps.items():
        segs = []; cur = []
        for o in seq:
            if m.T[o] in trails: cur.append(o)
            elif cur: segs.append(cur); cur = []
        if cur: segs.append(cur)
        out[X] = segs
    return seq, out


def main():
    fam_p, E_p, audit_p = sys.argv[1], sys.argv[2], sys.argv[3]
    mode = sys.argv[4] if len(sys.argv) > 4 else "cc"
    max_iter = int(sys.argv[5]) if len(sys.argv) > 5 else 400
    out_p = sys.argv[6] if len(sys.argv) > 6 else None
    t0 = time.time()
    m = Master(fam_p, E_p, mode)
    seq, covers = initial_covers(m, audit_p)
    items = []
    for X, segs in covers.items():
        sig, it = m.cover_column(X, segs); m.cover_sigs.add(sig); items.append(it)
    if len(sys.argv) > 7:
        prev = json.load(open(sys.argv[7]))
        for c in prev["covers_used"]:
            if c["X"] in m.comps:
                sig, it = m.cover_column(c["X"], c["paths"])
                if sig not in m.cover_sigs: m.cover_sigs.add(sig); items.append(it)
        m.add_cols(items); items = []
        m.add_secs([set(S) for S in prev.get("secs", [])])
    m.add_cols(items)
    print(json.dumps(dict(event="built", mode=mode, cols=m.ncol(), rows=m.nrow, sec=round(time.time() - t0, 1))), flush=True)
    hist = []
    for it in range(max_iter):
        status, dt = m.solve()
        M = m.sec_matrix()
        if it == 0:   # dual sign convention check: our reduced costs must equal HiGHS col_dual
            dev = 0.0
            for j in m.cover_cols: dev = max(dev, abs(m.rc_of_cover(m.payload[j]["X"], m.payload[j]["paths"], M) - m.d[j]))
            for j in m.arc_cols[:2000]:
                a, b = m.payload[j]; dev = max(dev, abs(float(m.E[a, b]) - m.y[m.out_row[a]] - m.y[m.in_row[b]] - M[m.T[a], m.T[b]] - m.d[j]))
            print(json.dumps(dict(event="rc_check", max_dev=dev)), flush=True)
            assert dev < 1e-6
        arc_items, arc_best, n_arc = m.price_arcs(M)
        cov_items = []; best = {}
        for X in m.comps:
            res = m.price_component(X, M)
            best[X] = min(r[1] for r in res)
            for r, rc, paths in res:
                if rc < -TOL:
                    chk = m.rc_of_cover(X, paths, M)
                    assert abs(chk - rc) < 1e-3, (chk, rc)
                    if chk >= -TOL: continue
                    sig, item = m.cover_column(X, paths)
                    if sig in m.cover_sigs: continue
                    m.cover_sigs.add(sig); cov_items.append(item)
        lag = m.obj + sum(min(0.0, v) for v in best.values()) if n_arc == 0 else None
        rec = dict(it=it, status=status, lp=round(m.obj, 6), lagr=None if lag is None else round(lag, 6), solve_s=round(dt, 1),
                   arcs_added=n_arc, arc_rc=round(arc_best, 4), covers_added=len(cov_items),
                   cover_rc={str(X): round(v, 4) for X, v in best.items()}, secs=len(m.secs), cols=m.ncol(), t=round(time.time() - t0, 1))
        if arc_items or cov_items:
            m.add_cols(arc_items + cov_items)
        else:
            cuts = m.separate(); nadd = m.add_secs(cuts); rec["cuts_added"] = nadd
            if nadd == 0:
                rec["converged"] = True; print(json.dumps(rec), flush=True); hist.append(rec); break
        print(json.dumps(rec), flush=True); hist.append(rec)
    if out_p:
        used = [dict(X=m.payload[j]["X"], paths=m.payload[j]["paths"], x=float(m.x[j])) for j in range(m.ncol()) if m.kind[j] == "cover" and m.x[j] > 1e-7]
        np.savez_compressed(out_p.replace(".json", "_duals.npz"), y=m.y, in_row=m.in_row, out_row=m.out_row, eo_row=m.eo_row, ei_row=m.ei_row,
                            sel_trails=np.array(sorted(m.sel_row)), sel_rows=np.array([m.sel_row[t] for t in sorted(m.sel_row)]),
                            conv_X=np.array(sorted(m.conv_row)), conv_rows=np.array([m.conv_row[X] for X in sorted(m.conv_row)]),
                            s_row=m.s_row, t_row=m.t_row, sec_rows=np.array(m.sec_rows), comp=m.comp,
                            sec_sets=np.array([[1 if t in S else 0 for t in range(m.NT)] for S in m.secs], np.int8).reshape(-1, m.NT))
        json.dump(dict(mode=mode, final_lp=m.obj, converged=bool(hist and hist[-1].get("converged")), iters=len(hist), secs=[sorted(S) for S in m.secs],
                       covers_used=used, history=hist), open(out_p, "w"))


if __name__ == "__main__":
    main()
