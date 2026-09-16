#!/usr/bin/env python3
"""Round 156 Phase 15 -- provenance for the H.extract audit."""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

AUDITED = [
    "src/l6_extraction_145.py",
    "src/l6_splicing_145.py",
    "src/l6_fixed_representative_145.py",
    "src/l6_master_identity_144.py",
    "src/l6_same_hex_145.py",
    "research/RR_L6_PROOF_145_CLAUDE.md",
    "r149/PROOF.md",
    "r152/src/rows152.py",
    "r152/certs/verify_all_c152.json",
    "r152/certs/verify_piece_c152.json",
    "r152/certs/census_152.json",
    "r153/certs/dag_153.json",
]
INPUTS = [
    "data/verified_872_witness.txt",
    "outputs/rr_nr6_n5_minima_142.json",
    "outputs/rr_l6_extraction_145.json",
]


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
    src = sorted(p.name for p in (ROOT / "r156" / "src").glob("*.py"))
    certs = sorted(p.name for p in (ROOT / "r156" / "certs").glob("*.json"))
    counts = {}
    for name, path, keys in (
        ("real_covers", "r156/certs/real_covers_156.json", ("stats",)),
        ("cutspace", "r156/certs/cutspace_156.json", ("stats",)),
        ("adversarial", "r156/certs/adversarial_156.json",
         ("runs", "mutation_detections", "catalogue_corruption")),
        ("inputs", "r156/certs/inputs_156.json", ("pool", "n3")),
        ("modelfeed", "r156/certs/modelfeed_156.json",
         ("witness_row", "chain_monotonicity")),
        ("prose_vs_impl", "r156/certs/prose_vs_impl_156.json",
         ("tally", "verdict")),
        ("closers", "r156/certs/closers_156.json", ("total",)),
        ("hunt", "r156/certs/hunt_156.json", ("runs", "patterns",
                                              "max_features", "ok")),
    ):
        q = ROOT / path
        if not q.exists():
            continue
        d = json.loads(q.read_text())
        counts[name] = {k: d.get(k) for k in keys}
    ab = ROOT / "r156" / "certs" / "abstract_156.json"
    if ab.exists():
        d = json.loads(ab.read_text())
        counts["abstract"] = dict(
            decided=sum(e["cases"] for e in d["orbit_exhaustive"]
                        + d["count_exhaustive"] + d["hex_exhaustive"]),
            sampled=sum(e["cases"] for e in d["sampled"]),
            violations=sum(e["violations"] for e in d["orbit_exhaustive"]
                           + d["count_exhaustive"] + d["hex_exhaustive"]
                           + d["sampled"]),
            ablations={a["name"]: a["violations"] for a in d["ablations"]},
            seconds=d["seconds"])
    out = dict(
        round=156, node="H.extract",
        git_commit=git("rev-parse", "HEAD"),
        git_branch=git("rev-parse", "--abbrev-ref", "HEAD"),
        git_dirty=bool(git("status", "--porcelain")),
        python=sys.version.split()[0], platform=platform.platform(),
        audited_sources={p: sha(p) for p in AUDITED},
        inputs={p: sha(p) for p in INPUTS},
        r156_sources={f"r156/src/{n}": sha(f"r156/src/{n}") for n in src},
        r156_certs={f"r156/certs/{n}": sha(f"r156/certs/{n}") for n in certs},
        theorem_doc=sha("r156/THEOREM.md"),
        totals=counts)
    (ROOT / "r156" / "certs" / "provenance_156.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("git_commit", "git_branch", "git_dirty", "python")},
                     ensure_ascii=False))
    print(json.dumps(counts, ensure_ascii=False, indent=1)[:1800])
    return 0


if __name__ == "__main__":
    sys.exit(main())
