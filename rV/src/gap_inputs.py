#!/usr/bin/env python3
"""Round V -- inputs for csrc/gap_pairs.c: the gap arc of every complete chain (host trail, first 7 letters of N0,
last-7 state of Q_end, cost 3 - w(Q_end, N0)), the orbit representatives, and the images of every chain under the four
relabelings that fix the selection.   usage: gap_inputs.py SEL TSV BASE WORK"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rU", "src"))
import wrapfam as WF
selp, tsvp, basep, work = sys.argv[1:5]
ent, tr, cnat, succ, pred, W = WF.base_tables(selp, tsvp, basep, work); chains = WF.chains_of(cnat, succ, pred); n = len(ent)
with open(os.path.join(work, "gaps.txt"), "w") as f:
    for i, ch in enumerate(chains):
        q = int(pred[ch[0]]); n0 = int(succ[ch[-1]]); f.write("%d %d %s %s %d\n" % (i, int(tr[ch[0]]), ent[n0][:7], ent[q][:7], 3 - int(W[q, n0])))
pos = {e: i for i, e in enumerate(ent)}; G = ["01234567", "01543267", "10243567", "10534267"]; start = {ch[0]: i for i, ch in enumerate(chains)}
img = []
for g in G:
    mp = dict(zip("01234567", g)); im = np.array([pos["".join(mp[c] for c in e)] for e in ent]); img.append([start[int(im[ch[0]])] for ch in chains])
reps = sorted({min(img[k][i] for k in range(4)) for i in range(len(chains))})
open(os.path.join(work, "reps.txt"), "w").write("".join("%d\n" % r for r in reps))
json.dump(dict(images=img, reps=reps, host=[int(tr[ch[0]]) for ch in chains], C0=[int(ch[0]) for ch in chains]), open(os.path.join(work, "chain_sym.json"), "w"))
print("chains", len(chains), "reps", len(reps))
