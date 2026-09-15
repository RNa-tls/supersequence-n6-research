#!/usr/bin/env python3
"""Round 153 -- hash everything the L6 = 872 verdict rests on, and check that
the hashes recorded inside the certificates match the files on disk."""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FILES = [
    # round 153
    "r153/src/recover153.py", "r153/src/eqwit153.c", "r153/src/eqwit153.py",
    "r153/src/eqcompare153.py", "r153/src/coexist153.py",
    "r153/src/covertree153.py", "r153/src/mutate153.py",
    "r153/src/adversarial153.py", "r153/src/theorem153.py",
    "r153/src/dag153.py", "r153/src/witness872_153.py",
    "r153/src/provenance153.py", "r153/src/cleanroom153.sh",
    "r153/src/checker152.c",
    "r153/certs/recover_153.json", "r153/certs/prune_certified_153.txt",
    "r153/certs/E1_table.jsonl", "r153/certs/E1_notable.jsonl",
    "r153/certs/E1_py.jsonl", "r153/certs/E2_table.jsonl",
    "r153/certs/E2_notable.jsonl", "r153/certs/E2_py.jsonl",
    "r153/certs/eqcompare_153.json", "r153/certs/coexist_153.json",
    "r153/certs/covertree_153.txt", "r153/certs/covertree_153.json",
    "r153/certs/mutations_153.json", "r153/certs/adversarial_153.json",
    "r153/certs/theorem_153.json", "r153/certs/dag_153.json",
    "r153/certs/witness872_153.json",
    "r153/logs/cleanroom_153.log",
    "r153/certs/cleanroom_153.json",
    "research/RR_L6_ROUND153_EQUALITY_COEXISTENCE.md",
    # the inputs it consumes
    "r152/certs/verify_all_c152.json", "r152/certs/verify_piece_c152.json",
    "r152/certs/census_152.json", "r152/certs/dag_152.json",
    "r152/src/checker152.py", "r152/src/checker152.c",
    "r152/src/piece152.c", "r152/src/piece152.py", "r152/src/rows152.py",
    "data/verified_872_witness.txt",
    # what round 148 left, kept for comparison only
    "r148/certs/witnesses_148.json",
    "r148/witnesses/row96_table.jsonl", "r148/witnesses/row96_notable.jsonl",
    "r148/witnesses/row92_table.jsonl", "r148/witnesses/row92_notable.jsonl",
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
        out["files"][rel] = (dict(present=True, sha256=sha(p),
                                  bytes=p.stat().st_size)
                             if p.exists() else dict(present=False))
    # hashes recorded INSIDE certificates must match the files
    checks = {}
    ct = json.loads((ROOT / "r153/certs/covertree_153.json").read_text())
    checks["covertree_153.txt"] = (
        ct["tree_sha256"] == out["files"]["r153/certs/covertree_153.txt"]["sha256"])
    w = json.loads((ROOT / "r153/certs/witness872_153.json").read_text())
    checks["verified_872_witness.txt"] = (
        w["sha256"] == out["files"]["data/verified_872_witness.txt"]["sha256"])
    out["recorded_hashes_match_files"] = checks
    out["all_recorded_hashes_match"] = all(checks.values())
    absent = [k for k, v in out["files"].items() if not v["present"]]
    out["absent"] = absent
    try:
        out["git_head"] = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True).stdout.strip()
        out["git_dirty"] = bool(subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain"],
            capture_output=True, text=True).stdout.strip())
    except Exception as exc:                                     # noqa: BLE001
        out["git_head"] = f"unavailable: {exc}"
    out["ok"] = not absent and out["all_recorded_hashes_match"]
    (ROOT / "r153" / "certs" / "provenance_153.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "files"}, indent=1))
    print("files hashed:", len(out["files"]))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
