#!/usr/bin/env python3
"""Round X -- data for the host-split two-wrap model (front A).

Two chains C1, C2 of one host trail h, not adjacent, both detached as closed trails (both wraps used).  In the split
model the host is not closed by its two skip links but used as two pieces
    A = from N0(C1) to Q(C2),   B = from N0(C2) to Q(C1)      (cuts at the two skip links, cost -1 each),
so the family has 19 pieces: C1, C2, A, B and the 15 other trails.  Removing the two chain pieces does not increase J
(Round W: insertion lemma W-ins + fact W-chain), so J >= J17, the optimum over paths of the 15 other trails and A, B.
A piece enters A through the first 7 letters of N0(C1), leaves A through the last 7 letters of Q(C2) (= the first 7
letters of the entry of the run Q(C2)), and so on.

Writes, for host trail h:  OUT/arcs_h.txt (letter arcs of the 15 other trails, renumbered 0..14, from the base letter
arcs) and OUT/chains_h.txt (one line per chain of h:  index first_run last_run Q N0 q_tail7 n0_head7 next_chain prev_chain,
next/prev = the chain that starts right after / ends right before, or -1).
usage: split_chains.py SEL TSV BASE WORKU BASE_LETTER_ARCS OUTDIR"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rU", "src"))
import wrapfam as WF
selp, tsvp, basep, work, arcsp, outd = sys.argv[1:7]; os.makedirs(outd, exist_ok=True)
ent, tr, cnat, succ, pred, W = WF.base_tables(selp, tsvp, basep, work); chains = WF.chains_of(cnat, succ, pred)
first = {int(C[0]): i for i, C in enumerate(chains)}; last = {int(C[6]): i for i, C in enumerate(chains)}
arcs = [l.split() for l in open(arcsp)]
def ov(t, h):
    for k in range(7, 0, -1):
        if t[7 - k:] == h[:k]: return k
    return 0
summary = {}
for h in sorted(set(int(tr[C[0]]) for C in chains)):
    rows = []
    for i, C in enumerate(chains):
        if int(tr[C[0]]) != h: continue
        Q, N0 = int(pred[C[0]]), int(succ[C[6]])
        qt, nh = ent[Q][:7], ent[N0][:7]
        assert int(W[Q, C[0]]) == 3 and int(W[C[6], N0]) == 3, "chain entry/exit links of weight 3"
        sk = int(W[Q, N0]); assert sk == 4 and 5 - ov(qt, nh) == sk - 3, "skip link of weight 4"
        nxt = first.get(N0, -1); prv = last.get(Q, -1)
        rows.append("%d %d %d %d %d %s %s %d %d\n" % (i, C[0], C[6], Q, N0, qt, nh, nxt, prv))
    open(os.path.join(outd, "chains_%d.txt" % h), "w").write("".join(rows))
    ren = {t: j for j, t in enumerate(t for t in range(16) if t != h)}
    out = ["%d %s %s %s %s %s\n" % (ren[int(a[0])], a[1], a[2], a[3], a[4], a[5]) for a in arcs if int(a[0]) != h]
    out.sort(key=lambda l: int(l.split()[0]))
    open(os.path.join(outd, "arcs_%d.txt" % h), "w").write("".join(out))
    summary[h] = dict(chains=len(rows), arcs=len(out), adjacent_pairs=sum(1 for r in rows if int(r.split()[7]) >= 0))
print(json.dumps(summary))
