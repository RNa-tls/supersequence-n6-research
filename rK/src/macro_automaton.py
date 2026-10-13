#!/usr/bin/env python3
"""Round K -- macro-letter window automaton: a rigorous lower bound on the cost/class ratio of every
r = 0 trail, hence on L_r0(8).

Identity (r = 0, audited in rJ):  L = CONST - ORB - 1 + sum_trails (k_T + 1) + sum_{inter-trail}(c - 4),
k_T = chains of trail T.  If every trail satisfies  k_T + 1 >= beta |T|  (|T| = classes), then
L >= CONST - ORB - 1 + ceil(beta * HEX)  for every r = 0 route.

Trail = sequence of chains joined by cost-3 joins (5 legal types sigma), all classes distinct.
Lemma R (checked by computation, rK/src/lemma_r_check.py): two consecutive FULL chains (length n-1)
are joined by bac, and at most n-2 = 6 full chains follow each other.  Hence a trail is a sequence of
MACRO letters joined by sigma:
    N(l): one non-full chain, l = 1..n-2          cost 1, classes l
    F(j): j full chains joined by bac, j = 1..6   cost j, classes 7j
with no F directly after an F (maximal runs).  Window-w relaxation: the classes of every w
consecutive macro letters are distinct (true trails satisfy this; so the automaton's paths include
all true trails and the bound is a valid lower bound).  State = last w-1 letters (sigma, kind, size);
validity is independent of the start perm (S_n acts on the left).

beta_w = largest beta such that every path from the root has sum(cost - beta*classes) >= -1;
computed by bisection + exact integer Bellman-Ford; the final potentials form a certificate.
usage: macro_automaton.py W [OUT.json]"""
import sys, os, json, time, math, itertools
from fractions import Fraction
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trailcore import comp, setup, canon

n = 8
I, F, Fp, sig, BAC, sigmas = setup(n)
FULL = n - 1
STEP_BAC = comp(Fp[FULL - 1], sig[BAC])       # full chain start -> next full chain start
KINDS = [("N", l) for l in range(1, n - 1)] + [("F", j) for j in range(1, n - 1)]

def letter_classes(P, kind, size):
    """classes visited by a macro letter starting at perm P, and the start of its last run"""
    cl = []
    if kind == "N":
        for j in range(size): cl.append(canon(comp(P, Fp[j])))
        return cl, comp(P, Fp[size - 1])
    Q = P
    for r in range(size):
        if r: Q = comp(Q, STEP_BAC)
        for j in range(FULL): cl.append(canon(comp(Q, Fp[j])))
    return cl, comp(Q, Fp[FULL - 1])

def seq_classes(seq):
    """seq = ((sigma or None, kind, size), ...); classes of each letter, start = identity"""
    P = I; out = []; last = None
    for i, (s, kind, size) in enumerate(seq):
        if i: P = comp(last, sig[s])
        cl, last = letter_classes(P, kind, size)
        out.append(cl)
    return out

def valid_window(seq):
    """all classes of the letters in seq distinct (only the newest letter needs checking if the
    rest was already checked, but we check everything for clarity)"""
    cls = seq_classes(seq)
    flat = [c for cl in cls for c in cl]
    return len(set(flat)) == len(flat)

def successors(state):
    """macro letters that may follow `state` (tuple of letters); the first letter has sigma None"""
    out = []
    if not state:
        for kind, size in KINDS: out.append((None, kind, size))
        return out
    lastkind = state[-1][1]
    for s in sigmas:
        for kind, size in KINDS:
            if lastkind == "F" and kind == "F": continue      # runs are maximal
            out.append((s, kind, size))
    return out

def build(w):
    t0 = time.time()
    root = ()
    idx = {root: 0}; order = [root]; eu, ev, ec, ek = [], [], [], []
    i = 0
    while i < len(order):
        st = order[i]; i += 1
        for L in successors(st):
            seq = st + (L,)
            if not valid_window(seq): continue
            nst = seq[-(w - 1):] if w > 1 else ()
            if nst and nst[0][0] is not None and len(seq) <= w - 1:
                pass
            if nst not in idx: idx[nst] = len(order); order.append(nst)
            cost = 1 if L[1] == "N" else L[2]
            cls = L[2] if L[1] == "N" else 7 * L[2]
            eu.append(idx[st]); ev.append(idx[nst]); ec.append(cost); ek.append(cls)
    return order, np.array(eu), np.array(ev), np.array(ec, dtype=np.int64), np.array(ek, dtype=np.int64), time.time() - t0

def bf_exact(V, U, Vv, C, K, a, b, return_pot=False):
    """beta = a/b.  integer weights b*cost - a*classes.  Feasible iff no negative cycle reachable
    from the root and every distance >= -b (i.e. sum(cost - beta*classes) >= -1)."""
    wts = b * C - a * K
    INF = np.iinfo(np.int64).max // 4
    d = np.full(V, INF, dtype=np.int64); d[0] = 0
    for it in range(V + 2):
        ok = d[U] < INF
        nd = d.copy(); np.minimum.at(nd, Vv[ok], d[U][ok] + wts[ok])
        if np.array_equal(nd, d):
            feas = bool(nd.min() + b >= 0)
            return (feas, nd) if return_pot else feas
        if nd.min() + b < 0: return (False, None) if return_pot else False
        d = nd
    return (False, None) if return_pot else False

def main():
    w = int(sys.argv[1]); out = sys.argv[2] if len(sys.argv) > 2 else None
    order, U, Vv, C, K, sec = build(w)
    V = len(order)
    print(json.dumps(dict(w=w, states=V, edges=len(U), build_sec=round(sec, 1))), flush=True)
    lo, hi = Fraction(1, 7), Fraction(1, 6)
    assert bf_exact(V, U, Vv, C, K, lo.numerator, lo.denominator)
    # bisection on rationals with bounded denominators, then exact verification
    flo, fhi = float(lo), float(hi)
    for _ in range(40):
        mid = (flo + fhi) / 2; fr = Fraction(mid).limit_denominator(100000)
        if bf_exact(V, U, Vv, C, K, fr.numerator, fr.denominator): flo = mid
        else: fhi = mid
    best = None
    for den in (20, 33, 60, 120, 330, 660, 1000, 5040, 20000, 100000):
        for cand in (Fraction(flo).limit_denominator(den), Fraction(math.floor(flo * den), den)):
            if (best is None or cand > best) and bf_exact(V, U, Vv, C, K, cand.numerator, cand.denominator): best = cand
    feas, pot = bf_exact(V, U, Vv, C, K, best.numerator, best.denominator, return_pot=True)
    HEX, ORB = math.factorial(n - 1), math.factorial(n - 2); CONST = math.factorial(n) + HEX + ORB + n - 3
    LB = CONST - ORB - 1 + math.ceil(best * HEX)
    res = dict(w=w, states=V, edges=len(U), beta_float_upper=fhi, beta_verified=str(best), beta_float=float(best),
               LB_r0=LB, CONST=CONST, sec=round(time.time() - t0, 1))
    print(json.dumps(res), flush=True)
    if out:
        json.dump(dict(res, states_list=[[list(x) if x else x for x in st] for st in order],
                       potentials=[int(x) for x in pot]), open(out, "w"))

t0 = time.time()
if __name__ == "__main__":
    main()
