#!/usr/bin/env python3
"""Round V -- exact PATH optimum of listed two-wrap families by the layered DP path_layer.c, at run level
(wrapfam2.py --arcs-only) or letter level (fam_letters2.py: class-inside cuts allowed).  Resumable.
usage: pairs_layer.py WORKU WORKV PAIRS.json OUT.jsonl run|letter"""
import sys, os, json, subprocess
here = os.path.dirname(os.path.abspath(__file__)); X = os.path.join(here, "..", "..", "rT", "external", "tholsh_46173")
wu, wv, pairsp, outp, mode = sys.argv[1:6]; pairs = json.load(open(pairsp))
done = set()
if os.path.exists(outp): done = {tuple(json.loads(l)["pair"]) for l in open(outp)}
arcs = os.path.join(wv, "pairs_layer_%s_arcs.txt" % mode)
for c1, c2 in pairs:
    if (c1, c2) in done: continue
    base = [os.path.join(X, "selection.txt"), os.path.join(X, "base.tsv"), os.path.join(X, "base.txt"), wu, str(c1), str(c2), arcs]
    if mode == "run": cmd = ["python3", "-I", os.path.join(here, "wrapfam2.py")] + base + ["--arcs-only"]
    else: cmd = ["python3", "-I", os.path.join(here, "fam_letters2.py")] + base
    info = json.loads(subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip().split("\n")[-1])
    out = json.loads(subprocess.run([os.path.join(wv, "path_layer"), arcs, "24"], check=True, capture_output=True, text=True).stdout)
    open(outp, "a").write(json.dumps(dict(pair=[c1, c2], mode=mode, adjacent=info.get("adjacent"), arcs=out["arcs"], optimal_J=out["optimal_J"], optimal_end_arcs=out["optimal_end_arcs"], end_arcs_le_24=out["end_arcs_le_thresh"])) + "\n")
rows = [json.loads(l) for l in open(outp)]
print(json.dumps(dict(pairs=len(rows), least_J=min(r["optimal_J"] for r in rows))))
