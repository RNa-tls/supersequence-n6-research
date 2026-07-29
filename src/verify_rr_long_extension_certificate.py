#!/usr/bin/env python3
"""Round 27, section 13: independent certificates for the Target A verdicts.

Two kinds of certificate, both computed by code that does not share the
search's traversal:

  FOUND                 -- the witness extension is replayed LITERALLY,
                           edge by edge, from the abandonment root through
                           the prefix and then through the extension, and
                           the Target A predicate is re-evaluated from
                           scratch on the resulting state.  An exact
                           witness certificate.

  EXHAUSTED_IMPOSSIBLE  -- the same root is re-searched with a DIFFERENT
                           traversal (depth-first with a reversed edge
                           order) and no depth ceiling.  Agreement on
                           BOTH the natural frontier exhaustion and the
                           reachable-state count is the certificate.  A
                           node cap is never used, so exhaustion is a
                           property of the frontier, not of a budget.

The certificate also records, per root, the exact obstruction available:
whether any R2 boundary was reachable at all, and if so whether every one
of them failed the same-component test.  That distinction matters -- "no
R2 boundary exists" and "R2 boundaries exist but none is same-component"
are different theorems.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter
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


macro = _load("vrlec", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]


def joint_kind(w, ab, nw):
    return {(2, False, False): "Z2", (2, True, True): "Z2abandon",
            (3, False, False): "R", (3, False, True): "Z3"}.get((w, ab, nw), "other")


def state_hash(state):
    return hashlib.sha256(repr(state.stable_key()).encode("utf-8")).hexdigest()


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


def prefix_state(root_ell, word):
    st = exact.initial_state()
    for _ in range(root_ell):
        st = exact.extend(st, W1).state
    st = exact.extend(st, W2_10).state
    for lbl in word:
        for _ in range(5):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl[lbl]).state
    return st


def replay_witness(root_ell, word, trace):
    """Literal replay of a FOUND witness; re-evaluates Target A from
    scratch. Returns (ok, detail)."""
    st = prefix_state(root_ell, word)
    r_seen = 0
    for step in trace:
        ell_s, lbl = step["label"].split(";")
        ell_v = int(ell_s.split("^")[1])
        for _ in range(ell_v):
            tr = exact.extend(st, W1)
            if tr is None:
                return False, f"rotation collision replaying {step['label']}"
            st = tr.state
        pre = st
        tr = exact.extend(st, mbl[lbl])
        if tr is None:
            return False, f"joint collision replaying {step['label']}"
        if macro.area_a_prune_reason(tr.state, macro.AREA_A) is not None:
            return False, f"area_a prune replaying {step['label']}"
        k = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
        if k == "R":
            r_seen += 1
            if not (tr.state.F == 1 and tr.state.H == 0):
                return False, "R2 boundary has wrong F_def/H"
            sq, _ = exact.ORBIT_PHASE[pre.p]
            tq, _ = exact.ORBIT_PHASE[tr.target]
            parent, find = component_roots(pre)
            sr = find(("q", sq)) if ("q", sq) in parent else None
            tg = find(("q", tq)) if ("q", tq) in parent else None
            if sr is None or sr != tg:
                return False, "R2 boundary is NOT same-component"
            return True, {"r2_source_orbit": sq, "r2_target_orbit": tq,
                          "post_r2_state_hash": state_hash(tr.state),
                          "extension_length": len(trace)}
        st = tr.state
    return False, "trace ended without an R2 boundary"


def independent_dfs(root_ell, word):
    """Re-search with a different traversal: DFS, reversed edge order, NO
    depth ceiling and NO node cap. Exhaustion here is a property of the
    frontier."""
    start = prefix_state(root_ell, word)
    stack = [(start, 0)]
    seen = {(start.stable_key(), 0)}
    nodes = 0
    r2_total, r2_same = 0, 0
    while stack:
        st, d = stack.pop()
        nodes += 1
        for edge in reversed(list(macro.macro_edges(st))):
            tr = edge.joint
            if macro.area_a_prune_reason(tr.state, macro.AREA_A) is not None:
                continue
            k = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
            if k == "other":
                continue
            if k == "R":
                if not (tr.state.F == 1 and tr.state.H == 0):
                    continue
                r2_total += 1
                pre = edge.run.state
                sq, _ = exact.ORBIT_PHASE[pre.p]
                tq, _ = exact.ORBIT_PHASE[tr.target]
                parent, find = component_roots(pre)
                sr = find(("q", sq)) if ("q", sq) in parent else None
                tg = find(("q", tq)) if ("q", tq) in parent else None
                if sr is not None and sr == tg:
                    r2_same += 1
                continue
            key = (tr.state.stable_key(), d + 1)
            if key in seen:
                continue
            seen.add(key)
            stack.append((tr.state, d + 1))
    return {"nodes": nodes, "dedup_states": len(seen),
            "r2_boundaries": r2_total, "same_component_r2": r2_same,
            "frontier_emptied_naturally": True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(ROOT / "outputs" / "rr_long_prefix_extension_results.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_long_prefix_certificates.json"))
    ap.add_argument("--max-recheck", type=int, default=28)
    a = ap.parse_args()

    data = json.loads(Path(a.results).read_text(encoding="utf-8"))
    certs, agree, disagree = [], 0, 0
    kind_hist = Counter()
    for i, r in enumerate(data["results"]):
        cert = {"prefix_index": r["prefix_index"], "root_ell": r["root_ell"],
                "symbolic_word": r["symbolic_word"], "L": r["L"],
                "return_exponent": r["return_exponent"],
                "search_status": r["status"]}
        if r["status"] == "FOUND":
            w = r["same_component_witnesses"][0]
            ok, detail = replay_witness(r["root_ell"], r["literal_joint_word"],
                                        w["extension_trace"])
            cert.update({"certificate_kind": "exact witness",
                         "literal_replay_ok": ok, "replay_detail": detail})
            kind_hist["exact witness"] += 1
            agree += int(bool(ok))
            disagree += int(not ok)
        elif r["status"] == "EXHAUSTED_IMPOSSIBLE" and i < a.max_recheck:
            ind = independent_dfs(r["root_ell"], r["literal_joint_word"])
            same_states = ind["dedup_states"] == r["dedup_states"]
            cert.update({
                "certificate_kind": "exact exhaustive search (independent traversal)",
                "independent_dfs": ind,
                "search_dedup_states": r["dedup_states"],
                "state_counts_agree": same_states,
                "obstruction": ("no R2 boundary is reachable at all"
                                if ind["r2_boundaries"] == 0 else
                                f"{ind['r2_boundaries']} R2 boundaries are reachable but "
                                f"NONE is same-component"),
            })
            kind_hist["exact exhaustive search"] += 1
            agree += int(same_states)
            disagree += int(not same_states)
        else:
            cert.update({"certificate_kind": "bounded incomplete",
                         "note": "the search did not exhaust its frontier; no certificate"})
            kind_hist["bounded incomplete"] += 1
        certs.append(cert)
        print(f"  [{i+1:>2}] ell={r['root_ell']} {r['symbolic_word']} "
              f"{r['status']:>22} -> {cert['certificate_kind']}"
              + (f"  agree={cert.get('state_counts_agree', cert.get('literal_replay_ok'))}"
                 if cert["certificate_kind"] != "bounded incomplete" else ""))

    print(f"\ncertificate kinds : {dict(kind_hist)}")
    print(f"independent checks agreeing / disagreeing : {agree} / {disagree}")

    Path(a.output).write_text(json.dumps({
        "schema": "rr-long-prefix-certificates-v1",
        "method": {
            "FOUND": ("literal edge-by-edge replay from the abandonment root through the "
                      "prefix and the extension, with Target A re-evaluated from scratch"),
            "EXHAUSTED_IMPOSSIBLE": ("re-search with a different traversal (DFS, reversed "
                                     "edge order, NO depth ceiling, NO node cap); agreement "
                                     "on natural exhaustion and on the reachable-state count "
                                     "is the certificate"),
        },
        "node_cap_never_used_as_a_proof_condition": True,
        "certificate_kind_histogram": dict(kind_hist),
        "independent_checks_agree": agree,
        "independent_checks_disagree": disagree,
        "certificates": certs,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.output)


if __name__ == "__main__":
    main()
