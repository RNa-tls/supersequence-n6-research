#!/usr/bin/env python3
"""Round T -- the ladder lemma (Round S, S1.4) re-checked on a family given as cyclic trail words (public selection or
old family, one version).  Same definition as rR/src/ladders_check.py; m = 2, 4, 6 exhaustively.
usage: ladders_public.py (old FAMILY.json | new SEL TSV BASE) OUT.json"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model, slice_structure as SS
a = sys.argv[1:]; outp = a[-1]
cyc = [SS.expand(t["versions"][0]) for t in json.load(open(a[1]))["trails"]] if a[0] == "old" else model.load(*a[1:4])
ent = []; tr = []; idx = []; cnat = []; tlen = []
for t, c in enumerate(cyc):
    rs = model.runs_of(c); d = c + c; tlen.append(len(rs))
    for i, r in enumerate(rs): ent.append([int(ch) for ch in d[r[0]:r[0] + 8]]); tr.append(t); idx.append(i); cnat.append(r[2])
S = np.array(ent, np.int64); N = len(S); T = np.array(tr); cnat = np.array(cnat); tofs = np.concatenate([[0], np.cumsum(tlen)])
X = np.concatenate([S[:, 7:], S[:, :7]], 1); W = np.full((N, N), 8, np.int16)
for k in range(7, 0, -1):
    A = (X[:, k:] * (8 ** np.arange(8 - k))).sum(1); B = (S[:, :8 - k] * (8 ** np.arange(8 - k))).sum(1)
    o = np.argsort(B, kind="stable"); Bs = B[o]; lo = np.searchsorted(Bs, A, "left"); hi = np.searchsorted(Bs, A, "right")
    for i in np.nonzero(hi > lo)[0]: W[i, o[lo[i]:hi[i]]] = k
np.fill_diagonal(W, 8)
succ = np.array([tofs[T[i]] + (idx[i] + 1) % tlen[T[i]] for i in range(N)]); pred = np.empty(N, np.int64); pred[succ] = np.arange(N)
cut = cnat[pred].astype(np.int16)                                # c(d): weight of the natural link into run d
wrapR = {}
for y in range(N):
    if cut[y] != 3: continue
    ch = [y]
    while cnat[ch[-1]] == 2 and len(ch) < 8: ch.append(int(succ[ch[-1]]))
    if len(ch) == 7 and cnat[ch[-1]] == 3: wrapR[int(succ[ch[-1]])] = y      # l = succ(D_6), r = D_0
def tight_right(l): return [("s", int(pred[l]))] + ([("w", wrapR[l])] if l in wrapR else [])
out = dict(runs=int(N), trails=len(cyc), full_chains=len(wrapR))
for k in (1, 2, 3):
    sides = []
    for t0 in range(N):
        stack = [([t0], "")]
        while stack:
            cs, ty = stack.pop()
            if len(cs) == k + 1:
                if len(set(cs)) == k + 1: sides.append(cs)
                continue
            for (typ, r) in tight_right(cs[-1]): stack.append((cs + [r], ty + typ))
    C = np.array(sides, np.int64); trs = T[C[:, 0]]; tot = 0; worst = -10 ** 9; zero = 0; nS = len(sides)
    sumcS = cut[C[:, :k]].sum(1); sumcT = cut[C[:, 1:]].sum(1)
    for i0 in range(0, nS, 256):
        Ti = C[i0:i0 + 256]; d = W[pred[Ti[:, 0]]][:, C[:, k]].astype(np.int32) + sumcS[None, :] + sumcT[i0:i0 + 256, None]
        for q in range(k):
            d -= W[pred[Ti[:, q]]][:, C[:, q]]; d -= W[pred[C[:, q]]][:, Ti[:, q + 1]].T
        d -= W[pred[Ti[:, k]]][:, C[:, k]]
        ok = trs[i0:i0 + 256, None] != trs[None, :]; tot += int(ok.sum()); dd = d[ok]
        if dd.size: worst = max(worst, int(dd.max())); zero += int((dd == 0).sum())
    out["m%d" % (2 * k)] = dict(sides=nS, ladders=tot, max_delta=worst, delta_zero=zero); print("m =", 2 * k, out["m%d" % (2 * k)], flush=True)
out["ladder_lemma_holds"] = all(v["max_delta"] <= 0 for v in out.values() if isinstance(v, dict))
json.dump(out, open(outp, "w"), indent=1)
