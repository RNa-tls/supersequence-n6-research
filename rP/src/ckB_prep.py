#!/usr/bin/env python3
"""Round P, checker B -- convert the family JSON and the symmetry group to flat binary input for ckB.c.
Writes  runs.bin: for t in 0..29, v in 0..1: int32 m, then m x 8 uint8 (first permutation of each run);
        group.bin: int32 G, then G x 30 int32 trail permutation, then G x NOPT int32 option permutation
        (option index = trail-major (t, v, k) as enumerated from runs.bin).
Nothing else is precomputed here.
usage: ckB_prep.py FAMILY.json GROUP.npz OUTDIR"""
import sys, json, os
import numpy as np
fam = json.load(open(sys.argv[1])); G = np.load(sys.argv[2]); out = sys.argv[3]; os.makedirs(out, exist_ok=True)
with open(os.path.join(out, "runs.bin"), "wb") as f:
    for tr in fam["trails"]:
        assert len(tr["versions"]) == 2
        for s in tr["versions"]:
            m = len(s) // 8
            np.array([m], np.int32).tofile(f)
            np.array([int(c) for c in s], np.uint8).tofile(f)
op, tp = G["operm"], G["tperm"]
with open(os.path.join(out, "group.bin"), "wb") as f:
    np.array([len(op)], np.int32).tofile(f); tp.astype(np.int32).tofile(f); op.astype(np.int32).tofile(f)
print("ok", len(op), op.shape)
