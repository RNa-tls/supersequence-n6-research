#!/usr/bin/env python3
"""Round 25, sections 5, 7, 8, 13, 16: the O* phase walk.

This is the non-additive object Round 24's impossibility theorem demands.
Instead of counting events, we follow the PHASE of the single orbit O*
(the nearest residual orbit left open by the abandonment) as the word is
read left to right, and ask how far it advances.

Three structural facts, each measured here and each hand-provable:

  1. F (fresh Z3 opening) NEVER targets O*.  An F event opens a NEW orbit,
     and O* is already open (the abandonment registered it), so an F event
     targeting O* would not be new.  Hence the zero-charge events that
     touch O* are exactly the E events.
  2. Every E step advances the O* phase by exactly +1.
  3. Every R step advances the O* phase by an EVEN amount (+2 or +4).

Together with the total advance being 4 (mod 5) in every branch, these give

     #E_{->O*}  ==  4 + 5k  ==  k   (mod 2)

so "#zero-charge events targeting O* is even" is EXACTLY "the winding
number k is even".  That is a genuine reduction of the open parity
proposition to a single ordered quantity -- but k even is NOT proved here,
and section 5 below exhibits a delta sequence with k=1 that is not
excluded by any local rule we know.  Reported 미완료.

Input: outputs/rr_ordered_event_words.json (produced by
analyze_rr_ordered_phase_actions.py).  No new search.
"""
from __future__ import annotations
import argparse, json
from collections import Counter
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEX0 = [0, 120, 33, 9, 3, 1]


def phase_walk(row):
    """Recover the ordered O*-phase walk with the symbol responsible for
    each step.  Returns (steps, start_phase) where steps is a list of
    (symbol, from_phase, to_phase, delta mod 5)."""
    seq = row["O_star_phase_sequence"]
    touching = [e for e in row["events"] if e["targets_O_star"]]
    assert len(seq) == len(touching) + 1, (len(seq), len(touching))
    steps = []
    for i, e in enumerate(touching):
        a, b = seq[i], seq[i + 1]
        steps.append({"sym": e["sym"], "from": a, "to": b, "delta": (b - a) % 5})
    return steps, seq[0]


def interval_structure(row):
    """Section 7: is every F (orbit opening) closed by a later E targeting
    the same orbit?  If so the word has a parenthesis structure and F
    events cancel in pairs at the orbit level."""
    opened, closed, unclosed = [], 0, 0
    pending = []
    for e in row["events"]:
        if e["sym"] == "F":
            pending.append(e["target_orbit"]); opened.append(e["target_orbit"])
        elif e["sym"] == "E":
            if e["target_orbit"] in pending:
                pending.remove(e["target_orbit"]); closed += 1
    unclosed = len(pending)
    return {"n_F": len(opened), "n_closed": closed, "n_unclosed": unclosed}


