#!/usr/bin/env python3
"""Round 37, sections 3, 4, 9: the fixed 1,398-boundary capacity ledger.

Round 36 found 1,398 Target A boundaries at the 22 long-prefix roots and
showed 0 of them survive the coarse capacity theorem
(5*(O_cap+R_cap)+4 >= B+1). This module fixes every boundary's exact
ledger row -- not just the coarse pass/fail, but THREE capacity theorems in
increasing strength (section 4), so the corpus can be classified by which
theorem first excludes it rather than treated as a single monolithic
pass/fail:

  THEOREM 1 (coarse segment bound, Round 30).
      bound_1 = 5*(O_cap + R_cap) + 4
      -- the loosest safe bound: every future segment (fresh or re-entry)
      covers at most 5 ports, and the current (possibly mid-flight) segment
      is charged the same loose +4 as a fresh one.

  THEOREM 2 (port-availability initial refinement, Round 31/34).
      bound_2 = (1 + (5 - used_ports(q0))) + 5*O_cap + 4*R_cap
      -- the current segment's remaining capacity is computed from how many
      ports of its own orbit are still unused, not the loose flat +4.

  THEOREM 3 (true phase-walk refinement, Round 33/35).
      bound_3 = true_phase_walk_capacity(q0, phase0) + 5*O_cap + 4*R_cap
      -- the current segment's capacity is the true maximum over LEGAL
      preserving words from the exact current phase (a legal phase walk's
      covered phases are partial sums of a word over {+1,+2}), which can be
      strictly below the raw port-availability count.

All three use R_cap = max(n_limit - Ndef, 0) (the orbit-reuse-penalty
4x factor, not the un-penalized 5x -- already established sound in Round
32). bound_1 >= bound_2 >= bound_3 always (each refines the last), so a
boundary's "first failing theorem" is the WEAKEST of the three that already
excludes it -- if Theorem 1 alone already fails, Theorems 2 and 3 add
nothing for that boundary and are not needed to explain it.

This is Q2 machinery, run as pure post-processing over an already-fixed
boundary corpus -- no search, no new enumeration, no Target A pruning.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"

spec = importlib.util.spec_from_file_location("bl_ledger", ROOT / "src" / "search_rr_target_a_unified.py")
sru = importlib.util.module_from_spec(spec)
sys.modules["bl_ledger"] = sru
spec.loader.exec_module(sru)
exact, core, W1, mbl, W2_10, macro = sru.exact, sru.core, sru.W1, sru.mbl, sru.W2_10, sru.macro
AREA_A = macro.AREA_A
NORB = len(core.E_REPS)
PORTS = [core.ports_of_e_orbit(core.E_REPS[q]) for q in range(NORB)]

popcount = lambda x: bin(x).count("1")


def sha(o):
    return hashlib.sha256(repr(o).encode("utf-8")).hexdigest()


def legal_preserving_words():
    """The 15 legal words over {+1 (E), +2 (E^2)} of length 0..4 whose
    partial sums (mod 5) never repeat -- established in Round 33."""
    out = []
    for n in range(5):
        for combo in product((1, 2), repeat=n):
            s, seen, ok = 0, [0], True
            for d in combo:
                s = (s + d) % 5
                if s in seen:
                    ok = False
                    break
                seen.append(s)
            if ok:
                out.append((combo, tuple(seen)))
    return out


PRESERVING_WORDS = legal_preserving_words()


def true_phase_walk_capacity(st):
    """Round 33's refinement: the maximum legal phase-walk capacity from the
    boundary's own (orbit, phase), restricted to hexagons still unvisited."""
    q0, ph0 = exact.ORBIT_PHASE[st.p]
    partial_hex = core.hexagon_id(st.p)
    unvisited = {h for h in range(len(core.ROT_REPS)) if st.hex_masks[h] == 0}
    best = 0
    for combo, offs in PRESERVING_WORDS:
        n, ok = 0, True
        for i, off in enumerate(offs):
            p2 = PORTS[q0][(ph0 + off) % 5]
            h = core.hexagon_id(p2)
            if i == 0:
                if h != partial_hex:
                    ok = False
                    break
            elif h not in unvisited:
                ok = False
                break
            n += 1
        if ok:
            best = max(best, n)
    return best


