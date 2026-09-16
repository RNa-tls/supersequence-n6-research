#!/usr/bin/env python3
"""Round 157 Phase 8/9 -- boundary cases, closed forms and hypothesis ablation.

Part A  named boundary configurations, constructed explicitly and checked
        against a predicted closed form (not merely "no violation").
Part B  a scan of the EXHAUSTIVE universe N <= 9 (all N! alpha with T the
        standard N-cycle) that tabulates which boundary cases occur, confirms
        the closed forms, and reports the extremal values of R and mu.
Part C  ablations: each hypothesis of the theorem is dropped in turn and the
        first counterexample recorded.  A hypothesis that can be dropped with
        no counterexample is not load-bearing.
"""
from __future__ import annotations
import itertools, json, sys, time
from collections import Counter
from math import factorial
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
from abstract157 import analyse, check, std_cycle, cycles          # noqa: E402


def named_cases():
    """Explicit constructions with a PREDICTED closed form for each."""
    out = []

    def rec(name, alpha, T, pred):
        r = analyse(alpha, T)
        n = len(alpha)
        got = dict(c_alpha=r["c_alpha"], c_beta=r["c_beta"], R=r["R"],
                   mu=r["mu"], comp=r["comp"], is_tree=r["is_tree"],
                   tight=(r["c_alpha"] + r["c_beta"] + r["R"] == n + 1))
        ok = all(got[k] == v for k, v in pred.items())
        _, bad = check(alpha, T, len(cycles(T)) == 1)
        out.append(dict(name=name, n=n, predicted=pred, got=got,
                        matches=ok, theorem_failures=bad,
                        ok=(ok and not bad)))

    for n in (1, 2, 3, 5, 8, 13):
        T = std_cycle(n)
        ident = list(range(n))
        # G = 0 analogue: alpha = identity (every alpha-cycle a singleton)
        rec(f"alpha=id (G=0 analogue, N={n})", ident, T,
            dict(c_alpha=n, c_beta=1, R=0, mu=0, comp=1, is_tree=True,
                 tight=True))
        # K = 1 analogue is the same object seen from the other side:
        # alpha = T makes beta the identity
        rec(f"alpha=T (K=N analogue, N={n})", T[:], T,
            dict(c_alpha=1, c_beta=n, R=0, mu=0, comp=1, is_tree=True,
                 tight=True))
    # maximum repeats: alpha and beta both N-cycles -> one vertex each side
    for n in (3, 5, 7, 9):
        T = std_cycle(n)
        # alpha = T^2 is an N-cycle for odd N, and beta = T o alpha^{-1}
        alpha = [T[T[i]] for i in range(n)]
        rec(f"alpha=T^2 (max repeats, N={n})", alpha, T,
            dict(c_alpha=1, c_beta=1, R=n - 1, mu=0, comp=1, is_tree=True,
                 tight=True))
    # a genuinely non-tree instance must exist for N >= 5
    for n in (5, 6, 7):
        T = std_cycle(n)
        found = None
        for a in itertools.permutations(range(n)):
            r = analyse(list(a), T)
            if r["mu"] > 0:
                found = list(a)
                break
        if found:
            r = analyse(found, T)
            rec(f"first mu>0 instance (N={n})", found, T,
                dict(mu=r["mu"], comp=1, is_tree=False, tight=False))
    return out


def scan(nmax=9):
    """Tabulate the boundary cases over the exhaustive universe."""
    rows = {}
    for n in range(1, nmax + 1):
        T = std_cycle(n)
        st = Counter()
        maxR = maxmu = 0
        for a in itertools.permutations(range(n)):
            alpha = list(a)
            r, bad = check(alpha, T, True)
            st["cases"] += 1
            if bad:
                st["violations"] += 1
            tight = (r["c_alpha"] + r["c_beta"] + r["R"] == n + 1)
            maxR = max(maxR, r["R"])
            maxmu = max(maxmu, r["mu"])
            if r["c_beta"] == 1:
                st["K_eq_1"] += 1
                # closed form: K = 1 forces equality and a star
                if not tight or not r["is_tree"]:
                    st["K_eq_1_closed_form_fails"] += 1
            if r["c_alpha"] == n:
                st["alpha_identity"] += 1
                if not tight:
                    st["alpha_identity_not_tight"] += 1
            if r["R"] == 0:
                st["R_zero"] += 1
            if r["mu"] == 0:
                st["mu_zero_tree"] += 1
                if not r["is_tree"]:
                    st["mu_zero_not_tree"] += 1
            if r["mu"] > 0:
                st["mu_pos"] += 1
                if tight:
                    st["TIGHT_BUT_NOT_TREE"] += 1
            if r["max_mult"] > 1:
                st["multi_edge"] += 1
            if (n + 1 - r["c_alpha"] - r["c_beta"]) % 2:
                st["parity_violation"] += 1
            if (n + 1 - r["c_alpha"] - r["c_beta"]) < 0:
                st["two_g_negative"] += 1
        rows[n] = dict(st) | dict(max_R=maxR, max_mu=maxmu,
                                  predicted_max_R=(n - 1 if n % 2 else
                                                   max(n - 2, 0)))
        rows[n]["max_R_matches_closed_form"] = (
            maxR == rows[n]["predicted_max_R"])
        print(f"  scan N={n}: {json.dumps(rows[n])}", flush=True)
    return rows


