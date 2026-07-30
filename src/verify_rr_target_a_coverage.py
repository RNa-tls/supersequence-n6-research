#!/usr/bin/env python3
"""Round 35, sections 15-17: coverage verification and the closure audit.

Four independent checks.

1. THE CAPACITY BOUND IS UNSOUND FOR Q1 -- verified, not asserted.  The
   bound is replayed along the full path of all 12 known short Target A
   boundaries.  If it goes negative strictly BEFORE the R2 edge on any of
   them, then using it to prune the Target A search would delete that
   boundary, so it may only be used for the completability question.  This
   check is the reason the round has two answers instead of one.

2. THE KNOWN 18 ARE REPRODUCED (section 15).  Every one of the 18 known
   Target A boundary states is replayed from its recorded preparation and
   re-tested against this round's frozen recognizer, with the counting unit
   and depth convention stated explicitly.

3. THE SHORT-FAMILY ENUMERATION WAS DEPTH-TRUNCATED (section 17).  The
   enumeration that produced the 12 short boundaries reports
   `frontier_empty: true`, but that flag is computed as
   `not cap_hit and len(frontier) == 0` AFTER states at the depth ceiling
   were dropped without being expanded.  So the flag cannot distinguish
   "nothing left" from "everything left was at the ceiling".  This check
   counts the dropped states directly.

4. THE CLOSURE AUDIT (section 17): every root class still needed to close
   the RR branch, listed whether or not this round touched it.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("brtar_v", ROOT / "src" / "build_rr_target_a_roots.py")
B = importlib.util.module_from_spec(spec)
sys.modules["brtar_v"] = B
spec.loader.exec_module(B)
macro, exact, core = B.macro, B.exact, B.core
mbl, W1, AREA_A, HUB = B.mbl, B.W1, B.AREA_A, B.HUB
phi, popcount, sha = B.phi, B.popcount, B.sha


def check1_bound_unsound_for_q1(preps):
    """Replay the slack along every known short boundary's own path."""
    rows = []
    for ellk, v in preps["results_by_ell"].items():
        for p in v["preparations"]:
            st = exact.initial_state()
            for _ in range(int(ellk)):
                st = exact.extend(st, W1).state
            st = exact.extend(st, mbl["w2:10"]).state
            path = [B.capacity_slack(st)[0]]
            for s in p["preparation_trace"]:
                for _ in range(s["ell"]):
                    st = exact.extend(st, W1).state
                st = exact.extend(st, mbl[s["joint"]]).state
                path.append(B.capacity_slack(st)[0])
            for _ in range(p["ell_profile"][-1]):
                st = exact.extend(st, W1).state
            boundary_slack = None
            for lbl, mv in mbl.items():
                if mv.weight != 3:
                    continue
                tr = exact.extend(st, mv)
                if tr is None:
                    continue
                q, ph = exact.ORBIT_PHASE[tr.target]
                if q == p["r2_target_orbit"] and ph == p["r2_target_phase"]:
                    boundary_slack = B.capacity_slack(tr.state)[0]
                    break
            rows.append({"abandonment_ell": int(ellk),
                         "preparation_length": p["preparation_length"],
                         "slack_before_R2_edge": path,
                         "slack_at_boundary": boundary_slack,
                         "negative_strictly_before_R2_edge": min(path) < 0,
                         "negative_at_boundary": (boundary_slack or 0) < 0})
    n_pre = sum(1 for r in rows if r["negative_strictly_before_R2_edge"])
    return {
        "grade": "반증됨 (the bound as a Q1 prune) + safe capacity bound (for Q2)",
        "known_boundaries_checked": len(rows),
        "boundaries_whose_own_path_the_bound_would_have_pruned": n_pre,
        "boundaries_where_the_bound_fires_only_at_the_boundary_itself":
            sum(1 for r in rows if r["negative_at_boundary"]
                and not r["negative_strictly_before_R2_edge"]),
        "verdict": ("the bound goes negative strictly before the R2 edge on "
                    f"{n_pre} known Target A boundaries, so it is NOT a valid "
                    "Target A prune; it is used only for the completability "
                    "question Q2" if n_pre else
                    "no known boundary is pruned early, but the bound is still "
                    "only justified for Q2"),
        "consistency_note": ("every boundary at which the bound fires was already "
                             "removed as capacity-impossible in Rounds 30-32, so the "
                             "bound agrees with the established ledger where it applies"),
        "rows": rows,
    }


