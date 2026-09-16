#!/usr/bin/env python3
"""Round 156 -- an INDEPENDENT corpus of fixed representatives.

Phi and the fixed-point iteration are rebuilt from the Round-145 write-up, not
imported.  The corpus deliberately contains dirty joints (type A / type B),
heavy joints, several beta components and several chains, because those are
exactly the configurations the 872 witness itself does NOT exercise.
"""
from __future__ import annotations
import itertools, random, sys
from math import factorial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract156 import omega, selected, is_cover, perm_windows      # noqa: E402


def Phi(W, n):
    sel = selected(W, n)
    out = sel[0][1]
    for j in range(1, len(sel)):
        k = omega(sel[j - 1][1], sel[j][1], n)
        out += sel[j][1][n - k:]
    return out


def fixed_representative(W, n, max_iter=100000):
    prev = None
    for _ in range(max_iter):
        V = Phi(W, n)
        if len(V) > len(W):
            raise AssertionError("Phi lengthened a word")
        if V == W:
            return W
        W = V
    raise AssertionError("no fixed point")


def random_cover(n, alpha, rng, extra=8):
    """Greedy random walk that ends when every permutation has appeared."""
    need = {"".join(p) for p in itertools.permutations(alpha)}
    w = "".join(rng.sample(alpha, n))
    seen = {w}
    guard = 0
    while seen != need and guard < 40 * factorial(n):
        guard += 1
        cands = []
        for ch in alpha:
            v = w[-(n - 1):] + ch
            cands.append((v in need and v not in seen, ch))
        fresh = [c for ok, c in cands if ok]
        w += rng.choice(fresh) if fresh and rng.random() < 0.85 \
            else rng.choice(alpha)
        v = w[-n:]
        if len(set(v)) == n:
            seen.add(v)
    if seen != need:
        return None
    return w


def corpus(n, alpha, bases, rng, tries):
    out, seen = [], set()
    for it in range(tries):
        mode = it % 3
        if mode == 0:
            w = random_cover(n, alpha, rng)
            if w is None:
                continue
        else:
            w = rng.choice(bases)
            for _ in range(rng.randint(1, 5)):
                p = rng.randrange(len(w))
                w = w[:p] + "".join(rng.choice(alpha)
                                    for _ in range(rng.randint(1, n + 3))) + w[p:]
        if not is_cover(w, n, alpha):
            continue
        try:
            ws = fixed_representative(w, n)
        except AssertionError:
            continue
        if ws in seen:
            continue
        seen.add(ws)
        out.append(ws)
    return out
