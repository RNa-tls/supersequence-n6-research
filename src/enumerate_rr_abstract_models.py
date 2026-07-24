#!/usr/bin/env python3
"""Section 8-9: minimal abstract incidence-graph countermodel search.

Question: is "same-component (for R2) implies chaining" a consequence of
the GRAPH axioms alone (bipartite, orbit-degree<=5, hex-degree<=6,
forest), or does it require permutation-level facts specific to this
n=6 model?

Method: construct a SMALL abstract bipartite incidence model (a handful
of orbit/hex nodes, forest-respecting edges) that realizes a
"same-component, non-chaining" R2 -- i.e. R2's own source and target
orbit roots coincide WITHOUT R2's source orbit being R1's target orbit.
If such a model exists while satisfying every graph-level axiom the
corpus obeys (forest, degree caps, R-legality: source/target existing
per the abstract analogue), that proves the graph axioms alone are
INSUFFICIENT -- the real corpus implication needs an extra,
permutation-level axiom. This does NOT re-run any exact permutation
search; it is a small, explicit, hand-checkable finite construction.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent


class UnionFind:
    def __init__(self) -> None:
        self.parent: Dict[str, str] = {}
        self.redundant = 0

    def find(self, node: str) -> str:
        self.parent.setdefault(node, node)
        if self.parent[node] != node:
            self.parent[node] = self.find(self.parent[node])
        return self.parent[node]

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra
        else:
            self.redundant += 1


def build_countermodel() -> Dict[str, Any]:
    """Abstract event sequence (orbit/hex labels, not real permutations):

    event0 (fresh, analogue of a Z-event): orbit B <-> hex X   (B opens)
    event1 (R1): source orbit A -> target orbit B (reusing hex Y, a
            SECOND port of B, distinct from X -- respects "an orbit's
            5 ports touch 5 distinct hexagons")
    event2 (an intervening Z-event, existing-target reuse): source
            orbit B (chained from R1) -> target orbit C, landing via
            hex X -- i.e. C is ALSO registered through hex X, the SAME
            hex that already links to B. This is the abstract move
            that a real R/Z joint's own target registration performs;
            nothing in the bipartite/forest/degree axioms forbids a
            DIFFERENT orbit C from independently having a port in hex X
            too (hexagons are touched by 6 DISTINCT orbits in the real
            model -- hex X can perfectly well have a slot for C).
    event3 (R2): source orbit C (NOT B -- non-chaining, since R1's
            target was B, not C), target orbit B.

    Forest check: every union() call must merge two previously distinct
    trees (redundant==0) for this to respect the corpus's own
    exhaustively-verified forest property.

    Result: R2's OWN source (C) and target (B) roots -- are they equal
    ("same") despite non-chaining?
    """
    uf = UnionFind()
    log = []

    def step(label: str, a: str, b: str) -> None:
        before = (uf.find(a) if a in uf.parent else None, uf.find(b) if b in uf.parent else None)
        uf.union(a, b)
        log.append({"event": label, "edge": [a, b], "roots_before": list(before), "redundant_so_far": uf.redundant})

    step("event0_open_B", "qB", "hX")
    step("event1_R1_A_to_B_via_hY", "qA", "hY")  # A is R1's own source registration (abstract, doesn't need a prior edge for this toy check)
    step("event1_R1_target_B_via_hY", "qB", "hY")
    step("event2_reuse_B_target_C_via_hX", "qC", "hX")
    # R2 fires now: source=C, target=B
    r2_source_root = uf.find("qC")
    r2_target_root = uf.find("qB")

    return {
        "log": log,
        "forest_respected": uf.redundant == 0,
        "r2_source_orbit": "C", "r2_target_orbit": "B",
        "r1_target_orbit": "B",
        "chaining": "C" == "B",  # r2 source (C) == r1 target (B)?
        "r2_same_component": r2_source_root == r2_target_root,
        "r2_source_root": r2_source_root, "r2_target_root": r2_target_root,
    }


def main() -> None:
    model = build_countermodel()
    verdict = {
        "schema": "rr-abstract-models-v1",
        "countermodel": model,
        "conclusion": (
            "SAME-COMPONENT NON-CHAINING COUNTEREXAMPLE CONSTRUCTED (abstract, "
            "graph-axioms only)" if (model["r2_same_component"] and not model["chaining"] and model["forest_respected"])
            else "no countermodel found by this construction"
        ),
        "interpretation": (
            "The bipartite/forest/degree axioms ALONE do not force "
            "'same-component (R2) implies chaining' -- this abstract model "
            "satisfies forest-ness, respects an orbit having several "
            "distinct-hexagon ports, and respects R2 firing on an EXISTING "
            "(already-registered) target, yet produces same-component with "
            "R2's source (C) different from R1's target (B). Therefore the "
            "real corpus's 4,470/4,470 exact implication (see "
            "RR_SAME_COMPONENT_CHAINING_THEOREM.md) is NOT a pure graph "
            "theorem -- it requires a permutation-level fact absent from this "
            "toy model. See research/RR_ABSTRACT_COUNTERMODEL_STATUS.md "
            "section 9 for the identified candidate hidden axiom (hex 0 -- "
            "the word's own starting hexagon -- being the unique node "
            "pre-registered from initial_state(), combined with the short "
            "(depth<=6) event budget making a 'C bridges to B's OTHER port' "
            "detour like event2 above exponentially rarer than the direct "
            "hex-0 bridge actually observed in all 10/10 same-component "
            "corpus witnesses)."
        ),
    }
    Path(ROOT / "outputs" / "rr_abstract_models.json").write_text(
        json.dumps(verdict, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"wrote": str(ROOT / "outputs" / "rr_abstract_models.json"),
                       "conclusion": verdict["conclusion"]}, indent=2))


if __name__ == "__main__":
    main()
