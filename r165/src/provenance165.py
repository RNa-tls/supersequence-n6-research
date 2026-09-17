#!/usr/bin/env python3
"""Round 165 -- provenance for the minimal machine-proof basis audit.

No wall-clock field is stored anywhere in this round's certificates; timings
go to stdout only.  Round 163 had to repair exactly that wart.
"""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AUDITED = ["r152/src/rows152.py", "r152/src/checker152.py",
           "r152/src/piece152.py", "r163/HAND_PROOF_INVENTORY.md",
           "r163/certs/dag_163.json", "r164/ROUTE_B_CERTIFICATE_REPLAY.md",
           "r164/certs/route_b_summary_164.json",
           "r164/certs/verifygen_164.json", "r164/certs/targets_164.json"]
INPUTS = ["r152/certs/verify_all_c152.json",
          "r152/certs/verify_subset_152.json",
          "r152/certs/verify_piece_c152.json",
          "r152/certs/verify_piece_152.json",
          "r152/certs/census_152.json",
          "r152/certs/pcert_all_152.txt",
          "r164/certs/extree_prefix_164.txt.gz",
          "r163/src/hidden163.py", "r164/src/routeb164.py"]


def sha(p):
    q = ROOT / p
    return hashlib.sha256(q.read_bytes()).hexdigest() if q.exists() else None


def git(*a):
    try:
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return None


def main():
    src = sorted(p.name for p in (ROOT / "r165" / "src").glob("*.py"))
    certs = sorted(p.name for p in (ROOT / "r165" / "certs").iterdir()
                   if p.is_file())
    tot = {}
    for name, path, keys in (
        ("row_closure", "r165/certs/row_closure_graph_165.json",
         ("remaining_single_route", "baseline", "all_withdrawn",
          "exposed_rows", "monotone", "individually_essential",
          "redundant_given_current_others", "ok")),
        ("minimum_basis", "r165/certs/minimum_basis_165.json",
         ("domination", "exposure", "essential_basis", "minimum_basis",
          "order_consistency", "ok")),
        ("weighted", "r165/certs/weighted_basis_165.json",
         ("basis", "cost", "failure_sensitivity", "ok")),
        ("sat_pilot", "r165/certs/sat_pilot_165.json",
         ("all_correctness_checks_agree", "ok")),
        ("drat", "r165/certs/drat_check_165.json",
         ("solver", "all_verified", "ok")),
        ("dp_pilot", "r165/certs/dp_pilot_165.json",
         ("all_bounds_sound", "any_tight", "median_gap", "ok")),
        ("summary", "r165/certs/basis_summary_165.json",
         ("three_sets", "minimum_basis", "equality_rows",
          "round_166_recommendation", "ok")),
    ):
        q = ROOT / path
        if q.exists():
            d = json.loads(q.read_text())
            tot[name] = {k: d.get(k) for k in keys}
    out = dict(round=165, node="minimal machine-proof basis",
               git_commit=git("rev-parse", "HEAD"),
               git_branch=git("rev-parse", "--abbrev-ref", "HEAD"),
               git_dirty=bool(git("status", "--porcelain")),
               python=sys.version.split()[0], platform=platform.platform(),
               audited_sources={p: sha(p) for p in AUDITED},
               inputs={p: sha(p) for p in INPUTS},
               r165_sources={f"r165/src/{n}": sha(f"r165/src/{n}")
                             for n in src},
               r165_certs={f"r165/certs/{n}": sha(f"r165/certs/{n}")
                           for n in certs},
               audit_doc=sha("r165/MACHINE_PROOF_BASIS.md"),
               totals=tot)
    (ROOT / "r165" / "certs" / "provenance_165.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("git_commit", "git_branch", "git_dirty", "python")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
