#!/usr/bin/env python3
"""라운드 119 — `(3,1)` 의 hard three (A/B/C) 를 구조 분기로 나눠 정확히 탐색한다.

라운드 118 이 남긴 세 하위경우를 구조로 더 쪼갠다 (§2–§4):

    A (e=1,x=1,f_out=2,H=0)  ->  A4 (X-Y 간격 4, W3a 점프가 블록 안)
                                 A5 (간격 5, 블록은 tau 강제, 점프는 블록 밖)
    B (e=2,x=0,f_out=2,H=0)  ->  B_i  (Y 가 경우 (i): 간격 5)
                                 B_ii (Y 가 경우 (ii): orb(X)·orb(Y) 만 두 run)
    C (e=1,x=0,f_out=2,H=1)  ->  C1 (무게-4 변이 X 앞)
                                 C2 (무게-4 변이 Y 뒤)

무게-4 변은 강제 tau-블록 안에도, X/Y 의 탈출에도 올 수 없으므로 C1/C2 가 전부다.

여기서 도는 것은 **b=1 파일럿에서 완주가 확인된 네 분기**뿐이다.
`B_ii` 와 `C1` 은 파일럿에서 캡에 걸렸고 **UNKNOWN 으로 남긴다.**
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
BIN = ROOT / "src" / "f1_cell_119.bin"
SRC = ROOT / "src" / "f1_cell_119.c"
JSONL = OUT / "rr_f1_k3_hard_119.jsonl"
NODECAP = 60_000_000_000

# label, case, args: cost orb x fout e fmin ygap rmax hcap dcap bforce revonly hregion yfresh
BRANCHES = [
    ("C2_heavy_after_Y", "C", [26, 27, 0, 2, 1, 2, 5, 28, 1, 14, 0, 0, 2, 0]),
    ("A5_gap5_block_forced", "A", [26, 27, 1, 2, 1, 2, 5, 28, 0, 14, 1, 0, 0, 0]),
    ("A4_gap4_jump_in_block", "A", [26, 27, 1, 2, 1, 2, 4, 28, 0, 14, 0, 0, 0, 0]),
    ("Bi_Y_case_i", "B", [26, 27, 0, 2, 2, 2, 5, 29, 0, 14, 0, 0, 0, 0]),
]
OPEN = [
    {"label": "Bii_Y_case_ii", "case": "B",
     "args": [26, 27, 0, 2, 2, 2, 0, 29, 0, 14, 0, 1, 0, 1],
     "pilot": {"b": 1, "verdict": "UNKNOWN_CAP", "nodes_at_cap": 30_000_000_000,
               "seconds": 400, "best_passes": 106},
     "structure": ("orb(X) and orb(Y) each take exactly two runs and every other orbit one; "
                   "the order type is forced to R_X^end..X, R_Y^start.., .., R_Y^end..Y, "
                   "R_X^start.. and orb(Y) must be fresh when X's free exit enters it"),
     "why_open": "still exceeds 3e10 nodes at b=1 after the revisit and freshness restrictions"},
    {"label": "C1_heavy_before_X", "case": "C",
     "args": [26, 27, 0, 2, 1, 2, 5, 28, 1, 14, 0, 0, 1, 0],
     "pilot": {"b": 1, "verdict": "UNKNOWN_CAP", "nodes_at_cap": 20_000_000_000,
               "seconds": 678, "best_passes": 110},
     "structure": ("the single weight-4 edge lies strictly before X; it can never sit inside "
                   "the forced tau-block nor be X's or Y's exit (both forced free)"),
     "why_open": "exceeds 2e10 nodes at b=1 even with the heavy edge confined to the prefix"},
]


def build():
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(BIN), str(SRC)], check=True)


def done_keys():
    if not JSONL.exists():
        return set()
    return {(json.loads(l)["branch"], json.loads(l)["b"])
            for l in JSONL.read_text().splitlines() if l.strip()}


def summarise():
    rows = [json.loads(l) for l in JSONL.read_text().splitlines() if l.strip()]
    verdicts = {}
    for r in rows:
        verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
    by_branch = {}
    for lbl, case, _a in BRANCHES:
        rs = [r for r in rows if r["branch"] == lbl]
        by_branch[lbl] = dict(case=case, runs=len(rs),
                              closed=(len(rs) == 5 and all(r["verdict"] == "UNSAT_COMPLETE"
                                                           for r in rs)),
                              nodes=sum(r["nodes"] for r in rs),
                              seconds=round(sum(r["seconds"] for r in rs)))
    closed = [b for b, v in by_branch.items() if v["closed"]]
    case_status = {}
    for c, need in (("A", {"A4_gap4_jump_in_block", "A5_gap5_block_forced"}),
                    ("B", {"Bi_Y_case_i", "Bii_Y_case_ii"}),
                    ("C", {"C1_heavy_before_X", "C2_heavy_after_Y"})):
        got = {b for b in closed if b in need}
        case_status[c] = dict(branches=sorted(need), closed_branches=sorted(got),
                              case_closed=(got == need))
    rep = dict(round=119, cell=[3, 1], node_cap=NODECAP, runs=len(rows), verdicts=verdicts,
               by_branch=by_branch, branches_closed=closed, case_status=case_status,
               open_branches=OPEN,
               cell_closed=all(v["case_closed"] for v in case_status.values()),
               total_nodes=sum(r["nodes"] for r in rows),
               total_seconds=round(sum(r["seconds"] for r in rows)),
               max_passes_reached=max((r["best_passes"] for r in rows), default=0),
               label="ROUND-119 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
               rows=rows,
               ledger={"INDEPENDENTLY_AUDITED_Q2_RESIDUAL": 4782,
                       "CLAUDE_FULL_JOINT_UNSAT_COMPLETE": 6396,
                       "unchanged_by_this_round": True},
               disclaimer="This project has not proved L6 >= 872.")
    (OUT / "rr_f1_k3_hard_119.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def main():
    build()
    have = done_keys()
    fh = open(JSONL, "a", buffering=1, encoding="utf-8")
    for lbl, case, args in BRANCHES:
        for b in range(1, 6):
            if (lbl, b) in have:
                print(f"  skip {lbl} b={b}", flush=True)
                continue
            t0 = time.time()
            r = subprocess.run([str(BIN), str(b)] + [str(a) for a in args] + [str(NODECAP)],
                               capture_output=True, text=True, check=True)
            lines = [x for x in r.stdout.splitlines() if x.strip()]
            d = json.loads(lines[0])
            d.update(branch=lbl, case=case, seconds=round(time.time() - t0, 1),
                     splits=[b, 6 - b])
            if len(lines) > 1:
                d["witness"] = json.loads(lines[1])
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")
            print(f"  {lbl} b={b}: {d['verdict']} best={d['best_passes']} "
                  f"nodes={d['nodes']:,} {d['seconds']}s", flush=True)
            summarise()
            if d["verdict"] == "SAT":
                print("  *** SAT — stopping; see section 15 handling ***", flush=True)
                fh.close()
                return
    fh.close()
    rep = summarise()
    print(f"verdicts: {rep['verdicts']}  branches closed: {rep['branches_closed']}  "
          f"cases: {[(c, v['case_closed']) for c, v in rep['case_status'].items()]}")


if __name__ == "__main__":
    main()
