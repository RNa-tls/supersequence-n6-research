#!/usr/bin/env python3
"""Round 167 phases 0-11 -- bridge-aware re-optimization of the basis.

Round 165 proved that 288 capacity FACTS are load bearing.  Round 166 added a
certified cross-model implication

    cap_piece(b, d, fp, lp)  <=  cap_chain(b, d, 0, 0, 0, 0)

so a single chain CERTIFICATE can discharge up to four piece facts.  The
number of facts has not changed; the number of certificates needed to support
them has.  This module recomputes that number exactly.

Round 166's enumeration was incomplete by construction: it only considered
chain cells that already appear in the round-152 capacity table.  A chain cell
that is absent from that table is still a perfectly well defined cell, and a
certificate can be generated for it directly (round 166 showed the
certificate-order prefix is not needed).  So the candidate universe here is
every (b, d, 0, 0, 0, 0) that some piece basis fact needs.
"""
from __future__ import annotations
import hashlib, json, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r163" / "src"))
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r165" / "src"))
sys.path.insert(0, str(ROOT / "r166" / "src"))
import hidden163 as H                                             # noqa: E402
import routeb164 as R                                             # noqa: E402
import closure165 as CL                                           # noqa: E402
import extree_basis_verify as V                                   # noqa: E402

CERTS = ROOT / "r152" / "certs"
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")
BATCHES = ["r164/certs/extree_prefix_164.txt.gz",
           "r166/certs/extree_batch2_166.txt.gz",
           "r166/certs/extree_batch3_166.txt.gz"]


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def certified_by_proof():
    """Cells with a verified exhaustion certificate, from the pinned report."""
    rep = json.loads((ROOT / "r166" / "certs"
                      / "verification_166.json").read_text())
    assert rep["all_ok"]
    out = {}
    for rel in BATCHES:
        import gzip
        text = gzip.decompress((ROOT / rel).read_bytes()).decode()
        for cell, capv, _ in V.parse_batch(text)[1]:
            out[cell] = capv
    return out