def free_winding_search(max_len=6, max_R=None):
    """Section 5 / 16: is k>=1 excluded by the step alphabet alone?

    The step alphabet observed is E:+1, R:+2, R:+4.  A walk from the
    abandonment phase to the hub phase with total advance 4 (mod 5) and
    winding number k has sum(deltas) = 4 + 5k.  Ask: does the alphabet
    admit a k=1 walk whose visited phases are all DISTINCT (each phase of
    a 5-phase orbit can be entered at most once)?  If none exists, k<=0
    follows from the alphabet plus injectivity, and the parity is closed.
    """
    witnesses = []
    alphabet = [("E", 1), ("R", 2), ("R", 4)]
    for n in range(1, max_len + 1):
        for combo in product(alphabet, repeat=n):
            if max_R is not None and sum(1 for s, _ in combo if s == "R") > max_R:
                continue
            deltas = [d for _, d in combo]
            total = sum(deltas)
            k, rem = divmod(total - 4, 5)
            if rem != 0 or k < 1:
                continue
            # simulate from phase 0; require every visited phase distinct
            cur, seen_ph, ok = 0, [0], True
            for d in deltas:
                cur = (cur + d) % 5
                if cur in seen_ph:
                    ok = False; break
                seen_ph.append(cur)
            if not ok:
                continue
            nE = sum(1 for s, _ in combo if s == "E")
            witnesses.append({"deltas": deltas, "symbols": [s for s, _ in combo],
                              "winding_k": k, "n_E": nE, "n_E_parity": nE % 2,
                              "visited_phases": seen_ph})
    return witnesses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(ROOT / "outputs" / "rr_ordered_event_words.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_o_star_winding.json"))
    a = ap.parse_args()

    data = json.loads(Path(a.input).read_text(encoding="utf-8"))
    rows = [r for r in data["rows"] if r["landing_class"] == "O_star"]

    delta_by_sym = Counter()
    winding = Counter()
    advance_by_ell = Counter()
    f_targets_o_star = 0
    per_row = []
    for r in rows:
        steps, start = phase_walk(r)
        for s in steps:
            delta_by_sym[f"{s['sym']}:+{s['delta']}"] += 1
            if s["sym"] == "F":
                f_targets_o_star += 1
        total = sum(s["delta"] for s in steps)
        end = r["O_star_phase_sequence"][-1]
        adv = (end - start) % 5
        advance_by_ell[(r["abandonment_ell"], adv)] += 1
        k, rem = divmod(total - adv, 5)
        winding[k if rem == 0 else "non-integral"] += 1
        nE = sum(1 for s in steps if s["sym"] == "E")
        per_row.append({"abandonment_ell": r["abandonment_ell"],
                        "ordered_word": r["ordered_word"],
                        "start_phase": start, "end_phase": end,
                        "advance": adv, "sum_deltas": total, "winding_k": k,
                        "n_E_to_O_star": nE, "n_E_parity": nE % 2,
                        "n_zero_charge": r["n_zero_charge"],
                        "zero_charge_parity": r["zero_charge_parity"],
                        "steps": steps,
                        "interval": interval_structure(r)})

    iv = Counter((p["interval"]["n_F"], p["interval"]["n_closed"], p["interval"]["n_unclosed"])
                 for p in per_row)
    first_last = Counter((r["ordered_word"][0], r["ordered_word"][-1]) for r in rows)
    zc = [[s for s in r["ordered_word"] if s != "R"] for r in rows]
    zc_first_last = Counter((w[0], w[-1]) for w in zc if w)
    kE = Counter((p["winding_k"], p["n_E_parity"]) for p in per_row)

    print(f"O*-landing completions: {len(rows)}")
    print(f"F events targeting O*      : {f_targets_o_star}   (expected 0)")
    print(f"O*-step delta by symbol    : {dict(sorted(delta_by_sym.items()))}")
    print(f"total advance by (ell,adv) : {dict(sorted(advance_by_ell.items()))}")
    print(f"winding number k           : {dict(sorted(winding.items(), key=str))}")
    print(f"(k, #E_to_O* parity)       : {dict(sorted(kE.items(), key=str))}")
    print(f"interval (nF,closed,open)  : {dict(sorted(iv.items()))}")
    print(f"(first,last) symbol        : {dict(sorted(first_last.items()))}")
    print(f"(first,last) zero-charge   : {dict(sorted(zc_first_last.items()))}")

    all_R_even = all(k.startswith("R:") and int(k.split("+")[1]) % 2 == 0
                     for k in delta_by_sym if k.startswith("R:"))
    all_E_one = all(k == "E:+1" for k in delta_by_sym if k.startswith("E:"))
    print(f"\nall R deltas even : {all_R_even}")
    print(f"all E deltas == 1 : {all_E_one}")

    nR_hist = Counter(sum(1 for s in p["steps"] if s["sym"] == "R") for p in per_row)
    print(f"#R steps targeting O*      : {dict(sorted(nR_hist.items()))}")
    inj = sum(1 for p in per_row
              if len({p["start_phase"], *[s["to"] for s in p["steps"]]}) != len(p["steps"]) + 1)
    len_hist = Counter(len(p["steps"]) for p in per_row)
    print(f"completions revisiting an O* phase : {inj}   (expected 0)")
    print(f"O*-walk length histogram   : {dict(sorted(len_hist.items()))}")

    wit = free_winding_search()
    print(f"\nk>=1 walks, distinct phases, alphabet only : {len(wit)}")
    for w in wit:
        print(f"   deltas={w['deltas']} syms={w['symbols']} k={w['winding_k']} "
              f"#E={w['n_E']} phases={w['visited_phases']}")
    wit2 = free_winding_search(max_R=2)
    print(f"k>=1 walks, distinct phases, #R<=2 (RR bound): {len(wit2)}")
    for w in wit2:
        print(f"   deltas={w['deltas']} syms={w['symbols']} k={w['winding_k']} "
              f"#E={w['n_E']} phases={w['visited_phases']}")

    rep = {
        "schema": "rr-o-star-winding-v1",
        "question": ("reduce '#zero-charge events targeting O* is even' to an ordered "
                     "quantity, per Round 24's additive-impossibility theorem"),
        "n_O_star_completions": len(rows),
        "F_events_targeting_O_star": f_targets_o_star,
        "o_star_step_delta_by_symbol": dict(sorted(delta_by_sym.items())),
        "total_advance_by_ell_and_advance": {f"ell={k[0]},advance={k[1]}": v
                                             for k, v in sorted(advance_by_ell.items())},
        "winding_number_histogram": {str(k): v for k, v in sorted(winding.items(), key=str)},
        "winding_vs_E_parity": {f"k={k[0]},E_parity={k[1]}": v for k, v in sorted(kE.items(), key=str)},
        "interval_structure_histogram": {f"nF={k[0]},closed={k[1]},unclosed={k[2]}": v
                                         for k, v in sorted(iv.items())},
        "first_last_symbol_histogram": {f"{k[0]}..{k[1]}": v for k, v in sorted(first_last.items())},
        "first_last_zero_charge_histogram": {f"{k[0]}..{k[1]}": v for k, v in sorted(zc_first_last.items())},
        "all_R_deltas_even": all_R_even,
        "all_E_deltas_are_plus_one": all_E_one,
        "hand_proof_fragment": (
            "(a) F never targets O*: an F event opens a NEW orbit, but O* is already "
            "open because the abandonment joint registered it; therefore the zero-charge "
            "events touching O* are exactly the E events. (b) E advances the O* phase by "
            "exactly +1 (a zero-charge Z2 steps to the adjacent phase of the orbit it is "
            "already inside). (c) every R step advances it by an even amount. (d) the "
            "total advance is 4 (mod 5) for EVERY ell: the hub position j has phase j-1 "
            "while the abandonment phase is j mod 5. Hence "
            "#E_{->O*} == 4 + 5k == k (mod 2): the parity of the zero-charge events "
            "targeting O* IS the parity of the winding number k."
        ),
        "n_R_steps_targeting_O_star_histogram": {str(k): v for k, v in sorted(nR_hist.items())},
        "completions_revisiting_an_O_star_phase": inj,
        "o_star_walk_length_histogram": {str(k): v for k, v in sorted(len_hist.items())},
        "finite_case_analysis_k_equals_zero": (
            "Given (i) step alphabet {E:+1, R:+2, R:+4}, (ii) the five O* phases are "
            "pairwise distinct along the walk so the walk has at most 4 steps, (iii) the "
            "total advance is 4 (mod 5), and (iv) an RR word has exactly two R events so "
            "at most 2 steps are R: sum(deltas) = 4 + 5k with all deltas positive forces "
            "k >= 0; k >= 2 needs sum >= 14 while the maximum is 4+4+1+1 = 10, so k <= 1; "
            "and k = 1 needs sum = 9, whose only multiset over {1} u {2,4} with at most "
            "two non-1 entries and at most four entries is {4,4,1} -- all three orderings "
            "revisit a phase (4,4,1: 0->4->3->4; 4,1,4: 0->4->0; 1,4,4: 0->1->0). Hence "
            "k = 0 and #E_{->O*} = sum - (even) == 4 == 0 (mod 2). The exhaustive search "
            "k_ge_1_witnesses_under_R_le_2 confirms this mechanically (0 witnesses). "
            "This step is a 손증명; the residual gap is premise (i)."
        ),
        "open_step": (
            "The alphabet alone does not exclude k>=1 (see alphabet_only_k_ge_1_witnesses: "
            "delta sequences with distinct visited phases, winding k=1 and ODD #E). "
            "Adding the RR structural bound '#R steps targeting O* <= 2' -- an RR word has "
            "exactly two R events, R1 inside the word and R2 strictly after the completer, "
            "so at most R1 and an R-completer can target O* -- kills every remaining "
            "witness, see k_ge_1_witnesses_under_R_le_2. THIS IS NOT YET A PROOF: the "
            "search is over delta sequences, and it has not been shown that every legal "
            "word's O*-walk is realizable as such a sequence and conversely. Stated as a "
            "candidate closure, graded 미완료."
        ),
        "alphabet_only_k_ge_1_witnesses": wit[:20],
        "k_ge_1_witnesses_under_R_le_2": wit2[:20],
        "grade": ("손증명 for fragments (a),(d) and for the finite case analysis k=0; "
                  "root-local exhaustive for the step alphabet (b),(c) and phase "
                  "injectivity; 미완료 overall, because (b) and (c) are measured, not proved"),
        "per_completion": per_row,
    }
    Path(a.output).write_text(json.dumps(rep, indent=2, sort_keys=True, ensure_ascii=False, default=str),
                              encoding="utf-8")
    print("wrote", a.output)


if __name__ == "__main__":
    main()
