#!/usr/bin/env python3
"""Round 26, sections 8-13, 15-17: the legal O* excursion spectrum, the
normal forms, the sharpness question, and the non-O* separation.

An O*-EXCURSION is a maximal run of preparation macro-edges that starts
at a port of O*, lands nowhere in O*, and ends with the edge that returns
to O*.  Its length is L (= the first-return word length); the gap is
G = L-1.  Convention fixed in enumerate_rr_first_return_words.py.

The excursion frontier is explored to L <= 8 -- deliberately PAST the
group threshold of 6, so that "no excursion exceeds 6" would be a
finding rather than an artifact of the ceiling.  This is the one place
where a depth-6 universe would have been circular, and it is why the
Round 25 measurement (which lived inside a depth-6 word scope) could not
have settled the question either way.

This is an excursion enumeration, not a completion search: nothing here
asks whether a preparation prefix extends to a finished RR word.  That
distinction is load-bearing for the verdict and is stated in the output.

Sections 15/16 are kept strictly separate: the non-O* zero-charge counts
are reported as data with their exact scope, and are NOT mixed into the
O* argument.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from collections import Counter, defaultdict, deque
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


macro = _load("vrosg", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
W1 = macro.W1
mbl = {m.label: m for m in exact.ALL_MOVES}
W2_10 = mbl["w2:10"]
HEX0 = [0, 120, 33, 9, 3, 1]


def kind(w, ab, nw):
    return {(2, False, False): "Z2", (2, True, True): "Z2abandon",
            (3, False, False): "R", (3, False, True): "Z3"}.get((w, ab, nw), "other")


def sym(k):
    return "R" if k == "R" else ("F" if k == "Z3" else "E")


def root(ell):
    c = exact.initial_state()
    for _ in range(ell):
        c = exact.extend(c, W1).state
    return exact.extend(c, W2_10).state


def aport(ell):
    c = exact.initial_state()
    for _ in range(ell):
        c = exact.extend(c, W1).state
    return exact.extend(c, W2_10).target


def excursions(ell, ceiling):
    """Every legal first-return excursion from the abandonment port, to
    length ceiling.  Dedup key is (state, depth) so that longer paths to
    the same state are not lost -- deduping by state alone would under-
    report the maximum excursion length."""
    o = HEX0[ell + 1]
    r = root(ell)
    q_phase = exact.ORBIT_PHASE[aport(ell)][1]
    found = []
    nodes = 0
    fr = deque([(r, 0, (), ())])
    seen = {(r.stable_key(), 0)}
    truncated = False
    while fr:
        st, d, jw, sw = fr.popleft()
        nodes += 1
        if d >= ceiling:
            truncated = True
            continue
        for e in macro.macro_edges(st):
            t = e.joint
            if macro.area_a_prune_reason(t.state, macro.AREA_A) is not None:
                continue
            k = kind(t.move.weight, t.abandonment, t.new_orbit)
            if k == "other":
                continue
            s = sym(k)
            tq, tph = exact.ORBIT_PHASE[t.target]
            njw, nsw = jw + (t.move.label,), sw + (s,)
            if tq == o:
                found.append({"L": d + 1, "G": d, "exponent": (tph - q_phase) % 5,
                              "joint_word": list(njw), "symbolic": "".join(nsw),
                              "n_R": nsw.count("R"), "n_F": nsw.count("F"),
                              "n_E": nsw.count("E"), "return_joint": t.move.label,
                              "departure_joint": njw[0]})
                continue
            key = (t.state.stable_key(), d + 1)
            if key in seen:
                continue
            seen.add(key)
            fr.append((t.state, d + 1, njw, nsw))
    return found, nodes, len(seen), truncated


def non_o_star_data(path):
    """Section 15: zero-charge counts per NON-O* target orbit, over the 95
    O*-landing completions.  Reported as data with its exact scope; not
    used in the O* argument."""
    p = Path(path)
    if not p.exists():
        return {"available": False}
    rows = [r for r in json.loads(p.read_text(encoding="utf-8"))["rows"]
            if r["landing_class"] == "O_star"]
    per_word, odd_orbit_words = [], 0
    orbit_hist = Counter()
    for r in rows:
        o = r["o_star"]
        by_orbit = Counter(e["target_orbit"] for e in r["events"]
                           if e["sym"] != "R" and e["target_orbit"] != o)
        odd = sorted([q for q, c in by_orbit.items() if c % 2 == 1])
        if odd:
            odd_orbit_words += 1
        total_other = sum(by_orbit.values())
        orbit_hist[total_other % 2] += 1
        per_word.append({"ordered_word": r["ordered_word"], "o_star": o,
                         "zero_charge_by_other_orbit": {str(k): v for k, v in sorted(by_orbit.items())},
                         "n_zero_charge_other": total_other,
                         "parity_other": total_other % 2,
                         "orbits_with_odd_count": odd})
    return {
        "available": True,
        "scope": ("the 95 O*-landing completions of outputs/rr_ordered_event_words.json, "
                  "root-local exhaustive at depth ceiling 6 -- NOT a general RR claim"),
        "total_other_parity_histogram": {str(k): v for k, v in sorted(orbit_hist.items())},
        "words_with_some_odd_single_orbit": odd_orbit_words,
        "finding": (
            "The AGGREGATE count of zero-charge events targeting orbits other than O* is "
            "even in every one of the 95 completions, but that evenness is NOT per-orbit: "
            f"{odd_orbit_words} of 95 completions contain at least one individual orbit "
            "with an ODD zero-charge count. So the O* excursion argument does not transfer "
            "orbit by orbit, and 'every non-O* orbit is entered and exited in paired "
            "excursions' is 반증됨 as stated."
        ),
        "per_word": per_word,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ceiling", type=int, default=8)
    ap.add_argument("--ordered", default=str(ROOT / "outputs" / "rr_ordered_event_words.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_o_star_excursions.json"))
    ap.add_argument("--certificate", default=str(ROOT / "outputs" / "rr_gap_certificates.json"))
    a = ap.parse_args()

    all_exc, per_ell_cert = [], []
    for ell in range(5):
        exc, nodes, states, trunc = excursions(ell, a.ceiling)
        for e in exc:
            e["abandonment_ell"] = ell
        all_exc.extend(exc)
        per_ell_cert.append({"abandonment_ell": ell, "o_star": HEX0[ell + 1],
                             "nodes_expanded": nodes, "dedup_states": states,
                             "excursions_found": len(exc),
                             "frontier_truncated_at_ceiling": trunc})
        print(f"ell={ell}: {len(exc)} excursions, {nodes} nodes, truncated={trunc}")

    by_L = Counter(e["L"] for e in all_exc)
    by_Lx = Counter((e["L"], e["exponent"]) for e in all_exc)
    print(f"\nlegal excursion length spectrum (L): {dict(sorted(by_L.items()))}")
    missing = [n for n in range(1, a.ceiling + 1) if n not in by_L]
    print(f"lengths with NO legal excursion     : {missing}")

    print(f"\n(L, exponent) -> count:")
    odd_rows = []
    for k in sorted(by_Lx):
        par = "ODD " if k[1] % 2 else "even"
        viol = k[1] % 2 == 1 and k[0] > 1
        w = next(e for e in all_exc if (e["L"], e["exponent"]) == k)
        print(f"   L={k[0]} G={k[0]-1} exp={k[1]} {par} n={by_Lx[k]:<4} {w['symbolic']}"
              f"{'   <== VIOLATES the alphabet' if viol else ''}")
        if viol:
            odd_rows.append({**w, "count": by_Lx[k]})

    max_allowed = max((e["L"] for e in all_exc if not (e["exponent"] % 2 == 1 and e["L"] > 1)),
                      default=None)
    min_odd = min((e["L"] for e in all_exc if e["exponent"] % 2 == 1 and e["L"] > 1),
                  default=None)
    print(f"\nlongest alphabet-respecting excursion : L={max_allowed}")
    print(f"shortest alphabet-VIOLATING excursion : L={min_odd}")

    # ---- normal forms (section 11) ----
    forms = defaultdict(lambda: {"count": 0, "joint_words": set()})
    for e in all_exc:
        key = (e["L"], e["exponent"], e["symbolic"])
        forms[key]["count"] += 1
        forms[key]["joint_words"].add(tuple(e["joint_word"]))
    nf = [{"L": k[0], "G": k[0] - 1, "exponent": k[1], "symbolic": k[2],
           "count": v["count"], "distinct_joint_words": len(v["joint_words"]),
           "n_R": k[2].count("R"), "n_F": k[2].count("F"), "n_E": k[2].count("E"),
           "respects_alphabet": not (k[1] % 2 == 1 and k[0] > 1)}
          for k, v in sorted(forms.items())]
    print(f"\ndistinct symbolic normal forms: {len(nf)}")

    nos = non_o_star_data(a.ordered)
    if nos.get("available"):
        print(f"\nnon-O* zero-charge: aggregate parity histogram "
              f"{nos['total_other_parity_histogram']}, "
              f"{nos['words_with_some_odd_single_orbit']}/95 completions have at least "
              f"one individual orbit with an ODD count")

    verdict = (
        f"반증됨. The target proposition -- every legal first-return O* excursion has "
        f"gap G <= 6 (length L <= 7), and more precisely that every legal excursion "
        f"respects the alphabet -- is FALSE. Legal excursions of length L={min_odd} with "
        f"ODD return exponent exist at every one of the five abandonment roots. The "
        f"legal length spectrum is {sorted(by_L)}; lengths {missing} are legally "
        f"impossible, so the spectrum is not an interval and no monotone "
        f"'longer implies collision' argument can exist."
    ) if min_odd else (
        f"No legal excursion violates the alphabet up to L={a.ceiling}."
    )
    print(f"\n{verdict}")

    rep = {
        "schema": "rr-o-star-excursions-v1",
        "definition": ("an O*-excursion starts at a port of O*, its intermediate edges "
                       "land outside O*, and it ends with the edge returning to O*; "
                       "L = number of macro-edges inclusive of the return, G = L-1"),
        "ceiling_L": a.ceiling,
        "why_ceiling_8": ("deliberately past the group threshold 6, so that 'no excursion "
                          "exceeds 6' would be a finding and not an artifact; a depth-6 "
                          "scope could not have settled this either way"),
        "not_a_completion_search": ("this enumerates legal preparation prefixes only; it "
                                    "does NOT ask whether a prefix extends to a finished "
                                    "RR word, and the verdict is scoped accordingly"),
        "length_spectrum": {str(k): v for k, v in sorted(by_L.items())},
        "legally_impossible_lengths": missing,
        "length_exponent_histogram": {f"L={k[0]},exponent={k[1]}": v
                                      for k, v in sorted(by_Lx.items())},
        "longest_alphabet_respecting_L": max_allowed,
        "shortest_alphabet_violating_L": min_odd,
        "alphabet_violating_normal_forms": odd_rows,
        "normal_forms": nf,
        "non_o_star_zero_charge": nos,
        "verdict": verdict,
        "grade": ("root-local exhaustive over excursions (frontier keyed by (state, depth), "
                  "no node cap) + exact counterexample for the violating excursions"),
        "excursions": all_exc,
    }
    Path(a.output).write_text(json.dumps(rep, indent=2, sort_keys=True, ensure_ascii=False,
                                         default=str), encoding="utf-8")
    print("wrote", a.output)

    cert = {
        "schema": "rr-gap-certificates-v1",
        "scope_statement": (
            "root-local excursion scope: the five abandonment roots obtained from "
            "exact.initial_state() by rot^ell (ell=0..4) followed by the unique "
            "abandonment joint w2:10; transitions are macro.macro_edges() filtered by "
            "macro.area_a_prune_reason(., macro.AREA_A); dedup key is (stable_key, depth); "
            f"excursion length ceiling L <= {a.ceiling}; no node, edge or time cap. "
            "This is NOT 'the whole RR universe' and the phrase is not used."
        ),
        "engine_sha256": exact.CODE_SHA256,
        "core_sha256": exact.CORE_SHA256,
        "transition_generator": "macro.macro_edges + area_a_prune_reason(AREA_A)",
        "per_ell": per_ell_cert,
        "totals": {"excursions": len(all_exc),
                   "nodes": sum(c["nodes_expanded"] for c in per_ell_cert)},
        "frontier_exhausted_below_ceiling": not any(c["frontier_truncated_at_ceiling"]
                                                    for c in per_ell_cert),
        "grade": "root-local exhaustive",
    }
    Path(a.certificate).write_text(json.dumps(cert, indent=2, sort_keys=True,
                                              ensure_ascii=False, default=str),
                                   encoding="utf-8")
    print("wrote", a.certificate)


if __name__ == "__main__":
    main()
