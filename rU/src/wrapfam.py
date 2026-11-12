#!/usr/bin/env python3
"""Round U -- wrap families of the public 16-trail selection (run level).
A route that uses the wrap C6 -> C0 of a complete chain C is a wrap-free route of the family F_C in which C is a closed
trail of its own (natural links C_i -> C_{i+1} and the wrap, all of weight 2) and the host trail t' = t - C has the
skip link Q_end -> N0 (weight 3 + 1) as a natural link.  The natural weights sum to the same total, so
L = 46149 + J with J = sum over cuts (3 - c) + sum over joins (w - 3) as before.
 wrapfam.py base  SEL TSV BASE WORK            : W.npy, run tables, chains and their orbits, base run-level arcs
 wrapfam.py fam   SEL TSV BASE WORK CHAIN OUT  : arcs of F_C (trail 0 = C, wrap not cut) and the checks of the facts
                                                  behind Theorem S1 in F_C (JSON on stdout)"""
import sys, os, json, itertools
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rT", "src"))
import model
def base_tables(selp, tsvp, basep, work):
    cyc = model.load(selp, tsvp, basep); ent = []; tr = []; idx = []; cnat = []; tlen = []
    for t, c in enumerate(cyc):
        rs = model.runs_of(c); d = c + c; tlen.append(len(rs))
        for i, r in enumerate(rs): ent.append(d[r[0]:r[0] + 8]); tr.append(t); idx.append(i); cnat.append(r[2])
    n = len(ent); tr = np.array(tr); idx = np.array(idx); cnat = np.array(cnat); tofs = np.concatenate([[0], np.cumsum(tlen)])
    succ = np.array([tofs[tr[i]] + (idx[i] + 1) % tlen[tr[i]] for i in range(n)]); pred = np.empty(n, np.int64); pred[succ] = np.arange(n)
    wp = os.path.join(work, "W.npy")
    if os.path.exists(wp): W = np.load(wp)
    else:
        S = np.array([[int(ch) for ch in e] for e in ent], np.int64); X = np.concatenate([S[:, 7:], S[:, :7]], 1); W = np.full((n, n), 8, np.int8)
        for k in range(7, 0, -1):
            A = (X[:, k:] * (8 ** np.arange(8 - k))).sum(1); B = (S[:, :8 - k] * (8 ** np.arange(8 - k))).sum(1)
            o = np.argsort(B, kind="stable"); Bs = B[o]; lo = np.searchsorted(Bs, A, "left"); hi = np.searchsorted(Bs, A, "right")
            for i in np.nonzero(hi > lo)[0]: W[i, o[lo[i]:hi[i]]] = k
        np.fill_diagonal(W, 8); np.save(wp, W)
    assert (W[np.arange(n), succ] == cnat).all()
    return ent, tr, cnat, succ, pred, W
def chains_of(cnat, succ, pred):
    cut = cnat[pred]; out = []
    for y in range(len(cnat)):
        if cut[y] < 3: continue
        ch = [y]
        while cnat[ch[-1]] == 2 and len(ch) < 8: ch.append(int(succ[ch[-1]]))
        if len(ch) == 7 and cnat[ch[-1]] >= 3: out.append(ch)
    return out
def write_arcs(path, ent, tr, cnat, succ, pred, order, skip=()):
    """one arc per run y (cut at the natural link into y): trail, y, 0, 3 - c, first 7 letters of y, last 7 of pred(y)"""
    cut = cnat[pred]; ren = {t: i for i, t in enumerate(order)}; rows = []
    for y in range(len(ent)):
        if y in skip: continue
        rows.append((ren[int(tr[y])], y, 0, 3 - int(cut[y]), ent[y][:7], ent[int(pred[y])][:7]))
    rows.sort(); open(path, "w").write("".join("%d %d %d %d %s %s\n" % r for r in rows)); return len(rows)
