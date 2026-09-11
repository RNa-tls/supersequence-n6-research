#!/usr/bin/env python3
"""L6 endgame — independent proof and check of the Round-142 incidence theorem.

    K + R_int <= G + 1,      K = G + 1  (mod 2)

SETTING.  After successor splicing the objects are the `P = 120 + G` selected
passes plus one dummy, so `n = P + 1 = 121 + G` elements.

  * `alpha` is the next-arc map `nu` on passes, extended by fixing the dummy.
    Its cycles are exactly the 120 rotation hexagons (a hexagon split into
    `m_h` arcs contributes one cycle of length `m_h`) plus the dummy, so
    `c(alpha) = 121` and `sum_h (m_h - 1) = G`.
  * `T` is the chronological successor, one `n`-cycle, so `c(T) = 1`.
  * `beta = T alpha^{-1}`, i.e. `beta alpha = T`, with `c(beta) = K`.

PARITY.  `sgn(alpha) = (-1)^{sum (m_h - 1)} = (-1)^G`, `sgn(T) = (-1)^{n-1}`.
From `sgn(beta) = sgn(T) sgn(alpha)` and `sgn(beta) = (-1)^{n-K}` we get
`n - K = n - 1 + G (mod 2)`, i.e. `K = G + 1 (mod 2)`.

THE BOUND.  Build the bipartite incidence graph on the 121 alpha-cycles and
the K beta-cycles, joining a hexagon to a component whenever they share a
pass.  `T = beta alpha` is an n-cycle, so `<alpha, beta>` is transitive and the
graph is CONNECTED; a connected bipartite graph on `121 + K` vertices has at
least `121 + K - 1` edges.  Counting elements by the pair they lie in,

    n = 121 + G = sum_{h,j} |h cap B_j| = E + sum_{h,j} (|h cap B_j| - 1)
                = E + R_int  >=  (121 + K - 1) + R_int,

which is exactly `K + R_int <= G + 1`.  `R_int` is by definition the
within-component duplicate-hexagon excess, so no other reading is possible.

The check below tests the statement on random instances of the ABSTRACT
setting (any alpha with 121 cycles, any beta with beta*alpha an n-cycle), so it
does not presuppose anything about superpermutations.
"""
from __future__ import annotations
import json, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def cycles(p):
    n = len(p)
    seen = [False] * n
    out = []
    for i in range(n):
        if seen[i]:
            continue
        c, x = [], i
        while not seen[x]:
            seen[x] = True
            c.append(x)
            x = p[x]
        out.append(c)
    return out


def instance(rng, n_hex, extra, n_elts=None):
    """Random alpha with `n_hex + 1` cycles and beta with beta*alpha an n-cycle."""
    # alpha: partition the elements into n_hex blocks plus one fixed dummy
    n = n_hex + extra + 1
    elts = list(range(n))
    dummy = n - 1
    rest = elts[:-1]
    rng.shuffle(rest)
    blocks, i = [], 0
    sizes = [1] * n_hex
    for _ in range(extra):
        sizes[rng.randrange(n_hex)] += 1
    for sz in sizes:
        blocks.append(rest[i:i + sz])
        i += sz
    alpha = [0] * n
    alpha[dummy] = dummy
    for b in blocks:
        for j, x in enumerate(b):
            alpha[x] = b[(j + 1) % len(b)]
    # T: a random n-cycle;  beta = T alpha^{-1}
    order = elts[:]
    rng.shuffle(order)
    T = [0] * n
    for j, x in enumerate(order):
        T[x] = order[(j + 1) % n]
    ainv = [0] * n
    for x in range(n):
        ainv[alpha[x]] = x
    beta = [T[ainv[x]] for x in range(n)]
    return alpha, beta, blocks, dummy


def check(trials=4000, seed=20260911):
    rng = random.Random(seed)
    bad, par = [], []
    for _ in range(trials):
        n_hex = rng.randint(2, 12)
        extra = rng.randint(0, 10)          # extra = G
        alpha, beta, blocks, dummy = instance(rng, n_hex, extra)
        G = extra
        comps = cycles(beta)
        K = len(comps)
        hexof = {}
        for hid, b in enumerate(blocks):
            for x in b:
                hexof[x] = hid
        hexof[dummy] = -1                   # the dummy is its own alpha-cycle
        R_int = 0
        for c in comps:
            cnt = {}
            for x in c:
                cnt[hexof[x]] = cnt.get(hexof[x], 0) + 1
            R_int += sum(v - 1 for v in cnt.values())
        if K + R_int > G + 1:
            bad.append(dict(G=G, K=K, R_int=R_int))
        if (K - (G + 1)) % 2:
            par.append(dict(G=G, K=K))
    return dict(trials=trials, bound_violations=len(bad), examples=bad[:3],
                parity_violations=len(par), parity_examples=par[:3],
                holds=(not bad and not par),
                statement="K + R_int <= G+1 and K == G+1 (mod 2)")


if __name__ == "__main__":
    r = check(int(sys.argv[1]) if len(sys.argv) > 1 else 4000)
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "rr_l6_incidence_144.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=1))
    print(json.dumps(r, ensure_ascii=False))
