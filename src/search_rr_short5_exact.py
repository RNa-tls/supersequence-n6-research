#!/usr/bin/env python3
"""Round 40: exact Target-A continuations from the five short RR roots.

The five roots are *only* the bare abandonment states
``short_ell0`` through ``short_ell4`` from Round 37.  In particular this
driver never loads the 28 long-root ledger and refuses any other root name.

It deliberately delegates literal macro traversal to the Round-35 engine:
the exact state, decoration, collision test, Area-A necessary prunes, and
Target-A recognizer are identical.  This file supplies only a separately
hash-bound root manifest, checkpoint namespace, state-key audit, and output
assembly.  A positive node/depth cap is rejected rather than being allowed to
masquerade as an exhaustion result.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
ROUND35_PATH = ROOT / "src" / "search_rr_target_a_exhaustive.py"
ROUND37_AUDIT = ROOT / "outputs" / "rr_round37_envelope_independent_verification.json"
OUTPUT = ROOT / "outputs" / "rr_short5_search_results.json"
CERTIFICATES = ROOT / "outputs" / "rr_short5_exhaustion_certificates.json"
NEW_BOUNDARIES = ROOT / "outputs" / "rr_short5_new_boundaries.json"
CHECKPOINT_DIR = ROOT / "outputs" / "rr_short5_checkpoints"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rr = load_module("rr_short5_round35", ROUND35_PATH)
exact, core, macro = rr.exact, rr.core, rr.macro
W1, W2_10 = rr.W1, rr.W2_10
HUB = rr.HUB


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    os.replace(temporary, path)


def short_root_records() -> list[dict[str, object]]:
    """Construct and cross-check the five Round-37 bare-abandonment roots.

    The literal word is empty, so the Round-35 initial-decoration replay
    consists exactly of ``rot^ell`` followed by the unique ``w2:10``
    abandonment.  ``o_star`` is the target E-orbit, agreeing with the frozen
    Round-27 convention ``HEX0[ell+1]``.
    """
    r37 = json.loads(ROUND37_AUDIT.read_text(encoding="utf-8"))
    row_by_id = {row["root_id"]: row for row in r37["rows"]}
    records = []
    for ell in range(5):
        root_id = f"short_ell{ell}"
        row = row_by_id.get(root_id)
        if row is None:
            raise AssertionError(f"missing Round-37 root {root_id}")
        state = exact.initial_state()
        path = []
        for _ in range(ell):
            transition = exact.extend(state, W1)
            if transition is None:
                raise AssertionError("short-root rotation collided")
            state = transition.state
            path.append("rot^1;w1:0")
        transition = exact.extend(state, W2_10)
        if transition is None or not transition.abandonment:
            raise AssertionError("short-root abandonment failed")
        state = transition.state
        path.append("rot^0;w2:10")
        o_star, _ = exact.ORBIT_PHASE[state.p]
        expected_o_star = rr.roots.HEX0[ell + 1]
        if o_star != expected_o_star:
            raise AssertionError((root_id, o_star, expected_o_star))
        if tuple(path) != tuple(row["root_literal_path"]):
            raise AssertionError(f"Round-37 literal path mismatch for {root_id}")
        record: dict[str, object] = {
            "root_id": root_id,
            "root_ell": ell,
            "o_star": o_star,
            "literal_joint_word": [],
            "r_count": 0,
            "post_return_state_hash": rr.state_hash(state),
            "round37_root_id": root_id,
            "round37_literal_path": path,
            "round37_envelope_margin": row["envelope_margin_1_upper_bound"],
            "root_unit": "bare abandonment root (ell, w2:10)",
        }
        replayed, decoration = rr.initial_decoration(record)
        if replayed.stable_key() != state.stable_key() or decoration.r_count != 0:
            raise AssertionError(f"Round-35 mapping failed for {root_id}")
        records.append(record)
    return records


def short_root_manifest(records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        "schema": "rr-short5-root-manifest-v1",
        "scope": "five bare Round-37 short roots only; all long roots excluded",
        "records": [dict(record) for record in records],
        "round37_audit_sha256": sha256_file(ROUND37_AUDIT),
        "round35_engine_sha256": sha256_file(ROUND35_PATH),
        "short5_driver_sha256": sha256_file(Path(__file__)),
    }


def _accepted_children(state, decoration):
    for edge, collision in rr.iter_raw_macro_candidates(state):
        if collision is not None or edge is None:
            continue
        verdict, child_decoration, _recognition = rr.evaluate_edge(state, decoration, edge)
        if verdict == "child":
            assert child_decoration is not None
            yield edge.state, child_decoration


def audit_short_state_key(records: Sequence[Mapping[str, object]], depth_limit: int = 2) -> dict[str, object]:
    """Finite regression plus the lossless-key contract for the short roots.

    The actual key is raw, not quotienting: ExactState.stable_key serializes
    p, all nonzero hex masks, all nonzero E masks, F/S/H.  Decoration.key
    serializes every decoration field read by evaluation except root_id, which
    has provenance-only use.  The finite signature check catches a mismatch
    between that contract and the current implementation.
    """
    groups: dict[tuple[object, ...], list[tuple[object, object]]] = {}
    queue = deque()
    root_count = 0
    for record in records:
        state, decoration = rr.initial_decoration(record)
        queue.append((0, state, decoration))
        root_count += 1
    examined, json_roundtrip_failures = 0, []
    while queue:
        depth, state, decoration = queue.popleft()
        examined += 1
        restored_state = exact.state_from_json(exact.state_to_json(state))
        restored_decoration = rr.Decoration.from_json(decoration.to_json())
        if rr.decorated_key(restored_state, restored_decoration) != rr.decorated_key(state, decoration):
            json_roundtrip_failures.append(rr.state_hash(state))
        key = rr.decorated_key(state, decoration)
        # Deliberate duplicate makes a real equality comparison, not merely a
        # vacuous "no collisions" count.
        groups.setdefault(key, []).extend(((state, decoration), (state, decoration)))
        if depth < depth_limit:
            queue.extend((depth + 1, child_state, child_decoration)
                         for child_state, child_decoration in _accepted_children(state, decoration))
    mismatches = []
    for key, samples in groups.items():
        signatures = {rr.successor_signature(state, decoration) for state, decoration in samples}
        if len(signatures) != 1:
            mismatches.append(sha256_bytes(repr(key).encode("utf-8")))
    return {
        "schema": "rr-short5-decorated-state-key-audit-v1",
        "grade": "lossless raw-key contract plus complete depth-2 successor-signature regression",
        "scope": "five short roots; accepted macro children through depth 2",
        "roots_checked": root_count,
        "states_examined": examined,
        "deliberate_duplicate_groups": len(groups),
        "key_collision_mismatches": mismatches,
        "json_roundtrip_failures": json_roundtrip_failures,
        "passed": not mismatches and not json_roundtrip_failures,
        "contract": {
            "exact_state": "stable_key = p + sparse hex masks + sparse E masks + F,S,H",
            "decoration": "key retains root_ell,o_star,hub_id,macro_index,ordered R events,hub touch count,first completer",
            "omitted_decoration_field": "root_id only; it is provenance-only because every root is searched independently",
        },
    }


def config_extra(manifest: Mapping[str, object]) -> dict[str, object]:
    return {
        "root_universe": "round37-short5-bare-abandonment-v1",
        "short5_manifest_sha256": sha256_bytes(json.dumps(manifest, sort_keys=True).encode("utf-8")),
        "short5_driver_sha256": sha256_file(Path(__file__)),
    }


def postprocess_boundaries(boundaries: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    """Attach helper-free Target-B triage to every discovered Target-A state.

    New coarse survivors deliberately remain ``FLOW_REQUIRED`` here.  The
    Round-34 exact flow search is then invoked by the independent verifier
    with a separately recorded cap-free/exhaustion result; this prevents a
    potentially expensive downstream flow calculation from being hidden in a
    root traversal's checkpoint semantics.
    """
    out = []
    known = rr.known_boundary_canonical_hashes()
    for boundary in boundaries:
        state = exact.state_from_json(boundary["post_r2_state"])
        canonical = rr.boundary_canonical_hash(state)
        need = exact.TARGET_P - state.P + 1
        o_cap = max(exact.TARGET_O - state.O, 0)
        r_cap = max(macro.AREA_A.n_limit - state.Ndef, 0)
        bound = 5 * (o_cap + r_cap) + 4
        if canonical in known:
            target_b = "KNOWN_18_BOUNDARY"
        elif need > bound:
            target_b = "COARSE_CAPACITY_IMPOSSIBLE"
        else:
            target_b = "FLOW_REQUIRED"
        row = dict(boundary)
        row["target_b_helper_free_triage"] = {
            "canonical_state_hash": canonical,
            "known_18": canonical in known,
            "coarse": {"need": need, "O_cap": o_cap, "R_cap": r_cap,
                       "bound": bound, "contradiction": need > bound},
            "status": target_b,
            "phase_helper_used": False,
        }
        out.append(row)
    return out


def read_prior_results(path: Path, manifest_sha: str) -> dict[str, Mapping[str, object]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("short5_manifest_sha256") != manifest_sha:
        raise ValueError("existing short5 result has a different root manifest")
    return {row["root_id"]: row for row in payload.get("results", [])}


def write_aggregate(path: Path, certificates_path: Path, boundaries_path: Path,
                    manifest: Mapping[str, object], state_key_audit: Mapping[str, object],
                    results_by_id: Mapping[str, Mapping[str, object]]) -> None:
    records = manifest["records"]  # type: ignore[index]
    results = [results_by_id[str(record["root_id"])] for record in records
               if str(record["root_id"]) in results_by_id]
    all_boundaries = postprocess_boundaries(
        [boundary for result in results for boundary in result["target_a_boundaries"]])
    status_histogram = Counter(str(result["status"]) for result in results)
    payload = {
        "schema": "rr-short5-exact-search-results-v1",
        "grade": "root-local exact search only when a root naturally exhausts; otherwise incomplete",
        "scope": "short_ell0 through short_ell4 only; no long roots, U/J, N=0, CH2, or T3 search",
        "attribution": {
            "search_implementation": "CODEX",
            "mathematical_envelope_facts": "CLAUDE, CODEX_VERIFIED",
            "new_discovered_boundaries": "CODEX_FINDING",
        },
        "short5_manifest": manifest,
        "short5_manifest_sha256": sha256_bytes(json.dumps(manifest, sort_keys=True).encode("utf-8")),
        "state_key_audit": dict(state_key_audit),
        "results": results,
        "status_histogram": dict(status_histogram),
        "all_requested_roots_processed": len(results) == 5,
        "all_root_statuses": sorted(status_histogram),
    }
    certificates = {
        "schema": "rr-short5-exhaustion-certificates-v1",
        "attribution": "CODEX",
        "short5_manifest_sha256": payload["short5_manifest_sha256"],
        "certificates": [{**rr.root_certificate(result),
                          "truncated": bool(result["interrupted_by_node_limit"] or result["interrupted_by_depth_limit"])}
                         for result in results],
    }
    found_payload = {
        "schema": "rr-short5-new-boundaries-v1",
        "attribution": "CODEX_FINDING",
        "phase_helper_used": False,
        "count": len(all_boundaries),
        "boundaries": all_boundaries,
        "scope": "Target-A boundaries from short roots; Target-B flow remains explicit per row",
    }
    atomic_json(path, payload)
    atomic_json(certificates_path, certificates)
    atomic_json(boundaries_path, found_payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-id", action="append", default=[])
    parser.add_argument("--checkpoint-dir", type=Path, default=CHECKPOINT_DIR)
    parser.add_argument("--checkpoint-every", type=int, default=10_000)
    parser.add_argument("--resume", type=Path, default=None,
                        help="resume the one selected root from this exact checkpoint")
    parser.add_argument("--resume-if-present", action="store_true")
    parser.add_argument("--node-limit", type=int, default=0)
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--certificates", type=Path, default=CERTIFICATES)
    parser.add_argument("--new-boundaries", type=Path, default=NEW_BOUNDARIES)
    args = parser.parse_args()
    if args.node_limit != 0 or args.max_depth is not None:
        raise ValueError("short5 proof traversal accepts no node or depth cap")
    if args.checkpoint_every < 1:
        raise ValueError("checkpoint interval must be positive")

    records = short_root_records()
    by_id = {str(record["root_id"]): record for record in records}
    wanted = args.root_id or list(by_id)
    if not wanted or set(wanted) - set(by_id):
        raise ValueError("--root-id may name only short_ell0 through short_ell4")
    if args.resume is not None and len(wanted) != 1:
        raise ValueError("--resume requires exactly one --root-id")
    manifest = short_root_manifest(records)
    manifest_sha = sha256_bytes(json.dumps(manifest, sort_keys=True).encode("utf-8"))
    state_key_audit = audit_short_state_key(records)
    if not state_key_audit["passed"]:
        raise RuntimeError("STATE_KEY_UNSOUND")
    results_by_id = read_prior_results(args.output, manifest_sha)
    extra = config_extra(manifest)

    for root_id in wanted:
        record = by_id[root_id]
        checkpoint = args.checkpoint_dir / f"{root_id}.json"
        resume = args.resume
        if resume is None and args.resume_if_present and checkpoint.exists():
            resume = checkpoint
        result = rr.search_root(record, node_limit=0, max_depth=None,
                                checkpoint=checkpoint, checkpoint_every=args.checkpoint_every,
                                resume=resume, checkpoint_config_extra=extra)
        results_by_id[root_id] = result
        write_aggregate(args.output, args.certificates, args.new_boundaries,
                        manifest, state_key_audit, results_by_id)
        print(f"{root_id}: {result['status']} expanded={result['stats']['expanded']} "
              f"frontier={result['stats']['frontier_size']} boundaries={len(result['target_a_boundaries'])}")


if __name__ == "__main__":
    main()
