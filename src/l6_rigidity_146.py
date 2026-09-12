#!/usr/bin/env python3
"""Round 146 — adversarial audit of the RIGIDITY step of the fixed-representative
reduction:

        |Phi(W)| = |W|   =>   W = Phi(W).

The proof has exactly four ingredients, each isolated and tested separately:

  (R1) g_j >= omega(q_j, q_{j+1}) for every consecutive pair of selected windows.
       If g_j < n the two windows overlap in n-g_j letters, forcing
       q_j[g_j:] = q_{j+1}[:n-g_j], so omega <= g_j; if g_j >= n then omega <= n <= g_j.
  (R2) |W| >= |W_trim| = n + sum g_j, and |Phi(W)| = n + sum omega_j.
  (R3) Equality therefore forces BOTH no trimming AND g_j = omega_j for all j.
  (R4) With every g_j = omega_j <= n, consecutive selected windows overlap or abut,
       so EVERY position of W_trim lies inside some selected window; hence W_trim
       is determined by the pair (selected sequence, gaps), and Phi(W) is built
       from exactly that pair.  So W = W_trim = Phi(W).

(R4) is the only step where a second word could sneak in, and it is exactly where
a gap > n would break the argument -- which equality forbids.  The test below
looks for a counterexample EXHAUSTIVELY over all words on three letters up to a
given length, and additionally checks, on every word it sees, that (R1) holds,
that positions are covered whenever all gaps <= n, and that a word with a gap > n
really does contain positions no selected window covers (so the hypothesis in
(R4) is not vacuous).
"""
from __future__ import annotations
import itertools, json, sys
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from l6_cleanroom_146 import omega                                    # noqa


def selected(W, n):
    seen, sel, pos = set(), [], []
    for i in range(len(W) - n + 1):
        w = W[i:i + n]
        if len(set(w)) == n and w not in seen:
            seen.add(w)
            sel.append(w)
            pos.append(i)
    return sel, pos


def phi(W, n):
    sel, _ = selected(W, n)
    out = sel[0]
    for j in range(1, len(sel)):
        out += sel[j][n - omega(sel[j - 1], sel[j]):]
    return out


def audit_word(W, n, fails, stats):
    sel, pos = selected(W, n)
    if len(sel) != factorial(n):
        return
    stats["covers"] += 1
    gaps = [pos[j + 1] - pos[j] for j in range(len(sel) - 1)]
    oms = [omega(sel[j], sel[j + 1], ) for j in range(len(sel) - 1)]
    # (R1)
    for j in range(len(gaps)):
        if gaps[j] < oms[j]:
            fails.append(("R1 violated", W, j, gaps[j], oms[j]))
    # (R2)
    Wt = W[pos[0]:pos[-1] + n]
    if len(Wt) != n + sum(gaps):
        fails.append(("R2 trim length", W))
    F = phi(W, n)
    if len(F) != n + sum(oms):
        fails.append(("R2 phi length", W))
    if len(F) > len(W):
        fails.append(("Phi lengthened", W))
    # (R4) coverage, and non-vacuity of its hypothesis
    covpos = set()
    for j, p in enumerate(pos):
        covpos |= set(range(p - pos[0], p - pos[0] + n))
    allcov = covpos == set(range(len(Wt)))
    if max(gaps, default=0) <= n and not allcov:
        fails.append(("R4 coverage fails with all gaps <= n", W))
    if max(gaps, default=0) > n:
        stats["has_gap_gt_n"] += 1
        if allcov:
            stats["gap_gt_n_but_covered"] += 1
    # ---- the implication itself
    if len(F) == len(W):
        stats["equal_length"] += 1
        if F != W:
            fails.append(("RIGIDITY COUNTEREXAMPLE", W, F))
        else:
            stats["equal_length_and_equal"] += 1
            if max(gaps, default=0) != max(oms, default=0) or gaps != oms:
                fails.append(("equal length but a gap exceeds omega", W))
            if pos[0] != 0 or pos[-1] + n != len(W):
                fails.append(("equal length but trimming was possible", W))


def exhaustive_n3(maxlen=13):
    n, alpha = 3, "012"
    fails, stats = [], {"words": 0, "covers": 0, "equal_length": 0,
                        "equal_length_and_equal": 0, "has_gap_gt_n": 0,
                        "gap_gt_n_but_covered": 0}
    for L in range(n, maxlen + 1):
        for t in itertools.product(alpha, repeat=L):
            W = "".join(t)
            stats["words"] += 1
            audit_word(W, n, fails, stats)
    return fails, stats


if __name__ == "__main__":
    ml = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    fails, stats = exhaustive_n3(ml)
    extra = {"n4_n5_n6_corpus": {}}
    for path, n in ((sys.argv[2] if len(sys.argv) > 2 else None, 4),):
        pass
    # also sweep any supplied word files (any n)
    for path in sys.argv[2:]:
        f2, s2 = [], {"words": 0, "covers": 0, "equal_length": 0,
                      "equal_length_and_equal": 0, "has_gap_gt_n": 0,
                      "gap_gt_n_but_covered": 0}
        import gzip
        op = gzip.open if path.endswith(".gz") else open
        with op(path, "rt") as fh:
            for line in fh:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                s2["words"] += 1
                audit_word(s, len(set(s)), f2, s2)
        extra["n4_n5_n6_corpus"][path.split("/")[-1]] = dict(stats=s2,
                                                            failures=len(f2))
        fails += f2
    res = dict(exhaustive_n3_maxlen=ml, n3_stats=stats, extra=extra,
               failures=len(fails), examples=[list(map(str, f)) for f in fails[:5]],
               rigidity_counterexamples=[list(map(str, f)) for f in fails
                                         if f[0] == "RIGIDITY COUNTEREXAMPLE"][:5],
               ok=not fails)
    (ROOT / "outputs" / "rr_l6_rigidity_146.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1)[:2200])
