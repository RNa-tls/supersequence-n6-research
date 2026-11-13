#!/usr/bin/env python3
"""Round W -- letter-level pieces of every detached chain C (the cyclic word C0 .. C6 closed by the wrap C6 -> C0),
cut anywhere except at the wrap, exactly as trail 0 of rV/src/fam_letters.py.  Also the letter words of the base
trails are not needed here.  Output lines: "chain start dropped cost head7 tail7 wi" with wi = 3 - cost the weight of
the cut link.   usage: chain_pieces.py SEL TSV BASE WORKU OUT.txt"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rU", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rT", "src"))
import wrapfam as WF, options as OP
selp, tsvp, basep, work, outp = sys.argv[1:6]
ent, tr, cnat, succ, pred, W = WF.base_tables(selp, tsvp, basep, work); chains = WF.chains_of(cnat, succ, pred)
fo = open(outp, "w"); tot = 0
for ci, C in enumerate(chains):
    seq = [int(x) for x in C]                      # C0 .. C6, then the wrap back to C0
    w = ent[seq[0]] + ent[seq[0]][:7]
    for a, b in zip(seq, seq[1:]):
        k = 8 - int(W[a, b]); w += ent[b][k:] + ent[b][:7]
    k0 = 8 - int(W[seq[-1], seq[0]]); assert int(W[seq[-1], seq[0]]) == 2 and w[len(w) - k0:] == w[:k0]
    c = w[:len(w) - k0]; R = len(c); d = c * 3
    for s, k in OP.options(c):
        if s == 0 and k >= 1: continue             # the cut at the wrap
        piece = d[s:s + R + 7 - k]; cost = 2 - k
        fo.write("%d %d %d %d %s %s %d\n" % (ci, s, k, cost, piece[:7], piece[-7:], 3 - cost)); tot += 1
fo.close(); print("chains", len(chains), "pieces", tot)
