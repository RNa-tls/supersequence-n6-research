#!/usr/bin/env python3
"""Round V -- letter-level arcs of a two-wrap family F_{C1,C2}: both chains detached as closed trails of their own
(their wraps C6 -> C0 natural), the hosts closed by skip links (one skip link for two adjacent chains of one host),
exactly as in src/wrapfam2.py.  Trails: 0 = C1, 1 = C2, 2..17 = the original trails 0..15.
The cyclic letter word of every trail is rebuilt from its runs and all single-opening arcs are enumerated as in
rT/src/options.py (cuts at weight-3, weight-2 and skip links and inside classes).  The arcs of the two detached chains
that cut their wraps are left out (both wraps must be used), unless --allow-wrap-cut.
usage: fam_letters2.py SEL TSV BASE WORK C1 C2 OUT_ARCS.txt [--allow-wrap-cut] [--words OUT.json]"""
import sys, os, json, collections
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rU", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rT", "src"))
import wrapfam as WF, options as OP
selp, tsvp, basep, work, c1, c2, outp = sys.argv[1:8]; c1 = int(c1); c2 = int(c2)
ent, tr, cnat, succ, pred, W = WF.base_tables(selp, tsvp, basep, work); n = len(ent); chains = WF.chains_of(cnat, succ, pred)
A, B = chains[c1], chains[c2]; assert not (set(int(x) for x in A) & set(int(x) for x in B))
succ2 = succ.copy(); tr2 = tr.copy() + 2
adj = None
if int(succ[A[6]]) == B[0]: adj = (A, B)
elif int(succ[B[6]]) == A[0]: adj = (B, A)
if adj:
    F1, F2 = adj; Q = int(pred[F1[0]]); N0 = int(succ[F2[6]]); assert N0 not in F1 and Q not in F2; succ2[Q] = N0
else:
    for Cc in (A, B):
        Q = int(pred[Cc[0]]); N0 = int(succ[Cc[6]]); assert Q not in A and Q not in B and N0 not in A and N0 not in B; succ2[Q] = N0
for Cc, tid in ((A, 0), (B, 1)):
    tr2[Cc] = tid; succ2[Cc[6]] = Cc[0]
assert sorted(succ2.tolist()) == list(range(n)), "succ2 is not a permutation"
def cyc_word(start):
    seq = [start]
    while int(succ2[seq[-1]]) != start: seq.append(int(succ2[seq[-1]]))
    w = ent[seq[0]] + ent[seq[0]][:7]
    for a, b in zip(seq, seq[1:]):
        k = 8 - int(W[a, b]); w += ent[b][k:] + ent[b][:7]
    k0 = 8 - int(W[seq[-1], seq[0]]); assert w[len(w) - k0:] == w[:k0]
    return w[:len(w) - k0] if k0 else w, seq
words = {}; starts = {0: int(A[0]), 1: int(B[0])}
for t in sorted(set(int(x) for x in tr2)):
    start = starts[t] if t in starts else int(np.nonzero(tr2 == t)[0][0]); words[t], seq = cyc_word(start)
    assert len(seq) == int((tr2 == t).sum()), "trail %d is not one cycle" % t
assert sorted(words) == list(range(18))
fo = open(outp, "w"); hist = collections.Counter(); tot = 0
for t in sorted(words):
    c = words[t]; R = len(c); d = c * 3
    for s, k in OP.options(c):
        if t in (0, 1) and s == 0 and k >= 1 and "--allow-wrap-cut" not in sys.argv: continue      # the arc that cuts the wrap C6 -> C0
        piece = d[s:s + R + 7 - k]; fo.write("%d %d %d %d %s %s\n" % (t, s, k, 2 - k, piece[:7], piece[-7:])); hist[2 - k] += 1; tot += 1
fo.close()
if "--words" in sys.argv: json.dump({str(t): words[t] for t in words}, open(sys.argv[sys.argv.index("--words") + 1], "w"))
print(json.dumps(dict(c1=c1, c2=c2, adjacent=bool(adj), trails=len(words), sum_R=sum(len(c) for c in words.values()), arcs=tot, arcs_by_cost={str(k): v for k, v in sorted(hist.items())})))
