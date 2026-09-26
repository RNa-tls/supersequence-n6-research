#!/usr/bin/env python3
"""Round 181 -- common-special (CS) inequality: falsification run and omega measurements.

For a Bridge instance (rows = marked rows of a normalized route) and a symbol s:
  k_s    = number of rows whose block has special s
  nu_s   = ORB - k_s                        (s-blocks that are not row blocks)
  Hid_s  = union over s-rows of (classes of the row block) minus (visible classes of the row)
  g_s    = |Hid_s| = total charge of the s-rows
  omega_s= max over blocks B of special t != s of |classes(B) & Hid_s|
Checked (Theorem CS of the r181 report):
  (CS1) g_s <= omega_s * (m + nu_s)
  (CS2) ORB-(n-2) <= (n-2)(eta+b) + ((n-2)+(n-1)omega_s) m + (n-1)(1+omega_s) nu_s
  (RUN) rows <= (n-2) * tau_used + (n-1) * N_nf   (C1 at g = 0 applied to full segments)
Also: omega of the Theorem-W walks, and the payload inequality PI on the n = 6 gap trails.
usage: cs181.py"""
import json, math, os, random, sys
from collections import Counter
from itertools import permutations
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "r178", "src")); sys.path.insert(0, os.path.join(ROOT, "r176", "src"))
sys.path.insert(0, os.path.join(ROOT, "r180", "src"))
from bridge178 import coarsen, normalize
from run178 import words, to_route, perturb, greedy
from checkA176 import CheckerA
from family180 import build as build_W


def hexrep(c):
    return min(c[i:] + c[:i] for i in range(len(c)))


def block_key(c, t):
    """the block of special t containing class c (c = canonical cyclic word of length n)."""
    i = c.index(t); p = c[i + 1:] + c[:i + 1]
    return (hexrep(p[:-1]), t)


def anatomy(rows, n):
    A = CheckerA(n)
    spec = Counter(r[0][-1] for r in rows)
    hid = {s: set() for s in range(n)}
    vis = set()
    for r in rows:
        v = A.visible(r); vis |= v
        allc = {hexrep(q) for q in A.states(r[0], n - 1)}
        hid[r[0][-1]] |= allc - v
    return A, spec, hid, vis


def omega(hid_s, s, n, weight=None):
    cnt = Counter()
    for c in hid_s:
        for t in range(n):
            if t != s: cnt[block_key(c, t)] += 1
    return max(cnt.values()) if cnt else 0


def route_run():
    rng = random.Random(1811)
    out = []; fails = []
    for n, lim, npert, ngr in ((6, 12, 12, 8), (7, 3, 2, 0)):
        ORB = math.factorial(n - 2)
        ws = words(n, lim)
        plan = [("archive", w, None) for w in ws] + [("perturbed", rng.choice(ws), 1 + rng.randrange(8)) for _ in range(npert)] \
             + [("greedy", None, rng.choice([0.0, 0.05, 0.2])) for _ in range(ngr)]
        for kind, w, prm in plan:
            route = normalize(to_route(w, n), n) if kind == "archive" else (perturb(to_route(w, n), n, rng, prm) if kind == "perturbed" else greedy(n, rng, prm))
            res = coarsen(route, n, rng)
            trails = [t for t in res["instance"] if t]
            flat = [x for t in trails for x in t]
            A, spec, hid, vis = anatomy(flat, n)
            m, b, eta = res["m"], res["b"], res["eta"]
            nnf = sum(1 for x in flat if A.charge(x) >= 1)
            run_ok = len(flat) <= (n - 2) * len(trails) + (n - 1) * nnf
            per_s = []
            for s in range(n):
                ks = spec.get(s, 0); nu = ORB - ks; gs = len(hid[s])
                gcharge = sum(A.charge(x) for x in flat if x[0][-1] == s)
                om = omega(hid[s], s, n)
                cs1 = gs <= om * (m + nu)
                cs2 = ORB - (n - 2) <= (n - 2) * (eta + b) + ((n - 2) + (n - 1) * om) * m + (n - 1) * (1 + om) * nu
                if not (cs1 and cs2 and gs == gcharge): fails.append((n, kind, s))
                per_s.append(dict(s=s, k_s=ks, nu=nu, g_s=gs, omega=om, cs1=cs1, cs2=cs2))
            best = min(per_s, key=lambda d: d["nu"])
            o = dict(n=n, kind=kind, m=m, r=res["r"], a=res["a"], b=b, eta=eta, D=res["D"], rows=len(flat),
                     trails=len(trails), N_nf=nnf, run_bound_ok=run_ok, dominant=best,
                     nu_min_over_ORB=round(best["nu"] / ORB, 3))
            out.append(o)
            if not run_ok: fails.append((n, kind, "RUN"))
    return out, fails


