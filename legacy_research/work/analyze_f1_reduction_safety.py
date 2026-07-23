#!/usr/bin/env python3
"""Read-only audit of proposed reductions for the partial-F=1 exact state.

This is deliberately a *negative* reduction study.  It checks whether the
bounded checkpoint provides evidence for a visited-mask dominance rule and
records the residual value-relabel stabilizer forced by retaining the terminal
permutation ``p`` in the exact state.  It never changes a checkpoint and never
enumerates beyond the states already serialized in its input.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
MACRO_PATH = HERE.with_name("superperm_partial_f1_macro.py")
SPEC = importlib.util.spec_from_file_location("partial_f1_reduction_macro", MACRO_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {MACRO_PATH}")
macro = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = macro
SPEC.loader.exec_module(macro)
exact = macro.exact


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sparse_hex_masks(state: exact.ExactState) -> tuple[tuple[int, int], ...]:
    return state.sparse_hex()


def hex_subset(left: exact.ExactState, right: exact.ExactState) -> bool:
    """Whether every literal visited window of ``left`` occurs in ``right``."""
    return all((a & ~b) == 0 for a, b in zip(left.hex_masks, right.hex_masks))


def weak_local_fingerprint(state: exact.ExactState) -> tuple[object, ...]:
    """Intentionally omits identities of fully visited hexagons.

    Equal fingerprints are therefore candidates for an unsafe compression;
    their exact legal macro-tail sets are compared below.
    """
    form = exact.f1_normal_form(state)
    assert form is not None
    return (
        state.p,
        state.F,
        state.S,
        state.H,
        tuple(mask for _q, mask in form.orbit_masks),
        form.current_components,
        form.fragment_components,
        form.fragment_hex is None,
        form.current_hex == form.fragment_hex,
    )


def macro_tail_labels(state: exact.ExactState) -> tuple[str, ...]:
    labels: list[str] = []
    for edge in macro.macro_edges(state):
        labels.append(f"r{edge.run.ell}:{edge.joint.move.label}")
    return tuple(sorted(labels))


def sample_pairs(groups: Mapping[tuple[object, ...], list[exact.ExactState]], limit: int) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for fingerprint, states in groups.items():
        if len(states) < 2:
            continue
        first = states[0]
        first_tails = macro_tail_labels(first)
        for other in states[1:]:
            other_tails = macro_tail_labels(other)
            if first_tails != other_tails:
                samples.append({
                    "weak_local_fingerprint": repr(fingerprint),
                    "first_hash": macro.stable_hash(first),
                    "other_hash": macro.stable_hash(other),
                    "first_legal_macro_tails": first_tails,
                    "other_legal_macro_tails": other_tails,
                    "first_only": sorted(set(first_tails) - set(other_tails)),
                    "other_only": sorted(set(other_tails) - set(first_tails)),
                })
                break
        if len(samples) >= limit:
            return samples
    return samples


def markdown(report: Mapping[str, Any]) -> str:
    obs = report["observations"]
    return "\n".join([
        "# Partial-F=1 reduction safety audit",
        "",
        "Status: read-only bounded-checkpoint audit.  It neither proves a new",
        "prune nor starts an enumeration.",
        "",
        "## Proven reduction boundary",
        "",
        "For every ordered permutation word `p`, a value relabelling `alpha`",
        "that fixes `p` fixes all six values, hence `alpha=id`.  Therefore an",
        "exact state retaining `p` has trivial residual left-`S_6` stabilizer.",
        "The existing full left-`S_6` canonicalization is already the complete",
        "value-relabel quotient; no additional stabilizer quotient is available",
        "without discarding part of the exact state.",
        "",
        "## Dominance boundary",
        "",
        "A raw relation `V(x) subset V(y)` is not a completion-preserving",
        "dominance relation by itself.  A completion suffix from `y` leaves",
        "`V(y)\\V(x)` unvisited when replayed from `x`; a completion suffix from",
        "`x` may collide with that same difference when replayed from `y`.",
        "Thus a safe prune requires an additional extension simulation or a",
        "coverage certificate, neither of which is supplied by mask inclusion.",
        "",
        "## Bounded observations",
        "",
        f"- checkpoint frontier states: {obs['frontier_states']}",
        f"- canonical states whose terminal word is the common representative: {obs['common_terminal_word_count']}",
        f"- weak local-fingerprint classes with multiple global states: {obs['weak_fingerprint_multi_state_classes']}",
        f"- sampled equal-local pairs with different legal macro-tail sets: {obs['different_tail_set_pairs_found']}",
        f"- same `(p,B,F,S,H)` groups containing a strict visited-mask inclusion: {obs['strict_inclusion_pairs_found']}",
        "",
        "These are counterexamples to omitting global occupancy from the exact",
        "transition state; they are not a claim that no stronger proved quotient",
        "can ever exist.",
        "",
        "## Safe conclusion",
        "",
        "Do not install visited-mask inclusion as a prune.  The only currently",
        "proved symmetry reduction is canonical-child quotienting by the full",
        "left `S_6` action already implemented in the exact engine.",
        "",
        "```json",
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--pair-limit", type=int, default=20)
    args = parser.parse_args()
    raw = args.checkpoint.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    if data.get("schema") != "partial-f1-profile-checkpoint-v1":
        raise ValueError("expected bounded macro profile checkpoint")
    # The bounded profile predates the macro wrapper and records only the
    # exact-engine/core hashes.  Those are the transition semantics relevant
    # to this read-only state audit; do not invent a missing macro SHA.
    observed = (data.get("engine_sha256"), data.get("core_sha256"))
    expected = (macro.ENGINE_SHA256, macro.CORE_SHA256)
    if observed != expected:
        raise ValueError("checkpoint exact-engine/core SHA does not match active code")
    states = [exact.state_from_json(item["state"]) for item in data["frontier"]]
    p_counts = Counter(state.p for state in states)

    weak_groups: dict[tuple[object, ...], list[exact.ExactState]] = defaultdict(list)
    strong_groups: dict[tuple[object, ...], list[exact.ExactState]] = defaultdict(list)
    for state in states:
        weak_groups[weak_local_fingerprint(state)].append(state)
        strong_groups[(state.p, state.orbit_masks, state.F, state.S, state.H)].append(state)
    tail_samples = sample_pairs(weak_groups, args.pair_limit)

    inclusion_samples: list[dict[str, Any]] = []
    for signature, group in strong_groups.items():
        for index, left in enumerate(group):
            for right in group[index + 1:]:
                if hex_subset(left, right) and left.hex_masks != right.hex_masks:
                    inclusion_samples.append({"signature": repr(signature), "smaller": macro.stable_hash(left), "larger": macro.stable_hash(right)})
                elif hex_subset(right, left) and left.hex_masks != right.hex_masks:
                    inclusion_samples.append({"signature": repr(signature), "smaller": macro.stable_hash(right), "larger": macro.stable_hash(left)})
                if len(inclusion_samples) >= args.pair_limit:
                    break
            if len(inclusion_samples) >= args.pair_limit:
                break
        if len(inclusion_samples) >= args.pair_limit:
            break

    identity_word = tuple(range(exact.N))
    report: dict[str, Any] = {
        "schema": "partial-f1-reduction-safety-audit-v1",
        "scope": "read-only bounded checkpoint; no new search and no installed pruning",
        "input": {"path": str(args.checkpoint), "sha256": hashlib.sha256(raw).hexdigest()},
        "code_sha256": {"analysis": sha256_file(HERE), "macro": macro.CODE_SHA256, "engine": macro.ENGINE_SHA256, "core": macro.CORE_SHA256},
        "proofs": {
            "left_S6_residual_stabilizer": "trivial: alpha(p_i)=p_i for all six distinct entries of p forces alpha=id",
            "mask_inclusion_not_a_standalone_dominance": "a completion suffix cannot be transferred in either direction without either leaving V(y)\\V(x) uncovered or colliding with it",
        },
        "observations": {
            "frontier_states": len(states),
            "frontier_canonicality": "not recomputed here; the checkpoint was emitted by canonical-child search and this audit avoids 720-image re-canonicalization while the unbounded search is live",
            "distinct_terminal_words_after_canonicalization": len(p_counts),
            "common_terminal_word_count": p_counts.get(identity_word, 0),
            "weak_fingerprint_classes": len(weak_groups),
            "weak_fingerprint_multi_state_classes": sum(len(group) > 1 for group in weak_groups.values()),
            "different_tail_set_pairs_found": len(tail_samples),
            "strict_inclusion_pairs_found": len(inclusion_samples),
        },
        "different_legal_tail_samples": tail_samples,
        "strict_mask_inclusion_samples": inclusion_samples,
        "limitations": "Absence of a pair in this bounded checkpoint would not prove a dominance rule. No relation from this audit is used by the search engine.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    args.markdown.write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report["observations"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
