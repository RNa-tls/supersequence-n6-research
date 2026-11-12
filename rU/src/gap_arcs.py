#!/usr/bin/env python3
"""Round U -- relaxed model for ALL wrap sets at once: the base run-level arcs of the 16 trails plus, for every run of
k >= 1 consecutive complete chains of a trail, the gap arc (head = run after the block, tail = run before it,
cost = 3 - w(tail, head) = -k by the skip weight law).  Removing an unsplit detached chain from a route does not
increase J (Monge at its natural weight-2 link), so a bracket tree of a wrap family with unsplit detached chains has
J >= the bracket-tree bound of this relaxed model.   usage: gap_arcs.py SEL TSV BASE WORK OUT.txt"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wrapfam as WF
selp, tsvp, basep, work, outp = sys.argv[1:6]
ent, tr, cnat, succ, pred, W = WF.base_tables(selp, tsvp, basep, work); chains = WF.chains_of(cnat, succ, pred); start = {ch[0]: ch for ch in chains}
cut = cnat[pred]; rows = [(int(tr[y]), y, 0, 3 - int(cut[y]), ent[y][:7], ent[int(pred[y])][:7]) for y in range(len(ent))]; extra = {}
for ch in chains:
    q = int(pred[ch[0]]); cur = ch; k = 0
    while True:
        k += 1; nx = int(succ[cur[-1]])
        if nx == ch[0] or nx == q or int(succ[nx]) == ch[0] and False: break
        if k > 6: break
        w = int(W[q, nx]); rows.append((int(tr[nx]), 10000 + nx, k, 3 - w, ent[nx][:7], ent[q][:7])); extra[(k, 3 - w)] = extra.get((k, 3 - w), 0) + 1
        if nx not in start: break
        cur = start[nx]
        if q in cur: break
rows.sort(); open(outp, "w").write("".join("%d %d %d %d %s %s\n" % r for r in rows)); print("arcs", len(rows), "gap arcs by (k, cost):", dict(sorted(extra.items())))
