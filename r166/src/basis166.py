#!/usr/bin/env python3
"""Round 166 phases 0, 1, 3 -- recover the basis and put it in cost order.

The cost of certifying a basis cell is NOT its own search node count.  A
tree's (p) leaves may only cite cells proved earlier in the certificate order,
so generation walks that order and the marginal cost of reaching a basis cell
is the cumulative cost of every cell before it that has not been generated
yet.  Prerequisites are therefore shared, and the order below is the one
generation actually pays for.
"""
from __future__ import annotations
import hashlib, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r163" / "src"))
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r165" / "src"))
import hidden163 as H                                             # noqa: E402
import routeb164 as R                                             # noqa: E402
import closure165 as CL                                           # noqa: E402

CERTS = ROOT / "r152" / "certs"


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main():
    g = json.loads((ROOT / "r165" / "certs"
                    / "row_closure_graph_165.json").read_text())
    ess = set(g["essential_cells"])
    ch = sorted(c for c in ess if g["ablation"][c]["model"] == "chain")
    pi = sorted(c for c in ess if g["ablation"][c]["model"] == "piece")

    vg = json.loads((ROOT / "r164" / "certs"
                     / "verifygen_164.json").read_text())
    already = [c for c in vg["targets_upper_certified_by_two_validators"]
               if c in ess]

    # ---------- phase 0: this basis must reproduce the census
    H.load()
    CERT0, PCERT0 = dict(H.CERT), dict(H.PCERT)
    tg = json.loads((ROOT / "r164" / "certs" / "targets_164.json").read_text())
    done = {tuple(int(x) for x in s.split("|"))
            for s in vg["targets_upper_certified_by_two_validators"]}
    red_chain = [tuple(c) for c in tg["CHAIN_SINGLE_IMPL"]
                 if tuple(c) not in done and "|".join(map(str, c)) not in ess]
    red_piece = [tuple(c) for c in tg["PIECE_SINGLE_IMPL"]
                 if tuple(c) not in done and "|".join(map(str, c)) not in ess]
    groups = CL.grouped()
    CL.withdraw(red_chain, red_piece)
    res = CL.evaluate(groups)
    CL.restore(CERT0, PCERT0)
    per_layer = {}
    for (t, k), v in res.items():
        per_layer.setdefault(f"L{867 + t}", Counter())[v["verdict"]] += 1
    per_layer = {k: dict(v) for k, v in sorted(per_layer.items())}
    eq = [list(k[1]) for k, v in res.items() if v["verdict"] == "EQUALITY"]

    # ---------- phase 3: certificate order and cumulative cost
    cap, corder = R.parse_capcert(CERTS / "cap_cert_all_152.txt")
    pc, porder = R.parse_pcert(CERTS / "pcert_all_152.txt")
    vC = json.loads((CERTS / "verify_all_c152.json").read_text())
    pC = json.loads((CERTS / "verify_piece_c152.json").read_text())
    cn = {r["cell"]: r.get("nodes", 0) for r in vC["rows"]}
    pn = {f"{r['b']}|{r['d']}|{r['fp']}|{r['lp']}": r.get("nodes", 0)
          for r in pC["rows"]}

    def schedule(order, nodes, basis, label):
        rows, cum, ncells, hit = [], 0, 0, 0
        for i, cell in enumerate(order):
            key = "|".join(map(str, cell))
            cum += nodes.get(key, 0)
            ncells += 1
            if key in basis:
                hit += 1
                rows.append(dict(rank=hit, index=i, cell=key,
                                 cap=(cap if label == "chain" else pc)[cell]["cap"],
                                 own_nodes=nodes.get(key, 0),
                                 cumulative_nodes_to_here=cum,
                                 prefix_cells=ncells,
                                 est_bytes_at_2_29=int(cum * 2.29)))
        return rows

    csched = schedule(corder, cn, set(ch), "chain")
    psched = schedule(porder, pn, set(pi), "piece")

    out = dict(
        inputs={p: sha(p) for p in
                ("r165/certs/row_closure_graph_165.json",
                 "r165/certs/basis_summary_165.json",
                 "r164/certs/verifygen_164.json",
                 "r152/certs/cap_cert_all_152.txt",
                 "r152/certs/pcert_all_152.txt")},
        basis=dict(chain=len(ch), piece=len(pi), total=len(ess)),
        counts_match_round_165=(len(ch) == 179 and len(pi) == 109
                                and len(ess) == 288),
        BASIS_ALREADY_EXTREE_CERTIFIED=sorted(already),
        BASIS_REMAINING=len(ess) - len(already),
        note_on_the_round_164_cell=(
            "round 164's extree-certified cell 1|0|0|0|0|2 is NOT in the "
            "basis: round 165 removed it from the 355 before the ablation, so "
            "it never competed for essentiality, and it stays available, "
            "which is why the 288 remain sufficient"),
        census_under_the_basis=dict(
            per_layer=per_layer,
            L871_strict=per_layer.get("L871", {}).get("STRICTLY_CLOSED"),
            L871_equality=per_layer.get("L871", {}).get("EQUALITY"),
            equality_rows=eq,
            matches=(per_layer.get("L871", {}).get("STRICTLY_CLOSED") == 1154
                     and per_layer.get("L871", {}).get("EQUALITY") == 2
                     and len(eq) == 2)),
        chain_schedule=csched,
        piece_schedule=psched,
        cheapest_reachable=dict(
            chain_first=csched[0] if csched else None,
            piece_first=psched[0] if psched else None),
        checkpoints={},
    )
    for budget in (10 ** 7, 3 * 10 ** 7, 10 ** 8, 3 * 10 ** 8, 10 ** 9,
                   10 ** 10, 2 * 10 ** 11):
        c = sum(1 for r in csched if r["cumulative_nodes_to_here"] <= budget)
        p = sum(1 for r in psched if r["cumulative_nodes_to_here"] <= budget)
        out["checkpoints"][f"{budget:.0e}"] = dict(chain=c, piece=p,
                                                   total=c + p)
    out["ok"] = (out["counts_match_round_165"]
                 and out["census_under_the_basis"]["matches"])
    (ROOT / "r166" / "certs" / "basis_order_166.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("inputs", "chain_schedule",
                                   "piece_schedule")},
                     ensure_ascii=False, indent=1))
    print("first chain basis cells:")
    for r in csched[:6]:
        print("  ", r)
    print("first piece basis cells:")
    for r in psched[:4]:
        print("  ", r)
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
