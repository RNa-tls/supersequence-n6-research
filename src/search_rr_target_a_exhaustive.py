#!/usr/bin/env python3
"""Round 35, sections 8, 13, 14: the uncapped Target A extension search.

TWO SEARCHES PER ROOT, because Target A and completability are different
questions (see build_rr_target_a_roots.py):

  Q1  uncapped-in-principle search with ONLY the safe prunes that a Target A
      boundary must satisfy: engine legality, area_a on the child, and "an RR
      word has exactly two R events".  The capacity bound is NOT used here --
      on one known ell=0 boundary it is already negative at the state its R2
      edge departs from, so it would delete that Target A boundary.  This search is expected to be
      INCOMPLETE and is reported as such.

  Q2  the same search plus the capacity bound of section 5, which is a sound
      necessary condition for an Area-A NR6 completion.  A root that
      exhausts here has no Target A boundary FROM WHICH A COMPLETION IS
      STILL POSSIBLE.

Statuses (section 13): FOUND_TARGET_A / EXHAUSTED_NO_TARGET_A / INCOMPLETE.
A node cap is never a proof condition and a timeout is never exhaustion: a
root reads EXHAUSTED_NO_TARGET_A only when its frontier empties naturally,
which is recorded per root as `frontier_emptied_naturally`.

CH1 / CH2 (section 8) are recorded as separate branch labels with their own
counters.  CH1 is "the hub completer edge C is itself the first R event";
CH2 is "C is a Z2 and R1 happened earlier".  All 22 roots already carry
exactly one R inside the prefix, so the branch is a property of the root and
is classified rather than searched twice.

Section 14: any newly found Target A boundary goes straight through the
existing pipeline -- witness, quotient comparison against the known 18,
capacity theorem, phase/R-reuse refinement -- and only a survivor of all of
that would be handed to the Round 34 flow solver.  The Target B search is
never restarted from scratch.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys, time
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"

spec = importlib.util.spec_from_file_location("brtar_mod", ROOT / "src" / "build_rr_target_a_roots.py")
B = importlib.util.module_from_spec(spec)
sys.modules["brtar_mod"] = B
spec.loader.exec_module(B)

macro, exact, core = B.macro, B.exact, B.core
mbl, W1, AREA_A, HUB = B.mbl, B.W1, B.AREA_A, B.HUB
phi, popcount, sha = B.phi, B.popcount, B.sha


def branch_label(rec):
    """Section 8: CH1 if the word's single R is also the hub completer,
    CH2 if the hub completer is a Z2 and the R happened elsewhere."""
    st = exact.initial_state()
    for _ in range(rec["root_ell"]):
        st = exact.extend(st, W1).state
    st = exact.extend(st, mbl["w2:10"]).state
    completer_kind, seen_r = None, False
    for lbl in rec["literal_joint_word"]:
        for _ in range(5):
            st = exact.extend(st, W1).state
        tr = exact.extend(st, mbl[lbl])
        k = B.joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
        if core.hexagon_id(tr.target) == HUB and completer_kind is None:
            completer_kind = k
        if k == "R":
            seen_r = True
        st = tr.state
    if completer_kind == "R":
        return "CH1", completer_kind
    if completer_kind is not None and seen_r:
        return "CH2", completer_kind
    return "CH_none" if completer_kind is None else "CH_other", completer_kind


def run(st, use_capacity_bound, node_cap, seconds):
    fr = deque([st])
    seen = {st.stable_key()}
    exp = 0
    hits, r2out, prunes = [], Counter(), Counter()
    maxdepth = 0
    depth_of = {st.stable_key(): 0}
    t0 = time.time()
    truncated_cap = truncated_time = False
    while fr:
        if node_cap is not None and exp >= node_cap:
            truncated_cap = True
            break
        if time.time() - t0 > seconds:
            truncated_time = True
            break
        cur = fr.popleft()
        d = depth_of[cur.stable_key()]
        exp += 1
        maxdepth = max(maxdepth, d)
        for e in macro.macro_edges(cur):
            tr = e.joint
            r = macro.area_a_prune_reason(tr.state, AREA_A)
            if r is not None:
                prunes[r] += 1
                continue
            k = B.joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            if k == "other":
                prunes["outside_RR_alphabet"] += 1
                continue
            if k == "R":
                # the second R of the word: a candidate Target A boundary,
                # never expanded past (definitional, 손증명)
                v = B.is_target_a(e)
                if v is None:
                    r2out["failed_F_H_or_area_a"] += 1
                elif v["same_component"]:
                    r2out["TARGET_A"] += 1
                    hits.append({**v, "extension_depth": d + 1,
                                 "boundary_raw_hash": sha(tr.state.stable_key())[:16],
                                 "boundary_canonical_hash":
                                     sha(exact.canonicalize(tr.state).stable_key())[:16]})
                else:
                    r2out[v["reason"]] += 1
                continue
            if use_capacity_bound:
                slack, _, _ = B.capacity_slack(tr.state)
                if slack < 0:
                    prunes["capacity_bound_Q2_only"] += 1
                    continue
            kk = tr.state.stable_key()
            if kk in seen:
                prunes["dedup"] += 1
                continue
            seen.add(kk)
            depth_of[kk] = d + 1
            fr.append(tr.state)
    natural = not (truncated_cap or truncated_time)
    if hits:
        status = "FOUND_TARGET_A"
    elif natural:
        status = "EXHAUSTED_NO_TARGET_A"
    else:
        status = "INCOMPLETE"
    return {"status": status, "expanded": exp, "distinct_states": len(seen),
            "max_r_free_depth": maxdepth, "seconds": round(time.time() - t0, 2),
            "frontier_emptied_naturally": natural,
            "truncated_by_node_cap": truncated_cap,
            "truncated_by_time": truncated_time,
            "r2_edge_outcomes": dict(r2out), "prune_histogram": dict(prunes),
            "n_target_a_boundaries": len(hits), "target_a_boundaries": hits[:20]}


def pipeline_for_new_boundary(hit, known):
    """Section 14, run only if a new boundary appears."""
    return {"witness": hit,
            "already_known": hit["boundary_canonical_hash"] in known,
            "next_steps": ["capacity theorem", "phase/R-reuse refinement",
                           "Round 34 flow solver, only if it survives both"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", default=str(ROOT / "outputs" / "rr_22_incomplete_roots.json"))
    ap.add_argument("--prefixes", default=str(ROOT / "outputs" / "rr_long_excursion_prefixes.json"))
    ap.add_argument("--survivors", default=str(ROOT / "outputs" / "rr_target_b_survivors.json"))
    ap.add_argument("--q1-seconds", type=float, default=45.0)
    ap.add_argument("--q1-node-cap", type=int, default=200000)
    ap.add_argument("--q2-seconds", type=float, default=1800.0)
    ap.add_argument("--out", default=str(ROOT / "outputs" / "rr_target_a_search_results.json"))
    a = ap.parse_args()

    data = json.loads(Path(a.roots).read_text(encoding="utf-8"))
    pref = json.loads(Path(a.prefixes).read_text(encoding="utf-8"))
    known = {r["canonical_state_hash"][:16]
             for r in json.loads(Path(a.survivors).read_text(encoding="utf-8"))["rows"]}
    inc = [r for r in data["roots"] if r["old_status"] == "INCOMPLETE"]

    print("=== section 8: CH1 / CH2 classification of the 22 roots ===")
    for x in inc:
        lbl, ck = branch_label(pref["prefixes"][x["prefix_index"]])
        x["ch_branch"], x["hub_completer_kind"] = lbl, ck
    print("  " + str(dict(Counter(x["ch_branch"] for x in inc)))
          + "  completer kinds " + str(dict(Counter(str(x["hub_completer_kind"]) for x in inc))))

    print("\n=== Q2: capacity-pruned exact search (uncapped, sound for completability) ===")
    rows = []
    for x in inc:
        rec = pref["prefixes"][x["prefix_index"]]
        st = B.replay_root(rec)
        if x["capacity_dead_at_root"]:
            q2 = {"status": "EXHAUSTED_NO_TARGET_A", "expanded": 0, "distinct_states": 1,
                  "max_r_free_depth": 0, "seconds": 0.0,
                  "frontier_emptied_naturally": True,
                  "truncated_by_node_cap": False, "truncated_by_time": False,
                  "r2_edge_outcomes": {}, "prune_histogram": {"capacity_bound_at_root": 1},
                  "n_target_a_boundaries": 0, "target_a_boundaries": [],
                  "decided_without_search": True}
        else:
            q2 = run(st, True, None, a.q2_seconds)
            q2["decided_without_search"] = False
        q1 = run(st, False, a.q1_node_cap, a.q1_seconds)
        rows.append({**{k: x[k] for k in ("prefix_index", "root_ell", "first_return_length_L",
                                          "symbolic_word", "capacity_slack",
                                          "capacity_dead_at_root", "ch_branch",
                                          "hub_completer_kind", "phi", "O", "Ndef")},
                     "Q2_completable_target_a": q2, "Q1_any_target_a": q1})
        print(f"  idx={x['prefix_index']:>3} ell={x['root_ell']} slack={x['capacity_slack']:>3} "
              f"{x['ch_branch']:<6} Q2 {q2['status']:<22} exp={q2['expanded']:>7} "
              f"natural={q2['frontier_emptied_naturally']} hits={q2['n_target_a_boundaries']} "
              f"| Q1 {q1['status']:<11} exp={q1['expanded']:>7}", flush=True)

    q2h = Counter(r["Q2_completable_target_a"]["status"] for r in rows)
    q1h = Counter(r["Q1_any_target_a"]["status"] for r in rows)
    new_hits = [h for r in rows for h in r["Q2_completable_target_a"]["target_a_boundaries"]]
    print(f"\n  Q2 status histogram: {dict(q2h)}")
    print(f"  Q1 status histogram: {dict(q1h)}")
    print(f"  new completable Target A boundaries found: {len(new_hits)}")
    q2_all_natural = all(r["Q2_completable_target_a"]["frontier_emptied_naturally"] for r in rows)
    print(f"  every Q2 frontier emptied naturally: {q2_all_natural}")

    Path(a.out).write_text(json.dumps({
        "schema": "rr-target-a-search-results-v1",
        "target_A_recognizer_sha256": data["target_A_recognizer_sha256"],
        "discipline": {
            "node_cap_is_not_a_proof_condition": True,
            "timeout_is_not_exhaustion": True,
            "exhausted_requires": "frontier_emptied_naturally == true",
            "Q1_capacity_bound_deliberately_not_used": (
                "on one ell=0 P_core=4 known boundary the bound is already negative at "
                "the state its R2 edge departs from, so using it for Q1 would delete that "
                "genuine Target A boundary"),
        },
        "Q2_status_histogram": {k: v for k, v in q2h.items()},
        "Q1_status_histogram": {k: v for k, v in q1h.items()},
        "Q2_all_frontiers_natural": q2_all_natural,
        "new_completable_target_a_boundaries": len(new_hits),
        "section_14_pipeline": [pipeline_for_new_boundary(h, known) for h in new_hits],
        "grade": ("exact exhaustive search for Q2 (completable Target A); "
                  "bounded incomplete for Q1 (Target A coverage without the "
                  "completability assumption)"),
        "results": rows,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
