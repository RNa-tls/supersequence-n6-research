#!/usr/bin/env python3
"""Round 157 -- provenance for the H.incidence audit."""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

AUDITED = [
    "src/l6_incidence_144.py", "src/l6_incidence_graph_146.py",
    "src/l6_splicing_145.py", "src/l6_cleanroom_146.py",
    "src/l6_circuit_coexist_144.py", "src/l6_master_identity_144.py",
    "src/l6_dag_146.py",
    "research/RR_INCIDENCE_FOREST_LEMMA.md",
    "research/RR_L6_PROOF_145_CLAUDE.md",
    "r148/src/dag148.py", "r150/certs/dag150.json",
    "r153/src/dag153.py", "r153/certs/dag_153.json",
]
INPUTS = ["data/verified_872_witness.txt",
          "outputs/rr_nr6_n5_minima_142.json",
          "r156/src/extract156.py", "r156/src/corpus156.py",
          "r156/src/run156.py", "r156/src/passes156.py"]


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
    src = sorted(p.name for p in (ROOT / "r157" / "src").glob("*.py"))
    certs = sorted(p.name for p in (ROOT / "r157" / "certs").glob("*.json"))
    tot = {}
    for name, path, keys in (
        ("abstract", "r157/certs/abstract_157.json",
         ("exhaustive_cases", "any_T_cases", "sampled_cases", "ok",
          "seconds")),
        ("real", "r157/certs/real_157.json", ("tally", "distinct_profiles",
                                              "ok")),
        ("boundary", "r157/certs/boundary_157.json",
         ("found_tight_but_not_tree", "found_bound_violation", "ok")),
        ("dag", "r157/certs/dag_157.json",
         ("diff_is_exactly_the_repairs", "every_derived_field_unchanged",
          "statuses_unchanged", "deps_unchanged")),
        ("hash_invariance", "r157/certs/hash_invariance_157.json",
         ("files", "all_unchanged")),
    ):
        q = ROOT / path
        if q.exists():
            d = json.loads(q.read_text())
            tot[name] = {k: d.get(k) for k in keys}
    out = dict(round=157, node="H.incidence",
               git_commit=git("rev-parse", "HEAD"),
               git_branch=git("rev-parse", "--abbrev-ref", "HEAD"),
               git_dirty=bool(git("status", "--porcelain")),
               python=sys.version.split()[0], platform=platform.platform(),
               audited_sources={p: sha(p) for p in AUDITED},
               inputs={p: sha(p) for p in INPUTS},
               r157_sources={f"r157/src/{n}": sha(f"r157/src/{n}")
                             for n in src},
               r157_certs={f"r157/certs/{n}": sha(f"r157/certs/{n}")
                           for n in certs},
               audit_doc=sha("research/RR_L6_H_INCIDENCE_AUDIT.md"),
               totals=tot)
    (ROOT / "r157" / "certs" / "provenance_157.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("git_commit", "git_branch", "git_dirty", "python")},
                     ensure_ascii=False))
    print(json.dumps(tot, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
