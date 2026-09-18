#!/usr/bin/env python3
"""Round 170 -- derive the census-safe upper bound S(K) from the census.

S(K) is the largest value that may be certified for K with every exposed row
still strictly closed under the CURRENT (P1)-closed rule system.  It is
derived by binary search over the census itself, not by taking a historical
capacity and adding slack: the historical value is printed afterwards as a
diagnostic and plays no part in choosing S.

Soundness.  A certificate proving cap(K) <= S is a valid proof object whatever
S is, and the census is then run with S.  What has to be checked -- and is
checked here -- is that S still closes the rows, which is exactly the search
criterion.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r168" / "src"))
sys.path.insert(0, str(ROOT / "r169" / "src"))
from closure169 import ClosedSystem                              # noqa: E402
from recheck168 import parse, cellstr                            # noqa: E402

GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")
TARGETS = ["0|15|0|0|0|1", "0|18|2|0|0|0", "2|10|0|0|0|0", "3|5|0|0|0|0"]


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main():
    rows = json.loads((ROOT / "r152" / "certs"
                       / "verify_all_c152.json").read_text())["rows"]
    U = {parse(r["cell"]): r["cap"] for r in rows if r["status"] in GOOD}
    prows = json.loads((ROOT / "r152" / "certs"
                        / "verify_piece_c152.json").read_text())["rows"]
    PC = {(r["b"], r["d"], r["fp"], r["lp"]): r["cap"] for r in prows
          if r["status"] in GOOD}
    cov = json.loads((ROOT / "r169" / "certs" / "cover_169.json").read_text())
    sel = [parse(c) for c in cov["constructed"]["members"]]

    S = ClosedSystem()
    S.full()
    base = S.verdicts()
    S.apply(set())
    empty = S.verdicts()
    EX = sorted(k for k in base if base[k] == "STRICTLY_CLOSED"
                and empty[k] != "STRICTLY_CLOSED")
    EXS = set(EX)

    def closes_all(vals):
        S.apply(set(sel), values=vals)
        v = S.verdicts(EXS)
        return all(v[k] == "STRICTLY_CLOSED" for k in EX)

    out = []
    for cs in TARGETS:
        K = parse(cs)
        fb = 120 + K[2] + K[3] + K[4]
        exact = U.get(K) or PC.get((K[0], K[1], 0, 0))
        base_vals = {}
        lo, hi = exact, fb          # closes at exact, must fail at fallback
        ok_lo = closes_all({K: lo})
        ok_hi = closes_all({K: hi})
        if not ok_lo:
            out.append(dict(cell=cs, error="the exact value does not close "
                                           "the rows under this selection"))
            continue
        if ok_hi:
            best = hi
        else:
            while hi - lo > 1:
                mid = (lo + hi) // 2
                if closes_all({K: mid}):
                    lo = mid
                else:
                    hi = mid
            best = lo
        out.append(dict(cell=cs, certified_upper_bound_S=best,
                        analytic_fallback=fb,
                        historical_capacity_diagnostic=exact,
                        slack_S_minus_C=best - exact,
                        fallback_is_enough=best >= fb,
                        derivation="binary search over the (P1)-closed census: "
                                   "the largest value with every exposed row "
                                   "still strictly closed",
                        checked_rows=len(EX)))
        print(json.dumps(out[-1], ensure_ascii=False), flush=True)

    res = dict(
        inputs={p: sha(p) for p in ("r169/certs/cover_169.json",
                                    "r152/certs/verify_all_c152.json",
                                    "r152/certs/verify_piece_c152.json",
                                    "r163/src/hidden163.py")},
        selection=sorted(cellstr(K) for K in sel),
        exposed_rows=len(EX),
        note="S is derived from row closure alone; the historical capacity is "
             "reported only as a diagnostic and never chooses S",
        bounds=out)
    (ROOT / "r170" / "certs" / "safe_bounds_170.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
