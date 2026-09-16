#!/usr/bin/env python3
"""Round 157 -- the incidence theorem in its ABSTRACT form, decided exhaustively.

THE ABSTRACT SETTING (no words, no hexagons, no n = 6).

  X        a finite set, |X| = N
  alpha    any permutation of X
  T        any permutation of X                (the repository uses an N-cycle)
  beta     := T o alpha^{-1},  so  beta o alpha = T
  B~       the BIPARTITE MULTIGRAPH whose vertices are the alpha-cycles
           together with the beta-cycles, with ONE EDGE PER ELEMENT x in X
           joining the alpha-cycle of x to the beta-cycle of x
  B        the simple graph obtained by merging parallel edges
  R        := |E(B~)| - |E(B)| = sum over pairs (A, C) of (|A cap C| - 1)

THE GENERAL THEOREM

  (G1)  comp(B) = the number of <alpha, beta>-orbits on X
  (G2)  mu(B) := |E(B)| - |V(B)| + comp(B) = N - R - c(alpha) - c(beta) + comp(B)
  (G3)  mu(B) >= 0, i.e.   c(alpha) + c(beta) + R <= N + comp(B)
  (G4)  if T is an N-cycle then comp(B) = 1, giving
            c(alpha) + c(beta) + R <= N + 1
  (G5)  equality in (G4)  <=>  mu(B) = 0  <=>  B is a TREE
  (G6)  parity: c(alpha) + c(beta) = N + 1  (mod 2) when T is an N-cycle,
        so  2g := N + 1 - c(alpha) - c(beta)  is a non-negative EVEN integer
  (G7)  the split identity   2g = mu(B) + R

The repository instance is  N = P + 1 = 121 + G,  c(alpha) = 121,
c(beta) = K,  R = R_int, which turns (G4) into  K + R_int <= G + 1  and (G7)
into  2g = mu(B) + R_int.

THE FINITE UNIVERSE.  Conjugation by g in Sym(X) sends (alpha, T) to
(g alpha g^-1, g T g^-1), sends beta to g beta g^-1, and induces an isomorphism
of B~.  All N-cycles are conjugate, so FIXING T to the standard cycle
(0 1 ... N-1) loses nothing: the universe of the theorem at size N is exactly
the N! permutations alpha, and the sweep below is EXHAUSTIVE over it.  The
unreduced universe has N! * (N-1)! pairs (alpha, T).

The `any_T` sweep additionally drops the N-cycle hypothesis to check (G1)-(G3)
and to show where connectivity -- and only connectivity -- is used.
"""
from __future__ import annotations
import itertools, json, random, sys, time
from collections import Counter
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def cycles(perm):
    n = len(perm)
    seen = [False] * n
    out = []
    for i in range(n):
        if seen[i]:
            continue
        c, x = [], i
        while not seen[x]:
            seen[x] = True
            c.append(x)
            x = perm[x]
        out.append(c)
    return out


def cycle_id(cyc, n):
    out = [0] * n
    for i, c in enumerate(cyc):
        for x in c:
            out[x] = i
    return out


