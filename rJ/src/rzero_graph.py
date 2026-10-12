#!/usr/bin/env python3
"""Structure of the zero-reduced-cost arc subgraph of the root LP (46187 chain set)."""
import sys, os, json
import numpy as np
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chainset_model import load_word, chains_from_word, Model, ov_cost
word, rcf = sys.argv[1], sys.argv[2]
w, n = load_word(word); ch = chains_from_word(w, n); M = Model(ch, n)
Z = np.load(rcf); r = Z["r"]; SC = int(Z["scale"][0])
q = M.q
trail = [0] * q; t = 0
for a in range(q - 1):
    trail[a] = t
    if ov_cost(ch[a][1], ch[a + 1][0], n) != 3: t += 1
trail[q - 1] = t
size = Counter(trail); kind = ["phi" if size[trail[a]] == 6 else "bundle" for a in range(q)]
def typ(j):
    a, b, wt = M.arcs[j]
    if a == M.D or b == M.D: return "depot"
    if a == M.H or b == M.H: return "hub"
    if trail[a] == trail[b] and wt == 0: return "w0-same-trail(" + kind[a] + ")"
    if trail[a] == trail[b]: return f"link-same-trail w={wt} ({kind[a]})"
    return f"link {kind[a]}->{kind[b]} w={wt}"
for lvl in (0, 1, 2, 3):
    sel = np.nonzero(r == lvl * SC // 2)[0]
    print(f"r = {lvl/2}: {len(sel)} arcs:", dict(Counter(typ(j) for j in sel)))
neg = np.nonzero(r < 0)[0]
print("negative:", [(typ(j), r[j] / SC) for j in neg])