if __name__ == "__main__":
    mode, selp, tsvp, basep, work = sys.argv[1:6]; os.makedirs(work, exist_ok=True)
    ent, tr, cnat, succ, pred, W = base_tables(selp, tsvp, basep, work); n = len(ent); chains = chains_of(cnat, succ, pred)
    if mode == "base":
        na = write_arcs(os.path.join(work, "base_arcs.txt"), ent, tr, cnat, succ, pred, list(range(16)))
        # orbits of chains under the letter relabelings that fix the selection (Klein four-group found in Round T)
        pos = {e: i for i, e in enumerate(ent)}; G = ["01234567", "01543267", "10243567", "10534267"]; start = {ch[0]: i for i, ch in enumerate(chains)}
        maps = []
        for g in G:
            mp = dict(zip("01234567", g)); im = [pos.get("".join(mp[c] for c in e), -1) for e in ent]; assert min(im) >= 0, "not an automorphism of the run set"
            im = np.array(im); assert (im[succ] == succ[im]).all(); maps.append(im)
        seen = set(); reps = []
        for i, ch in enumerate(chains):
            if i in seen: continue
            orb = {start[int(m[ch[0]])] for m in maps}; seen |= orb; reps.append(dict(chain=i, first_run=int(ch[0]), trail=int(tr[ch[0]]), orbit=sorted(orb)))
        json.dump(dict(runs=n, arcs=na, chains=len(chains), chains_by_trail_kind=dict(D=sum(1 for ch in chains if tr[ch[0]] < 12), W=sum(1 for ch in chains if tr[ch[0]] >= 12)),
                       orbits=len(reps), orbit_sizes=sorted({len(r["orbit"]) for r in reps}), representatives=reps), open(os.path.join(work, "chains.json"), "w"), indent=0)
        print("runs", n, "arcs", na, "chains", len(chains), "orbits", len(reps), "sizes", sorted({len(r["orbit"]) for r in reps}))
    else:
        ci = int(sys.argv[6]); outp = sys.argv[7]; C = chains[ci]; C0, C6 = C[0], C[6]; Q = int(pred[C0]); N0 = int(succ[C6])
        tr2 = tr.copy(); succ2 = succ.copy(); cn2 = cnat.copy()
        tr2[C] = 16; succ2[C6] = C0; cn2[C6] = 2; succ2[Q] = N0; cn2[Q] = int(W[Q, N0])
        pred2 = np.empty(n, np.int64); pred2[succ2] = np.arange(n); cut2 = cn2[pred2]
        assert (W[np.arange(n), succ2] == cn2).all()
        order = [16] + list(range(16)); na = write_arcs(outp, ent, tr2, cn2, succ2, pred2, order, skip={C0})
        # ---- facts behind S1 in F_C
        natural = np.zeros((n, n), bool); natural[np.arange(n), succ2] = True; same = tr2[:, None] == tr2[None, :]
        w2 = (W <= 2) & ~natural & ~np.eye(n, dtype=bool); xs, ys = np.nonzero(w2)
        ch2 = chains_of(cn2, succ2, pred2); wrapR = {int(succ2[ch[-1]]): ch[0] for ch in ch2}
        wrapset = {(ch[-1], ch[0]) for ch in ch2}; other = [(int(x), int(y)) for x, y in zip(xs, ys) if (int(x), int(y)) not in wrapset]
        E = W.astype(np.int16) - cut2[None, :] - 1; cross = ~same; neg = np.nonzero((E < 0) & cross)
        negl = sorted({(int(y), int(E[x, y])) for x, y in zip(*neg)})
        # ladders, never deleting N0 (the gap cut is kept: it is in the spanning tree)
        def tight_right(l): return [int(pred2[l])] + ([wrapR[l]] if l in wrapR else [])
        lad = {}
        Wi = W.astype(np.int16)
        for k in (1, 2):
            sides = []
            for t0 in range(n):
                stack = [[t0]]
                while stack:
                    cs = stack.pop()
                    if len(cs) == k + 1:
                        if len(set(cs)) == k + 1: sides.append(cs)
                        continue
                    for r in tight_right(cs[-1]): stack.append(cs + [r])
            Cm = np.array(sides, np.int64); okT = ~(Cm[:, 1:] == N0).any(1); okS = ~(Cm[:, :k] == N0).any(1); trs = tr2[Cm[:, 0]]
            sumcS = cut2[Cm[:, :k]].sum(1); sumcT = cut2[Cm[:, 1:]].sum(1); worst = -99; tot = 0
            for i0 in range(0, len(sides), 512):
                Ti = Cm[i0:i0 + 512]; d = Wi[pred2[Ti[:, 0]]][:, Cm[:, k]].astype(np.int32) + sumcS[None, :] + sumcT[i0:i0 + 512, None]
                for q in range(k):
                    d -= Wi[pred2[Ti[:, q]]][:, Cm[:, q]]; d -= Wi[pred2[Cm[:, q]]][:, Ti[:, q + 1]].T
                d -= Wi[pred2[Ti[:, k]]][:, Cm[:, k]]
                ok = (trs[i0:i0 + 512, None] != trs[None, :]) & okT[i0:i0 + 512, None] & okS[None, :]; tot += int(ok.sum())
                if ok.any(): worst = max(worst, int(d[ok].max()))
            lad["m%d" % (2 * k)] = dict(ladders=tot, max_delta=worst)
        print(json.dumps(dict(chain=ci, C0=int(C0), host=int(tr[C0]), skip_weight=int(W[Q, N0]), arcs=na, other_wraps=len(ch2), non_natural_w_le2_not_wraps=len(other),
                              cross_trail_negative_e_heads=negl[:6], cross_trail_negative_e_only_into_N0=all(y == N0 for y, _ in negl), N0=N0, ladders=lad,
                              facts_ok=(len(other) == 0 and all(y == N0 for y, _ in negl) and all(v["max_delta"] <= 0 for v in lad.values())))))
