#!/usr/bin/env python3
"""Finite truth-table audit for the F=1,H=0,N=0 joint flow lemma.

The theorem itself is algebraic.  This checker records every Boolean joint
case compatible with the blocked-w2 lemma and verifies the listed zero-credit
normal forms.  It performs no state-space search.
"""

from __future__ import annotations

import hashlib
import json
from itertools import product
from pathlib import Path


HERE = Path(__file__).resolve()


def main() -> None:
    rows = []
    zero_cases = []
    for weight, abandonment, new_orbit in product((2, 3), (0, 1), (0, 1)):
        blocked_w2_violation = weight == 2 and abandonment == 0 and new_orbit == 1
        delta_n = int(weight >= 3) + abandonment - new_orbit
        row = {"weight": weight, "abandonment": abandonment, "new_E_orbit": new_orbit, "delta_N": delta_n, "blocked_w2_violation": blocked_w2_violation}
        rows.append(row)
        if not blocked_w2_violation and delta_n == 0:
            zero_cases.append(row)
    expected = [
        {"weight": 2, "abandonment": 0, "new_E_orbit": 0, "delta_N": 0, "blocked_w2_violation": False},
        {"weight": 2, "abandonment": 1, "new_E_orbit": 1, "delta_N": 0, "blocked_w2_violation": False},
        {"weight": 3, "abandonment": 0, "new_E_orbit": 1, "delta_N": 0, "blocked_w2_violation": False},
    ]
    report = {"schema": "f1-n0-flow-lemma-truth-table-v1", "checker_sha256": hashlib.sha256(HERE.read_bytes()).hexdigest(), "rows": rows, "zero_N_cases_compatible_with_blocked_w2": zero_cases, "expected_normal_forms": expected, "passed": zero_cases == expected}
    output = HERE.parent.parent / "outputs" / "f1_n0_flow_lemma_truth_table.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
