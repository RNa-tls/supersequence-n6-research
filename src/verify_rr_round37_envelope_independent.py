#!/usr/bin/env python3
"""Independent Round-38 audit of the Round-37 root envelope.

This intentionally does *not* import any Round-37 helper.  It uses the
unchanged exact engine only after byte-for-byte checking it against commit
``0dcde29``; all root replay, edge accounting, capacity arithmetic, and
ledger comparison are implemented below.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
R37 = "0dcde297a3d87686e0a6bb8dd0bbfceabca02d84"
WORK = ROOT / "legacy_research" / "work"


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def stable_sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def git_bytes(rev_path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{R37}:{rev_path}"], cwd=ROOT)


def git_json(rev_path: str) -> Any:
    return json.loads(git_bytes(rev_path).decode("utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


macro = load_module("rr38_macro", WORK / "superperm_partial_f1_macro.py")
exact, core = macro.exact, macro.core
W1 = macro.W1
MOVE = {m.label: m for m in exact.ALL_MOVES}
W2_10 = MOVE["w2:10"]
N_LIMIT, TARGET_P, TARGET_O = 3, 121, 25


def assert_engine_identity() -> dict[str, str]:
    """Avoid silently auditing a different transition system than Round 37."""
    paths = ("legacy_research/work/superperm_partial_f1.py",
             "legacy_research/work/superperm_partial_f1_macro.py")
    result = {}
    for rel in paths:
        local = ROOT / rel
        # Git stores LF while this Windows checkout may have CRLF.  Hash the
        # normalized source text, not line-ending noise, then record it.
        norm = lambda b: b.replace(b"\r\n", b"\n")
        local_hash, r37_hash = sha_bytes(norm(local.read_bytes())), sha_bytes(norm(git_bytes(rel)))
        assert local_hash == r37_hash, (rel, local_hash, r37_hash)
        result[rel] = local_hash
    return result


def replay_root(root_id: str, prefixes: dict[str, Any]):
    """Independent literal replay of the 33 Round-37 root definitions."""
    st, path = exact.initial_state(), []
    if root_id.startswith("short_ell"):
        ell, word, r_count = int(root_id.removeprefix("short_ell")), (), 0
    else:
        index = int(root_id.rsplit("_", 1)[1])
        rec = prefixes["prefixes"][index]
        ell, word, r_count = rec["root_ell"], tuple(rec["literal_joint_word"]), 1
    for _ in range(ell):
        tr = exact.extend(st, W1); assert tr is not None; st = tr.state
        path.append("rot^1;w1:0")
    tr = exact.extend(st, W2_10); assert tr is not None; st = tr.state
    path.append("rot^0;w2:10")
    for label in word:
        for _ in range(5):
            tr = exact.extend(st, W1); assert tr is not None; st = tr.state
        tr = exact.extend(st, MOVE[label]); assert tr is not None; st = tr.state
        path.append(f"rot^5;{label}")
    return st, r_count, ell, tuple(path)


def replay_macro_path(state, path: Iterable[str]):
    st = state
    for item in path:
        lhs, label = item.split(";")
        for _ in range(int(lhs.removeprefix("rot^"))):
            tr = exact.extend(st, W1); assert tr is not None; st = tr.state
        tr = exact.extend(st, MOVE[label]); assert tr is not None, item
        st = tr.state
    return st


def joint_kind(edge) -> str:
    tr = edge.joint
    if tr.move.weight == 2:
        return "Z2abandon" if tr.abandonment else "Z2"
    if tr.move.weight == 3 and tr.new_orbit:
        return "Z3"
    if tr.move.weight == 3 and not tr.new_orbit:
        return "R"
    return "other"


def transition_law(root_states: Iterable[Any]) -> dict[str, Any]:
    """Check *every macro edge emitted from the named exact states.

    The dM formula itself follows from dP=1 and the transition's exact
    ``new_orbit`` bit.  The census confirms the RR kinds used by the envelope
    have precisely the advertised dO values; no stored Round-37 witness is
    called.
    """
    expected = {"Z2": (1, 0, 1), "R": (1, 0, 1), "Z3": (1, 1, -4)}
    counts, checked = Counter(), 0
    for st in root_states:
        for edge in macro.macro_edges(st):
            child, kind = edge.state, joint_kind(edge)
            dP, dO = child.P - st.P, child.O - st.O
            dM = dP - 5 * dO
            checked += 1; counts[kind] += 1
            assert dP == 1 and dO in (0, 1) and dM == (1 if dO == 0 else -4)
            if kind in expected:
                assert (dP, dO, dM) == expected[kind], (kind, dP, dO, dM)
    return {"checked_exact_macro_edges": checked, "kind_counts": dict(counts),
            "expected": expected,
            "scope": "all legal macro edges from all 33 independently replayed roots; algebraic dM identity is universal for any exact macro edge"}


def envelope(st, r_count: int) -> dict[str, int | bool]:
    k = 1 if r_count == 1 else 2
    M = st.P - 5 * st.O
    rcap = max(N_LIMIT - st.Ndef - k, 0)
    value = M + 5 * k + 7 + 5 * rcap
    return {"k_required_R_events": k, "M_root": M, "P_root": st.P,
            "O_root": st.O, "Ndef_root": st.Ndef,
            "Ndef_boundary_exact": st.Ndef + k,
            "R_cap_boundary_exact": rcap, "max_delta_M_total": 5 * k,
            "envelope_margin_1_upper_bound": value,
            "certified_q2_impossible": value < 0}


def phase_words():
    ans = []
    for n in range(5):
        for word in product((1, 2), repeat=n):
            x, seen = 0, {0}
            ok = True
            for step in word:
                x = (x + step) % 5
                if x in seen: ok = False; break
                seen.add(x)
            if ok: ans.append((word, tuple([0])))
    return ans


def old_phase_capacity(st) -> int:
    """Reimplementation of the rejected Round-33 helper, for its regression."""
    q0, ph0 = exact.ORBIT_PHASE[st.p]
    ports = core.ports_of_e_orbit(core.E_REPS[q0])
    partial_hex = core.hexagon_id(st.p)
    unvisited = {h for h, mask in enumerate(st.hex_masks) if mask == 0}
    best = 0
    for word, _ in phase_words():
        offset, n, ok = 0, 0, True
        for i, step in enumerate((0,) + word):
            if i: offset = (offset + step) % 5
            h = core.hexagon_id(ports[(ph0 + offset) % 5])
            if i == 0 and h != partial_hex: ok = False; break
            if i and h not in unvisited: ok = False; break
            n += 1
        if ok: best = max(best, n)
    return best


def map_round35(prefixes: dict[str, Any], resumed: dict[str, Any]) -> list[dict[str, Any]]:
    ledger = json.loads((ROOT / "outputs" / "rr_target_a_22_root_ledger.json").read_text(encoding="utf-8"))
    index_to_r37 = {int(x.rsplit("_", 1)[1]): x for x in resumed if x.startswith("long_q1_")}
    rows = []
    for rec in ledger["roots"]:
        index = rec["prefix_index"]
        rid = index_to_r37.get(index)
        if rid is None:
            rows.append({"round35_root_id": rec["root_id"], "classification": "NO_MATCH", "matching_evidence": "no long_q1 prefix index"})
            continue
        st, rc, ell, _ = replay_root(rid, prefixes)
        state_hash = stable_sha(st.stable_key())
        exact_match = state_hash == rec["post_return_state_hash"]
        env = envelope(st, rc)
        rows.append({"round35_root_id": rec["root_id"], "prefix_index": index,
                     "literal_joint_word": rec["literal_joint_word"], "ell": ell,
                     "round35_exact_state_hash": rec["post_return_state_hash"],
                     "replayed_exact_state_hash": state_hash,
                     "round35_decorated_key": rec["conservative_history_key_sha256"],
                     "round37_root_id": rid, "classification": "LONG_Q2_IMPOSSIBLE" if env["certified_q2_impossible"] else "SHORT_UNRESOLVED",
                     "matching_evidence": {"prefix_index_equal": True, "literal_word_equal": tuple(rec["literal_joint_word"]) == tuple(prefixes["prefixes"][index]["literal_joint_word"]), "ell_equal": ell == rec["root_ell"], "independent_replay_state_hash_equal": exact_match,
                                           "q2_envelope": env["envelope_margin_1_upper_bound"]}})
        assert exact_match
    assert len(rows) == 22 and all(r["classification"] == "LONG_Q2_IMPOSSIBLE" for r in rows)
    return rows


def audit() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    engine_hashes = assert_engine_identity()
    prefixes = git_json("outputs/rr_long_excursion_prefixes.json")
    resumed = git_json("outputs/rr_target_a_resumed_frontiers.json")["results"]
    r37_env = git_json("outputs/rr_root_capacity_envelopes.json")
    r37_ledger = git_json("outputs/rr_1398_boundary_capacity_ledger.json")
    assert len(resumed) == 33
    roots = {key: replay_root(key, prefixes) for key in resumed}
    law = transition_law(st for st, _, _, _ in roots.values())
    r37_by_id = {x["root_id"]: x for x in r37_env["rows"]}
    rows = []
    for root_id, (st, r_count, ell, path) in sorted(roots.items()):
        own = envelope(st, r_count); claimed = r37_by_id[root_id]
        compare = {k: own[k] == claimed[k] for k in own}
        assert all(compare.values()), (root_id, own, claimed)
        rows.append({"root_id": root_id, "root_literal_path": list(path), "root_ell": ell,
                     **own, "matches_round37_artifact": True})
    long_rows, short_rows = [r for r in rows if r["root_id"].startswith("long_")], [r for r in rows if r["root_id"].startswith("short_")]
    assert len(long_rows) == 28 and len(short_rows) == 5
    assert all(r["certified_q2_impossible"] for r in long_rows)
    assert not any(r["certified_q2_impossible"] for r in short_rows)

    # Literal replay of every recorded word-level boundary, followed by the
    # coarse theorem calculated here rather than read from Claude's verdict.
    sources, raw_hashes, word_hashes, profiles = set(), set(), set(), set()
    coarse_failures = 0
    for row in r37_ledger["rows"]:
        source = row["root_id"]
        root_st, _, _, root_path = roots[source]
        st = replay_macro_path(root_st, row["replay_certificate"]["path"])
        raw = stable_sha(st.stable_key())[:16]
        assert raw == row["raw_boundary_hash"], (source, raw, row["raw_boundary_hash"])
        B, ocap, rcap = TARGET_P - st.P, TARGET_O - st.O, max(N_LIMIT - st.Ndef, 0)
        bound = 5 * (ocap + rcap) + 4
        assert bound < B + 1
        coarse_failures += 1; sources.add(source); raw_hashes.add(raw)
        word_hashes.add(stable_sha(tuple(root_path) + tuple(row["replay_certificate"]["path"]))[:16])
        q, _ = exact.ORBIT_PHASE[st.p]
        cport = 1 + (5 - st.orbit_masks[q].bit_count())
        profiles.add((ocap, rcap, cport))
    assert len(r37_ledger["rows"]) == coarse_failures == 1398
    assert len(raw_hashes) == len(word_hashes) == 1398
    assert len(profiles) == 15
    assert sources <= {r["root_id"] for r in long_rows}

    mappings = map_round35(prefixes, resumed)
    relevance = {"scope": "Q2/completion-compatible Target-A only; this does not enumerate or negate Q1 abundance.",
                 "roots": [{"round35_root_id": r["round35_root_id"], "classification": "SEARCH_OBSOLETE_BY_Q2_CERTIFICATE", "reason": "independent negative root envelope; preserve existing Q1 checkpoint"} for r in mappings]}
    audit_result = {"schema": "rr-round38-independent-envelope-v1", "round37_commit": R37,
                    "engine_identity_sha256": engine_hashes, "transition_law": law,
                    "root_counts": {"total": 33, "long_q2_impossible": 28, "short_unresolved": 5},
                    "rows": rows,
                    "boundary_replay": {"word_level_rows": 1398, "distinct_raw_states": len(raw_hashes), "distinct_literal_words": len(word_hashes), "source_long_roots_with_hits": len(sources), "all_sources_long_family": True, "coarse_failures": coarse_failures, "capacity_relevant_profiles": len(profiles), "q1_missing_witness_roots": sorted(set(r["root_id"] for r in long_rows) - sources)},
                    "q1_q2_scope": {"Q2_implies_Q1": True, "Q1_does_not_imply_Q2_witness_count": len(sources), "correction": "Only 26 long roots have exhibited Q1 witnesses in the fixed 1398 corpus; Q1 for long_q1_140 and long_q1_178 remains unproved by these artifacts. The envelope nevertheless proves Q2 false for all 28."}}
    return audit_result, {"schema": "rr-round35-round37-root-mapping-v1", "rows": mappings}, relevance


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--out-dir", default=str(ROOT / "outputs")); a = ap.parse_args()
    out = Path(a.out_dir); out.mkdir(exist_ok=True)
    audit_result, mapping, relevance = audit()
    (out / "rr_round37_envelope_independent_verification.json").write_text(json.dumps(audit_result, indent=2, sort_keys=True), encoding="utf-8")
    (out / "rr_round35_round37_root_mapping.json").write_text(json.dumps(mapping, indent=2, sort_keys=True), encoding="utf-8")
    (out / "rr_round35_search_relevance.json").write_text(json.dumps(relevance, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"long": 28, "short": 5, "boundaries": 1398, "mapping": len(mapping["rows"])}, indent=2))


if __name__ == "__main__":
    main()
