#!/usr/bin/env python3
"""Finite controls for the F=1,D=4 port-skeleton lemmas; no search."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve()
CORE_PATH = HERE.with_name("superperm_port_lift.py")
SPEC = importlib.util.spec_from_file_location("f1_port_skeleton_core", CORE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {CORE_PATH}")
core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = core
SPEC.loader.exec_module(core)


def partitions(total: int, largest: int | None = None) -> list[tuple[int, ...]]:
    if total == 0:
        return [()]
    largest = min(total, largest if largest is not None else total)
    answer: list[tuple[int, ...]] = []
    for first in range(largest, 0, -1):
        for rest in partitions(total - first, first):
            answer.append((first,) + rest)
    return answer


def main() -> None:
    ksets = [core.kset_of_e_orbit(rep) for rep in core.E_REPS]
    distinct = [len(set(kset)) == 5 for kset in ksets]
    def rotate(mask: int, shift: int) -> int:
        return sum(1 << ((bit + shift) % 5) for bit in range(5) if mask & (1 << bit))
    def phase_type(mask: int) -> int:
        return min(rotate(mask, shift) for shift in range(5))
    masks_by_deficit = {
        str(deficit): sorted({phase_type(mask) for mask in range(1, 32) if 5 - mask.bit_count() == deficit})
        for deficit in range(1, 5)
    }
    # Deficit partitions use the C5 orbit type of each partial phase mask,
    # but do not pretend that independent rotations of different E-orbits are
    # a global symmetry of a whole state.
    shape_count = 0
    for part in partitions(4):
        choices = [masks_by_deficit[str(deficit)] for deficit in part]
        if part == (2, 2):
            shape_count += len(choices[0]) * (len(choices[0]) + 1) // 2
        elif part == (1, 1, 1, 1):
            shape_count += 1
        else:
            local_count = 1
            for choice in choices:
                local_count *= len(choice)
            shape_count += local_count
    out = {
        "schema": "f1-port-skeleton-finite-control-v1",
        "checker_sha256": hashlib.sha256(HERE.read_bytes()).hexdigest(),
        "core_sha256": hashlib.sha256(CORE_PATH.read_bytes()).hexdigest(),
        "E_orbit_count": len(ksets),
        "five_distinct_hexagons_per_E_orbit": all(distinct),
        "exceptions": [index for index, ok in enumerate(distinct) if not ok],
        "deficit_partitions_of_4": [list(part) for part in partitions(4)],
        "expected_deficit_partitions": [[4], [3, 1], [2, 2], [2, 1, 1], [1, 1, 1, 1]],
        "phase_mask_C5_types_by_deficit": masks_by_deficit,
        "local_deficit_shape_count": shape_count,
        "expected_local_deficit_shape_count": 9,
    }
    out["passed"] = out["five_distinct_hexagons_per_E_orbit"] and out["deficit_partitions_of_4"] == out["expected_deficit_partitions"] and shape_count == 9
    output = HERE.parent.parent / "outputs" / "f1_port_skeleton_finite_control.json"
    output.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
