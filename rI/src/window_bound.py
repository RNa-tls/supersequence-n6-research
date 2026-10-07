#!/usr/bin/env python3
"""Rigorous r = 0 lower bound from the window-w trail automaton (sec. 9-10, 25).
Exact r = 0 identity:  L = CONST - ORB + sum_trails k_i + sum_{inter-trail joins}(c-3)
                         >= CONST - ORB - 1 + sum_trails (k_i + 1).
A trail is a sequence of chains (letter = (sigma_in, l)); being a trail requires all its classes
distinct, in particular every chain's classes avoid those of the previous w chains (window
validity; a relaxation, and independent of the start since S_n acts on the left).
beta* = min over window-valid letter sequences of (k + 1) / sum l   (parametric: largest beta with
        min_path [ sum (1 - beta*l) ] + 1 >= 0 and no negative cycle).
Then sum_trails (k_i + 1) >= beta* * HEX, so  L_r0 >= CONST - ORB - 1 + ceil(beta* * HEX).
beta* is found by bisection with exact Bellman-Ford (numpy) on the window automaton."""
import sys, itertools, math, json, time
import numpy as np
from fractions import Fraction
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
n, w = int(sys.argv[1]), int(sys.argv[2])
F = tuple(list(range(1, n - 1)) + [0, n - 1]); I = tuple(range(n))
Fp = [I]
for _ in range(n - 1): Fp.append(comp(Fp[-1], F))
def canon(p):
    k = p.index(0); return p[k:] + p[:k]
sigmas = [s for s in itertools.permutations((0, 1, n - 1))]
T = {s: tuple(list(range(2, n - 1)) + list(s)) for s in sigmas}
letters = [(None, l) for l in range(1, n)] + [(s, l) for s in sigmas for l in range(1, n)]
def chain_classes(P, l): return [canon(comp(P, Fp[j])) for j in range(l)]
FULL = n - 1; BAC = (1, 0, n - 1)
# Lemma R: consecutive full chains are joined by bac (phi); a run of full chains has <= n-2 chains, and
# bac after a run of exactly n-2 full chains returns to the run's first start (collision).
# state = (tuple of last <= w letters, c = number of consecutive full chains ending here) (first letter of a trail has sigma None and only appears first)
def valid(seq):
    """seq = letters; check classes of the last chain avoid all earlier ones in seq (and own distinct)."""
    P = I; allc = []
    for i, (s, l) in enumerate(seq):
        if i > 0: P = comp(comp(P, Fp[seq[i - 1][1] - 1]), T[s])
        cl = chain_classes(P, l)
        allc.append(cl)
    last = set(allc[-1])
    if len(last) != len(allc[-1]): return False
    return all(not (last & set(c)) for c in allc[:-1])
t0 = time.time()
root = ((), 0)
states = {root: 0}; order = [root]; edges = []   # (u, v, l)
i = 0
while i < len(order):
    st, c = order[i]; i += 1
    cand = [L for L in letters if (L[0] is None) == (len(st) == 0)]
    for L in cand:
        seq = st + (L,)
        if not valid(seq): continue
        if L[1] == FULL:
            nc = c + 1 if (c > 0 and L[0] == BAC) else 1
            if nc > n - 2: continue
        else: nc = 0
        if c == n - 2 and L[0] == BAC: continue
        nst = (seq[-w:] if w > 0 else (), nc)
        if nst not in states: states[nst] = len(order); order.append(nst)
        edges.append((states[(st, c)], states[nst], L[1]))
V = len(order); E = np.array(edges)
print(json.dumps(dict(n=n, w=w, states=V, edges=len(edges), build_sec=round(time.time() - t0, 1))), flush=True)
U, Vv, Ls = E[:, 0], E[:, 1], E[:, 2].astype(float)
def feasible(beta):
    """True iff min over paths from root of sum(1 - beta*l) + 1 >= 0 with no negative cycle."""
    d = np.full(V, np.inf); d[0] = 0.0
    wts = 1.0 - beta * Ls
    for it in range(V + 1):
        cand = d[U] + wts
        nd = d.copy(); np.minimum.at(nd, Vv, cand)
        if np.all(nd == d):
            return bool(np.min(nd) + 1 >= -1e-12)
        if np.min(nd) + 1 < -1e-12: return False
        d = nd
    return False          # still relaxing after V+1 rounds: negative cycle
lo, hi = 1.0 / (n - 1) - 1e-9, 1.0
for _ in range(50):
    mid = (lo + hi) / 2
    if feasible(mid): lo = mid
    else: hi = mid
HEX = math.factorial(n - 1); ORB = math.factorial(n - 2)
CONST = math.factorial(n) + HEX + ORB + n - 3
def feasible_exact(fr):
    """Integer Bellman-Ford: weights b - a*l (beta = a/b); feasible iff no negative cycle and
    min path + b >= 0.  Exact (int64, values bounded by V * n * b)."""
    a, b = fr.numerator, fr.denominator
    wts = (b - a * E[:, 2]).astype(np.int64)
    INF = np.iinfo(np.int64).max // 4
    d = np.full(V, INF, dtype=np.int64); d[0] = 0
    for it in range(V + 1):
        ok = d[U] < INF
        nd = d.copy(); np.minimum.at(nd, Vv[ok], d[U][ok] + wts[ok])
        if np.array_equal(nd, d): return bool(nd.min() + b >= 0)
        if nd.min() + b < 0: return False
        d = nd
    return False
fr = None
for den in (12, 60, 240, 1000, 5000, 20000):
    for cand in (Fraction(lo).limit_denominator(den), Fraction(math.floor(lo * den), den)):
        if (fr is None or cand > fr) and feasible_exact(cand): fr = cand
beta = fr
LB = CONST - ORB - 1 + math.ceil(fr * HEX)
print(json.dumps(dict(n=n, w=w, beta_float=lo, beta_exact_verified=str(fr), inv_beta=float(1 / fr), LB_r0=LB, CONST=CONST,
                      f=CONST + math.factorial(n - 3) - 1, sec=round(time.time() - t0, 1))), flush=True)
