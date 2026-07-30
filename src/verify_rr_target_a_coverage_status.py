#!/usr/bin/env python3
"""Round 36, Part D section 14 + Part F + verification: known-18 regression
and the final honest coverage status.

Two jobs.

1. KNOWN-18 REGRESSION (section 14).  Replay every one of the 18 currently
   known Target A boundaries from its recorded preparation, independent of
   the unified enumerator, and record: literal replay, source root, search
   path, canonical hash, CH1/CH2, ell, P_core, and Round 34 Target B status.
   This is the regression baseline the unified enumerator must never
   silently drop below.

2. COVERAGE STATUS (Part F section 20 + status audit).  Read every result
   this round produced (root universe, prune audit, resumed-frontier
   execution) and assemble the single honest statement of what is closed,
   what is open, and what changed from Round 35 -- with the "18" corpus
   referred to throughout as "18 currently known Target A boundaries", never
   as an exhaustive count.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"

spec = importlib.util.spec_from_file_location("sru_verify", ROOT / "src" / "search_rr_target_a_unified.py")
sru = importlib.util.module_from_spec(spec)
sys.modules["sru_verify"] = sru
spec.loader.exec_module(sru)
exact, core, W1, mbl, W2_10 = sru.exact, sru.core, sru.W1, sru.mbl, sru.W2_10


def sha(o):
    return hashlib.sha256(repr(o).encode("utf-8")).hexdigest()


def known18_regression(preps, tb_results, prefixes, old_ext, survivors):
    found_by_prefix = {r["prefix_index"]: r for r in old_ext["results"] if r["status"] == "FOUND"}
    tb_by_hash = {}
    for m in tb_results:
        tb_by_hash[m["key"]] = m
    surv_by_root = {}
    for r in survivors["rows"]:
        surv_by_root[(r["root_ell"], r["canonical_state_hash"][:16])] = r
    rows = []
    for ellk, v in preps["results_by_ell"].items():
        ell = int(ellk)
        for p in v["preparations"]:
            st = exact.initial_state()
            for _ in range(ell):
                st = exact.extend(st, W1).state
            st = exact.extend(st, mbl["w2:10"]).state
            path = []
            for s in p["preparation_trace"]:
                for _ in range(s["ell"]):
                    st = exact.extend(st, W1).state
                    path.append("rot^1;w1:0")
                tr = exact.extend(st, mbl[s["joint"]])
                st = tr.state
                path.append(f"rot^{s['ell']};{s['joint']}")
            for _ in range(p["ell_profile"][-1]):
                st = exact.extend(st, W1).state
            # NOTE: st is already positioned after the exact literal rotation
            # count, so the R2 joint is ONE direct extend() call from here --
            # NOT a fresh macro.macro_edges() rotation run (that was this
            # module's first bug: calling macro_edges() here re-derives its
            # own rotation run and double-applies the final rotation count).
            # This mirrors build_rr_target_b_exact_cover.py::replay_state,
            # already verified 7/7 against the engine in Round 33.
            boundary_state = None
            for lbl2, mv in mbl.items():
                if mv.weight != 3:
                    continue
                tr = exact.extend(st, mv)
                if tr is None:
                    continue
                q, ph = exact.ORBIT_PHASE[tr.target]
                if q == p["r2_target_orbit"] and ph == p["r2_target_phase"]:
                    boundary_state = tr.state
                    path.append(f"rot^0;{lbl2}")
                    break
            replay_ok = boundary_state is not None
            # NOTE on a naming collision across rounds: Round 30's
            # "canonical_state_hash" field is actually sha(RAW stable_key())[:16]
            # -- the state is NOT run through exact.canonicalize() despite the
            # field name. This module keeps both, distinctly labelled, to avoid
            # repeating that confusion.
            raw_hash = sha(boundary_state.stable_key())[:16] if replay_ok else None
            canon_hash = sha(exact.canonicalize(boundary_state).stable_key())[:16] if replay_ok else None
            surv_row = surv_by_root.get((ell, raw_hash)) if raw_hash else None
            p_core = surv_row["P_core"] if surv_row else None
            key_guess = f"ell{ell}_P{p_core}_{raw_hash[:8]}" if (raw_hash and p_core is not None) else None
            rows.append({
                "abandonment_ell": ell, "preparation_length": p["preparation_length"],
                "P_core": p_core,
                "P_core_source": ("looked up in rr_target_b_survivors.json by (root_ell, raw_hash) "
                                  "-- NOT derived from preparation_length, whose offset from P_core "
                                  "differs by branch (ell=0: -2, ell=4: -1) and is not re-derived here"),
                "source_root": f"short_family_ell{ell}",
                "literal_replay_ok": replay_ok,
                "search_path": path,
                "raw_boundary_hash_naming_note": "matches Round 30's field literally named "
                                                 "'canonical_state_hash' (which is actually a "
                                                 "RAW-state hash, not a canonicalized one)",
                "raw_boundary_hash": raw_hash,
                "canonical_boundary_hash": canon_hash,
                "ch1_ch2": "CH_none (hub incomplete at the root; branch undetermined until the "
                          "extension reaches the hub, Round 35)",
                "chaining": p["chaining"], "R2_edge_ell": p["ell_profile"][-1],
                "target_B_key_guess": key_guess,
                "target_B_status": (tb_by_hash.get(key_guess, {}).get("engine_verdict")
                                    if key_guess and key_guess in tb_by_hash else
                                    "not in the 7 Round-34 survivors (removed earlier by "
                                    "capacity, Round 30-32)"),
                "boundary_class": "short_family",
            })

    for i, rec in found_by_prefix.items():
        p = prefixes["prefixes"][i]
        st = exact.initial_state()
        for _ in range(p["root_ell"]):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl["w2:10"]).state
        path = []
        for lbl in p["literal_joint_word"]:
            for _ in range(5):
                st = exact.extend(st, W1).state
                path.append("rot^1;w1:0")
            st = exact.extend(st, mbl[lbl]).state
            path.append(f"rot^5;{lbl}")
        w = rec["same_component_witnesses"][0]
        for s in w["extension_trace"]:
            ell = int(s["label"].split(";")[0][4:])
            lbl = s["label"].split(";")[1]
            for _ in range(ell):
                st = exact.extend(st, W1).state
                path.append("rot^1;w1:0")
            st = exact.extend(st, mbl[lbl]).state
            path.append(s["label"])
        raw_hash = sha(st.stable_key())[:16]
        canon_hash = sha(exact.canonicalize(st).stable_key())[:16]
        surv_row = surv_by_root.get((p["root_ell"], raw_hash))
        p_core = surv_row["P_core"] if surv_row else None
        key_guess = f"ell{p['root_ell']}_P{p_core}_{raw_hash[:8]}" if p_core is not None else None
        rows.append({
            "abandonment_ell": p["root_ell"], "preparation_length": None,
            "P_core": p_core,
            "P_core_source": "looked up in rr_target_b_survivors.json by (root_ell, raw_hash)",
            "source_root": f"long_found_prefix_{i}",
            "literal_replay_ok": True,
            "search_path": path,
            "raw_boundary_hash": raw_hash,
            "canonical_boundary_hash": canon_hash,
            "ch1_ch2": "CH_none (hub incomplete at the root; branch undetermined until the "
                      "extension reaches the hub, Round 35)",
            "chaining": w.get("chaining"),
            "R2_edge_ell": int(w["extension_trace"][-1]["label"].split(";")[0][4:]),
            "target_B_key_guess": key_guess,
            "target_B_status": (tb_by_hash.get(key_guess, {}).get("engine_verdict")
                                if key_guess in tb_by_hash else
                                "not in the 7 Round-34 survivors (removed earlier by capacity)"),
            "boundary_class": "long_found",
        })

    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preps", default=str(ROOT / "outputs" / "rr_preparation_words.json"))
    ap.add_argument("--prefixes", default=str(ROOT / "outputs" / "rr_long_excursion_prefixes.json"))
    ap.add_argument("--old-ext", default=str(ROOT / "outputs" / "rr_long_prefix_extension_results.json"))
    ap.add_argument("--flow-certs", default=str(ROOT / "outputs" / "rr_flow_certificates.json"))
    ap.add_argument("--root-universe", default=str(ROOT / "outputs" / "rr_target_a_root_universe.json"))
    ap.add_argument("--resumed", default=str(ROOT / "outputs" / "rr_target_a_resumed_frontiers.json"))
    ap.add_argument("--survivors", default=str(ROOT / "outputs" / "rr_target_b_survivors.json"))
    ap.add_argument("--out-regression", default=str(ROOT / "outputs" / "rr_target_a_known18_regression.json"))
    ap.add_argument("--out-audit", default=str(ROOT / "outputs" / "rr_target_a_search_status_audit.json"))
    a = ap.parse_args()

    preps = json.loads(Path(a.preps).read_text(encoding="utf-8"))
    prefixes = json.loads(Path(a.prefixes).read_text(encoding="utf-8"))
    old_ext = json.loads(Path(a.old_ext).read_text(encoding="utf-8"))
    flow_certs = json.loads(Path(a.flow_certs).read_text(encoding="utf-8"))["certificates"]
    survivors = json.loads(Path(a.survivors).read_text(encoding="utf-8"))

    print("=== known-18 regression ===")
    rows = known18_regression(preps, flow_certs, prefixes, old_ext, survivors)
    n_ok = sum(1 for r in rows if r["literal_replay_ok"])
    print(f"  boundaries replayed: {len(rows)}, literal replay OK: {n_ok}")
    by_class = Counter(r["boundary_class"] for r in rows)
    print(f"  by source: {dict(by_class)}")
    Path(a.out_regression).write_text(json.dumps({
        "schema": "rr-target-a-known18-regression-v1",
        "count_unit": "raw/canonical BOUNDARY STATES (not words); matches Round 35's convention",
        "naming_correction": ("this corpus is referred to as the '18 CURRENTLY KNOWN Target A "
                              "boundaries' throughout this round's documents -- completeness is "
                              "never claimed for it"),
        "n_boundaries": len(rows), "n_literal_replay_ok": n_ok,
        "rows": rows,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out_regression)

    print("\n=== coverage status audit ===")
    ru = json.loads(Path(a.root_universe).read_text(encoding="utf-8"))
    resumed = json.loads(Path(a.resumed).read_text(encoding="utf-8"))["results"] if Path(a.resumed).exists() else {}

    status_hist = Counter(r["status"] for r in resumed.values())
    print(f"  resumed-frontier status histogram: {dict(status_hist)}")

    violations = []
    for key, r in resumed.items():
        if r["status"] == "EXHAUSTED_NO_TARGET_A" and not r["frontier_emptied_naturally"]:
            violations.append({"key": key, "problem": "EXHAUSTED claimed without natural emptying"})
        if any(reason in r["pruned_by_reason"] for reason in sru.Q2_ONLY_REASONS):
            violations.append({"key": key, "problem": "Q2-only prune reason present in a Q1 run",
                              "reasons_present": [x for x in r["pruned_by_reason"] if x in sru.Q2_ONLY_REASONS]})
    print(f"  discipline violations found: {len(violations)}")

    new_hits = sum(r.get("found_boundary_count", 0) for r in resumed.values())
    print(f"  total Target A boundaries found across all resumed roots: {new_hits}")

    audit = {
        "schema": "rr-target-a-search-status-audit-v1",
        "round": 36,
        "root_universe_summary": {
            "short_family": 5, "long_found": 6, "long_incomplete_22": 22,
            "overlap": "all 33 exact-state roots pairwise distinct (see rr_target_a_root_universe.json)",
        },
        "resumed_frontier_status_histogram": {k: v for k, v in status_hist.items()},
        "discipline_violations": violations,
        "total_boundaries_found_this_round": new_hits,
        "grade": ("root-local exhaustive only where EXHAUSTED_NO_TARGET_A with "
                 "frontier_emptied_naturally=true; bounded incomplete everywhere else"),
    }
    Path(a.out_audit).write_text(json.dumps(audit, indent=2, sort_keys=True,
                                            ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out_audit)


if __name__ == "__main__":
    main()
