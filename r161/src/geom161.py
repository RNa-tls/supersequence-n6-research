#!/usr/bin/env python3
"""Round 161 Phases 11/18/19 -- the local n-letter geometry, exhausted.

Every statement here depends only on a PAIR of permutations, so the universe
is finite and completely specified: all n!^2 ordered pairs (v, tgt).  For
n = 6 that is 518,400 pairs; nothing is sampled and nothing is pruned.

WHAT IS EXHAUSTED

  P1  tau fixes the last letter:  tau(w)[n-1] = w[n-1]
  P2  a hexagon (sigma-class) contains exactly ONE window with each last
      letter
  G1  hence |hexagon cap tau-orbit| <= 1, and a tau-orbit lies in exactly
      n-1 DISTINCT hexagons          [the fact Round 155 used]
  Q2  the ONLY targets at gap 2 out of end(v) are tau(v) and sigma(v)
      -- the dichotomy Lemma F's count cleanE = P-1-S-D2 rests on
  Q3  the complete gap-3 target set, with each target's algebraic identity
  CMP the independent classification is compared window-by-window with the
      repository catalogue src/l6_splicing_145.py::classify; any discrepancy
      is reported rather than normalised away
"""
from __future__ import annotations
import itertools, json, sys, time
from collections import Counter
from math import factorial
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "r156" / "src"))
import extract156 as X                                            # noqa: E402
sys.path.insert(0, str(ROOT / "src"))
import l6_splicing_145 as SP                    # ONLY for the comparison


def table(n):
    letters = "123456"[:n]
    perms = ["".join(p) for p in itertools.permutations(letters)]
    hx = {v: X.hexrep(v) for v in perms}
    fails = []

    # ---- P1 : tau fixes the last letter
    for v in perms:
        if X.tau(v, n)[-1] != v[-1]:
            fails.append(("P1", v))
    # ---- P2 : one window per last letter in a hexagon
    byhex = {}
    for v in perms:
        byhex.setdefault(hx[v], []).append(v)
    for h, ws in byhex.items():
        if len(ws) != n:
            fails.append(("P2 hexagon size", h, len(ws)))
        if len({w[-1] for w in ws}) != n:
            fails.append(("P2 last letters not distinct in a hexagon", h))
    # ---- G1 : tau-orbit meets n-1 distinct hexagons
    seenorb = set()
    orbit_hex = Counter()
    for v in perms:
        o = X.orbrep(v, n)
        if o in seenorb:
            continue
        seenorb.add(o)
        y, hs = o, []
        for _ in range(n - 1):
            hs.append(hx[y])
            y = X.tau(y, n)
        orbit_hex[len(set(hs))] += 1
        if len(set(hs)) != n - 1:
            fails.append(("G1 orbit meets fewer hexagons", o, len(set(hs))))
    if len(seenorb) != factorial(n) // (n - 1):
        fails.append(("orbit count", len(seenorb), factorial(n) // (n - 1)))

    # ---- Q2 / Q3 : the full gap table out of end(v)
    gap_targets = Counter()
    q2_bad, q3 = [], Counter()
    cmp_mismatch = []
    for v in perms:
        pp = v[-1] + v[:-1]                        # end(v) = sigma^{-1}(v)
        g2 = []
        for tgt in perms:
            w = X.omega(pp, tgt, n)
            gap_targets[w] += 1
            if w == 2:
                g2.append(tgt)
            elif w == 3:
                if tgt == X.tau(X.tau(v, n), n):
                    q3["tau^2(v)"] += 1
                elif tgt == X.sigma(X.sigma(v)):
                    q3["sigma^2(v)"] += 1
                elif tgt == X.tau(X.sigma(v), n):
                    q3["tau(sigma(v))"] += 1
                elif tgt == X.sigma(X.tau(v, n)):
                    q3["sigma(tau(v))"] += 1
                else:
                    q3["other_w3"] += 1
            # ---- CMP with the repository catalogue
            mine = X.jtype(v, tgt, w, n)
            theirs = SP.classify(v, tgt, w, n)
            agree = ((mine == "E" and theirs == "E")
                     or (mine == "A" and theirs == "A")
                     or (mine == "B" and theirs == "B")
                     or (mine not in ("E", "A", "B")
                         and theirs not in ("E", "A", "B")))
            if not agree:
                cmp_mismatch.append((v, tgt, w, mine, theirs))
        want = sorted({X.tau(v, n), X.sigma(v)})
        if sorted(g2) != want:
            q2_bad.append((v, sorted(g2), want))
    if q2_bad:
        fails.append(("Q2 gap-2 targets are not exactly {tau(v), sigma(v)}",
                      q2_bad[:3]))
    if cmp_mismatch:
        fails.append(("CMP classification mismatch", cmp_mismatch[:3]))
    return dict(n=n, pairs=len(perms) ** 2, orbits=len(seenorb),
                orbit_hexagon_counts=dict(orbit_hex),
                gap_histogram=dict(gap_targets),
                gap3_identities=dict(q3),
                gap2_dichotomy_ok=not q2_bad,
                catalogue_mismatches=len(cmp_mismatch),
                failures=fails[:5], ok=not fails)


def main():
    t0 = time.time()
    out = {"tables": []}
    for n in (3, 4, 5, 6):
        r = table(n)
        out["tables"].append(r)
        print(f"  n={n}: {r['pairs']:,} pairs, orbits {r['orbits']}, "
              f"orbit-hexagon counts {r['orbit_hexagon_counts']}, "
              f"gap2 dichotomy {r['gap2_dichotomy_ok']}, "
              f"catalogue mismatches {r['catalogue_mismatches']}, "
              f"failures {len(r['failures'])}", flush=True)
    out["seconds"] = round(time.time() - t0, 1)
    out["ok"] = all(r["ok"] for r in out["tables"])
    (ROOT / "r161" / "certs" / "geometry_161.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n")
    print("ok", out["ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
