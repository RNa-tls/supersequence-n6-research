#!/usr/bin/env python3
"""Necessary port-incidence envelope for intermediate F slabs at n=6.

The program is intentionally not an enumerator.  It validates a selected set
of E-orbit phase ports against conditions which every NR6 completion must
satisfy, while deliberately omitting ordering, collision and literal-tail
constraints.  Infeasibility in this model is therefore a safe exclusion;
feasibility is only a relaxation witness.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
CORE_PATH = HERE.with_name("superperm_port_lift.py")
SPEC = importlib.util.spec_from_file_location("semi_saturated_core", CORE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {CORE_PATH}")
core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = core
SPEC.loader.exec_module(core)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class Slab:
    k: int
    F: int
    N: int
    H: int

    @property
    def P(self) -> int:
        return 120 + self.F

    @property
    def O(self) -> int:
        return 24 + self.k

    @property
    def D(self) -> int:
        return 5 * self.k - self.F

    @property
    def S(self) -> int:
        return self.O - self.F + self.N

    @property
    def excess_over_867(self) -> int:
        return self.k + self.N + self.H


def validate_slab(slab: Slab) -> list[str]:
    errors: list[str] = []
    if slab.k < 0 or slab.F < 0 or slab.N < 0 or slab.H < 0:
        errors.append("coordinates must be nonnegative")
    if slab.D < 0:
        errors.append("D=5k-F is negative")
    if slab.O > 144:
        errors.append("requested opened E-orbits exceeds 144")
    if slab.S < 1:
        errors.append("strand count is below its initial strand")
    if slab.excess_over_867 > 4:
        errors.append("not inside the hypothetical L<=871 counterexample budget")
    return errors


def port_hexagon(qid: int, phase: int) -> int:
    return core.hexagon_id(core.ports_of_e_orbit(core.E_REPS[qid])[phase])


def validate_ports(slab: Slab, ports: Iterable[tuple[int, int]]) -> dict[str, Any]:
    selected = tuple(sorted(set(ports)))
    raw = tuple(ports)
    errors = validate_slab(slab)
    if len(raw) != len(selected):
        errors.append("a phase port was selected more than once")
    if any(not (0 <= q < 144 and 0 <= phase < 5) for q, phase in selected):
        errors.append("port outside 144-by-5 E-phase universe")
    orbit_masks = [0] * 144
    by_hex: Counter[int] = Counter()
    for q, phase in selected:
        orbit_masks[q] |= 1 << phase
        by_hex[port_hexagon(q, phase)] += 1
    P = len(selected)
    O = sum(mask != 0 for mask in orbit_masks)
    D = sum(5 - mask.bit_count() for mask in orbit_masks if mask)
    uncovered = [h for h in range(120) if by_hex[h] == 0]
    excess = sum(max(0, multiplicity - 1) for multiplicity in by_hex.values())
    if P != slab.P:
        errors.append(f"P mismatch: selected {P}, required {slab.P}")
    if O != slab.O:
        errors.append(f"O mismatch: selected {O}, required {slab.O}")
    if D != slab.D:
        errors.append(f"D mismatch: selected {D}, required {slab.D}")
    if uncovered:
        errors.append(f"{len(uncovered)} rotation hexagons receive no pass start")
    if excess != slab.F:
        errors.append(f"hexagon incidence excess {excess}, required F={slab.F}")
    return {
        "valid_necessary_port_envelope": not errors,
        "errors": errors,
        "derived": {"P": P, "O": O, "D": D, "hexagon_excess": excess, "uncovered_hexagons": uncovered},
        "orbit_phase_masks": [[qid, mask] for qid, mask in enumerate(orbit_masks) if mask],
        "double_or_higher_hexagons": [[h, by_hex[h]] for h in sorted(by_hex) if by_hex[h] >= 2],
        "warning": "This ignores port ordering, rotation-arc partitioning, literal collision avoidance, N-credit chronology and heavy-tail reachability. A valid result is not an exact walk.",
    }


def all_counterexample_coordinate_envelopes() -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for k in range(1, 5):
        for F in range(1, 5 * k + 1):
            for N in range(5 - k):
                for H in range(5 - k - N):
                    slab = Slab(k, F, N, H)
                    if not validate_slab(slab):
                        rows.append({"k": k, "F": F, "N": N, "H": H, "P": slab.P, "O": slab.O, "D": slab.D, "S": slab.S})
    return rows


def forest_control(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cert = data["certificates"][0]
    ids = cert["canonical_cover_representative"]
    ports = [(qid, phase) for qid in ids for phase in range(5)]
    return validate_ports(Slab(k=1, F=5, N=0, H=0), ports)


def f1_relaxed_control(path: Path) -> dict[str, Any]:
    """A deliberately relaxed F=1 witness from a stored 24-partition.

    It validates the envelope only: the selected extra phase is not claimed
    to be chronologically orderable as an exact F=1 walk.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    cert = data["certificates"][0]
    ids = cert["canonical_cover_representative"]
    extra = int(cert["exact_partition_deletion_orbit"])
    base = [qid for qid in ids if qid != extra]
    ports = [(qid, phase) for qid in base for phase in range(5)] + [(extra, 0)]
    return validate_ports(Slab(k=1, F=1, N=0, H=0), ports)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("coordinate-table")
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("forest-control")
    p.add_argument("forest_json", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("f1-relaxed-control")
    p.add_argument("forest_json", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "coordinate-table":
        payload: dict[str, Any] = {"schema": "semi-saturated-coordinate-envelope-v1", "core_sha256": sha256_file(CORE_PATH), "rows": all_counterexample_coordinate_envelopes(), "warning": "Coordinate feasibility only; no enumeration has been performed."}
    elif args.command == "forest-control":
        payload = {"schema": "semi-saturated-forest-control-v1", "core_sha256": sha256_file(CORE_PATH), "input": str(args.forest_json), "control": forest_control(args.forest_json)}
    else:
        payload = {"schema": "semi-saturated-f1-relaxed-control-v1", "core_sha256": sha256_file(CORE_PATH), "input": str(args.forest_json), "control": f1_relaxed_control(args.forest_json), "warning": "This proves only that the port envelope is nonempty; it does not construct a walk."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"schema": payload["schema"], "rows": len(payload.get("rows", [])), "valid": payload.get("control", {}).get("valid_necessary_port_envelope")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
