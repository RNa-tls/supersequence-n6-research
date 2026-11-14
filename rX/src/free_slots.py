#!/usr/bin/env python3
"""Round X -- free insertion slots of the wrap chains at run level, and the three-wrap triples they cannot serve.

Run level: every piece is cut at a link between runs.  A detached chain C = (c_0..c_6) used as a wrap is cut at one of
its six inner links c_k -> c_{k+1} (weight 2, cost 1); its piece starts at the entry of c_{k+1} and ends at the exit
of c_k.  Inserting it into a join a -> b (exit of run a, entry of run b) changes J by
    ins = W[a, c_{k+1}] + W[c_k, b] - W[a, b] - 2   (>= 0, Round W lemma W-ins),
and a chain piece at an end of the path costs >= 1 (W[c_k, b] >= 3 and W[a, c_{k+1}] >= 3 for runs a, b outside C:
the only weight-2 steps out of an exit or into an entry are the door steps, which stay in C).  For a stack of chain
pieces inserted in one join, ins_stack >= ins of each member alone (remove the others first).  Hence, for a triple of
chains on three different hosts, every host cut at its gap (16-trail part R, J(R) >= beta3):
    J >= beta3 + #{chains i with no usable free slot},
where a free slot of C_i is (k, a, b) with ins = 0, and it is usable for the triple when a, b lie outside the three
chains, in different trails, and a run of a host trail h_j is allowed only as the end Q(C_j) of the gap piece (for a)
or its start N0(C_j) (for b).
usage: free_slots.py SEL TSV BASE WORKU TRIPLES.json OUT.json"""
import sys, os, json, collections
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rU", "src"))
import wrapfam as WF
selp, tsvp, basep, work, triplesp, outp = sys.argv[1:7]
ent, tr, cnat, succ, pred, W = WF.base_tables(selp, tsvp, basep, work); n = len(ent); chains = WF.chains_of(cnat, succ, pred)
W16 = W.astype(np.int16); tr = np.asarray(tr)
slots = {}; stats = collections.Counter()
for ci, C in enumerate(chains):
    Cs = set(int(x) for x in C); out = []
    for k in range(6):
        T, P1 = int(C[k]), int(C[k + 1]); assert int(W[T, P1]) == 2
        M = W16[:, P1][:, None] + W16[T, :][None, :] - W16 - 2
        assert M.min() >= 0, "insertion lemma violated"          # check of W-ins on all run pairs
        a_idx, b_idx = np.nonzero(M == 0)
        for a, b in zip(a_idx.tolist(), b_idx.tolist()):
            if a in Cs or b in Cs or a == b or tr[a] == tr[b]: continue
            out.append((k, a, b, int(W[a, b]), int(W[a, P1]), int(W[T, b])))
    slots[ci] = out; stats[len(out)] += 1
T3 = json.load(open(triplesp))
killed, alive = [], []
for (c1, c2, c3), b3 in T3:
    cs = (c1, c2, c3); hosts = {int(tr[chains[c][0]]): c for c in cs}
    inC = set(int(x) for c in cs for x in chains[c])
    Q = {c: int(pred[chains[c][0]]) for c in cs}; N0 = {c: int(succ[chains[c][6]]) for c in cs}
    without = []
    for c in cs:
        use = 0
        for (k, a, b, wab, w1, w2) in slots[c]:
            if a in inC or b in inC: continue
            ta, tb = int(tr[a]), int(tr[b])
            if ta in hosts and a != Q[hosts[ta]]: continue
            if tb in hosts and b != N0[hosts[tb]]: continue
            use += 1
        if use == 0: without.append(c)
    lb = b3 + len(without)
    (killed if lb >= 24 else alive).append(dict(triple=list(cs), beta3=b3, chains_without_usable_slot=without, lower_bound=lb))
res = dict(chains=len(chains), slots_per_chain_histogram={str(k): v for k, v in sorted(stats.items())},
           total_slots=sum(len(v) for v in slots.values()), slot_weights=dict(collections.Counter("%d:%d+%d" % (s[3], s[4], s[5]) for v in slots.values() for s in v).most_common()),
           triples=len(T3), killed=len(killed), alive=len(alive), alive_triples=alive,
           killed_by_beta3={str(b): sum(1 for x in killed if x["beta3"] == b) for b in (21, 22, 23)},
           alive_by_beta3={str(b): sum(1 for x in alive if x["beta3"] == b) for b in (21, 22, 23)})
json.dump(res, open(outp, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "alive_triples"}))
json.dump({str(k): v for k, v in slots.items()}, open(outp.replace(".json", "_slots.json"), "w"))
