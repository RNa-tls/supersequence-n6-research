#!/usr/bin/env python3
"""Round 155 -- exhaustive abstract test of the incidence slack identity.

THE UNIVERSE.  Fix m >= 2.  Let T be the standard m-cycle (0 1 ... m-1).  The
universe is ALL m! permutations alpha of {0..m-1}, with beta := T alpha^{-1}.

WHY FIXING T LOSES NOTHING.  Conjugating the pair (alpha, T) by any pi sends
beta to pi beta pi^{-1} and permutes the alpha-cycles and beta-cycles without
changing any of A = c(alpha), K = c(beta), R_int, E or the isomorphism type of
the bipartite incidence graph.  All m-cycles are conjugate, so fixing T is an
exact quotient, not a sample.

WHAT IS CHECKED, for every pair:

  (I1)  m = E + R_int                       an exact identity
  (I2)  B is connected                      from T = beta alpha being an m-cycle
  (I3)  mu(B) = E - (A + K) + 1 >= 0        cyclomatic number of a connected graph
  (I4)  mu(B) = m + 1 - A - K - R_int       the slack identity
  (I5)  K + R_int <= m + 1 - A              the incidence bound (= I3 + I4)
  (I6)  mu(B) = 0  <=>  B is a tree
  (I7)  slack = 0  =>  R_int = 0 and B is a tree
        (the implication H.tight uses; slack := m + 1 - A - K - R_int is not
         the hypothesis -- the hypothesis is (m + 1 - A) - K = 0, i.e. g = 0)
  (I8)  g := ((m + 1 - A) - K)/2 integral, and 2g = mu + R_int

In the L6 instance m = P + 1 = 121 + G, A = 121, so m + 1 - A = G + 1 and (I5)
is exactly K + R_int <= G + 1.
"""
from __future__ import annotations
import itertools, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def cycles(p):
    seen, out = [False] * len(p), []
    for s in range(len(p)):
        if seen[s]:
            continue
        c, x = [], s
        while not seen[x]:
            seen[x] = True
            c.append(x)
            x = p[x]
        out.append(c)
    return out


def test(m):
    T = [(i + 1) % m for i in range(m)]
    fails = Counter()
    examined = 0
    g_parity_fail = 0
    stats = Counter()
    for a in itertools.permutations(range(m)):
        examined += 1
        ainv = [0] * m
        for i, x in enumerate(a):
            ainv[x] = i
        beta = [T[ainv[x]] for x in range(m)]
        ac, bc = cycles(list(a)), cycles(beta)
        A, K = len(ac), len(bc)
        aid = [0] * m
        for j, c in enumerate(ac):
            for x in c:
                aid[x] = j
        R_int, edges = 0, set()
        for j, c in enumerate(bc):
            cnt = Counter(aid[x] for x in c)
            R_int += sum(v - 1 for v in cnt.values())
            for q in cnt:
                edges.add((q, j))
        E = len(edges)
        adj = {}
        for q, j in edges:
            adj.setdefault(("a", q), set()).add(("b", j))
            adj.setdefault(("b", j), set()).add(("a", q))
        seen, stack = set(), [next(iter(adj))]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            stack.extend(adj[x] - seen)
        connected = len(seen) == A + K
        mu = E - (A + K) + 1
        if m != E + R_int:
            fails["I1_m_eq_E_plus_Rint"] += 1
        if not connected:
            fails["I2_connected"] += 1
        if mu < 0:
            fails["I3_mu_nonneg"] += 1
        if mu != m + 1 - A - K - R_int:
            fails["I4_slack_identity"] += 1
        if K + R_int > m + 1 - A:
            fails["I5_incidence_bound"] += 1
        tree = connected and E == A + K - 1
        if (mu == 0) != tree:
            fails["I6_mu0_iff_tree"] += 1
        twog = (m + 1 - A) - K
        if twog % 2:
            g_parity_fail += 1
        if twog == 0:
            if R_int != 0 or not tree:
                fails["I7_g0_forces_Rint0_and_tree"] += 1
            stats["g0_cases"] += 1
        if twog != mu + R_int:
            fails["I8_2g_eq_mu_plus_Rint"] += 1
    return dict(m=m, universe_size=examined, examined=examined, exhaustive=True,
                quotient="T fixed to the standard m-cycle (conjugation; exact)",
                pruning="none",
                failures=dict(fails), parity_odd_2g=g_parity_fail,
                g0_cases=stats["g0_cases"],
                ok=not fails)


def main(mmax=8):
    out = dict(tests=[])
    for m in range(2, mmax + 1):
        r = test(m)
        out["tests"].append(r)
        print(f"  m={m}: universe={r['universe_size']:,} exhaustive="
              f"{r['exhaustive']} g0_cases={r['g0_cases']:,} "
              f"failures={r['failures']} odd_2g={r['parity_odd_2g']}")
    out["ok"] = all(t["ok"] for t in out["tests"])
    out["total_pairs_examined"] = sum(t["examined"] for t in out["tests"])
    (ROOT / "r155" / "certs" / "abstract_slack_155.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print("total examined:", f"{out['total_pairs_examined']:,}", " ok:", out["ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 8))
