#!/usr/bin/env python3
"""Final attack -- exact per-trail decomposition of the saving (corollary of Theorem C):
   V_nf - Omega = sum_trails (v_i - (n-2)) - u_out - (n-1) a - (n-2) delta_tau,
   v_i = rows_i - charge_i  (= Houston's kernel score of trail i, generalized to marked rows).
Checked on archive / perturbed / greedy routes with the Bridge instance of bridge178.coarsen."""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
for d in ("r178/src", "r176/src", "rF/src", "r182/src"): sys.path.insert(0, os.path.join(ROOT, d))
from bridge178 import normalize, route_of_word, coarsen
from run178 import words, to_route, perturb, greedy
from conservation import terms

def check(route, n, rng):
    d = terms(route, n, random.Random(0), "x")
    res = coarsen(route, n, random.Random(0))
    trails = [t for t in res["instance"] if t]
    ch = lambda x: (n - 1 - x[1]) + len(x[2])
    vs = [len(t) - sum(ch(x) for x in t) for t in trails]
    lhs = d["V_nf"] - d["Omega"]
    rhs = sum(v - (n - 2) for v in vs) - d["u_out"] - (n - 1) * d["a"] - (n - 2) * d["d_tau"]
    return lhs == rhs, max(vs), lhs

if __name__ == "__main__":
    rng = random.Random(7); ok = True; cnt = 0; best = {}
    for n, lim in ((5, 60), (6, 30), (7, 12)):
        ws = words(n, 200 if n == 7 else lim)
        rs = [normalize(to_route(w, n), n) for w in (ws if n < 7 else ws[::12])]
        if n < 7: rs += [perturb(to_route(rng.choice(ws), n), n, rng, 3) for _ in range(8)] + [greedy(n, rng, 0.05) for _ in range(4)]
        for rt in rs:
            e, vmax, sig = check(rt, n, rng); ok &= e; cnt += 1
            best[n] = max(best.get(n, -10**9), vmax)
    print(f"routes {cnt}: per-trail decomposition exact in all: {ok}; max single-trail score seen per n: {best}")
