#!/usr/bin/env python3
"""Round 36, Part E: the coverage execution driver.

Runs the unified enumerator (search_rr_target_a_unified.py) over every root
in the audited universe (build_rr_target_a_root_universe.py), in the
priority order Part E specifies:

  1. short-family roots (5) -- smallest resumed/re-run frontier first is not
     meaningful here since all 5 start from a bare abandonment state; run in
     ell order 0,1,2,3,4.
  2. long FOUND roots (6) -- re-run without --stop-on-first.
  3. the 22 long INCOMPLETE roots -- Q1-safe enumerator (Q2 already closed
     in Round 35 and is NOT re-run here).
  4. (there is no separate "large ell=4 short frontier" beyond #1; the ell=4
     short-family root IS that frontier, run first in group 1.)

IMPORTANT CORRECTION relative to the naive re-use of build_rr_target_a_
roots.py: a SHORT-family root's r_count is 0 (the abandonment edge is a
Z2abandon event, not an R event -- the root has used NEITHER of its two R
budget slots yet). A long-excursion-prefix root's r_count is 1 (the R-budget
obstruction filter guarantees exactly one R already inside the prefix).
Passing the wrong r_count would silently change which edges are treated as
"the second R" and corrupt every downstream count; both values are computed
from the actual replayed state's history, not hard-coded.

Every root gets its own checkpoint file and independent budget so a slow
root cannot starve the others.  No status is ever upgraded past what the
enumerator actually returned.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"
CKDIR = ROOT / "outputs" / "rr_target_a_checkpoints"

spec = importlib.util.spec_from_file_location("sru_run", ROOT / "src" / "search_rr_target_a_unified.py")
sru = importlib.util.module_from_spec(spec)
sys.modules["sru_run"] = sru
spec.loader.exec_module(sru)

exact, core, W1, mbl, W2_10 = sru.exact, sru.core, sru.W1, sru.mbl, sru.W2_10


def replay_short_root(ell):
    st = exact.initial_state()
    for _ in range(ell):
        st = exact.extend(st, W1).state
    st = exact.extend(st, W2_10).state
    return st, 0  # r_count = 0: the abandonment is not an R event


def replay_long_root(rec):
    st = exact.initial_state()
    for _ in range(rec["root_ell"]):
        st = exact.extend(st, W1).state
    st = exact.extend(st, W2_10).state
    for lbl in rec["literal_joint_word"]:
        for _ in range(5):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl[lbl]).state
    return st, rec["r_count"]  # r_count = 1, guaranteed by the R-budget obstruction filter


def run_one(key, st, r0, node_cap, seconds, resume):
    ckpath = CKDIR / f"{key}.json"
    CKDIR.mkdir(parents=True, exist_ok=True)
    resume_from = str(ckpath) if (resume and ckpath.exists()) else None
    t0 = time.time()
    res = sru.enumerate_target_a(st, r0, mode="Q1", coverage=True, node_cap=node_cap,
                                 depth_cap=None, seconds=seconds,
                                 checkpoint_path=str(ckpath), checkpoint_every=20000,
                                 resume_from=resume_from)
    res["key"] = key
    res["resumed_from_checkpoint"] = resume_from is not None
    res["wall_seconds"] = round(time.time() - t0, 2)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefixes", default=str(ROOT / "outputs" / "rr_long_excursion_prefixes.json"))
    ap.add_argument("--old-ext", default=str(ROOT / "outputs" / "rr_long_prefix_extension_results.json"))
    ap.add_argument("--node-cap", type=int, default=150000)
    ap.add_argument("--seconds", type=float, default=150.0)
    ap.add_argument("--groups", default="short,found,incomplete22",
                    help="comma list of groups to run this invocation")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "outputs" / "rr_target_a_resumed_frontiers.json"))
    a = ap.parse_args()
    groups = set(a.groups.split(","))

    prefixes = json.loads(Path(a.prefixes).read_text(encoding="utf-8"))
    old_ext = json.loads(Path(a.old_ext).read_text(encoding="utf-8"))
    surviving = set(prefixes["r_budget_obstruction"]["surviving_indices"])
    found_recs = [r for r in old_ext["results"] if r["status"] == "FOUND"]
    inc_recs = [r for r in old_ext["results"] if r["status"] == "INCOMPLETE"]
    assert {r["prefix_index"] for r in found_recs} | {r["prefix_index"] for r in inc_recs} == surviving

    existing = {}
    if Path(a.out).exists():
        existing = json.loads(Path(a.out).read_text(encoding="utf-8")).get("results", {})

    results = dict(existing)

    if "short" in groups:
        print("=== group 1: short-family roots (5), r_count=0, priority order ell=0..4 ===")
        for ell in range(5):
            key = f"short_ell{ell}"
            st, r0 = replay_short_root(ell)
            print(f"  running {key} ...", flush=True)
            res = run_one(key, st, r0, a.node_cap, a.seconds, a.resume)
            results[key] = res
            print(f"  {key}: {res['status']} expanded={res['expanded_nodes']} "
                  f"hits={res['found_boundary_count']} natural={res['frontier_emptied_naturally']} "
                  f"queued={res['queued_frontier_at_stop']} secs={res['wall_seconds']}", flush=True)
            Path(a.out).write_text(json.dumps({"schema": "rr-target-a-resumed-frontiers-v1",
                                               "results": results}, indent=2, sort_keys=True,
                                               ensure_ascii=False, default=str), encoding="utf-8")

    if "found" in groups:
        print("\n=== group 2: long FOUND roots (6), r_count=1, re-run without stop-on-first ===")
        for rec in sorted(found_recs, key=lambda r: r["prefix_index"]):
            key = f"long_found_{rec['prefix_index']}"
            st, r0 = replay_long_root(prefixes["prefixes"][rec["prefix_index"]])
            print(f"  running {key} (was FOUND via stop-on-first, node {rec['nodes_expanded']}) ...",
                  flush=True)
            res = run_one(key, st, r0, a.node_cap, a.seconds, a.resume)
            results[key] = res
            print(f"  {key}: {res['status']} expanded={res['expanded_nodes']} "
                  f"hits={res['found_boundary_count']} natural={res['frontier_emptied_naturally']} "
                  f"queued={res['queued_frontier_at_stop']} secs={res['wall_seconds']}", flush=True)
            Path(a.out).write_text(json.dumps({"schema": "rr-target-a-resumed-frontiers-v1",
                                               "results": results}, indent=2, sort_keys=True,
                                               ensure_ascii=False, default=str), encoding="utf-8")

    if "incomplete22" in groups:
        print("\n=== group 3: the 22 long INCOMPLETE roots, Q1-safe enumerator ===")
        for rec in sorted(inc_recs, key=lambda r: r["prefix_index"]):
            key = f"long_q1_{rec['prefix_index']}"
            st, r0 = replay_long_root(prefixes["prefixes"][rec["prefix_index"]])
            print(f"  running {key} ...", flush=True)
            res = run_one(key, st, r0, a.node_cap, a.seconds, a.resume)
            results[key] = res
            print(f"  {key}: {res['status']} expanded={res['expanded_nodes']} "
                  f"hits={res['found_boundary_count']} natural={res['frontier_emptied_naturally']} "
                  f"queued={res['queued_frontier_at_stop']} secs={res['wall_seconds']}", flush=True)
            Path(a.out).write_text(json.dumps({"schema": "rr-target-a-resumed-frontiers-v1",
                                               "results": results}, indent=2, sort_keys=True,
                                               ensure_ascii=False, default=str), encoding="utf-8")

    print(f"\nwrote {a.out} ({len(results)} roots total so far)")


if __name__ == "__main__":
    main()
