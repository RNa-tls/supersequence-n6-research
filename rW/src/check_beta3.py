#!/usr/bin/env python3
"""Round W -- direct check of the three-gap table of csrc/beta3.c: for sampled triples (g1 representative, g2, g3 with
pairwise different hosts), the 16-trail arcs with the three hosts restricted to their gap arcs are written and the
exact optimum over all orders is computed by rV/csrc/path_layer.c; it must equal the minimum of the table over the
six orders of the triple (orders whose first gap is not a representative are mapped by the relabeling symmetry).
usage: check_beta3.py ARCS GAPS CHAIN_SYM.json REPS BETA3.bin PATH_LAYER N SEED OUT.json"""
import sys, json, random, subprocess, itertools, os
import numpy as np
arcsp, gapsp, symp, repsp, b3p, pl, N, seed, outp = sys.argv[1:10]; N = int(N); random.seed(int(seed))
gaps = {}
for l in open(gapsp):
    i, h, hd, tl, c = l.split(); gaps[int(i)] = (int(h), hd, tl, int(c))
ng = len(gaps); sym = json.load(open(symp)); img = np.array(sym["images"]); reps = [int(x) for x in open(repsp).read().split()]
ridx = {r: i for i, r in enumerate(reps)}; B3 = np.fromfile(b3p, np.int8).reshape(len(reps), ng, ng).astype(int)
torep = {}
for a in range(ng):
    for k in range(4):
        if int(img[k][a]) in ridx: torep[a] = k; break
def ordered(a, b, c):
    k = torep[a]; return B3[ridx[int(img[k][a])], int(img[k][b]), int(img[k][c])]
base = [l for l in open(arcsp)]
rows = []
while len(rows) < N:
    a, b, c = random.sample(range(ng), 3)
    if len({gaps[a][0], gaps[b][0], gaps[c][0]}) < 3: continue
    tab = min(ordered(*o) for o in itertools.permutations((a, b, c)))
    H = {gaps[g][0]: gaps[g] for g in (a, b, c)}
    out = [l for l in base if int(l.split()[0]) not in H] + ["%d 0 0 %d %s %s\n" % (h, cc, hd, tl) for h, (hh, hd, tl, cc) in H.items()]
    out.sort(key=lambda l: int(l.split()[0])); tmp = outp + ".arcs"; open(tmp, "w").write("".join(out))
    d = json.loads(subprocess.run([pl, tmp], capture_output=True, text=True, check=True).stdout)["optimal_J"]
    rows.append(dict(triple=[a, b, c], table=int(tab), direct=int(d), agree=int(tab) == int(d)))
    print(rows[-1], flush=True)
os.remove(outp + ".arcs")
json.dump(dict(checked=len(rows), agree=sum(r["agree"] for r in rows), rows=rows), open(outp, "w"), indent=1)
print("checked", len(rows), "agree", sum(r["agree"] for r in rows))
