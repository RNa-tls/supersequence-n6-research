#!/usr/bin/env python3
"""Final round -- exact conservation law (Theorem C of the report), checked on every route type.
For a Bridge instance:  F_rows / N_nf = full / non-full rows,  V_nf = sum over non-full rows of
visible count (n-1-charge),  S_f = number of maximal full-row segments,  tau_used = nonempty trails,
  delta_seg = (n-2) S_f - F_rows  (>= 0 by C1(0)),   delta_S = tau_used + N_nf - S_f  (>= 0),
  delta_tau = 1 + b + eta - tau_used (>= 0),         u_out = u - (total charge)   (>= 0),
Identity:  (n-2)(D+1) = ORB - V_nf + u_out + (n-1) a + (n-2)(delta_S + delta_tau) + delta_seg.
Also records the per-route 'saving'  Sigma = V_nf - Omega  =  ORB - (n-2)(D+1)."""
import math, os, random, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
for d in ("r178/src", "r176/src", "r182/src", "rF/src"): sys.path.insert(0, os.path.join(ROOT, d))
from bridge178 import coarsen, normalize, check_instance, cost
from run178 import words, to_route, perturb, greedy
from checkA176 import CheckerA
from checkB176 import CheckerB
from r0routes182 import build as build_r0

def terms(route, n, rng, kind):
    ORB = math.factorial(n - 2)
    res = coarsen(route, n, rng)
    okB = check_instance(res, CheckerB(n))[0]
    okA = check_instance(res, CheckerA(n))[0] if n <= 7 else None
    trails = [t for t in res["instance"] if t]
    ch = lambda x: (n - 1 - x[1]) + len(x[2])
    rows = [x for t in trails for x in t]
    F_rows = sum(1 for x in rows if ch(x) == 0); N_nf = len(rows) - F_rows
    V_nf = sum(n - 1 - ch(x) for x in rows if ch(x) > 0)
    S_f = 0
    for t in trails:
        prev_full = False
        for x in t:
            f = ch(x) == 0
            if f and not prev_full: S_f += 1
            prev_full = f
    G = sum(ch(x) for x in rows)
    d = dict(n=n, kind=kind, D=res["D"], m=res["m"], r=res["r"], a=res["a"], b=res["b"], eta=res["eta"],
             N_nf=N_nf, V_nf=V_nf, u_out=res["u"] - G, d_seg=(n - 2) * S_f - F_rows, d_S=len(trails) + N_nf - S_f,
             d_tau=1 + res["b"] + res["eta"] - len(trails), okA=okA, okB=okB,
             length=n + sum(cost(route[i], route[i + 1], n) for i in range(len(route) - 1)))
    lhs = (n - 2) * (d["D"] + 1)
    rhs = ORB - V_nf + d["u_out"] + (n - 1) * d["a"] + (n - 2) * (d["d_S"] + d["d_tau"]) + d["d_seg"]
    d.update(identity=lhs == rhs, nonneg=min(d["u_out"], d["d_seg"], d["d_S"], d["d_tau"]) >= 0,
             Sigma=ORB - lhs, Omega=d["u_out"] + (n - 1) * d["a"] + (n - 2) * (d["d_S"] + d["d_tau"]) + d["d_seg"])
    return d

if __name__ == "__main__":
    from nfcex import family
    from ttrail182 import to_route as z_route
    rng = random.Random(2026); out = []
    for n, lim in ((5, 148), (6, 80)):
        ws = words(n, lim)
        for w in ws: out.append(terms(normalize(to_route(w, n), n), n, rng, f"archive{len(w)}"))
        for _ in range(15): out.append(terms(perturb(to_route(rng.choice(ws), n), n, rng, 1 + rng.randrange(8)), n, rng, "perturbed"))
        for _ in range(8): out.append(terms(greedy(n, rng, rng.choice([0.0, 0.05, 0.2])), n, rng, "greedy"))
        for ls in (n - 1, n - 2, n - 3): out.append(terms(build_r0(n, ls, rng), n, rng, f"r0"))
    for n in (6, 7): out.append(terms(z_route(family(n), n), n, rng, "nfcex"))
    ws = words(7, 139); seen = {}
    for w in ws:
        if seen.get(len(w), 0) < 4:
            seen[len(w)] = seen.get(len(w), 0) + 1
            out.append(terms(normalize(to_route(w, 7), 7), 7, rng, f"archive{len(w)}"))
    json.dump(out, open(os.path.join(HERE, "..", "certs", "conservation.json"), "w"), indent=0)
    print("routes", len(out), "identity all:", all(o["identity"] for o in out), "nonneg all:", all(o["nonneg"] for o in out),
          "checkers all:", all(o["okB"] and o["okA"] in (True, None) for o in out))
    for o in out:
        if o["kind"].startswith("archive") or o["kind"] == "nfcex":
            pass
    import collections
    agg = collections.defaultdict(list)
    for o in out: agg[(o["n"], o["kind"])].append(o)
    for key in sorted(agg):
        L = agg[key]; best = max(L, key=lambda o: o["Sigma"])
        print(key, "routes", len(L), "max Sigma", best["Sigma"], "at D", best["D"], "len", best["length"],
              {k: best[k] for k in ("N_nf", "V_nf", "u_out", "a", "d_S", "d_tau", "d_seg")})
