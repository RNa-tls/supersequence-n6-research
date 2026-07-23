#!/usr/bin/env python3
"""Read-only final summary for a completed retry2 N=0 exact search.

This program never resumes or changes the search checkpoint.  It refuses to
state nonexistence unless the result is complete, the checkpoint frontier is
empty, both code-SHA records agree, and the existing structural and literal
replay verifier both pass again in this independent invocation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Mapping


HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
VERIFIER_PATH = HERE.with_name("verify_partial_f1_certificates.py")
SPEC = importlib.util.spec_from_file_location("retry2_verifier", VERIFIER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {VERIFIER_PATH}")
verifier = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verifier
SPEC.loader.exec_module(verifier)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def markdown(report: Mapping[str, Any]) -> str:
    conclusion = report["conclusion"]
    statement = (
        "Under NR6 and the exact-state reduction, the subcase "
        "`F=1,H=0,N=0` contains no complete walk."
        if conclusion["permitted"] else
        "No absence conclusion is permitted."
    )
    return "\n".join([
        "# F=1, H=0, N=0 retry2 final status",
        "",
        f"Status: `{report['status']}`.",
        "",
        statement,
        "",
        "Scope is only the selected NR6/exact-state subcase; it says nothing",
        "about `N>0`, other F slabs, or the global n=6 lower bound.",
        "",
        "```json",
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--certificates", type=Path, required=True)
    args = parser.parse_args()

    result_raw = args.result.read_bytes()
    result = json.loads(result_raw.decode("utf-8"))
    checkpoint_raw = args.checkpoint.read_bytes()
    checkpoint = json.loads(checkpoint_raw.decode("utf-8"))
    structural = verifier.verify(args.result, full_terminal_replay=False)
    literal = verifier.verify(args.result, full_terminal_replay=True)
    stats = result.get("stats", {})
    config = result.get("config", {})
    sha_triplet_result = (result.get("macro_sha256"), result.get("engine_sha256"), result.get("core_sha256"))
    sha_triplet_checkpoint = (checkpoint.get("macro_sha256"), checkpoint.get("engine_sha256"), checkpoint.get("core_sha256"))
    canonical_duplicate_free = len(checkpoint.get("seen_keys", [])) == len(set(checkpoint.get("seen_keys", [])))
    checks = {
        "result_completed": bool(result.get("completed")),
        "node_limit_zero": config.get("node_limit") == 0,
        "unbounded_depth": config.get("max_macro_depth") is None,
        "frontier_exhausted_in_result": int(stats.get("frontier_remaining", -1)) == 0,
        "frontier_empty_in_checkpoint": len(checkpoint.get("frontier", [])) == 0,
        "result_checkpoint_sha_match": sha_triplet_result == sha_triplet_checkpoint,
        "canonical_state_key_duplicates_absent": canonical_duplicate_free,
        "structural_verifier_passed": bool(structural.get("passed")),
        "literal_replay_verifier_passed": bool(literal.get("passed")),
        "coordinates_are_small_N0": config.get("name") == "small_F1_H0_N0" and config.get("n_limit") == 0,
        "success_count_recorded": "success_certificates" in stats,
        "terminal_count_recorded": "terminal_certificates" in stats,
    }
    successes = list(stats.get("success_certificates", []))
    terminals = list(stats.get("terminal_certificates", []))
    checks["no_success_states"] = len(successes) == 0
    permitted = all(checks.values()) and len(successes) == 0
    report: dict[str, Any] = {
        "schema": "partial-f1-n0-retry2-final-summary-v1",
        "status": "N=0 exhaustive search completed and verified" if permitted else "output inconsistency; no conclusion permitted",
        "scope": "NR6/exact-state subcase F=1,H=0,N=0 only",
        "finalizer_sha256": sha256_file(HERE),
        "verifier_sha256": sha256_file(VERIFIER_PATH),
        "input": {"result": str(args.result), "result_sha256": hashlib.sha256(result_raw).hexdigest(), "checkpoint": str(args.checkpoint), "checkpoint_sha256": hashlib.sha256(checkpoint_raw).hexdigest()},
        "checks": checks,
        "search_summary": {"expanded": stats.get("expanded"), "accepted": stats.get("accepted"), "seen": stats.get("seen"), "frontier_remaining": stats.get("frontier_remaining"), "terminal_certificates": len(terminals), "success_certificates": len(successes), "prunes": stats.get("prunes")},
        "structural_verification": structural,
        "literal_replay_verification": literal,
        "conclusion": {"permitted": permitted, "statement": "Under NR6 and exact-state reduction, F=1,H=0,N=0 contains no complete walk." if permitted else None},
    }
    certificate_payload = {"schema": "partial-f1-n0-retry2-terminal-certificates-v1", "result_sha256": report["input"]["result_sha256"], "terminal_certificates": terminals, "success_certificates": successes}
    write(args.output, report)
    write(args.certificates, certificate_payload)
    args.markdown.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "conclusion_permitted": permitted}, ensure_ascii=False))


if __name__ == "__main__":
    main()
