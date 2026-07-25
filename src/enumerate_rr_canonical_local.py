#!/usr/bin/env python3
"""Round 19, section 1: a genuinely CANONICAL root-local enumerator.

Round 17's enumerator deduped on the RAW state.stable_key() (a labeling
error found and corrected in Round 18). This script does the real thing:
it dedups on the canonicalized state paired with a canonically-transported
history summary.

THE SUBTLETY THIS SCRIPT HANDLES (and Round 17 did not have to):
exact.canonicalize() returns the lexicographically-least left-S6 translate
but NOT the alpha that achieved it. History fields like "R1's target orbit"
are RAW orbit ids, so pairing a canonical state with a raw orbit id is
inconsistent -- the same structural situation would get different keys
depending on which left-S6 copy the search happened to reach. The fix is
to canonicalize the PAIR: for every alpha achieving the minimal state key
(there can be several -- a nontrivial stabilizer), transport the history
orbit ids through LEFT_ORBIT_ACTION[alpha] and take the lexicographic
minimum over those tied alphas. Tie counts are recorded in the output so
the reader can see whether stabilizers actually occur.

History summary fields, and why each is present (section 1 requires
justifying necessity or giving an ablation counterexample):
  - r_count            REQUIRED. Distinguishes "0 R events so far" from
                       "1 R event so far"; without it a state reached
                       before R1 and after R1 would merge and the RR word
                       structure (exactly 2 R events) could not be tracked.
                       Ablation: see --ablate r_count.
  - r1_target_orbit    REQUIRED for the chaining relation, which is
                       defined as (R1 target orbit == R2 source orbit).
                       Without it chaining is simply not computable at the
                       R2 boundary. Ablation: see --ablate r1_target.
Fields deliberately NOT included (and why): the full path, the hub
identity, and the abandonment ell are all recoverable from the state or
fixed per-root, so adding them would only refine the quotient without
changing any relation this round computes. This is asserted, not proved,
and is re-tested empirically by --ablate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
ENGINE_FILES = [
    WORK / "superperm_partial_f1.py",
    WORK / "superperm_partial_f1_macro.py",
    WORK / "superperm_port_lift.py",
]
ENGINE_VERSION = "rr-canonical-local-enumerator-v1"


def _load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = _load("ercl_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
move_by_label = {m.label: m for m in exact.ALL_MOVES}
W2_10 = move_by_label["w2:10"]


def joint_kind(weight: int, abandonment: bool, new_orbit: bool) -> str:
    return {
        (2, False, False): "Z2", (2, True, False): "A2", (2, True, True): "Z2abandon",
        (3, False, False): "R", (3, False, True): "Z3", (3, True, False): "J", (3, True, True): "A3",
    }.get((weight, abandonment, new_orbit), "?")


def engine_sha256() -> Dict[str, str]:
    return {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in ENGINE_FILES if f.exists()}


def state_hash(state) -> str:
    return hashlib.sha256(repr(state.stable_key()).encode("utf-8")).hexdigest()


def canonical_alphas(state) -> Tuple[Tuple[object, ...], List[int]]:
    """Returns (minimal stable_key, ALL alpha indices achieving it).
    len(alphas) > 1 means the state has a nontrivial left-S6 stabilizer."""
    best_key = None
    best_alphas: List[int] = []
    for a in range(len(core.ALL_WORDS)):
        key = exact.relabel_sparse_key(state, a)
        if best_key is None or key < best_key:
            best_key, best_alphas = key, [a]
        elif key == best_key:
            best_alphas.append(a)
    return best_key, best_alphas


def canonical_pair_key(state, history: Tuple[Any, ...]) -> Tuple[Any, ...]:
    """Canonicalize the (state, history) PAIR. history entries that are orbit
    ids get transported through each tied alpha; the lexicographic minimum
    over tied alphas is the canonical representative of the pair."""
    best_key, alphas = canonical_alphas(state)
    r_count, r1_target_orbit = history
    variants = []
    for a in alphas:
        if r1_target_orbit is None:
            transported = None
        else:
            transported = exact.LEFT_ORBIT_ACTION[a][r1_target_orbit][0]
        variants.append((r_count, transported))
    return (best_key, min(variants)), len(alphas)


def component_map(state):
    parent: Dict[Any, Any] = {}

    def find(node):
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for q, mask in enumerate(state.orbit_masks):
        for phase in range(5):
            if mask & (1 << phase):
                port = core.ports_of_e_orbit(core.E_REPS[q])[phase]
                union(("q", q), ("h", core.hexagon_id(port)))
    return parent, find


def legal_trailing_edges(state) -> List[str]:
    out = []
    for edge in macro.macro_edges(state):
        if macro.area_a_prune_reason(edge.joint.state, macro.AREA_A) is None:
            out.append(f"rot^{edge.run.ell};{edge.joint.move.label}")
    return sorted(out)


def abandonment_root(init, ell: int):
    cur = init
    for _ in range(ell):
        cur = exact.extend(cur, W1).state
    atr = exact.extend(cur, W2_10)
    assert atr is not None and atr.abandonment and atr.state.F == 1
    return atr.state


def enumerate_canonical(root_state, hex0: int, depth_ceiling: int,
                        ablate: Optional[str] = None,
                        collect_post_r2: bool = True) -> Dict[str, Any]:
    """BFS with canonical (state, history) dedup. No node/edge/time cap;
    termination is frontier-empty (bounded by the declared depth_ceiling,
    which is reported, never used silently)."""

    def make_key(state, rc, r1t):
        if ablate == "r_count":
            hist = (0, r1t)
        elif ablate == "r1_target":
            hist = (rc, None)
        elif ablate == "both":
            hist = (0, None)
        else:
            hist = (rc, r1t)
        return canonical_pair_key(state, hist)

    root_key, root_ties = make_key(root_state, 0, None)
    frontier = deque([(root_state, 0, None, 0)])
    seen = {root_key}
    expanded = 0
    generated_edges = 0
    duplicate_count = 0
    max_depth_seen = 0
    stabilizer_ties: Counter = Counter([root_ties])
    terminal_reasons: Counter = Counter()
    post_r2: Dict[str, Dict[str, Any]] = {}
    rr_final_count = 0
    chaining_count = 0
    same_count = 0
    completer_orbits: Counter = Counter()

    while frontier:
        state, rc, r1t, depth = frontier.popleft()
        expanded += 1
        max_depth_seen = max(max_depth_seen, depth)
        if depth >= depth_ceiling:
            terminal_reasons["depth_ceiling_reached"] += 1
            continue
        edges = list(macro.macro_edges(state))
        if not edges:
            terminal_reasons["no_macro_edges"] += 1
            continue
        for edge in edges:
            generated_edges += 1
            tr = edge.joint
            reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
            if reason is not None:
                terminal_reasons[reason] += 1
                continue
            kind = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            if tr.target is not None and core.hexagon_id(tr.target) == hex0:
                q, _ = exact.ORBIT_PHASE[tr.target]
                completer_orbits[q] += 1
            nrc, nr1t = rc, r1t
            if kind == "R":
                nrc = rc + 1
                src_q, src_ph = exact.ORBIT_PHASE[edge.run.state.p]
                tgt_q, tgt_ph = exact.ORBIT_PHASE[tr.target]
                if nrc == 1:
                    nr1t = tgt_q
                elif nrc == 2 and tr.state.F == 1 and tr.state.H == 0:
                    rr_final_count += 1
                    pm, find = component_map(edge.run.state)
                    sr = find(("q", src_q)) if ("q", src_q) in pm else None
                    tg = find(("q", tgt_q)) if ("q", tgt_q) in pm else None
                    chaining = (r1t == src_q)
                    is_same = sr is not None and sr == tg
                    if chaining:
                        chaining_count += 1
                    if is_same:
                        same_count += 1
                    if collect_post_r2 and is_same:
                        ck, ties = canonical_pair_key(tr.state, (2, r1t))
                        ch = hashlib.sha256(repr(ck).encode()).hexdigest()
                        if ch not in post_r2:
                            canon = exact.canonicalize(tr.state)
                            post_r2[ch] = {
                                "canonical_pair_hash": ch,
                                "canonical_state_hash": state_hash(canon),
                                "raw_state_hash": state_hash(tr.state),
                                "stabilizer_tie_count": ties,
                                "depth_from_abandonment_root": depth + 1,
                                "depth_from_word_start": depth + 2,
                                "r1_target_orbit": r1t,
                                "r2_source_orbit": src_q, "r2_source_phase": src_ph,
                                "r2_target_orbit": tgt_q, "r2_target_phase": tgt_ph,
                                "r2_target_hexagon": core.hexagon_id(tr.target),
                                "chaining": chaining, "same_component": is_same,
                                "legal_trailing_edges": legal_trailing_edges(tr.state),
                                "endpoint": list(tr.state.p),
                                "F": tr.state.F, "S": tr.state.S, "H": tr.state.H,
                                "O": tr.state.O, "D": tr.state.D, "P": tr.state.P,
                                "Ndef": tr.state.Ndef,
                                "visited_count": tr.state.visited_count,
                                "phi": 5 + 6 * (exact.TARGET_P - tr.state.P) - (720 - tr.state.visited_count),
                                "literal_multiplicity": 1,
                            }
                        else:
                            post_r2[ch]["literal_multiplicity"] += 1
                            post_r2[ch]["depth_from_abandonment_root"] = min(
                                post_r2[ch]["depth_from_abandonment_root"], depth + 1)
            if nrc > 2:
                terminal_reasons["r_event_count_exceeds_scope"] += 1
                continue
            key, ties = make_key(tr.state, nrc, nr1t)
            stabilizer_ties[ties] += 1
            if key in seen:
                duplicate_count += 1
                continue
            seen.add(key)
            frontier.append((tr.state, nrc, nr1t, depth + 1))

    for v in post_r2.values():
        v["legal_trailing_edge_count"] = len(v["legal_trailing_edges"])

    return {
        "root_raw_hash": state_hash(root_state),
        "root_canonical_hash": state_hash(exact.canonicalize(root_state)),
        "depth_ceiling_applied": depth_ceiling,
        "expanded_count": expanded,
        "generated_edges": generated_edges,
        "unique_canonical_pair_keys": len(seen),
        "duplicate_count": duplicate_count,
        "frontier_empty": True,
        "max_depth_seen": max_depth_seen,
        "dedup_key": "canonical (state, history) pair; history=(r_count, r1_target_orbit) transported through tied alphas"
                     + (f"; ABLATED={ablate}" if ablate else ""),
        "stabilizer_tie_histogram": dict(stabilizer_ties),
        "terminal_reasons": dict(terminal_reasons),
        "rr_final_count": rr_final_count,
        "chaining_count": chaining_count,
        "same_component_count": same_count,
        "distinct_same_component_canonical_states": len(post_r2),
        "same_component_states": sorted(post_r2.values(),
                                         key=lambda r: (r["depth_from_abandonment_root"], r["canonical_state_hash"])),
        "hub_completer_orbit_distribution": dict(completer_orbits),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth-ceiling", type=int, default=6)
    parser.add_argument("--ablate", choices=["r_count", "r1_target", "both"], default=None)
    parser.add_argument("--output", default=str(ROOT / "outputs" / "rr_canonical_local_universe.json"))
    args = parser.parse_args()

    init = exact.initial_state()
    hex0 = core.hexagon_id(init.p)

    results = {}
    for ell in range(5):
        root = abandonment_root(init, ell)
        r = enumerate_canonical(root, hex0, args.depth_ceiling, ablate=args.ablate)
        results[str(ell)] = r
        print(f"ell={ell}: expanded={r['expanded_count']} canon_keys={r['unique_canonical_pair_keys']} "
              f"dup={r['duplicate_count']} rr_final={r['rr_final_count']} "
              f"same={r['same_component_count']} distinct_same_states={r['distinct_same_component_canonical_states']} "
              f"chaining={r['chaining_count']} ties={r['stabilizer_tie_histogram']}")

    report = {
        "schema": "rr-canonical-local-universe-v1",
        "engine_version": ENGINE_VERSION,
        "engine_sha256": engine_sha256(),
        "root_class": "abandonment-instant state (root class 1), real w2:10 abandonment move, ell=0..4",
        "dedup": "canonical (state, history) pair -- see module docstring for the tied-alpha transport argument",
        "ablation": args.ablate,
        "no_node_cap": True, "no_edge_cap": True,
        "termination": "frontier empty within the declared depth ceiling",
        "depth_ceiling": args.depth_ceiling,
        "results_by_ell": results,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print("wrote", args.output)


if __name__ == "__main__":
    main()
