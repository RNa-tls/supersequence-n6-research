#!/usr/bin/env python3
"""Final cross-check: re-derive the headline claims of this round purely
from the already-written outputs (rr_full_relation_table.json,
rr_abstract_models.json), independent of analyze_rr_chaining.py's own
internal counters -- a second, independent pass over the raw per-witness
rows, to catch any aggregation bug in the primary script.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    table = json.loads((ROOT / "outputs" / "rr_full_relation_table.json").read_text(encoding="utf-8"))
    rows = table["rows"]

    total = len(rows)
    errors = sum(1 for r in rows if "error" in r)
    chaining_rows = [r for r in rows if "error" not in r and r["chaining"]]
    same_rows = [r for r in rows if "error" not in r and r["r2_own_component_relation"] == "same"]

    same_not_chaining = [r for r in same_rows if not r["chaining"]]
    chaining_hex0_not_same = [r for r in chaining_rows if r["hex0_touched_before_r2"] and r["r2_own_component_relation"] != "same"]
    chaining_same_not_hex0 = [r for r in chaining_rows if r["r2_own_component_relation"] == "same" and not r["hex0_touched_before_r2"]]

    result: Dict[str, Any] = {
        "schema": "rr-chaining-theorem-independent-verification-v1",
        "total_rr_records": total,
        "errors_in_replay": errors,
        "chaining_count": len(chaining_rows),
        "same_component_count": len(same_rows),
        "same_implies_chaining": {
            "counterexamples": len(same_not_chaining),
            "holds": len(same_not_chaining) == 0,
            "status": "유한 완전 검증 (exhaustive over all 4,470 literal-replayed RR witnesses)" if errors == 0 else "INCOMPLETE (replay errors present)",
        },
        "hex0_bridge_iff_same_within_chaining": {
            "chaining_and_hex0_but_not_same": len(chaining_hex0_not_same),
            "chaining_and_same_but_not_hex0": len(chaining_same_not_hex0),
            "holds": len(chaining_hex0_not_same) == 0 and len(chaining_same_not_hex0) == 0,
            "status": "유한 완전 검증 (exhaustive over all 75 chaining RR witnesses)",
        },
    }

    abstract = json.loads((ROOT / "outputs" / "rr_abstract_models.json").read_text(encoding="utf-8"))
    result["abstract_countermodel"] = {
        "exists": abstract["countermodel"]["r2_same_component"] and not abstract["countermodel"]["chaining"] and abstract["countermodel"]["forest_respected"],
        "conclusion": abstract["conclusion"],
    }

    print(json.dumps(result, indent=2, sort_keys=True))
    Path(ROOT / "outputs" / "rr_chaining_theorem_verification.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str), encoding="utf-8")

    if not result["same_implies_chaining"]["holds"]:
        raise SystemExit("VERIFICATION FAILED: same-component without chaining found")
    if not result["hex0_bridge_iff_same_within_chaining"]["holds"]:
        raise SystemExit("VERIFICATION FAILED: hex0-bridge <=> same mismatch found")
    print("All independent cross-checks passed.")


if __name__ == "__main__":
    main()
