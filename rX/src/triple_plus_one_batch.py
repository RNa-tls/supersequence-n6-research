#!/usr/bin/env python3
"""Round X -- batch form of rX/src/triple_plus_one.py: the run tables are loaded once and the 17-piece arcs of each
triple are built in process with the construction of rW/src/wrapfam3_arcs.py (three chains of three different hosts
detached as closed trails, wraps natural and not cut, every host closed by its skip link), then reduced to: the kept
chain C_i, the 13 other trails, and each host's single gap arc (cut at the skip link, cost -1).
Bound and use as in triple_plus_one.py; the arcs agree with wrapfam3_arcs.py (checked on the first triples with
--check).  usage: triple_plus_one_batch.py SEL TSV BASE WORKU WORKDIR PATH_LAYER TRIPLES.json OUT.jsonl FIRST LAST [--check]"""
import sys, os, json, subprocess
import numpy as np
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "..", "..", "rU", "src"))
import wrapfam as WF
selp, tsvp, basep, wu, wd, pl, tp, outp, lo, hi = sys.argv[1:11]; lo, hi = int(lo), int(hi); check = "--check" in sys.argv
ent, tr, cnat, succ, pred, W = WF.base_tables(selp, tsvp, basep, wu); n = len(ent); chains = WF.chains_of(cnat, succ, pred)
T = json.load(open(tp)); done = set()
if os.path.exists(outp): done = {tuple(json.loads(l)["triple"]) for l in open(outp)}
sub = os.path.join(wd, "t3b_%d.txt" % os.getpid())
def arcs3(cs):
    CH = [chains[c] for c in cs]; hosts = [int(tr[C[0]]) for C in CH]; assert len(set(hosts)) == 3
    tr2 = tr.copy() + 3; succ2 = succ.copy()
    for C in CH:
        Q = int(pred[C[0]]); N0 = int(succ[C[6]]); succ2[Q] = N0
    for C, tid in zip(CH, (0, 1, 2)):
        tr2[C] = tid; succ2[C[6]] = C[0]
    pred2 = np.empty(n, np.int64); pred2[succ2] = np.arange(n)
    starts = {int(C[0]) for C in CH}
    rows = sorted((int(tr2[y]), y, 0, 3 - int(W[int(pred2[y]), y]), ent[y][:7], ent[int(pred2[y])][:7]) for y in range(n) if y not in starts)
    return rows, hosts
for (c1, c2, c3), b3 in T[lo:hi]:
    if (c1, c2, c3) in done: continue
    rows, hosts = arcs3((c1, c2, c3)); H = [h + 3 for h in hosts]
    if check:
        ref = os.path.join(wd, "ref_%d.txt" % os.getpid())
        subprocess.run(["python3", "-I", os.path.join(here, "..", "..", "rW", "src", "wrapfam3_arcs.py"), selp, tsvp, basep, wu, str(c1), str(c2), str(c3), ref], check=True, capture_output=True)
        assert open(ref).read() == "".join("%d %d %d %d %s %s\n" % r for r in rows), "arcs differ from wrapfam3_arcs.py"
        os.remove(ref)
    vals = []
    for keep in range(3):
        out = [r for r in rows if not (r[0] in (0, 1, 2) and r[0] != keep) and not (r[0] in H and r[3] != -1)]
        ren = {t: i for i, t in enumerate(sorted({r[0] for r in out}))}
        assert len(ren) == 17 and all(sum(1 for r in out if r[0] == h) == 1 for h in H)
        open(sub, "w").write("".join("%d %d %d %d %s %s\n" % (ren[r[0]], r[1], r[2], r[3], r[4], r[5]) for r in sorted(out, key=lambda r: ren[r[0]])))
        v = json.loads(subprocess.run([pl, sub], check=True, capture_output=True, text=True).stdout)["optimal_J"]
        vals.append(v)
        if v >= 24: break
    row = dict(triple=[c1, c2, c3], beta3=b3, beta3_plus=vals, closed=max(vals) >= 24)
    open(outp, "a").write(json.dumps(row) + "\n")
if os.path.exists(sub): os.remove(sub)
rows = [json.loads(l) for l in open(outp)] if os.path.exists(outp) else []
print(json.dumps(dict(done=len(rows), closed=sum(r["closed"] for r in rows))))
