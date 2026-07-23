#!/usr/bin/env python3
"""Produce an honest post-run certificate status for the selected N=0 subcase."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
OUTPUTS = ROOT / "outputs"
RESULT = OUTPUTS / "f1_small_n0_search.json"
VERIFY = HERE / "verify_partial_f1_certificates.py"
VERIFY_OUT = OUTPUTS / "f1_small_n0_verification.json"
STATUS_OUT = OUTPUTS / "f1_small_n0_finalization.json"
MD_OUT = OUTPUTS / "F1_SMALL_SUBCASE_CERTIFICATE.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    result: dict[str, object] | None = None
    parse_error = None
    if RESULT.exists():
        try:
            result = json.loads(RESULT.read_text(encoding="utf-8"))
        except Exception as exc:
            parse_error = repr(exc)
    completed = bool(result and result.get("completed"))
    verification: dict[str, object] | None = None
    verification_exit = None
    if completed:
        proc = subprocess.run(
            [sys.executable, str(VERIFY), str(RESULT), "--output", str(VERIFY_OUT)],
            cwd=str(ROOT), capture_output=True, text=True,
        )
        verification_exit = proc.returncode
        if VERIFY_OUT.exists():
            verification = json.loads(VERIFY_OUT.read_text(encoding="utf-8"))
    payload = {
        "schema": "partial-f1-small-n0-finalization-v1",
        "finalizer_sha256": sha(HERE),
        "result_exists": RESULT.exists(),
        "result_sha256": sha(RESULT) if RESULT.exists() else None,
        "result_parse_error": parse_error,
        "completed": completed,
        "verification_exit_code": verification_exit,
        "verification": verification,
        "conclusion_permitted": bool(completed and verification and verification.get("passed")),
        "scope": "selected F=1,H=0,N=0 exact-state subcase only",
    }
    STATUS_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    if payload["conclusion_permitted"]:
        status = "The selected exact subcase completed and its serialized certificates passed read-only verification."
    elif completed:
        status = "The search completed, but verification did not pass; no mathematical conclusion is permitted."
    else:
        status = "The selected search did not complete (or no result was written); no nonexistence conclusion is permitted."
    MD_OUT.write_text(
        "# F=1 small subcase certificate\n\n"
        f"Status: {status}\n\n"
        "Scope: `F=1, H=0, N=0, P=121, O=25, D=4`.  This file never asserts anything about `N>0`, other F slabs, or the full superpermutation problem.\n\n"
        "```json\n" + json.dumps(payload, ensure_ascii=False, indent=2) + "\n```\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
