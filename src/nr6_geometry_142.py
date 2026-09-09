#!/usr/bin/env python3
"""NR6 hard core — overlap-graph geometry for general n.

Vertices: permutations. w(p,q) = n - maxoverlap(p,q) in {1..n}.
The max-overlap spelling of (p,q) is unique. A TRANSIT of (p,q) is a
permutation window strictly inside that spelling. An edge is CLEAN iff it has
no transit. tau(p) = the unique clean weight-2 successor = E(sigma(p)).
"""
from __future__ import annotations
from itertools import permutations
from functools import lru_cache


class Geo:
    def __init__(self, n):
        self.n = n
        self.P = list(permutations(range(n)))
        self.IDX = {p: i for i, p in enumerate(self.P)}
        self.N = len(self.P)
        N, P = self.N, self.P
        self.SIG = [self.IDX[p[1:] + p[:1]] for p in P]
        self.E = [self.IDX[p[1:n - 1] + p[:1] + p[n - 1:]] for p in P]
        self.TAU = [self.E[self.SIG[i]] for i in range(N)]
        # overlap weight
        self.W = [[0] * N for _ in range(N)]
        for a in range(N):
            pa = P[a]
            for b in range(N):
                if a == b:
                    continue
                pb = P[b]
                w = n
                for k in range(1, n):
                    if pa[k:] == pb[:n - k]:
                        w = k
                        break
                self.W[a][b] = w
        self._transit = {}

    def spell(self, a, b):
        return self.P[a] + self.P[b][self.n - self.W[a][b]:]

    def transit(self, a, b):
        """List of (offset, vertex) permutation windows strictly inside (a,b)."""
        key = (a, b)
        if key in self._transit:
            return self._transit[key]
        s = self.spell(a, b)
        out = []
        for off in range(1, self.W[a][b]):
            win = s[off:off + self.n]
            if len(set(win)) == self.n:
                out.append((off, self.IDX[win]))
        self._transit[key] = out
        return out

    def clean(self, a, b):
        return not self.transit(a, b)

    def chain(self, a, b):
        """Transit chain a -> r1 -> ... -> b as vertex list."""
        return [a] + [v for _, v in self.transit(a, b)] + [b]

    # ---- spelling of a whole order / walk
    def spell_walk(self, seq):
        s = list(self.P[seq[0]])
        for i in range(len(seq) - 1):
            s += self.P[seq[i + 1]][self.n - self.W[seq[i]][seq[i + 1]]:]
        return s

    def windows(self, s):
        n = self.n
        return [(i, self.IDX[tuple(s[i:i + n])]) for i in range(len(s) - n + 1)
                if len(set(s[i:i + n])) == n]

    def cost(self, seq):
        return sum(self.W[seq[i]][seq[i + 1]] for i in range(len(seq) - 1))

    def repeats(self, seq):
        """Number of repeated permutation-window occurrences in the spelling."""
        ws = self.windows(self.spell_walk(seq))
        return len(ws) - len({v for _, v in ws})


def sanity(n):
    g = Geo(n)
    N = g.N
    # triangle inequality
    tri = all(g.W[a][b] <= g.W[a][c] + g.W[c][b]
              for a in range(N) for b in range(N) for c in range(N)
              if a != b and c not in (a, b))
    # transit chain decomposes into clean sub-edges with additive weights
    chain_ok = True
    for a in range(N):
        for b in range(N):
            if a == b:
                continue
            ch = g.chain(a, b)
            if sum(g.W[ch[i]][ch[i + 1]] for i in range(len(ch) - 1)) != g.W[a][b]:
                chain_ok = False
            if any(not g.clean(ch[i], ch[i + 1]) for i in range(len(ch) - 1)):
                chain_ok = False
    # tau order
    o = 1
    x = g.TAU[0]
    while x != 0:
        x = g.TAU[x]
        o += 1
    # geodesic uniqueness: w(a,c)+w(c,b) == w(a,b) iff c is a transit of (a,b)
    uniq = True
    for a in range(N):
        for b in range(N):
            if a == b:
                continue
            T = {v for _, v in g.transit(a, b)}
            for c in range(N):
                if c in (a, b):
                    continue
                if (g.W[a][c] + g.W[c][b] == g.W[a][b]) != (c in T):
                    uniq = False
    return dict(n=n, triangle=tri, chain_decomposition=chain_ok, tau_order=o,
                geodesic_unique=uniq,
                clean_edges=sum(1 for a in range(N) for b in range(N)
                                if a != b and g.clean(a, b)),
                total_edges=N * (N - 1))


if __name__ == "__main__":
    import json, sys
    for n in (3, 4, 5):
        print(json.dumps(sanity(n)))
