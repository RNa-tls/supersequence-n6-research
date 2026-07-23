#!/usr/bin/env python3
"""Create a read-only status ledger for the current F=1 research program."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


def sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def load(path: Path) -> Any:
    # PowerShell's UTF8 output may contain a BOM; status files are otherwise
    # ordinary JSON and are read without modifying the active supervisor file.
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else None


def main() -> None:
    status_path = OUT / "f1_small_n0_retry2_status.json"
    status = load(status_path)
    controls = {
        "N0_flow_truth_table": load(OUT / "f1_n0_flow_lemma_truth_table.json"),
        "F1_port_skeleton": load(OUT / "f1_port_skeleton_finite_control.json"),
        "F1_reduction_safety": load(OUT / "f1_reduction_safety.json"),
        "F1_relaxed_port_control": load(OUT / "semi_saturated_f1_relaxed_control.json"),
        "F5_forest_port_control": load(OUT / "semi_saturated_forest_control.json"),
    }
    artifacts = [
        ROOT / "PARTIAL_F1_N0_FLOW_LEMMA.md",
        ROOT / "PARTIAL_F1_PORT_SKELETON.md",
        ROOT / "PARTIAL_F1_REDUCTION_SAFETY.md",
        ROOT / "SEMI_SATURATED_F2_TO_F4_ARCHITECTURE.md",
        ROOT / "work" / "superperm_semisaturated_model.py",
        ROOT / "work" / "run_with_atomic_replace_retry.py",
        ROOT / "work" / "finalize_f1_n0_retry2.py",
    ]
    report = {
        "schema": "superpermutation-research-execution-status-v1",
        "N0_search": status,
        "proof_or_finite_controls": {
            name: {"exists": control is not None, "passed": control.get("passed") if isinstance(control, dict) else None, "valid": control.get("control", {}).get("valid_necessary_port_envelope") if isinstance(control, dict) else None}
            for name, control in controls.items()
        },
        "artifact_sha256": {str(path.relative_to(ROOT)): sha(path) for path in artifacts},
        "scope": {
            "proved": ["F=1,H=0,N=0 joint-flow normal form", "F=1,D=4 port-incidence forest and nine local deficit-shape families", "trivial residual left-S6 stabilizer once p is retained"],
            "finite_controls": ["144 E-orbit distinct-hexagon check", "joint-flow truth table", "F=5 and relaxed F=1 port-envelope controls"],
            "not_claimed": ["completion or failure of active N=0 exhaustive search", "safe visited-mask dominance", "any F=2,3,4 exact enumeration", "L6>=872"],
        },
    }
    status_label = status.get("state") if isinstance(status, dict) else "retry2 status unavailable"
    report["status"] = status_label
    (OUT / "research_execution_status.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Research execution status",
        "",
        f"N=0 search status: `{status_label}`.",
        "",
        "No global lower-bound conclusion is licensed until the active search",
        "has completed and the passive finalizer has recorded both replays.",
        "",
        "## Added proved structure",
        "",
        "- `PARTIAL_F1_N0_FLOW_LEMMA.md`: exact N=0 joint normal form.",
        "- `PARTIAL_F1_PORT_SKELETON.md`: one-double-hexagon forest skeleton.",
        "- `PARTIAL_F1_REDUCTION_SAFETY.md`: no residual value stabilizer and no unproved dominance prune.",
        "- `SEMI_SATURATED_F2_TO_F4_ARCHITECTURE.md`: necessary-only intermediate-slab architecture.",
        "",
        "## Verification gates",
        "",
        "The retry2 supervisor performs structural and literal replay on normal",
        "completion.  A passive independent finalizer then records a final summary",
        "only when the result and empty checkpoint meet every required condition.",
    ]
    (OUT / "RESEARCH_EXECUTION_STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": status_label, "controls": report["proof_or_finite_controls"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
