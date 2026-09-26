#!/usr/bin/env python3
"""Round 182 -- falsification run of Theorem F (forced non-full rows) and the NF ratio.
For each normalized route: Bridge instance via bridge178.coarsen, instance validated by checkers A
and B (r176), then
  RUN   : k <= (n-2) tau_used + (n-1) N_nf
  F_ex  : (n-1) N_nf >= ORB + m - r + a - (n-2)(1 + eta + b)
  F     : (n-1) N_nf + (n-2)(1 + X) >= ORB,          X = m + b + eta
  ratio : N_nf / X,  and the implied bound D >= (ORB - (n-1) N_nf)/(n-2) - 1.
Route sets: archive superpermutations (n = 5, 6, 7 incl. all five n = 7 lengths), random
perturbations + normalization, random greedy routes, r = 0 greedy routes (r0routes182.build)."""
import math, os, random, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
for d in ("r178/src", "r176/src", "r182/src"): sys.path.insert(0, os.path.join(ROOT, d))
from bridge178 import coarsen, normalize, check_instance, cost
from run178 import words, to_route, perturb, greedy
from checkA176 import CheckerA
from checkB176 import CheckerB
from r0routes182 import build as build_r0


def analyse(route, n, rng, kind, extra=""):
    ORB = math.factorial(n - 2)
    res = coarsen(route, n, rng)
    okA = check_instance(res, CheckerA(n))[0]; okB = check_instance(res, CheckerB(n))[0]
    trails = [t for t in res["instance"] if t]; flat = [x for t in trails for x in t]
    nnf = sum(1 for x in flat if (n - 1 - x[1]) + len(x[2]) >= 1)
    m, r, a, b, eta, k = res["m"], res["r"], res["a"], res["b"], res["eta"], res["k"]
    X = m + b + eta
    run = k <= (n - 2) * len(trails) + (n - 1) * nnf
    fex = (n - 1) * nnf >= ORB + m - r + a - (n - 2) * (1 + eta + b)
    f = (n - 1) * nnf + (n - 2) * (1 + X) >= ORB
    slack = (n - 1) * nnf + (n - 2) * (1 + X) - ORB
    length = n + sum(cost(route[i], route[i + 1], n) for i in range(len(route) - 1))
    return dict(n=n, kind=kind + extra, len=length, m=m, r=r, a=a, b=b, eta=eta, D=res["D"], X=X, k=k,
                tau=len(trails), N_nf=nnf, ratio=round(nnf / X, 3), okA=okA, okB=okB, RUN=run, Fex=fex, F=f,
                slackF=slack, Fbound=math.ceil((ORB - (n - 1) * nnf) / (n - 2) - 1))


def main():
    rng = random.Random(1822); out = []
    for n, lim in ((5, 148), (6, 60)):
        ws = words(n, lim)
        for w in ws: out.append(analyse(normalize(to_route(w, n), n), n, rng, "archive", str(len(w))))
        for _ in range(20): out.append(analyse(perturb(to_route(rng.choice(ws), n), n, rng, 1 + rng.randrange(8)), n, rng, "perturbed"))
        for _ in range(10): out.append(analyse(greedy(n, rng, rng.choice([0.0, 0.05, 0.2])), n, rng, "greedy"))
        for ls in (n - 1, n - 2, n - 3, 2):
            for _ in range(4): out.append(analyse(build_r0(n, ls, rng), n, rng, "r0", f"l*={ls}"))
    n = 7
    ws = words(n, 139); bylen = {}
    for w in ws: bylen.setdefault(len(w), []).append(w)
    for L in sorted(bylen):
        for w in bylen[L][:3]: out.append(analyse(normalize(to_route(w, n), n), n, rng, "archive", str(L)))
    for ls in (6, 5): out.append(analyse(build_r0(n, ls, rng), n, rng, "r0", f"l*={ls}"))
    return out


if __name__ == "__main__":
    out = main(); lines = []
    for o in out:
        lines.append(" ".join(f"{k}={v}" for k, v in o.items()))
    agg = Counter((o["n"], o["kind"].rstrip("0123456789=l*")) for o in out)
    lines.append(f"routes: {len(out)}  all checkers: {all(o['okA'] and o['okB'] for o in out)}  "
                 f"RUN violations: {sum(not o['RUN'] for o in out)}  F_ex violations: {sum(not o['Fex'] for o in out)}  "
                 f"F violations: {sum(not o['F'] for o in out)}")
    for n in (5, 6, 7):
        R = [o for o in out if o["n"] == n]
        lines.append(f"n={n}: max N_nf/X = {max(o['ratio'] for o in R)}, min F slack = {min(o['slackF'] for o in R)}, "
                     f"tight routes = {[(o['kind'], o['D'], o['N_nf']) for o in R if o['slackF'] == min(x['slackF'] for x in R)][:4]}")
    txt = "\n".join(lines); print("\n".join(lines[-4:]))
    open(os.path.join(HERE, "..", "certs", "fcheck182.txt"), "w").write(txt + "\n")