def replay_root(key, resumed_meta, prefixes):
    """Returns (root_state, root_r_count, root_ell, root_full_path) where
    root_full_path is the literal macro-edge label sequence from the TRUE
    initial state to the root -- needed so word hashes are computed on the
    FULL literal word, not just the extension (two different roots can
    otherwise share an identical-looking extension label sequence)."""
    if key.startswith("short_ell"):
        ell = int(key[len("short_ell"):])
        st = exact.initial_state()
        path = []
        for _ in range(ell):
            st = exact.extend(st, W1).state
            path.append("rot^1;w1:0")
        st = exact.extend(st, W2_10).state
        path.append(f"rot^0;{W2_10.label}")
        return st, 0, ell, path
    for pfx in ("long_found_", "long_q1_"):
        if key.startswith(pfx):
            idx = int(key[len(pfx):])
            rec = prefixes["prefixes"][idx]
            st = exact.initial_state()
            path = []
            for _ in range(rec["root_ell"]):
                st = exact.extend(st, W1).state
                path.append("rot^1;w1:0")
            st = exact.extend(st, W2_10).state
            path.append(f"rot^0;{W2_10.label}")
            for lbl in rec["literal_joint_word"]:
                for _ in range(5):
                    st = exact.extend(st, W1).state
                st = exact.extend(st, mbl[lbl]).state
                path.append(f"rot^5;{lbl}")
            return st, 1, rec["root_ell"], path
    raise ValueError(key)


def replay_path(root_state, path):
    st = root_state
    for lbl in path:
        ell_s, joint = lbl.split(";")
        ell = int(ell_s[4:])
        for _ in range(ell):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl[joint]).state
    return st


