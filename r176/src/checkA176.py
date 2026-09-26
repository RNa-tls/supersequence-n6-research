#!/usr/bin/env python3
"""Round 176 -- checker A: direct row / permutation-class checker.

Works from the raw definitions only: states are computed by iterating F, visible
hexagons are canonical R-orbit representatives of the non-omitted states, beta is
drop 3 (Rinv lastState), blocks are F-orbits.  Shares no code with checker B.
A row is (start: tuple, length: int, omitted: tuple of positions)."""


class CheckerA:
    def __init__(self, n):
        self.n = n

    def F(self, s):
        n = self.n
        return s[1:n - 1] + (s[0], s[n - 1])

    def states(self, p, count):
        out = [p]
        for _ in range(count - 1):
            out.append(self.F(out[-1]))
        return out

    def hexagon(self, s):
        return min(s[i:] + s[:i] for i in range(self.n))

    def block(self, p):
        return frozenset(self.states(p, self.n - 1))

    def admissible(self, row):
        p, l, om = row
        n = self.n
        if sorted(p) != list(range(n)) or not (1 <= l <= n - 1):
            return False
        return all(0 < i and i + 1 < l for i in om) and len(set(om)) == len(om)

    def charge(self, row):
        return (self.n - 1 - row[1]) + len(row[2])

    def visible(self, row):
        p, l, om = row
        st = self.states(p, l)
        return {self.hexagon(st[i]) for i in range(l) if i not in om}

    def beta(self, row):
        p, l, om = row
        last = self.states(p, l)[-1]
        rinv = (last[-1],) + last[:-1]
        return rinv[3:]

    def compatible(self, x, y):
        return self.beta(x) == y[0][:self.n - 3]

    def disjoint(self, x, y):
        return self.block(x[0]) != self.block(y[0]) and not (self.visible(x) & self.visible(y))

    def trail(self, rows, gmax=None):
        """(ok, reason).  ModelTrail + optional charge budget."""
        for r in rows:
            if not self.admissible(r):
                return False, "admissible"
        for x, y in zip(rows, rows[1:]):
            if not self.compatible(x, y):
                return False, "compat"
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                if not self.disjoint(rows[i], rows[j]):
                    return False, "class/block"
        if gmax is not None and sum(self.charge(r) for r in rows) > gmax:
            return False, "charge"
        return True, "ok"
