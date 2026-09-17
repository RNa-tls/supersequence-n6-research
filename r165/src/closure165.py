#!/usr/bin/env python3
"""Round 165 phases 0-3 -- row-closure dependency graph and cell ablation.

The census reads certified capacities as UPPER bounds.  Withdrawing a cell
makes the census fall back to a PROVED analytic bound -- (P2) 120 + a + bb + e
for a chain cell, 120 for a piece cell -- and both fallbacks are >= the
certified value.  So every model bound is MONOTONE NON-DECREASING as cells are
withdrawn, and a row can only move from closed to open, never back.  That
monotonicity is checked here, not assumed, and it is what makes the rest cheap:
a row that survives the withdrawal of ALL single-route cells cannot be opened
by withdrawing fewer.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r163" / "src"))
import hidden163 as H                                             # noqa: E402

LAYERS = (0, 1, 2, 3, 4)


def key(r):
    return tuple(r[c] for c in H.COORD)


def grouped():
    """Row groups, independent of any capacity table."""
    out = {}
    for t in LAYERS:
        g = {}
        for r in H.rows(t):
            g.setdefault(key(r), []).append(r)
        out[t] = g
    return out


def evaluate(groups, keys=None):
    """Verdict and model bounds for each row group (or a chosen subset)."""
    res = {}
    for t, g in groups.items():
        for k, variants in g.items():
            if keys is not None and (t, k) not in keys:
                continue
            req, b = H.bounds(variants)
            closing = {m: v for m, v in b.items() if v < req}
            res[(t, k)] = dict(required=req, bounds=b,
                               verdict=("STRICTLY_CLOSED" if closing else
                                        ("EQUALITY" if b and min(b.values()) == req
                                         else "SURVIVING")),
                               closers=sorted(closing))
    return res


def withdraw(chain, piece):
    for c in chain:
        H.CERT.pop(c, None)
    for c in piece:
        H.PCERT.pop(c, None)
    H.best.cache_clear()


def restore(cert, pcert):
    H.CERT.clear()
    H.CERT.update(cert)
    H.PCERT.clear()
    H.PCERT.update(pcert)
    H.best.cache_clear()


def main():
    H.load()
    CERT0, PCERT0 = dict(H.CERT), dict(H.PCERT)
    tg = json.loads((ROOT / "r164" / "certs" / "targets_164.json").read_text())
    vg = json.loads((ROOT / "r164" / "certs"
                     / "verifygen_164.json").read_text())
    done = {tuple(int(x) for x in s.split("|"))
            for s in vg["targets_upper_certified_by_two_validators"]}
    chain = [tuple(c) for c in tg["CHAIN_SINGLE_IMPL"] if tuple(c) not in done]
    piece = [tuple(c) for c in tg["PIECE_SINGLE_IMPL"] if tuple(c) not in done]

    groups = grouped()
    base = evaluate(groups)
    base_tally = Counter(v["verdict"] for v in base.values())

    # ---------- phase 2: withdraw everything that is single-route
    withdraw(chain, piece)
    allout = evaluate(groups)
    restore(CERT0, PCERT0)
    out_tally = Counter(v["verdict"] for v in allout.values())
    exposed = sorted(k for k in base
                     if base[k]["verdict"] == "STRICTLY_CLOSED"
                     and allout[k]["verdict"] != "STRICTLY_CLOSED")
    # the two genuine equality rows must be untouched by all of this
    equality_rows = sorted(k for k in base if base[k]["verdict"] == "EQUALITY")

    # ---------- monotonicity, checked rather than assumed
    mono_bad = []
    for k in base:
        for m, v in base[k]["bounds"].items():
            w = allout[k]["bounds"].get(m)
            if w is not None and w < v:
                mono_bad.append(dict(row=str(k), model=m, full=v,
                                     withdrawn=w))

    # ---------- phase 3: ablate one cell at a time
    # Only the exposed rows can change: a row that stays closed with ALL
    # single-route cells gone cannot open when only one is gone.
    ex = set(exposed)
    ablation = {}
    for kind, cells in (("chain", chain), ("piece", piece)):
        for c in cells:
            if kind == "chain":
                withdraw([c], [])
            else:
                withdraw([], [c])
            r = evaluate(groups, ex)
            restore(CERT0, PCERT0)
            opened = sorted(k for k in ex
                            if r[k]["verdict"] != "STRICTLY_CLOSED")
            ablation["|".join(map(str, c))] = dict(
                model=kind, opens=len(opened),
                rows=[list(k[1]) for k in opened][:40],
                classification=("INDIVIDUALLY_ESSENTIAL" if opened
                                else "REDUNDANT_GIVEN_CURRENT_OTHERS"))

    ess = [c for c, v in ablation.items()
           if v["classification"] == "INDIVIDUALLY_ESSENTIAL"]
    red = [c for c, v in ablation.items()
           if v["classification"] == "REDUNDANT_GIVEN_CURRENT_OTHERS"]

    out = dict(
        head_inputs={p: __import__("hashlib").sha256(
            (ROOT / p).read_bytes()).hexdigest() for p in
            ("r164/certs/targets_164.json", "r164/certs/verifygen_164.json",
             "r152/certs/verify_all_c152.json",
             "r152/certs/verify_piece_c152.json",
             "r163/src/hidden163.py")},
        remaining_single_route=dict(chain=len(chain), piece=len(piece),
                                    total=len(chain) + len(piece),
                                    already_route_b_certified=sorted(
                                        "|".join(map(str, c)) for c in done)),
        baseline=dict(tally=dict(base_tally), rows=len(base)),
        all_withdrawn=dict(tally=dict(out_tally)),
        exposed_rows=len(exposed),
        equality_rows=[list(k[1]) for k in equality_rows],
        equality_rows_still_equality_after_withdrawal=[
            list(k[1]) for k in equality_rows
            if allout[k]["verdict"] == "EQUALITY"],
        monotonicity_violations=mono_bad,
        monotone=not mono_bad,
        ablation=ablation,
        individually_essential=len(ess),
        redundant_given_current_others=len(red),
        essential_cells=sorted(ess),
        exposed_row_keys=[list(k[1]) for k in exposed],
        exposed_row_layers=dict(Counter(f"L{867 + k[0]}" for k in exposed)),
    )
    out["ok"] = (out["monotone"]
                 and base_tally["STRICTLY_CLOSED"] == 1607
                 and base_tally["EQUALITY"] == 2
                 and len(equality_rows) == 2)
    (ROOT / "r165" / "certs" / "row_closure_graph_165.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("ablation", "exposed_row_keys",
                                   "essential_cells", "head_inputs")},
                     ensure_ascii=False, indent=1))
    print("essential:", len(ess), "redundant:", len(red))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
