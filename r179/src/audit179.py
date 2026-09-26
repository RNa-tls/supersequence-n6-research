#!/usr/bin/env python3
"""Round 179 -- adversarial falsification of the Round 178 chain on concrete routes.

For every route (archive / perturbed / greedy, n = 6, 7) we rebuild the Bridge(n)
instance (r178 bridge178.coarsen, which asserts B1-B12) and test consequences that
would FAIL if C1, Bridge(n) or the Delta derivation were wrong:
  T1  per-trail C1:        rows_i <= (n-2) + (n-3) c_i / 2      (n >= 6)
  T2  aggregate:           k <= (n-2) tau + (n-3) u / 2  with k = ORB+m-r+a, tau = eta+1+b,
                           u = (n-1)m - r
  T3  final bound:         D >= ceil(2(n-2)((n-3)!-1)/(n^2-4n+1))
  T4  universal payload (UPL, r179 report section 5): every cyclic class not visible in
      the rows has a run start in one of the M - k = r - a non-row touched blocks, and
      every selected state of a row block is visible  -- in ALL three trichotomy cases
  M   effective rows-per-hole  lambda_eff = (k - (n-2) tau) / u  (a measurement)
usage: audit179.py"""
import json, math, os, random, sys
from fractions import Fraction as Fr
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "r178", "src"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "r176", "src"))
from bridge178 import coarsen, normalize
from run178 import words, to_route, perturb, greedy, case_of
from checkA176 import CheckerA


def audit(route, n, rng):
    res = coarsen(route, n, rng)
    A = CheckerA(n)
    R = lambda s: s[1:] + s[:1]
    hexrep = lambda s: min(s[i:] + s[:i] for i in range(n))
    N = len(route)
    cst = lambda x, y: next((n - j for j in range(n - 1, 0, -1) if x[n - j:] == y[:j]), n)
    S = {route[0]} | {route[i + 1] for i in range(N - 1) if cst(route[i], route[i + 1]) != 1}
    blk = res["blk"]
    touched = {blk(s) for s in S}
    inst = res["instance"]
    rows = [x for t in inst for x in t]
    row_blocks = {blk(x[0]) for x in rows}
    ORB = math.factorial(n - 2)
    out = {}
    # T1
    lam = Fr(n - 3, 2)
    out["T1"] = all(len(t) <= (n - 2) + lam * sum(A.charge(x) for x in t) for t in inst)
    # T2
    k, tau, u = ORB + res["m"] - res["r"] + res["a"], res["eta"] + 1 + res["b"], (n - 1) * res["m"] - res["r"]
    out["T2"] = k <= (n - 2) * tau + lam * u and k == len(rows)
    # T3
    bound = -(-(2 * (n - 2) * (math.factorial(n - 3) - 1)) // (n * n - 4 * n + 1))
    out["T3"] = res["D"] >= bound
    # T4 (UPL)
    visible = set().union(*[A.visible(x) for x in rows])
    sel_visible = True
    F = lambda s: s[1:n - 1] + (s[0], s[n - 1])
    for x in rows:
        z = x[0]; st = []
        for _ in range(n - 1): st.append(z); z = F(z)
        for zz in st:
            if zz in S and hexrep(zz) not in A.visible(x): sel_visible = False
    payload = touched - row_blocks
    ok = len(payload) == res["r"] - res["a"]
    for s in S:
        c = hexrep(s)
        if c in visible: continue
        # every run start of an invisible class lies in a payload block
        if blk(s) not in payload: ok = False
    classes_invisible = {hexrep(s) for s in S} - visible
    all_classes = math.factorial(n - 1)
    ok = ok and len({hexrep(s) for s in S}) == all_classes
    out["T4"] = ok and sel_visible
    out["counts"] = dict(k=k, tau=tau, u=u, D=res["D"], bound=bound, payload=len(payload),
                         invisible=len(classes_invisible), case=case_of(res),
                         lambda_eff=float(Fr(k - (n - 2) * tau, u)) if u > 0 else None)
    return out


def main():
    rng = random.Random(179)
    plan = []
    for n, lim, npert, ngreedy in ((6, 12, 20, 12), (7, 3, 3, 0)):
        ws = words(n, lim)
        for w in ws: plan.append((n, "archive", w, None))
        for _ in range(npert): plan.append((n, "perturbed", rng.choice(ws), 1 + rng.randrange(8)))
        for _ in range(ngreedy): plan.append((n, "greedy", None, rng.choice([0.0, 0.05, 0.2])))
    log = []
    fails = 0
    for n, kind, w, param in plan:
        if kind == "archive": route = normalize(to_route(w, n), n)
        elif kind == "perturbed": route = perturb(to_route(w, n), n, rng, param)
        else: route = greedy(n, rng, param)
        o = audit(route, n, rng)
        o.update(n=n, kind=kind)
        log.append(o)
        bad = [t for t in ("T1", "T2", "T3", "T4") if not o[t]]
        if bad: fails += 1; print("FAIL", n, kind, bad, o["counts"])
    for n in (6, 7):
        L = [o for o in log if o["n"] == n]
        lam = [o["counts"]["lambda_eff"] for o in L if o["counts"]["lambda_eff"] is not None]
        arch = [o["counts"]["lambda_eff"] for o in L if o["kind"] == "archive" and o["counts"]["lambda_eff"] is not None]
        print(f"n={n}: routes {len(L)}; T1..T4 all hold: {sum(all(o[t] for t in ('T1','T2','T3','T4')) for o in L)}; "
              f"cases {sorted({o['counts']['case'] for o in L})}; D range {min(o['counts']['D'] for o in L)}..{max(o['counts']['D'] for o in L)} (bound {L[0]['counts']['bound']}); "
              f"lambda_eff archive {min(arch):.3f}..{max(arch):.3f}, all {min(lam):.3f}..{max(lam):.3f}; C1 lambda {(n-3)/2}")
    print("FAILURES:", fails)
    json.dump(log, open(os.path.join(HERE, "..", "certs", "audit179.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
