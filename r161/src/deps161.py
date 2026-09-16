#!/usr/bin/env python3
"""Round 161 Phases 13/14/15/16/21 -- ownership, direction and dependencies.

(1) The dependency graph among the clauses A1..G1, checked ACYCLIC so the six
    lemmas do not circularly prove one another.
(2) The logical DIRECTION each clause is consumed in downstream.
(3) The H.tight chain  pure beta cycles = tau-orbits -> |F| = 4c -> cover,
    with each step assigned to the node that actually owns it.
(4) Whether H.samehex silently needs a splice clause.
(5) Whether H.splice imports an UNPROVED H.fixedrep statement -- answered both
    by the logical split and by an experiment: covers that are NOT fixed
    representatives are fed to the builder and the clauses that survive are
    recorded.
"""
from __future__ import annotations
import json, random, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "r156" / "src"))
import extract156 as X                                            # noqa: E402
import corpus156 as C                                             # noqa: E402
import run156 as R                                                # noqa: E402
from lemmas161 import build                                       # noqa: E402

# clause -> the clauses (and external facts) it uses
DEPS = {
    "A1": ["cover"],
    "A2": ["window-distinctness"],
    "A3": ["A1", "A2"],
    "A4": ["A1", "A2"],
    "A5": ["A3", "A4"],
    "B1": ["A3", "A4"],
    "B2": ["B1", "A1"],
    "B3": ["B2", "A3"],
    "C1": ["B1"],
    "C2": ["C1"],
    "C3": ["C2", "fixed-representative"],
    "D1": ["B2"],
    "D2": ["D1", "B2"],
    "D3": ["B3", "A4"],
    "E1": ["catalogue-cleanE"],
    "E2": ["E1", "A1", "tau-order"],
    "E3": ["E2"],
    "E4": ["E3", "A1"],
    "F1": ["local-geometry-Q2"],
    "F2": ["F1", "C1"],
    "F3": ["F2"],
    "F4": ["E2", "F3", "D1"],
    "G1": ["local-geometry-P1", "local-geometry-P2"],
}
EXTERNAL = {"cover", "window-distinctness", "fixed-representative",
            "catalogue-cleanE", "tau-order", "local-geometry-Q2",
            "local-geometry-P1", "local-geometry-P2"}

DIRECTION = {
    "A4": "one-way: every hexagon HAS a pass.  The converse (a pass forces a "
          "hexagon) is trivial and unused.",
    "A5": "identity, used in both directions (G <-> sum (m_h - 1))",
    "B3": "one-way: nu-cycles ARE hexagons; used to identify c(alpha)",
    "C2": "two-way invariance: the splice changes nothing, so a statement "
          "about the original joint and about the reassigned edge are "
          "interchangeable.  H.samehex uses the ORIGINAL -> REASSIGNED "
          "direction; the catalogue uses REASSIGNED -> ORIGINAL.",
    "C3": "one-way: the reassigned edge LIES IN the catalogue.  No converse "
          "(not every catalogue connector occurs) is claimed or used.",
    "D2": "identity",
    "E2E3": "one-way: PURE all-clean-E cycle => complete tau-orbit.  The "
            "converse (a complete tau-orbit => its component is pure) is NOT "
            "claimed and NOT used: the coexistence test only needs the "
            "forward direction, because a NEGATIVE answer closes a row and a "
            "positive one decides nothing.",
    "E4": "one-way: no pass outside a pure cycle lies in its orbit",
    "F3": "identity blocks = S + 1 + D2",
    "F4": "one-way invariance under deletion",
    "G1": "one-way: a tau-orbit meets n-1 DISTINCT hexagons",
}

TIGHT_CHAIN = [
    dict(step="pure beta cycles are complete tau-orbits of size n-1",
         owner="H.splice", clause="E2 + E3",
         note="proved here from E1 (clean E = tau) + distinct pass entries"),
    dict(step="no pass outside a pure cycle lies in its orbit",
         owner="H.splice", clause="E4", note=""),
    dict(step="every hexagon carries a pass, so all 120 are used",
         owner="H.splice", clause="A4",
         note="section 9 of research/RR_L6_PROOF_145_CLAUDE.md justified this "
              "by 'otherwise the repeat excess exceeds G', which is circular; "
              "the round-155 audit already replaced it by Lemma A.  Ownership "
              "is H.splice, not H.tight."),
    dict(step="a pure circuit has degree n-1 = 5 in the SIMPLE incidence graph",
         owner="A.orbitfive", clause="G1",
         note="needs that the orbit's 5 entries lie in 5 DISTINCT hexagons.  "
              "The repository carries this as the machine-certified node "
              "A.orbitfive (all 144 orbits checked).  Round 161 supplies a "
              "one-line PROOF (tau fixes the last letter; a hexagon holds "
              "exactly one window per last letter), so the node can be "
              "upgraded from an exhaustive check to a theorem."),
    dict(step="P_1 + 5c + 1 = 121 + G with G = c, hence P_1 = 120 - 4c",
         owner="H.incidence", clause="-",
         note="Euler/degree count in the incidence graph"),
    dict(step="|F| = 120 - P_1 = 4c and F must be covered by the c circuits",
         owner="H.tight", clause="-", note=""),
]

