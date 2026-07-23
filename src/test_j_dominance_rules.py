#!/usr/bin/env python3
"""Empirical falsification tests for five candidate dominance relations
(research/J_DOMINANCE_RULES.md). For each candidate, this searches the
actual reachable neighborhoods of the 9 remaining J seeds for a concrete
pair of states satisfying the candidate's premise, then compares their
REAL one-step legal-continuation behavior (not assumed) to check whether
the claimed dominance could possibly hold. A single confirmed mismatch is
enough to falsify a candidate; absence of a found pair within this bounded
search is reported as UNDETERMINED, never as a proof of safety.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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


macro = _load("dominance_macro", "superperm_partial_f1_macro.py")
exact = macro.exact


def phi(state: "exact.ExactState") -> int:
    n = exact.TARGET_P - state.P
    deficit = 720 - state.visited_count
    return 5 + 6 * n - deficit


def visited_bitset(state: "exact.ExactState") -> int:
    """A single big integer with one bit per visited (hexagon, position)
    slot -- lets us test genuine visited-set containment cheaply."""
    total = 0
    for h, mask in enumerate(state.hex_masks):
        total |= mask << (h * exact.N)
    return total


def legal_continuation_signature(state: "exact.ExactState") -> frozenset:
    """The set of (weight, new_orbit, rotation_length) triples legally
    reachable in one step -- an observable proxy for 'future options'."""
    sig = set()
    for edge in macro.macro_edges(state):
        tr = edge.joint
        if tr.abandonment:
            continue
        if phi(tr.state) < 0:
            continue
        if macro.area_a_prune_reason(tr.state, macro.AREA_A) is not None:
            continue
        sig.add((tr.move.weight, tr.new_orbit, edge.run.ell))
    return frozenset(sig)


def collect_neighborhood(seed_state: "exact.ExactState", max_depth: int, node_cap: int) -> List["exact.ExactState"]:
    """Raw (non-canonicalized, for speed) BFS collecting reachable states --
    used only as a pool to search for dominance-candidate pairs, not as an
    exhaustive search in itself."""
    frontier = deque([(0, seed_state)])
    pool = [seed_state]
    expanded = 0
    while frontier and expanded < node_cap:
        depth, state = frontier.popleft()
        if depth >= max_depth:
            continue
        expanded += 1
        for edge in macro.macro_edges(state):
            tr = edge.joint
            if tr.abandonment:
                continue
            if phi(tr.state) < 0:
                continue
            if macro.area_a_prune_reason(tr.state, macro.AREA_A) is not None:
                continue
            pool.append(tr.state)
            frontier.append((depth + 1, tr.state))
    return pool


def test_candidate_A(pool: List["exact.ExactState"]) -> Dict[str, Any]:
    """A. Superset-visited dominance: if T's visited set ⊇ S's, same
    endpoint, T's remaining resources <= S's, can S be discarded?"""
    by_endpoint: Dict[Tuple[int, ...], List["exact.ExactState"]] = {}
    for s in pool:
        by_endpoint.setdefault(tuple(s.p), []).append(s)
    for endpoint, states in by_endpoint.items():
        for i, s in enumerate(states):
            for t in states[i + 1:]:
                vs, vt = visited_bitset(s), visited_bitset(t)
                if vt & vs == vs and vt != vs and t.visited_count >= s.visited_count:
                    # T visited superset of S, same endpoint. Check resource ordering.
                    if (exact.TARGET_P - t.P) <= (exact.TARGET_P - s.P):
                        sig_s, sig_t = legal_continuation_signature(s), legal_continuation_signature(t)
                        if not sig_t.issuperset(sig_s) and not sig_s.issuperset(sig_t):
                            return {
                                "candidate": "A_superset_visited_dominance",
                                "verdict": "FALSIFIED",
                                "counterexample": {
                                    "s_hash": macro.stable_hash(exact.canonicalize(s)),
                                    "t_hash": macro.stable_hash(exact.canonicalize(t)),
                                    "s_signature": sorted(sig_s), "t_signature": sorted(sig_t),
                                    "note": "T has superset-visited + <= remaining-P-need vs S, "
                                            "same endpoint, yet neither's 1-step legal signature "
                                            "dominates the other's -- T does not safely dominate S.",
                                },
                            }
    return {"candidate": "A_superset_visited_dominance", "verdict": "UNDETERMINED",
            "note": "no qualifying pair found in this bounded pool"}


def test_candidate_B(pool: List["exact.ExactState"]) -> Dict[str, Any]:
    """B. Lower-Phi dominance: does a strictly lower Phi at otherwise-equal
    boundary data mean strictly worse prospects (safe to discard the
    higher-Phi one only if lower-Phi one's options are a subset)?"""
    by_endpoint: Dict[Tuple[int, ...], List["exact.ExactState"]] = {}
    for s in pool:
        by_endpoint.setdefault(tuple(s.p), []).append(s)
    for endpoint, states in by_endpoint.items():
        for i, s in enumerate(states):
            for t in states[i + 1:]:
                if s.P == t.P and phi(s) != phi(t):
                    lower, higher = (s, t) if phi(s) < phi(t) else (t, s)
                    sig_lo, sig_hi = legal_continuation_signature(lower), legal_continuation_signature(higher)
                    if not sig_hi.issuperset(sig_lo):
                        return {
                            "candidate": "B_lower_phi_dominance", "verdict": "FALSIFIED",
                            "counterexample": {
                                "lower_phi_hash": macro.stable_hash(exact.canonicalize(lower)),
                                "higher_phi_hash": macro.stable_hash(exact.canonicalize(higher)),
                                "lower_phi": phi(lower), "higher_phi": phi(higher),
                                "lower_signature": sorted(sig_lo), "higher_signature": sorted(sig_hi),
                                "note": "Same endpoint and P, but the higher-Phi state's legal "
                                        "signature is NOT a superset of the lower-Phi one's.",
                            },
                        }
    return {"candidate": "B_lower_phi_dominance", "verdict": "UNDETERMINED",
            "note": "no qualifying pair found in this bounded pool"}


def test_candidate_C(pool: List["exact.ExactState"]) -> Dict[str, Any]:
    """C. Fewer-unused-orbit dominance: does using fewer orbits so far (at
    matched endpoint/P) dominate?"""
    by_endpoint: Dict[Tuple[int, ...], List["exact.ExactState"]] = {}
    for s in pool:
        by_endpoint.setdefault(tuple(s.p), []).append(s)
    for endpoint, states in by_endpoint.items():
        for i, s in enumerate(states):
            for t in states[i + 1:]:
                if s.P == t.P and s.O != t.O:
                    fewer, more = (s, t) if s.O < t.O else (t, s)
                    sig_fewer, sig_more = legal_continuation_signature(fewer), legal_continuation_signature(more)
                    if not sig_fewer.issuperset(sig_more) and not sig_more.issuperset(sig_fewer):
                        return {
                            "candidate": "C_fewer_unused_orbit_dominance", "verdict": "FALSIFIED",
                            "counterexample": {
                                "fewer_orbit_hash": macro.stable_hash(exact.canonicalize(fewer)),
                                "more_orbit_hash": macro.stable_hash(exact.canonicalize(more)),
                                "fewer_O": fewer.O, "more_O": more.O,
                                "fewer_signature": sorted(sig_fewer), "more_signature": sorted(sig_more),
                            },
                        }
    return {"candidate": "C_fewer_unused_orbit_dominance", "verdict": "UNDETERMINED",
            "note": "no qualifying pair found in this bounded pool"}


def test_candidate_D(pool: List["exact.ExactState"]) -> Dict[str, Any]:
    """D. Phase-mask containment dominance: if T's orbit_masks are
    bitwise-contained in S's (fewer phases used per orbit) at the same
    endpoint/P/O, does T dominate?"""
    by_endpoint: Dict[Tuple[int, ...], List["exact.ExactState"]] = {}
    for s in pool:
        by_endpoint.setdefault(tuple(s.p), []).append(s)
    for endpoint, states in by_endpoint.items():
        for i, s in enumerate(states):
            for t in states[i + 1:]:
                if s.P == t.P and s.O == t.O and s.orbit_masks != t.orbit_masks:
                    contained = all((tm & sm) == tm for tm, sm in zip(t.orbit_masks, s.orbit_masks))
                    if contained:
                        sig_s, sig_t = legal_continuation_signature(s), legal_continuation_signature(t)
                        if not sig_t.issuperset(sig_s):
                            return {
                                "candidate": "D_phase_mask_containment_dominance", "verdict": "FALSIFIED",
                                "counterexample": {
                                    "s_hash": macro.stable_hash(exact.canonicalize(s)),
                                    "t_hash": macro.stable_hash(exact.canonicalize(t)),
                                    "s_signature": sorted(sig_s), "t_signature": sorted(sig_t),
                                },
                            }
    return {"candidate": "D_phase_mask_containment_dominance", "verdict": "UNDETERMINED",
            "note": "no qualifying pair found in this bounded pool"}


def test_candidate_E(pool: List["exact.ExactState"]) -> Dict[str, Any]:
    """E. Same-boundary, larger-used-resource dominance: same endpoint/O/D,
    but S has used strictly more P (further along) -- does S dominate T
    (i.e. is being 'further along' always at least as good)?"""
    by_endpoint: Dict[Tuple[int, ...], List["exact.ExactState"]] = {}
    for s in pool:
        by_endpoint.setdefault(tuple(s.p), []).append(s)
    for endpoint, states in by_endpoint.items():
        for i, s in enumerate(states):
            for t in states[i + 1:]:
                if s.O == t.O and s.D == t.D and s.P != t.P:
                    further, less_far = (s, t) if s.P > t.P else (t, s)
                    sig_further, sig_less = legal_continuation_signature(further), legal_continuation_signature(less_far)
                    if not sig_further.issuperset(sig_less) and not sig_less.issuperset(sig_further):
                        return {
                            "candidate": "E_same_boundary_larger_used_resource_dominance", "verdict": "FALSIFIED",
                            "counterexample": {
                                "further_hash": macro.stable_hash(exact.canonicalize(further)),
                                "less_far_hash": macro.stable_hash(exact.canonicalize(less_far)),
                                "further_P": further.P, "less_far_P": less_far.P,
                                "further_signature": sorted(sig_further), "less_far_signature": sorted(sig_less),
                            },
                        }
    return {"candidate": "E_same_boundary_larger_used_resource_dominance", "verdict": "UNDETERMINED",
            "note": "no qualifying pair found in this bounded pool"}


def main() -> None:
    witnesses = {
        w["target_hash"]: exact.state_from_json(w["final_state_json"])
        for w in json.loads((ROOT / "outputs" / "j_230_literal_witnesses.json").read_text())["witnesses"]
    }
    nine = sorted([
        "45929408de25b866a834c1fe59a79dba3e3d6427efdca37b22220d469d015459",
        "624257c39b75859d58f62e3c7f1369ecea9ce84434d6df14b4b67950abf6b21a",
        "6b42cfe0deafcfa4344e18928f6c7b173dffa0a11a10fd341bb536417e080117",
        "ad74dbc3a5f5c987c4d8595bd5c40f95ce820aafda92009dabd097b57b83acee",
        "c652843b153b6c7b12f1afcbd7f45ac7f467f74dc17706f410de3ab26d3ed6c3",
        "e0f8ed14b4832a7272cbf641aa7ed449588d195046e359d2f61a74ef76dce184",
        "eaa42caf37c5f6ad1ebaa3268d0969e7acbae46f471d66cbc644d2cbb340af63",
        "f4e71fe28ebaa10b5f525b78e86b174fc323fdc6428421731471201dafcff1a9",
        "f95ab0147fb90de8477d344e8e8fc7fca3283357e8bcdc62c0d093d7e69cfb2e",
    ])

    pool: List["exact.ExactState"] = []
    for h in nine:
        pool.extend(collect_neighborhood(witnesses[h], max_depth=5, node_cap=600))
    print(f"pool size: {len(pool)}")

    results = [
        test_candidate_A(pool),
        test_candidate_B(pool),
        test_candidate_C(pool),
        test_candidate_D(pool),
        test_candidate_E(pool),
    ]
    out = {"schema": "j-dominance-rules-v1", "pool_size": len(pool), "results": results}
    (ROOT / "outputs" / "j_reduction_benchmarks.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    for r in results:
        print(r["candidate"], "->", r["verdict"])
    print(json.dumps({"wrote": "outputs/j_reduction_benchmarks.json"}, indent=2))


if __name__ == "__main__":
    main()