def analyse(alpha, T):
    """Build B~ / B and return every quantity the theorem talks about."""
    n = len(alpha)
    ainv = [0] * n
    for x in range(n):
        ainv[alpha[x]] = x
    beta = [T[ainv[x]] for x in range(n)]
    ac, bc = cycles(alpha), cycles(beta)
    A, C = cycle_id(ac, n), cycle_id(bc, n)
    ca, cb = len(ac), len(bc)
    multi = Counter((A[x], C[x]) for x in range(n))
    E_multi, E_simple = sum(multi.values()), len(multi)
    R = E_multi - E_simple
    V = ca + cb
    # union-find over the simple graph, and an independent acyclicity test
    par = list(range(V))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    cyc_found = False
    for (a, c) in multi:
        ra, rc = find(a), find(ca + c)
        if ra == rc:
            cyc_found = True
        else:
            par[ra] = rc
    comp = len({find(v) for v in range(V)})
    mu = E_simple - V + comp
    # <alpha, beta>-orbits
    seen, orbits = [False] * n, 0
    for s in range(n):
        if seen[s]:
            continue
        orbits += 1
        stack = [s]
        seen[s] = True
        while stack:
            x = stack.pop()
            for y in (alpha[x], beta[x], ainv[x]):
                if not seen[y]:
                    seen[y] = True
                    stack.append(y)
    return dict(n=n, beta=beta, c_alpha=ca, c_beta=cb, R=R, V=V,
                E_multi=E_multi, E_simple=E_simple, comp=comp, mu=mu,
                orbits=orbits, acyclic=not cyc_found,
                is_tree=(comp == 1 and not cyc_found),
                max_mult=max(multi.values()),
                min_degree=min(Counter(
                    [a for a, _ in multi] + [ca + c for _, c in multi]).values())
                if multi else 0)


def check(alpha, T, T_is_cycle):
    r = analyse(alpha, T)
    n, bad = r["n"], []
    if r["E_multi"] != n:
        bad.append("E_multi")
    if r["comp"] != r["orbits"]:                                   # (G1)
        bad.append("G1_comp_ne_orbits")
    if r["mu"] != n - r["R"] - r["c_alpha"] - r["c_beta"] + r["comp"]:  # (G2)
        bad.append("G2_euler")
    if r["mu"] < 0:                                                # (G3)
        bad.append("G3_mu_negative")
    if r["c_alpha"] + r["c_beta"] + r["R"] > n + r["comp"]:        # (G3')
        bad.append("G3_general_bound")
    if r["min_degree"] < 1:
        bad.append("isolated_vertex")
    if T_is_cycle:
        if r["comp"] != 1:                                         # (G4)
            bad.append("G4_not_connected")
        if r["c_alpha"] + r["c_beta"] + r["R"] > n + 1:
            bad.append("G4_bound")
        tight = (r["c_alpha"] + r["c_beta"] + r["R"] == n + 1)
        if tight != r["is_tree"]:                                  # (G5)
            bad.append("G5_tight_iff_tree")
        if tight != (r["mu"] == 0):
            bad.append("G5_tight_iff_mu0")
        two_g = n + 1 - r["c_alpha"] - r["c_beta"]
        if two_g % 2:                                              # (G6)
            bad.append("G6_parity")
        if two_g < 0:
            bad.append("G6_two_g_negative")
        if two_g != r["mu"] + r["R"]:                              # (G7)
            bad.append("G7_split_identity")
    return r, bad


def std_cycle(n):
    return [(i + 1) % n for i in range(n)]


def sweep_exhaustive(n):
    """EXHAUSTIVE over all n! alpha with T fixed to the standard n-cycle."""
    T = std_cycle(n)
    st, ex = Counter(), []
    prof = Counter()
    for alpha in itertools.permutations(range(n)):
        r, bad = check(list(alpha), T, True)
        st["cases"] += 1
        prof[(r["c_alpha"], r["c_beta"], r["R"], r["mu"], r["is_tree"])] += 1
        if bad:
            st["violations"] += 1
            for b in bad:
                st["v_" + b] += 1
            if len(ex) < 4:
                ex.append(dict(n=n, alpha=list(alpha), broke=bad))
    return st, ex, prof


