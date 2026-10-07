#!/usr/bin/env python3
"""Structure of the six long trails (104 rows, score 48) of the n = 8 46188 word:
 - minimal period of the row-length string; charge pattern
 - special symbol of each row and where it changes
 - symmetry: relabellings of {0..7} mapping one long trail's row set onto another's
 - the frames of the phi-cycle trails."""
import sys, os, json, random, itertools
from collections import Counter
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
for d in ("r178/src", "r176/src", "rG/src"): sys.path.insert(0, os.path.join(ROOT, d))
from bridge178 import normalize, route_of_word, coarsen
n = 8
w = "".join(ch for ch in open(os.path.join(ROOT, "rH", "data", "superperm8_46188.txt")).read() if not ch.isspace())
mp = {c: i for i, c in enumerate(sorted(set(w)))}
route = normalize([tuple(mp[c] for c in t) for t in route_of_word(w, n)], n)
res = coarsen(route, n, random.Random(0))
trails = [t for t in res["instance"] if t]
longs = [t for t in trails if len(t) > 20]
def period(s):
    for p in range(1, len(s) + 1):
        if all(s[i] == s[i % p] for i in range(len(s))): return p
for t in longs[:2]:
    ls = "".join(str(x[1]) for x in t); sp = [x[0][-1] for x in t]
    print("lengths", ls, "period", period(ls))
    print("specials", "".join(map(str, sp)))
    print("special changes at rows", [i for i in range(1, len(t)) if sp[i] != sp[i - 1]])
# symmetry between long trails: try all relabellings mapping first row start of trail A to some row of trail B
def rowset(t): return {(x[0], x[1]) for x in t}
sets = [rowset(t) for t in longs]
maps = []
for j in range(1, len(longs)):
    found = None
    for x in longs[j]:
        p0 = longs[0][0][0]; q = x[0]
        sig = {p0[i]: q[i] for i in range(n)}
        img = {(tuple(sig[c] for c in p), l) for p, l in sets[0]}
        if img == sets[j]: found = sig; break
    maps.append(found)
print("relabelling maps trail0 -> trail j (j=1..):", [None if m is None else tuple(m[i] for i in range(n)) for m in maps])
phis = [t for t in trails if len(t) == 6 and all(x[1] == n - 1 for x in t)]
print("phi-cycle trails:", len(phis), "specials:", Counter(t[0][0][-1] for t in phis))
