#!/usr/bin/env python3
"""Which arcs does a certified B&B tree branch on?  Classify branching arcs by type (cycle successor,
intra-cycle link, inter-cycle link by kinds, depot/hub) using the word's trail structure."""
import sys, os, json, gzip
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chainset_model import load_word, chains_from_word, Model, ov_cost
word, certf = sys.argv[1], sys.argv[2]
C = json.load(gzip.open(certf, "rt") if certf.endswith(".gz") else open(certf))
w, n = load_word(word); ch = chains_from_word(w, n); M = Model(ch, n); q = M.q
trail = [0] * q; t = 0
for a in range(q - 1):
    trail[a] = t
    if ov_cost(ch[a][1], ch[a + 1][0], n) != 3: t += 1
trail[q - 1] = t
size = Counter(trail); kind = ["phi" if size[trail[a]] == 6 else "bundle" for a in range(q)]
arcs = C["arcs"]
def typ(j):
    a, b, wt = arcs[j]
    if a == M.D or b == M.D: return "depot " + (kind[b] if a == M.D else kind[a])
    if a == M.H or b == M.H: return "hub " + (kind[b] if a == M.H else kind[a])
    if trail[a] == trail[b] and wt == 0 and b == a + 1: return "successor " + kind[a]
    if trail[a] == trail[b]: return f"intra-trail w={wt} {kind[a]}"
    return f"link {kind[a]}->{kind[b]} w={wt}"
br = Counter(typ(nd["branch_var"]) for nd in C["nodes"] if nd["kind"] == "branch")
for k, v in br.most_common(): print(f"{v:5d}  {k}")
