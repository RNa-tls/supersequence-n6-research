#!/usr/bin/env python3
"""Independent ledger verifier for the Round-59 FZ1 candidate audit."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "outputs" / "rr_short_ell2_r1_37_fz1_candidate_orbits.json"
LEDGER = ROOT / "outputs" / "rr_short_ell2_r1_37_fz1_condition_ledger.json"
SEEDS = ROOT / "outputs" / "rr_short_ell2_r1_37_seed3_seed6_candidate_census.json"
R4 = ROOT / "outputs" / "rr_short_ell2_r1_37_r4_candidate_crosscheck.json"
BOUND = ROOT / "outputs" / "rr_short_ell2_r1_37_144z3_bound_audit.json"
RESULT = ROOT / "outputs" / "rr_short_ell2_r1_37_first_component_z3_results.json"
STAGE_D_VERIFIED = ROOT / "outputs" / "rr_short_ell2_r1_37_component_change_verified.json"
OUTPUT = ROOT / "outputs" / "rr_short_ell2_r1_37_fz1_candidate_verified.json"
R1_ORBIT = 91
HUB_HEXAGONS = {0, 1, 4, 6, 8, 9, 18, 24, 96}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


base = load_module(
    "rr_fz1_verify_base",
    ROOT / "src" / "analyze_rr_short_ell2_r1_37_z2_z3_bridge.py",
)
core, exact = base.core, base.exact


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def iter_top_array(path: Path, key: str) -> Iterable[dict[str, object]]:
    marker = (json.dumps(key) + ":[").encode("ascii")
    decoder = json.JSONDecoder()
    with path.open("rb") as handle:
        data = b""
        while marker not in data:
            block = handle.read(1 << 20)
            if not block:
                raise AssertionError(f"missing {key} in {path}")
            data = (data + block)[-len(block) - len(marker):]
        buffer = data[data.index(marker) + len(marker):].decode("utf-8")
        while True:
            buffer = buffer.lstrip(" \t\r\n,")
            if buffer.startswith("]"):
                return
            try:
                value, end = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                block = handle.read(1 << 20)
                if not block:
                    raise
                buffer += block.decode("utf-8")
                continue
            if not isinstance(value, dict):
                raise AssertionError("top-level array contains a non-object")
            yield value
            buffer = buffer[end:]


def independent_fixed_table() -> tuple[list[int], list[int], dict[int, set[int]]]:
    phase_hex: dict[int, set[int]] = {}
    phase_contact: dict[int, set[int]] = {}
    for q in range(exact.ORBIT_COUNT):
        rows = []
        for phase, word in enumerate(core.orbit(core.E_REPS[q], core.E)):
            rq, rp = exact.ORBIT_PHASE[word]
            if (rq, rp) != (q, phase):
                raise AssertionError("independent fixed-table inverse failed")
            rows.append((phase, core.hexagon_id(word)))
        phase_hex[q] = {h for _p, h in rows}
    r1_hex = phase_hex[R1_ORBIT]
    candidates = sorted(q for q in range(exact.ORBIT_COUNT) if q != R1_ORBIT and phase_hex[q] & r1_hex)
    for q in candidates:
        phase_contact[q] = {
            phase for phase, word in enumerate(core.orbit(core.E_REPS[q], core.E))
            if core.hexagon_id(word) in r1_hex
        }
    hub = sorted(q for q in candidates if phase_hex[q] & HUB_HEXAGONS)
    degrees = {
        sum(bool(phase_hex[q] & phase_hex[r]) for r in range(exact.ORBIT_COUNT) if r != q)
        for q in range(exact.ORBIT_COUNT)
    }
    if len(candidates) != 20 or hub != [96, 120, 126, 128, 129] or degrees != {20}:
        raise AssertionError("independent 20/5/degree-20 table reproduction failed")
    return candidates, hub, phase_contact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    candidate_payload = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    seed_payload = json.loads(SEEDS.read_text(encoding="utf-8"))
    r4 = json.loads(R4.read_text(encoding="utf-8"))
    bound = json.loads(BOUND.read_text(encoding="utf-8"))
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    verified = json.loads(STAGE_D_VERIFIED.read_text(encoding="utf-8"))
    if not verified.get("verified"):
        raise AssertionError("the independent Stage-D literal verifier is not green")

    candidates, hub, phases = independent_fixed_table()
    if candidate_payload["hub_touching_candidate_orbits"] != hub:
        raise AssertionError("stored hub candidate list mismatch")
    stored_rows = {int(row["orbit_id"]): row for row in candidate_payload["candidate_orbits"]}
    if sorted(stored_rows) != candidates:
        raise AssertionError("stored 20-orbit list mismatch")
    for q in candidates:
        if set(stored_rows[q]["orbit_91_contact_phases"]) != phases[q]:
            raise AssertionError(f"stored contact phases mismatch for orbit {q}")

    branch_ledger = {str(row["seed_id"]): row for row in ledger["branches"]}
    result_rows = {str(row["seed_id"]): row for row in result["branches"]}
    global_digests: set[str] = set()
    branch_checks = []
    for seed_id, result_row in result_rows.items():
        path = ROOT / result_row["checkpoint"]["path"]
        if sha256_file(path) != result_row["checkpoint"]["sha256"]:
            raise AssertionError(f"checkpoint hash mismatch: {seed_id}")
        node_count = 0
        accepted_candidate = Counter()
        for row in iter_top_array(path, "nodes"):
            node_count += 1
            global_digests.add(str(row["decorated_state_sha256"]))
            edge = row.get("incoming_macro_edge")
            if not edge or edge.get("kind") != "Z3":
                continue
            q = int(edge["target"][0])
            if q in candidates:
                accepted_candidate[str(q)] += 1
        frontier_count = sum(1 for _row in iter_top_array(path, "frontier"))
        stored = branch_ledger[seed_id]
        if node_count != int(stored["node_count"]):
            raise AssertionError(f"node count mismatch: {seed_id}")
        if frontier_count != int(stored["frontier_count"]):
            raise AssertionError(f"frontier count mismatch: {seed_id}")
        if node_count - frontier_count != int(stored["expanded_states"]):
            raise AssertionError(f"expanded conservation mismatch: {seed_id}")
        expected = {q: int(stored["literal_census"]["legal_Z3_target_exposure"][q]) for q in map(str, candidates)}
        actual = {q: int(accepted_candidate[q]) for q in map(str, candidates)}
        if actual != expected:
            raise AssertionError(f"accepted candidate-Z3 ledger mismatch: {seed_id}")
        branch_checks.append({
            "seed_id": seed_id,
            "nodes": node_count,
            "frontier": frontier_count,
            "accepted_candidate_Z3": sum(actual.values()),
            "checkpoint_sha256": result_row["checkpoint"]["sha256"],
        })
    if len(global_digests) != 1318577:
        raise AssertionError(f"global decorated-state count mismatch: {len(global_digests)}")

    literal = ledger["literal_parent_DAG_census"]
    if int(literal["states"]) != int(result["aggregate"]["expansions"]):
        raise AssertionError("literal expanded-state total mismatch")
    for q in map(str, candidates):
        if sum(int(literal["level_counts"][q][level]) for level in ("C0", "C1", "C2", "C3", "C4", "C5", "C6")) != int(literal["candidate_orbit_exposure"][q]):
            raise AssertionError(f"C0-C6 conservation failed for orbit {q}")
    if sum(int(literal["level_counts"][str(q)]["C6"]) for q in candidates) != 0:
        raise AssertionError("stored ledger contains an FZ1 witness despite Stage-D zero witness result")
    if r4["r4_entry_count"] != 22 or len(r4["entries"]) != 22:
        raise AssertionError("R4 crosscheck does not contain exactly 22 rows")
    if {str(row["seed_id"]) for row in seed_payload["branches"]} != {"short_ell2_r1_37:3", "short_ell2_r1_37:6"}:
        raise AssertionError("seed_3/seed_6 split mismatch")
    if bound["verdict"] != "NOT_PROVED_BY_ORBIT_PIGEONHOLE" or not bound["exact_revisit_examples"]:
        raise AssertionError("144-Z3 proof-gap certificate is incomplete")

    payload = {
        "schema": "rr-short-ell2-r1-37-fz1-candidate-independent-verification-v1",
        "verified": True,
        "verification_scope": [
            "independent fixed-table reproduction of 20 candidates, five hub-touch candidates, and degree 20",
            "streamed immutable-checkpoint node/frontier conservation",
            "accepted candidate-Z3 child counts reconstructed from stored literal edge records",
            "C0-C6 arithmetic conservation and zero-C6 agreement with the existing full Stage-D literal verifier",
            "global 1,318,577 decorated-state digest census",
            "Round-57 R4 and seed_3/seed_6 ledger identities",
        ],
        "branches": branch_checks,
        "global_unique_decorated_states": len(global_digests),
        "candidate_count": len(candidates),
        "hub_touching_candidates": hub,
        "artifact_sha256": {
            "candidate_orbits": sha256_file(CANDIDATES),
            "condition_ledger": sha256_file(LEDGER),
            "seed3_seed6": sha256_file(SEEDS),
            "r4_crosscheck": sha256_file(R4),
            "bound_audit": sha256_file(BOUND),
            "stage_D_verified": sha256_file(STAGE_D_VERIFIED),
        },
        "verifier_sha256": sha256_file(Path(__file__)),
    }
    if args.write:
        OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verified": True, "states": len(global_digests), "candidates": len(candidates)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
