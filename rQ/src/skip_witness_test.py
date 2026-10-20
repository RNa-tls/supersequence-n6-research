#!/usr/bin/env python3
"""Round Q, section 6.5 -- end-to-end test of the skip decomposition and of skip_eval.c on real words.

From a single-opening word: pick a trail T (its block opens T at run u) and a jump alpha-1 -> beta of T's version with
E' = w(last r_{alpha-1}, r_beta) - c_beta >= 0 and u -> alpha -> beta -> u; replace T's block by the 2-piece visit
[u, alpha) [beta, u) and insert the skipped piece [alpha, beta) between the blocks j and j+1 (both not T).  The word is
built run by run; its exact length gives G_word = L - 46162.  The decomposition predicts
    G = 1 + E' + (F - e(x -> y)) + e(x -> T(alpha)) + e(T(beta) -> y)       (F of the single-opening word).
Writes the pattern line (SIGMA, junction) for skip_eval.c and the built word for minicheck / word_pieces.
usage: skip_witness_test.py WORD FAMILY.json TRAIL_POS JUNCTION_AFTER EPMAX OUT_PREFIX"""
import sys, json
import numpy as np

n = 8
def load_word(p):
    t = "".join(ch for ch in open(p).read() if not ch.isspace()); al = sorted(set(t)); return [al.index(c) for c in t]
def starts(w):
    seen = set(); route = []
    for i in range(len(w) - n + 1):
        p = tuple(w[i:i + n])
        if len(set(p)) == n and p not in seen: seen.add(p); route.append(p)
    st = route[0::n]
    for b, s in enumerate(st):
        for j in range(n): assert route[n * b + j] == s[j:] + s[:j]
    return st
def canon(p): return min(p[i:] + p[:i] for i in range(n))

def main():
    word, famp, tpos, jafter, epmax, outp = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
    st = starts(load_word(word)); N = len(st); fam = json.load(open(famp))
    cls_trail = {}
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]):
            for k in range(len(s) // 8): cls_trail[canon(tuple(int(c) for c in s[8 * k:8 * k + 8]))] = t
    trail = np.array([cls_trail[canon(s)] for s in st])
    S = np.array(st, np.int64); X = np.concatenate([S[:, 7:], S[:, :7]], 1)
    W = np.full((N, N), 8, np.int64)
    for k in range(7, 0, -1):
        a = (X[:, k:] * (8 ** np.arange(8 - k))).sum(1); b = (S[:, :8 - k] * (8 ** np.arange(8 - k))).sum(1)
        W[a[:, None] == b[None, :]] = k
    np.fill_diagonal(W, 8)
    blocks = []; i = 0
    while i < N:
        j = i
        while j + 1 < N and trail[j + 1] == trail[i]: j += 1
        blocks.append(list(range(i, j + 1))); i = j + 1
    assert len(blocks) == 30
    L0 = 35288 + int(W[np.arange(N - 1), np.arange(1, N)].sum()); F = L0 - 46162
    B = blocks[tpos]; m = len(B); T = int(trail[B[0]])
    # T's version cycle opened at u = B[0]: offsets 0..m-1; cut weight c(k) = W[B[k-1], B[k]], c(0) = W[B[-1], B[0]]
    c = [int(W[B[(k - 1) % m], B[k]]) for k in range(m)]
    best = None
    for da in range(1, m - 1):
        for db in range(da + 1, m):
            ep = int(W[B[da - 1], B[db]]) - c[db]
            if 0 <= ep <= epmax:
                cand = (ep, da, db)
                if best is None or cand < best: best = cand
    if best is None: print(json.dumps({"error": "no jump with 0 <= E' <= EPMAX"})); return
    ep, da, db = best
    visit = B[:da] + B[db:]; Y = B[da:db]
    assert jafter - 1 != tpos and jafter != tpos, "T adjacent to the junction"
    order_blocks = [b if bi != tpos else visit for bi, b in enumerate(blocks)]
    route = []
    for bi, b in enumerate(order_blocks):
        route += b
        if bi == jafter - 1: route += Y
    assert sorted(route) == list(range(N))
    L = 35288 + int(W[np.array(route[:-1]), np.array(route[1:])].sum()); Gw = L - 46162
    xl = blocks[jafter - 1][-1]; yf = blocks[jafter][0]
    def e(xrun, yrun, cy): return int(W[xrun, yrun]) - cy - 1
    cy = int(W[blocks[jafter][-1], blocks[jafter][0]])          # y's cut weight inside its own (single-piece) cycle
    exy = e(xl, yf, cy); exa = e(xl, Y[0], c[da]); eby = e(Y[-1], yf, cy)
    Gf = 1 + ep + (F - exy) + exa + eby
    w = list(st[route[0]])
    for k, r in enumerate(route):
        if k > 0: kk = int(W[route[k - 1], r]); w += list(st[r][8 - kk:])
        w += list(st[r][:7])
    assert len(w) == L
    open(outp + ".txt", "w").write("".join(str(x + 1) for x in w) + "\n")
    # pattern line for skip_eval: phi tokens = trail ids (as written by ckT_search.c), A tokens = 1100 + (1 << A index), junction = -1
    isA = [len(tr["versions"][0]) // 8 > 100 for tr in fam["trails"]]
    phl = [t for t in range(30) if not isA[t]]; Al = [t for t in range(30) if isA[t]]
    toks = []
    for bi, b in enumerate(blocks):
        t = int(trail[b[0]]); toks.append(str(t) if not isA[t] else str(1100 + (1 << Al.index(t))))
        if bi == jafter - 1: toks.append("-1")
    open(outp + ".pat", "w").write(" ".join(toks) + "\n")
    print(json.dumps(dict(word=word, F=F, trail=T, trail_pos=tpos, junction_after=jafter, Ep=ep, alpha_offset=da, beta_offset=db,
                          skipped_runs=len(Y), length=L, G_word=Gw, G_formula=Gf, match=Gw == Gf, e_xy=exy, e_x_alpha=exa, e_beta_y=eby)))

main()
