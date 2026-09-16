#!/usr/bin/env python3
"""Round 162 -- provenance for the H.fixedrep audit."""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AUDITED = ["src/l6_fixed_representative_145.py", "src/l6_splicing_145.py",
           "src/l6_rigidity_146.py", "src/l6_cleanroom_146.py",
           "src/l6_same_hex_145.py", "src/l6_extraction_145.py",
           "src/l6_proof_145.py", "src/l6_audit_witness_145.py",
           "r152/src/rows152.py", "r149/PROOF.md", "r156/THEOREM.md",
           "r161/certs/dag_161.json", "r153/certs/dag_153.json"]
INPUTS = ["data/verified_872_witness.txt", "outputs/rr_nr6_n5_minima_142.json",
          "r156/src/extract156.py", "r156/src/run156.py",
          "r156/src/passes156.py", "r161/src/lemmas161.py",
          "r161/src/deps161.py", "r161/certs/deps_161.json"]


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
    src = sorted(p.name for p in (ROOT / "r162" / "src").glob("*.py"))
    certs = sorted(p.name for p in (ROOT / "r162" / "certs").glob("*.json"))
    tot = {}
    for name, path, keys in (
        ("real", "r162/certs/real_162.json", ("stats", "ok")),
        ("bridge", "r162/certs/bridge_162.json", ("stats", "ok")),
        ("equivariance", "r162/certs/equivariance_162.json",
         ("stats", "ok")),
        ("exhaust", "r162/certs/exhaust_162.json",
         ("universe_size", "exhaustive", "stats",
          "distinct_fixed_representatives", "ok")),
        ("downstream", "r162/certs/downstream_162.json",
         ("theorem_path_files", "D1_distinct_predicate_forms",
          "D1_failures", "D3_entry_points_not_enforcing", "D3_failures",
          "D4_positive", "ok")),
        ("dag", "r162/certs/dag_162.json",
         ("diff_is_exactly_the_repairs", "every_derived_field_unchanged",
          "statuses_unchanged", "deps_unchanged")),
        ("hash_invariance", "r162/certs/hash_invariance_162.json",
         ("files", "all_unchanged")),
    ):
        q = ROOT / path
        if q.exists():
            d = json.loads(q.read_text())
            tot[name] = {k: d.get(k) for k in keys}
    out = dict(round=162, node="H.fixedrep",
               git_commit=git("rev-parse", "HEAD"),
               git_branch=git("rev-parse", "--abbrev-ref", "HEAD"),
               git_dirty=bool(git("status", "--porcelain")),
               python=sys.version.split()[0], platform=platform.platform(),
               audited_sources={p: sha(p) for p in AUDITED},
               inputs={p: sha(p) for p in INPUTS},
               r162_sources={f"r162/src/{n}": sha(f"r162/src/{n}")
                             for n in src},
               r162_certs={f"r162/certs/{n}": sha(f"r162/certs/{n}")
                           for n in certs},
               audit_doc=sha("research/RR_L6_H_FIXEDREP_AUDIT.md"),
               totals=tot)
    (ROOT / "r162" / "certs" / "provenance_162.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("git_commit", "git_branch", "git_dirty", "python")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
