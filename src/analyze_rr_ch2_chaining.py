#!/usr/bin/env python3
"""Round 30, Part B sections 12-19: the CH2 chaining problem.

CH1 (Round 29, 손증명) settles the 5 cases where the hub completer C is
itself an R: then C = R1 (R2 comes after C) and C's target is (1,4), so
R1 target = R2 source = orbit 1.

CH2 is the remaining case: C is a Z2.  This file fixes that corpus,
determines which event actually OPENS orbit 1, and runs a root-local
exhaustive search for a counterexample.

A correction the round's own sketch needs: the proposed Lemma CH2-B
("orbit 1's first opener is R1") is FALSE.  Orbit 1 is opened by the
ABANDONMENT itself -- at ell=4 the abandonment joint lands on (1,0).  So
the first-opener route cannot give chaining, and section 17's check is
reported as a refutation of that route rather than as support for it.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from collections import Counter, deque
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


macro = _load("arcc", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
HUB = core.hexagon_id(exact.initial_state().p)
O_STAR = 1


def joint_kind(w, ab, nw):
    return {(2, False, False): "Z2", (2, True, True): "Z2abandon",
            (3, False, False): "R", (3, False, True): "Z3"}.get((w, ab, nw), "other")


def sym(k):
    return "R" if k == "R" else ("F" if k == "Z3" else "E")


def ell4_root():
    st = exact.initial_state()
    for _ in range(4):
        st = exact.extend(st, W1).state
    tr = exact.extend(st, W2_10)
    return tr.state, tr.target


def abandonment_opens_orbit1():
    """Section 16/17: which event opens orbit 1?"""
    st = exact.initial_state()
    for _ in range(4):
        st = exact.extend(st, W1).state
    before = st.orbit_masks[O_STAR]
    tr = exact.extend(st, W2_10)
    after = tr.state.orbit_masks[O_STAR]
    return {
        "orbit1_mask_before_abandonment": before,
        "orbit1_mask_after_abandonment": after,
        "abandonment_target": list(exact.ORBIT_PHASE[tr.target]),
        "abandonment_new_orbit_flag": bool(tr.new_orbit),
        "orbit1_opened_by": ("the abandonment joint" if before == 0 and after != 0
                             else "something earlier"),
        "verdict": ("Lemma CH2-B as proposed is 반증됨: orbit 1's first opener is the "
                    "abandonment, not R1. The first-opener route cannot yield chaining."),
    }


def ch2_corpus(witnesses, prep_words):
    """Section 12: the exact cases with C = Z2."""
    rows = []
    for i, w in enumerate(witnesses):
        C = w["trace"][w["C_index"]]
        if C["sym"] == "R":
            continue
        r1 = w["trace"][w["R_indices"][0]]
        rows.append({
            "source": "long witness", "index": i, "root_ell": w["root_ell"],
            "C_index": w["C_index"], "C_label": C["label"], "C_sym": C["sym"],
            "C_target": [C["target_orbit"], C["target_phase"]],
            "R1_index": w["R_indices"][0], "R1_label": r1["label"],
            "R1_target": [r1["target_orbit"], r1["target_phase"]],
            "R1_to_C_macro_distance": w["C_index"] - w["R_indices"][0],
            "intervening_symbolic": "".join(
                x["sym"] for x in w["trace"][w["R_indices"][0] + 1:w["C_index"]]),
            "O_star_phase_sequence": w["O_star_phase_sequence"],
            "winding_k": w["winding_number_k"],
            "n_R_odd_delta": w["n_R_steps_with_odd_delta"],
            "P_core": w["P_core"], "chaining": w["chaining"],
        })
    for ell, r in prep_words["results_by_ell"].items():
        if ell != "4":
            continue
        for p in r["preparations"]:
            ci = p["edges_before_completer"]
            tr = p["preparation_trace"]
            if ci >= len(tr) or tr[ci]["kind"] == "R":
                continue
            ridx = [j for j, s in enumerate(tr) if s["kind"] == "R"]
            rows.append({
                "source": "historical", "index": p["raw_state_hash"][:12],
                "root_ell": 4, "C_index": ci, "C_label": tr[ci]["label"],
                "C_sym": sym(tr[ci]["kind"]), "C_target": tr[ci]["tgt"],
                "R1_index": ridx[0] if ridx else None,
                "R1_label": tr[ridx[0]]["label"] if ridx else None,
                "R1_target": tr[ridx[0]]["tgt"] if ridx else None,
                "R1_to_C_macro_distance": (ci - ridx[0]) if ridx else None,
                "intervening_symbolic": "".join(
                    sym(s["kind"]) for s in tr[(ridx[0] + 1 if ridx else 0):ci]),
                "P_core": ci, "chaining": p.get("chaining"),
            })
    return rows


def counterexample_search(depth, node_cap):
    """Section 18: a root-local search from the ell=4 abandonment root for a
    preparation that reaches C = (1,4) with C zero-charge and R1 target
    != orbit 1.  Only ell=5 preparation edges (forced)."""
    root, aport = ell4_root()
    frontier = deque([(root, 0, 0, None, ())])
    seen = {(root.stable_key(), 0)}
    nodes = 0
    truncated = False
    completions = Counter()
    counterexamples = []
    while frontier:
        if node_cap is not None and nodes >= node_cap:
            truncated = True
            break
        st, d, rc, r1t, trace = frontier.popleft()
        nodes += 1
        if d >= depth:
            truncated = True
            continue
        for e in macro.macro_edges(st):
            if e.run.ell != 5:
                continue
            tr = e.joint
            if macro.area_a_prune_reason(tr.state, macro.AREA_A) is not None:
                continue
            k = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            if k == "other":
                continue
            s = sym(k)
            tq, tph = exact.ORBIT_PHASE[tr.target]
            nrc, nr1t = rc, r1t
            if s == "R":
                nrc = rc + 1
                if nrc == 1:
                    nr1t = tq
            if nrc > 1:
                continue                      # R1 only; R2 comes after C
            if core.hexagon_id(tr.target) == HUB:
                # this is the hub completer C
                completions[(s, nr1t)] += 1
                if s != "R" and nr1t is not None and nr1t != O_STAR:
                    counterexamples.append({
                        "C_label": f"rot^5;{tr.move.label}", "C_sym": s,
                        "C_target": [tq, tph], "R1_target_orbit": nr1t,
                        "trace": list(trace) + [f"rot^5;{tr.move.label}"],
                    })
                continue
            key = (tr.state.stable_key(), d + 1)
            if key in seen:
                continue
            seen.add(key)
            frontier.append((tr.state, d + 1, nrc, nr1t,
                             trace + (f"rot^5;{tr.move.label}",)))
    return {
        "depth_ceiling": depth, "node_cap": node_cap,
        "nodes_expanded": nodes, "frontier_emptied_naturally": not truncated,
        "completions_by_C_sym_and_R1_target": {f"{k[0]}|R1tgt={k[1]}": v
                                               for k, v in sorted(completions.items(), key=str)},
        "n_counterexamples": len(counterexamples),
        "counterexamples": counterexamples[:20],
        "status": ("exact counterexample" if counterexamples else
                   ("root-local exhaustive absence" if not truncated else "bounded incomplete")),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--witnesses", default=str(ROOT / "outputs" / "rr_six_counterexamples.json"))
    ap.add_argument("--preps", default=str(ROOT / "outputs" / "rr_preparation_words.json"))
    ap.add_argument("--depth", type=int, default=8)
    ap.add_argument("--node-cap", type=int, default=200000)
    ap.add_argument("--corpus", default=str(ROOT / "outputs" / "rr_ch2_witnesses.json"))
    ap.add_argument("--opener", default=str(ROOT / "outputs" / "rr_orbit1_opener_ledger.json"))
    a = ap.parse_args()

    op = abandonment_opens_orbit1()
    print("=== sections 16-17: who opens orbit 1? ===")
    print(f"   abandonment target = (orbit {op['abandonment_target'][0]}, "
          f"phase {op['abandonment_target'][1]}), new_orbit flag "
          f"{op['abandonment_new_orbit_flag']}")
    print(f"   orbit 1 mask before/after: {op['orbit1_mask_before_abandonment']} -> "
          f"{op['orbit1_mask_after_abandonment']}")
    print(f"   => opened by: {op['orbit1_opened_by']}")
    print(f"   {op['verdict']}")

    wits = json.loads(Path(a.witnesses).read_text(encoding="utf-8"))["witnesses"]
    preps = json.loads(Path(a.preps).read_text(encoding="utf-8"))
    corpus = ch2_corpus(wits, preps)
    print(f"\n=== section 12: CH2 corpus (C is zero-charge) ===")
    print(f"   cases: {len(corpus)}  "
          f"({sum(1 for r in corpus if r['source']=='long witness')} long, "
          f"{sum(1 for r in corpus if r['source']=='historical')} historical)")
    print("   src         P_core  C_label        C_tgt    R1_label       R1_tgt   dist")
    for r in corpus:
        print(f"   {r['source']:<11} {str(r['P_core']):>4}   {r['C_label']:<13} "
              f"{str(r['C_target']):<8} {str(r['R1_label']):<14} "
              f"{str(r['R1_target']):<8} {r['R1_to_C_macro_distance']}")
    r1_orbits = {tuple(r["R1_target"])[0] if r["R1_target"] else None for r in corpus}
    print(f"   distinct R1 target orbits in the CH2 corpus: {r1_orbits}")

    print(f"\n=== section 18: counterexample search (ell=4 root, ell=5 edges only) ===")
    res = counterexample_search(a.depth, a.node_cap)
    print(f"   depth ceiling {res['depth_ceiling']}, nodes {res['nodes_expanded']}, "
          f"frontier emptied naturally: {res['frontier_emptied_naturally']}")
    print(f"   completions by (C symbol | R1 target): "
          f"{res['completions_by_C_sym_and_R1_target']}")
    print(f"   counterexamples (C zero-charge, R1 target != orbit 1): "
          f"{res['n_counterexamples']}")
    print(f"   status: {res['status']}")

    Path(a.corpus).write_text(json.dumps({
        "schema": "rr-ch2-witnesses-v1",
        "definition": "the ell=4 same-component cases whose hub completer C is zero-charge",
        "n_cases": len(corpus),
        "distinct_R1_target_orbits": sorted(x for x in r1_orbits if x is not None),
        "counterexample_search": res,
        "cases": corpus,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    Path(a.opener).write_text(json.dumps({
        "schema": "rr-orbit1-opener-ledger-v1",
        "question": "which event first opens orbit 1 at ell=4?",
        "answer": op,
        "consequence": ("the proposed Lemma CH2-B is 반증됨; chaining cannot be derived "
                        "from a first-opener argument, and section 19's architecture must "
                        "be replaced"),
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.corpus)
    print("wrote", a.opener)


if __name__ == "__main__":
    main()
