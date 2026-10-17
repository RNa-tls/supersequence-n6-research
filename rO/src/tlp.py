#!/usr/bin/env python3
"""Round O (sections 3, 11-13) -- TRIPLE-CONSISTENT order LP (radius-1 option-order coupling).

The order-hull LP (oh_lp.py) mixes orders but lets option flows cross over between them: at a trail b
the LP may receive flow from b's predecessor in one order and send it to b's successor in another.
Here every option of every trail carries flow only along an actual consecutive triple of the mixed
orders:
    q^b_{a,o,c} >= 0      trail b uses option o with predecessor a and successor c
                          (a = S: b is first, start cost [cut(o) = 2]; c = E: b is last)
  (R1) for each consecutive triple (a, b, c) of the pool:   sum_o q^b_{a,o,c} = sum_pi lam_pi [abc in pi]
  (R2) for each adjacent pair (a, b) and option o' of b:    sum_{o in a} y_{o,o'} + ein_{a,o'} = sum_c q^b_{a,o',c}
  (R3) for each adjacent pair (a, b) and option o of a:     sum_{o' in b} y_{o,o'} + eout_{o,b} = sum_{a'} q^a_{a',o,b}
  (R4) else balance (a, b):  sum_o eout_{o,b} = sum_o' ein_{a,o'}      (else links cost 3 <= e)
  (R5) sum lam = 1
  objective: sum e y + 3 sum eout + sum_{q with a = S} [cut(o) = 2] q.
Every single-opening word is a 0/1 point (lam = its order); for one fixed order the LP is the exact
shortest-path LP.  With a restricted POOL of orders the value is an upper bound of the full
triple-consistent LP (a diagnostic: does radius-1 coupling block this mixture?).
usage: tlp.py FAMILY.json E.npy POOL.json OUT.json   (POOL: hull_test.json decomposition + 46185)"""
import sys, os, json, time
import numpy as np
import highspy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "rN", "src"))
import options as OP

S, EN = 30, 31


def build_and_solve(fam_p, E_p, pool, solver="ipm", verbose=False):
    fam, opts = OP.load(fam_p)
    E = np.load(E_p).astype(np.int64)
    T = np.array([o["t"] for o in opts]); cut = np.array([o["cut"] for o in opts])
    NT = 30; topts = [np.nonzero(T == t)[0] for t in range(NT)]
    tri = {}; pairs = {}
    lam_rows = []
    for p in pool:
        rows = []
        for i, b in enumerate(p):
            a = p[i - 1] if i else S; c = p[i + 1] if i + 1 < len(p) else EN
            if (a, b, c) not in tri: tri[(a, b, c)] = len(tri)
            rows.append(tri[(a, b, c)])
            if a != S and (a, b) not in pairs: pairs[(a, b)] = len(pairs)
        lam_rows.append(rows)
    nR1 = len(tri)
    # R2 rows: (pair, option of b); R3 rows: (pair, option of a)
    r2 = {}; r3 = {}; r = nR1
    for (a, b), k in pairs.items():
        for o in topts[b]: r2[(k, int(o))] = r; r += 1
    for (a, b), k in pairs.items():
        for o in topts[a]: r3[(k, int(o))] = r; r += 1
    r4 = {k: r + k for k in pairs.values()}; r += len(pairs)
    r5 = r; r += 1
    nrow = r
    cols_cost = []; cols_rows = []; cols_vals = []; kinds = []
    def add(cost, rows, vals, kind):
        cols_cost.append(cost); cols_rows.append(rows); cols_vals.append(vals); kinds.append(kind)
    for i, rows in enumerate(lam_rows):
        add(0.0, rows + [r5], [-1.0] * len(rows) + [1.0], ("lam", i))
    for (a, b, c), ti in tri.items():
        ka = pairs.get((a, b)); kc = pairs.get((b, c))
        for o in topts[b]:
            o = int(o); rows = [ti]; vals = [1.0]
            if a != S: rows.append(r2[(ka, o)]); vals.append(-1.0)
            if c != EN: rows.append(r3[(kc, o)]); vals.append(-1.0)
            add(float(cut[o] == 2) if a == S else 0.0, rows, vals, ("q", a, b, c, o))
    nq = len(kinds)
    for (a, b), k in pairs.items():
        sub = E[np.ix_(topts[a], topts[b])]
        ii, jj = np.nonzero(sub <= 2)
        for i_, j_ in zip(ii, jj):
            o, o2 = int(topts[a][i_]), int(topts[b][j_])
            add(float(sub[i_, j_]), [r2[(k, o2)], r3[(k, o)]], [1.0, 1.0], ("y", o, o2))
        for o in topts[a]:
            add(3.0, [r3[(k, int(o))], r4[k]], [1.0, 1.0], ("eout", k, int(o)))
        for o2 in topts[b]:
            add(0.0, [r2[(k, int(o2))], r4[k]], [1.0, -1.0], ("ein", k, int(o2)))
    ncol = len(kinds)
    lo = np.zeros(nrow); up = np.zeros(nrow); lo[r5] = up[r5] = 1.0
    st = np.zeros(ncol + 1, np.int64); st[1:] = np.cumsum([len(x) for x in cols_rows])
    ix = np.concatenate([np.array(x, np.int32) for x in cols_rows]); vl = np.concatenate([np.array(x, float) for x in cols_vals])
    h = highspy.Highs(); h.setOptionValue("output_flag", verbose); h.setOptionValue("solver", solver)
    h.setOptionValue("threads", 2)
    lp = highspy.HighsLp(); lp.num_col_ = ncol; lp.num_row_ = nrow
    lp.col_cost_ = np.array(cols_cost); lp.col_lower_ = np.zeros(ncol); lp.col_upper_ = np.full(ncol, highspy.kHighsInf)
    lp.row_lower_ = lo; lp.row_upper_ = up
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = st.astype(np.int32); lp.a_matrix_.index_ = ix; lp.a_matrix_.value_ = vl
    h.passModel(lp)
    t0 = time.time(); h.run()
    status = h.modelStatusToString(h.getModelStatus())
    sol = np.array(h.getSolution().col_value)
    obj = h.getInfo().objective_function_value
    lam = [(i, float(sol[i])) for i in range(len(pool)) if sol[i] > 1e-9]
    return dict(status=status, obj=obj, sec=round(time.time() - t0, 1), rows=nrow, cols=ncol, triples=nR1, pairs=len(pairs), q_vars=nq - len(pool),
                lam=lam)


def main():
    fam_p, E_p, pool_p, out = sys.argv[1:5]
    d = json.load(open(pool_p))
    pool = [x["order"] for x in (d["decomposition"] if "decomposition" in d else d["orders"])]
    if len(sys.argv) > 5:                       # optional second pool file (union)
        d2 = json.load(open(sys.argv[5])); pool += [x["order"] for x in (d2["decomposition"] if "decomposition" in d2 else d2["orders"])]
    seen = set(); pool = [p for p in pool if not (tuple(p) in seen or seen.add(tuple(p)))]
    a = json.load(open(os.path.join(HERE, "..", "..", "rN", "certs", "audit_superperm8_46185.json")))
    b0 = [r["trail"] for r in a["table"]]
    if tuple(b0) not in seen: pool.append(b0)
    res = build_and_solve(fam_p, E_p, pool)
    res["pool"] = len(pool)
    res["lam_orders"] = [dict(idx=i, lam=v, order=pool[i]) for i, v in res.pop("lam")]
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "lam_orders"}))
    print(json.dumps([(x["idx"], round(x["lam"], 4)) for x in res["lam_orders"]]))


if __name__ == "__main__":
    main()
