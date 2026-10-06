#!/usr/bin/env python3
"""Extract (kernel rows, payload blocks) from a verified 5906 word and check it is a completion under
the canonical definition (flowsat.verify)."""
import sys, os, json, random
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
for d in ("r178/src", "r176/src", HERE): sys.path.insert(0, d if d == HERE else os.path.join(ROOT, d))
from bridge178 import normalize, route_of_word, coarsen
from run178 import words
from complete import World, canon
from flowsat import verify
n = 7; W = World(n)
w = [w for w in words(7, 200) if len(w) == 5906][0]
mp = {c: i for i, c in enumerate(sorted(set(w)))}
route = normalize([tuple(mp[c] for c in t) for t in route_of_word(w, n)], n)
res = coarsen(route, n, random.Random(0))
rows = [x for t in res["instance"] for x in t]
R = lambda x: x[1:] + x[:1]
S = {route[0]} | {route[i + 1] for i in range(len(route) - 1) if route[i + 1] != R(route[i])}
touched = {W.bid[(canon(s[:n - 1]), s[n - 1])] for s in S}
rowb = {W.bid[(canon(r[0][:n - 1]), r[0][n - 1])] for r in rows}
payload = sorted(touched - rowb)
ok, why = verify(W, rows, payload, n)
print("rows", len(rows), "lengths", "".join(str(r[1]) for r in rows), "payload", len(payload), "forest:", ok, why)
json.dump(dict(rows=[[list(r[0]), r[1], list(r[2])] for r in rows], payload=payload),
          open(os.path.join(HERE, "..", "certs", "base5906.json"), "w"))
