#!/usr/bin/env python3
"""Round 162 Phase 18/16 -- exhaustion over ALL small-n covers.

UNIVERSE.  Every word over the n-letter alphabet of length L, for
n = 3 and L = 9 .. LMAX.  The universe size is exactly sum_L n^L; every word
is generated, no sampling, no symmetry quotient, no pruning beyond discarding
words that are not covers (which are not in the theorem's domain).

For every cover W in the universe:

  T1  the Phi iteration terminates
  T2  it terminates within |W| - (n! + n - 1) non-fixed steps
  T3  the fixed point W* is a cover
  T4  |W*| <= |W|
  T5  W* satisfies the fixed-representative condition (L5 a/b/c, trimmed)
  T6  no length ever increases along the trajectory

A failure of any of these would refute the node.  The search also records the
set of DISTINCT fixed representatives reached, and their lengths, so that the
claim `min over covers is attained at a fixed point' can be inspected directly.
"""
from __future__ import annotations
import itertools, json, sys, time
from collections import Counter
from math import factorial
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "r156" / "src"))
import extract156 as X                                            # noqa: E402
from fixedrep162 import iterate, audit_fixed_point                # noqa: E402


def covers(n, alpha, L):
    """Every word of length L over `alpha` that is a cover."""
    need = {"".join(p) for p in itertools.permutations(alpha)}
    out = []
    for t in itertools.product(alpha, repeat=L):
        w = "".join(t)
        seen = set()
        for i in range(L - n + 1):
            v = w[i:i + n]
            if len(set(v)) == n:
                seen.add(v)
        if seen == need:
            out.append(w)
    return out


def main(LMAX=14):
    t0 = time.time()
    n, alpha = 3, "123"
    N = factorial(n)
    floor = N + n - 1
    st, bad = Counter(), []
    fps = Counter()
    universe = 0
    for L in range(N + n - 1, LMAX + 1):
        universe += len(alpha) ** L
        cs = covers(n, alpha, L)
        st[f"covers_len_{L}"] = len(cs)
        for W in cs:
            st["covers"] += 1
            Ws, lens, steps, b = iterate(W, n, alpha)
            b += audit_fixed_point(Ws, n, alpha)
            if not X.is_cover(Ws, n, alpha):
                b.append("T3 fixed point is not a cover")
            if len(Ws) > len(W):
                b.append("T4 fixed point is longer")
            if any(lens[i + 1] > lens[i] for i in range(len(lens) - 1)):
                b.append("T6 a step increased the length")
            if steps > max(0, len(W) - floor):
                b.append(("T2 iteration bound exceeded", steps,
                          len(W) - floor))
            if b:
                st["failures"] += 1
                if len(bad) < 6:
                    bad.append(dict(W=W, failures=[str(x) for x in b][:4]))
            st["total_steps"] += steps
            st["max_steps"] = max(st["max_steps"], steps)
            if len(Ws) < len(W):
                st["shortened"] += 1
            fps[Ws] += 1
        print(f"  L={L}: {len(alpha) ** L:,} words, {len(cs):,} covers, "
              f"failures so far {st['failures']}", flush=True)
    out = dict(seconds=round(time.time() - t0, 1), n=n, LMAX=LMAX,
               universe_size=universe, exhaustive=True,
               symmetry_quotient="none", pruning="none (non-covers are "
                                                 "outside the theorem domain)",
               stats=dict(st),
               distinct_fixed_representatives=len(fps),
               fixed_representative_lengths=dict(
                   Counter(len(w) for w in fps)),
               shortest_fixed_representative=min((len(w) for w in fps),
                                                 default=None),
               failures=bad, ok=(st["failures"] == 0))
    (ROOT / "r162" / "certs" / "exhaust_162.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("stats",)}, ensure_ascii=False, indent=1))
    print("covers:", st["covers"], "max steps:", st["max_steps"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 14))
