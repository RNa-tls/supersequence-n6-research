#!/usr/bin/env python3
"""Round 161 -- provenance for the H.splice audit."""
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
    src = sorted(p.name for p in (ROOT / "r161" / "src").glob("*.py"))
    certs = sorted(p.name for p in (ROOT / "r161" / "certs").glob("*.json"))
    tot = {}
    for name, path, keys in (
        ("real", "r161/certs/real_161.json", ("stats", "ok")),
        ("geometry", "r161/certs/geometry_161.json", ("ok",)),
        ("abstract", "r161/certs/abstract_161.json", ("totals", "ok")),
        ("deps", "r161/certs/deps_161.json",
         ("acyclic", "only_C3_depends_on_fixed_representative",
          "fixedrep_experiment", "ok")),
        ("dag", "r161/certs/dag_161.json",
         ("diff_is_exactly_the_repairs", "every_derived_field_unchanged",
          "statuses_unchanged", "deps_unchanged")),
        ("hash_invariance", "r161/certs/hash_invariance_161.json",
         ("files", "all_unchanged")),
    ):
        q = ROOT / path
        if q.exists():
            d = json.loads(q.read_text())
            tot[name] = {k: d.get(k) for k in keys}
    out = dict(round=161, node="H.splice",
               git_commit=git("rev-parse", "HEAD"),
               git_branch=git("rev-parse", "--abbrev-ref", "HEAD"),
               git_dirty=bool(git("status", "--porcelain")),
               python=sys.version.split()[0], platform=platform.platform(),
               audited_sources={p: sha(p) for p in AUDITED},
               inputs={p: sha(p) for p in INPUTS},
               r161_sources={f"r161/src/{n}": sha(f"r161/src/{n}")
                             for n in src},
               r161_certs={f"r161/certs/{n}": sha(f"r161/certs/{n}")
                           for n in certs},
               audit_doc=sha("research/RR_L6_H_SPLICE_AUDIT.md"),
               totals=tot)
    (ROOT / "r161" / "certs" / "provenance_161.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("git_commit", "git_branch", "git_dirty", "python")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
