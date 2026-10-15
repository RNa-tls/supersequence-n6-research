#!/usr/bin/env python3
"""Round M -- independent checker of the single-opening LP certificate (single_opening_lp.py).
Shares no code with the generator (own overlap function, own option and arc enumeration).

Model (every column in [0, 1]; the meaning of every column fixes its row coefficients):
  y_o  : option o = (trail, version, cut edge) chosen      select(t) +1, out(o) -1, in(o) -1
  z_a  : arc a = (o -> o'), trails differ, e(a) <= EMAX    out(o) +1, in(o') +1, X(t,t') +1;  cost e(a)
  h_o  : else-out of o                                    out(o) +1, hbal(t) +1
  r_o  : else-in of o                                     in(o) +1,  rbal(t) +1
  s_o  : o is the first piece                             in(o) +1,  start +1;  cost [cut(o) = 2]
  t_o  : o is the last piece                              out(o) +1, end +1, cut(S) +1 for S containing t
  F_tu : else arc t -> u                                  hbal(t) -1, rbal(u) -1, X(t,u) +1;  cost EMAX+1
  X_tu : trail-level arc                                  X(t,u) -1, cut(S) +1 if t in S, u not in S
Rows: select = 1, out = in = hbal = rbal = X = 0, start = end = 1, cut(S) >= 1.
Every single-opening word gives a 0/1 point of cost <= sum of its excesses (an arc with e > EMAX is
an else arc of cost EMAX + 1 <= e), so for any duals (cut duals >= 0) the value
  sum_rows dual * rhs + sum_cols min(rc, 0)
is a lower bound on sum_k e_k, and J >= 77 + ceil(bound).  Arithmetic: duals rounded to 2^-K, int64.
Also checked: both reference words (opening descriptions) are feasible 0/1 points of the model, with
objective = their sum of excesses, and every certificate cut holds for them.
usage: so_lp_check.py FAMILY.json CERT.npz [DESC.json ...]"""
import sys, json, itertools
import numpy as np