def sweep_any_T(n, sample=None, rng=None):
    """T no longer an n-cycle: (G1)-(G3) must still hold, (G4)-(G7) need not."""
    st, ex = Counter(), []
    src = (((list(a), list(t)) for a in itertools.permutations(range(n))
            for t in itertools.permutations(range(n))) if not sample
           else ((rng.sample(range(n), n), rng.sample(range(n), n))
                 for _ in range(sample)))
    for alpha, T in src:
        is_cycle = len(cycles(T)) == 1
        r, bad = check(alpha, T, False)
        st["cases"] += 1
        if is_cycle:
            st["T_is_a_cycle"] += 1
        elif r["comp"] == 1:
            st["disconnected_T_but_B_connected"] += 1
        elif r["c_alpha"] + r["c_beta"] + r["R"] > n + 1:
            # the n=6 form FAILS here: this is what connectivity buys
            st["G4_form_fails_without_cycle_T"] += 1
        if bad:
            st["violations"] += 1
            for b in bad:
                st["v_" + b] += 1
            if len(ex) < 4:
                ex.append(dict(n=n, alpha=alpha, T=T, broke=bad))
    return st, ex


def sweep_sampled(n, tries, rng):
    T = std_cycle(n)
    st, ex = Counter(), []
    base = list(range(n))
    for _ in range(tries):
        alpha = base[:]
        rng.shuffle(alpha)
        r, bad = check(alpha, T, True)
        st["cases"] += 1
        if bad:
            st["violations"] += 1
            for b in bad:
                st["v_" + b] += 1
            if len(ex) < 4:
                ex.append(dict(n=n, alpha=alpha, broke=bad))
    return st, ex


def main():
    t0 = time.time()
    rng = random.Random(157157)
    out = {"exhaustive": [], "any_T": [], "sampled": []}
    for n in range(1, 10):
        st, ex, prof = sweep_exhaustive(n)
        out["exhaustive"].append(dict(
            n=n, universe_alpha=factorial(n),
            universe_alpha_T_pairs=factorial(n) * factorial(max(n - 1, 1)),
            cases=st["cases"], violations=st["violations"], examples=ex,
            distinct_profiles=len(prof),
            max_R=max(k[2] for k in prof), max_mu=max(k[3] for k in prof),
            trees=sum(v for k, v in prof.items() if k[4])))
        print(f"  exhaustive n={n}: {st['cases']:,} cases "
              f"(universe {factorial(n):,}) violations={st['violations']} "
              f"maxR={max(k[2] for k in prof)} maxmu={max(k[3] for k in prof)}",
              flush=True)
    for n in range(1, 7):
        st, ex = sweep_any_T(n)
        out["any_T"].append(dict(n=n, cases=st["cases"],
                                 violations=st["violations"],
                                 T_is_a_cycle=st["T_is_a_cycle"],
                                 disconnected_T_but_B_connected=
                                 st["disconnected_T_but_B_connected"],
                                 G4_form_fails_without_cycle_T=
                                 st["G4_form_fails_without_cycle_T"],
                                 examples=ex))
        print(f"  any_T n={n}: {st['cases']:,} cases violations="
              f"{st['violations']} G4-form-fails="
              f"{st['G4_form_fails_without_cycle_T']}", flush=True)
    for n, tries in ((10, 400000), (12, 300000), (16, 200000), (24, 120000),
                     (64, 40000), (121, 20000), (146, 20000)):
        st, ex = sweep_sampled(n, tries, rng)
        out["sampled"].append(dict(n=n, cases=st["cases"],
                                   violations=st["violations"], examples=ex))
        print(f"  sampled n={n}: {st['cases']:,} cases "
              f"violations={st['violations']}", flush=True)
    out["seconds"] = round(time.time() - t0, 1)
    out["exhaustive_cases"] = sum(e["cases"] for e in out["exhaustive"])
    out["any_T_cases"] = sum(e["cases"] for e in out["any_T"])
    out["sampled_cases"] = sum(e["cases"] for e in out["sampled"])
    out["ok"] = all(e["violations"] == 0 for e in
                    out["exhaustive"] + out["any_T"] + out["sampled"])
    (ROOT / "r157" / "certs" / "abstract_157.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print("exhaustive", out["exhaustive_cases"], "any_T", out["any_T_cases"],
          "sampled", out["sampled_cases"], "ok", out["ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
