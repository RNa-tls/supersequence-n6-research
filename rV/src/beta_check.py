#!/usr/bin/env python3
"""Round V -- independent check of the gap-arc bounds of csrc/gap_pairs.c (three-segment minimum) by a direct
Held-Karp run (csrc/path_witness.c): the base arcs with the host trail(s) restricted to the gap arc(s).
 beta1(g): all 16 trails, host of g has the single arc g.    beta2{a, b}: both hosts restricted.
usage: beta_check.py WORKU WORKV N_SAMPLE SEED OUT.json"""
import sys, os, json, random, subprocess
import numpy as np
wu, wv, ns, seed, outp = sys.argv[1:6]; ns = int(ns); random.seed(int(seed))
base = [l.split() for l in open(os.path.join(wu, "base_arcs.txt"))]
gaps = [l.split() for l in open(os.path.join(wu, "gaps.txt"))]            # chain host head tail cost
sym = json.load(open(os.path.join(wu, "chain_sym.json"))); img = np.array(sym["images"]); reps = sym["reps"]; host = sym["host"]; ridx = {r: i for i, r in enumerate(reps)}
b1 = {int(l.split()[0]): int(l.split()[2]) for l in open(os.path.join(wv, "beta1.txt"))}
T = np.fromfile(os.path.join(wv, "beta2.bin"), np.int8).reshape(len(reps), len(gaps)).astype(int)
torep = {a: next(k for k in range(4) if int(img[k][a]) in ridx) for a in range(len(gaps))}
def B(a, b):
    k = torep[a]; return int(T[ridx[int(img[k][a])], int(img[k][b])])
def direct(chs):
    hs = {int(gaps[c][1]) for c in chs}; rows = [r for r in base if int(r[0]) not in hs]
    for c in chs: g = gaps[c]; rows.append([g[1], str(90000 + c), "0", g[4], g[2], g[3]])
    rows.sort(key=lambda r: int(r[0])); p = os.path.join(wv, "bc_arcs.txt"); open(p, "w").write("".join(" ".join(r) + "\n" for r in rows))
    subprocess.run([os.path.join(wv, "path_witness"), p, os.path.join(wv, "bc.json")], capture_output=True); return json.load(open(os.path.join(wv, "bc.json")))["optimal_J"]
res = dict(beta1=[], beta2=[]); bad = 0
for c in random.sample(reps, min(len(reps), max(10, ns // 4))):
    d = direct([c]); res["beta1"].append([c, b1[c], d]); bad += d != b1[c]
low = json.load(open(os.path.join(os.path.dirname(outp), "gap_arc_bounds.json")))["low_pairs"]
pairs = [(p["a"], p["b"]) for p in random.sample(low, min(len(low), ns // 4))]
while len(pairs) < ns:
    a = random.choice(reps); b = random.randrange(len(gaps))
    if host[a] != host[b]: pairs.append((a, b))
for a, b in pairs:
    v = min(B(a, b), B(b, a)); d = direct([a, b]); res["beta2"].append([a, b, v, d]); bad += d != v
res["mismatches"] = bad; res["checked_beta1"] = len(res["beta1"]); res["checked_beta2"] = len(res["beta2"])
json.dump(res, open(outp, "w"), indent=0); print("beta1 checked", len(res["beta1"]), "beta2 checked", len(res["beta2"]), "mismatches", bad)
