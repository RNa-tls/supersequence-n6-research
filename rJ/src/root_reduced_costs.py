#!/usr/bin/env python3
"""Exact (integer, scaled) root reduced costs r_j and y.b from a root certificate -> .npz (for CP-SAT)."""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chainset_model import load_word, chains_from_word, Model
from chainset_bc import BC
word, rootf, outf = sys.argv[1], sys.argv[2], sys.argv[3]
w, n = load_word(word); ch = chains_from_word(w, n); M = Model(ch, n)
R = json.load(open(rootf))
bc = BC(M, R["T"], [list(range(M.q))])
for S in R["pool"]: bc.add_cut(S)
y = np.zeros(len(bc.rows_b))
for k, v in R["root"]["y"]: y[k] = v / R["SCALE"]
lb, r, yi = bc.node_bound(y, [], [])
yb = lb - int(np.sum(np.minimum(0, r)))
np.savez(outf, r=r, yb=np.array([yb]), scale=np.array([R["SCALE"]]), fixed0=np.array(R["root"]["fixed0"]))
print(json.dumps(dict(lb=lb / R["SCALE"], yb=yb / R["SCALE"], nonzero_r=int(np.sum(r != 0)), r_le_2_5=int(np.sum(r <= 2.5 * R["SCALE"])))))
