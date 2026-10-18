#!/usr/bin/env python3
"""Round P -- mutation files for checker B (env CKB_MUT, lines "a b v": e(a, b) := v, option index = trail-major
(t, v, k) as in ckB.c / options.py).

mode 'plant': take a record word (description JSON: trail, version, opening k, runs m per position), choose the
  first link with e >= 1 whose endpoints include an A trail, and lower e by 1 on that link AND on all its images
  under the 12-element group (so the instance stays symmetric).  The word then costs F - 1, so a correct
  pipeline must find a word with F <= F - 1 at THR = F - 1.
mode 'asym' : lower the same link only (no images) -- the group check of checker B must reject the instance.
usage: plant_mut.py plant|asym FAMILY.json GROUP.npz DESCRIPTION.json OUT.txt"""
import sys, json
import numpy as np
N = 8
def w(x, y):
    for s in range(1, N):
        if x[s:] == y[:N - s]: return s
    return N

def main():
    mode, fam_p, grp_p, desc_p, out = sys.argv[1:6]
    fam = json.load(open(fam_p)); G = np.load(grp_p); operm = G["operm"]
    ent, ext, tr, tofs = [], [], [], {}
    for t, T in enumerate(fam["trails"]):
        tofs[t] = len(ent)
        for v, s in enumerate(T["versions"]):
            runs = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]
            for k in range(len(runs)):
                p = runs[k - 1]; ent.append(runs[k]); ext.append((p[7],) + p[:7]); tr.append(t)
    cut = lambda o: w(ext[o], ent[o])
    e = lambda a, b: w(ext[a], ent[b]) - cut(b) - 1
    d = json.load(open(desc_p))
    nrun = lambda t, v: len(fam["trails"][t]["versions"][v]) // 8
    opts = [tofs[t] + (nrun(t, 0) if v else 0) + k for (t, v, k, m) in d["description"]]
    links = [(opts[i], opts[i + 1], e(opts[i], opts[i + 1])) for i in range(len(opts) - 1)]
    F = int(cut(opts[0]) == 2) + sum(x[2] for x in links)
    ntr = len(fam["trails"]); isA = [len(fam["trails"][t]["versions"][0]) // 8 > 100 for t in range(ntr)]
    pick = next(i for i, (a, b, v) in enumerate(links) if v >= 1 and (isA[tr[a]] or isA[tr[b]]))
    a, b, v = links[pick]
    pairs = {(int(P[a]), int(P[b])) for P in operm} if mode == "plant" else {(a, b)}
    for (x, y) in pairs: assert e(x, y) == v
    with open(out, "w") as f:
        for (x, y) in sorted(pairs): f.write(f"{x} {y} {v - 1}\n")
    print(json.dumps(dict(mode=mode, word_F=F, link_position=pick, link=[int(a), int(b)], trails=[tr[a], tr[b]], e=v,
                          new_e=v - 1, mutated_entries=len(pairs), word_F_after=F - 1)))

main()
