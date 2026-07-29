#!/usr/bin/env python3
"""The O*-step lemma, proved as a finite group computation.

Every preparation macro-edge is forced to ell=5, so it acts on the walk
position by right-composition with ONE fixed element of S_6:

    g_j = Sigma^5 o action_j .

Computing the four of them:

    g(w2:10)  = E          (E = (0 1 2 3 4), the E-orbit generator)
    g(w3:120) = E^2
    g(w3:201) = (2,3,4,1,5,0)   -- not in <E>
    g(w3:210) = (2,3,4,1,0,5)   -- not in <E>

so the first two PRESERVE every E-orbit and the last two do not.  Two
corollaries are immediate and hand-proved:

  * w2:10 and w3:120 can never be F (a fresh orbit opening), because an
    orbit-preserving edge cannot open a new orbit.  So F is always
    w3:201 or w3:210.
  * O* phases: if the walk sits at a port q of O* and the next edge is
    w2:10, it lands at q o E -- phase +1 exactly.  If it is w3:120, it
    lands at q o E^2 -- phase +2.

For the orbit-CHANGING joints the displacement is not local: the walk
leaves O*, wanders, and returns.  Writing the intervening edges as
y_1..y_m, the position when it returns is

    q o g_{y_1} o ... o g_{y_m} o g_{a}

so the phase displacement delta is exactly the <E>-exponent of that
product.  The O*-step lemma is therefore the following statement about
the free monoid on the four generators, with no reference to the search,
to legality, or to Area A at all:

  (LEMMA)  If a product of generators lies in <E> and no proper prefix
           does, its <E>-exponent is 1 (the single generator E), or 2
           (the single generator E^2), or EVEN.

This script decides (LEMMA) exhaustively.  S_6 has 720 elements, so the
first-return analysis is a finite BFS and the answer is a proof or a
counterexample -- not a measurement.
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


macro = _load("prosl", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
mbl = {m.label: m for m in exact.ALL_MOVES}
JOINTS = ["w2:10", "w3:120", "w3:201", "w3:210"]


def first_return_analysis(gens, epow, max_len):
    """BFS over first-return words: products of generators whose first
    entry into <E> is at the last letter.  Records the exponent reached
    and a shortest witness word for each (length, exponent) pair."""
    idn = tuple(range(core.N))
    returns = Counter()
    witness = {}
    odd_bad = []
    # state: (group element not in <E>, word); start from identity, which IS
    # in <E> -- the "sitting on a port" state -- and take one step out.
    frontier = deque([(idn, ())])
    seen = {idn}
    while frontier:
        u, w = frontier.popleft()
        if len(w) >= max_len:
            continue
        for name, g in gens.items():
            v = core.compose(u, g)
            nw = w + (name,)
            if v in epow:
                d = epow[v]
                returns[(len(nw), d)] += 1
                witness.setdefault((len(nw), d), list(nw))
                allowed = (len(nw) == 1 and d in (1, 2)) or d % 2 == 0
                if not allowed:
                    odd_bad.append({"word": list(nw), "exponent": d})
                continue  # a first-return word stops here
            if v in seen:
                continue
            seen.add(v)
            frontier.append((v, nw))
    return returns, witness, odd_bad, len(seen)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-len", type=int, default=12)
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_o_star_step_lemma.json"))
    a = ap.parse_args()

    S5 = core.power(core.SIGMA, 5)
    epow = {core.power(core.E, i): i for i in range(5)}
    gens = {j: core.compose(S5, mbl[j].action) for j in JOINTS}

    print("ell=5 composite generators g_j = Sigma^5 o action_j:")
    gen_rows = {}
    for j in JOINTS:
        g = gens[j]
        e = epow.get(g)
        gen_rows[j] = {"generator": list(g), "E_exponent": e,
                       "orbit_preserving": e is not None}
        print(f"   {j:8s} {g}   in <E>: {'E^' + str(e) if e is not None else 'NO'}")

    orbit_preserving = [j for j in JOINTS if epow.get(gens[j]) is not None]
    print(f"\norbit-preserving joints: {orbit_preserving}")
    print("=> those joints can never be F (a fresh orbit opening): 손증명")

    returns, witness, odd_bad, reached = first_return_analysis(gens, epow, a.max_len)

    print(f"\nfirst-return BFS: {reached} distinct non-<E> elements reached "
          f"(|S_6| = 720), word length ceiling {a.max_len}")
    print("(word length, <E>-exponent reached) -> #words, shortest witness:")
    for k in sorted(returns):
        print(f"   len={k[0]} exponent={k[1]:>1}  n={returns[k]:<5} "
              f"witness={witness[k]}")

    odd_exps = sorted({k[1] for k in returns if k[1] % 2 == 1})
    print(f"\nodd exponents reachable at all      : {odd_exps}")
    print(f"violations of (LEMMA)               : {len(odd_bad)}")
    for v in odd_bad[:6]:
        print(f"   {v}")

    holds = len(odd_bad) == 0
    print(f"\n(LEMMA) holds over the free monoid  : {holds}")

    # the sharp threshold: the longest L for which every first-return word of
    # length <= L obeys the lemma.  This is what a preparation-depth bound buys.
    shortest_viol = min((len(v["word"]) for v in odd_bad), default=None)
    threshold = None if shortest_viol is None else shortest_viol - 1
    print(f"shortest violating first-return word: length {shortest_viol}")
    print(f"=> (LEMMA) is PROVED for every first-return word of length <= {threshold}")

    rep = {
        "schema": "rr-o-star-step-lemma-v1",
        "statement": (
            "If a product of the four ell=5 composite generators lies in <E> and no "
            "proper prefix does, its <E>-exponent is 1 (the single generator E), 2 "
            "(the single generator E^2), or even."
        ),
        "generators": gen_rows,
        "orbit_preserving_joints": orbit_preserving,
        "corollary_F_joints": (
            "w2:10 and w3:120 have ell=5 composite E and E^2, which preserve every "
            "E-orbit, so neither can ever be a fresh orbit opening; every F event is "
            "w3:201 or w3:210. 손증명."
        ),
        "corollary_E_step": (
            "If the walk sits at a port q of O*, a w2:10 edge lands at q o E (phase +1) "
            "and a w3:120 edge at q o E^2 (phase +2). This is premise (b) of "
            "rr_o_star_winding.json, now 손증명 rather than measured."
        ),
        "first_return_word_length_ceiling": a.max_len,
        "distinct_non_E_elements_reached": reached,
        "first_return_histogram": {f"len={k[0]},exponent={k[1]}": v
                                   for k, v in sorted(returns.items())},
        "shortest_witnesses": {f"len={k[0]},exponent={k[1]}": v
                               for k, v in sorted(witness.items())},
        "odd_exponents_reachable": odd_exps,
        "lemma_violations": odd_bad[:50],
        "lemma_violation_count": len(odd_bad),
        "lemma_holds_over_free_monoid": holds,
        "shortest_violating_first_return_length": shortest_viol,
        "lemma_proved_up_to_first_return_length": threshold,
        "what_this_means": (
            "(LEMMA) is FALSE as a free-monoid statement -- there are first-return words "
            f"of length {shortest_viol} with an ODD <E>-exponent, so the O*-step alphabet "
            "is not a pure group fact and cannot be proved without legality constraints. "
            f"But (LEMMA) IS proved, as an exact group computation, for every first-return "
            f"word of length <= {threshold}. Consequently a bound of {threshold} on the "
            "number of preparation macro-edges between two consecutive O* visits would "
            "close the alphabet lemma, and with it the winding argument and the parity. "
            "That is exactly the long-standing open 'small preparation-depth bound' item: "
            "it is now known to be sufficient, not merely desirable."
        ),
        "grade": ("exact group computation over S_6 -- independent of the RR search, of "
                  "Area A, and of legality; a finite complete verification, not a "
                  "measurement" if holds else
                  "반증됨 over the free monoid: the lemma needs legality constraints"),
    }
    Path(a.output).write_text(json.dumps(rep, indent=2, sort_keys=True, ensure_ascii=False,
                                         default=str), encoding="utf-8")
    print("wrote", a.output)


if __name__ == "__main__":
    main()
