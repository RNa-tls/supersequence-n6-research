#!/usr/bin/env python3
"""라운드 118 — `(k,F) = (3,1)` 칸의 정확한 탐색 구동기.

§1 예산 유도가 준 (3,1) 의 자원 경우는 7개이고 `H <= 1` 이다.
`H = 0` 이면 `t = 1` (all-light 121-pass 사슬), `H = 1` 이면 무게-4 joint 정확히 하나다.

여기서 도는 것은 **파일럿에서 완주가 확인된 4개 그룹 × 5 분할 = 20회**뿐이다.
남은 세 하위경우는 파일럿에서 3e10 노드를 넘겨 **UNKNOWN 으로 남긴다** — 추측성
다중 시간 스윕은 돌리지 않는다 (브리프 §13).

결과는 한 줄씩 즉시 기록한다 (컨테이너 롤백 대비).  캡 도달은 UNSAT 이 아니다.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
BIN = ROOT / "src" / "f1_cell_118.bin"
SRC = ROOT / "src" / "f1_cell_118.c"
JSONL = OUT / "rr_f1_k3_118.jsonl"
NODECAP = 50_000_000_000

# label, rows covered, then: costcap orbcap xcap foutcap ecap foutmin ygap rmax hcap dcap bforce revonly
GROUPS = [
    ("G1_e0_H0", ["(0,0,0)", "(0,0,1)H0", "(0,1,1)"], [26, 27, 1, 1, 0, 0, 0, 27, 0, -1, 0, 0]),
    ("G3_e1_x0_f2_H0", ["(1,0,2)H0"],                 [26, 27, 0, 2, 1, 2, 5, 28, 0, 14, 0, 0]),
    ("G6_H1_e0", ["(0,0,1)H1"],                       [26, 27, 0, 1, 0, 1, 0, 27, 1, -1, 0, 0]),
    ("G2_e1_x0_f1_H0", ["(1,0,1)"],                   [26, 27, 0, 1, 1, 0, 0, 28, 0, 14, 0, 0]),
]
OPEN_SUBCASES = [
    {"label": "G4_e1_x1_f2_H0", "rows": ["(1,1,2)H0"],
     "reason": "one W3a jump; exceeded 3e10 nodes at b=1 with both the jump-inside (gap<=4) "
               "and jump-outside (gap=5, block forced) splits"},
    {"label": "G5_e2_x0_f2_H0", "rows": ["(2,0,2)H0"],
     "reason": "e = 2 lets BOTH h* orbits take a second run, so the forced 5-pass separation "
               "breaks; exceeded 3e10 nodes at b=1 with both the Y-case-(i) and Y-case-(ii) "
               "(revisit-restricted) splits"},
    {"label": "G7_H1_e1_x0_f2", "rows": ["(1,0,2)H1"],
     "reason": "hub tax 1 on top of e = 1; exceeded 2e10 nodes at b=1"},
]


def build():
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(BIN), str(SRC)], check=True)


def done_keys():
    if not JSONL.exists():
        return set()
    return {(json.loads(l)["group"], json.loads(l)["b"])
            for l in JSONL.read_text().splitlines() if l.strip()}


def summarise():
    rows = [json.loads(l) for l in JSONL.read_text().splitlines() if l.strip()]
    verdicts = {}
    for r in rows:
        verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
    by_group = {}
    for g, _rows, _args in GROUPS:
        rs = [r for r in rows if r["group"] == g]
        by_group[g] = dict(runs=len(rs),
                           closed=(len(rs) == 5 and all(r["verdict"] == "UNSAT_COMPLETE"
                                                        for r in rs)),
                           verdicts=sorted({r["verdict"] for r in rs}),
                           nodes=sum(r["nodes"] for r in rs),
                           seconds=round(sum(r["seconds"] for r in rs)))
    rep = dict(round=118, cell=[3, 1], node_cap=NODECAP, runs=len(rows),
               verdicts=verdicts, by_group=by_group,
               groups_closed=[g for g, v in by_group.items() if v["closed"]],
               open_subcases=OPEN_SUBCASES,
               total_nodes=sum(r["nodes"] for r in rows),
               total_seconds=round(sum(r["seconds"] for r in rows)),
               max_passes_reached=max((r["best_passes"] for r in rows), default=0),
               cell_closed=False,
               label="ROUND-118 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
               rows=rows,
               ledger={"INDEPENDENTLY_AUDITED_Q2_RESIDUAL": 4782,
                       "CLAUDE_FULL_JOINT_UNSAT_COMPLETE": 6396,
                       "unchanged_by_this_round": True},
               disclaimer="This project has not proved L6 >= 872.")
    rep["cell_closed"] = (len(rep["groups_closed"]) == len(GROUPS)
                          and not OPEN_SUBCASES)
    (OUT / "rr_f1_k3_118.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def main():
    build()
    have = done_keys()
    fh = open(JSONL, "a", buffering=1, encoding="utf-8")
    for label, covers, args in GROUPS:
        for b in range(1, 6):
            if (label, b) in have:
                print(f"  skip {label} b={b}", flush=True)
                continue
            t0 = time.time()
            r = subprocess.run([str(BIN), str(b)] + [str(a) for a in args] + [str(NODECAP)],
                               capture_output=True, text=True, check=True)
            lines = [x for x in r.stdout.splitlines() if x.strip()]
            d = json.loads(lines[0])
            d.update(group=label, covers=covers, seconds=round(time.time() - t0, 1),
                     splits=[b, 6 - b])
            if len(lines) > 1:
                d["witness"] = json.loads(lines[1])
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")
            print(f"  {label} b={b}: {d['verdict']} best={d['best_passes']} "
                  f"nodes={d['nodes']:,} {d['seconds']}s", flush=True)
            summarise()
            if d["verdict"] == "SAT":
                print("  *** SAT — stopping; see section 15 handling ***", flush=True)
                fh.close()
                return
    fh.close()
    rep = summarise()
    print(f"verdicts: {rep['verdicts']}  groups closed: {rep['groups_closed']}  "
          f"total nodes {rep['total_nodes']:,}")


if __name__ == "__main__":
    main()
