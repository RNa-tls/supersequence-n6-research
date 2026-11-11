#!/usr/bin/env python3
"""Round S -- collect the cross-checks of rR/csrc/kappa_rev.c against the Round R kappa programs into one summary.
usage: kappa_rev_summary.py WORKDIR(tables, logs) CERTDIR(rR/certs/kappa45_rev) ROUND_R_CERTS(rR/certs/kappa45) OUT.json"""
import sys, os, json, hashlib
import numpy as np
wd, cd, rd, outp = sys.argv[1:5]
def norm(path, B):
    a = np.fromfile(path, np.int8); m = int(round(a.size ** 0.5)); A = a.reshape(m, m).copy(); np.fill_diagonal(A, 99); A[A > B] = 99; return A
out = dict(program="rR/csrc/kappa_rev.c (backward search from the exit run, mirrored exit-blocked bound)", trail=1, version=0)
ex = {}
for B in range(4):
    r, d = os.path.join(wd, "rev_B%d.bin" % B), os.path.join(wd, "dfs2_B%d.bin" % B)
    if os.path.exists(r) and os.path.exists(d):
        A, Bm = norm(r, B), norm(d, B); ex[str(B)] = dict(pairs=int((A < 99).sum()), identical_to_kappa_dfs2=bool((A == Bm).all()), differences=int((A != Bm).sum()))
out["exact_tables_B0_to_B3"] = ex
sl = os.path.join(wd, "slack_t1v0.bin")
if os.path.exists(sl): out["slack_table_sha256"] = hashlib.sha256(open(sl, "rb").read()).hexdigest()
pl = {}
for a, ref in ((0, "crit_B3_slackadd0.json"), (1, "crit_B3_slackadd1_planted.json"), (2, "crit_B3_slackadd2_planted.json")):
    mine = json.load(open(os.path.join(cd, "rev_B3_slackadd%d%s.json" % (a, "" if a == 0 else "_planted")))); theirs = json.load(open(os.path.join(rd, ref)))
    A = sorted(tuple(x) for x in mine["undominated"]); Bq = sorted(tuple(x) for x in theirs["undominated"])
    pl["SLACK_ADD_%d" % a] = dict(pairs=len(A), kappa_crit_pairs=len(Bq), identical_lists=(A == Bq), nodes=mine["nodes"])
out["planted_slack_B3"] = pl
runs = {}
for name in sorted(os.listdir(cd)):
    if name.startswith("rev_B4") or name.startswith("rev_B5"):
        d = json.load(open(os.path.join(cd, name)))
        runs[name] = {k: d[k] for k in ("B", "x_range", "undominated_pairs", "undominated_paths", "exit_runs_searched", "exit_runs_skipped", "complete_paths_reached", "nodes", "sec")}
out["target_runs"] = runs
b5 = [v for k, v in runs.items() if k.startswith("rev_B5")]
cov = sorted(tuple(v["x_range"]) for v in b5)
out["kappa_le_4"] = dict(undominated=sum(v["undominated_pairs"] for k, v in runs.items() if k.startswith("rev_B4")), kappa_crit_undominated=0)
out["kappa_5"] = dict(exit_ranges_done=cov, exit_runs_searched=sum(v["exit_runs_searched"] for v in b5), undominated=sum(v["undominated_pairs"] for v in b5), nodes=sum(v["nodes"] for v in b5),
                      complete_for_representatives_0_167=(len(cov) > 0 and cov[0][0] == 0 and cov[-1][1] == 168 and all(cov[i][1] == cov[i + 1][0] for i in range(len(cov) - 1))),
                      kappa_crit_nodes=213147507124, kappa_crit_undominated=0)
json.dump(out, open(outp, "w"), indent=1); print(json.dumps(out)[:1800])
