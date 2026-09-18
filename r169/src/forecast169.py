#!/usr/bin/env python3
"""Round 169 phases 11, 12, 19, 20, 21 -- forecast, schedule, parallelism.

Three scenarios are costed on the same measured throughput.

  A  the round-168 plan: no (P1) closure in the census, 164 certificates.
  B  (P1) closure, candidates restricted to the old 190-cell basis.
  C  (P1) closure, any single-route tabulated chain cell may be certified,
     so a dominator outside the old basis competes on equal terms.

Throughput is measured, not assumed (round 168, batch 1):

    generator          38,246 search nodes/s, and a cell costs 2.1605x its
                       round-167 projection in search nodes because the
                       value-discovery pass roughly doubles it
    verifier B         39,144 proof nodes/s
    verifier A         41,487 proof nodes/s
    proof nodes        1.0759x the round-167 projection

Total wall clock is generation + verifier B + verifier A, never generation
alone, so a change in certificate node count propagates through all three.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")
INDEP, GEN, VB, VA, PROOF = 2.1605, 38246, 39144, 41487, 1.0759


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def cellstr(K):
    return "|".join(map(str, K))


def chain_dom(K, T):
    return all(t <= k for t, k in zip(T, K))


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def seconds(n):
    return n * INDEP / GEN + n * PROOF * (1 / VB + 1 / VA)


def main():
    rows = json.loads((ROOT / "r152" / "certs"
                       / "verify_all_c152.json").read_text())["rows"]
    N = {parse(r["cell"]): r["nodes"] for r in rows if r["status"] in GOOD}
    U = {parse(r["cell"]): r["cap"] for r in rows if r["status"] in GOOD}
    prows = json.loads((ROOT / "r152" / "certs"
                        / "verify_piece_c152.json").read_text())["rows"]
    PN = {(r["b"], r["d"], r["fp"], r["lp"]): r["nodes"] for r in prows
          if r["status"] in GOOD}

    def nodes(K):
        if N.get(K):
            return N[K], "measured chain search"
        p = (K[0], K[1], 0, 0)
        if K[2:] == (0, 0, 0, 0) and PN.get(p):
            return PN[p], "measured piece search of the same cell, which "\
                          "(BRIDGE-EQ) says counts the same walks"
        best = None
        for k, v in N.items():
            if v and all(x <= y for x, y in zip(K, k)):
                best = v if best is None else min(best, v)
        return best, "estimated from the cheapest measured dominating cell"

    st = json.loads((ROOT / "r168" / "certs" / "state_168.json").read_text())
    cov = json.loads((ROOT / "r169" / "certs" / "cover_169.json").read_text())
    clo = json.loads((ROOT / "r169" / "certs"
                      / "p1_closure_169.json").read_text())
    OPT = {parse(c) for c in st["optimum"]}
    sel = [parse(c) for c in cov["constructed"]["members"]]
    old_remaining = [parse(c) for c in st["remaining"]["cells"]]

    def plan(cells):
        per = [dict(cell=cellstr(K), projected_search_nodes=nodes(K)[0],
                    basis=nodes(K)[1], capacity=U.get(K)) for K in cells]
        tot = sum(p["projected_search_nodes"] or 0 for p in per)
        per.sort(key=lambda p: -(p["projected_search_nodes"] or 0))
        return dict(certificates=len(cells), projected_search_nodes=tot,
                    generation_nodes_with_discovery=int(tot * INDEP),
                    proof_nodes=int(tot * PROOF),
                    one_core_days=round(seconds(tot) / 86400, 1),
                    generation_days=round(tot * INDEP / GEN / 86400, 1),
                    verifier_b_days=round(tot * PROOF / VB / 86400, 1),
                    verifier_a_days=round(tot * PROOF / VA / 86400, 1),
                    top_10=per[:10],
                    fraction_in_top_10=(round(
                        sum(p["projected_search_nodes"] or 0 for p in per[:10])
                        / tot, 4) if tot else 0.0),
                    per_cell=per)

    A = plan(old_remaining)
    C = plan(sel)
    outside = [cellstr(K) for K in sel if K not in OPT]

    # ---------- parallelism: the domination DAG over the selection
    edges = [(cellstr(K), cellstr(T)) for K in sel for T in sel
             if K != T and chain_dom(K, T)]
    layer = {}

    def depth(K):
        if cellstr(K) in layer:
            return layer[cellstr(K)]
        ups = [J for J in sel if J != K and chain_dom(J, K)]
        layer[cellstr(K)] = 0 if not ups else 1 + max(depth(J) for J in ups)
        return layer[cellstr(K)]

    for K in sel:
        depth(K)
    layers = {}
    for K in sel:
        layers.setdefault(layer[cellstr(K)], []).append(cellstr(K))
    crit = max((nodes(K)[0] or 0) for K in sel)
    crit_cell = max(sel, key=lambda K: nodes(K)[0] or 0)
    par = {}
    for c in (1, 2, 4, 8):
        par[f"{c}_cores_days"] = round(
            max(seconds(C["projected_search_nodes"]) / c, seconds(crit))
            / 86400, 1)

    # ---------- the recommended round-170 batch: cheapest first WITHIN the
    # optimized set, because every member is (P1)-maximal and none of them
    # makes another cheaper, so ordering cannot buy pruning -- it can only buy
    # early falsification of the cost model
    order = sorted(sel, key=lambda K: (nodes(K)[0] or 0, K))
    batch = []
    for K in order:
        n, basis = nodes(K)
        ups = [cellstr(J) for J in sel if J != K and chain_dom(J, K)]
        downs = [cellstr(T) for T in OPT
                 if T != K and chain_dom(K, T) and T not in sel]
        batch.append(dict(
            cell=cellstr(K), projected_search_nodes=n, cost_basis=basis,
            capacity=U.get(K),
            predecessors_in_the_selection=ups,
            old_basis_cells_it_discharges_by_P1=len(downs),
            examples_discharged=sorted(downs)[:6],
            reason=("no selected cell dominates it, so it must be certified "
                    "directly; placed by ascending projected cost so a wrong "
                    "cost estimate surfaces in hours, not weeks"
                    if not ups else
                    "a selected dominator exists, so it is certified after "
                    "that dominator")))

    out = dict(
        inputs={p: sha(p) for p in
                ("r169/certs/cover_169.json", "r169/certs/p1_closure_169.json",
                 "r168/certs/state_168.json",
                 "r152/certs/verify_all_c152.json",
                 "r152/certs/verify_piece_c152.json")},
        throughput=dict(generator_nodes_per_second=GEN,
                        discovery_multiplier=INDEP,
                        verifier_b_nodes_per_second=VB,
                        verifier_a_nodes_per_second=VA,
                        proof_nodes_per_projected_node=PROOF,
                        source="round 168 batch 1, measured"),
        scenario_A_no_closure=A,
        scenario_B_closure_basis_only=dict(
            note="every member of the optimized set is already in the old "
                 "190-cell basis, so B and C coincide; no dominator outside "
                 "the basis was needed",
            certificates=len(sel), same_as_C=True,
            cells_outside_the_old_basis=outside),
        scenario_C_closure_any_cell=C,
        savings=dict(
            certificates=A["certificates"] - C["certificates"],
            certificate_factor=round(A["certificates"] / C["certificates"], 2),
            projected_search_nodes=A["projected_search_nodes"]
            - C["projected_search_nodes"],
            node_factor=round(A["projected_search_nodes"]
                              / C["projected_search_nodes"], 2),
            one_core_days_saved=round(A["one_core_days"] - C["one_core_days"], 1)),
        bracket=dict(lower_bound=clo["minimum"]["necessary"],
                     constructed=len(sel),
                     exact_minimum_proved=False,
                     why="the individually necessary cells do not close the "
                         "rows on their own, so necessity and sufficiency do "
                         "not meet as they did in rounds 165 and 167"),
        deferred_cells_resolved=dict(
            note="both round-168 deferrals are discharged by (P1), not by "
                 "cheaper generation",
            cells=[dict(cell="0|14|0|0|0|1", dominator="0|15|0|0|0|1",
                        dominator_capacity=U[(0, 15, 0, 0, 0, 1)],
                        own_capacity=U[(0, 14, 0, 0, 0, 1)],
                        equal=U[(0, 15, 0, 0, 0, 1)] == U[(0, 14, 0, 0, 0, 1)],
                        dominator_in_the_selection=(0, 15, 0, 0, 0, 1) in sel,
                        certificate_needed=False),
                   dict(cell="0|17|2|0|0|0", dominator="0|18|2|0|0|0",
                        dominator_capacity=U[(0, 18, 2, 0, 0, 0)],
                        own_capacity=U[(0, 17, 2, 0, 0, 0)],
                        equal=False,
                        dominator_in_the_selection=(0, 18, 2, 0, 0, 0) in sel,
                        certificate_needed=False,
                        comment="the closure only gives cap <= 107 where the "
                                "table says 103, and that is still enough to "
                                "close every exposed row")]),
        parallelism=dict(
            domination_edges=edges, layers={str(k): v for k, v in
                                            sorted(layers.items())},
            independent_cells=len(layers.get(0, [])),
            critical_path_cell=cellstr(crit_cell),
            critical_path_projected_nodes=crit,
            critical_path_days=round(seconds(crit) / 86400, 2),
            wall_clock=par,
            note="planning information only; the round-169 environment has "
                 "four cores and the standing rule is one CPU job at a time"),
        round_170_batch=batch,
    )
    (ROOT / "r169" / "certs" / "cost_forecast_169.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    show = json.loads(json.dumps(out))
    show.pop("inputs")
    for k in ("scenario_A_no_closure", "scenario_C_closure_any_cell"):
        show[k].pop("per_cell")
        show[k]["top_10"] = show[k]["top_10"][:4]
    show["round_170_batch"] = show["round_170_batch"][:4]
    show["parallelism"].pop("domination_edges")
    print(json.dumps(show, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
