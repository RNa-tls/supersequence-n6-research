#!/usr/bin/env python3
"""Round 176 -- checker B: frame-coordinate checker (no hexagon enumeration, no F-iteration).

A row (start p = w_1..w_{n-1} s, length l, omitted set Om) is represented by
  W = cyclic word <w_1 .. w_{n-1}>, special s, visible positions V = {0..l-1} \\ Om,
where position i means "s right after w_i" (w_0 := w_{n-1}).
  beta  : symbolic endpoint formula (R174 Thm 2(a)):  beta_k = w_{(l+2+k) mod (n-1)},
          k = 0..n-4 (indices of the cyclic W).
  block : (canonical rotation of W, s).
  disjointness (universal frame rule, r176 report Lemma U):
    same block -> conflict.  s_x = s_y, different W -> disjoint.
    s_x != s_y: common hexagons exist only if W_x \\ s_y = W_y \\ s_x (as cycles) =: E;
      then e_x = symbol after s_y in W_x, e_y = symbol after s_x in W_y, and
      e_x != e_y: one common hexagon, at position idx_x(prev_{W_x}(e_y)) in x and
                  idx_y(prev_{W_y}(e_x)) in y;
      e_x == e_y: two, at (idx_x(s_y), idx_y(prev_{W_y}(s_x))) and
                  (idx_x(prev_{W_x}(s_y)), idx_y(s_x)).
      conflict iff some common hexagon is visible in both rows.
Shares no code with checker A."""


class CheckerB:
    def __init__(self, n):
        self.n = n

    @staticmethod
    def canon(cyc):
        k = len(cyc)
        return min(tuple(cyc[i:] + cyc[:i]) for i in range(k))

    def rep(self, row):
        p, l, om = row
        n = self.n
        W = list(p[:n - 1])
        return dict(W=W, s=p[n - 1], V=set(range(l)) - set(om), l=l)

    def idx(self, W, t):
        i = W.index(t) + 1                       # 1-based
        return 0 if i == self.n - 1 else i

    @staticmethod
    def after(W, t):
        return W[(W.index(t) + 1) % len(W)]

    @staticmethod
    def before(W, t):
        return W[(W.index(t) - 1) % len(W)]

    def admissible(self, row):
        p, l, om = row
        n = self.n
        return (sorted(p) == list(range(n)) and 1 <= l <= n - 1 and len(set(om)) == len(om)
                and all(0 < i < l - 1 for i in om))

    def charge(self, row):
        return (self.n - 1 - row[1]) + len(row[2])

    def beta(self, row):
        p, l, _ = row
        n = self.n
        W = p[:n - 1]
        return tuple(W[(l + 1 + k) % (n - 1)] for k in range(n - 3))

    def compatible(self, x, y):
        return self.beta(x) == tuple(y[0][:self.n - 3])

    def disjoint(self, x, y):
        X, Y = self.rep(x), self.rep(y)
        if X["s"] == Y["s"]:
            return self.canon(X["W"]) != self.canon(Y["W"])
        sx, sy = X["s"], Y["s"]
        Kx = [t for t in X["W"] if t != sy]
        Ky = [t for t in Y["W"] if t != sx]
        if self.canon(Kx) != self.canon(Ky):
            return True
        ex, ey = self.after(X["W"], sy), self.after(Y["W"], sx)
        if ex != ey:
            common = [(self.idx(X["W"], self.before(X["W"], ey)), self.idx(Y["W"], self.before(Y["W"], ex)))]
        else:
            common = [(self.idx(X["W"], sy), self.idx(Y["W"], self.before(Y["W"], sx))),
                      (self.idx(X["W"], self.before(X["W"], sy)), self.idx(Y["W"], sx))]
        return not any(a in X["V"] and b in Y["V"] for a, b in common)

    def trail(self, rows, gmax=None):
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
