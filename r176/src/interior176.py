#!/usr/bin/env python3
"""Round 176 -- S2 probe: longest full-row run with a NON-full row on BOTH sides.

Lemma E (proved, r176 report) gives <= n-3 for a run with at least one non-full
neighbour.  Question for S2: is an interior run (non-full rows on both sides) <= n-4?
WLOG (relabelling) the run is the phi-chain p, phi p, ..., phi^{k-1} p, p = identity.
x: every row (start, length l, omitted interior set) with beta(x) = alpha(p) and charge
<= cmax;  y: every row with alpha(y.start) = beta(phi^{k-1} p) and charge <= cmax.
Reports, for k = n-3, whether some x, y make x R y a ModelTrail, and the minimal
charge(x) + charge(y) over such pairs.
usage: interior176.py n cmax"""
import sys
from itertools import permutations, combinations
n, cmax = int(sys.argv[1]), int(sys.argv[2])
def F(s): return s[1:n - 1] + (s[0], s[n - 1])
def Finv(s): return (s[n - 2],) + s[:n - 2] + (s[n - 1],)
def Rinv(s): return (s[n - 1],) + s[:n - 1]
def hexrep(s): return min(s[i:] + s[:i] for i in range(n))
def phi(s): return s[1:n - 2] + (s[0],) + s[n - 2:]
def row(p, l, om=()):
    st = [p]
    for _ in range(n - 2): st.append(F(st[-1]))
    return dict(p=p, l=l, om=om, ch=(n - 1 - l) + len(om), block=min(st), beta=Rinv(st[l - 1])[3:],
                vis=frozenset(hexrep(st[i]) for i in range(l) if i not in om))
def variants(start):
    for l in range(max(1, n - 1 - cmax), n):
        inner = list(range(1, l - 1))
        for k in range(0, cmax - (n - 1 - l) + 1):
            for om in combinations(inner, k):
                yield row(start, l, om)
def ok(a, b): return a["block"] != b["block"] and not (a["vis"] & b["vis"])
p = tuple(range(n))
for k in (n - 3, n - 4):
    R = [row(p, n - 1)]
    for _ in range(k - 1): R.append(row(phi(R[-1]["p"]), n - 1))
    alpha = p[:n - 3]
    xs = []
    for t in permutations([c for c in range(n) if c not in alpha]):
        last = (t[1], t[2]) + alpha + (t[0],)          # last state l with l_3..l_{n-1} = alpha
        for l in range(max(1, n - 1 - cmax), n):
            s = last
            for _ in range(l - 1): s = Finv(s)
            for x in variants(s):
                if x["l"] == l and x["beta"] == alpha and x["ch"] >= 1 and all(ok(x, r) for r in R):
                    xs.append(x)
    beta = R[-1]["beta"]
    ys = [y for t in permutations([c for c in range(n) if c not in beta]) for y in variants(beta + t)
          if y["ch"] >= 1 and all(ok(y, r) for r in R)]
    pairs = [(x["ch"] + y["ch"], x["ch"], y["ch"]) for x in xs for y in ys if ok(x, y)]
    print(f"n={n} cmax={cmax} run k={k}: #x={len(xs)} #y={len(ys)} valid x R y: {len(pairs)}; "
          f"min charge(x)+charge(y) = {min(pairs)[0] if pairs else None}; "
          f"charge pairs seen {sorted(set((a, b) for _, a, b in pairs))}")
