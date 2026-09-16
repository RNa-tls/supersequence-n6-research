#!/usr/bin/env python3
"""Round 163 phase 16 -- how much of the capacity certification is
double-implemented, and which cells the census actually reads.

The recommendation for the next round has to name something concrete.  The
census reads certified capacities; those come from r152/src/checker152.py and
its C twin, which are INDEPENDENT of the production solver (they rebuild the
catalogue from string algebra and implement the feasibility theorem from its
statement).  But the two checkers do not cover the same cells: the Python one
runs under a 20M-node cap, so the expensive cells are certified by the C
checker alone.  This module measures that gap exactly.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CERT = ROOT / "r152" / "certs"


def load(name):
    return json.loads((CERT / name).read_text())


def main():
    c = load("verify_all_c152.json")
    p = load("verify_subset_152.json")
    pc = load("verify_piece_c152.json")
    pp = load("verify_piece_152.json")
    census = load("census_152.json")

    c_cells = {r["cell"]: r for r in c["rows"]}
    p_cells = {r["cell"]: r for r in p["rows"]}
    key = lambda r: f"{r['b']}|{r['d']}|{r['fp']}|{r['lp']}"
    pc_cells = {key(r): r for r in pc["rows"]}
    pp_cells = {key(r): r for r in pp["rows"]}

    chain_shared = sorted(set(c_cells) & set(p_cells))
    piece_shared = sorted(set(pc_cells) & set(pp_cells))
    chain_only_c = sorted(set(c_cells) - set(p_cells))
    piece_only_c = sorted(set(pc_cells) - set(pp_cells))
    chain_dis = [x for x in chain_shared
                 if c_cells[x]["cap"] != p_cells[x]["cap"]]
    piece_dis = [x for x in piece_shared
                 if pc_cells[x]["cap"] != pp_cells[x]["cap"]]

    out = dict(
        chain=dict(certified_by_C=len(c_cells), certified_by_python=len(p_cells),
                   python_is_a_subset_of_C=set(p_cells) <= set(c_cells),
                   double_implemented=len(chain_shared),
                   single_implementation_only=len(chain_only_c),
                   cap_disagreements_on_shared_cells=len(chain_dis),
                   python_node_cap=p.get("node_cap"),
                   C_node_caps=c.get("caps"),
                   C_total_nodes=c.get("total_nodes"),
                   statuses={s: sum(1 for r in c["rows"] if r["status"] == s)
                             for s in sorted({r["status"] for r in c["rows"]})}),
        piece=dict(certified_by_C=len(pc_cells),
                   certified_by_python=len(pp_cells),
                   python_is_a_subset_of_C=set(pp_cells) <= set(pc_cells),
                   double_implemented=len(piece_shared),
                   single_implementation_only=len(piece_only_c),
                   cap_disagreements_on_shared_cells=len(piece_dis),
                   python_node_cap=pp.get("node_cap"),
                   C_total_nodes=pc.get("total_nodes")),
        census_reads=dict(
            chain_cells_read=census["certified_cells_read"],
            chain_cells_unread=len(census["certified_cells_unread"]),
            piece_cells_read=census["piece_cells_read"],
            analytic_fallback_cells=census["analytic_fallback_cells"],
            analytic_fallback_uses=census["analytic_fallback_uses"],
            piece_fallback_vectors=len(census["piece_fallback_vectors"])),
        checker_independence=(
            "r152/src/checker152.py imports nothing from the production "
            "solvers: it rebuilds the joint catalogue from string algebra, "
            "implements the feasibility theorem from its statement and reads "
            "no production table.  Its only non-analytic prune is the "
            "monotone bound (P1) from cells it has itself already certified "
            "in the same run.  It is fail-closed: a search that hits the node "
            "cap is UNKNOWN_CAP, never 'verified'."),
        residual=(
            "every capacity the census reads is certified, and 0 cells are "
            "unread, but 247 of the 1,101 chain cells and 109 of the 220 "
            "piece cells carry ONE implementation's certification.  Those are "
            "exactly the expensive cells, the ones the 20M-node Python cap "
            "excludes.  This is a MACHINE residual, not a hand proof."),
    )
    out["single_implementation_cells_the_census_reads"] = (
        out["chain"]["single_implementation_only"]
        + out["piece"]["single_implementation_only"])
    out["ok"] = (not chain_dis and not piece_dis
                 and census["certified_cells_unread"] == []
                 and out["chain"]["python_is_a_subset_of_C"]
                 and out["piece"]["python_is_a_subset_of_C"])
    (ROOT / "r163" / "certs" / "coverage_163.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("checker_independence", "residual")},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
