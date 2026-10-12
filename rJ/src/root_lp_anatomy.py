#!/usr/bin/env python3
"""Anatomy of the root subtour-LP solution on a chain set: fractional arcs classified as
successor (cost-3 cycle arc) / intra-cycle link / inter-cycle link, by kind of the endpoint cycles."""
import sys, os, json
import numpy as np
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chainset_model import load_word, chains_from_word, Model, reference_orders
from chainset_bc import BC
w, n = load_word(sys.argv[1]); ch = chains_from_word(w, n); M = Model(ch, n)
# cycles of the chain set: follow cost-3 links that close up (word order trails, glued)
from collections import defaultdict
q = M.q; succ = {}
for a in range(q):
    for b in range(q):
        pass
# word-order trails: consecutive chains joined by cost 3 in the word are cycle successors
from chainset_model import ov_cost
trail_of = [0] * q; t = 0
for a in range(q - 1):
    trail_of[a] = t
    if ov_cost(ch[a][1], ch[a + 1][0], n) != 3: t += 1
trail_of[q - 1] = t
size = Counter(trail_of)
kind = ["phi" if size[trail_of[a]] == 6 else "bundle" for a in range(q)]
bc = BC(M, 54, reference_orders(M, list(range(q)), k_random=20))
res = bc.solve_node([], [])
x = res["x"]; print("LP", res["obj"], "cuts", len(bc.pool))
cls = Counter(); vals = Counter()
for j in np.nonzero(x > 1e-6)[0]:
    a, b, wt = M.arcs[j]
    if a >= q or b >= q:
        typ = ("depot" if (a == M.D or b == M.D) else "hub", kind[b] if a >= q else kind[a])
    elif wt == 0 and ov_cost(ch[a][1], ch[b][0], n) == 3 and trail_of[a] == trail_of[b]:
        typ = ("cycle-arc", kind[a])
    else:
        typ = ("link", kind[a] + "->" + kind[b], "w=%d" % wt)
    cls[typ] += x[j]; vals[(typ[0], round(float(x[j]), 3))] += 1
for k, v in sorted(cls.items(), key=lambda kv: str(kv[0])): print(k, round(v, 3))
print("value histogram:", dict(vals))
