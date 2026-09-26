#!/usr/bin/env python3
"""Round 177 -- small-n probe for the one configuration the C1 accounting leaves open at
n = 6: a COMPLETE long block (n-2 rows of length n-1 on all gaps of one frame, exactly
one of them marked) flanked on both sides by rows of charge >= 2 and length >= 2.

Block: first row starts at the identity (WLOG); each step is phi or psi (the only
long-to-long transitions, R175 Lemma 2); exactly one row carries one interior omission.
x: every row with beta(x) = alpha(first) of length >= 2, charge >= 2; y likewise after.
Uses checker A for the search and checker B to re-check any hit.
usage: block177.py n [n ...]"""
import os, sys
from itertools import permutations, combinations, product
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "r176", "src"))
from checkA176 import CheckerA
from checkB176 import CheckerB


def phi(n, s): return s[1:n - 2] + (s[0],) + s[n - 2:]
def psi(n, s): return s[1:n - 2] + (s[0],) + (s[n - 1], s[n - 2])


for n in [int(a) for a in sys.argv[1:]]:
    A, B = CheckerA(n), CheckerB(n)
    k = n - 2
    blocks = []
    for steps in product((0, 1), repeat=k - 1):
        starts = [tuple(range(n))]
        for st in steps:
            starts.append((phi, psi)[st](n, starts[-1]))
        for i in range(k):
            for j in range(1, n - 2):
                rows = [(s, n - 1, (j,) if t == i else ()) for t, s in enumerate(starts)]
                if A.trail(rows)[0]:
                    blocks.append(rows)

    def all_rows(start, minlen=2):
        for l in range(minlen, n):
            inner = list(range(1, l - 1))
            for kk in range(len(inner) + 1):
                for om in combinations(inner, kk):
                    yield (start, l, om)
    hits = []
    for U in blocks:
        alpha = U[0][0][:n - 3]
        xs = [x for q in permutations(range(n)) if q[n - 3:] and True
              for x in all_rows(q) if A.charge(x) >= 2 and A.beta(x) == alpha and A.trail([x] + U)[0]]
        beta = A.beta(U[-1])
        ys = [y for t in permutations([c for c in range(n) if c not in beta]) for y in all_rows(beta + t)
              if A.charge(y) >= 2 and A.trail(U + [y])[0]]
        for x in xs:
            for y in ys:
                if A.disjoint(x, y):
                    assert B.trail([x] + U + [y])[0]
                    hits.append((A.charge(x), A.charge(y), U))
    print(f"n={n}: complete long blocks with exactly one mark: {len(blocks)}; "
          f"flanked by length>=2, charge>=2 rows on both sides: {len(hits)}; charge pairs {sorted({(a, b) for a, b, _ in hits})}")
