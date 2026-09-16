#!/usr/bin/env python3
"""Round 162 Phase 15 -- Phi versus the left S_n action (H.wlog).

H.fixedrep and H.wlog are DIFFERENT normalisations of DIFFERENT objects:

  H.fixedrep  a REWRITING of the word W (re-spell at maximum overlap, trim),
              iterated to a fixed point.  It is not a group action: it does
              not relabel, rotate or conjugate, and it can SHORTEN the word.
  H.wlog      a left S_n RELABELLING, used inside the capacity search to fix
              the starting PORT of a chain at 123456.

They are nevertheless compatible, and this file proves and checks it:

  EQV   for every relabelling pi in S_n,   Phi(pi . W) = pi . Phi(W)
        hence  W is a fixed representative  <=>  pi . W is.

So the two normalisations commute and may be imposed simultaneously.  The
proof: relabelling is a bijection on windows that preserves position, so the
first-occurrence sequence of pi.W is pi applied termwise to that of W, in the
same order and at the same positions; and omega(pi a, pi b) = omega(a, b)
because the defining condition a[k:] = b[:n-k] is preserved.
"""
from __future__ import annotations
import itertools, json, random, sys, time
from collections import Counter
from math import factorial
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "r156" / "src"))
import extract156 as X                                            # noqa: E402
from fixedrep162 import Phi, iterate, inflate, audit_fixed_point   # noqa: E402


def relabel(W, alpha, perm):
    m = dict(zip(alpha, perm))
    return "".join(m[c] for c in W)


def check(W, n, alpha, perms):
    bad = Counter()
    base = Phi(W, n)
    for p in perms:
        Wp = relabel(W, alpha, p)
        if not X.is_cover(Wp, n, alpha):
            bad["relabel_lost_coverage"] += 1
            continue
        if len(Wp) != len(W):
            bad["relabel_changed_length"] += 1
        lhs = Phi(Wp, n)
        rhs = relabel(base, alpha, p)
        if lhs != rhs:
            bad["EQV_failed"] += 1
        # omega equivariance, on every selected pair
        sel = X.selected(W, n)
        selp = X.selected(Wp, n)
        if [i for i, _ in sel] != [i for i, _ in selp]:
            bad["selected_positions_moved"] += 1
        if [relabel(w, alpha, p) for _, w in sel] != [w for _, w in selp]:
            bad["selected_windows_not_relabelled"] += 1
        # fixed-representative status is preserved both ways
        f0 = (Phi(W, n) == W)
        f1 = (Phi(Wp, n) == Wp)
        if f0 != f1:
            bad["fixed_status_changed"] += 1
        bad["pairs"] += 1
    return bad


def main():
    t0 = time.time()
    rng = random.Random(1621621)
    sys.path.insert(0, str(ROOT / "r156" / "src"))
    import run156 as R                                            # noqa: E402
    import passes156 as P3                                        # noqa: E402
    raw = json.loads((ROOT / "outputs" /
                      "rr_nr6_n5_minima_142.json").read_text())
    w5 = sorted({e["word"] for e in raw if isinstance(e, dict) and "word" in e})
    W6 = (ROOT / "data" / "verified_872_witness.txt").read_text().strip()
    tot = Counter()
    rows = []
    for n, alpha, words, exhaustive in (
            (3, "123", P3.n3_family()[:20], True),
            (4, "1234", [R.W4], True),
            (5, "01234", w5[:3], True),
            (6, "123456", [W6], False)):
        allp = ["".join(p) for p in itertools.permutations(alpha)]
        perms = allp if exhaustive else rng.sample(allp, 120)
        st = Counter()
        pool = list(words)
        for W in words:
            for _ in range(4):
                V, wid = inflate(W, n, rng)
                if wid and X.is_cover(V, n, alpha):
                    pool.append(V)
        for W in pool:
            st.update(check(W, n, alpha, perms))
        rows.append(dict(n=n, words=len(pool), group_elements=len(perms),
                         exhaustive_over_S_n=exhaustive, stats=dict(st)))
        tot.update(st)
        print(f"  n={n}: {len(pool)} words x {len(perms)} relabellings "
              f"({'ALL of S_n' if exhaustive else 'sampled'}) -> "
              f"{st['pairs']:,} pairs, failures "
              f"{sum(v for k, v in st.items() if k != 'pairs')}", flush=True)
    out = dict(seconds=round(time.time() - t0, 1), rows=rows,
               totals=dict(tot),
               ok=all(v == 0 for k, v in tot.items() if k != "pairs"))
    (ROOT / "r162" / "certs" / "equivariance_162.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print("total pairs", tot["pairs"], "ok", out["ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
