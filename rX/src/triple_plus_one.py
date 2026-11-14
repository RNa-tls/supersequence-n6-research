#!/usr/bin/env python3
"""Round X -- run-level lower bound beta3^{+i} for three-wrap triples: the exact path optimum of the 17 pieces made of
the 13 trails that are not hosts, the three hosts restricted to their gap arcs (cut at the skip link, cost -1), and
the wrap chain C_i (cut at one of its six inner links); the other two chain pieces are removed, which does not
increase J (Round W lemma W-ins with fact W-chain).  So J(three wraps, all hosts cut at their gaps) >= beta3^{+i}
for each i; a triple with max_i beta3^{+i} >= 24 is closed.  Arcs from rW/src/wrapfam3_arcs.py, optimum by
rV/csrc/path_layer.c.  Resumable; tries i = 1, 2, 3 in turn and stops at the first value >= 24.
usage: triple_plus_one.py WORKU WORKDIR PATH_LAYER TRIPLES.json OUT.jsonl [FIRST LAST]"""
import sys, os, json, subprocess
here = os.path.dirname(os.path.abspath(__file__)); X = os.path.join(here, "..", "..", "rT", "external", "tholsh_46173")
wu, wd, pl, tp, outp = sys.argv[1:6]; T = json.load(open(tp))
lo, hi = (int(sys.argv[6]), int(sys.argv[7])) if len(sys.argv) > 7 else (0, len(T))
done = set()
if os.path.exists(outp): done = {tuple(json.loads(l)["triple"]) for l in open(outp)}
arcs = os.path.join(wd, "t3_%d.txt" % os.getpid()); sub = os.path.join(wd, "t3p_%d.txt" % os.getpid())
for (c1, c2, c3), b3 in T[lo:hi]:
    if (c1, c2, c3) in done: continue
    info = json.loads(subprocess.run(["python3", "-I", os.path.join(here, "..", "..", "rW", "src", "wrapfam3_arcs.py"), os.path.join(X, "selection.txt"), os.path.join(X, "base.tsv"), os.path.join(X, "base.txt"), wu, str(c1), str(c2), str(c3), arcs], check=True, capture_output=True, text=True).stdout)
    rows = [l.split() for l in open(arcs)]
    hosts = [h + 3 for h in info["hosts"]]
    # the gap arc of host i starts at N0(C_i): the run that follows the chain; it is the arc of cost -1 of that host
    vals = []
    for keep in range(3):
        out = []
        for r in rows:
            t = int(r[0])
            if t in (0, 1, 2) and t != keep: continue
            if t in hosts and int(r[3]) != -1: continue
            out.append(r)
        ren = {t: i for i, t in enumerate(sorted({int(r[0]) for r in out}))}
        assert len(ren) == 17 and all(sum(1 for r in out if int(r[0]) == h) == 1 for h in hosts), "host must keep exactly its gap arc"
        open(sub, "w").write("".join("%d %s %s %s %s %s\n" % (ren[int(r[0])], r[1], r[2], r[3], r[4], r[5]) for r in sorted(out, key=lambda r: ren[int(r[0])])))
        v = json.loads(subprocess.run([pl, sub], check=True, capture_output=True, text=True).stdout)["optimal_J"]
        vals.append(v)
        if v >= 24: break
    row = dict(triple=[c1, c2, c3], beta3=b3, beta3_plus=vals, closed=max(vals) >= 24)
    open(outp, "a").write(json.dumps(row) + "\n"); print(row, flush=True)
for p in (arcs, sub):
    if os.path.exists(p): os.remove(p)
