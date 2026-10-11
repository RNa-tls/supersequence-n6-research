#!/usr/bin/env python3
"""Minimal standalone superpermutation check (no shared code): alphabet size n, every length-n
window that is a permutation is collected; success iff all n! permutations occur."""
import sys, math
w = open(sys.argv[1]).read().strip()
syms = sorted(set(w)); n = len(syms)
found = set()
for i in range(len(w) - n + 1):
    t = w[i:i + n]
    if len(set(t)) == n: found.add(t)
print(f"n={n} length={len(w)} distinct_permutation_windows={len(found)} n!={math.factorial(n)} OK={len(found) == math.factorial(n)}")
