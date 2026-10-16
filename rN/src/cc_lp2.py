#!/usr/bin/env python3
"""Round N (section 3) -- stabilised column generation for the CC-LP (Wentges smoothing) with an
exact Lagrangian lower bound at every step.

For ANY dual vector y with y >= 0 on the cut rows, L(y) = b^T y + (sum of group corrections) is a valid
lower bound on the master LP with the current cuts, hence on [c0 = 2] + sum e of every single-opening
word:  c^T x = y^T A x + d^T x >= b^T y + sum_j d_j x_j, and the columns are grouped so that the x of
each group sums to at most 1 (explicit arcs by tail option, else arcs by tail trail, eout/ein per
option, s and t globally, z per free trail, covers per component); the cover minimum comes from the
exact subset DP.
usage: cc_lp2.py FAMILY.json E.npy AUDIT.json MODE OUT.json [alpha] [max_iter] [resume.json]"""
import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc_lp as CC

TOL = CC.TOL


def lagrangian(m, y, cover_rc_min):
    T = m.T; M = m.sec_matrix(y); NO = m.NO
    b = sum(y[rr] for rr in m.sel_row.values()) + sum(y[rr] for rr in m.conv_row.values()) + y[m.s_row] + y[m.t_row]
    b += sum(y[rr] for rr in m.sec_rows)
    corr = {}
    d = m.all_e - y[m.out_row[m.all_a]] - y[m.in_row[m.all_b]] - M[T[m.all_a], T[m.all_b]]
    g = np.zeros(NO); np.minimum.at(g, m.all_a, d); corr["arc"] = g.sum()
    et = np.array(m.else_t); eu = np.array(m.else_u)
    de = CC.ELSE_COST + y[m.eo_row[et]] + y[m.ei_row[eu]] - M[et, eu]
    ge = np.zeros(m.NT); np.minimum.at(ge, et, de); corr["else"] = ge.sum()
    corr["eout"] = np.minimum(0, -y[m.out_row] - y[m.eo_row[T]]).sum()
    corr["ein"] = np.minimum(0, -y[m.in_row] - y[m.ei_row[T]]).sum()
    secsum = np.zeros(m.NT)
    for S, rr in zip(m.secs, m.sec_rows): secsum[list(S)] += y[rr]
    corr["s"] = min(0.0, ((3 - m.cut) - y[m.in_row] - y[m.s_row] - secsum[T]).min())
    corr["t"] = min(0.0, (-y[m.out_row] - y[m.t_row]).min())
    cz = 0.0
    for t, rr in m.sel_row.items():
        oo = m.topts[t]; cz += min(0.0, (-y[rr] + y[m.in_row[oo]] + y[m.out_row[oo]]).min())
    corr["z"] = cz
    corr["cover"] = sum(min(0.0, v) for v in cover_rc_min.values())
    return b + sum(corr.values()), corr


