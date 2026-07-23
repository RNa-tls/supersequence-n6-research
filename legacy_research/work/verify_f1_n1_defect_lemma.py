#!/usr/bin/env python3
"""Finite Boolean audit of the three F=1,H=0,N=1 defect normal forms."""

from __future__ import annotations

import hashlib
import json
from itertools import product
from pathlib import Path


HERE = Path(__file__).resolve()


def main() -> None:
    rows = []
    defect_rows = []
    for weight, abandonment, new_orbit in product((2, 3), (0, 1), (0, 1)):
        blocked_w2_forbidden = weight == 2 and abandonment == 0 and new_orbit == 1
        delta_n = int(weight >= 3) + abandonment - new_orbit
        name = None
        if not blocked_w2_forbidden and delta_n == 1:
            name = {
                (3, 0, 0): "R_blocked_w3_existing",
                (3, 1, 1): "A3_abandon_w3_new",
                (2, 1, 0): "A2_abandon_w2_existing",
            }.get((weight, abandonment, new_orbit), "unexpected")
        row = {"weight": weight, "abandonment": abandonment, "new_E_orbit": new_orbit, "delta_N": delta_n, "blocked_w2_forbidden": blocked_w2_forbidden, "defect_normal_form": name}
        rows.append(row)
        if name is not None:
            defect_rows.append(row)
    report = {"schema": "f1-n1-defect-truth-table-v1", "checker_sha256": hashlib.sha256(HERE.read_bytes()).hexdigest(), "rows": rows, "delta_N_one_normal_forms": defect_rows, "passed": sorted(r["defect_normal_form"] for r in defect_rows) == ["A2_abandon_w2_existing", "A3_abandon_w3_new", "R_blocked_w3_existing"]}
    output = HERE.parent.parent / "outputs" / "f1_n1_defect_truth_table.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
