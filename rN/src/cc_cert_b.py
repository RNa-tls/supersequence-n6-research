#!/usr/bin/env python3
"""Round N (section 3, checker B) -- independent re-check of a CC-LP dual certificate.

Independent of cc_cert.py / options.py / Efull.npy:
  * options and the excess e(o -> o') are rebuilt from the family JSON with a different overlap
    computation (base-8 codes compared by broadcasting, largest overlap wins);
  * the cover minimum is computed BACKWARDS (paths grown at their start) and the cover recursion
    splits off the block containing the HIGHEST trail;
  * the arc group minimum is computed head-block-wise and reduced to tails with minimum.at.
Same integer scale 2^30 and the same column groups as checker A, so the two lower bounds must be
identical integers.
usage: cc_cert_b.py FAMILY.json DUALS.npz MODE [key=y_best]"""
import sys, json
from fractions import Fraction
import numpy as np

C1 = [2, 3, 4, 5, 6, 7, 23, 24, 25, 26, 27]
C2 = [9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21]
AT = [1, 8, 15, 22, 28, 29]
SC = 1 << 30
BIG = np.int64(1) << 60
n = 8


def build(fam_path):
    fam = json.load(open(fam_path))
    T = []; cut = []; ent = []; ext = []
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]):
            runs = [[int(c) for c in s[8 * k:8 * k + 8]] for k in range(len(s) // 8)]
            for k in range(len(runs)):
                p = runs[k - 1]; x = [p[7]] + p[:7]          # last permutation of the previous run
                T.append(t); ent.append(runs[k]); ext.append(x)
    ent = np.array(ent, np.int64); ext = np.array(ext, np.int64)
    return np.array(T), ent, ext


def codes(A, lo, hi):
    c = np.zeros(len(A), np.int64)
    for i in range(lo, hi): c = c * 8 + A[:, i]
    return c


def weights(X, Y):
    """W[i, j] = smallest k >= 1 with X[i][k:] == Y[j][:8-k], else 8"""
    W = np.full((len(X), len(Y)), n, np.int8)
    for k in range(n - 1, 0, -1):
        sx = codes(X, k, n); py = codes(Y, 0, n - k)
        W[sx[:, None] == py[None, :]] = k
    return W


def excess(ext, ent, T):
    NO = len(T)
    cutw = np.array([weights(ext[i:i + 1], ent[i:i + 1])[0, 0] for i in range(NO)], np.int64)
    E = np.empty((NO, NO), np.int16)
    for lo in range(0, NO, 2048):
        hi = min(NO, lo + 2048)
        E[lo:hi] = weights(ext[lo:hi], ent).astype(np.int16) - cutw[None, :] - 1
    E[T[:, None] == T[None, :]] = 99
    return E, cutw


def cover_min_backward(Eloc, tl, din, dout, nt):
    nm = 1 << nt; nl = len(tl)
    R = np.full((nm, nl), BIG, np.int64)
    R[1 << tl, np.arange(nl)] = dout
    member = [np.nonzero((S >> tl) & 1)[0] for S in range(nm)]
    for S in range(1, nm):
        ii = member[S]; v = R[S, ii]                   # best path covering S starting at option ii
        if v.min() >= BIG // 2: continue
        oo = np.nonzero(((S >> tl) & 1) == 0)[0]
        if len(oo) == 0: continue
        cand = (Eloc[np.ix_(oo, ii)] + v[None, :]).min(1)
        np.minimum.at(R, (S | (1 << tl[oo]), oo), cand)
    Q = np.array([BIG] + [int((R[S, member[S]] + din[member[S]]).min()) for S in range(1, nm)], np.int64)
    Cov = np.full(nm, BIG, np.int64); Cov[0] = 0
    for S in range(1, nm):
        top = 1 << (S.bit_length() - 1); rest = S ^ top; sub = rest; best = BIG
        while True:
            U = sub | top
            best = min(best, int(Q[U] + Cov[S ^ U]))
            if sub == 0: break
            sub = (sub - 1) & rest
        Cov[S] = best
    return int(Cov[nm - 1])


def main():
    fam_p, d_p, mode = sys.argv[1:4]
    key = sys.argv[4] if len(sys.argv) > 4 else "y_best"
    T, ent, ext = build(fam_p)
    E, cutw = excess(ext, ent, T)
    NO = len(T); NT = int(T.max()) + 1
    comp = np.zeros(NT, int); comps = {}
    if mode in ("cc", "cca"): comp[C1] = 1; comp[C2] = 2; comps = {1: C1, 2: C2}
    if mode == "cca": comp[AT] = 3; comps[3] = AT
    D = np.load(d_p); y = D[key].astype(float)
    free = [t for t in range(NT) if comp[t] == 0]
    base = 2 * NO + len(free) + 2 * NT + len(comps) + 2
    sec = D["sec_sets"].astype(bool).reshape(-1, NT); ns = len(sec)
    if len(y) < base + ns: y = np.concatenate([y, np.zeros(base + ns - len(y))])
    Y = np.round(y * SC).astype(np.int64)
    yin = Y[:NO]; yout = Y[NO:2 * NO]; r = 2 * NO
    ysel = {t: Y[r + i] for i, t in enumerate(free)}; r += len(free)
    yeo = Y[r:r + NT]; r += NT
    yei = Y[r:r + NT]; r += NT
    yconv = {X: Y[r + i] for i, X in enumerate(sorted(comps))}; r += len(comps)
    ys, yt = Y[r], Y[r + 1]; r += 2
    rho = np.maximum(Y[r:r + ns], 0)
    M = np.zeros((NT, NT), np.int64)
    for S, rv in zip(sec, rho): M += rv * np.outer(~S, S)
    ok_tt = (comp[:, None] != comp[None, :]) | (comp[:, None] == 0)
    np.fill_diagonal(ok_tt, False)
    total = int(sum(ysel.values())) + int(sum(yconv.values())) + int(ys) + int(yt) + int(rho.sum())
    # arcs: head blocks, reduce to tails
    g = np.zeros(NO, np.int64)
    for lo in range(0, NO, 1024):
        b = np.arange(lo, min(NO, lo + 1024))
        Eb = E[:, b].astype(np.int64)
        okb = (Eb <= 2) & ok_tt[:, T[b]][T]
        d = Eb * SC - yout[:, None] - yin[b][None, :] - M[:, T[b]][T]
        d = np.where(okb, d, 0)
        g = np.minimum(g, d.min(1))
    corr = int(g.sum())
    de = 3 * SC + yeo[:, None] + yei[None, :] - M
    corr += int(np.where(ok_tt, de, 0).min(1).clip(max=0).sum())
    corr += int(np.minimum(0, -yout - yeo[T]).sum()) + int(np.minimum(0, -yin - yei[T]).sum())
    secsum = (rho[:, None] * sec).sum(0)
    corr += int(min(0, ((3 - cutw) * SC - yin - ys - secsum[T]).min())) + int(min(0, (-yout - yt).min()))
    for t in free:
        oo = np.nonzero(T == t)[0]; corr += int(min(0, (-ysel[t] + yin[oo] + yout[oo]).min()))
    det = {}
    for X in sorted(comps):
        trails = comps[X]
        loc = np.concatenate([np.nonzero(T == t)[0] for t in trails])
        tl = np.concatenate([np.full(int((T == t).sum()), i) for i, t in enumerate(trails)])
        Eloc = E[np.ix_(loc, loc)].astype(np.int64) * SC - M[np.ix_(T[loc], T[loc])]
        Eloc[tl[:, None] == tl[None, :]] = BIG
        cm = cover_min_backward(Eloc, tl, yin[loc], yout[loc], len(trails)) - int(yconv[X])
        det[str(X)] = cm; corr += min(0, cm)
    total += corr
    LB = Fraction(total, SC)
    print(json.dumps(dict(checker="B", mode=mode, key=key, scaled_total=total, cover_rc_min=det, lower_bound=str(LB), lower_bound_float=float(LB))))


if __name__ == "__main__":
    main()
