#!/usr/bin/env python3
"""Round 27, sections 1, 2, 8: the long-excursion prefix corpus and its
exact state quotient.

TERMINOLOGY (section 8) -- two different things have been called "F" and
conflating them would silently break every budget argument:

  * F_def   = ExactState.F, the DEFECT/abandonment counter.  TARGET_F = 1.
              An RR word has exactly one abandonment, so F_def = 1 from
              the abandonment joint onward and any further abandonment is
              pruned F_exceeded.
  * F_sym   = the fresh-orbit-opening EVENT symbol (a Z3 joint, i.e.
              tr.new_orbit is True).  It is NOT bounded by TARGET_F; it is
              bounded only through O <= TARGET_O = 25.

Round 26 wrote "#F=4" for the minimal counterexample.  That is F_sym = 4,
NOT a violation of F_def <= 1.  Every field in this corpus is named
f_def_* or f_sym_* so the two can never be compared by accident.

The corpus is the odd-exponent first-return prefixes of length 7 and 8
that replay legally through the engine (Round 26 found 38 such WORDS,
realizable from at least one abandonment root).  A prefix here is a
(word, root ell) PAIR -- the unit that actually has a state -- and both
counts are reported, because they are different numbers and the round's
brief quotes the word count.

No completion search here: this file only builds roots.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter, defaultdict
from itertools import product
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


macro = _load("brler", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
JOINTS = ["w2:10", "w3:120", "w3:201", "w3:210"]
HEX0 = [0, 120, 33, 9, 3, 1]
HUB = core.hexagon_id(exact.initial_state().p)


def joint_kind(w, ab, nw):
    return {(2, False, False): "Z2", (2, True, True): "Z2abandon",
            (3, False, False): "R", (3, False, True): "Z3"}.get((w, ab, nw), "other")


def sym(k):
    return "R" if k == "R" else ("F" if k == "Z3" else "E")


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


def root_state(ell):
    c = exact.initial_state()
    for _ in range(ell):
        c = exact.extend(c, W1).state
    return exact.extend(c, W2_10).state


def aport(ell):
    c = exact.initial_state()
    for _ in range(ell):
        c = exact.extend(c, W1).state
    return exact.extend(c, W2_10).target


def odd_first_return_words(lengths):
    S5 = core.power(core.SIGMA, 5)
    epow = {core.power(core.E, i): i for i in range(5)}
    gens = {j: core.compose(S5, mbl[j].action) for j in JOINTS}
    idn = tuple(range(core.N))
    out = []
    for n in lengths:
        for combo in product(JOINTS, repeat=n):
            u, ok = idn, True
            for i, name in enumerate(combo):
                u = core.compose(u, gens[name])
                if u in epow and i < n - 1:
                    ok = False
                    break
            if not ok or u not in epow:
                continue
            if epow[u] % 2 == 1:
                out.append({"word": list(combo), "L": n, "exponent": epow[u]})
    return out


def replay_prefix(word, ell):
    """Replay as ell=5 macro edges; returns the full record or None with a
    failure reason."""
    o = HEX0[ell + 1]
    st = root_state(ell)
    q_phase = exact.ORBIT_PHASE[aport(ell)][1]
    syms, kinds, events = [], [], []
    r_count, f_sym, zero_charge = 0, 0, 0
    r1_target_orbit = None
    hub_touched = 0
    for i, lbl in enumerate(word):
        cur = st
        for _ in range(5):
            tr = exact.extend(cur, W1)
            if tr is None:
                return None, f"rotation collision at step {i}"
            cur = tr.state
        tr = exact.extend(cur, mbl[lbl])
        if tr is None:
            return None, f"joint target already visited at step {i}"
        reason = macro.area_a_prune_reason(tr.state, macro.AREA_A)
        if reason is not None:
            return None, f"area_a prune at step {i}: {reason}"
        k = joint_kind(tr.move.weight, tr.abandonment, tr.new_orbit)
        if k == "other":
            return None, f"joint outside the model at step {i}"
        s = sym(k)
        tq, tph = exact.ORBIT_PHASE[tr.target]
        thex = core.hexagon_id(tr.target)
        if tq == o and i < len(word) - 1:
            return None, f"returned to O* early at step {i}"
        if s == "R":
            r_count += 1
            if r_count == 1:
                r1_target_orbit = tq
        if tr.new_orbit:
            f_sym += 1
        if s != "R":
            zero_charge += 1
        if thex == HUB:
            hub_touched += 1
        syms.append(s)
        kinds.append(k)
        events.append({"index": i, "joint": lbl, "sym": s, "kind": k,
                       "target_orbit": tq, "target_phase": tph, "target_hexagon": thex,
                       "new_orbit": bool(tr.new_orbit)})
        st = tr.state
    tq_final, tph_final = exact.ORBIT_PHASE[st.p]
    parent, find = component_roots(st)
    comp_root = find(("q", o)) if ("q", o) in parent else None
    n_components = len({find(x) for x in list(parent)})
    rec = {
        "root_ell": ell, "o_star": o,
        "literal_joint_word": list(word), "L": len(word), "G": len(word) - 1,
        "symbolic_word": "".join(syms), "kinds": kinds,
        "return_exponent": (tph_final - q_phase) % 5,
        "r_count": r_count, "r1_target_orbit": r1_target_orbit,
        "f_sym_count": f_sym, "zero_charge_count": zero_charge,
        "hub_touches": hub_touched,
        "post_return_state_hash": state_hash(st),
        "post_return_stable_key": repr(st.stable_key()),
        "visited_mask_hash": hashlib.sha256(
            repr(tuple(st.orbit_masks)).encode("utf-8")).hexdigest()[:32],
        "endpoint_permutation": list(st.p),
        "endpoint_orbit": tq_final, "endpoint_phase": tph_final,
        "o_star_phase_of_endpoint": tph_final if tq_final == o else None,
        "f_def": st.F, "N_def": st.Ndef, "H": st.H, "P": st.P, "S": st.S,
        "O": st.O, "D": st.D, "visited_count": st.visited_count,
        "phi": 5 + 6 * (exact.TARGET_P - st.P) - (720 - st.visited_count),
        "component_root_of_O_star": str(comp_root),
        "n_components": n_components,
        "remaining_R_budget": 2 - r_count,
        "events": events,
    }
    return rec, None


def canonical_pair_key(state, o_star, r1t):
    """Section 2: canonicalize the (state, decoration) PAIR -- transporting
    the distinguished O* and the R1 target orbit through every tied alpha,
    as in enumerate_rr_canonical_local.py."""
    best_key, alphas = None, []
    for alpha in range(len(core.ALL_WORDS)):
        key = exact.relabel_sparse_key(state, alpha)
        if best_key is None or key < best_key:
            best_key, alphas = key, [alpha]
        elif key == best_key:
            alphas.append(alpha)
    variants = [(exact.LEFT_ORBIT_ACTION[a][o_star][0],
                 None if r1t is None else exact.LEFT_ORBIT_ACTION[a][r1t][0])
                for a in alphas]
    return (repr(best_key), min(variants)), len(alphas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lengths", default="7,8")
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_long_excursion_prefixes.json"))
    ap.add_argument("--quotient", default=str(ROOT / "outputs" / "rr_long_prefix_quotient.json"))
    a = ap.parse_args()
    lengths = [int(x) for x in a.lengths.split(",")]

    words = odd_first_return_words(lengths)
    print(f"odd-exponent group first-return words of length {lengths}: {len(words)}")

    prefixes, failures = [], Counter()
    legal_words = set()
    for w in words:
        for ell in range(5):
            rec, why = replay_prefix(w["word"], ell)
            if rec is None:
                failures[why.split(":")[0]] += 1
                continue
            prefixes.append(rec)
            legal_words.add(tuple(w["word"]))

    print(f"legal (word, root ell) PREFIXES : {len(prefixes)}")
    print(f"distinct legal WORDS            : {len(legal_words)}  "
          f"(Round 26's '38' counts words, not prefixes)")
    print(f"replay failures by reason       : {dict(failures)}")

    by_L = Counter(p["L"] for p in prefixes)
    by_R = Counter(p["r_count"] for p in prefixes)
    by_Fsym = Counter(p["f_sym_count"] for p in prefixes)
    by_Fdef = Counter(p["f_def"] for p in prefixes)
    print(f"\nby L        : {dict(sorted(by_L.items()))}")
    print(f"by R count  : {dict(sorted(by_R.items()))}   (RR budget 2)")
    print(f"by F_sym    : {dict(sorted(by_Fsym.items()))}   (fresh openings -- NOT the defect budget)")
    print(f"by F_def    : {dict(sorted(by_Fdef.items()))}   (defect counter, TARGET_F=1)")
    assert set(by_Fdef) == {1}, "every prefix must carry exactly one abandonment"
    print("   F_def == 1 for every prefix: the abandonment budget is intact. 손증명 check passed.")

    # ---- section 2: quotient ----
    exact_states = defaultdict(list)
    for i, p in enumerate(prefixes):
        exact_states[p["post_return_stable_key"]].append(i)
    canon = defaultdict(list)
    stab = Counter()
    for i, p in enumerate(prefixes):
        st = replay_state(p)
        key, nties = canonical_pair_key(st, p["o_star"], p["r1_target_orbit"])
        stab[nties] += 1
        canon[repr(key)].append(i)
    resource = defaultdict(list)
    for i, p in enumerate(prefixes):
        resource[(p["r_count"], p["f_sym_count"], p["O"], p["P"], p["visited_count"])].append(i)

    print(f"\n=== quotient ===")
    print(f"literal prefixes                : {len(prefixes)}")
    print(f"distinct EXACT states           : {len(exact_states)}")
    print(f"distinct left-S6 canonical pairs: {len(canon)}")
    print(f"distinct resource signatures    : {len(resource)}")
    print(f"stabilizer tie histogram        : {dict(sorted(stab.items()))}")

    # ---- section 4 (ledger obstruction, hand proof): the R budget ----
    usable = [i for i, p in enumerate(prefixes) if p["remaining_R_budget"] >= 1]
    print(f"\n=== ledger obstruction: the RR R budget (손증명) ===")
    print(f"an RR word has EXACTLY two R events, and R2 is the last event of the word,")
    print(f"so a preparation prefix strictly before R2 may contain at most ONE R.")
    print(f"prefixes with r_count >= 2 (immediately impossible) : {len(prefixes)-len(usable)}")
    print(f"prefixes surviving to Target A search               : {len(usable)}")
    print(f"   their L values : {dict(sorted(Counter(prefixes[i]['L'] for i in usable).items()))}")
    print(f"   their exponents: {dict(sorted(Counter(prefixes[i]['return_exponent'] for i in usable).items()))}")
    print(f"   their F_sym    : {dict(sorted(Counter(prefixes[i]['f_sym_count'] for i in usable).items()))}")

    Path(a.output).write_text(json.dumps({
        "schema": "rr-long-excursion-prefixes-v1",
        "terminology": {
            "F_def": "ExactState.F, the defect/abandonment counter; TARGET_F=1",
            "F_sym": "fresh-orbit-opening event symbol (Z3, tr.new_orbit); bounded only via O<=TARGET_O",
            "warning": ("Round 26's '#F=4' is F_sym=4 and is NOT a violation of F_def<=1; "
                        "the two are different quantities and are never compared here"),
        },
        "counting_note": ("Round 26's '38' counts WORDS legal from at least one root; a "
                          "prefix is a (word, root ell) pair, which is the unit that has a "
                          "state. Both counts are reported."),
        "distinct_legal_words": len(legal_words),
        "legal_prefix_count": len(prefixes),
        "replay_failures_by_reason": dict(failures),
        "by_L": {str(k): v for k, v in sorted(by_L.items())},
        "by_r_count": {str(k): v for k, v in sorted(by_R.items())},
        "by_f_sym": {str(k): v for k, v in sorted(by_Fsym.items())},
        "by_f_def": {str(k): v for k, v in sorted(by_Fdef.items())},
        "grade": "exact replay",
        "r_budget_obstruction": {
            "statement": ("an RR word has exactly two R events and R2 is the last event "
                          "of the word, so any preparation prefix lying strictly before "
                          "R2 contains at most one R"),
            "grade": "손증명",
            "immediately_impossible_prefixes": len(prefixes) - len(usable),
            "surviving_prefixes": len(usable),
            "surviving_indices": usable,
        },
        "prefixes": prefixes,
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.output)

    Path(a.quotient).write_text(json.dumps({
        "schema": "rr-long-prefix-quotient-v1",
        "literal_prefixes": len(prefixes),
        "distinct_exact_states": len(exact_states),
        "distinct_left_s6_canonical_pairs": len(canon),
        "distinct_resource_signatures": len(resource),
        "canonicalization": ("the (state, decoration) PAIR is canonicalized: the "
                             "distinguished O* and the R1 target orbit are transported "
                             "through every tied alpha via LEFT_ORBIT_ACTION and the "
                             "lexicographic minimum is taken"),
        "exact_state_classes": {k: v for k, v in list(exact_states.items())},
        "canonical_classes": {k: v for k, v in canon.items()},
        "resource_classes": {str(k): v for k, v in resource.items()},
        "grade": "exact replay + exact canonicalization",
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.quotient)


def replay_state(p):
    st = root_state(p["root_ell"])
    for lbl in p["literal_joint_word"]:
        for _ in range(5):
            st = exact.extend(st, W1).state
        st = exact.extend(st, mbl[lbl]).state
    return st


if __name__ == "__main__":
    main()