def main():
    g = json.loads((ROOT / "r165" / "certs"
                    / "row_closure_graph_165.json").read_text())
    ess = set(g["essential_cells"])
    chain_facts = sorted(c for c in ess if g["ablation"][c]["model"] == "chain")
    piece_facts = sorted(c for c in ess if g["ablation"][c]["model"] == "piece")

    vC = json.loads((CERTS / "verify_all_c152.json").read_text())
    pC = json.loads((CERTS / "verify_piece_c152.json").read_text())
    cn = {r["cell"]: r.get("nodes", 0) for r in vC["rows"]}
    ccap = {r["cell"]: r["cap"] for r in vC["rows"] if r["status"] in GOOD}
    pn = {f"{r['b']}|{r['d']}|{r['fp']}|{r['lp']}": r.get("nodes", 0)
          for r in pC["rows"]}
    pcap = {f"{r['b']}|{r['d']}|{r['fp']}|{r['lp']}": r["cap"]
            for r in pC["rows"] if r["status"] in GOOD}

    # ---------- phase 4/5: the COMPLETE bridge candidate enumeration
    groups = defaultdict(list)
    for c in piece_facts:
        b, d = c.split("|")[:2]
        groups[(int(b), int(d))].append(c)
    bridges = {}
    for (b, d), members in sorted(groups.items()):
        key = "|".join(map(str, (b, d, 0, 0, 0, 0)))
        bridges[key] = dict(
            chain_cell=key, bd=[b, d], piece_facts=sorted(members),
            piece_fact_count=len(members),
            in_the_round_152_table=key in cn,
            in_the_chain_basis=key in ess,
            historical_cap=ccap.get(key),
            historical_nodes=cn.get(key),
            piece_caps={m: pcap.get(m) for m in sorted(members)},
            noticed_by_round_166=key in set(
                json.loads((ROOT / "r166" / "certs"
                            / "cross_model_bridge_166.json").read_text())
                ["coverage"]["chain_cells_needed"]))
    covered = sum(v["piece_fact_count"] for v in bridges.values())

    # ---------- the certificate set needed for the FACT-level objective
    need_chain = set(chain_facts) | set(bridges)
    extra = sorted(set(bridges) - set(chain_facts))
    done = {"|".join(map(str, k)) for k in certified_by_proof()}
    direct_done = sorted(c for c in done if c in need_chain)
    bridge_done = sorted(c for c in piece_facts
                         if "|".join(map(str, (int(c.split("|")[0]),
                                               int(c.split("|")[1]),
                                               0, 0, 0, 0))) in done)

    # ---------- phase 8 inputs: cost.  Cells absent from the table have no
    # measured node count; their cost is estimated from the nearest measured
    # cell that DOMINATES them, which is an upper estimate, and flagged.
    measured = {k: v for k, v in cn.items() if v}

    def estimate(cell):
        if cell in measured:
            return measured[cell], "measured"
        t = tuple(int(x) for x in cell.split("|"))
        best = None
        for k, v in measured.items():
            kk = tuple(int(x) for x in k.split("|"))
            if all(a <= b for a, b in zip(t, kk)):
                if best is None or v < best:
                    best = v
        return best, "estimated from the cheapest measured dominating cell"

    cost = {}
    for c in sorted(need_chain):
        n, how = estimate(c)
        cost[c] = dict(nodes=n, basis=how, in_table=c in cn,
                       already_certified=c in done)
    total_needed = sum(v["nodes"] or 0 for v in cost.values()
                       if not v["already_certified"])

    # cost of the OLD plan: certify all 288 facts directly
    old_cost = 0
    for c in chain_facts:
        old_cost += cn.get(c, 0)
    for c in piece_facts:
        old_cost += pn.get(c, 0)

    out = dict(
        inputs={p: sha(p) for p in
                ("r165/certs/row_closure_graph_165.json",
                 "r166/certs/cross_model_bridge_166.json",
                 "r166/certs/verification_166.json",
                 "r152/certs/verify_all_c152.json",
                 "r152/certs/verify_piece_c152.json")},
        facts=dict(chain=len(chain_facts), piece=len(piece_facts),
                   total=len(ess),
                   matches_round_165=(len(chain_facts) == 179
                                      and len(piece_facts) == 109)),
        bridge_enumeration=dict(
            distinct_bd_groups=len(bridges),
            piece_facts_covered=covered,
            covers_every_piece_fact=covered == len(piece_facts),
            completeness_argument=(
                "a piece fact (b,d,fp,lp) is bridged by the chain cell "
                "(b,d,0,0,0,0) and by no other cell more tightly: any other "
                "chain cell K' that bounds it must dominate (b,d,0,0,0,0) "
                "componentwise, and monotonicity then gives "
                "cap_chain(b,d,0,0,0,0) <= cap_chain(K'), so the (b,d) cell "
                "is the strongest bridge.  Grouping the 109 piece facts by "
                "(b,d) therefore enumerates every useful bridge, and there "
                "are exactly as many as there are distinct (b,d)"),
            round_166_found=18,
            round_166_missed=len(bridges) - 18,
            why_round_166_missed_them=(
                "round 166 only accepted chain cells already present in the "
                "round-152 capacity table; the rest are absent from that "
                "table but are ordinary cells whose certificate can be "
                "generated directly"),
            bridges=bridges),
        fact_level_objective=dict(
            chain_facts_to_certify=len(chain_facts),
            bridge_chain_cells=len(bridges),
            already_in_the_chain_basis=len(set(bridges) & set(chain_facts)),
            extra_chain_cells=len(extra),
            extra_cells=extra,
            total_direct_certificates=len(need_chain),
            piece_certificates_avoided=len(piece_facts),
            reduction_from_288=len(ess) - len(need_chain)),
        current_progress=dict(
            DIRECT_SECOND_ROUTE=sorted(direct_done),
            DIRECT_SECOND_ROUTE_count=len(direct_done),
            BRIDGE_DERIVED_SECOND_ROUTE_count=len(bridge_done),
            OTHER_DERIVED_SECOND_ROUTE_count=0,
            supported_facts=len(direct_done) + len(bridge_done),
            note="a bridge-derived piece fact is NOT a directly certified "
                 "EXTREE cell and is counted separately"),
        cost=dict(
            old_plan_certify_all_288_facts=old_cost,
            new_plan_remaining_direct_certificates=total_needed,
            savings=old_cost - total_needed,
            per_cell=cost),
    )
    fl = out["fact_level_objective"]
    out["ok"] = (out["facts"]["matches_round_165"]
                 and out["bridge_enumeration"]["covers_every_piece_fact"])
    (ROOT / "r167" / "certs" / "bridge_rebasis_167.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("inputs", "cost")},
                     ensure_ascii=False, indent=1)[:2600])
    print("cost:", json.dumps({k: v for k, v in out["cost"].items()
                               if k != "per_cell"}))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
