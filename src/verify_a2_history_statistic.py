#!/usr/bin/env python3
"""Section 3-4: structural identity of the two orbits that drive A2
legality (the ell=4 candidate orbit, implementation index 1, and the
ell=0 candidate orbit, implementation index 120), plus the two-bit
occupancy causal table across all 24 RA2 witnesses.

Reuses outputs/a2_rotation_candidate_tables.json (built in round 9/10 by
analyze_a2_legality_history.py -- NOT re-searched here) plus direct
group-theoretic computation of the fixed candidate-orbit sequence proven
in UNIQUE_WEIGHT2_MOVE_THEOREM.md (target(ell) = compose(p0, g_ell) for
6 FIXED group elements g_ell independent of p0).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

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


macro = _load("vahs_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core

U4_HASHES = [
    "17a42b24ccfb84e90762e3e20e0bce201e745121336c8c899bee6d12c683b870",
    "1d8b48ab7d56ddf782592f86dd50f91c5a4325c09186bd5b4aabaf30c3978e4b",
    "29f6af1e8aee1bf776b8f8d5dc1ad82b2111df9993705086ab22bc945d3ce00e",
    "86ec22eaaba4d52e04d3cac623464de8ad443133e4b6d2f5330168db55af3658",
]
OUTLIER_HASH = "e2b44997e7838537176bd6e0e72ea41df259f429863731b696dc76692beeb98c"


def fixed_candidate_orbit_sequence() -> List[int]:
    """The 6 candidate-target E-orbit indices for ell=0..5 when p0 =
    IDENTITY (the shared canonical convention of all 24 RA2 witnesses),
    computed directly from the group formula, not read off any witness."""
    w2 = core.tail_permutations(2)
    action = core.tail_action(2, w2[0])
    seq = []
    for ell in range(6):
        g = core.compose(core.power(core.SIGMA, ell), action)
        q, _phase = exact.ORBIT_PHASE[g]
        seq.append(q)
    return seq


def orbit_structural_facts(qid: int) -> Dict[str, Any]:
    rep = core.E_REPS[qid]
    ports = core.ports_of_e_orbit(rep)
    kset = core.kset_of_e_orbit(rep)
    return {
        "e_orbit_id": qid,
        "canonical_representative": list(rep),
        "port_count": len(ports),
        "hexagons_touched": list(kset),
    }


def two_bit_table(tables_path: Path) -> Dict[str, Any]:
    data = json.loads(tables_path.read_text(encoding="utf-8"))
    tables = data["tables_by_witness"]
    rows = []
    combo_counts: Dict[str, List[str]] = {}
    for h, entry in tables.items():
        table = entry["candidate_table"]
        row4 = next((r for r in table if r["ell"] == 4), None)
        row0 = next((r for r in table if r["ell"] == 0), None)
        b1 = row4.get("target_existing") if row4 is not None else None
        b120 = row0.get("target_existing") if row0 is not None else None
        key = ("T" if b1 else ("F" if b1 is False else "N")) + \
              ("T" if b120 else ("F" if b120 is False else "N"))
        rows.append({
            "hash": h, "group": entry["group"], "b1_existing_orbit1_at_ell4": b1,
            "b120_existing_orbit120_at_ell0": b120,
            "b1_raw_target_visited_at_ell4": row4.get("target_visited") if row4 else None,
            "legal_ells": entry["legal_ells"], "combo_key": key,
        })
        combo_counts.setdefault(key, []).append(h[:12])
    return {"rows": rows, "combo_membership": combo_counts}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tables", default=str(ROOT / "outputs" / "a2_rotation_candidate_tables.json"))
    parser.add_argument("--output", default=str(ROOT / "outputs" / "a2_two_orbit_truth_table.json"))
    args = parser.parse_args()

    seq = fixed_candidate_orbit_sequence()
    assert seq == [120, 33, 9, 3, 1, 0], f"fixed candidate sequence changed unexpectedly: {seq}"

    orbit1 = orbit_structural_facts(1)
    orbit120 = orbit_structural_facts(120)

    two_bit = two_bit_table(Path(args.tables))

    report = {
        "schema": "a2-two-orbit-truth-table-v1",
        "fixed_candidate_orbit_sequence_ell_0to5_for_p0_identity": seq,
        "orbit_structural_facts": {
            "ell4_candidate_orbit_impl_id_1": orbit1,
            "ell0_candidate_orbit_impl_id_120": orbit120,
        },
        "invariant_names": {
            "orbit_1": "ell=4 candidate orbit (E-orbit of Sigma^4 * unique-weight2-action; canonical rep is its own fixed point under further rotation among the 6 candidates)",
            "orbit_120": "ell=0 candidate orbit (E-orbit of the unique weight-2 action itself, i.e. the action's own canonical representative -- SIGMA)",
        },
        "two_bit_occupancy_table": two_bit,
        "combo_key_legend": "each key is two letters (b1 then b120); T=existing(True), F=fresh-not-visited-not-existing(False), N=target(4) already VISITED (a strictly stronger block than fresh, only applies to the b1/ell=4 position in this corpus)",
        "note_on_TT_combination": "(existing(orbit1)=True, existing(orbit120)=True) is NOT observed in the 24-witness RA2 corpus (0/24) -- any theorem about this combination is necessarily abstract/untested, not corpus-verified.",
        "note_on_FF_combination": "(False, False) covers most of C20 but is NOT uniquely determined by these two bits alone -- within FF, legal_ells varies (typically [1], one exception [3]) depending on the existing/visited status of the other 4 candidate orbits (33, 9, 3, 0).",
        "note_on_NF_combination": "9/24 C20 witnesses have target(4) already VISITED (not merely fresh) at ell=4, combined with existing(orbit120)=False at ell=0 -- this is a third state beyond the binary existing/fresh distinction requested; it is strictly stronger than F for blocking purposes since visited alone already forces A2Legal(.,4)=False regardless of existing().",
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({
        "wrote": args.output,
        "fixed_candidate_orbit_sequence": seq,
        "combo_membership": {k: len(v) for k, v in two_bit["combo_membership"].items()},
    }, indent=2))


if __name__ == "__main__":
    main()
