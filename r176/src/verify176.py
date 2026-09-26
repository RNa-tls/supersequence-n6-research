#!/usr/bin/env python3
"""Round 176 -- S1-L witness family, differential test of checkers A/B, mutation suite.

S1-L family (Theorem L of r176/CHARGE2_CAPACITY_REPORT.md), n >= 5, symbols c_1..c_n:
  p  = c_1 .. c_n                                   (T = short row, length n-3, charge 2)
  R  = phi^{-(n-3)} p, ..., phi^{-1} p              (n-3 full rows)
  q0 = c_{n-1} c_1 .. c_{n-4} c_{n-2} c_{n-3} c_n   (exit D+wvz)
  R' = q0, phi q0, ..., phi^{n-4} q0                (n-3 full rows)
  trail = R, T, R'   (2n-5 rows, total charge 2)
usage: verify176.py"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
from checkA176 import CheckerA
from checkB176 import CheckerB


def phi(n, s): return s[1:n - 2] + (s[0],) + s[n - 2:]
def phiinv(n, s): return (s[n - 3],) + s[:n - 3] + s[n - 2:]


def family(n):
    p = tuple(range(n))                               # c_i = i - 1
    c = lambda i: i - 1
    R = []
    s = p
    for _ in range(n - 3):
        s = phiinv(n, s); R.append((s, n - 1, ()))
    R.reverse()
    T = (p, n - 3, ())
    q = (c(n - 1),) + tuple(c(i) for i in range(1, n - 3)) + (c(n - 2), c(n - 3), c(n))
    Rp = []
    for _ in range(n - 3):
        Rp.append((q, n - 1, ())); q = phi(n, q)
    return R + [T] + Rp


def r175_counterexample(n):
    A = tuple(range(n - 3)); x, y, z = n - 3, n - 2, n - 1
    w = [(A + (x, y, z), n - 2, ()), (A + (z, y, x), n - 2, ())]
    q = A + (y, x, z)
    for k in range(n - 3):
        w.append((q, n - 1, (n - 3 - k,))); q = phi(n, q)
    return w


def mutants(n, W):
    """(name, rows, gmax) -- every one must be rejected."""
    a = n - 3                                          # index of T in W
    out = []
    T = W[a]
    # endpoint off-by-one on the charge-2 row
    out.append(("T length +1 (n-2)", W[:a] + [(T[0], n - 2, ())] + W[a + 1:], 2))
    if n - 4 >= 1:
        out.append(("T length -1 (n-4), charge 3", W[:a] + [(T[0], n - 4, ())] + W[a + 1:], 2))
    # charge total
    out.append(("extra omission on a full row (charge 3)", [(W[0][0], n - 1, (1,))] + W[1:], 2))
    # omission not interior (position 0 / last)
    out.append(("omission at position 0", [(W[0][0], n - 1, (0,))] + W[1:], 3))
    out.append(("omission at last position", [(W[0][0], n - 1, (n - 2,))] + W[1:], 3))
    # frame orientation: swap the last two symbols (a <-> special) of a row
    for k in (a - 1, a + 1):
        s = W[k][0]
        out.append((f"orientation swap row {k}", W[:k] + [(s[:n - 2] + (s[n - 1], s[n - 2]), n - 1, ())] + W[k + 1:], 2))
    # illegal but compatible exits of T (table: D+vwz same block, D+zvw / D+zwv conflict)
    D = W[a + 1][0][:n - 3]; v, w_, z = T[0][n - 4], T[0][n - 3], T[0][n - 1]
    for name, tail in (("D+vwz", (v, w_, z)), ("D+zvw", (z, v, w_)), ("D+zwv", (z, w_, v))):
        q = D + tail
        Rp = []
        for _ in range(n - 3):
            Rp.append((q, n - 1, ())); q = phi(n, q)
        out.append((f"exit {name}", W[:a + 1] + Rp, 2))
    # non-compatible successor (alpha changed)
    s = W[a + 1][0]
    out.append(("alpha mismatch after T", W[:a + 1] + [(s[1:n - 1] + (s[0], s[n - 1]), n - 1, ())] + W[a + 2:], 2))
    # repeated class: complete either chain (Lemma E)
    out.append(("complete R' (n-2 rows)", W + [(phi(n, W[-1][0]), n - 1, ())], 2))
    out.append(("complete R (n-2 rows)", [(phiinv(n, W[0][0]), n - 1, ())] + W, 2))
    # duplicated row
    out.append(("duplicate row", W[:1] + W, 2))
    return out


def mutants_marked(n, W):
    out = []
    for k in range(2, len(W)):
        om = W[k][2][0]
        for d in (-1, 1):
            if 0 < om + d < n - 2:
                out.append((f"R175 cex: omission row {k} shifted {d:+d}", W[:k] + [(W[k][0], n - 1, (om + d,))] + W[k + 1:], None))
    out.append(("R175 cex: second loop phase (F applied)", [W[0], ((W[1][0][1:n - 1] + (W[1][0][0], W[1][0][n - 1])), n - 2, ())] + W[2:], None))
    return out


def random_row(n, rng):
    p = list(range(n)); rng.shuffle(p)
    l = rng.randint(1, n - 1)
    inner = list(range(1, l - 1))
    om = tuple(sorted(rng.sample(inner, rng.randint(0, min(2, len(inner)))))) if inner else ()
    return (tuple(p), l, om)


def frame_kind(B, x, y):
    X, Y = B.rep(x), B.rep(y)
    if X["s"] == Y["s"]: return "same_special"
    Kx = [t for t in X["W"] if t != Y["s"]]; Ky = [t for t in Y["W"] if t != X["s"]]
    if B.canon(Kx) != B.canon(Ky): return "no_common_frame"
    return "frame_same_gap" if B.after(X["W"], Y["s"]) == B.after(Y["W"], X["s"]) else "frame_diff_gap"


def main():
    rng = random.Random(176)
    report = dict(family={}, differential={}, mutations={})
    ok_all = True
    for n in range(5, 15):
        A, B = CheckerA(n), CheckerB(n)
        W = family(n)
        ra, rb = A.trail(W, 2), B.trail(W, 2)
        ch = sum(A.charge(r) for r in W)
        report["family"][n] = dict(rows=len(W), charge=ch, A=ra, B=rb)
        good = ra[0] and rb[0] and len(W) == 2 * n - 5 and ch == 2
        ok_all &= good
        print(f"n={n}: family rows={len(W)} (2n-5={2*n-5}) charge={ch}  A={ra}  B={rb}")
        if n <= 10:
            res = []
            for name, rows, g in mutants(n, W):
                a_, b_ = A.trail(rows, g), B.trail(rows, g)
                res.append((name, a_, b_))
                if a_[0] or b_[0]:
                    ok_all = False; print("   MUTANT ACCEPTED:", name, a_, b_)
            Wc = r175_counterexample(n)
            assert A.trail(Wc)[0] and B.trail(Wc)[0]
            for name, rows, g in mutants_marked(n, Wc):
                a_, b_ = A.trail(rows, g), B.trail(rows, g)
                res.append((name, a_, b_))
                if a_[0] or b_[0]:
                    ok_all = False; print("   MUTANT ACCEPTED:", name, a_, b_)
            report["mutations"][n] = res
            print(f"   {len(res)} mutants, all rejected by both: {all(not a[0] and not b[0] for _, a, b in res)}")
    for n in range(5, 10):
        A, B = CheckerA(n), CheckerB(n)
        dis = com = conflicts = 0; cover = {}
        for _ in range(20000):
            x, y = random_row(n, rng), random_row(n, rng)
            if rng.random() < 0.5:                      # force compatibility half the time
                bx = A.beta(x); rest = [c for c in range(n) if c not in bx]; rng.shuffle(rest)
                y = (bx + tuple(rest), y[1], y[2])
            if rng.random() < 0.3:                      # force a shared frame often
                s = list(x[0]); i, j = n - 1, rng.randrange(n - 1); s[i], s[j] = s[j], s[i]
                y = (tuple(s), y[1], y[2])
            if rng.random() < 0.4:                      # random same-frame partner, random gap / phase
                W = list(x[0][:n - 1]); t = rng.choice(W); E = [c for c in W if c != t]
                g = rng.randrange(n - 2); Wy = E[:g] + [x[0][n - 1]] + E[g:]
                r = rng.randrange(n - 1); Wy = Wy[r:] + Wy[:r]
                y = (tuple(Wy) + (t,), y[1], y[2])
            kind = frame_kind(B, x, y); cover[kind] = cover.get(kind, 0) + 1
            conflicts += not A.disjoint(x, y)
            if A.disjoint(x, y) != B.disjoint(x, y): dis += 1
            if A.compatible(x, y) != B.compatible(x, y): com += 1
        report["differential"][n] = dict(pairs=20000, disjoint_disagreements=dis, compat_disagreements=com,
                                         conflicts=conflicts, branch_coverage=cover)
        ok_all &= dis == 0 and com == 0
        print(f"n={n}: differential A vs B on 20000 random pairs: disjoint disagreements {dis}, compat disagreements {com}; conflicts {conflicts}; branches {cover}")
    print("ALL OK" if ok_all else "FAILURES")
    json.dump(report, open(os.path.join(os.path.dirname(__file__), "..", "certs", "verify_176.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
