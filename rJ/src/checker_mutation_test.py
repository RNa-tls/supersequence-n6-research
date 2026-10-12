#!/usr/bin/env python3
"""Mutation tests for the certificate checkers: every tampered certificate must be rejected.
usage: checker_mutation_test.py WORD CERT [CHECKER]   (CHECKER = chainset_check.py (default) or chainset_check2.py)"""
import json, subprocess, sys, os, copy, tempfile, gzip
word, cert = sys.argv[1], sys.argv[2]
CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), sys.argv[3] if len(sys.argv) > 3 else "chainset_check.py")
C = json.load(gzip.open(cert, "rt") if cert.endswith(".gz") else open(cert)); PY = sys.executable
def run(c):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f: json.dump(c, f); p = f.name
    r = subprocess.run([PY, "-I", CK, word, p], capture_output=True, text=True)
    os.unlink(p); return r.returncode == 0
res = {}
res["original_accepted"] = run(C)
c = copy.deepcopy(C); c["T"] += 1; res["T_plus_1_rejected"] = not run(c)
c = copy.deepcopy(C); c["arcs"] = c["arcs"][:5] + c["arcs"][6:]; res["missing_arc_rejected"] = not run(c)
H = max(max(a, b) for a, b, _ in C["arcs"]); c = copy.deepcopy(C); c["pool"].append([H]); c["rows"].append(["ge", 1.0, ["cut", len(c["pool"]) - 1]]); res["hub_only_cut_rejected"] = not run(c)
c = copy.deepcopy(C)
leaf = next(nd for nd in c["nodes"] if nd["kind"] == "pruned"); leaf["y"] = [(k, v // 2) for k, v in leaf["y"]]; res["halved_leaf_dual_rejected"] = not run(c)
c = copy.deepcopy(C); br = next(nd for nd in c["nodes"] if nd["kind"] == "branch"); c["nodes"] = [nd for nd in c["nodes"] if not (nd["parent"] == br["id"] and nd["val"] == 0)]; res["dropped_subtree_rejected"] = not run(c)
c = copy.deepcopy(C); c["arcs"][10] = [c["arcs"][10][0], c["arcs"][10][1], c["arcs"][10][2] + 1]; res["wrong_weight_rejected"] = not run(c)
# an arc fixed at the root without justification (one that the root dual does not price out)
c = copy.deepcopy(C); f0 = set(c["root"]["fixed0"])
cand = [j for j in range(len(c["arcs"])) if j not in f0]
c["root"]["fixed0"] = sorted(f0 | {cand[0]}); res["unjustified_root_fixing_rejected"] = not run(c)
# a branch child relabelled so that the split is no longer {x_j = 0, x_j = 1}
c = copy.deepcopy(C); br = next(nd for nd in c["nodes"] if nd["kind"] == "branch")
ch = [nd for nd in c["nodes"] if nd["parent"] == br["id"]]; ch[0]["val"] = ch[1]["val"]; res["broken_split_rejected"] = not run(c)
# an INCUMBENT record smuggled in as a leaf
c = copy.deepcopy(C); leaf = next(nd for nd in c["nodes"] if nd["kind"] == "pruned"); leaf["kind"] = "INCUMBENT"; res["incumbent_leaf_rejected"] = not run(c)
# a cut row whose set contains the depot D
Dn = H - 1; c = copy.deepcopy(C); c["pool"][0] = sorted(set(c["pool"][0]) | {Dn}); res["cut_with_depot_rejected"] = not run(c)
print(json.dumps(dict(checker=os.path.basename(CK), **res))); assert all(res.values())