def main():
    fam_p, E_p, audit_p, mode, out_p = sys.argv[1:6]
    alpha = float(sys.argv[6]) if len(sys.argv) > 6 else 0.8
    max_iter = int(sys.argv[7]) if len(sys.argv) > 7 else 3000
    t0 = time.time()
    m = CC.Master(fam_p, E_p, mode)
    seq, covers = CC.initial_covers(m, audit_p)
    items = []
    for X, segs in covers.items():
        sig, it = m.cover_column(X, segs); m.cover_sigs.add(sig); items.append(it)
    # all-singleton covers: cover j puts every trail of X alone with its j-th option (gives every option a column)
    for X, trails in m.comps.items():
        nmax = max(len(m.topts[t]) for t in trails)
        for j in range(nmax):
            paths = [[int(m.topts[t][j % len(m.topts[t])])] for t in trails]
            sig, it = m.cover_column(X, paths)
            if sig not in m.cover_sigs: m.cover_sigs.add(sig); items.append(it)
    # isolating covers: all singletons with the 46185 reference options, except one trail that uses option o
    ref = {}
    for o in seq: ref[int(m.T[o])] = int(o)
    for X, trails in m.comps.items():
        for t in trails:
            for o in m.topts[t]:
                paths = [[int(o)] if u == t else [ref[u]] for u in trails]
                sig, it = m.cover_column(X, paths)
                if sig not in m.cover_sigs: m.cover_sigs.add(sig); items.append(it)
    m.add_cols(items)
    if len(sys.argv) > 8:
        prev = json.load(open(sys.argv[8])); items = []
        for c in prev.get("covers_used", []):
            if c["X"] in m.comps:
                sig, it = m.cover_column(c["X"], c["paths"])
                if sig not in m.cover_sigs: m.cover_sigs.add(sig); items.append(it)
        m.add_cols(items); m.add_secs([set(S) for S in prev.get("secs", [])])
    print(json.dumps(dict(event="built", mode=mode, cols=m.ncol(), rows=m.nrow, sec=round(time.time() - t0, 1))), flush=True)
    center = None; Lbest = -1e18; best_y = None; hist = []
    for it in range(max_iter):
        status, dt = m.solve()
        yin = m.y.copy(); z = m.obj
        if center is None: center = yin.copy()
        elif len(center) < len(yin): center = np.concatenate([center, np.zeros(len(yin) - len(center))])
        Min = m.sec_matrix(yin)
        a = alpha; new_items = []; npr = 0
        while True:
            ysep = a * center + (1 - a) * yin
            Msep = Min if a == 0 else m.sec_matrix(ysep)
            cmin = {}; npr += 1
            for X in m.comps:
                res = m.price_component(X, Msep, ysep)
                cmin[X] = min(r[1] for r in res)
                for r, rc, paths in res:
                    rin = rc if a == 0 else m.rc_of_cover(X, paths, Min, yin)
                    if a == 0: rin = m.rc_of_cover(X, paths, Min, yin)
                    if rin < -TOL:
                        sig, item = m.cover_column(X, paths)
                        if sig not in m.cover_sigs: m.cover_sigs.add(sig); new_items.append(item)
            L, corr = lagrangian(m, ysep, cmin)
            if L > Lbest: Lbest = L; center = ysep.copy(); best_y = ysep.copy()
            arc_items, arc_best, n_arc = m.price_arcs(Min)
            new_items += arc_items
            if new_items or a == 0: break
            a = 0.0 if a < 0.1 else a / 2
        rec = dict(it=it, status=status, lp=round(z, 6), L=round(Lbest, 6), gap=round(z - Lbest, 6), alpha_used=a, pricings=npr,
                   added=len(new_items), cover_rc={str(X): round(v, 4) for X, v in cmin.items()}, secs=len(m.secs), cols=m.ncol(),
                   solve_s=round(dt, 1), t=round(time.time() - t0, 1))
        if it % 20 == 19:
            ck = [dict(X=m.payload[j]["X"], paths=m.payload[j]["paths"], x=float(m.x[j])) for j in range(m.ncol()) if m.kind[j] == "cover" and m.x[j] > 1e-7]
            json.dump(dict(covers_used=ck, secs=[sorted(S) for S in m.secs], it=it, lp=z, Lbest=Lbest), open(out_p.replace(".json", "_ckpt.json"), "w"))
        if new_items:
            m.add_cols(new_items); print(json.dumps(rec), flush=True); hist.append(rec); continue
        cuts = m.separate(); nadd = m.add_secs(cuts); rec["cuts_added"] = nadd
        print(json.dumps(rec), flush=True); hist.append(rec)
        if nadd == 0:
            rec["converged"] = True; break
        center = np.concatenate([center, np.zeros(m.nrow - len(center))]) if len(center) < m.nrow else center
    used = [dict(X=m.payload[j]["X"], paths=m.payload[j]["paths"], x=float(m.x[j])) for j in range(m.ncol()) if m.kind[j] == "cover" and m.x[j] > 1e-7]
    json.dump(dict(mode=mode, final_lp=m.obj, Lbest=Lbest, converged=bool(hist and hist[-1].get("converged")), iters=len(hist),
                   secs=[sorted(S) for S in m.secs], covers_used=used, history=hist), open(out_p, "w"))
    np.savez_compressed(out_p.replace(".json", "_duals.npz"), y_best=best_y if best_y is not None else m.y, y_last=m.y,
                        sec_sets=np.array([[1 if t in S else 0 for t in range(m.NT)] for S in m.secs], np.int8).reshape(-1, m.NT),
                        sec_rows=np.array(m.sec_rows), comp=m.comp)


if __name__ == "__main__":
    main()
