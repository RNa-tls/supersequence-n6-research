#!/usr/bin/env python3
"""Round V -- letter-level arcs of a wrap family F_C (or of the base family): the cyclic letter word of every trail
is rebuilt from its runs, then all single-opening arcs are enumerated as in rT/src/options.py (cuts at weight-3 steps,
weight-2 steps and inside classes; repeated windows may be dropped).  Trail 0 = the detached chain (if any),
trails 1..16 (or 0..15 for the base) = the original trails.
The arc of the detached chain that cuts its wrap is left out (the wrap must be used), unless --allow-wrap-cut.
usage: fam_letters.py SEL TSV BASE WORK CHAIN(-1 = base) OUT_ARCS.txt [--allow-wrap-cut]"""
import sys, os, json, collections
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rU", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rT", "src"))
import wrapfam as WF, options as OP, model as MD, build_from_selection as BS
selp, tsvp, basep, work, ci, outp = sys.argv[1:7]; ci = int(ci)
ent, tr, cnat, succ, pred, W = WF.base_tables(selp, tsvp, basep, work); n = len(ent); chains = WF.chains_of(cnat, succ, pred)
succ2 = succ.copy(); tr2 = tr.copy()
if ci >= 0:
    C = chains[ci]; Q = int(pred[C[0]]); N0 = int(succ[C[6]]); succ2[C[6]] = C[0]; succ2[Q] = N0; tr2 = tr + 1; tr2[C] = 0
def cyc_word(start):
    seq = [start]
    while int(succ2[seq[-1]]) != start: seq.append(int(succ2[seq[-1]]))
    w = ent[seq[0]] + ent[seq[0]][:7]
    for a, b in zip(seq, seq[1:]):
        k = 8 - int(W[a, b]); w += ent[b][k:] + ent[b][:7]
    k0 = 8 - int(W[seq[-1], seq[0]]); assert w[len(w) - k0:] == w[:k0]
    return w[:len(w) - k0] if k0 else w, seq
words = {}
for t in sorted(set(int(x) for x in tr2)):
    start = int(C[0]) if (ci >= 0 and t == 0) else int(np.nonzero(tr2 == t)[0][0]); words[t], seq = cyc_word(start); assert len(seq) == int((tr2 == t).sum())
if ci < 0:
    orig = {BS.canon(c) for c in MD.load(selp, tsvp, basep)}; assert {BS.canon(c) for c in words.values()} == orig, "rebuilt cyclic words differ from the trails"
fo = open(outp, "w"); hist = collections.Counter(); tot = 0
for t in sorted(words):
    c = words[t]; R = len(c); d = c * 3
    for s, k in OP.options(c):
        if ci >= 0 and t == 0 and s == 0 and k >= 1 and "--allow-wrap-cut" not in sys.argv: continue      # the arc that cuts the wrap C6 -> C0 (then the wrap is not used)
        piece = d[s:s + R + 7 - k]; fo.write("%d %d %d %d %s %s\n" % (t, s, k, 2 - k, piece[:7], piece[-7:])); hist[2 - k] += 1; tot += 1
fo.close(); print(json.dumps(dict(chain=ci, trails=len(words), sum_R=sum(len(c) for c in words.values()), arcs=tot, arcs_by_cost={str(k): v for k, v in sorted(hist.items())})))
