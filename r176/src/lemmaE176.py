#!/usr/bin/env python3
"""Round 176 -- falsification test of Lemma E (proved symbolically in the report):
no row of ANY length / omission set can follow or precede a complete phi-chain of n-2
full rows in a ModelTrail.  Chain = identity, phi(identity), ... (WLOG by relabelling).
Uses checker A (direct).  usage: lemmaE176.py n [n ...]"""
import sys, os
from itertools import permutations, combinations
sys.path.insert(0, os.path.dirname(__file__))
from checkA176 import CheckerA
def phi(n, s): return s[1:n - 2] + (s[0],) + s[n - 2:]
for n in map(int, sys.argv[1:]):
    A = CheckerA(n)
    chain = [(tuple(range(n)), n - 1, ())]
    for _ in range(n - 3): chain.append((phi(n, chain[-1][0]), n - 1, ()))
    assert A.trail(chain)[0]
    def all_rows(p):
        for l in range(1, n):
            inner = list(range(1, l - 1))
            for k in range(len(inner) + 1):
                for om in combinations(inner, k):
                    yield (p, l, om)
    beta = A.beta(chain[-1]); after = 0; after_ok = 0
    for t in permutations([c for c in range(n) if c not in beta]):
        for r in all_rows(beta + t):
            after += 1; after_ok += A.trail(chain + [r])[0]
    alpha = chain[0][0][:n - 3]; before = 0; before_ok = 0
    for p in permutations(range(n)):
        for r in all_rows(p):
            if A.beta(r) == alpha:
                before += 1; before_ok += A.trail([r] + chain)[0]
    print(f"n={n}: rows after complete chain tried {after}, legal {after_ok}; rows before tried {before}, legal {before_ok}")
