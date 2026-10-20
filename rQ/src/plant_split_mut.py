#!/usr/bin/env python3
"""Round Q, section 13 -- planted-solution mutation for the single-split pipeline (end-to-end completeness test).
Takes the verified single-split witness (split_witness.py JSON: P_options, Z_options, anchor_b_option) and lowers e by
1 on DROP edges of it that have e >= 1, on every image under the 12-element option group (the instance stays
symmetric, so ckB/ckT/ckT_search accept it).  The witness then has G - DROP; a correct pipeline run at the lowered
threshold must report it (or something better).  Output: CKB_MUT lines "a b v".
usage: plant_split_mut.py FAMILY.json GROUP.npz WITNESS.json DROP OUT.txt"""
import sys, json
import numpy as np
def w(x, y):
    for s in range(1, 8):
        if x[s:] == y[:8 - s]: return s
    return 8
fam = json.load(open(sys.argv[1])); operm = np.load(sys.argv[2])["operm"]; W = json.load(open(sys.argv[3])); drop = int(sys.argv[4])
ent, ext, tr = [], [], []
for t, T in enumerate(fam["trails"]):
    for v, s in enumerate(T["versions"]):
        runs = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]
        for k in range(len(runs)):
            p = runs[k - 1]; ent.append(runs[k]); ext.append((p[7],) + p[:7]); tr.append(t)
cut = lambda o: w(ext[o], ent[o]); e = lambda a, b: w(ext[a], ent[b]) - cut(b) - 1
P, Z, b = W["P_options"], W["Z_options"], W["anchor_b_option"]
edges = [(P[i], P[i + 1]) for i in range(len(P) - 1)] + [(Z[i], Z[i + 1]) for i in range(len(Z) - 1)] + [(Z[-1], b), (b, Z[0])]
G = 1 + int(cut(P[0]) == 2) + sum(e(x, y) for x, y in edges)
assert G == W["G"], (G, W["G"])
pick = [(x, y) for (x, y) in edges if e(x, y) >= 1 and tr[x] != tr[y]][:drop]
assert len(pick) == drop
lines = {}
for (x, y) in pick:
    v = e(x, y)
    for Pm in operm:
        a, c = int(Pm[x]), int(Pm[y]); assert e(a, c) == v
        lines[(a, c)] = v - 1
open(sys.argv[5], "w").write("".join("%d %d %d\n" % (a, c, v) for (a, c), v in sorted(lines.items())))
print(json.dumps(dict(witness_G=G, planted_G=G - drop, edges=[(int(x), int(y), e(x, y)) for x, y in pick], mutation_lines=len(lines))))
