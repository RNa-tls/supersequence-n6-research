#!/usr/bin/env python3
"""Round 152 -- provenance: hash everything the capacity certification rests on.

Prints (and stores) a single record naming every file in the trusted base, so a
later reader can check that the artefacts they hold are the ones the verdict was
computed from.  Files that are absent are recorded as absent, never skipped.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FILES = [
    "r152/src/checker152.py",
    "r152/src/checker152.c",
    "r152/src/producer152.py",
    "r152/src/producer152.c",
    "r152/src/mutate152.py",
    "r152/src/mutextree152.py",
    "r152/src/pmutate152.py",
    "r152/src/extree152.c",
    "r152/src/extree152.py",
    "r152/src/piece152.c",
    "r152/src/piece152.py",
    "r152/src/agree152.py",
    "r152/src/subset152.py",
    "r152/src/invariants152.py",
    "r152/src/catcheck152.py",
    "r152/src/dag152.py",
    "r152/src/cleanroom152.sh",
    "r152/src/rows152.py",
    "r152/src/heavyfix152.py",
    "r152/CAPACITY_CERTIFICATE.md",
    "r152/certs/claims_152.txt",
    "r152/certs/all_cells_152.json",
    "r152/certs/pilot_cells_152.json",
    "r152/certs/cap_cert_pilot_152.txt",
    "r152/certs/cap_cert_all_152.txt",
    "r152/certs/verify_pilot_152.json",
    "r152/certs/verify_pilot_c152.json",
    "r152/certs/verify_subset_152.json",
    "r152/certs/cap_cert_pysubset_152.txt",
    "r152/certs/pcert_pysubset_152.txt",
    "r152/certs/hygiene_152.json",
    "r152/certs/equality_152.json",
    "r152/certs/dag_152.json",
    "r152/certs/agreement_piece_152.json",
    "r152/certs/verify_all_c152.json",
    "r152/certs/mutations_152.json",
    "r152/certs/census_152.json",
    "r152/certs/heavyfix_152.json",
    "r152/certs/pclaims_152.txt",
    "r152/certs/pcert_all_152.txt",
    "r152/certs/pcert_mut_152.txt",
    "r152/certs/verify_piece_c152.json",
    "r152/certs/verify_piece_152.json",
    "r152/certs/mutations_piece_152.json",
    "r152/certs/mutations_extree_152.json",
    "r152/certs/extree_pilot_152.txt",
    "r152/certs/extree_pilot_152.json",
    "r152/certs/invariants_152.json",
    "r152/certs/catalogue_crosscheck_152.json",
    "r152/certs/agreement_152.json",
    "r152/REPRODUCE.md",
    "research/RR_L6_R147_SOUND_UB.md",
    "r149/PROOF.md",
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    out = {"files": {}}
    for rel in FILES:
        p = ROOT / rel
        out["files"][rel] = (dict(present=True, sha256=sha(p), bytes=p.stat().st_size)
                             if p.exists() else dict(present=False))
    try:
        out["git_head"] = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True).stdout.strip()
        out["git_dirty"] = bool(subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain"],
            capture_output=True, text=True).stdout.strip())
    except Exception as exc:                                  # noqa: BLE001
        out["git_head"] = f"unavailable: {exc}"
    p = ROOT / "r152" / "certs" / "provenance_152.json"
    p.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
