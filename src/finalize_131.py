#!/usr/bin/env python3
"""라운드 131 마무리 — 보고서 JSON 을 만들고 master 원장에 키를 하나 더한다."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "outputs"
import g2_k4_closure_131 as D                                   # noqa: E402

T121 = ROOT / "src" / "g2_cell_131_t121.bin"
BIN = ROOT / "src" / "g2_cell_131.bin"


def round125_controls():
    cases = [("Round 125 e=0 f=0 rmax=26",
              ["2", "25", "25", "0", "0", "0", "0", "4", "5", "1", "1", "1", "26", "26"], 20584),
             ("Round 125 e=1 f=0 rmax=26",
              ["2", "25", "25", "0", "0", "0", "1", "4", "5", "1", "1", "1", "26", "26"], 462058),
             ("Round 125 e=1 f=1 rmax=26",
              ["2", "25", "24", "0", "1", "1", "1", "4", "5", "1", "1", "1", "26", "26"], 487122)]
    out = []
    for name, args, want in cases:
        p = subprocess.run([str(T121)] + args + ["0", "0", "0", "0", "200000000000",
                                                 "1", "0", "0", "0"],
                           capture_output=True, text=True, check=True)
        got = json.loads(p.stdout.strip().splitlines()[0])
        out.append(dict(name=name, recorded=want, replayed=got["nodes"],
                        matches=(got["nodes"] == want), verdict=got["verdict"]))
    return out


def regression_controls():
    """§19 — `A/e=0` 과 `B/e=0` 각각 한 분할씩, 라운드 130 노드와 일치해야 한다."""
    cases = [("A_e0_l114", ["0", "28", "25", "0", "2", "2", "0", "18", "20", "1", "1", "1",
                            "25", "28", "0", "0", "0", "0", "30000000000", "1", "3", "1",
                            "3", "0", "2"], 680651642),
             ("B_e0_b11", ["1", "28", "25", "0", "2", "2", "0", "18", "20", "1", "1", "1",
                           "25", "28", "0", "0", "0", "0", "30000000000", "1", "5", "1",
                           "5", "0", "2"], 1738262553)]
    out = []
    for name, args, want in cases:
        p = subprocess.run([str(BIN)] + args, capture_output=True, text=True, check=True)
        got = json.loads(p.stdout.strip().splitlines()[0])
        out.append(dict(name="Round 130 regression " + name, recorded=want,
                        replayed=got["nodes"], matches=(got["nodes"] == want),
                        verdict=got["verdict"]))
    return out


def main(with_controls=True):
    theory = json.loads((OUT / "rr_g2_ae1_131.json").read_text())
    pos = json.loads((OUT / "rr_g2_machine_131.json").read_text())
    controls = (round125_controls() + regression_controls()) if with_controls else None
    rep = D.summarise(controls=controls, positive=pos,
                      theory=dict(module="src/verify_g2_ae1_131.py",
                                  theorem=theory["theorem"],
                                  lock_corollaries=theory["lock_corollaries"],
                                  ae1=theory["ae1"], b_order=theory["b_order"],
                                  n4_check=theory["n4_check"],
                                  n4_order=theory["n4_order"]))
    rep["pilots"] = dict(
        A_e1_l114=dict(round130_nodes=17038540046, round130_seconds=1926.8,
                       round131_nodes=12981632834, round131_seconds=1460,
                       reduction_factor=round(17038540046 / 12981632834, 3),
                       verdict="UNSAT_COMPLETE"),
        B_capped_pilots=[
            dict(label="B_e2_b11 alpha", nodes=6000000178, seconds=667,
                 verdict="UNKNOWN_CAP"),
            dict(label="B_e2_b11 beta", nodes=6000000138, seconds=829,
                 verdict="UNKNOWN_CAP"),
            dict(label="B_e1_b11 closer0", nodes=6000000115, seconds=624,
                 verdict="UNKNOWN_CAP")],
        node_rate_per_second=9_000_000)
    cs = rep["cell_status"]
    closed = [k for k, v in cs.items() if v["closed"]]
    rep["headline"] = (
        "Theorem 131.1 pins the free-exit / repeat-run / lock pattern of all five (4,2) "
        "subcases; A/e=1 is now %s (%d/%d splits, %s nodes) while B/e=1 and B/e=2 are "
        "structurally reduced (100 -> 75 and 25 -> 50 branches, opener locks now proved) "
        "but computationally open - their 6e9-node pilots all returned UNKNOWN_CAP, never "
        "UNSAT.  Closed subcases: %s.  The cell is %sclosed."
        % ("CLOSED" if cs["A_e1"]["closed"] else "NOT closed",
           cs["A_e1"].get("unsat", 0), cs["A_e1"]["planned"],
           f'{cs["A_e1"]["nodes"]:,}', ", ".join(sorted(closed)),
           "" if rep["cell_closed"] else "NOT "))
    (OUT / "rr_g2_k4_131.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1))

    m = OUT / "superpermutation_n6_master_status.json"
    d = json.loads(m.read_text())
    d["round_131_G2_k4_remaining_subcases"] = dict(
        round=131, cell="(k,G) = (4,2)", outer_axis="G (never F)",
        cell_closed=rep["cell_closed"],
        claude_closed_outer_cells=("9/55 (k,G) - NOT incremented"
                                   if not rep["cell_closed"]
                                   else "10/55 (k,G)"),
        headline=rep.get("headline", ""),
        theorem_131_1=theory["theorem"],
        lock_corollaries=theory["lock_corollaries"],
        ae1_forcing=theory["ae1"], b_order_theorem=theory["b_order"],
        n4_census=theory["n4_check"], n4_order_census=theory["n4_order"],
        positive_control=pos["n4"], controls=controls,
        branch_counts=rep["branch_counts"], cell_status=rep["cell_status"],
        subcases_remaining=rep["subcases_remaining"],
        pilots=rep["pilots"], verdicts=rep["verdicts"],
        total_nodes_round131=rep["total_nodes_round131"],
        label="ROUND-131 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
        ledger=rep["ledger"], disclaimer=rep["disclaimer"])
    m.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print(json.dumps(dict(keys=len(d), cell_closed=rep["cell_closed"],
                          remaining=rep["subcases_remaining"],
                          verdicts=rep["verdicts"],
                          nodes=rep["total_nodes_round131"],
                          seconds=rep["total_seconds_round131"],
                          controls_all_match=all(c["matches"] for c in (controls or []))),
                     indent=1))


if __name__ == "__main__":
    main("--fast" not in sys.argv)
