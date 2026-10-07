#!/usr/bin/env python3
"""Bridge parameters (r, m, a, b, eta, D, E5) of words after Lemma-2.2 normalization (r178 code)."""
import sys, os, json, random
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
for d in ("r178/src", "r176/src"): sys.path.insert(0, os.path.join(ROOT, d))
from bridge178 import normalize, route_of_word, coarsen, cost
for p in sys.argv[1:]:
    w = "".join(ch for ch in open(p).read().split("\n")[0] if not ch.isspace())
    al = sorted(set(w)); n = len(al); mp = {c: i for i, c in enumerate(al)}
    try:
        route = normalize([tuple(mp[c] for c in t) for t in route_of_word(w, n)], n)
        L = n + sum(cost(route[i], route[i + 1], n) for i in range(len(route) - 1))
        res = coarsen(route, n, random.Random(0))
        E5 = sum(max(0, cost(route[i], route[i + 1], n) - 4) for i in range(len(route) - 1))
        print(json.dumps(dict(file=os.path.basename(p), n=n, L=L, **{k: res[k] for k in ("r", "m", "a", "b", "eta", "D", "u")}, E5=E5)), flush=True)
    except Exception as e:
        print(json.dumps(dict(file=os.path.basename(p), err=str(e)[:100])), flush=True)
