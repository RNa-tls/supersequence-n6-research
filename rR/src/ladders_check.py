#!/usr/bin/env python3
"""Round S -- second implementation (numpy) of the ladder lemma check of rR/csrc/ladders.c, for m = 2 and m = 4.
A ladder d_0, d_1, ..., d_{m+1}: even-indexed cuts in trail T, odd-indexed in another trail S, (d_{i-1}, d_{i+1}) a tight
pair (singleton: d_{i-1} = succ(d_{i+1}); wrap: d_{i-1} = succ(D_6), d_{i+1} = D_0 for a full chain D).  Deleting
d_1..d_m at once changes the weight by
    Delta = w(pred d_0, d_{m+1}) + sum_{i=1..m} c(d_i) - sum_{i=0..m} w(pred d_i, d_{i+1}).
The program enumerates all T sides and S sides (chains of m/2 tight steps), evaluates Delta for every pair of sides of
different trails with numpy, and prints the number of ladders and the largest Delta (must agree with ladders.c).
usage: ladders_check.py RUNS.bin OUT.json"""
import sys, os, json, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import runs_io, chains

def main():
    runs, tv, tofs, mlen = runs_io.load(sys.argv[1]); N = len(runs); cache = os.environ.get("W_CACHE")
    W = np.load(cache) if cache and os.path.exists(cache) else runs_io.weight_matrix(runs)
    W = W.astype(np.int16); np.fill_diagonal(W, 8)
    ci = chains.chain_info(W, tofs, mlen); cut = ci["cut"].astype(np.int16)
    T = np.array([x[0] for x in tv]); pred = np.zeros(N, np.int64); succ = np.zeros(N, np.int64)
    for t in range(30):
        for v in range(2):
            o0 = tofs[t] + v * mlen[t]; m = mlen[t]
            for k in range(m): pred[o0 + k] = o0 + (k - 1) % m; succ[o0 + k] = o0 + (k + 1) % m
    wrapR = {}
    for c in ci["chains"]:
        if c["full"]: wrapR[int(succ[c["runs"][-1]])] = c["runs"][0]
    def tight_right(l): return [("s", int(pred[l]))] + ([("w", wrapR[l])] if l in wrapR else [])
    out = {}
    for k in (1, 2):
        sides = []
        for t0 in range(N):
            stack = [([t0], "")]
            while stack:
                cs, ty = stack.pop()
                if len(cs) == k + 1:
                    if len(set(cs)) == k + 1: sides.append((cs, ty))
                    continue
                for (typ, r) in tight_right(cs[-1]): stack.append((cs + [r], ty + typ))
        C = np.array([s[0] for s in sides], np.int64)                # sides x (k + 1)
        tr = T[C[:, 0]]
        # T side: kept t_0 = C[:,0], deleted t_1..t_k;  S side: deleted s_1..s_k = C[:,0..k-1], kept s_{k+1} = C[:,k]
        tot = 0; worst = -10 ** 9; zero = 0; nS = len(sides)
        sumcS = cut[C[:, :k]].sum(1); sumcT = cut[C[:, 1:]].sum(1)
        for i0 in range(0, nS, 256):
            Ti = C[i0:i0 + 256]                                       # block of T sides
            d = W[pred[Ti[:, 0]]][:, C[:, k]].astype(np.int32)        # w(pred t_0, s_{k+1})
            d += sumcS[None, :] + sumcT[i0:i0 + 256, None]
            for q in range(k):
                d -= W[pred[Ti[:, q]]][:, C[:, q]]                    # pred(t_q) -> s_{q+1}
                d -= W[pred[C[:, q]]][:, Ti[:, q + 1]].T              # pred(s_{q+1}) -> t_{q+1}
            d -= W[pred[Ti[:, k]]][:, C[:, k]]                        # pred(t_k) -> s_{k+1}
            ok = tr[i0:i0 + 256, None] != tr[None, :]
            tot += int(ok.sum()); dd = d[ok]
            if dd.size: worst = max(worst, int(dd.max())); zero += int((dd == 0).sum())
        out["m%d" % (2 * k)] = dict(sides=nS, ladders=tot, max_delta=worst, delta_zero=zero)
        print("m =", 2 * k, out["m%d" % (2 * k)])
    out["ladder_lemma_holds"] = all(v["max_delta"] <= 0 for v in out.values() if isinstance(v, dict))
    json.dump(out, open(sys.argv[2], "w"), indent=1)
main()
