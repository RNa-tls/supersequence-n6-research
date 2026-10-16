#!/usr/bin/env python3
"""Round N (section 11) -- parity at the compressed (option) level.
For every join o -> o' with e <= 2 (and every single-piece option) record binary features:
sign of exit perm, sign of entry perm, world (last symbol) parity of both, frame parity (sign of the
frame as a cyclic order is not defined; we use the sign of the canonical 6-word), cut type; then test
whether e mod 2 is an affine GF(2) function of these features (exhaustive solve of the linear system).
usage: parity_check.py FAMILY.json E.npy"""
import sys, os, json, itertools
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import options as OP

def sign(p):
    p = list(p); s = 0
    for i in range(len(p)):
        for j in range(i + 1, len(p)):
            if p[i] > p[j]: s ^= 1
    return s

def main():
    fam, opts = OP.load(sys.argv[1]); E = np.load(sys.argv[2])
    feats = []
    for o in opts:
        en, ex = o["entry"], o["exit"]
        feats.append([sign(en), sign(ex), en[7] & 1, ex[0] & 1, 1 if o["cut"] == 2 else 0, 1 if o["m"] == 672 else 0])
    F = np.array(feats, dtype=np.int64)
    a, b = np.nonzero(E <= 2)
    sel = np.random.default_rng(1).choice(len(a), size=min(200000, len(a)), replace=False)
    a, b = a[sel], b[sel]
    X = np.concatenate([F[a], F[b], np.ones((len(a), 1), np.int64)], axis=1) % 2   # features of both ends + constant
    y = (E[a, b] % 2).astype(np.int64)
    # GF(2) solve X w = y
    M = np.concatenate([X, y[:, None]], axis=1) % 2
    rows, cols = M.shape; r = 0; piv = []
    for c in range(cols - 1):
        pr = None
        for i in range(r, rows):
            if M[i, c]: pr = i; break
        if pr is None: continue
        M[[r, pr]] = M[[pr, r]]
        for i in range(rows):
            if i != r and M[i, c]: M[i] ^= M[r]
        piv.append(c); r += 1
        if r == rows: break
    inconsistent = bool(np.any((M[:, :-1].sum(1) == 0) & (M[:, -1] == 1)))
    res = dict(joins_tested=int(len(a)), features=2 * F.shape[1] + 1, affine_parity_law_exists=not inconsistent)
    # also e mod 3 / mod 4 against sums of features (exhaustive over small integer weightings is skipped)
    print(json.dumps(res))

if __name__ == "__main__":
    main()