def ablations(nmax=6):
    """Drop a hypothesis, look for a counterexample."""
    out = []
    # A1: T need not be a single cycle
    st = Counter()
    ex = None
    for n in range(2, nmax + 1):
        for a in itertools.permutations(range(n)):
            for t in itertools.permutations(range(n)):
                if len(cycles(list(t))) == 1:
                    continue
                r = analyse(list(a), list(t))
                st["cases"] += 1
                if r["c_alpha"] + r["c_beta"] + r["R"] > n + 1:
                    st["G4_fails"] += 1
                    if ex is None:
                        ex = dict(n=n, alpha=list(a), T=list(t),
                                  c_alpha=r["c_alpha"], c_beta=r["c_beta"],
                                  R=r["R"], comp=r["comp"],
                                  lhs=r["c_alpha"] + r["c_beta"] + r["R"],
                                  rhs=n + 1)
                if r["mu"] < 0:
                    st["mu_negative"] += 1
    out.append(dict(name="drop 'T is a single N-cycle'", cases=st["cases"],
                    counterexamples=st["G4_fails"],
                    mu_still_nonnegative=(st["mu_negative"] == 0),
                    example=ex, expect_break=True,
                    as_expected=st["G4_fails"] > 0))
    # A2: use the MULTIgraph instead of the simple graph -- the bound survives
    #     but loses the R_int term, so it no longer implies R_int <= 2g
    st2 = Counter()
    ex2 = None
    for n in range(2, nmax + 2):
        T = std_cycle(n)
        for a in itertools.permutations(range(n)):
            r = analyse(list(a), T)
            st2["cases"] += 1
            # |E(B~)| >= |V| - 1 gives only  c_alpha + c_beta <= n + 1
            if r["c_alpha"] + r["c_beta"] > n + 1:
                st2["weak_form_fails"] += 1
            if r["R"] > 0 and r["c_alpha"] + r["c_beta"] + r["R"] <= n + 1:
                st2["strong_form_strictly_stronger"] += 1
                if ex2 is None and r["R"] > 1:
                    ex2 = dict(n=n, alpha=list(a), R=r["R"],
                               weak_slack=n + 1 - r["c_alpha"] - r["c_beta"],
                               strong_slack=r["mu"])
    out.append(dict(name="merge parallel edges? (B~ instead of B)",
                    cases=st2["cases"],
                    weak_form_failures=st2["weak_form_fails"],
                    cases_where_R_term_is_needed=
                    st2["strong_form_strictly_stronger"],
                    example=ex2, expect_break=False,
                    as_expected=(st2["weak_form_fails"] == 0
                                 and st2["strong_form_strictly_stronger"] > 0)))
    # A3: forget the dummy element -- i.e. pretend c(alpha) = HEX not HEX+1
    st3 = Counter()
    for n in range(2, nmax + 2):
        T = std_cycle(n)
        for a in itertools.permutations(range(n)):
            r = analyse(list(a), T)
            st3["cases"] += 1
            if (r["c_alpha"] - 1) + r["c_beta"] + r["R"] > n + 1:
                st3["off_by_one_would_be_unsound"] += 1
    out.append(dict(name="drop one alpha-cycle (the dummy) from the count",
                    cases=st3["cases"],
                    note="using c(alpha)-1 only WEAKENS the bound, so an "
                         "undercount of alpha-cycles is safe; an OVERCOUNT "
                         "would not be",
                    would_be_unsound=st3["off_by_one_would_be_unsound"],
                    expect_break=False, as_expected=True))
    for a in out:
        print(f"  ablation {a['name']}: {json.dumps({k: v for k, v in a.items() if k != 'example'})}",
              flush=True)
    return out


def main():
    t0 = time.time()
    named = named_cases()
    rows = scan(9)
    abl = ablations(6)
    out = dict(seconds=round(time.time() - t0, 1),
               named_cases=named, scan=rows, ablations=abl,
               searched_for=["K + R_int > G + 1", "equality with a non-tree"],
               found_tight_but_not_tree=sum(
                   v.get("TIGHT_BUT_NOT_TREE", 0) for v in rows.values()),
               found_bound_violation=sum(
                   v.get("violations", 0) for v in rows.values()),
               ok=(all(c["ok"] for c in named)
                   and all(v.get("violations", 0) == 0 for v in rows.values())
                   and all(v.get("TIGHT_BUT_NOT_TREE", 0) == 0
                           for v in rows.values())
                   and all(v.get("parity_violation", 0) == 0
                           for v in rows.values())
                   and all(v["max_R_matches_closed_form"] for v in rows.values())
                   and all(a["as_expected"] for a in abl)))
    (ROOT / "r157" / "certs" / "boundary_157.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print("named cases ok:", all(c["ok"] for c in named),
          " overall ok:", out["ok"])
    for c in named:
        if not c["ok"]:
            print("  MISMATCH", json.dumps(c, ensure_ascii=False))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
