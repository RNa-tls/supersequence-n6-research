#!/usr/bin/env python3
"""Round 159 Phase 4 -- the local geometry of a dirty joint, exhaustively.

For every source permutation v and EVERY target window tgt the connector
leaving the full-pass endpoint  p' = end(v) = sigma^{-1}(v)  is the shortest
one, of gap  w = omega(p', tgt).  This file enumerates the complete finite
table of (v, tgt) pairs for n = 4, 5, 6 -- n!^2 pairs, no sampling -- and
records for each

    the gap w,
    the algebraic identity of tgt relative to v,
    hex(tgt) == hex(v)?           (does the joint stay in the source hexagon)
    orb(tgt) == orb(v)?           (does it stay in the tau-orbit)
    the literal hidden windows of the connector.

The facts SAME-HEX needs are then read off the table rather than off a
production label:

  A   w = 2 and tgt = sigma(v)     -> SAME hexagon, hidden = [v]
  B   w = 3 and tgt = sigma^2(v)   -> SAME hexagon, hidden = [v, sigma(v)]
  E   w = 2 and tgt = tau(v)       -> DIFFERENT hexagon, hidden = []

and the table also shows exactly which OTHER connectors land in the source
hexagon (they only make R_int larger, so they are safe for the lower bound).
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


def name_of(v, tgt, w, n):
    """Algebraic identity of tgt relative to v, computed not looked up."""
    s, t = X.sigma, (lambda z: X.tau(z, n))
    cands = {}
    x = v
    for i in range(n):
        cands.setdefault(x, f"sigma^{i}")
        x = s(x)
    x = v
    for i in range(n - 1):
        cands.setdefault(x, f"tau^{i}")
        x = t(x)
    for lab, z in (("tau(sigma(v))", t(s(v))), ("sigma(tau(v))", s(t(v))),
                   ("tau^2(v)", t(t(v))), ("sigma^2(v)", s(s(v))),
                   ("sigma^3(v)", s(s(s(v))))):
        cands.setdefault(z, lab)
    return cands.get(tgt, "other")


def table(n):
    perms = ["".join(p) for p in itertools.permutations("123456"[:n])]
    hx = {v: X.hexrep(v) for v in perms}
    ob = {v: X.orbrep(v, n) for v in perms}
    rows = Counter()
    same_hex_by_type = Counter()
    checks = []
    for v in perms:
        pp = v[-1] + v[:-1]                       # end(v) = sigma^{-1}(v)
        for tgt in perms:
            w = X.omega(pp, tgt, n)
            ty = X.jtype(v, tgt, w, n)
            same_h = hx[tgt] == hx[v]
            same_o = ob[tgt] == ob[v]
            hid = tuple(X.hidden_windows(pp, tgt, w, n))
            key = (w, ty, same_h, same_o, len(hid))
            rows[key] += 1
            if same_h:
                same_hex_by_type[ty] += 1
            if ty == "A":
                checks.append(("A", tgt == X.sigma(v), same_h, w == 2,
                               list(hid) == [v]))
            elif ty == "B":
                checks.append(("B", tgt == X.sigma(X.sigma(v)), same_h, w == 3,
                               list(hid) == [v, X.sigma(v)]))
            elif ty == "E":
                checks.append(("E", tgt == X.tau(v, n), not same_h, w == 2,
                               list(hid) == []))
    bad = [c for c in checks if not all(c[1:])]
    per_source = Counter()
    for v in perms:
        pp = v[-1] + v[:-1]
        cnt = Counter()
        for tgt in perms:
            cnt[X.jtype(v, tgt, X.omega(pp, tgt, n), n)] += 1
        per_source[tuple(sorted(cnt.items()))] += 1
    return dict(n=n, pairs=len(perms) ** 2,
                profile={str(k): v for k, v in sorted(rows.items())},
                same_hex_by_type=dict(same_hex_by_type),
                per_source_profiles={str(k): v
                                     for k, v in per_source.items()},
                A_B_E_checks=len(checks), A_B_E_failures=len(bad),
                failures=bad[:4], ok=not bad)


def main():
    t0 = time.time()
    out = {"tables": []}
    for n in (4, 5, 6):
        r = table(n)
        out["tables"].append(r)
        print(f"  n={n}: {r['pairs']:,} pairs, A/B/E checks "
              f"{r['A_B_E_checks']:,}, failures {r['A_B_E_failures']}, "
              f"same-hex by type {json.dumps(r['same_hex_by_type'])}",
              flush=True)
    out["seconds"] = round(time.time() - t0, 1)
    out["ok"] = all(r["ok"] for r in out["tables"])
    (ROOT / "r159" / "certs" / "geometry_159.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print("ok", out["ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
