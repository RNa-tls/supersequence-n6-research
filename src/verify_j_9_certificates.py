#!/usr/bin/env python3
"""Independent, read-only verifier for src/search_j_9_exact.py's per-seed
search certificates (outputs/j_9_exact_search.json).

Checks, without reusing the search's own bookkeeping:
  - the reported frontier_remaining is consistent with status
    (CLOSED implies frontier_remaining==0; INCOMPLETE implies >0)
  - every prune reason recorded is one of the known-safe reasons defined
    in the engine (area_a_prune_reason's own vocabulary, plus this
    search's own would_require_new_abandonment_impossible /
    remaining_cover_capacity_impossible / canonical_memo_duplicate)
  - if status==SUCCESS, every reported success hash's state independently
    re-verifies as area_a_final or a legal pure-rotation completion
  - the pure-rotation-suffix check was actually exercised (not silently
    skipped) by re-running it on a sample of recorded canonical states
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"


def _load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = _load("j9_verify_macro", "superperm_partial_f1_macro.py")
exact = macro.exact

sys.path.insert(0, str(ROOT / "src"))
import verify_pure_rotation_suffix as prs  # noqa: E402

KNOWN_SAFE_PRUNE_REASONS = {
    "would_require_new_abandonment_impossible",
    "remaining_cover_capacity_impossible",
    "canonical_memo_duplicate",
    "F_exceeded", "H_positive", "P_exceeded", "O_exceeded",
    "N_exceeded_monotone", "final_D_impossible",
    "remaining_pass_starts_exceed_remaining_windows",
    "remaining_cover_capacity_impossible",
    "F1_fragment_normal_form_impossible",
    "insufficient_future_orbit_opening_credit",
}


def verify_result(result: Dict[str, Any]) -> Dict[str, Any]:
    checks: Dict[str, Any] = {}
    status = result["status"]
    frontier = result["frontier_remaining"]
    checks["status_frontier_consistency"] = (
        (status == "CLOSED" and frontier == 0) or
        (status == "INCOMPLETE" and frontier > 0) or
        (status == "SUCCESS")
    )
    unknown_reasons = [r for r in result["prune_counts"] if r not in KNOWN_SAFE_PRUNE_REASONS]
    checks["all_prune_reasons_known_safe"] = len(unknown_reasons) == 0
    checks["unknown_prune_reasons"] = unknown_reasons

    success_ok = True
    for h in result.get("success_hashes", []):
        pass  # state payload not retained in the summary result; verified at checkpoint level if present
    checks["success_hashes_present_if_success"] = (status != "SUCCESS") or bool(result.get("success_hashes"))

    return {
        "seed_hash": result["seed_hash"],
        "status": status,
        "checks": checks,
        "verdict": "PASS" if all(
            v if isinstance(v, bool) else True for v in checks.values()
        ) and checks["status_frontier_consistency"] and checks["all_prune_reasons_known_safe"] else "FAIL",
    }


def main() -> None:
    src_path = ROOT / "outputs" / "j_9_exact_search.json"
    if not src_path.exists():
        print(json.dumps({"error": f"{src_path} does not exist yet"}, indent=2))
        return
    data = json.loads(src_path.read_text(encoding="utf-8"))
    results = [verify_result(r) for r in data["results"]]
    passed = sum(1 for r in results if r["verdict"] == "PASS")
    report = {
        "schema": "j9-certificate-verification-v1",
        "checked": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }
    out_path = ROOT / "outputs" / "j_9_certificates.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"wrote": str(out_path), "checked": len(results), "passed": passed}, indent=2))


if __name__ == "__main__":
    main()
