#!/usr/bin/env python3
"""Round V -- second implementation of the exact two-wrap PATH optima (Theorem V2): for every pair of the result files
(two_wrap_path_221_pairs.jsonl, two_wrap_path_adjacent_27_pairs.jsonl; computed by wrapfam2.py + path_witness.c), the
run-level arcs are rebuilt (wrapfam2.py --arcs-only) and the optimum is recomputed by the layered DP path_layer.c; the
optimal J and the number of optimal end arcs are compared.  Resumable (pairs already in OUT are skipped).
usage: check_pairs_layer.py WORKU WORKV OUT.jsonl RESULTS.jsonl..."""
import sys, os, json, subprocess
here = os.path.dirname(os.path.abspath(__file__)); X = os.path.join(here, "..", "..", "rT", "external", "tholsh_46173")
wu, wv, outp = sys.argv[1:4]; refs = []
for p in sys.argv[4:]: refs += [json.loads(l) for l in open(p)]
done = set()
if os.path.exists(outp): done = {tuple(json.loads(l)["pair"]) for l in open(outp)}
arcs = os.path.join(wv, "check_pairs_arcs.txt")
for r in refs:
    c1, c2 = r["pair"]
    if (c1, c2) in done: continue
    subprocess.run(["python3", "-I", os.path.join(here, "wrapfam2.py"), os.path.join(X, "selection.txt"), os.path.join(X, "base.tsv"), os.path.join(X, "base.txt"), wu, str(c1), str(c2), arcs, "--arcs-only"], check=True, capture_output=True)
    out = json.loads(subprocess.run([os.path.join(wv, "path_layer"), arcs], check=True, capture_output=True, text=True).stdout)
    row = dict(pair=[c1, c2], arcs=out["arcs"], path_witness=dict(J=r["path"]["optimal_J"], end_arcs=r["path"]["optimal_end_arcs"]), path_layer=dict(J=out["optimal_J"], end_arcs=out["optimal_end_arcs"]))
    row["agree"] = row["path_witness"] == row["path_layer"] and out["arcs"] == r["facts"]["arcs"]
    open(outp, "a").write(json.dumps(row) + "\n")
rows = [json.loads(l) for l in open(outp)]
print(json.dumps(dict(pairs=len(rows), agree=sum(r["agree"] for r in rows), least_J=min(r["path_layer"]["J"] for r in rows))))
