#!/usr/bin/env python3
"""Round V -- literal word of a path found in a wrap family F_C (rU/src/wrapfam.py numbering: trail 0 = the detached
chain, trails 1..16 = the original trails 0..15), and its structure in the original 16-trail selection.
usage: route_word.py SEL TSV BASE WORK CHAIN PATH.json OUT_WORD.txt OUT.json"""
import sys, os, json, hashlib
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rU", "src"))
import wrapfam as WF
selp, tsvp, basep, work, ci, pathp, outw, outj = sys.argv[1:9]; ci = int(ci)
ent, tr, cnat, succ, pred, W = WF.base_tables(selp, tsvp, basep, work); n = len(ent); chains = WF.chains_of(cnat, succ, pred)
C = chains[ci]; C0, C6 = C[0], C[6]; Q = int(pred[C0]); N0 = int(succ[C6])
succ2 = succ.copy(); succ2[C6] = C0; succ2[Q] = N0
wit = json.load(open(pathp))["witness"]; route = []; pieces = []
for ev in wit:
    y = ev["start"]; seq = [y]
    while int(succ2[seq[-1]]) != y: seq.append(int(succ2[seq[-1]]))
    route += seq; pieces.append((ev["trail"], y, len(seq)))
assert sorted(route) == list(range(n)), "not a Hamiltonian route"
word = ent[route[0]] + ent[route[0]][:7]; wsum = 0
for x, y in zip(route, route[1:]):
    w = int(W[x, y]); k = 8 - w; f = ent[y]; last = ent[x][7] + ent[x][:7]; assert last[8 - k:] == f[:k] if k else True
    word += f[k:] + f[:7]; wsum += w
assert len(word) == 35288 + wsum
open(outw, "w").write(word + "\n")
# structure in the original selection
links = list(zip(route, route[1:])); nat = sum(1 for x, y in links if succ[x] == y)
joins = [(x, y, int(W[x, y])) for x, y in links if succ[x] != y]; used = {(x, y) for x, y in links}
cuts = [(int(pred[y]), y, int(cnat[pred[y]])) for y in range(n) if (int(pred[y]), y) not in used]
bytr = {}
for _, y, _ in cuts: bytr[int(tr[y])] = bytr.get(int(tr[y]), 0) + 1
wraps = [(x, y) for x, y, w in joins if w == 2]
res = dict(chain=ci, C0=int(C0), C6=int(C6), Q_end=Q, N0=N0, host_trail=int(tr[C0]), length=len(word), sum_link_weights=wsum,
           sha256_with_lf=hashlib.sha256((word + "\n").encode()).hexdigest(), sha256_no_lf=hashlib.sha256(word.encode()).hexdigest(),
           pieces_in_F_C=[dict(trail_F=t, start_run=y, runs=m) for t, y, m in pieces],
           original_selection=dict(pieces_P=len(cuts), cuts_by_weight={str(c): sum(1 for q in cuts if q[2] == c) for c in (2, 3)}, joins_by_weight={str(w): sum(1 for q in joins if q[2] == w) for w in range(2, 9) if any(q[2] == w for q in joins)},
                                   opening_cost=sum(3 - q[2] for q in cuts), join_cost=sum(q[2] - 3 for q in joins), J=sum(3 - q[2] for q in cuts) + sum(q[2] - 3 for q in joins),
                                   trails_with_several_pieces={str(t): v for t, v in bytr.items() if v > 1}, wrap_joins=[[int(x), int(y)] for x, y in wraps],
                                   wrap_is_C6_to_C0=wraps == [(int(C6), int(C0))], joins_inside_one_trail=[[int(x), int(y), w] for x, y, w in joins if tr[x] == tr[y]]))
res["original_selection"]["length_formula"] = 46149 + res["original_selection"]["J"]
json.dump(res, open(outj, "w"), indent=1); print(json.dumps({k: v for k, v in res.items() if k != "pieces_in_F_C"}))
