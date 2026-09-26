#!/usr/bin/env python3
"""Round 180 -- the explicit walk family refuting global LS (Theorem W of r180 report).

Special-c_n walk: first row T at the identity p_0 = c_1..c_n; then periods of
(T row, n-4 full rows).  Next start after a full row = phi(p); after a T row = the exit
D+wvz, tm(s) = (s[n-2],) + s[:n-4] + (s[n-3], s[n-4], s[n-1]).  After K = floor((n-3)/3)
periods one more FULL row (the start of period K) is appended.
Claims checked (proved symbolically in the report, re-checked here):
  (S1) rows = (n-3) K + 1, charge = 2K, every row has special c_n;
  (S2) with N = n-1, c_0 = n-5 and cyclic positions of W_0 = (0, 1, ..., n-2):
       the T-row word W_{j+1} = W_j with the letters at positions c_j, c_j+1 swapped,
       c_j = c_0 - 3j (mod N), and x_j (the travelling letter of period j) = W_0[c_0+1-3j];
  (S3) all rows of period j contain the same frame E_j = W_j minus x_j;
  (S4) all cyclic words distinct  <=>  ModelTrail (Lemma U, common special c_n);
  (S5) ModelTrail re-checked by checker A (direct, n <= 14) and checker B (all n tested).
Also records the full length J(n) of the periodic walk (empirical, growth180.py).
usage: family180.py nmin nmax"""
import json, os, sys
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "r176", "src"))
from checkA176 import CheckerA
from checkB176 import CheckerB


def build(n):
    phi = lambda s: s[1:n - 2] + (s[0],) + s[n - 2:]
    tm = lambda s: (s[n - 2],) + s[:n - 4] + (s[n - 3], s[n - 4], s[n - 1])
    K = (n - 3) // 3
    s = tuple(range(n)); rows = []; periods = []
    for j in range(K):
        per = [(s, n - 3, ())]
        s = tm(s)
        for _ in range(n - 4):
            per.append((s, n - 1, ())); s = phi(s)
        periods.append(per); rows += per
    rows.append((s, n - 1, ()))
    return K, rows, periods


def cyc_from(word, anchor):
    i = word.index(anchor); return word[i:] + word[:i]


def check(n):
    K, rows, periods = build(n)
    N = n - 1
    out = dict(n=n, K=K, rows=len(rows), charge=2 * K)
    out["S1"] = len(rows) == (n - 3) * K + 1 and all(r[0][-1] == n - 1 for r in rows)
    # S2: track absolute cyclic arrangement of the T-row words
    W0 = list(range(N))
    ok2 = True; Wj = list(W0)
    for j in range(K):
        Tstart = periods[j][0][0][:N]
        # absolute arrangement must equal Wj up to rotation
        if cyc_from(list(Tstart), 0) != cyc_from(Wj, 0): ok2 = False
        cj = (n - 5 - 3 * j) % N
        xj = W0[(cj + 1) % N]
        if Wj[(cj + 1) % N] != xj: ok2 = False
        # S3: every row of the period contains E_j = W_j minus x_j (as cyclic words)
        Ej = [t for t in Wj if t != xj]
        for r in periods[j]:
            w = [t for t in r[0][:N] if t != xj]
            if cyc_from(w, Ej[0]) != cyc_from(Ej, Ej[0]): out["S3"] = False
        Wj[cj], Wj[(cj + 1) % N] = Wj[(cj + 1) % N], Wj[cj]
    out["S2"] = ok2
    out.setdefault("S3", True)
    words = [cyc_from(list(r[0][:N]), 0) for r in rows]
    out["S4"] = len(set(map(tuple, words))) == len(words)
    B = CheckerB(n)
    out["checkerB"] = B.trail(rows, 2 * K)[0]
    if n <= 14:
        out["checkerA"] = CheckerA(n).trail(rows, 2 * K)[0]
    out["C1_bound_at_2K"] = (n - 2) + (n - 3) * K
    return out


if __name__ == "__main__":
    lo, hi = int(sys.argv[1]), int(sys.argv[2])
    res = []
    for n in range(lo, hi + 1):
        o = check(n); res.append(o)
        print(o)
    json.dump(res, open(os.path.join(HERE, "..", "certs", "family180.json"), "w"), indent=1)
