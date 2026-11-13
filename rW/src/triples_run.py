#!/usr/bin/env python3
"""Round W -- exact run-level PATH optimum of listed three-wrap families (wrapfam3_arcs.py + rV/csrc/path_layer.c).
Resumable.  usage: triples_run.py WORKU WORKDIR TRIPLES.json OUT.jsonl     TRIPLES.json: [[[c1, c2, c3], beta3], ...]"""
import sys, os, json, subprocess
here = os.path.dirname(os.path.abspath(__file__)); X = os.path.join(here, "..", "..", "rT", "external", "tholsh_46173")
wu, wd, tp, outp = sys.argv[1:5]; T = json.load(open(tp))
done = set()
if os.path.exists(outp): done = {tuple(json.loads(l)["triple"]) for l in open(outp)}
arcs = os.path.join(wd, "t3_arcs.txt")
for (c1, c2, c3), b3 in T:
    if (c1, c2, c3) in done: continue
    info = json.loads(subprocess.run(["python3", "-I", os.path.join(here, "wrapfam3_arcs.py"), os.path.join(X, "selection.txt"), os.path.join(X, "base.tsv"), os.path.join(X, "base.txt"), wu, str(c1), str(c2), str(c3), arcs], check=True, capture_output=True, text=True).stdout)
    out = json.loads(subprocess.run([os.path.join(wd, "path_layer"), arcs, "23"], check=True, capture_output=True, text=True).stdout)
    row = dict(triple=[c1, c2, c3], beta3_run=b3, optimal_J=out["optimal_J"], end_arcs_le_23=out["end_arcs_le_thresh"], arcs=out["arcs"], skip_weights=info["skip_weights"])
    open(outp, "a").write(json.dumps(row) + "\n")
rows = [json.loads(l) for l in open(outp)]
print(json.dumps(dict(triples=len(rows), least_J=min(r["optimal_J"] for r in rows))))
