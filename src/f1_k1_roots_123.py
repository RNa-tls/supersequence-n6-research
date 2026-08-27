#!/usr/bin/env python3
"""라운드 123 — 일반 `(1,1)` 뿌리 열거 드라이버.

`src/f1_k1_roots_123.c` 를 예외 예산(`e`, `x`, `H`)마다 돌려 **접두가 유계임**을 확인하고
뿌리 수를 센다.  완성 탐색이 아니다 — 첫 짧은 pass `X` 에서 멈춘다.

인자 순서: b qcap costcap orbcap xcap ecap hcap dcap exccap fod nodecap
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
BIN = ROOT / "src" / "f1_k1_roots_123.bin"
SRC = ROOT / "src" / "f1_k1_roots_123.c"
JSONL = OUT / "rr_f1_k1_roots_123.jsonl"
NODECAP = 15_000_000_000

# The 13 MAXIMAL exception cells (e, x, H) with e + x + H = 4, e <= 4, x <= 3, H <= 3.
# Every cell with e + x + H <= 4 is dominated componentwise by one of these, so their union
# is the COMPLETE generic (1,1) root family.  Running each cell with its own exact caps keeps
# the deficit prunes tight; running one combined job with all caps at once is far weaker and
# does not terminate (measured: > 3e10 nodes).
CELLS = [(4, 0, 0), (3, 1, 0), (3, 0, 1), (2, 2, 0), (2, 1, 1), (2, 0, 2), (1, 3, 0),
         (1, 2, 1), (1, 1, 2), (1, 0, 3), (0, 3, 1), (0, 2, 2), (0, 1, 3)]
CONFIGS = ([("rigid_e0_x0_H0", 0, 0, 0)]
           + [(f"e{e}_x{x}_H{h}", x, e, h) for (e, x, h) in CELLS])


def build():
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(BIN), str(SRC)], check=True)


def done():
    if not JSONL.exists():
        return set()
    return {json.loads(l)["label"] for l in JSONL.read_text().splitlines() if l.strip()}


def summarise():
    rows = [json.loads(l) for l in JSONL.read_text().splitlines() if l.strip()]
    by = {r["label"]: r for r in rows}
    complete = [r["label"] for r in rows if r["verdict"] == "COMPLETE"]
    capped = [r["label"] for r in rows if r["verdict"] == "UNKNOWN_CAP"]
    rigid = by.get("rigid_e0_x0_H0")
    rep = dict(
        round=123, cell=[1, 1], node_cap=NODECAP,
        model=("prefix enumeration that STOPS at the first short pass X; every pass before X "
               "is full (Round 123 Proposition 1), so the prefix is an F=0 prefix"),
        first_word_fixed=("S6 left multiplication is simply transitive on the 720 words and "
                          "commutes with sigma, tau and all 550 tails, so fixing the first "
                          "entry word is a complete 720x reduction"),
        heavy_tails_included={"weight4": 13, "weight5": 71, "weight6": 461, "total": 545},
        runs=len(rows), configs_complete=complete, configs_capped=capped,
        by_config=by,
        prefix_bound=dict(
            rigid_max_q=(rigid or {}).get("max_prefix_q"),
            NTAB_4=46,
            matches_R115_chain_capacity=((rigid or {}).get("max_prefix_q") == 46),
            note=("with e = x = H = 0 the prefix is a single R115-model all-light chain whose "
                  "run-shortfall budget is D = 4, so NTAB[4] = 46 is an analytic upper bound; "
                  "the exhaustive enumeration returns exactly 46")),
        cells=[list(c) for c in CELLS],
        root_family_complete=(len(capped) == 0
                              and all(f"e{e}_x{x}_H{h}" in complete
                                      for (e, x, h) in CELLS)),
        total_roots_over_cells=sum(r["roots"] for r in rows
                                   if r["verdict"] == "COMPLETE"
                                   and r["label"] != "rigid_e0_x0_H0"),
        max_q_over_cells=max((r["max_prefix_q"] for r in rows), default=0),
        label="ROUND-123 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
        ledger={"INDEPENDENTLY_AUDITED_Q2_RESIDUAL": 4782,
                "CLAUDE_FULL_JOINT_UNSAT_COMPLETE": 6396,
                "unchanged_by_this_round": True},
        disclaimer="This project has not proved L6 >= 872.")
    (OUT / "rr_f1_k1_roots_123.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def main():
    build()
    have = done()
    fh = open(JSONL, "a", buffering=1, encoding="utf-8")
    for label, xcap, ecap, hcap in CONFIGS:
        if label in have:
            print(f"  skip {label}", flush=True)
            continue
        t0 = time.time()
        r = subprocess.run([str(BIN), "0", "119", "26", "25", str(xcap), str(ecap),
                            str(hcap), "4", "5", "1", str(NODECAP)],
                           capture_output=True, text=True, check=True)
        lines = [x for x in r.stdout.splitlines() if x.strip()]
        d = json.loads(lines[0])
        d.update(label=label, seconds=round(time.time() - t0, 1))
        if len(lines) > 1:
            hist = json.loads(lines[1])
            d["prefix_states_by_q"] = hist["prefix_states_by_q"]
        fh.write(json.dumps(d, ensure_ascii=False) + "\n")
        print(f"  {label:18s}: {d['verdict']:12s} prefix_nodes={d['nodes']:>13,} "
              f"roots={d['roots']:>15,} max_q={d['max_prefix_q']:>3} {d['seconds']}s",
              flush=True)
        summarise()
    fh.close()
    rep = summarise()
    print(f"complete: {len(rep['configs_complete'])}  capped: {len(rep['configs_capped'])}  "
          f"rigid max_q={rep['prefix_bound']['rigid_max_q']}")


if __name__ == "__main__":
    main()
