#!/usr/bin/env python3
"""Round 163 -- provenance for the hand-proof inventory."""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AUDITED = ["r149/PROOF.md", "r149/AUDIT.md", "r150/PROOF.md",
           "r150/REPORT.md", "r156/THEOREM.md",
           "research/RR_L6_H_TIGHT_AUDIT.md",
           "research/RR_L6_H_EXTRACT_AUDIT.md",
           "research/RR_L6_H_INCIDENCE_AUDIT.md",
           "research/RR_L6_H_ENVELOPE_AUDIT.md",
           "research/RR_L6_H_SAMEHEX_AUDIT.md",
           "research/RR_L6_H_MASTER_AUDIT.md",
           "research/RR_L6_H_SPLICE_AUDIT.md",
           "research/RR_L6_H_FIXEDREP_AUDIT.md",
           "research/RR_L6_HAND_PROOF_NODE_INVENTORY.md",
           "research/RR_L6_PROOF_145_CLAUDE.md",
           "r152/src/rows152.py", "r153/src/theorem153.py",
           "r162/certs/dag_162.json", "r153/certs/dag_153.json"]
INPUTS = ["r152/certs/verify_all_c152.json",
          "r152/certs/verify_piece_c152.json",
          "r152/certs/census_152.json", "r153/certs/theorem_153.json",
          "r153/certs/witness872_153.json",
          "r149/certs/catalogue_complete_149.json",
          "r149/certs/feaslemma_149.json",
          "r150/certs/final150.json", "r150/certs/coverage.json",
          "r150/certs/source_conformance.json",
          "data/verified_872_witness.txt"]


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
    src = sorted(p.name for p in (ROOT / "r163" / "src").glob("*.py"))
    certs = sorted(p.name for p in (ROOT / "r163" / "certs").glob("*.json"))
    tot = {}
    for name, path, keys in (
        ("inventory", "r163/certs/inventory_163.json",
         ("dag_path", "dag_sha256", "node_count",
          "theorem_path_node_count", "status_counts", "hand_proof_nodes",
          "hidden_claims_still_unrepresented", "provenance_defects", "ok")),
        ("recheck", "r163/certs/recheck_163.json", ("ok",)),
        ("hidden", "r163/certs/hidden_163.json",
         ("baseline", "baseline_reproduces_stored_census", "verdicts",
          "load_bearing_but_unrepresented",
          "load_bearing_only_in_an_equivalent_form", "ok")),
        ("evidence", "r163/certs/evidence_163.json",
         ("verdict_tokens", "nodes_without_a_dedicated_audit_round",
          "unrecorded_corrections", "missing_artefacts", "ok")),
        ("dag", "r163/certs/dag_163.json",
         ("supersedes", "source_sha256", "diff_is_exactly_the_repairs",
          "every_derived_field_unchanged", "statuses_unchanged",
          "deps_unchanged")),
        ("hash_invariance", "r163/certs/hash_invariance_163.json",
         ("files", "all_unchanged")),
        ("summary", "r163/certs/hand_proof_inventory_163.json",
         ("category_counts", "ownership_rows_whose_owner_does_not_state_them",
          "remaining_hand_proof_obligations", "ok")),
    ):
        q = ROOT / path
        if q.exists():
            d = json.loads(q.read_text())
            tot[name] = {k: d.get(k) for k in keys}
    out = dict(round=163, node="(inventory: all 12 hand-proof nodes)",
               git_commit=git("rev-parse", "HEAD"),
               git_branch=git("rev-parse", "--abbrev-ref", "HEAD"),
               git_dirty=bool(git("status", "--porcelain")),
               python=sys.version.split()[0], platform=platform.platform(),
               audited_sources={p: sha(p) for p in AUDITED},
               inputs={p: sha(p) for p in INPUTS},
               r163_sources={f"r163/src/{n}": sha(f"r163/src/{n}")
                             for n in src},
               r163_certs={f"r163/certs/{n}": sha(f"r163/certs/{n}")
                           for n in certs},
               audit_doc=sha("r163/HAND_PROOF_INVENTORY.md"),
               totals=tot)
    (ROOT / "r163" / "certs" / "provenance_163.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("git_commit", "git_branch", "git_dirty", "python")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
