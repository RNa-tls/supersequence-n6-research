#!/usr/bin/env python3
"""Round 154 -- the beta-component construction, rebuilt from the definitions.

Everything here is derived from string algebra and from the definitions printed
in research/RR_L6_PROOF_145_CLAUDE.md sections 4-5; no production table and no
round-14x solver is imported.

DEFINITIONS (the ones the repository actually uses).

  fixed representative   a covering word W whose selected windows w_0..w_{N-1}
                         satisfy gap_j = omega(w_j, w_{j+1}) for every j, where
                         omega(a,b) is the maximal overlap distance
  pass                   a maximal run of consecutive selected windows at gap 1;
                         pass i has entry v_i and length l_i and is the arc
                         (v_i, sigma v_i, ..., sigma^{l_i-1} v_i) of one hexagon
  nu(i)                  the pass whose entry is sigma^{l_i}(v_i) -- "the next
                         arc in the same hexagon"
  alpha                  nu extended by fixing one dummy element; its cycles are
                         the 120 hexagons plus the dummy, so c(alpha) = 121
  T                      the (P+1)-cycle 1 -> 2 -> ... -> P -> dummy -> 1
  beta                   T . alpha^{-1}
  beta-component         a cycle of the permutation beta
  K                      c(beta)

  The identity that makes beta meaningful is beta(nu(i)) = i + 1: the joint
  i -> i+1 of the walk is carried by the beta-edge out of nu(i), and (Lemma C)
  that reassignment changes nothing -- same source string end(v_{nu(i)}), same
  target v_{i+1}, same gap, same spelling, same hidden windows.  So every
  beta-edge except the two incident to the dummy is labelled by the catalogue
  type of a real joint.
"""
from __future__ import annotations
import itertools
from math import factorial


def build(n):
    P = ["".join(p) for p in itertools.permutations("123456"[:n])]
    return P, {p: i for i, p in enumerate(P)}


def sigma(s):
    return s[1:] + s[0]


def tau(s):
    return s[1:-1] + s[0] + s[-1]


def end(v):
    return v[-1] + v[:-1]


def omega(a, b, n):
    for k in range(1, n):
        if b.startswith(a[k:]):
            return k
    return n


def classes(words, f):
    seen, cid = {}, 0
    for p in words:
        if p in seen:
            continue
        q = p
        while q not in seen:
            seen[q] = cid
            q = f(q)
        cid += 1
    return [seen[p] for p in words], cid


def hidden_windows(src, tgt, gap, n):
    raw = src + tgt[n - gap:]
    return [raw[o:o + n] for o in range(1, gap)
            if len(set(raw[o:o + n])) == n]


def joint_type(v, tgt, n):
    """The catalogue type of the shortest connector end(v) -> tgt.

    This is the round-145 classification, rebuilt here; the names are the ones
    the repository uses.  'clean_w3' is the 201/210 pair, which the two
    remaining weight-3 shapes C and D are distinguished from.
    """
    e = end(v)
    g = omega(e, tgt, n)
    if g == 1:
        return None, g                      # inside a pass, not a joint
    if g == 2:
        if tgt == tau(v):
            return "E", g
        if tgt == sigma(v):
            return "A", g
        return "?w2", g
    if g == 3:
        if tgt == tau(tau(v)):
            return "120", g
        if tgt == sigma(sigma(v)):
            return "B", g
        if tgt == tau(sigma(v)):
            return "C", g
        if tgt == sigma(tau(v)):
            return "D", g
        return "clean_w3", g
    return "heavy", g


def selected_windows(W, n):
    """The first occurrence of each permutation, in time order."""
    seen, out = set(), []
    for i in range(len(W) - n + 1):
        w = W[i:i + n]
        if len(set(w)) == n and w not in seen:
            seen.add(w)
            out.append((i, w))
    return out


def splice(W, n):
    """passes, nu, beta and the beta-components of a fixed representative."""
    N = factorial(n)
    sel = selected_windows(W, n)
    if len(sel) != N:
        raise ValueError(f"not a cover: {len(sel)} of {N} permutations")
    gaps = [sel[j + 1][0] - sel[j][0] for j in range(N - 1)]
    fixed = all(gaps[j] == omega(sel[j][1], sel[j + 1][1], n)
                for j in range(N - 1))
    passes, cur_start, cur_len = [], 0, 1
    for j in range(N - 1):
        if gaps[j] == 1:
            cur_len += 1
        else:
            passes.append((sel[cur_start][1], cur_len))
            cur_start, cur_len = j + 1, 1
    passes.append((sel[cur_start][1], cur_len))
    P = len(passes)
    entry = {p[0]: i for i, p in enumerate(passes)}
    if len(entry) != P:
        raise ValueError("two passes share an entry word")

    # nu(i): the pass whose entry is sigma^{l_i}(v_i)
    nu = []
    for v, l in passes:
        x = v
        for _ in range(l):
            x = sigma(x)
        nu.append(entry[x])
    if sorted(nu) != list(range(P)):
        raise ValueError("nu is not a permutation")

    dummy = P
    # alpha = nu with the dummy fixed;  T = (0 1 ... P-1 dummy);  beta = T alpha^-1
    ainv = [0] * (P + 1)
    for i, x in enumerate(nu):
        ainv[x] = i
    ainv[dummy] = dummy
    T = list(range(1, P + 1)) + [0]          # T[x] = x+1, T[P-1]=dummy, T[dummy]=0
    beta = [T[ainv[x]] for x in range(P + 1)]

    # the joint carried by the beta-edge out of q = nu(i) is the joint i -> i+1
    edge_type = {}
    for i in range(P - 1):
        src_pass = nu[i]
        t, g = joint_type(passes[src_pass][0], passes[i + 1][0], n)
        edge_type[src_pass] = (t, g)
    # the two dummy edges carry no joint
    edge_type[nu[P - 1]] = ("DUMMY_IN", None)
    edge_type[dummy] = ("DUMMY_OUT", None)

    seen, comps = [False] * (P + 1), []
    for s in range(P + 1):
        if seen[s]:
            continue
        c, x = [], s
        while not seen[x]:
            seen[x] = True
            c.append(x)
            x = beta[x]
        comps.append(c)
    return dict(n=n, N=N, P=P, G=P - factorial(n - 1), passes=passes, nu=nu,
                beta=beta, dummy=dummy, comps=comps, K=len(comps),
                edge_type=edge_type, fixed_representative=fixed)
