#!/usr/bin/env python3
"""Final attack -- anatomy of the n = 7 length-5906 routes (Sigma = 5): trail layout (charges per row
in order), specials, how hidden classes of non-full rows are covered (row-visible vs payload), and the
class-multiplicity / forest data."""
import sys, os, math, random
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
for d in ("r178/src", "r176/src", "rF/src"): sys.path.insert(0, os.path.join(ROOT, d))
from bridge178 import normalize, route_of_word, coarsen
from run178 import words
from checkA176 import CheckerA

def canon(t): return min(t[i:] + t[:i] for i in range(len(t)))
n = 7
ws = [w for w in words(7, 200) if len(w) == 5906]
print("5906 words:", len(ws))
for w in ws[:4]:
    mp = {c: i for i, c in enumerate(sorted(set(w)))}
    route = normalize([tuple(mp[c] for c in t) for t in route_of_word(w, n)], n)
    res = coarsen(route, n, random.Random(0))
    A = CheckerA(n)
    trails = [t for t in res["instance"] if t]
    lay = [[(n - 1 - x[1]) + len(x[2]) for x in t] for t in trails]
    spec = [[x[0][-1] for x in t] for t in trails]
    vis = set(); hid = set()
    for t in trails:
        for x in t:
            v = A.visible(x); vis |= v
            hid |= {A.hexagon(q) for q in A.states(x[0], n - 1)} - v
    allc = {canon(p) for p in __import__('itertools').permutations(range(n))}
    print(dict(m=res["m"], r=res["r"], a=res["a"], b=res["b"], eta=res["eta"], k=res["k"], trails=len(trails)),
          "charges by trail:", lay, "specials:", spec,
          "hidden classes:", len(hid), "of which visible in other rows:", len(hid & vis), "invisible (payload):", len(allc - vis))
