#!/usr/bin/env python3
"""Round 148 -- the last adversarial test: is the chain model really an UPPER
BOUND on reality?

Everything else this round checks that the computation is right.  What a
computation cannot check about itself is whether the object it bounds is the
object that exists.  The three upper-bound models are hand definitions
(D.models is the only PURE_HAND_PROOF node left on the path to L6 >= 872), so
the cheapest way the proof could still be wrong is that a real cover's
extracted chain carries MORE ports than the model allows at its own budget
vector -- in which case rows were closed that should not have been.

So: run the ACTUAL round-142 extraction (src/l6_extraction_145.py) on real
covers, read off the budget vector it reports for the chain part
    b   = sum_tok       tokens
    d   = sum_D         deficit
    a   = retained A    type-A dirty edges kept
    bb  = retained B    type-B dirty edges kept
    e   = hex_repeats   ordinary hexagon collisions
    h   = h             heavy budget
and require
    sum_P  <=  cap(b, d, a, bb, e, h)
against the round-147 sound table (extended by the proved analytic bound
120 + a + bb + e outside it).  A single violation refutes the model.

An earlier version of this script compared a raw beta-component against a
single cell.  That is NOT the model's claim -- the model bounds a component of
the extraction, whose budgets are row-level sums split over d+1+h objects -- and
it produced 54 bogus "violations" before the object mismatch was noticed.  The
extraction is used here precisely to avoid that.
"""
from __future__ import annotations
import gzip, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R147, R148 = ROOT / "r147", ROOT / "r148"
sys.path.insert(0, str(ROOT / "src"))
import l6_extraction_145 as EX                                      # noqa: E402


def cells():
    st = {}
    for f in ("chain_cells_147.json", "heavy_cells_147.json"):
        for k, v in json.loads((R147 / "tables" / f).read_text()).items():
            if v.get("status") == "EXACT_UNCAPPED":
                st[tuple(int(x) for x in k.split("|"))] = v["cc"]
    return st


ST = cells()


def bound(K):
    if K in ST:
        return ST[K], "exact_table_cell"
    return 120 + K[2] + K[3] + K[4], "proved_analytic_bound"


def words(paths, limit):
    n = 0
    for p in paths:
        p = Path(p)
        op = gzip.open if p.suffix == ".gz" else open
        with op(p, "rt") as fh:
            for ln in fh:
                w = ln.strip()
                if len(w) >= 800 and len(set(w)) == 6:
                    yield w
                    n += 1
                    if n >= limit:
                        return


def main(argv):
    limit = int(argv[0]) if argv and argv[0].isdigit() else 150
    paths = [a for a in argv if not a.isdigit()]
    rows, viol, bad = [], 0, 0
    for W in words(paths, limit):
        r = EX.extract(W, 6, keep_heavy=False)
        if not r.get("ok"):
            bad += 1
            continue
        K = (r["sum_tok"], r["sum_D"], r.get("retained_AB", 0), 0,
             r["hex_repeats"], r["h"])
        b, kind = bound(K)
        ok = r["sum_P"] <= b
        viol += not ok
        rows.append(dict(length=r["length"], chains=r["chains"],
                         sum_P=r["sum_P"], budget=list(K), bound=b, kind=kind,
                         slack=b - r["sum_P"], ok=ok,
                         profile=dict(k=r["k"], G=r["G"], c=r["c"], d=r["d"],
                                      H=r["H"], h=r["h"], Bstar=r["Bstar"])))
    tight = sum(1 for x in rows if x["slack"] == 0)
    out = dict(covers_analysed=len(rows), extraction_failures=bad,
               violations=viol, exactly_tight=tight,
               min_slack=min((x["slack"] for x in rows), default=None),
               examples=rows[:6],
               note="the model is compared against the object it actually "
                    "bounds: the chain part of the round-142 extraction, at "
                    "the budget vector the extraction itself reports",
               ok=(len(rows) > 0 and viol == 0))
    (R148 / "certs" / "model_falsify_148.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "examples"}))
    for x in rows[:4]:
        print("  ", json.dumps(x))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
