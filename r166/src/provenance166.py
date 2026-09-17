#!/usr/bin/env python3
"""Round 166 -- provenance for the extree basis certification audit.

No wall-clock field is stored anywhere in this round's certificates; timings
go to stdout only.  Round 163 had to repair exactly that wart.
"""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AUDITED = ["r152/src/checker152.py", "r152/src/piece152.py",
           "r152/src/extree152.py", "r152/src/rows152.py",
           "r163/HAND_PROOF_INVENTORY.md", "r164/ROUTE_B_CERTIFICATE_REPLAY.md",
           "r165/MACHINE_PROOF_BASIS.md",
           "r165/certs/row_closure_graph_165.json",
           "r165/certs/basis_summary_165.json",
           "r164/certs/extree_prefix_164.txt.gz"]
INPUTS = ["r152/certs/cap_cert_all_152.txt",
          "r152/certs/pcert_all_152.txt",
          "r152/certs/verify_all_c152.json",
          "r152/certs/verify_subset_152.json",
          "r152/certs/verify_piece_c152.json",
          "r152/certs/verify_piece_152.json",
          "r163/src/hidden163.py", "r164/src/routeb164.py",
          "r165/src/closure165.py"]


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
    src = sorted(p.name for p in (ROOT / "r166" / "src").glob("*.py"))
    certs = sorted(p.name for p in (ROOT / "r166" / "certs").iterdir()
                   if p.is_file())
    tot = {}
    for name, path, keys in (
        ("basis_order", "r166/certs/basis_order_166.json",
         ("basis", "counts_match_round_165", "BASIS_REMAINING",
          "census_under_the_basis", "ok")),
        ("bridge", "r166/certs/cross_model_bridge_166.json",
         ("lemma", "move_set_identity", "witness_replay",
          "certified_value_consistency", "coverage", "ok")),
        ("verification", "r166/certs/verification_166.json", ("all_ok",)),
        ("manifest", "r166/certs/extree_manifest_166.json",
         ("totals", "basis_coverage", "ok")),
        ("census", "r166/certs/independent_census_166.json",
         ("certificate_dag", "capacity_agreement", "basis_progress",
          "independence_census", "ok")),
        ("mutations", "r166/certs/mutations_166.json",
         ("invalid", "invalid_rejected", "valid", "valid_accepted",
          "not_expressible_in_this_format", "ok")),
        ("generator_controls", "r166/certs/generator_controls_166.json",
         ("controls", "applied", "caught", "caught_by_the_verifier",
          "caught_by_divergence", "missed", "ok")),
    ):
        q = ROOT / path
        if q.exists():
            d = json.loads(q.read_text())
            tot[name] = {k: d.get(k) for k in keys}
    out = dict(round=166, node="extree basis certification",
               git_commit=git("rev-parse", "HEAD"),
               git_branch=git("rev-parse", "--abbrev-ref", "HEAD"),
               git_dirty=bool(git("status", "--porcelain")),
               python=sys.version.split()[0], platform=platform.platform(),
               audited_sources={p: sha(p) for p in AUDITED},
               inputs={p: sha(p) for p in INPUTS},
               r166_sources={f"r166/src/{n}": sha(f"r166/src/{n}")
                             for n in src},
               r166_certs={f"r166/certs/{n}": sha(f"r166/certs/{n}")
                           for n in certs},
               audit_doc=sha("r166/EXTREE_BASIS_CERTIFICATION.md"),
               totals=tot)
    (ROOT / "r166" / "certs" / "provenance_166.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("git_commit", "git_branch", "git_dirty", "python")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
