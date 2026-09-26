#!/usr/bin/env python3
"""Round 177 -- falsification checks for Lemma E1 and consistency of C1 with data.
(1) E1: every all-charge<=1 ModelTrail with EXACTLY one charge-1 row has <= n-2 rows
    (exhaustive from the identity start, marked model; uses R175 llsearch tables).
(2) C1 against the external certified n=7 table capTab (Superperm7/CapTab.lean, g<=36)
    and against the marked values computed in R176 (n=5..8, g<=2 or 3).
usage: checks177.py"""
import os, sys
from itertools import permutations
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "r175", "src"))
from llsearch175 import build
sys.setrecursionlimit(100000)
for n in (5, 6, 7, 8):
    info, *_ = build(n, True)
    best = {0: 0, 1: 0}
    def rec(beta, blocks, hexes, ones, depth):
        for q in permutations([c for c in range(n) if c not in beta]):
            p = beta + q; b, rows = info[p]
            if b in blocks: continue
            for name, l, om, nb, vis in rows:
                if vis & hexes: continue
                o = ones + (name != "full")
                if o > 1: continue
                best[o] = max(best[o], depth + 1)
                blocks.add(b); rec(nb, blocks, hexes | vis, o, depth + 1); blocks.discard(b)
    p0 = tuple(range(n)); b0, rows0 = info[p0]
    for name, l, om, nb, vis in rows0:
        o = int(name != "full"); best[o] = max(best[o], 1)
        rec(nb, {b0}, set(vis), o, 1)
    print(f"(1) n={n}: longest charge<=1 trail with no charge-1 row {best[0]}, with exactly one {best[1]} (E1 bound n-2 = {n-2})")
capTab = [5, 5, 9, 9, 13, 13, 16, 16, 20, 20, 24, 24, 27, 27, 31, 31, 34, 34, 36, 38, 40, 41, 43, 44, 46, 47, 50, 51, 52, 54, 56, 57, 59, 60, 63, 64, 66]
bad = [g for g, v in enumerate(capTab) if v > 5 + 2 * g]
tight = [g for g, v in enumerate(capTab) if v == 5 + 2 * g]
print(f"(2) n=7 certified capTab (g<=36) vs C1 = 5 + 2g: violations {bad}; tight at g = {tight}")
small = {5: [3, 3, 5, 5], 6: [4, 4, 7, 7], 7: [5, 5, 9], 8: [6, 6, 11]}
for n, vals in small.items():
    c1 = [(n - 2) + (n - 3) * g / 2 for g in range(len(vals))]
    print(f"    n={n} marked M(g) (R176 checker A) {vals} vs C1 {c1}: ok={all(v <= c for v, c in zip(vals, c1))}")
