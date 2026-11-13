#!/usr/bin/env python3
"""Round W -- second implementation for the letter-level two-wrap optima: for every listed pair, the 18-trail letter
arcs are rebuilt (rV/src/fam_letters2.py) and the optimum is recomputed by the BACKWARD layered DP rW/csrc/path_back.c;
the value is compared with the forward result (rV/csrc/path_layer.c) given in the input list.  Resumable.
usage: check_back.py WORKU WORKDIR PAIRS.json OUT.jsonl      PAIRS.json: [[c1, c2, forward_J], ...]"""
import sys, os, json, subprocess
here = os.path.dirname(os.path.abspath(__file__)); X = os.path.join(here, "..", "..", "rT", "external", "tholsh_46173")
wu, wd, pairsp, outp = sys.argv[1:5]; pairs = json.load(open(pairsp))
done = set()
if os.path.exists(outp): done = {tuple(json.loads(l)["pair"]) for l in open(outp)}
arcs = os.path.join(wd, "back_arcs.txt")
for c1, c2, fj in pairs:
    if (c1, c2) in done: continue
    subprocess.run(["python3", "-I", os.path.join(here, "..", "..", "rV", "src", "fam_letters2.py"), os.path.join(X, "selection.txt"), os.path.join(X, "base.tsv"), os.path.join(X, "base.txt"), wu, str(c1), str(c2), arcs], check=True, capture_output=True)
    out = json.loads(subprocess.run([os.path.join(wd, "path_back"), arcs, "25"], check=True, capture_output=True, text=True).stdout)
    row = dict(pair=[c1, c2], forward_J=fj, backward_J=out["optimal_J"], agree=out["optimal_J"] == fj, start_arcs_le_25=out["start_arcs_le_thresh"], last_two_layer_states_le_25=out["last_two_layer_states_le_thresh"])
    open(outp, "a").write(json.dumps(row) + "\n"); print(row, flush=True)
rows = [json.loads(l) for l in open(outp)]
print(json.dumps(dict(pairs=len(rows), agree=sum(r["agree"] for r in rows))))
