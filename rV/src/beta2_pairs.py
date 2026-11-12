#!/usr/bin/env python3
"""Round V -- assemble the two-gap-arc path bounds of csrc/gap_pairs.c into unordered pairs of chains up to the
symmetry of the selection.  beta2.bin[r][g] = bound for "rep[r] before g".  For an unordered pair {a, b}:
   beta2{a, b} = min( B(a > b), B(b > a) ),  B(a > b) = table[rep of a][image of b under the relabeling a -> rep(a)].
usage: beta2_pairs.py WORK(chain_sym.json, reps.txt) beta1.txt beta2.bin OUT.json"""
import sys, os, json, collections
import numpy as np
work, b1p, b2p, outp = sys.argv[1:5]
sym = json.load(open(os.path.join(work, "chain_sym.json"))); img = np.array(sym["images"]); reps = sym["reps"]; host = sym["host"]; ng = img.shape[1]
ridx = {r: i for i, r in enumerate(reps)}
b1 = {int(l.split()[0]): int(l.split()[2]) for l in open(b1p)}
T = np.fromfile(b2p, np.int8).reshape(len(reps), ng).astype(int)
# for chain a: the group element k with img[k][a] in reps (img[k] maps chain -> image chain)
torep = {}
for a in range(ng):
    for k in range(4):
        if int(img[k][a]) in ridx: torep[a] = k; break
def B(a, b):
    k = torep[a]; return T[ridx[int(img[k][a])], int(img[k][b])]
hist = collections.Counter(); low = []; seen = set(); npairs = 0; samehost = 0
for a in reps:
    for b in range(ng):
        if b == a: continue
        # canonical representative of the unordered pair under the group
        key = min(tuple(sorted((int(img[k][a]), int(img[k][b])))) for k in range(4))
        if key in seen: continue
        seen.add(key); npairs += 1
        if host[a] == host[b]: samehost += 1; continue
        v = min(B(a, b), B(b, a)); hist[v] += 1
        if v <= 23: low.append(dict(a=a, b=b, beta2=int(v), beta1_a=b1[a], beta1_b=b1[b], host_a=host[a], host_b=host[b]))
res = dict(chains=ng, orbit_representatives=len(reps), unordered_pairs_up_to_symmetry=npairs, same_host_pairs=samehost, beta1_histogram={str(k): v for k, v in sorted(collections.Counter(b1.values()).items())},
           beta2_histogram_different_hosts={str(k): v for k, v in sorted(hist.items())}, pairs_with_beta2_le_23=len(low), low_pairs=sorted(low, key=lambda d: d["beta2"]))
json.dump(res, open(outp, "w"), indent=1); print({k: v for k, v in res.items() if k != "low_pairs"}); print(res["low_pairs"][:12])
