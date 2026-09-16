#!/usr/bin/env python3
"""Round 162 Phases 10/17 -- the C3 bridge and its negative control.

Round 161 established that among the splice lemmas only clause

  C3   the reassigned edge is a SHORTEST connector out of the full-pass
       endpoint, i.e.  g_j = omega(end(v_{nu(i)}), q_{j+1})

uses the fixed-representative hypothesis, and exhibited covers on which C3
fails.  This file reproduces that independently and then closes the loop:

  1. take a cover W that is NOT a fixed representative;
  2. verify C3 FAILS on W  (and that the other clauses do not);
  3. normalise:  W* = Phi^m(W);
  4. verify the fixed-representative condition holds on W*;
  5. verify C3 now HOLDS on W*, together with every other clause;
  6. verify W* is still a cover and |W*| <= |W|.

Step 5 is the whole point of the node: it is what makes "WLOG a fixed
representative" legitimate rather than cosmetic.
"""
from __future__ import annotations
import json, random, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "r156" / "src"))
sys.path.insert(0, str(ROOT / "r161" / "src"))
import extract156 as X                                            # noqa: E402
from lemmas161 import build                                       # noqa: E402
from fixedrep162 import Phi, iterate, inflate, pad, audit_fixed_point  # noqa


def clauses(W, n):
    """Which lemma clauses fail on W (C3 evaluated unconditionally)."""
    r = build(W, n, require_cover=True, require_fixed=False)
    out = set()
    for f in r["failures"]:
        s = str(f)
        for c in ("A1", "A2", "A3", "A4", "A5", "B1", "B2", "B3",
                  "C1", "C2", "C3", "D1", "D2", "D3",
                  "E1", "E2", "E3", "E4", "F1", "F2", "F3", "F4", "G1"):
            if c in s:
                out.add(c)
    return out, r


def main():
    t0 = time.time()
    rng = random.Random(1620162)
    sys.path.insert(0, str(ROOT / "r156" / "src"))
    import run156 as R                                            # noqa: E402
    import passes156 as P3                                        # noqa: E402
    raw = json.loads((ROOT / "outputs" /
                      "rr_nr6_n5_minima_142.json").read_text())
    w5 = sorted({e["word"] for e in raw if isinstance(e, dict) and "word" in e})
    W6 = (ROOT / "data" / "verified_872_witness.txt").read_text().strip()
    seeds = ([(4, "1234", R.W4)] + [(5, "01234", w) for w in w5[:4]]
             + [(3, "123", w) for w in P3.n3_family()[:10]]
             + [(6, "123456", W6)])

    st, bad, ex = Counter(), [], []
    for n, alpha, W0 in seeds:
        for trial in range(60):
            V, wid = inflate(W0, n, rng)
            if not wid or not X.is_cover(V, n, alpha):
                continue
            before, rb = clauses(V, n)
            st["non_fixed_candidates"] += 1
            if rb.get("fixed", True):
                st["still_fixed_after_inflate"] += 1
                continue
            st["non_fixed"] += 1
            # 2. C3 must fail, and it must be the ONLY thing that fails
            if "C3" not in before:
                st["C3_did_not_fail_before"] += 1
                if len(bad) < 6:
                    bad.append(dict(n=n, stage="before", broke=sorted(before)))
                continue
            st["C3_failed_before"] += 1
            if before != {"C3"}:
                st["other_clauses_also_failed_before"] += 1
                st["extra_" + "_".join(sorted(before - {"C3"}))] += 1
            # 3. normalise
            Ws, lens, steps, b = iterate(V, n, alpha)
            if b:
                st["normalisation_audit_failed"] += 1
                continue
            # 4/5/6
            fp = audit_fixed_point(Ws, n, alpha)
            after, ra = clauses(Ws, n)
            okall = (not fp and not after and ra.get("fixed") is True
                     and X.is_cover(Ws, n, alpha) and len(Ws) <= len(V))
            if okall:
                st["bridge_ok"] += 1
            else:
                st["bridge_failed"] += 1
                if len(bad) < 6:
                    bad.append(dict(n=n, stage="after", fp=[str(x) for x in fp],
                                    broke=sorted(after),
                                    fixed=ra.get("fixed"),
                                    len_before=len(V), len_after=len(Ws)))
            if len(ex) < 4:
                ex.append(dict(n=n, len_before=len(V), len_after=len(Ws),
                               steps=steps, broke_before=sorted(before),
                               broke_after=sorted(after),
                               fixed_after=ra.get("fixed")))
    out = dict(seconds=round(time.time() - t0, 1), stats=dict(st),
               examples=ex, failures=bad,
               ok=(st["bridge_failed"] == 0 and st["bridge_ok"] > 0
                   and st["C3_did_not_fail_before"] == 0
                   and st["normalisation_audit_failed"] == 0))
    (ROOT / "r162" / "certs" / "bridge_162.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "examples"},
                     ensure_ascii=False, indent=1)[:1600])
    for e in ex:
        print("  ", json.dumps(e, ensure_ascii=False))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
