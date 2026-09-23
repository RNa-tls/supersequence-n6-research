#!/usr/bin/env python3
"""Round 172 (EXPERIMENTAL) -- dual verification gate for experiment trees.

For every COMPLETED experiment tree:
  r1 trees  (L6-EXTREE-4): verifier A4 and verifier B4, compared per batch on
            acceptance, node count, and leaf-class counts
            (A: L_b/L_f/L_p/S_live/S_dead  <->  B: b/f/p/r1_token_split/r1_dead).
  old trees (L6-EXTREE-3): the UNCHANGED Round-168 verifiers A (verifyA168)
            and B (verify168.verify_any), same comparison on nodes.
Also records whether the generator's own counters match the verifiers'.
"""
from __future__ import annotations
import glob, hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r172" / "src"))
sys.path.insert(0, str(ROOT / "r168" / "src"))
import trust172                                                   # noqa: E402
import verifyA172 as VA                                           # noqa: E402
import verifyB172 as VB                                           # noqa: E402
import verifyA168 as A3                                           # noqa: E402
import verify168 as B3                                            # noqa: E402

OUT = "r172/certs/dual_verification_experiment.json"
MAP = {"L_b": "b_hexagon_and_repeat_budget", "L_f": "f_feasibility",
       "L_p": "p_monotone_from_earlier_cells", "S_live": "r1_token_split",
       "S_dead": "r1_dead_no_live_branch"}


def main():
    trust172.setup()
    rows = []
    for jp in sorted(glob.glob(str(ROOT / "r172/certs/exp/*.json"))):
        exp = json.loads(Path(jp).read_text())
        if exp["status"] != "COMPLETED" or "tree" not in exp:
            continue
        rel = exp["tree"]["path"]
        t0 = time.monotonic()
        if exp["mode"] == "r1":
            a = VA.verify(rel, log=lambda *_x, **_k: None)
            b = VB.verify_any4(rel)
            a_leaves = {MAP[k]: v for k, v in (a.get("leaves") or {}).items()}
            agree = (a["ok"] and b["ok"] and a["nodes"] == b["nodes"]
                     == b["hist_checks"] and a_leaves == b["leaves"])
            c = exp["counters"]
            gen = {"b_hexagon_and_repeat_budget": c.get("leaf_b", 0),
                   "f_feasibility": c.get("leaf_f", 0),
                   "p_monotone_from_earlier_cells": c.get("leaf_p_old", 0),
                   "r1_token_split": c.get("leaf_r1_only", 0) - c.get("leaf_r1_dead", 0),
                   "r1_dead_no_live_branch": c.get("leaf_r1_dead", 0)}
            gen = {k: v for k, v in gen.items() if v}
            row = dict(tree=rel, mode="r1", cell=exp["cell"], J=exp["bound"],
                       A4=dict(ok=a["ok"], nodes=a.get("nodes"), leaves=a_leaves,
                               error=a.get("error")),
                       B4=dict(ok=b["ok"], nodes=b.get("nodes"), leaves=b.get("leaves"),
                               hist_checks=b.get("hist_checks"), error=b.get("error")),
                       A_B_agree=agree,
                       generator_counts_match=(gen == b.get("leaves")
                                               and exp["visited_nodes"] == b.get("nodes")))
        else:
            a = A3.verify(rel, log=lambda *_x, **_k: None)
            b = B3.verify_any(rel)
            agree = (a["ok"] and b["ok"] and a["nodes"] == b["nodes"]
                     == b["hist_checks"])
            row = dict(tree=rel, mode="old", cell=exp["cell"], J=exp["bound"],
                       A3=dict(ok=a["ok"], nodes=a.get("nodes")),
                       B3=dict(ok=b["ok"], nodes=b.get("nodes"),
                               hist_checks=b.get("hist_checks")),
                       A_B_agree=agree,
                       generator_counts_match=exp["visited_nodes"] == b.get("nodes"))
        row["plain_sha256"] = exp["tree"]["plain_sha256"]
        row["seconds_noncanonical"] = round(time.monotonic() - t0, 1)
        rows.append(row)
        print(json.dumps({k: row[k] for k in ("tree", "A_B_agree",
                                              "generator_counts_match")}), flush=True)
    out = dict(title="dual verification of experiment trees (EXPERIMENTAL)",
               verifier_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                                for p in ("r172/src/verifyA172.py", "r172/src/verifyB172.py",
                                          "r168/src/verifyA168.py", "r168/src/verify168.py",
                                          "r152/src/extree152.py", "r164/src/routeb164.py")},
               rows=rows, all_agree=all(r["A_B_agree"] and r["generator_counts_match"]
                                        for r in rows))
    (ROOT / OUT).write_text(json.dumps(out, indent=1) + "\n")
    print("ALL_AGREE", out["all_agree"], len(rows))


if __name__ == "__main__":
    main()