n = 8
def ov(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n

def main():
    fam = json.load(open(sys.argv[1])); z = np.load(sys.argv[2]); descs = sys.argv[3:]
    EMAX = int(z["emax"]); K = 20; sc = 1 << K
    T = len(fam["trails"])
    # options keyed by (trail, version, edge)
    key2o = {}; okeys = []; entry = []; exitp = []; cutw = []; otrail = []
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]):
            st = [tuple(int(c) for c in s[8 * i:8 * i + 8]) for i in range(len(s) // 8)]
            m = len(st)
            for k in range(m):
                prev = st[k - 1]; ex = (prev[7],) + prev[:7]
                key2o[(t, v, k)] = len(okeys); okeys.append((t, v, k)); entry.append(st[k]); exitp.append(ex)
                cutw.append(ov(ex, st[k])); otrail.append(t)
    NO = len(okeys)
    # map certificate rows (by key) to our option ids
    ck = [tuple(r) for r in z["option_keys"].tolist()]
    assert sorted(ck) == sorted(okeys), "option sets differ"
    perm = np.array([key2o[k] for k in ck])
    def remap(arr):
        out = np.zeros(NO); out[perm] = arr; return out
    D = lambda a: np.round(np.asarray(a, dtype=float) * sc).astype(np.int64)
    d_sel = D(z["d_sel"]); d_out = D(remap(z["d_out"])); d_in = D(remap(z["d_in"]))
    d_hb = D(z["d_hbal"]); d_rb = D(z["d_rbal"]); d_start = int(D(z["d_start"])); d_end = int(D(z["d_end"]))
    pairs = [tuple(p) for p in z["pairs"].tolist()]; d_X = dict(zip(pairs, D(z["d_X"]).tolist()))
    ptr = z["cuts_ptr"]; cl = z["cuts"]
    cuts = [set(cl[ptr[i]:ptr[i + 1]].tolist()) for i in range(len(ptr) - 1)]
    d_cut = np.maximum(D(z["d_cut"]), 0)
    assert all(1 <= len(S) <= T and all(0 <= t < T for t in S) for S in cuts)
    # cut contributions: for X_tu: sum over cuts with t in S, u not in S; for t_o: sum over cuts with t in S
    cutX = {p: 0 for p in pairs}; cutT = [0] * T
    for S, dv in zip(cuts, d_cut.tolist()):
        if dv == 0: continue
        for t in S:
            cutT[t] += dv
            for u in range(T):
                if u not in S: cutX[(t, u)] += dv
    total = 0
    total += int(d_sel.sum()) + d_start + d_end + int(d_cut.sum())          # rhs: select 1, start 1, end 1, cuts 1
    neg = 0
    # y_o: rc = 0 - (d_sel[t] - d_out[o] - d_in[o])
    for o in range(NO):
        rc = -(int(d_sel[otrail[o]]) - int(d_out[o]) - int(d_in[o])); neg += min(rc, 0)
        rc = -(int(d_out[o]) + int(d_hb[otrail[o]])); neg += min(rc, 0)                  # h_o
        rc = -(int(d_in[o]) + int(d_rb[otrail[o]])); neg += min(rc, 0)                   # r_o
        rc = (sc if cutw[o] == 2 else 0) - (int(d_in[o]) + d_start); neg += min(rc, 0)   # s_o
        rc = -(int(d_out[o]) + d_end + cutT[otrail[o]]); neg += min(rc, 0)               # t_o
    for (t, u) in pairs:
        rc = (EMAX + 1) * sc - (-int(d_hb[t]) - int(d_rb[u]) + d_X[(t, u)]); neg += min(rc, 0)   # F
        rc = -(-d_X[(t, u)] + cutX[(t, u)]); neg += min(rc, 0)                                      # X
    # z arcs: enumerate all arcs with e <= EMAX
    by_entry = {}
    for o in range(NO): by_entry.setdefault(entry[o], []).append(o)
    narcs = 0
    for a in range(NO):
        ex = exitp[a]
        for w in range(2, EMAX + 5):
            for p_ in itertools.permutations(ex[:w]):
                y = ex[w:] + p_
                if ov(ex, y) != w: continue
                for b in by_entry.get(y, []):
                    if otrail[b] == otrail[a]: continue
                    e = w - cutw[b] - 1
                    if e > EMAX: continue
                    narcs += 1
                    rc = e * sc - (int(d_out[a]) + int(d_in[b]) + d_X[(otrail[a], otrail[b])]); neg += min(rc, 0)
    bound_scaled = total + neg
    ceilb = -((-bound_scaled) // sc)
    res = dict(cert=sys.argv[2], emax=EMAX, options=NO, arcs=narcs, cuts=len(cuts), bound=bound_scaled / sc,
               sum_e_lb=int(ceilb), J_lb=77 + int(ceilb), L_lb=46085 + 77 + int(ceilb), negative_rc=neg / sc)
    # reference words: build the 0/1 point and check rows + cuts + objective
    refs = []
    for dp in descs:
        dsc = json.load(open(dp))["description"]
        seq = [key2o[(p[0], p[1], p[2])] for p in dsc]
        assert len(seq) == T and len({otrail[o] for o in seq}) == T, "not a single-opening word"
        es = []; okrows = True
        for a, b in zip(seq, seq[1:]):
            e = ov(exitp[a], entry[b]) - cutw[b] - 1
            es.append(e)
        obj = sum(min(e, EMAX + 1) if e > EMAX else e for e in es) + (1 if cutw[seq[0]] == 2 else 0)
        true = sum(es) + (1 if cutw[seq[0]] == 2 else 0)
        order = [otrail[o] for o in seq]
        pos = {t: i for i, t in enumerate(order)}
        viol = 0
        for S in cuts:
            # the path leaves S at least once: some consecutive pair (S -> not S) or the last trail in S
            leaves = any(order[i] in S and order[i + 1] not in S for i in range(T - 1)) or (order[-1] in S)
            viol += not leaves
        refs.append(dict(desc=dp, sum_e=true, model_objective=obj, J=77 + true, cuts_violated=viol,
                         bound_below_objective=(bound_scaled <= obj * sc)))
    res["references"] = refs
    print(json.dumps(res))

if __name__ == "__main__":
    main()
