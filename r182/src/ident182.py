#!/usr/bin/env python3
"""Round 182 -- numerical check of the balanced-special double-counting identities (report sec. 3).
Per route (Bridge instance from bridge178.coarsen):
  I1  sum_s k_s = k,   sum_s nu_s = (n-1) ORB - m + (r - a)
  I2  G := total charge = sum_s g_s = (n-1)(m - r + a) + |Inv|
  I3  sum_c mu(c) = (n-1) k,  h(c) := mu(c) - [c visible],  sum_c h(c) = G
  I4  J_s := sum over blocks B in (non-s rows) u (non-s payload) of |cls(B) & Hid_s|;
      J_s >= g_s (covering) and  sum_s J_s = sum_c rho(c) h(c) - G,  rho(c) = #(row or payload blocks) containing c
  AV  if >= 2 specials carry charge and m <= ORB/n then sum_s omega_s (m + nu_s) >= (n-1) m >= G."""
import math, os, random, sys
from itertools import permutations
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
for d in ("r178/src", "r176/src", "r182/src", "r181/src"): sys.path.insert(0, os.path.join(ROOT, d))
from bridge178 import coarsen, normalize
from run178 import words, to_route, perturb, greedy
from checkA176 import CheckerA
from r0routes182 import build as build_r0

def check(route, n, rng):
    A = CheckerA(n); ORB = math.factorial(n - 2)
    res = coarsen(route, n, rng)
    rows = [x for t in res["instance"] for x in t]
    F = lambda s: s[1:n - 1] + (s[0], s[n - 1]); R = lambda s: s[1:] + s[:1]
    S = {route[0]} | {route[i + 1] for i in range(len(route) - 1) if route[i + 1] != R(route[i])}
    bl = lambda p: A.block(p)
    touched = {bl(s) for s in S}; rowblk = {bl(x[0]) for x in rows}
    payload = touched - rowblk
    allc = {A.hexagon(p) for p in permutations(range(n))}
    vis = set(); hid = {s: set() for s in range(n)}; mu = Counter()
    for x in rows:
        v = A.visible(x); vis |= v
        cl = {A.hexagon(q) for q in A.states(x[0], n - 1)}
        for c in cl: mu[c] += 1
        hid[x[0][-1]] |= cl - v
    inv = allc - vis
    k_s = Counter(x[0][-1] for x in rows); nu = {s: ORB - k_s[s] for s in range(n)}
    G = sum(A.charge(x) for x in rows); m, r, a = res["m"], res["r"], res["a"]
    I1 = sum(k_s.values()) == len(rows) and sum(nu.values()) == (n - 1) * ORB - m + (r - a)
    I2 = G == sum(len(h) for h in hid.values()) == (n - 1) * (m - r + a) + len(inv)
    h = {c: mu[c] - (c in vis) for c in allc}
    I3 = sum(mu.values()) == (n - 1) * len(rows) and sum(h.values()) == G
    blocks = [(b, x[0][-1]) for b, x in ((bl(x[0]), x) for x in rows)] + [(b, next(iter(b))[-1]) for b in payload]
    rho = Counter()
    J = Counter()
    for b, sp in blocks:
        cl = {A.hexagon(q) for q in b}
        for c in cl: rho[c] += 1
        for s in range(n):
            if s != sp: J[s] += len(cl & hid[s])
    I4 = all(J[s] >= len(hid[s]) for s in range(n)) and sum(J.values()) == sum(rho[c] * h[c] for c in allc) - G
    charged = [s for s in range(n) if hid[s]]
    AV = None
    if len(charged) >= 2 and m <= ORB / n:
        AV = sum(nu[s] for s in charged) >= (n - 1) * m >= G
    return dict(I1=I1, I2=I2, I3=I3, I4=I4, AV=AV, balanced=max(k_s.values()) / ORB if k_s else 0)

if __name__ == "__main__":
    rng = random.Random(1823); out = []
    for n in (5, 6):
        ws = words(n, 30)
        rs = [normalize(to_route(w, n), n) for w in ws[:15]] + [perturb(to_route(rng.choice(ws), n), n, rng, 3) for _ in range(8)] \
           + [greedy(n, rng, 0.05) for _ in range(5)] + [build_r0(n, l, rng) for l in (n - 1, n - 2, n - 3)]
        for rt in rs: out.append((n, check(rt, n, rng)))
    for w in words(7, 139)[::30]: out.append((7, check(normalize(to_route(w, 7), 7), 7, rng)))
    keys = ["I1", "I2", "I3", "I4"]
    lines = [f"routes {len(out)}: " + ", ".join(f"{k} all true: {all(o[k] for _, o in out)}" for k in keys),
             f"AV applicable in {sum(o['AV'] is not None for _, o in out)} routes, true in all: {all(o['AV'] for _, o in out if o['AV'] is not None)}",
             f"max k_s/ORB over routes (dominance): {max(o['balanced'] for _, o in out):.3f}"]
    print("\n".join(lines)); open(os.path.join(HERE, "..", "certs", "ident182.txt"), "w").write("\n".join(lines) + "\n")
