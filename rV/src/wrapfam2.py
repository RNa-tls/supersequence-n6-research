#!/usr/bin/env python3
"""Round V -- two-wrap families of the public selection: both chains C1, C2 detached as closed trails of their own
(wraps natural, not cut), hosts with skip links.  Trails: 0 = C1, 1 = C2, 2..17 = the original trails 0..15.
Writes the run-level arcs and checks the facts behind the reduction (no other non-natural link of weight <= 2,
ladder lemma m = 2, 4 with the gap heads never deleted).
usage: wrapfam2.py SEL TSV BASE WORK C1 C2 OUT_ARCS.txt   (JSON line on stdout)"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rU", "src"))
import wrapfam as WF
selp, tsvp, basep, work, c1, c2, outp = sys.argv[1:8]; c1 = int(c1); c2 = int(c2)
ent, tr, cnat, succ, pred, W = WF.base_tables(selp, tsvp, basep, work); n = len(ent); chains = WF.chains_of(cnat, succ, pred)
A, B = chains[c1], chains[c2]
tr2 = tr.copy() + 2; succ2 = succ.copy(); cn2 = cnat.copy()
adj = None
if int(succ[A[6]]) == B[0]: adj = (A, B)
elif int(succ[B[6]]) == A[0]: adj = (B, A)
gaps = []
if adj:
    F1, F2 = adj; Q = int(pred[F1[0]]); N0 = int(succ[F2[6]]); assert N0 not in F1 and Q not in F2
    succ2[Q] = N0; cn2[Q] = int(W[Q, N0]); gaps.append(N0)
else:
    for Cc in (A, B):
        Q = int(pred[Cc[0]]); N0 = int(succ[Cc[6]]); succ2[Q] = N0; cn2[Q] = int(W[Q, N0]); gaps.append(N0)
for Cc, tid in ((A, 0), (B, 1)):
    tr2[Cc] = tid; succ2[Cc[6]] = Cc[0]; cn2[Cc[6]] = 2
pred2 = np.empty(n, np.int64); pred2[succ2] = np.arange(n); cut2 = cn2[pred2]
assert (W[np.arange(n), succ2] == cn2).all()
rows = sorted((int(tr2[y]), y, 0, 3 - int(cut2[y]), ent[y][:7], ent[int(pred2[y])][:7]) for y in range(n) if y not in (A[0], B[0]))
open(outp, "w").write("".join("%d %d %d %d %s %s\n" % r for r in rows))
natural = np.zeros((n, n), bool); natural[np.arange(n), succ2] = True
w2 = (W <= 2) & ~natural & ~np.eye(n, dtype=bool); xs, ys = np.nonzero(w2)
ch2 = WF.chains_of(cn2, succ2, pred2); wrapR = {int(succ2[ch[-1]]): ch[0] for ch in ch2}; wrapset = {(ch[-1], ch[0]) for ch in ch2}
other = [(int(x), int(y)) for x, y in zip(xs, ys) if (int(x), int(y)) not in wrapset]
def tight_right(l): return [int(pred2[l])] + ([wrapR[l]] if l in wrapR else [])
lad = {}; Wi = W.astype(np.int16); G = np.array(gaps)
for k in (1, 2):
    sides = []
    for t0 in range(n):
        stack = [[t0]]
        while stack:
            cs = stack.pop()
            if len(cs) == k + 1:
                if len(set(cs)) == k + 1: sides.append(cs)
                continue
            for r in tight_right(cs[-1]): stack.append(cs + [r])
    Cm = np.array(sides, np.int64); okT = ~np.isin(Cm[:, 1:], G).any(1); okS = ~np.isin(Cm[:, :k], G).any(1); trs = tr2[Cm[:, 0]]
    sumcS = cut2[Cm[:, :k]].sum(1); sumcT = cut2[Cm[:, 1:]].sum(1); worst = -99
    for i0 in range(0, len(sides), 512):
        Ti = Cm[i0:i0 + 512]; d = Wi[pred2[Ti[:, 0]]][:, Cm[:, k]].astype(np.int32) + sumcS[None, :] + sumcT[i0:i0 + 512, None]
        for q in range(k):
            d -= Wi[pred2[Ti[:, q]]][:, Cm[:, q]]; d -= Wi[pred2[Cm[:, q]]][:, Ti[:, q + 1]].T
        d -= Wi[pred2[Ti[:, k]]][:, Cm[:, k]]
        ok = (trs[i0:i0 + 512, None] != trs[None, :]) & okT[i0:i0 + 512, None] & okS[None, :]
        if ok.any(): worst = max(worst, int(d[ok].max()))
    lad["m%d" % (2 * k)] = worst
print(json.dumps(dict(c1=c1, c2=c2, hosts=[int(tr[A[0]]), int(tr[B[0]])], adjacent=bool(adj), gaps=gaps, skip_weights=[int(cut2[g]) for g in gaps], arcs=len(rows), other_wraps=len(ch2),
                      non_natural_w_le2_not_wraps=len(other), ladders=lad, facts_ok=(len(other) == 0 and all(v <= 0 for v in lad.values())))))
