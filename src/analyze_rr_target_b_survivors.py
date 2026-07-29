#!/usr/bin/env python3
"""Round 31, Part A: apply the capacity theorem to every known Target A
boundary and fix the exact survivor set.

CAPACITY THEOREM (Round 30, 손증명).  From a Phi=0 Target A boundary
state, a Target B continuation requires

    B <= 5*(O_cap + R_cap) + 4,       B = TARGET_P - P,
                                      O_cap = TARGET_O - O,
                                      R_cap = AREA_A.n_limit - N.

Cleaner derivation, used again in Round 31: the continuation's entry
ports p_0..p_B lie in orbit segments, one segment per maximal run of
orbit-preserving edges.  There are at most m+1 segments (m = number of
orbit-CHANGING edges) and a segment uses at most 5 ports of its orbit, so
B+1 <= 5(m+1), i.e. B <= 5m+4, and m <= O_cap + R_cap.

The theorem needs only Phi = 0 and the generator structure -- NOT ell=4 --
so it applies to the ell=0 boundaries as well.

The six long-preparation states are already closed (Round 30) and are NOT
re-searched here; they are carried in the corpus for completeness only.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"


def _load(n, f):
    p = WORK / f
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s)
    sys.modules[n] = m
    s.loader.exec_module(m)
    return m


macro = _load("artbs", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]


def phi(s):
    return 5 + 6 * (exact.TARGET_P - s.P) - (720 - s.visited_count)


def state_hash(s):
    return hashlib.sha256(repr(s.stable_key()).encode()).hexdigest()


def replay_historical(ell, prep):
    """Replay a historical preparation record through to the post-R2 state."""
    st = exact.initial_state()
    for _ in range(ell):
        st = exact.extend(st, W1).state
    st = exact.extend(st, W2_10).state
    for s in prep["preparation_trace"]:
        for _ in range(s["ell"]):
            tr = exact.extend(st, W1)
            if tr is None:
                return None
            st = tr.state
        tr = exact.extend(st, mbl[s["joint"]])
        if tr is None:
            return None
        st = tr.state
    for _ in range(prep["ell_profile"][-1]):
        tr = exact.extend(st, W1)
        if tr is None:
            return None
        st = tr.state
    for lbl, mv in mbl.items():
        if mv.weight != 3:
            continue
        tr = exact.extend(st, mv)
        if tr is None:
            continue
        q, ph = exact.ORBIT_PHASE[tr.target]
        if q == prep["r2_target_orbit"] and ph == prep["r2_target_phase"]:
            return tr.state
    return None


def replay_long(w):
    st = exact.initial_state()
    for _ in range(w["root_ell"]):
        st = exact.extend(st, W1).state
    st = exact.extend(st, W2_10).state
    for lab in w["literal_full_word"]:
        e, l = lab.split(";")
        for _ in range(int(e.split("^")[1])):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl[l]).state
    return st


def capacity_row(st, provenance, cls, extra):
    B = exact.TARGET_P - st.P
    O_cap = exact.TARGET_O - st.O
    R_cap = max(macro.AREA_A.n_limit - st.Ndef, 0)
    bound = 5 * (O_cap + R_cap) + 4
    legal = []
    for e in macro.macro_edges(st):
        tr = e.joint
        if macro.area_a_prune_reason(tr.state, macro.AREA_A) is None:
            legal.append(f"rot^{e.run.ell};{tr.move.label}")
    return {
        "provenance": provenance, "preparation_class": cls,
        "canonical_state_hash": state_hash(st)[:16],
        "B": B, "O_cap": O_cap, "R_cap": R_cap,
        "bound": bound, "margin": bound - B,
        "O": st.O, "P": st.P, "D": 5 * st.O - st.P, "phi": phi(st),
        "visited": st.visited_count,
        "legal_outgoing_signature": sorted(legal),
        "verdict": "CAPACITY_IMPOSSIBLE" if B > bound else "CAPACITY_SURVIVOR",
        **extra,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preps", default=str(ROOT / "outputs" / "rr_preparation_words.json"))
    ap.add_argument("--long", default=str(ROOT / "outputs" / "rr_six_counterexamples.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_target_b_survivors.json"))
    a = ap.parse_args()

    rows = []
    d = json.loads(Path(a.preps).read_text(encoding="utf-8"))
    for ell, r in d["results_by_ell"].items():
        for p in r["preparations"]:
            st = replay_historical(int(ell), p)
            if st is None:
                continue
            rows.append(capacity_row(st, "historical corpus", "short", {
                "root_ell": int(ell), "P_core": p["edges_before_completer"],
                "raw_state_hash": p["raw_state_hash"][:12],
                "chaining": p.get("chaining"),
            }))
    for i, w in enumerate(json.loads(Path(a.long).read_text(encoding="utf-8"))["witnesses"]):
        st = replay_long(w)
        rows.append(capacity_row(st, "Round 27 long witness", "long", {
            "root_ell": w["root_ell"], "P_core": w["P_core"],
            "witness_index": i, "chaining": w["chaining"],
        }))

    rows.sort(key=lambda r: (r["preparation_class"], r["root_ell"], r["P_core"],
                             r["canonical_state_hash"]))

    print("=== full Target A corpus, capacity theorem applied ===")
    print(" cls    ell P_core   B  O_cap R_cap bound margin   O   P   D  verdict")
    for r in rows:
        print(f" {r['preparation_class']:<6} {r['root_ell']:>2}  {r['P_core']:>4}  "
              f"{r['B']:>4}  {r['O_cap']:>4}  {r['R_cap']:>3}  {r['bound']:>4}  "
              f"{r['margin']:>5}  {r['O']:>3} {r['P']:>3} {r['D']:>3}  {r['verdict']}")

    surv = [r for r in rows if r["verdict"] == "CAPACITY_SURVIVOR"]
    imp = [r for r in rows if r["verdict"] == "CAPACITY_IMPOSSIBLE"]
    print(f"\n boundary STATES: {len(rows)}  "
          f"(survivors {len(surv)}, impossible {len(imp)})")
    print(f" distinct canonical state hashes among survivors: "
          f"{len({r['canonical_state_hash'] for r in surv})}")
    print(f" distinct legal outgoing signatures among survivors: "
          f"{len({tuple(r['legal_outgoing_signature']) for r in surv})}")

    mh = Counter(r["margin"] for r in surv)
    print(f"\n=== margin distribution among survivors ===")
    print(f"   M = 0      : {mh.get(0,0)}")
    print(f"   M in 1..4  : {sum(v for k,v in mh.items() if 1 <= k <= 4)}")
    print(f"   M >= 5     : {sum(v for k,v in mh.items() if k >= 5)}")
    print(f"   full histogram: {dict(sorted(mh.items()))}")

    by_class = Counter((r["preparation_class"], r["verdict"]) for r in rows)
    print(f"\n by class: {dict(by_class)}")

    Path(a.output).write_text(json.dumps({
        "schema": "rr-target-b-survivors-v1",
        "capacity_theorem": {
            "statement": "B <= 5*(O_cap + R_cap) + 4",
            "grade": "손증명",
            "derivation": ("continuation entry ports p_0..p_B split into at most m+1 orbit "
                           "segments (m = orbit-changing edges); a segment uses at most 5 "
                           "ports of its orbit, so B+1 <= 5(m+1)"),
            "scope": ("needs only Phi=0 and the generator structure; applies to ell=0 "
                      "boundaries as well as ell=4"),
        },
        "counting_note": ("rows are boundary STATES, not words; the historical corpus "
                          "contributes one state per preparation record"),
        "n_boundary_states": len(rows),
        "n_survivors": len(surv),
        "n_capacity_impossible": len(imp),
        "distinct_survivor_state_hashes": len({r["canonical_state_hash"] for r in surv}),
        "distinct_survivor_legal_signatures": len(
            {tuple(r["legal_outgoing_signature"]) for r in surv}),
        "survivor_margin_histogram": {str(k): v for k, v in sorted(mh.items())},
        "rows": rows,
        "grade": "safe capacity bound + exact replay",
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.output)


if __name__ == "__main__":
    main()
