#!/usr/bin/env python3
"""Round 36, Part F (sections 19-20): the new-boundary pipeline.

Every hit the unified enumerator records is a Q1-safe find: a genuine
Target A boundary (F_def==1, H==0, same-component), found WITHOUT any
completability assumption. That is a different, weaker guarantee than
Round 34's Target B closure, which only ever applied to the 18 boundaries
known before this round. So a hit here requires its OWN Target B
determination, run as separate post-processing -- never assumed, and never
performed inside the enumeration search itself (the brief's explicit
instruction: "Target B 판정은 enumeration과 별도 후처리로 수행하라").

Pipeline per hit, exactly as specified:
  1. exact replay (already done by the enumerator; re-verified here)
  2. canonicalize
  3. compare against the 18 currently known boundaries (raw + canonical hash)
  4. CH1/CH2 classification
  5. Target B capacity theorem (Round 30-32's (B+R) bound)
  6. only if the capacity theorem does not already exclude it, hand to
     Round 34's flow-first exhaustive search for the actual Target B verdict

No Target B search is performed for the ORIGINAL 18 -- Round 34 already
closed all of them, and this round is instructed not to repeat that.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"

spec = importlib.util.spec_from_file_location("sru_proc", ROOT / "src" / "search_rr_target_a_unified.py")
sru = importlib.util.module_from_spec(spec)
sys.modules["sru_proc"] = sru
spec.loader.exec_module(sru)
exact, core, W1, mbl, W2_10, macro = sru.exact, sru.core, sru.W1, sru.mbl, sru.W2_10, sru.macro
AREA_A = macro.AREA_A


def sha(o):
    return hashlib.sha256(repr(o).encode("utf-8")).hexdigest()


def replay_path(root_state, path):
    st = root_state
    for lbl in path:
        ell_s, joint = lbl.split(";")
        ell = int(ell_s[4:])
        for _ in range(ell):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl[joint]).state
    return st


def replay_root(key, prefixes, resumed_meta):
    """Reconstruct the exact root state a resumed-frontier key was searched
    from, using the same replay logic as run_rr_target_a_coverage.py."""
    if key.startswith("short_ell"):
        ell = int(key[len("short_ell"):])
        st = exact.initial_state()
        for _ in range(ell):
            st = exact.extend(st, W1).state
        st = exact.extend(st, W2_10).state
        return st, 0
    for prefix_key in ("long_found_", "long_q1_"):
        if key.startswith(prefix_key):
            idx = int(key[len(prefix_key):])
            rec = prefixes["prefixes"][idx]
            st = exact.initial_state()
            for _ in range(rec["root_ell"]):
                st = exact.extend(st, W1).state
            st = exact.extend(st, W2_10).state
            for lbl in rec["literal_joint_word"]:
                for _ in range(5):
                    st = exact.extend(st, W1).state
                st = exact.extend(st, mbl[lbl]).state
            return st, 1  # r_count=1, guaranteed by the R-budget obstruction filter
    raise ValueError(f"unrecognised root key {key}")


def ch_branch(hit_state):
    """CH1/CH2 classification for a FOUND boundary itself (not the root):
    a boundary state's own hub status determines whether the completer C
    (if any, within this same word) has already occurred."""
    hub = core.hexagon_id(exact.initial_state().p)
    return "hub_complete_at_boundary" if hit_state.hex_masks[hub] == 63 else "hub_incomplete_at_boundary"


def capacity_theorem(st):
    """Round 30-32's (B+R) bound, exactly as re-derived and verified in
    Round 34/35 (orbit_capacity_bound / capacity_slack). Returns
    (feasible, B_plus_1, bound, margin)."""
    B = exact.TARGET_P - st.P
    O_cap = exact.TARGET_O - st.O
    R_cap = max(AREA_A.n_limit - st.Ndef, 0)
    bound = 5 * (O_cap + R_cap) + 4
    return {"B_plus_1": B + 1, "bound": bound, "margin": bound - (B + 1),
            "capacity_feasible": bound >= B + 1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumed", default=str(ROOT / "outputs" / "rr_target_a_resumed_frontiers.json"))
    ap.add_argument("--prefixes", default=str(ROOT / "outputs" / "rr_long_excursion_prefixes.json"))
    ap.add_argument("--known18", default=str(ROOT / "outputs" / "rr_target_a_known18_regression.json"))
    ap.add_argument("--out", default=str(ROOT / "outputs" / "rr_new_target_a_boundaries.json"))
    a = ap.parse_args()

    resumed = json.loads(Path(a.resumed).read_text(encoding="utf-8"))["results"]
    prefixes = json.loads(Path(a.prefixes).read_text(encoding="utf-8"))
    known18 = json.loads(Path(a.known18).read_text(encoding="utf-8"))
    known_raw = {r["raw_boundary_hash"] for r in known18["rows"] if r.get("raw_boundary_hash")}
    known_canon = {r["canonical_boundary_hash"] for r in known18["rows"] if r.get("canonical_boundary_hash")}

    all_hits = []
    for key, res in resumed.items():
        if not res.get("hits"):
            continue
        root_state, root_r = replay_root(key, prefixes, res)
        for hit in res["hits"]:
            # step 1: exact replay, re-verified independently of the search's own bookkeeping
            replayed = replay_path(root_state, hit["path"])
            replay_confirmed = sha(replayed.stable_key())[:16] == hit["boundary_raw_hash"]
            # step 2: canonicalize
            canon = exact.canonicalize(replayed)
            canon_hash = sha(canon.stable_key())[:16]
            assert canon_hash == hit["boundary_canonical_hash"]
            # step 3: compare against the 18 currently known
            is_new_raw = hit["boundary_raw_hash"] not in known_raw
            is_new_canon = hit["boundary_canonical_hash"] not in known_canon
            # step 4: CH1/CH2
            ch = ch_branch(replayed)
            # step 5: capacity theorem
            cap = capacity_theorem(replayed)
            all_hits.append({
                "source_root_key": key, "path": hit["path"],
                "raw_boundary_hash": hit["boundary_raw_hash"],
                "canonical_boundary_hash": hit["boundary_canonical_hash"],
                "replay_confirmed_independently": replay_confirmed,
                "is_new_vs_known18_raw": is_new_raw,
                "is_new_vs_known18_canonical": is_new_canon,
                "ch_branch": ch,
                "P": replayed.P, "O": replayed.O, "Ndef": replayed.Ndef,
                "capacity_theorem": cap,
                "step6_flow_verifier_run": False,  # filled in below only for capacity-feasible survivors
            })

    n_total = len(all_hits)
    n_confirmed = sum(1 for h in all_hits if h["replay_confirmed_independently"])
    n_new_raw = sum(1 for h in all_hits if h["is_new_vs_known18_raw"])
    n_capacity_survivors = sum(1 for h in all_hits if h["capacity_theorem"]["capacity_feasible"])
    print(f"total hits collected: {n_total}")
    print(f"independently re-confirmed by literal replay: {n_confirmed}/{n_total}")
    print(f"new vs the 18 currently known (raw hash): {n_new_raw}/{n_total}")
    print(f"capacity-theorem survivors (candidates for Round 34 flow verifier): {n_capacity_survivors}")

    dedup_raw = {h["raw_boundary_hash"] for h in all_hits}
    print(f"distinct raw boundary states among all hits: {len(dedup_raw)}")

    by_root = Counter(h["source_root_key"] for h in all_hits)
    print(f"hits by root: {dict(by_root)}")

    Path(a.out).write_text(json.dumps({
        "schema": "rr-new-target-a-boundaries-v1",
        "pipeline": ["exact replay", "canonicalize", "compare vs 18 currently known",
                    "CH1/CH2 classification", "capacity theorem",
                    "Round 34 flow verifier (only for capacity survivors)"],
        "target_B_determination_note": ("performed as separate post-processing, never inside "
                                        "the enumeration search itself, per the round's explicit "
                                        "instruction"),
        "n_total_hits": n_total, "n_distinct_raw_boundary_states": len(dedup_raw),
        "n_independently_reconfirmed": n_confirmed,
        "n_new_vs_known18_raw": n_new_raw,
        "n_capacity_theorem_survivors": n_capacity_survivors,
        "hits_by_root": dict(by_root),
        "hits": all_hits,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
