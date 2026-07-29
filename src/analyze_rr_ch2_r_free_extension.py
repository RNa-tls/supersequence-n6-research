#!/usr/bin/env python3
"""Round 31, Part D: does the R-free-to-C prefix extend to a Target A
boundary, and does it break chaining?

Round 30 found a legal ell=4 preparation that reaches the hub completer
C = rot^5;w2:10 with ZERO R events before C -- the walk climbs orbit 1
from the abandonment's (1,0) to (1,4) by pure E steps.  That is exactly
what blocks the CH2 chaining argument, so this file pins it down.

Hand classification first (section 18).  If #R_{<=C} = 0 then BOTH R
events must sit after C.  After C the walk stands on hex0 position 5, a
rotation is impossible (position 0 is visited from the initial state), so
the next macro-edge has ell = 0; at that endpoint the unique R joint is
w3:120.  Two cases follow, and both are searched exactly below:

  (i)  the ell=0 edge is w3:120 -- then it is R1, Phi drops 5 -> 0, and
       every later macro-edge is forced to ell=5; R2 must come later.
  (ii) the ell=0 edge is one of the three non-R joints -- then R1 comes
       later still, again at Phi = 0.

The search reports FOUND_COUNTEREXAMPLE / EXHAUSTED_NO_COUNTEREXAMPLE /
INCOMPLETE and never reads a node cap as absence.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter, deque
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"


def _load(n, f):
    p = WORK / f
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s)
    sys.modules[n] = m
    s.loader.exec_module(m)
    return m


macro = _load("arcrfe", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
HUB = core.hexagon_id(exact.initial_state().p)
O_STAR = 1


def phi(s):
    return 5 + 6 * (exact.TARGET_P - s.P) - (720 - s.visited_count)


def joint_kind(w, ab, nw):
    return {(2, False, False): "Z2", (2, True, True): "Z2abandon",
            (3, False, False): "R", (3, False, True): "Z3"}.get((w, ab, nw), "other")


def sym(k):
    return "R" if k == "R" else ("F" if k == "Z3" else "E")


def component_roots(state):
    parent: Dict[Any, Any] = {}

    def find(n):
        parent.setdefault(n, n)
        if parent[n] != n:
            parent[n] = find(parent[n])
        return parent[n]

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for q, mask in enumerate(state.orbit_masks):
        for ph in range(5):
            if mask & (1 << ph):
                union(("q", q), ("h", core.hexagon_id(core.ports_of_e_orbit(core.E_REPS[q])[ph])))
    return parent, find


def root4():
    st = exact.initial_state()
    for _ in range(4):
        st = exact.extend(st, W1).state
    return exact.extend(st, W2_10).state


def find_r_free_prefixes(depth, node_cap):
    """Section 16: every legal ell=5 preparation reaching C with no R."""
    root = root4()
    out = []
    fr = deque([(root, 0, ())])
    seen = {(root.stable_key(), 0)}
    nodes, trunc = 0, False
    while fr:
        if node_cap and nodes >= node_cap:
            trunc = True
            break
        st, d, tr_ = fr.popleft()
        nodes += 1
        if d >= depth:
            trunc = True
            continue
        for e in macro.macro_edges(st):
            if e.run.ell != 5:
                continue
            t = e.joint
            if macro.area_a_prune_reason(t.state, macro.AREA_A) is not None:
                continue
            k = joint_kind(t.move.weight, t.abandonment, t.new_orbit)
            if k == "other" or k == "R":
                continue                     # R-free prefixes only
            lab = f"rot^5;{t.move.label}"
            if core.hexagon_id(t.target) == HUB:
                tq, tph = exact.ORBIT_PHASE[t.target]
                out.append({"literal_word": list(tr_) + [lab],
                            "C_label": lab, "C_sym": sym(k),
                            "C_target": [tq, tph],
                            "P_core": d,
                            "post_C_state": t.state})
                continue
            key = (t.state.stable_key(), d + 1)
            if key in seen:
                continue
            seen.add(key)
            fr.append((t.state, d + 1, tr_ + (lab,)))
    return out, {"nodes": nodes, "truncated": trunc, "depth_ceiling": depth}


def post_c_hand_classification(st):
    """Section 18: what can happen on the ell=0 edge right after C."""
    rot = exact.extend(st, W1)
    rows = []
    for lbl in ["w2:10", "w3:120", "w3:201", "w3:210"]:
        t = exact.extend(st, mbl[lbl])
        if t is None:
            rows.append({"joint": lbl, "legal": False, "reason": "target visited"})
            continue
        reason = macro.area_a_prune_reason(t.state, macro.AREA_A)
        k = joint_kind(t.move.weight, t.abandonment, t.new_orbit)
        tq, tph = exact.ORBIT_PHASE[t.target]
        rows.append({"joint": lbl, "legal": reason is None, "prune": reason,
                     "kind": k, "is_R": k == "R", "target_orbit": tq,
                     "target_phase": tph, "phi_after": phi(t.state)})
    return {"rotation_possible": rot is not None, "phi_at_C": phi(st), "joints": rows}


def extension_search(st, depth, node_cap):
    """Sections 19-20: from the post-C state, find any Target A boundary
    (second R, F_def=1, H=0, same-component) and record chaining."""
    fr = deque([(st, 0, 0, None, ())])
    seen = {(st.stable_key(), 0)}
    nodes, trunc = 0, False
    boundaries, counterexamples = [], []
    reasons = Counter()
    while fr:
        if node_cap and nodes >= node_cap:
            trunc = True
            break
        cur, d, rc, r1t, tr_ = fr.popleft()
        nodes += 1
        if d >= depth:
            trunc = True
            continue
        for e in macro.macro_edges(cur):
            t = e.joint
            if macro.area_a_prune_reason(t.state, macro.AREA_A) is not None:
                reasons["area_a"] += 1
                continue
            k = joint_kind(t.move.weight, t.abandonment, t.new_orbit)
            if k == "other":
                continue
            pre = e.run.state
            sq, sph = exact.ORBIT_PHASE[pre.p]
            tq, tph = exact.ORBIT_PHASE[t.target]
            lab = f"rot^{e.run.ell};{t.move.label}"
            nrc, nr1t = rc, r1t
            if k == "R":
                nrc = rc + 1
                if nrc == 1:
                    nr1t = tq
                elif nrc == 2:
                    if not (t.state.F == 1 and t.state.H == 0):
                        reasons["r2_F_or_H_wrong"] += 1
                        continue
                    parent, find = component_roots(pre)
                    sr = find(("q", sq)) if ("q", sq) in parent else None
                    tg = find(("q", tq)) if ("q", tq) in parent else None
                    if sr is not None and sr == tg:
                        rec = {"trace": list(tr_) + [lab], "extension_length": d + 1,
                               "r1_target_orbit": nr1t, "r2_source_orbit": sq,
                               "r2_target_orbit": tq, "chaining": nr1t == sq}
                        boundaries.append(rec)
                        if not rec["chaining"]:
                            counterexamples.append(rec)
                    else:
                        reasons["r2_not_same_component"] += 1
                    continue
                else:
                    reasons["third_R"] += 1
                    continue
            key = (t.state.stable_key(), d + 1)
            if key in seen:
                continue
            seen.add(key)
            fr.append((t.state, d + 1, nrc, nr1t, tr_ + (lab,)))
    if counterexamples:
        status = "FOUND_COUNTEREXAMPLE"
    elif trunc:
        status = "INCOMPLETE"
    else:
        status = "EXHAUSTED_NO_COUNTEREXAMPLE"
    return {"status": status, "nodes": nodes, "truncated": trunc,
            "depth_ceiling": depth,
            "n_target_A_boundaries": len(boundaries),
            "n_chaining": sum(1 for b in boundaries if b["chaining"]),
            "n_non_chaining": len(counterexamples),
            "boundaries": boundaries[:20], "counterexamples": counterexamples[:20],
            "prune_reasons": dict(reasons)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix-depth", type=int, default=8)
    ap.add_argument("--ext-depth", type=int, default=6)
    ap.add_argument("--node-cap", type=int, default=150000)
    ap.add_argument("--out-prefix", default=str(ROOT / "outputs" / "rr_ch2_r_free_prefix.json"))
    ap.add_argument("--out-ext", default=str(ROOT / "outputs" / "rr_ch2_extension_results.json"))
    a = ap.parse_args()

    print("=== section 16: R-free-to-C prefixes ===")
    pref, meta = find_r_free_prefixes(a.prefix_depth, a.node_cap)
    print(f"   depth ceiling {meta['depth_ceiling']}, nodes {meta['nodes']}, "
          f"truncated {meta['truncated']}")
    print(f"   R-free prefixes reaching C: {len(pref)}")
    recs = []
    for p in pref:
        st = p["post_C_state"]
        recs.append({
            "root_ell": 4, "literal_word": p["literal_word"], "P_core": p["P_core"],
            "C_label": p["C_label"], "C_sym": p["C_sym"], "C_target": p["C_target"],
            "R_count_before_C": 0,
            "post_C_phi": phi(st), "post_C_F_def": st.F, "post_C_N": st.Ndef,
            "post_C_H": st.H, "post_C_O": st.O, "post_C_P": st.P,
            "post_C_visited": st.visited_count,
            "post_C_state_hash": hashlib.sha256(repr(st.stable_key()).encode()).hexdigest()[:16],
        })
        print(f"      P_core={p['P_core']} word={p['literal_word']}")
        print(f"        C target {p['C_target']}, post-C Phi {phi(st)}, "
              f"O {st.O}, P {st.P}")

    if not pref:
        print("   none found in this scope -- nothing to extend")
        Path(a.out_prefix).write_text(json.dumps({"schema": "rr-ch2-r-free-prefix-v1",
                                                  "n_prefixes": 0, "search": meta},
                                                 indent=2, ensure_ascii=False), encoding="utf-8")
        return

    print("\n=== section 18: hand classification of the ell=0 edge after C ===")
    hc = post_c_hand_classification(pref[0]["post_C_state"])
    print(f"   rotation possible after C: {hc['rotation_possible']}  "
          f"(so ell = 0 is forced)")
    print(f"   Phi at C: {hc['phi_at_C']}")
    for r in hc["joints"]:
        print(f"      {r['joint']:<8} legal={r.get('legal')} kind={r.get('kind')} "
              f"R={r.get('is_R')} tgt_orbit={r.get('target_orbit')} "
              f"phi_after={r.get('phi_after')}")

    print("\n=== sections 19-20: extension search to a Target A boundary ===")
    results = []
    for i, p in enumerate(pref):
        res = extension_search(p["post_C_state"], a.ext_depth, a.node_cap)
        res["prefix_index"] = i
        res["prefix_word"] = p["literal_word"]
        results.append(res)
        print(f"   prefix {i}: {res['status']}  nodes={res['nodes']} "
              f"boundaries={res['n_target_A_boundaries']} "
              f"chaining={res['n_chaining']} non-chaining={res['n_non_chaining']}")
        for b in res["boundaries"][:3]:
            print(f"      R1 tgt {b['r1_target_orbit']}, R2 src {b['r2_source_orbit']}, "
                  f"chaining {b['chaining']}, ext len {b['extension_length']}")

    Path(a.out_prefix).write_text(json.dumps({
        "schema": "rr-ch2-r-free-prefix-v1",
        "search": meta, "n_prefixes": len(recs),
        "post_c_hand_classification": hc,
        "prefixes": recs,
        "grade": "exact observation (the prefixes) + 손증명 (the ell=0 forcing)",
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    Path(a.out_ext).write_text(json.dumps({
        "schema": "rr-ch2-extension-results-v1",
        "target": ("a Target A boundary reached from an R-free-to-C prefix: exactly two R "
                   "events after C, F_def=1, H=0, same-component; chaining recorded"),
        "coverage_scope": (f"root-local from the ell=4 abandonment root; preparation depth "
                           f"ceiling {a.prefix_depth} for the prefix, extension depth "
                           f"ceiling {a.ext_depth}, node cap {a.node_cap}"),
        "node_cap_is_not_absence": True,
        "results": results,
        "overall_status": ("FOUND_COUNTEREXAMPLE" if any(
            r["status"] == "FOUND_COUNTEREXAMPLE" for r in results) else
            ("EXHAUSTED_NO_COUNTEREXAMPLE" if all(
                r["status"] == "EXHAUSTED_NO_COUNTEREXAMPLE" for r in results)
             else "INCOMPLETE")),
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.out_prefix)
    print("wrote", a.out_ext)


if __name__ == "__main__":
    main()
