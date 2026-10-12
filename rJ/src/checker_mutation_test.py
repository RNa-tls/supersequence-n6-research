#!/usr/bin/env python3
"""Mutation tests for chainset_check.py: every tampered certificate must be rejected."""
import json, subprocess, sys, os, copy, tempfile
word, cert = sys.argv[1], sys.argv[2]
C = json.load(open(cert)); PY = sys.executable
def run(c):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f: json.dump(c, f); p = f.name
    r = subprocess.run([PY, "-I", os.path.join(os.path.dirname(__file__), "chainset_check.py"), word, p], capture_output=True, text=True)
    os.unlink(p); return r.returncode == 0
res = {}
res["original_accepted"] = run(C)
c = copy.deepcopy(C); c["T"] += 1; res["T_plus_1_rejected"] = not run(c)
c = copy.deepcopy(C); c["arcs"] = c["arcs"][:5] + c["arcs"][6:]; res["missing_arc_rejected"] = not run(c)
c = copy.deepcopy(C); q = max(a for a, b, _ in C["arcs"] if b == a + 0) if False else None
H = max(max(a, b) for a, b, _ in C["arcs"]); c["pool"].append([H]); c["rows"].append(["ge", 1.0, ["cut", len(c["pool"]) - 1]]); res["hub_only_cut_rejected"] = not run(c)
c = copy.deepcopy(C)
leaf = next(nd for nd in c["nodes"] if nd["kind"] == "pruned"); leaf["y"] = [(k, v // 2) for k, v in leaf["y"]]; res["halved_leaf_dual_rejected"] = not run(c)
c = copy.deepcopy(C); br = next(nd for nd in c["nodes"] if nd["kind"] == "branch"); c["nodes"] = [nd for nd in c["nodes"] if not (nd["parent"] == br["id"] and nd["val"] == 0)]; res["dropped_subtree_rejected"] = not run(c)
c = copy.deepcopy(C); c["arcs"][10] = [c["arcs"][10][0], c["arcs"][10][1], c["arcs"][10][2] + 1]; res["wrong_weight_rejected"] = not run(c)
print(json.dumps(res)); assert all(res.values())
