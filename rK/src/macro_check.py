#!/usr/bin/env python3
"""Independent checker for macro_automaton.py certificates (shares no code with it or trailcore.py).

Claim checked:  every r = 0 trail T of S_8 satisfies  k_T + 1 >= beta |T|  (beta = a/b),
hence (identity L = CONST - ORB - 1 + sum_T (k_T + 1) + sum (c-4), rJ / rI Lean R0Identity)
every r = 0 route has  L >= CONST - ORB - 1 + ceil(beta * (n-1)!).

Steps (all exact):
 1. Lemma R, recomputed: two consecutive full chains must be joined by bac (other cost-3 joins make
    the two chains share a class); 7 bac-joined full chains repeat a class, 6 do not.
    Consequently every trail is a sequence of macro letters N(l) (l <= n-2) and maximal runs F(j)
    (j <= n-2, bac-joined full chains), no F directly after F.
 2. The automaton is regenerated from scratch: states = last w-1 macro letters (with incoming join
    type), an edge for EVERY macro letter whose addition keeps the classes of the last w letters
    distinct.  (True trails keep all classes distinct, so every trail is a path from the root.)
    The certificate's state list must equal the regenerated one (same order), so the potentials
    are attached to the right states.
 3. Potentials pi (integers): pi[root] = 0, pi[v] <= pi[u] + b*cost - a*classes on every edge,
    pi[v] >= -b.  Then every path from the root has sum(b*cost - a*classes) >= -b, i.e.
    k + 1 >= (a/b)|T|.
usage: macro_check.py CERT.json"""
import sys, json, math
from fractions import Fraction

n = 8
def rot_left(p, k):                       # p as a tuple of symbols in positions 0..n-1
    return p[k:] + p[:k]
def cls(p):                               # canonical class representative: lexicographically least rotation
    return min(rot_left(p, k) for k in range(n))
def Fstep(p):                             # rotate positions 0..n-2 left by one, keep position n-1
    return p[1:n - 1] + p[:1] + p[n - 1:]
def join(x, sigma):                       # cost-3 join from run start x: keep x[2..n-2], then x[s] for s in sigma
    return x[2:n - 1] + tuple(x[s] for s in sigma)
SIGMAS = [(0, 1, n - 1), (0, n - 1, 1), (1, 0, n - 1), (1, n - 1, 0), (n - 1, 1, 0)]   # (n-1,0,1) = R^2, excluded
BAC = (1, 0, n - 1)
def chain(p, l):
    out = []; x = p
    for i in range(l):
        out.append(cls(x))
        if i < l - 1: x = Fstep(x)
    return out, x                         # classes, last run start

def lemma_r():
    e = tuple(range(n))
    c1, x = chain(e, n - 1)
    for s in SIGMAS:
        c2, _ = chain(join(x, s), n - 1)
        disjoint = not (set(c1) & set(c2))
        assert disjoint == (s == BAC), ("Lemma R1 fails", s)
    allc = []; p = e
    for j in range(1, n + 1):
        c, x = chain(p, n - 1); allc += c
        assert (len(set(allc)) == len(allc)) == (j <= n - 2), ("Lemma R2 fails", j)
        p = join(x, BAC)

def letter(p, kind, size):
    if kind == "N":
        return chain(p, size)
    out = []; q = p
    for r in range(size):
        c, x = chain(q, n - 1); out += c
        q = join(x, BAC)
    return out, x

def window_ok(seq):
    p = tuple(range(n)); x = None; seen = set(); total = 0
    for i, (s, kind, size) in enumerate(seq):
        if i: p = join(x, tuple(s))
        c, x = letter(p, kind, size)
        seen |= set(c); total += len(c)
    return len(seen) == total

def regenerate(w):
    kinds = [("N", l) for l in range(1, n - 1)] + [("F", j) for j in range(1, n - 1)]
    states = [()]; index = {(): 0}; edges = []; i = 0
    while i < len(states):
        st = states[i]; i += 1
        if not st: succ = [(None, k, s) for k, s in kinds]
        else: succ = [(sg, k, s) for sg in SIGMAS for k, s in kinds if not (st[-1][1] == "F" and k == "F")]
        for L in succ:
            seq = st + (L,)
            if not window_ok(seq): continue
            nst = seq[-(w - 1):] if w > 1 else ()
            if nst not in index: index[nst] = len(states); states.append(nst)
            edges.append((index[st], index[nst], 1 if L[1] == "N" else L[2], L[2] if L[1] == "N" else (n - 1) * L[2]))
    return states, edges

def main():
    C = json.load(open(sys.argv[1]))
    w = C["w"]; beta = Fraction(C["beta_verified"]); a, b = beta.numerator, beta.denominator
    lemma_r()
    states, edges = regenerate(w)
    norm = lambda st: tuple((None if s is None else tuple(s), k, int(z)) for s, k, z in st)
    cert_states = [norm(st) if st else () for st in C["states_list"]]
    assert len(cert_states) == len(states) and all(x == y for x, y in zip(cert_states, states)), "state list differs"
    pi = C["potentials"]; assert len(pi) == len(states) and pi[0] == 0
    bad = sum(1 for u, v, cost, k in edges if pi[v] > pi[u] + b * cost - a * k)
    assert bad == 0, f"{bad} edges violate the potential inequality"
    assert min(pi) >= -b, "a path from the root has sum < -1"
    HEX, ORB = math.factorial(n - 1), math.factorial(n - 2); CONST = math.factorial(n) + HEX + ORB + n - 3
    print(json.dumps(dict(ok=True, checker="macro_check", w=w, states=len(states), edges=len(edges), beta=str(beta),
                          theorem=f"every r=0 trail has k+1 >= {beta}*|T|; every r=0 route has L >= {CONST - ORB - 1 + math.ceil(beta * HEX)}")))

if __name__ == "__main__":
    main()
