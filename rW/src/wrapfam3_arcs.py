#!/usr/bin/env python3
"""Round W -- run-level arcs of a three-wrap family F_{C1,C2,C3} (three chains of three different hosts detached as
closed trails of their own, wraps natural and not cut; every host closed by its skip link), the same construction as
rV/src/wrapfam2.py.  Trails: 0, 1, 2 = C1, C2, C3; 3..18 = the original trails 0..15.
usage: wrapfam3_arcs.py SEL TSV BASE WORK C1 C2 C3 OUT_ARCS.txt   (JSON line on stdout)"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rU", "src"))
import wrapfam as WF
selp, tsvp, basep, work, c1, c2, c3, outp = sys.argv[1:9]; cs = [int(c1), int(c2), int(c3)]
ent, tr, cnat, succ, pred, W = WF.base_tables(selp, tsvp, basep, work); n = len(ent); chains = WF.chains_of(cnat, succ, pred)
CH = [chains[c] for c in cs]
hosts = [int(tr[C[0]]) for C in CH]; assert len(set(hosts)) == 3, "hosts must be different"
tr2 = tr.copy() + 3; succ2 = succ.copy()
for C in CH:
    Q = int(pred[C[0]]); N0 = int(succ[C[6]]); succ2[Q] = N0
for C, tid in zip(CH, (0, 1, 2)):
    tr2[C] = tid; succ2[C[6]] = C[0]
pred2 = np.empty(n, np.int64); pred2[succ2] = np.arange(n)
starts = {int(C[0]) for C in CH}
rows = sorted((int(tr2[y]), y, 0, 3 - int(W[int(pred2[y]), y]), ent[y][:7], ent[int(pred2[y])][:7]) for y in range(n) if y not in starts)
open(outp, "w").write("".join("%d %d %d %d %s %s\n" % r for r in rows))
print(json.dumps(dict(chains=cs, hosts=hosts, arcs=len(rows), skip_weights=[int(W[int(pred[C[0]]), int(succ[C[6]])]) for C in CH])))