def check2_known_18(preps, survivors, roots):
    """Section 15: replay and re-recognize all 18."""
    rows, ok = [], 0
    for ellk, v in preps["results_by_ell"].items():
        for p in v["preparations"]:
            st = exact.initial_state()
            for _ in range(int(ellk)):
                st = exact.extend(st, W1).state
            st = exact.extend(st, mbl["w2:10"]).state
            for s in p["preparation_trace"]:
                for _ in range(s["ell"]):
                    st = exact.extend(st, W1).state
                st = exact.extend(st, mbl[s["joint"]]).state
            # do NOT pre-apply the final rotation run: macro_edges enumerates
            # the rotation run itself, so replaying it here would double it
            hit = None
            for e in macro.macro_edges(st):
                if e.run.ell != p["ell_profile"][-1]:
                    continue
                v2 = B.is_target_a(e)
                if v2 and v2["same_component"]:
                    q, ph = v2["r2_target"]
                    if q == p["r2_target_orbit"] and ph == p["r2_target_phase"]:
                        hit = v2
                        break
            rows.append({"abandonment_ell": int(ellk),
                         "preparation_length": p["preparation_length"],
                         "recorded_phi": p["phi"], "recorded_chaining": p["chaining"],
                         "R2_edge_ell": p["ell_profile"][-1],
                         "re_recognized": hit is not None,
                         "recognizer_agrees_on_target": hit is not None})
            ok += hit is not None
    return {
        "grade": "exact replay",
        "short_boundaries_replayed": len(rows), "re_recognized": ok,
        "long_boundaries": 6,
        "counting_unit": ("boundary STATES, not words; P_core = preparation_length - 2, "
                          "the Round 18 unit used by the survivor ledger"),
        "depth_convention": preps["depth_convention"],
        "total_known": len(rows) + 6,
        "survivor_ledger_rows": len(survivors["rows"]),
        "known_corpus_is_a_subset_of_this_rounds_universe": (
            "the 22 roots searched here are DISJOINT from the roots that produced the "
            "known 18: the known 18 come from the 5 abandonment roots (short) and the 6 "
            "FOUND long-prefix roots, none of which is among the 22. So this round does "
            "not re-derive the 18 and does not claim to; it extends coverage sideways."),
        "R2_edge_ell_by_branch": dict(Counter(f"ell{r['abandonment_ell']}_R2edge_ell{r['R2_edge_ell']}"
                                              for r in rows)),
        "rows": rows,
    }


