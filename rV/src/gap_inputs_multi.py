#!/usr/bin/env python3
"""Round V -- gap arcs for blocks of k >= 2 consecutive complete chains of one trail (all k chains detached):
head = run after the block, tail = run before it, cost = 3 - w(tail, head).   usage: gap_inputs_multi.py SEL TSV BASE WORK"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rU", "src"))
import wrapfam as WF
selp, tsvp, basep, work = sys.argv[1:5]
ent, tr, cnat, succ, pred, W = WF.base_tables(selp, tsvp, basep, work); chains = WF.chains_of(cnat, succ, pred); start = {ch[0]: i for i, ch in enumerate(chains)}
rows = []; meta = []; cid = {ch[0]: i for i, ch in enumerate(chains)}
for i, ch in enumerate(chains):
    q = int(pred[ch[0]]); cur = ch; ids = [i]
    while len(ids) < 5:
        nx = int(succ[cur[-1]])
        if nx not in cid or nx == ch[0]: break
        cur = chains[cid[nx]]
        if q in cur: break
        ids.append(cid[nx]); n0 = int(succ[cur[-1]])
        if n0 == ch[0] or n0 == q: break
        rows.append((len(rows), int(tr[ch[0]]), ent[n0][:7], ent[q][:7], 3 - int(W[q, n0]))); meta.append(dict(first_chain=i, k=len(ids), chains=list(ids), host=int(tr[ch[0]]), skip_weight=int(W[q, n0])))
open(os.path.join(work, "gaps_multi.txt"), "w").write("".join("%d %d %s %s %d\n" % r for r in rows))
json.dump(meta, open(os.path.join(work, "gaps_multi.json"), "w"))
import collections
print("multi-chain gap arcs:", len(rows), dict(collections.Counter((m["k"], m["skip_weight"]) for m in meta)))
