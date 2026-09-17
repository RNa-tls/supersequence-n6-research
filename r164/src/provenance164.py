#!/usr/bin/env python3
"""Round 164 -- provenance for the Route-B certificate replay audit.

No wall-clock field is stored anywhere in this round's certificates; timings
go to stdout only.  Round 163 had to repair exactly that wart.
"""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AUDITED = ["r152/src/checker152.py", "r152/src/piece152.py",
           "r152/src/extree152.py", "r152/src/rows152.py",
           "r150/PROOF.md", "r149/PROOF.md",
           "r163/HAND_PROOF_INVENTORY.md",
           "r163/certs/dag_163.json", "r163/certs/coverage_163.json"]
INPUTS = ["r152/certs/cap_cert_all_152.txt", "r152/certs/pcert_all_152.txt",
          "r152/certs/extree_pilot_152.txt",
          "r152/certs/verify_all_c152.json",
          "r152/certs/verify_subset_152.json",
          "r152/certs/verify_piece_c152.json",
          "r152/certs/verify_piece_152.json",
          "r152/certs/census_152.json",
          "r163/src/hidden163.py"]


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
    src = sorted(p.name for p in (ROOT / "r164" / "src").glob("*.py"))
    certs = sorted(p.name for p in (ROOT / "r164" / "certs").iterdir()
                   if p.is_file())
    tot = {}
    for name, path, keys in (
        ("targets", "r164/certs/targets_164.json",
         ("chain", "piece", "total_targets", "exhaustion_trees",
          "matches_round_163_expectation", "ok")),
        ("replay", "r164/certs/route_b_replay_164.json",
         ("targets", "lower_bounds", "upper_bounds", "gap", "ok")),
        ("mutations", "r164/certs/mutations_164.json", ("ok",)),
        ("impact", "r164/certs/impact_164.json",
         ("route_comparison", "census_exposure", "ok")),
        ("gentree", "r164/certs/gentree_164.json",
         ("prefix", "cells_built", "targets_built", "total_search_nodes",
          "stored_bytes", "ok")),
        ("verifygen", "r164/certs/verifygen_164.json",
         ("cells", "targets_in_the_file", "r164_validator", "r152_validator",
          "caps_match_route_a",
          "targets_upper_certified_by_two_validators", "ok")),
    ):
        q = ROOT / path
        if q.exists():
            d = json.loads(q.read_text())
            tot[name] = {k: d.get(k) for k in keys}
    out = dict(round=164, node="Route B certificate replay",
               git_commit=git("rev-parse", "HEAD"),
               git_branch=git("rev-parse", "--abbrev-ref", "HEAD"),
               git_dirty=bool(git("status", "--porcelain")),
               python=sys.version.split()[0], platform=platform.platform(),
               audited_sources={p: sha(p) for p in AUDITED},
               inputs={p: sha(p) for p in INPUTS},
               r164_sources={f"r164/src/{n}": sha(f"r164/src/{n}")
                             for n in src},
               r164_certs={f"r164/certs/{n}": sha(f"r164/certs/{n}")
                           for n in certs},
               audit_doc=sha("r164/ROUTE_B_CERTIFICATE_REPLAY.md"),
               totals=tot)
    (ROOT / "r164" / "certs" / "provenance_164.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("git_commit", "git_branch", "git_dirty", "python")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
