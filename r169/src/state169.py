#!/usr/bin/env python3
"""Round 169 phases 0-2 -- state, the (p) rule, and the domination graph.

Round 168 proved that the round-167 ordering is not a generation-cost model.
The cost of an EXTREE certificate depends on which capacity cells are ALREADY
independently certified, because a `(p)` leaf is justified by the minimum
capacity among certified componentwise dominators of the state.

THE RULE, recovered verbatim from the generator and both verifiers.  At a
search node with remaining budgets (tok, a, bb, e, h), deficit and the cell's
dmax, the generator forms

    d*   = dmax - deficit + 4 + 5 * tok
    ub(tok, d*, a, bb, e, h)
         = min( 120 + a + bb + e,
                min { cap(K) : K = (kb,kd,ka,kbb,ke,kh) certified,
                               kb >= tok, kd >= d*, ka >= a,
                               kbb >= bb, ke >= e, kh >= h } )
    r2   = ports + ub(...) - 1

and emits a leaf when r2 < cap + 1.  `120 + a + bb + e` is the certified
analytic fallback (P2); the other term is the monotone bound (P1).

MONOTONICITY.  ub is a minimum over a set that only grows as cells are
certified, so adding a certified dominator can only keep or decrease ub, hence
only keep or widen the set of states where r2 < target, hence only keep or
reduce the node count -- the deterministic move order is unchanged, and a
branch pruned by r2 < best+1 cannot have improved the incumbent, so the
incumbent trajectory of the discovery pass is unchanged too.  The claim is
checked numerically as well, not only argued.

NOTHING here reads a capacity from the round-152 table.  The certified set is
recovered from the proof objects themselves.
"""
from __future__ import annotations
import gzip, hashlib, json, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r163" / "src"))
sys.path.insert(0, str(ROOT / "r166" / "src"))
sys.path.insert(0, str(ROOT / "r168" / "src"))
import hidden163 as H                                             # noqa: E402
from verify168 import scan_headers, read_text                     # noqa: E402
from recheck168 import System, parse, cellstr                     # noqa: E402

BATCHES = ("r164/certs/extree_prefix_164.txt.gz",
           "r166/certs/extree_batch2_166.txt.gz",
           "r166/certs/extree_batch3_166.txt.gz",
           "r168/certs/extree_batch1_168.txt.gz")
UBFALL = 120


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def certified_from_proof_objects():
    """(cell -> cap) taken from the certificates, never from a table."""
    out, prov = {}, {}
    for rel in BATCHES:
        text, _c, _p = read_text(rel)
        _refs, _deps, cells = scan_headers(text)
        for cell, cap in cells:
            if cell in out and out[cell] != cap:
                raise SystemExit(f"{cellstr(cell)} carries two capacities")
            out[cell] = cap
            prov.setdefault(cell, rel)
    return out, prov


def dominates(K, s):
    """K may justify a (p) leaf at budget vector s."""
    return all(k >= v for k, v in zip(K, s))


def ub(cert, s):
    """the exact current formula: analytic fallback meets the monotone bound"""
    tok, d, a, bb, e, h = s
    best = UBFALL + a + bb + e
    for K, c in cert.items():
        if c < best and dominates(K, s):
            best = c
    return best


def main():
    S = System()
    st = json.loads((ROOT / "r168" / "certs" / "state_168.json").read_text())
    cen = json.loads((ROOT / "r168" / "certs" / "census_168.json").read_text())
    assert st["ok"] and cen["ok"]
    OPT = {parse(c) for c in st["optimum"]}
    EX = [(t, tuple(k)) for t, k in st["exposed_rows"]]
    CERT, PROV = certified_from_proof_objects()

    S.apply(set(CERT))
    v = S.verdicts(set(EX))
    closed = [k for k in EX if v[k] == "STRICTLY_CLOSED"]
    remaining = sorted(OPT - set(CERT))

    # ---------- phase 1: monotonicity of ub, checked not assumed
    import random
    rng = random.Random(169)
    states = []
    for _ in range(20000):
        states.append((rng.randrange(0, 6), rng.randrange(0, 60),
                       rng.randrange(0, 6), rng.randrange(0, 4),
                       rng.randrange(0, 6), rng.randrange(0, 4)))
    half = dict(sorted(CERT.items())[:len(CERT) // 2])
    bad = [s for s in states if ub(CERT, s) > ub(half, s)]
    strictly_better = sum(1 for s in states if ub(CERT, s) < ub(half, s))

    out = dict(
        inputs={p: sha(p) for p in
                ("r168/certs/state_168.json", "r168/certs/census_168.json",
                 "r152/certs/verify_all_c152.json") + BATCHES},
        certified_from_proof_objects=dict(
            cells=len(CERT),
            batches={rel: sum(1 for c in PROV.values() if c == rel)
                     for rel in BATCHES},
            inside_the_target=len(set(CERT) & OPT),
            outside_the_target=len(set(CERT) - OPT)),
        target=dict(required=len(OPT), certified=len(set(CERT) & OPT),
                    remaining=len(remaining),
                    matches_round_168=(len(set(CERT) & OPT) == 26
                                       and len(remaining) == 164)),
        rows=dict(exposed=len(EX), independently_closed=len(closed),
                  still_open=len(EX) - len(closed),
                  matches_round_168=len(closed) == 34),
        p_rule=dict(
            formula="ub(tok,d*,a,bb,e,h) = min(120+a+bb+e, "
                    "min{cap(K) : K certified and K >= (tok,d*,a,bb,e,h) "
                    "componentwise})",
            dstar="d* = dmax - deficit + 4 + 5*tok",
            leaf="a (p) leaf is legal when ports + ub(...) - 1 < cap + 1",
            monotone_states_sampled=len(states),
            monotonicity_violations=len(bad),
            states_where_the_full_set_is_strictly_better=strictly_better,
            monotone=not bad,
            argument="ub is a minimum over a set that only grows, so it can "
                     "only decrease; the move order is deterministic and a "
                     "branch pruned by r2 < best+1 cannot improve the "
                     "incumbent, so the node count can only decrease"),
        remaining_cells=[cellstr(K) for K in remaining],
        certified_cells=sorted(cellstr(K) for K in CERT),
        certified_capacities={cellstr(K): c for K, c in sorted(CERT.items())},
    )
    out["ok"] = (out["target"]["matches_round_168"]
                 and out["rows"]["matches_round_168"]
                 and out["p_rule"]["monotone"])
    (ROOT / "r169" / "certs" / "state_169.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("inputs", "remaining_cells",
                                   "certified_cells")},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
