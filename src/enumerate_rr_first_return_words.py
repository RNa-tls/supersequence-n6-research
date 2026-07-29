#!/usr/bin/env python3
"""Round 26, sections 1, 2, 6, 7: the exact first-return table.

COUNTING CONVENTION (section 1), fixed once and used everywhere from
here on.  Let v_i, v_{i+1} be consecutive O* visits -- macro-edges whose
JOINT TARGET lies in O*.  Then

    L  =  the first-return WORD LENGTH
       =  number of macro-edges from the port v_i up to and including
          the edge that lands back in O*
    G  =  L - 1  =  number of intervening macro-edges that do not land
          in O* ("the gap")

so an immediate return (the very next macro-edge lands in O*) is L = 1,
G = 0.  Both numbers are reported side by side in every table below,
because Round 25's write-up compared observed G values (0, 3, 4) against
a group threshold stated in L (<= 6) without saying so -- the conclusion
was unaffected (L = 1, 4, 5 are all <= 6) but the statement mixed units.
This file is the correction.

Every preparation macro-edge is forced to ell=5, so it acts on the walk
position by right-composition with a fixed element g_j = Sigma^5 o a_j:

    g(w2:10) = E,  g(w3:120) = E^2,  g(w3:201), g(w3:210) not in <E>.

A first-return word is therefore a word over these four generators whose
product lies in <E> and none of whose proper prefixes does.  The return
exponent is the <E>-exponent of the product, i.e. the O* phase
displacement.

The enumeration is LAYERED: layer_d holds every group element reachable
by a length-d word all of whose prefixes avoid <E>.  Tracking (element,
exact length) rather than (element) alone makes the table complete for
every length, not merely a shortest-path witness -- Round 25's BFS
deduped by element, which is sound for shortest lengths but does not
enumerate longer words.

This is a finite computation in S_6.  No search, no engine state, no
legality: those enter in analyze_rr_length7_obstructions.py.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
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


macro = _load("erfrw", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core
mbl = {m.label: m for m in exact.ALL_MOVES}
JOINTS = ["w2:10", "w3:120", "w3:201", "w3:210"]


def build():
    S5 = core.power(core.SIGMA, 5)
    epow = {core.power(core.E, i): i for i in range(5)}
    gens = {j: core.compose(S5, mbl[j].action) for j in JOINTS}
    return S5, epow, gens


def layered_first_returns(gens, epow, max_len):
    """layer[d] = {element: one witness word of length exactly d, all of
    whose prefixes avoid <E>}.  Returns the layers and, per length, the
    complete set of achievable return exponents with witnesses."""
    idn = tuple(range(core.N))
    layers = [{idn: ()}]
    returns = defaultdict(list)          # L -> list of records
    for d in range(max_len):
        nxt = {}
        for u, w in layers[d].items():
            for name, g in gens.items():
                v = core.compose(u, g)
                nw = w + (name,)
                if v in epow:
                    returns[d + 1].append({"word": list(nw), "exponent": epow[v]})
                    continue
                if v not in nxt:
                    nxt[v] = nw
        layers.append(nxt)
        if not nxt:
            break
    return layers, returns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-len", type=int, default=8)
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_first_return_table.json"))
    a = ap.parse_args()

    S5, epow, gens = build()
    gen_rows = {j: {"generator": list(gens[j]), "E_exponent": epow.get(gens[j]),
                    "orbit_preserving": gens[j] in epow} for j in JOINTS}
    print("ell=5 composite generators:")
    for j in JOINTS:
        e = epow.get(gens[j])
        print(f"   {j:8s} {gens[j]}  {'E^' + str(e) if e is not None else 'NOT in <E>'}")

    layers, returns = layered_first_returns(gens, epow, a.max_len)
    print(f"\nlayer sizes (elements reachable by a length-d prefix-avoiding word):")
    for d, L in enumerate(layers):
        print(f"   d={d}: {len(L)}")

    print(f"\n=== first-return table (L = word length, G = L-1 = gap) ===")
    print(f"{'L':>2} {'G':>2}  {'#returns':>8}  exponents (count)             odd?")
    table = {}
    first_odd = None
    for L in sorted(returns):
        recs = returns[L]
        exps = Counter(r["exponent"] for r in recs)
        odd = sorted({e for e in exps if e % 2 == 1})
        # exponent 1 reached by the single generator E is the legitimate E step
        bad = [r for r in recs
               if r["exponent"] % 2 == 1 and not (L == 1 and r["word"] == ["w2:10"])]
        if bad and first_odd is None:
            first_odd = L
        table[str(L)] = {
            "gap_G": L - 1, "n_first_return_words": len(recs),
            "exponent_histogram": {str(k): v for k, v in sorted(exps.items())},
            "odd_exponents": odd,
            "violating_word_count": len(bad),
            "violating_words": [r for r in bad[:200]],
            "sample_words": {str(e): next(r["word"] for r in recs if r["exponent"] == e)
                             for e in sorted(exps)},
        }
        print(f"{L:>2} {L-1:>2}  {len(recs):>8}  "
              f"{dict(sorted(exps.items()))}  {'ODD:' + str(odd) if odd else ''}"
              f"{'  <-- VIOLATES' if bad else ''}")

    safe_L = (first_odd - 1) if first_odd else a.max_len
    print(f"\nfirst length with a violating (odd, non-E) return : L = {first_odd}  (G = {first_odd-1})")
    print(f"=> every first-return word with L <= {safe_L} (G <= {safe_L-1}) has "
          f"exponent 1 (single E), 2 (single E^2), or EVEN")

    rep = {
        "schema": "rr-first-return-table-v1",
        "counting_convention": (
            "L = first-return word length = macro-edges from the O* port up to and "
            "including the edge landing back in O*. G = L-1 = intervening macro-edges "
            "('the gap'). An immediate return is L=1, G=0. Round 25's write-up compared "
            "observed G values against a threshold stated in L without saying so; the "
            "conclusion was unaffected but the units were mixed. This is the correction."
        ),
        "generators": gen_rows,
        "enumeration": ("layered over (element, exact length) rather than element alone, "
                        "so the table is complete for every length up to the ceiling, "
                        "not a shortest-path witness set"),
        "max_len": a.max_len,
        "layer_sizes": {str(d): len(L) for d, L in enumerate(layers)},
        "by_length": table,
        "first_violating_length_L": first_odd,
        "safe_length_L": safe_L,
        "safe_gap_G": safe_L - 1,
        "theorem": (
            f"Every first-return word of length L <= {safe_L} (gap G <= {safe_L-1}) has "
            "<E>-exponent 1 (the single generator E), 2 (the single generator E^2), or "
            "even. Odd exponents first occur at L = "
            f"{first_odd}. exact group theorem."
        ),
        "grade": "exact group theorem (finite complete computation in S_6)",
    }
    Path(a.output).write_text(json.dumps(rep, indent=2, sort_keys=True, ensure_ascii=False,
                                         default=str), encoding="utf-8")
    print("wrote", a.output)


if __name__ == "__main__":
    main()
