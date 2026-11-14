#!/usr/bin/env python3
"""Round X -- exact optimum of the host-split two-wrap model with the two chain pieces (19 pieces), for listed pairs.
Pieces: C1 and C2 (letter arcs of the detached chains, the arc that cuts the wrap left out: both wraps used; from
rV/src/fam_letters2.py), the 15 other trails (rX/src/split_chains.py arcs), and A = (N0(C1) .. Q(C2)),
B = (N0(C2) .. Q(C1)), one arc each, cost -1.  Optimum by rV/csrc/path_layer.c (layered Held-Karp).  Resumable.
usage: split19.py SEL TSV BASE WORKU SPLITDIR PATH_LAYER PAIRS.txt OUT.jsonl      PAIRS.txt: lines "host c1 c2 J17" """
import sys, os, json, subprocess
here = os.path.dirname(os.path.abspath(__file__))
selp, tsvp, basep, wu, sd, pl, pairsp, outp = sys.argv[1:9]
done = set()
if os.path.exists(outp): done = {tuple(json.loads(l)["pair"]) for l in open(outp)}
tmp = os.path.join(sd, "t19_%d.txt" % os.getpid()); fam = os.path.join(sd, "fam_%d.txt" % os.getpid())
for line in open(pairsp):
    h, c1, c2, j17 = map(int, line.split())
    if (c1, c2) in done: continue
    subprocess.run(["python3", "-I", os.path.join(here, "..", "..", "rV", "src", "fam_letters2.py"), selp, tsvp, basep, wu, str(c1), str(c2), fam], check=True, capture_output=True)
    chain_arcs = [l for l in open(fam) if int(l.split()[0]) in (0, 1)]
    ch = {int(l.split()[0]): l.split() for l in open(os.path.join(sd, "chains_%d.txt" % h))}
    q1, n1, q2, n2 = ch[c1][5], ch[c1][6], ch[c2][5], ch[c2][6]
    other = ["%d %s" % (int(l.split()[0]) + 2, l.split(None, 1)[1]) for l in open(os.path.join(sd, "arcs_%d.txt" % h))]
    rows = chain_arcs + [x if x.endswith("\n") else x + "\n" for x in other] + ["17 0 0 -1 %s %s\n" % (n1, q2), "18 0 0 -1 %s %s\n" % (n2, q1)]
    open(tmp, "w").write("".join(rows))
    out = json.loads(subprocess.run([pl, tmp, "23"], check=True, capture_output=True, text=True).stdout)
    row = dict(host=h, pair=[c1, c2], J17=j17, J19=out["optimal_J"], arcs=out["arcs"], end_arcs_le_23=out.get("end_arcs_le_thresh"))
    open(outp, "a").write(json.dumps(row) + "\n"); print(row, flush=True)
for p in (tmp, fam):
    if os.path.exists(p): os.remove(p)
