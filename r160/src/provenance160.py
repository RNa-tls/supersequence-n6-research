#!/usr/bin/env python3
"""Round 160 -- provenance for the H.master audit."""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AUDITED = ["src/l6_envelope_146.py", "src/l6_coupled_144.py",
           "src/l6_cleanroom_146.py", "src/l6_same_hex_145.py",
           "src/l6_incidence_144.py", "src/l6_extraction_145.py",
           "r152/src/rows152.py", "r152/src/heavyfix152.py",
           "r149/PROOF.md", "r156/THEOREM.md",
           "r157/certs/dag_157.json", "r153/certs/dag_153.json"]
INPUTS = ["data/verified_872_witness.txt", "outputs/rr_nr6_n5_minima_142.json",
          "r156/src/extract156.py", "r156/src/abstract156.py",
          "r156/src/corpus156.py", "r156/src/run156.py",
          "r156/src/passes156.py",
          "r152/certs/verify_all_c152.json",
          "r152/certs/verify_piece_c152.json"]


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
    src = sorted(p.name for p in (ROOT / "r160" / "src").glob("*.py"))
    certs = sorted(p.name for p in (ROOT / "r160" / "certs").glob("*.json"))
    tot = {}
    for name, path, keys in (
        ("real", "r160/certs/real_160.json",
         ("stats", "max_abs_difference", "ok")),
        ("symbolic", "r160/certs/symbolic_160.json", ("ok",)),
        ("constant", "r160/certs/constant_160.json",
         ("words", "boundaries", "all_perturbations_always_detected", "ok")),
        ("notation", "r160/certs/notation_160.json",
         ("reachable_files", "contamination_on_path", "ok")),
        ("dag", "r160/certs/dag_160.json",
         ("diff_is_exactly_the_repairs", "every_derived_field_unchanged",
          "statuses_unchanged", "deps_unchanged")),
        ("hash_invariance", "r160/certs/hash_invariance_160.json",
         ("files", "all_unchanged")),
    ):
        q = ROOT / path
        if q.exists():
            d = json.loads(q.read_text())
            tot[name] = {k: d.get(k) for k in keys}
    out = dict(round=160, node="H.master",
               git_commit=git("rev-parse", "HEAD"),
               git_branch=git("rev-parse", "--abbrev-ref", "HEAD"),
               git_dirty=bool(git("status", "--porcelain")),
               python=sys.version.split()[0], platform=platform.platform(),
               audited_sources={p: sha(p) for p in AUDITED},
               inputs={p: sha(p) for p in INPUTS},
               r160_sources={f"r160/src/{n}": sha(f"r160/src/{n}")
                             for n in src},
               r160_certs={f"r160/certs/{n}": sha(f"r160/certs/{n}")
                           for n in certs},
               audit_doc=sha("research/RR_L6_H_MASTER_AUDIT.md"),
               totals=tot)
    (ROOT / "r160" / "certs" / "provenance_160.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("git_commit", "git_branch", "git_dirty", "python")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
