#!/usr/bin/env python3
"""Round-39 independent re-audit of all 18 historical Target-B boundaries.

Replacement proof path: literal replay -> Round-30 coarse bound -> exact
macro DFS with only ``area_a_prune_reason`` plus the separately proved,
occupancy-independent Round-32 B+R orbit-reuse bound.  This module does not
import, call, or deserialize ``true_phase_walk_capacity``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
sys.setrecursionlimit(20000)


def load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


macro = load("rr39_macro", "superperm_partial_f1_macro.py")
exact, core, AREA_A = macro.exact, macro.core, macro.AREA_A
W1 = macro.W1
MOVE = {move.label: move for move in exact.ALL_MOVES}
W2_10 = MOVE["w2:10"]


def state_hash(st) -> str:
    return hashlib.sha256(repr(st.stable_key()).encode("utf-8")).hexdigest()


def phi(st) -> int:
    return 5 + 6 * (exact.TARGET_P - st.P) - (720 - st.visited_count)


def replay_short(ell: int, preparation: dict[str, Any]):
    st = exact.initial_state()
    for _ in range(ell):
        tr = exact.extend(st, W1); assert tr is not None; st = tr.state
    tr = exact.extend(st, W2_10); assert tr is not None; st = tr.state
    for step in preparation["preparation_trace"]:
        for _ in range(step["ell"]):
            tr = exact.extend(st, W1); assert tr is not None; st = tr.state
        tr = exact.extend(st, MOVE[step["joint"]]); assert tr is not None; st = tr.state
    for _ in range(preparation["ell_profile"][-1]):
        tr = exact.extend(st, W1); assert tr is not None; st = tr.state
    for move in exact.ALL_MOVES:
        if move.weight != 3:
            continue
        tr = exact.extend(st, move)
        if tr is None:
            continue
        q, phase = exact.ORBIT_PHASE[tr.target]
        if (q, phase) == (preparation["r2_target_orbit"], preparation["r2_target_phase"]):
            return tr.state
    raise AssertionError("recorded R2 target did not replay")


def replay_long(witness: dict[str, Any]):
    st = exact.initial_state()
    for _ in range(witness["root_ell"]):
        tr = exact.extend(st, W1); assert tr is not None; st = tr.state
    tr = exact.extend(st, W2_10); assert tr is not None; st = tr.state
    for label in witness["literal_full_word"]:
        rot, joint = label.split(";")
        for _ in range(int(rot.removeprefix("rot^"))):
            tr = exact.extend(st, W1); assert tr is not None; st = tr.state
        tr = exact.extend(st, MOVE[joint]); assert tr is not None; st = tr.state
    return st


def coarse_bound(st) -> tuple[int, int]:
    """Round 30: B <= 5(O_cap + R_cap)+4."""
    need = exact.TARGET_P - st.P + 1
    ocap = max(exact.TARGET_O - st.O, 0)
    rcap = max(AREA_A.n_limit - st.Ndef, 0)
    return need, 5 * (ocap + rcap) + 4


def b_plus_r_bound(st) -> tuple[int, int]:
    """Round 32, recomputed solely from the exact state.

    The present segment contributes at most its current port and its unused
    orbit ports; a fresh future orbit gives at most five hexagons; a
    re-entered orbit gives at most four because it already has a used port.
    """
    need = exact.TARGET_P - st.P + 1
    q, _ = exact.ORBIT_PHASE[st.p]
    used = st.orbit_masks[q].bit_count()
    ocap = max(exact.TARGET_O - st.O, 0)
    rcap = max(AREA_A.n_limit - st.Ndef, 0)
    return need, 1 + (5 - used) + 5 * ocap + 4 * rcap


def new_stats(st) -> dict[str, Any]:
    return {"nodes": 0, "truncated": False, "depth": 0, "max_depth": 0,
            "max_visited": st.visited_count, "leaf_states": 0,
            "prunes": Counter(), "surviving_ells": set()}


def engine_dfs(st, *, node_cap: int, deadline: float, stats: dict[str, Any]):
    """Complete DFS under the same exact Area-A semantics, no phase table."""
    stats["nodes"] += 1
    if stats["nodes"] > node_cap or time.monotonic() > deadline:
        stats["truncated"] = True
        return None
    final_run = macro.rotation_runs(st)[-1]
    if final_run.state.visited_count == 720:
        return []
    stats["max_depth"] = max(stats["max_depth"], stats["depth"])
    stats["max_visited"] = max(stats["max_visited"], st.visited_count)
    alive = False
    for edge in macro.macro_edges(st):
        child = edge.state
        reason = macro.area_a_prune_reason(child, AREA_A)
        if reason is not None:
            stats["prunes"][reason] += 1
            continue
        need, bound = b_plus_r_bound(child)
        if need > bound:
            stats["prunes"]["round32_B_plus_R"] += 1
            continue
        alive = True
        stats["surviving_ells"].add(edge.run.ell)
        stats["depth"] += 1
        result = engine_dfs(child, node_cap=node_cap, deadline=deadline, stats=stats)
        stats["depth"] -= 1
        if result is not None:
            return [edge.label] + result
        if stats["truncated"]:
            return None
    if not alive:
        stats["leaf_states"] += 1
    return None


def existing_maps() -> dict[str, Any]:
    old18 = json.loads((ROOT / "outputs" / "rr_target_b_survivors.json").read_text(encoding="utf-8"))["rows"]
    phase_port = json.loads((ROOT / "outputs" / "rr_refined_phase_capacities.json").read_text(encoding="utf-8"))["rows"]
    r32 = json.loads((ROOT / "outputs" / "rr_short_survivor_ledger.json").read_text(encoding="utf-8"))["rows"]
    flow = json.loads((ROOT / "outputs" / "rr_flow_certificates.json").read_text(encoding="utf-8"))["certificates"]
    return {
        "old18": {r["canonical_state_hash"]: r for r in old18},
        "phase_port": {r["raw_state_hash"]: r for r in phase_port},
        "r32": {r["raw_state_hash"]: r for r in r32},
        "flow": {r["canonical_state_hash"]: r for r in flow},
    }


def rebuild_rows(*, node_cap: int, seconds: float) -> list[dict[str, Any]]:
    preps = json.loads((ROOT / "outputs" / "rr_preparation_words.json").read_text(encoding="utf-8"))
    long = json.loads((ROOT / "outputs" / "rr_six_counterexamples.json").read_text(encoding="utf-8"))
    maps = existing_maps()
    candidates: list[tuple[str, Any, dict[str, Any]]] = []
    for ell_s, group in preps["results_by_ell"].items():
        for prep in group["preparations"]:
            candidates.append((f"short_ell{ell_s}_{prep['raw_state_hash'][:12]}", replay_short(int(ell_s), prep),
                               {"preparation_class": "short", "root_ell": int(ell_s), "P_core": prep["edges_before_completer"], "raw_state_hash": prep["raw_state_hash"][:12]}))
    for index, witness in enumerate(long["witnesses"]):
        candidates.append((f"long_{index}", replay_long(witness),
                           {"preparation_class": "long", "root_ell": witness["root_ell"], "P_core": witness["P_core"], "witness_index": index}))
    assert len(candidates) == 18

    rows = []
    for identity, st, meta in candidates:
        canonical = state_hash(st)[:16]
        old = maps["old18"].get(canonical)
        assert old is not None, (identity, canonical)
        raw = old.get("raw_state_hash", "")
        need_coarse, bound_coarse = coarse_bound(st)
        need_r, bound_r = b_plus_r_bound(st)
        if need_coarse > bound_coarse:
            final, stats = "COARSE_CAPACITY_IMPOSSIBLE", None
        else:
            stats = new_stats(st)
            path = engine_dfs(st, node_cap=node_cap, deadline=time.monotonic() + seconds, stats=stats)
            final = "FOUND_TARGET_B" if path is not None else ("INCOMPLETE" if stats["truncated"] else "EXHAUSTED_NO_PATH")
            if path is not None:
                stats["solution_macro_path"] = path
        port_old = maps["phase_port"].get(raw)
        r32_old = maps["r32"].get(raw)
        flow_old = maps["flow"].get(canonical)
        rows.append({"boundary_id": identity, **meta, "canonical_state_hash": canonical,
                     "coordinates": {"P": st.P, "O": st.O, "Ndef": st.Ndef, "D": st.D, "visited": st.visited_count, "phi": phi(st)},
                     "old_classification": old["verdict"],
                     "old_phase_port": (None if port_old is None else {"bound": port_old["refined_port_bound"], "contradiction": port_old["refined_contradiction"]}),
                     "old_round32": (None if r32_old is None else {"bound": r32_old["bound_B_with_R_penalty"], "contradiction": r32_old["contradiction_B_R"]}),
                     "old_flow_certificate": (None if flow_old is None else flow_old["engine_verdict"]),
                     "coarse": {"need": need_coarse, "bound": bound_coarse, "contradiction": need_coarse > bound_coarse},
                     "round32_B_plus_R": {"need": need_r, "bound": bound_r, "contradiction": need_r > bound_r},
                     "corrected_final_status": final,
                     "exact_engine_flow": (None if stats is None else {"nodes": stats["nodes"], "truncated": stats["truncated"], "max_depth": stats["max_depth"], "max_visited": stats["max_visited"], "leaf_states": stats["leaf_states"], "prunes": dict(stats["prunes"]), "surviving_ells": sorted(stats["surviving_ells"]), **({"solution_macro_path": stats["solution_macro_path"]} if "solution_macro_path" in stats else {})})})
    assert len({r["canonical_state_hash"] for r in rows}) == 18
    return sorted(rows, key=lambda r: (r["preparation_class"], r["root_ell"], r["P_core"], r["canonical_state_hash"]))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--node-cap", type=int, default=8_000_000)
    ap.add_argument("--seconds", type=float, default=900.0)
    ap.add_argument("--out", default=str(ROOT / "outputs" / "rr_target_b_18_boundary_corrected_ledger.json"))
    a = ap.parse_args()
    rows = rebuild_rows(node_cap=a.node_cap, seconds=a.seconds)
    hist = Counter(r["corrected_final_status"] for r in rows)
    assert hist["COARSE_CAPACITY_IMPOSSIBLE"] == 9
    payload = {"schema": "rr-target-b-18-boundary-corrected-ledger-v1",
               "grade": "exact literal replay + sound capacity bounds + exact macro DFS where indicated",
               "phase_helper_used": False,
               "replacement_path": ["Round-30 coarse capacity", "Round-32 B+R bound", "exact macro DFS"],
               "counts": {"all_boundaries": len(rows), **dict(hist)}, "rows": rows}
    Path(a.out).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload["counts"], indent=2))


if __name__ == "__main__":
    main()