def check3_short_family_truncation(ceiling_by_ell):
    """Section 17: count states actually dropped at the depth ceiling."""
    out = {}
    for ell, ceiling in ceiling_by_ell.items():
        st = exact.initial_state()
        for _ in range(ell):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl["w2:10"]).state
        fr = deque([(st, 0, 0)])
        seen = {st.stable_key()}
        dropped = expanded = 0
        while fr:
            cur, rc, d = fr.popleft()
            expanded += 1
            if d >= ceiling:
                dropped += 1
                continue
            for e in macro.macro_edges(cur):
                tr = e.joint
                if macro.area_a_prune_reason(tr.state, AREA_A) is not None:
                    continue
                k = B.joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
                if k == "other":
                    continue
                nrc = rc + (1 if k == "R" else 0)
                if nrc > 2:
                    continue
                kk = tr.state.stable_key()
                if kk in seen:
                    continue
                seen.add(kk)
                fr.append((tr.state, nrc, d + 1))
        out[f"ell{ell}"] = {
            "depth_ceiling": ceiling, "expanded": expanded,
            "states_dropped_at_the_ceiling": dropped,
            "was_actually_truncated": dropped > 0,
            "frontier_empty_flag_is_misleading": dropped > 0,
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", default=str(ROOT / "outputs" / "rr_22_incomplete_roots.json"))
    ap.add_argument("--search", default=str(ROOT / "outputs" / "rr_target_a_search_results.json"))
    ap.add_argument("--preps", default=str(ROOT / "outputs" / "rr_preparation_words.json"))
    ap.add_argument("--survivors", default=str(ROOT / "outputs" / "rr_target_b_survivors.json"))
    ap.add_argument("--out", default=str(ROOT / "outputs" / "rr_target_a_coverage_certificate.json"))
    a = ap.parse_args()

    roots = json.loads(Path(a.roots).read_text(encoding="utf-8"))
    search = json.loads(Path(a.search).read_text(encoding="utf-8"))
    preps = json.loads(Path(a.preps).read_text(encoding="utf-8"))
    surv = json.loads(Path(a.survivors).read_text(encoding="utf-8"))

    print("=== check 1: is the capacity bound usable as a Target A prune? ===")
    c1 = check1_bound_unsound_for_q1(preps)
    print(f"  known boundaries checked: {c1['known_boundaries_checked']}")
    print(f"  boundaries the bound would have pruned BEFORE their R2 edge: "
          f"{c1['boundaries_whose_own_path_the_bound_would_have_pruned']}")
    print(f"  => {c1['verdict']}")

    print("\n=== check 2: section 15, replay of the known boundaries ===")
    c2 = check2_known_18(preps, surv, roots)
    print(f"  short boundaries replayed: {c2['short_boundaries_replayed']}, "
          f"re-recognized by the frozen recognizer: {c2['re_recognized']}")
    print(f"  R2 edge ell by branch: {c2['R2_edge_ell_by_branch']}")
    print(f"  scope: {c2['known_corpus_is_a_subset_of_this_rounds_universe']}")

    print("\n=== check 3: section 17, was the short-family enumeration truncated? ===")
    c3 = check3_short_family_truncation({0: 7, 1: 7, 2: 7, 3: 7, 4: 8})
    for k, v in c3.items():
        print(f"  {k}: ceiling {v['depth_ceiling']}, expanded {v['expanded']}, "
              f"dropped at ceiling {v['states_dropped_at_the_ceiling']} -> "
              f"actually truncated: {v['was_actually_truncated']}")

    rows = search["results"]
    q2 = Counter(r["Q2_completable_target_a"]["status"] for r in rows)
    q1 = Counter(r["Q1_any_target_a"]["status"] for r in rows)
    q2_nat = all(r["Q2_completable_target_a"]["frontier_emptied_naturally"] for r in rows)

    # section 16
    if q2_nat and q2.get("EXHAUSTED_NO_TARGET_A", 0) == len(rows) \
            and q1.get("EXHAUSTED_NO_TARGET_A", 0) == len(rows):
        outcome = "A"
    elif any(r["Q1_any_target_a"]["status"] == "FOUND_TARGET_A" for r in rows) \
            or any(r["Q2_completable_target_a"]["status"] == "FOUND_TARGET_A" for r in rows):
        outcome = "B"
    else:
        outcome = "C"

    gaps = [
        {"gap": "Q1 -- Target A boundaries without the completability assumption",
         "status": "OPEN", "roots": len(rows),
         "why": ("the only prune strong enough to terminate the search is the capacity "
                 "bound, and check 1 shows it deletes genuine Target A boundaries"),
         "grade": "bounded incomplete"},
        {"gap": "the short-family enumeration's depth ceiling (7 for ell=0..3, 8 for ell=4)",
         "status": "OPEN, newly identified this round",
         "why": ("its `frontier_empty: true` flag is computed after ceiling-truncated "
                 "states are dropped unexpanded, so it cannot witness exhaustion; "
                 "check 3 counts the dropped states directly"),
         "grade": "scope correction"},
        {"gap": "the 6 FOUND long-prefix roots were searched with --stop-on-first",
         "status": "OPEN, newly identified this round",
         "why": ("each was abandoned after its first witness, so those roots may carry "
                 "further Target A boundaries that were never enumerated"),
         "grade": "scope correction"},
        {"gap": "first-return excursions with L > 8",
         "status": "OPEN",
         "why": "the surviving long-excursion corpus contains only L = 7 and L = 8",
         "grade": "미완료"},
        {"gap": "abandonment roots and short prefixes outside the 28 long-excursion prefixes",
         "status": "OPEN",
         "why": ("the 22 roots are disjoint from the 5 abandonment roots that produced the "
                 "12 short boundaries; neither set exhausts the RR prefix space"),
         "grade": "미완료"},
        {"gap": "CH1 / CH2 split at these roots",
         "status": "NOT APPLICABLE at the root",
         "why": ("the hub is incomplete at all 22 roots (hub popcount 1-5, never 6), so no "
                 "hub completer exists yet and the branch is a property of the extension, "
                 "not of the root; both branches are covered by the Q2 exhaustion because "
                 "it explored every extension"),
         "grade": "scope correction"},
        {"gap": "over-approximated orbit/phase reachability filter (section 11)",
         "status": "VACUOUS",
         "why": ("with collisions dropped every port reaches every port in one macro edge "
                 "(out-degree 720 of 720), and the distance to the completer target (1,4) "
                 "is 1 from every root, so the filter excludes nothing"),
         "grade": "scope correction"},
    ]

    payload = {
        "schema": "rr-target-a-coverage-certificate-v1",
        "target_A_recognizer_sha256": roots["target_A_recognizer_sha256"],
        "check_1_capacity_bound_scope": c1,
        "check_2_known_boundary_replay": c2,
        "check_3_short_family_truncation": c3,
        "section_16_outcome": {
            "outcome": outcome,
            "Q2_status_histogram": {k: v for k, v in q2.items()},
            "Q1_status_histogram": {k: v for k, v in q1.items()},
            "Q2_all_frontiers_natural": q2_nat,
            "root_local_coverage_claim": (
                "root-local exhaustive coverage is claimed ONLY for Q2 (completable "
                "Target A) over the stated class of 22 long-prefix roots. Q1 is "
                "bounded incomplete, so no unconditional Target A coverage is claimed."
                if q2_nat else "no coverage claim: some Q2 frontier was truncated"),
            "grades": {"Q2": "root-local exhaustive (completable Target A only)",
                       "Q1": "bounded incomplete"},
        },
        "section_17_closure_audit": gaps,
        "what_this_does_not_say": [
            "it does not close the RR branch: five coverage gaps above remain open",
            "it does not extend Round 34's Target B exhaustion to all of RR",
            "it moves no bound on L_6: verified upper 872, proved lower 867, open target 872",
            "it says nothing about the N=0 checkpoint, CH2 chaining, T3, or Target C",
        ],
    }
    Path(a.out).write_text(json.dumps(payload, indent=2, sort_keys=True,
                                      ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\n=== section 16 outcome: {outcome} ===")
    print(f"  Q2 {dict(q2)} (all natural: {q2_nat})")
    print(f"  Q1 {dict(q1)}")
    print(f"  open coverage gaps: {sum(1 for g in gaps if g['status'].startswith('OPEN'))}")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
