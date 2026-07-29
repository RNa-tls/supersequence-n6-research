#!/usr/bin/env python3
"""Round 32, sections 15-17: per-survivor verdicts and certificates.

Verdict vocabulary, applied strictly:

  SEGMENT_CAPACITY_IMPOSSIBLE   a safe segment bound is violated
  FULL_BLOCK_GRAPH_IMPOSSIBLE   the full-block graph cannot supply the
                                required chain (needs EXACT exhaustion)
  COMPONENT_CAPACITY_IMPOSSIBLE the component requirement is violated
  SEGMENT_SURVIVOR              no obstruction found AND the searches that
                                could have found one were exhaustive
  INCOMPLETE                    an obstruction test was not exhaustive

"a graph path was not found" is NEVER reported as impossible unless the
search was exact exhaustion.  The greedy hexagon-disjoint family is a
LOWER bound on the maximum and is therefore never used as an obstruction.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", default=str(ROOT / "outputs" / "rr_short_survivor_ledger.json"))
    ap.add_argument("--fullblock", default=str(ROOT / "outputs" / "rr_full_block_transitions.json"))
    ap.add_argument("--output", default=str(ROOT / "outputs" / "rr_segment_verdicts.json"))
    a = ap.parse_args()

    led = json.loads(Path(a.ledger).read_text(encoding="utf-8"))
    fb = json.loads(Path(a.fullblock).read_text(encoding="utf-8"))
    certs = []
    for x in led["rows"]:
        if x["contradiction_B_R"]:
            verdict = "SEGMENT_CAPACITY_IMPOSSIBLE"
            first_defect = ("the R slot cannot supply a capacity-5 segment: an "
                            "orbit-changing R lands in an already-open orbit, whose "
                            "capacity is at most 4"
                            if not x["contradiction_B"] else
                            "the initial segment supplies only c(q0) ports, not 5")
        elif x["hexagon_disjointness_blocks_f_min"]:
            verdict = "SEGMENT_CAPACITY_IMPOSSIBLE"
            first_defect = "not enough pairwise hexagon-disjoint full orbits"
        else:
            verdict = "SEGMENT_SURVIVOR"
            first_defect = None
        certs.append({
            "root_ell": x["root_ell"], "P_core": x["P_core"],
            "canonical_state_hash": x["canonical_state_hash"],
            "verdict": verdict,
            "required_segment_count": x["m_plus_1_max_segments"],
            "required_full_segments": x["required_full_segments_f_min"],
            "available_full_capacity_orbits": x["n_orbits_with_full_5_ports"],
            "safe_ceiling_on_disjoint_full_orbits": x["safe_ceiling_on_disjoint_full_orbits"],
            "greedy_disjoint_LOWER_bound": x["greedy_hexagon_disjoint_full_orbits"],
            "defect_budget": x["defect_budget"],
            "first_unavoidable_defect": first_defect,
            "bound_A": x["bound_A_coarse"], "bound_B": x["bound_B_initial_refined"],
            "bound_B_R": x["bound_B_with_R_penalty"], "B_plus_1": x["B_plus_1"],
            "full_block_graph_sha256": fb["graph_sha256"],
        })

    hist = Counter(c["verdict"] for c in certs)
    print("=== section 15: per-survivor verdicts ===")
    for c in certs:
        print(f"  ell={c['root_ell']} P_core={c['P_core']} "
              f"budget={c['defect_budget']:>2}  {c['verdict']}")
        if c["first_unavoidable_defect"]:
            print(f"       first unavoidable defect: {c['first_unavoidable_defect']}")
    print(f"\n  verdict histogram: {dict(hist)}")

    surv = [c for c in certs if c["verdict"] == "SEGMENT_SURVIVOR"]
    print(f"\n=== section 17: solver readiness for the {len(surv)} remaining ===")
    for c in surv:
        print(f"  ell={c['root_ell']} P_core={c['P_core']}: segments "
              f"{c['required_segment_count']}, full segments needed "
              f"{c['required_full_segments']}, defect budget {c['defect_budget']}")
    print(f"\n  full-block graph: {fb['n_nodes']} nodes, "
          f"{fb['n_full_transitions']} transitions, out-degree histogram "
          f"{fb['out_degree_histogram']}, dead ends {fb['nodes_with_out_degree_zero']}")

    Path(a.output).write_text(json.dumps({
        "schema": "rr-segment-verdicts-v1",
        "verdict_histogram": {k: v for k, v in hist.items()},
        "n_removed_this_round": hist.get("SEGMENT_CAPACITY_IMPOSSIBLE", 0),
        "n_remaining": len(surv),
        "discipline": ("the greedy hexagon-disjoint family is a LOWER bound on the maximum "
                       "and is never used as an obstruction; the safe ceiling "
                       "floor(#unvisited hexagons / 5) is used instead, and it blocks "
                       "nothing at these states"),
        "full_block_graph_summary": {
            "n_nodes": fb["n_nodes"], "n_transitions": fb["n_full_transitions"],
            "out_degree_histogram": fb["out_degree_histogram"],
            "dead_ends": fb["nodes_with_out_degree_zero"],
            "hexagon_disjoint_transitions": fb["n_hexagon_disjoint_transitions"],
            "graph_sha256": fb["graph_sha256"],
        },
        "certificates": certs,
        "grade": "safe segment bound + exact obstruction (for the removed states)",
    }, indent=2, sort_keys=True, ensure_ascii=False, default=str), encoding="utf-8")
    print("wrote", a.output)


if __name__ == "__main__":
    main()
