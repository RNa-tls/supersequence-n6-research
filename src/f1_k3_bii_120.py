#!/usr/bin/env python3
"""라운드 120 — `(3,1)` 의 마지막 두 분기 `B_ii` · `C1`.

`C1` 은 **탐색 없이 닫힌다**: 뒤집기 대칭 Phi 가 `C1` 을 이미 닫힌
`C2`(라운드 119) 와 `G6`(라운드 118) 위로 보낸다 (§7~§10, `CASE_MAP` 참조).

`B_ii` 는 Phi 가 자기 자신 위로 보내므로 닫히지 않는다.  대신 Phi 에서
**정규형 세 개**가 나오고, 그것으로 라운드 119 가 캡에 걸렸던 탐색이 완주한다:

    seam=1    t' >= 2 이고 t >= 2 (X·Y 로 들어오는 이음매가 둘 다 tau).
              t'=1 또는 t=1 인 walk 은 Phi 상이 G2 / G1 행이라 이미 닫혔다.
    pmax=59   Phi 는 "X 앞 pass 수" 와 "Y 뒤 pass 수" 를 맞바꾼다.  따라서
              p-1 <= 121-q 를 가정해도 좋고, B_ii 에서 q-p >= 4 이므로 p <= 59.
    symcut=1  Y 를 놓을 때 p-1 <= 121-q 를 정확히 확인한다.
    exccap=15 궤도-덮개 잉여 한계 (정확하지만 효과는 작다 — 문서 §6 참조).
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
BIN = ROOT / "src" / "f1_cell_120.bin"
SRC = ROOT / "src" / "f1_cell_120.c"
JSONL = OUT / "rr_f1_k3_bii_120.jsonl"
NODECAP = 60_000_000_000

# cost orb x fout e fmin ygap rmax hcap dcap bforce revonly hregion yfresh exccap seam pmax symcut
BII_ARGS = [26, 27, 0, 2, 2, 2, 0, 29, 0, 14, 0, 1, 0, 1, 15, 1, 59, 1]

# every sub-case of the two Round-119 open branches, and where reversal sends it.
CASE_MAP = [
    {"branch": "C1", "subcase": "t' >= 2 (the joint into X is tau)",
     "image_row": {"e": 1, "x": 0, "f_out": 2, "H": 1, "r": 28,
                   "heavy_region": "strictly after the second short pass"},
     "closed_by": "Round 119 C2 (hregion=2), 5/5 UNSAT_COMPLETE", "needs_search": False},
    {"branch": "C1", "subcase": "t' = 1 and the heavy joint IS the joint into X",
     "image_row": {"e": 0, "x": 0, "f_out": 1, "H": 1, "r": 27},
     "closed_by": "Round 118 G6_H1_e0, 5/5 UNSAT_COMPLETE", "needs_search": False},
    {"branch": "C1", "subcase": "t' = 1 and the heavy joint is strictly earlier",
     "image_row": {"e": 0, "x": 0, "f_out": 1, "H": 1, "r": 27},
     "closed_by": "Round 118 G6_H1_e0, 5/5 UNSAT_COMPLETE", "needs_search": False},
    {"branch": "B_ii", "subcase": "t' = 1, t >= 2",
     "image_row": {"e": 1, "x": 0, "f_out": 1, "H": 0, "r": 28},
     "closed_by": "Round 118 G2_e1_x0_f1_H0, 5/5 UNSAT_COMPLETE", "needs_search": False},
    {"branch": "B_ii", "subcase": "t >= 2 reversed: t = 1, t' >= 2",
     "image_row": {"e": 1, "x": 0, "f_out": 1, "H": 0, "r": 28},
     "closed_by": "Round 118 G2_e1_x0_f1_H0, 5/5 UNSAT_COMPLETE", "needs_search": False},
    {"branch": "B_ii", "subcase": "t' = 1 and t = 1",
     "image_row": {"e": 0, "x": 0, "f_out": 0, "H": 0, "r": 27},
     "closed_by": "Round 118 G1_e0_H0 (row (0,0,0)), 5/5 UNSAT_COMPLETE",
     "needs_search": False},
    {"branch": "B_ii", "subcase": "t' >= 2 and t >= 2 (Phi maps B_ii onto B_ii, b -> 6-b)",
     "image_row": {"e": 2, "x": 0, "f_out": 2, "H": 0, "r": 29},
     "closed_by": "this round: seam + pmax + symcut search, 5 splits", "needs_search": True},
]


def build():
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(BIN), str(SRC)], check=True)


def done_bs():
    if not JSONL.exists():
        return set()
    return {json.loads(l)["b"] for l in JSONL.read_text().splitlines() if l.strip()}


def summarise():
    rows = [json.loads(l) for l in JSONL.read_text().splitlines() if l.strip()]
    rows.sort(key=lambda r: r["b"])
    verdicts = {}
    for r in rows:
        verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
    bii_closed = (len(rows) == 5 and all(r["verdict"] == "UNSAT_COMPLETE" for r in rows))
    rep = dict(
        round=120, cell=[3, 1], node_cap=NODECAP,
        branch="B_ii", args=BII_ARGS, runs=len(rows), verdicts=verdicts,
        b_ii_closed=bii_closed,
        c1_closed_by_reversal=True,
        cell_closed=bii_closed,
        case_map=CASE_MAP,
        total_nodes=sum(r["nodes"] for r in rows),
        total_seconds=round(sum(r["seconds"] for r in rows)),
        max_passes_reached=max((r["best_passes"] for r in rows), default=0),
        round_119_baseline={"b": 1, "verdict": "UNKNOWN_CAP", "nodes_at_cap": 30_000_000_000,
                            "best_passes": 106},
        label="ROUND-120 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
        rows=rows,
        ledger={"INDEPENDENTLY_AUDITED_Q2_RESIDUAL": 4782,
                "CLAUDE_FULL_JOINT_UNSAT_COMPLETE": 6396,
                "unchanged_by_this_round": True},
        disclaimer="This project has not proved L6 >= 872.")
    (OUT / "rr_f1_k3_bii_120.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def main():
    build()
    have = done_bs()
    fh = open(JSONL, "a", buffering=1, encoding="utf-8")
    for b in range(1, 6):
        if b in have:
            print(f"  skip b={b}", flush=True)
            continue
        t0 = time.time()
        r = subprocess.run([str(BIN), str(b)] + [str(a) for a in BII_ARGS] + [str(NODECAP)],
                           capture_output=True, text=True, check=True)
        lines = [x for x in r.stdout.splitlines() if x.strip()]
        d = json.loads(lines[0])
        d.update(branch="B_ii", seconds=round(time.time() - t0, 1), splits=[b, 6 - b])
        if len(lines) > 1:
            d["witness"] = json.loads(lines[1])
        fh.write(json.dumps(d, ensure_ascii=False) + "\n")
        print(f"  B_ii b={b}: {d['verdict']} best={d['best_passes']} "
              f"nodes={d['nodes']:,} {d['seconds']}s", flush=True)
        summarise()
        if d["verdict"] == "SAT":
            print("  *** SAT - stopping; section 17 replay handling ***", flush=True)
            fh.close()
            return
    fh.close()
    rep = summarise()
    print(f"verdicts: {rep['verdicts']}  B_ii closed: {rep['b_ii_closed']}  "
          f"cell closed: {rep['cell_closed']}")


if __name__ == "__main__":
    main()