def classify_row(st, root_st, root_ell, d):
    """Sections 3, 4: every ledger field, and the first-failing theorem."""
    B = exact.TARGET_P - st.P
    O_cap = exact.TARGET_O - st.O
    R_cap = max(AREA_A.n_limit - st.Ndef, 0)
    q0, ph0 = exact.ORBIT_PHASE[st.p]
    used_ports = popcount(st.orbit_masks[q0])
    c_q0_port = 1 + (5 - used_ports)
    c_q0_phase = true_phase_walk_capacity(st)
    need = B + 1

    bound1 = 5 * (O_cap + R_cap) + 4
    bound2 = c_q0_port + 5 * O_cap + 4 * R_cap
    bound3 = c_q0_phase + 5 * O_cap + 4 * R_cap
    assert bound1 >= bound2 >= bound3, (bound1, bound2, bound3)

    if bound1 < need:
        first_fail = "coarse_segment_bound"
    elif bound2 < need:
        first_fail = "initial_phase_port_refinement"
    elif bound3 < need:
        first_fail = "true_phase_walk_refinement"
    else:
        first_fail = "NO_KNOWN_BOUND_EXCLUDES_THIS"

    return {
        "ell": root_ell, "root_P": root_st.P, "root_O": root_st.O,
        "root_Ndef": root_st.Ndef, "extension_depth": d,
        "P": st.P, "O": st.O, "Ndef": st.Ndef,
        "B": B, "B_plus_1": need,
        "O_cap": O_cap, "R_cap": R_cap,
        "current_orbit": q0, "current_phase": ph0, "used_ports": used_ports,
        "c_q0_port_availability": c_q0_port,
        "c_q0_true_phase_walk": c_q0_phase,
        "bound_1_coarse_segment": bound1,
        "bound_2_initial_phase_port": bound2,
        "bound_3_true_phase_walk": bound3,
        "margin_1": bound1 - need, "margin_2": bound2 - need, "margin_3": bound3 - need,
        "first_failing_theorem": first_fail,
        "terminal_signature": (q0, ph0, st.O, st.Ndef),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundaries", default=str(ROOT / "outputs" / "rr_new_target_a_boundaries.json"))
    ap.add_argument("--resumed", default=str(ROOT / "outputs" / "rr_target_a_resumed_frontiers.json"))
    ap.add_argument("--prefixes", default=str(ROOT / "outputs" / "rr_long_excursion_prefixes.json"))
    ap.add_argument("--out", default=str(ROOT / "outputs" / "rr_1398_boundary_capacity_ledger.json"))
    a = ap.parse_args()

    hits_data = json.loads(Path(a.boundaries).read_text(encoding="utf-8"))
    resumed = json.loads(Path(a.resumed).read_text(encoding="utf-8"))["results"]
    prefixes = json.loads(Path(a.prefixes).read_text(encoding="utf-8"))

    root_cache = {}
    rows = []
    word_hashes = set()
    for h in hits_data["hits"]:
        key = h["source_root_key"]
        if key not in root_cache:
            root_cache[key] = replay_root(key, resumed.get(key), prefixes)
        root_st, root_r, root_ell, root_path = root_cache[key]
        st = replay_path(root_st, h["path"])
        row = classify_row(st, root_st, root_ell, len(h["path"]))
        word_hash = sha(tuple(root_path) + tuple(h["path"]))[:16]
        word_hashes.add(word_hash)
        rows.append({
            "root_id": key,
            "canonical_boundary_hash": h["canonical_boundary_hash"],
            "raw_boundary_hash": h["raw_boundary_hash"],
            "literal_word_hash": word_hash,
            "replay_certificate": {
                "path": h["path"], "replay_confirmed_independently": h["replay_confirmed_independently"],
                "raw_hash_matches": sha(st.stable_key())[:16] == h["raw_boundary_hash"],
            },
            **row,
        })

    n_distinct_boundary_states = len({r["raw_boundary_hash"] for r in rows})
    n_distinct_words = len(word_hashes)
    hist = Counter(r["first_failing_theorem"] for r in rows)
    print(f"total boundary rows (word-level): {len(rows)}")
    print(f"distinct boundary STATES (raw hash): {n_distinct_boundary_states}")
    print(f"distinct WORDS (literal path hash): {n_distinct_words}")
    print(f"first-failing-theorem histogram: {dict(hist)}")
    all_replay_ok = all(r["replay_certificate"]["raw_hash_matches"] for r in rows)
    print(f"all replay certificates match independently: {all_replay_ok}")

    Path(a.out).write_text(json.dumps({
        "schema": "rr-1398-boundary-capacity-ledger-v1",
        "count_units": {
            "word_level_rows": len(rows),
            "distinct_boundary_states_raw_hash": n_distinct_boundary_states,
            "distinct_literal_words": n_distinct_words,
            "note": ("a boundary STATE can in principle be reached by more than one literal "
                    "word; this ledger is word-level (one row per (root, path) pair found by "
                    "the search) and reports the state-level distinct count separately"),
        },
        "theorems": {
            "1_coarse_segment_bound": "5*(O_cap + R_cap) + 4 >= B+1 (Round 30)",
            "2_initial_phase_port_refinement": "(1+(5-used_ports(q0))) + 5*O_cap + 4*R_cap >= B+1 (Round 31/34)",
            "3_true_phase_walk_refinement": "true_phase_walk_capacity(q0,ph0) + 5*O_cap + 4*R_cap >= B+1 (Round 33/35)",
            "ordering": "bound_1 >= bound_2 >= bound_3 always (checked by assertion on every row)",
        },
        "first_failing_theorem_histogram": {k: v for k, v in hist.items()},
        "all_replay_certificates_match": all_replay_ok,
        "grade": "exact replay + exact theorem application (no new search)",
        "rows": rows,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
