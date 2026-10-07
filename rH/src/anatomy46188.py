#!/usr/bin/env python3
"""Structure of the n = 8 length-46188 word (superpermutators archive, 2026-10-01, author rumstd):
Bridge parameters, trails with per-trail score v_i, specials, row-length strings, waste terms, the
per-trail score identity and the conservation law, and the Theorem-H forest of its payload."""
import sys, os, json, math, random
from collections import Counter
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
for d in ("r178/src", "r176/src", "rF/src", "rG/src"): sys.path.insert(0, os.path.join(ROOT, d))
from bridge178 import normalize, route_of_word, coarsen, cost, check_instance
from checkB176 import CheckerB
n = 8
w = "".join(ch for ch in open(os.path.join(ROOT, "rH", "data", "superperm8_46188.txt")).read() if not ch.isspace())
mp = {c: i for i, c in enumerate(sorted(set(w)))}
route = normalize([tuple(mp[c] for c in t) for t in route_of_word(w, n)], n)
L = n + sum(cost(route[i], route[i + 1], n) for i in range(len(route) - 1))
res = coarsen(route, n, random.Random(0))
okB = check_instance(res, CheckerB(n))[0]
trails = [t for t in res["instance"] if t]
ch = lambda x: (n - 1 - x[1]) + len(x[2])
vs = [len(t) - sum(ch(x) for x in t) for t in trails]
ORB = math.factorial(n - 2); CONST = math.factorial(n) + math.factorial(n - 1) + ORB + n - 3
G = sum(ch(x) for t in trails for x in t)
u_out = res["u"] - G
E5 = sum(max(0, cost(route[i], route[i + 1], n) - 4) for i in range(len(route) - 1))
lhs = (n - 2) * res["D"]
rhs = ORB - sum(vs) + (n - 2) * (res["b"] + res["eta"]) + u_out + (n - 1) * res["a"]
out = dict(length_route=L, word_length=len(w), D=res["D"], m=res["m"], r=res["r"], a=res["a"], b=res["b"], eta=res["eta"],
           k=res["k"], trails=len(trails), trail_scores=vs, sum_scores=sum(vs), u_out=u_out, E5=E5,
           score_identity_holds=lhs == rhs, checkerB_instance=okB,
           L_from_identity=CONST + (ORB - sum(vs) + u_out + (n - 1) * res["a"]) // (n - 2) + res["b"] + res["eta"] + E5,
           specials=[dict(Counter(x[0][-1] for x in t)) for t in trails],
           lengths=["".join(str(x[1]) for x in t) for t in trails],
           omissions=sum(len(x[2]) for t in trails for x in t))
print(json.dumps(out, indent=1))
json.dump(out, open(os.path.join(ROOT, "rH", "certs", "anatomy46188.json"), "w"), indent=1)