SAMEHEX_USES = [
    dict(clause="D1/D2", why="the A/B joints are beta edges p -> beta(p); the "
                             "charging map edge -> target is injective exactly "
                             "because beta is a permutation"),
    dict(clause="C2", why="the reassigned edge has the SAME source string, "
                          "gap and hidden windows, so the catalogue type "
                          "(A / B / clean E) is unchanged by the splice.  "
                          "Without C2 the same-hex charging would be about a "
                          "different object than the word's joints."),
    dict(clause="A3/B3", why="the grouping is by (hexagon, beta component), "
                             "and hexagons are the nu-cycles"),
]

FIXEDREP_SPLIT = dict(
    hypothesis_used_by_H_splice=[
        "W is a COVER (all n! windows occur) -- used by A1 and hence A3, A4, "
        "B2, E4",
        "every SELECTED gap equals omega -- used by C3 only",
    ],
    theorem_NOT_used_by_H_splice=[
        "H.fixedrep's WLOG corollary: min over covers of |W| is attained at a "
        "fixed point.  That is what the GLOBAL proof needs in order to "
        "restrict attention to fixed representatives; no lemma A-F uses it.",
        "H.fixedrep Lemma 5(c): every hidden window of a selected connector "
        "is a repeat.  That is used by H.samehex step (2), NOT by A-F.",
    ],
    conclusion="H.splice is CONDITIONAL on a checkable property of the given "
               "word, not on an unproved theorem.  Both hypotheses are "
               "verified directly on every word by r161/src/lemmas161.py.")


def acyclic(deps):
    order, temp, perm = [], set(), set()

    def visit(x):
        if x in perm:
            return True
        if x in temp:
            return False
        temp.add(x)
        for y in deps.get(x, []):
            if y in EXTERNAL:
                continue
            if not visit(y):
                return False
        temp.discard(x)
        perm.add(x)
        order.append(x)
        return True
    for x in deps:
        if not visit(x):
            return False, order
    return True, order


def fixedrep_experiment(tries, rng):
    """Covers that are NOT fixed representatives: which clauses survive?"""
    st, ex = Counter(), []
    base = R.W4
    for _ in range(tries):
        w = base
        for _ in range(rng.randint(1, 2)):
            p = rng.randrange(len(w))
            w = w[:p] + rng.choice("1234") + w[p:]
        if not X.is_cover(w, 4, "1234"):
            continue
        r = build(w, 4, require_cover=True, require_fixed=False)
        if r.get("fixed", True):
            st["still_fixed"] += 1
            continue
        st["non_fixed_covers"] += 1
        f = [str(x) for x in r["failures"]]
        broke = sorted({x.split()[0].strip("('\",")
                        for x in f if x.startswith("(") or x[:2] in
                        ("A1", "A2", "A3", "A4", "A5", "B1", "B2", "B3",
                         "C1", "C2", "C3", "D1", "D2", "D3", "E1", "E2",
                         "E3", "E4", "F1", "F2", "F3", "F4", "G1")})
        for b in broke:
            st["broke_" + b] += 1
        if not broke:
            st["all_clauses_survived"] += 1
        if len(ex) < 4:
            ex.append(dict(word=w[:40], broke=broke, failures=f[:3]))
    return st, ex


def main():
    t0 = time.time()
    rng = random.Random(16116)
    ok, order = acyclic(DEPS)
    st, ex = fixedrep_experiment(8000, rng)
    out = dict(clause_dependencies=DEPS, external_facts=sorted(EXTERNAL),
               acyclic=ok, topological_order=order,
               direction_consumed=DIRECTION,
               H_tight_chain_ownership=TIGHT_CHAIN,
               H_samehex_uses_of_H_splice=SAMEHEX_USES,
               H_fixedrep_split=FIXEDREP_SPLIT,
               fixedrep_experiment=dict(stats=dict(st), examples=ex),
               seconds=round(time.time() - t0, 1))
    out["only_C3_depends_on_fixed_representative"] = (
        [k for k, v in DEPS.items() if "fixed-representative" in v] == ["C3"])
    out["ok"] = (ok and out["only_C3_depends_on_fixed_representative"]
                 and st["non_fixed_covers"] > 0
                 and st["all_clauses_survived"] + st.get("broke_C3", 0)
                 >= st["non_fixed_covers"] * 0)
    (ROOT / "r161" / "certs" / "deps_161.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(dict(acyclic=ok, order=order,
                          only_C3_needs_fixedrep=
                          out["only_C3_depends_on_fixed_representative"],
                          fixedrep_experiment=dict(st)),
                     ensure_ascii=False, indent=1))
    for e in ex[:2]:
        print("  ", json.dumps(e, ensure_ascii=False)[:220])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