def walk_omega(nmax):
    out = []
    for n in range(7, nmax + 1):
        K, rows, _ = build_W(n)
        A, spec, hid, vis = anatomy(rows, n)
        s = n - 1
        out.append(dict(n=n, K=K, rows=len(rows), g_s=len(hid[s]), omega=omega(hid[s], s, n)))
    return out


def gap_PI():
    """payload inequality on the r179 n = 6 gap trails (m, a, b, eta, r) = (4, 0, 0, 0, 6), P = r - a = 6."""
    n = 6; ORB = 24; P = 6
    rep = json.load(open(os.path.join(ROOT, "r179", "certs", "gap179.json")))
    allc = {hexrep(p) for p in permutations(range(n))}
    out = []
    for t in rep:
        rows = [(tuple(int(ch) for ch in s), l, ()) for s, l in t["trail"]]
        A, spec, hid, vis = anatomy(rows, n)
        inv = allc - vis
        res = {}
        for s in range(n):
            ks = spec.get(s, 0); nu = ORB - ks
            # omega' over non-s blocks against Inv, and omega over non-s blocks against Inv & Hid_s
            cnt_inv = Counter(); cnt_h = Counter()
            for c in inv:
                for tt in range(n):
                    if tt == s: continue
                    cnt_inv[block_key(c, tt)] += 1
                    if c in hid[s]: cnt_h[block_key(c, tt)] += 1
            wI = max(cnt_inv.values()); wH = max(cnt_h.values()) if cnt_h else 0
            hs = len(inv & hid[s])
            # feasible P_s in [0, min(nu, P)] with |Inv & Hid_s| <= wH (P - P_s) and |Inv| <= (n-1) P_s + wI (P - P_s)
            feas = [Ps for Ps in range(0, min(nu, P) + 1)
                    if hs <= wH * (P - Ps) and len(inv) <= (n - 1) * Ps + wI * (P - Ps)]
            res[s] = dict(k_s=ks, nu=nu, inv=len(inv), inv_hid_s=hs, omega_inv=wI, omega_hid=wH, feasible_Ps=feas)
        out.append(dict(specials=dict(spec), PI_refutes=any(not v["feasible_Ps"] for v in res.values()), per_s=res))
    return out


if __name__ == "__main__":
    routes, fails = route_run()
    W = walk_omega(16)
    G = gap_PI()
    lines = []
    for o in routes:
        d = o["dominant"]
        lines.append(f"n={o['n']} {o['kind']:9s} m={o['m']:4d} r={o['r']:5d} D={o['D']:5d} rows={o['rows']:4d} N_nf={o['N_nf']:3d} "
                     f"RUN={o['run_bound_ok']}  dominant s={d['s']} k_s={d['k_s']} nu={d['nu']} g_s={d['g_s']} omega={d['omega']} "
                     f"CS1={d['cs1']} CS2={d['cs2']}  nu/ORB={o['nu_min_over_ORB']}")
    lines.append(f"failures (any s): {fails}")
    for w in W: lines.append(f"TheoremW walk {w}")
    for g in G:
        lines.append(f"gap trail specials={g['specials']} PI_refutes={g['PI_refutes']}")
        for s, v in g["per_s"].items():
            if v["k_s"]: lines.append(f"   s={s} {v}")
    txt = "\n".join(lines); print(txt)
    os.makedirs(os.path.join(HERE, "..", "certs"), exist_ok=True)
    open(os.path.join(HERE, "..", "certs", "cs181.txt"), "w").write(txt + "\n")
