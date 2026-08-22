#!/usr/bin/env python3
"""라운드 117 — `(k,F) = (4,1)` 칸의 정확한 all-light 탐색 구동기.

라운드 117 §1 의 예산 유도(보조정리 E 포함)에서 이 칸은 **정확히 두 하위경우**다.

    A :  e = 0, x = 0, f_out = 1, r = 28
    B1:  e = 1, x = 0, f_out = 2, r = 29

둘 다 `S = 26`, `H = 0`, `t = 1`, `O = 28` 이다.  분할 `b = 1..5` 마다 한 번씩,
합쳐서 10회를 **순차로** 돌린다 (동시 실행 없음).

결과는 한 줄씩 즉시 기록한다 — 컨테이너가 재시작해도 최대 한 건만 잃는다.
캡 도달은 UNSAT 이 아니라 UNKNOWN_CAP 이다.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
BIN = ROOT / "src" / "f1_all_light_117.bin"
SRC = ROOT / "src" / "f1_all_light_117.c"
JSONL = OUT / "rr_f1_k4_117.jsonl"
NODECAP = 200_000_000_000

SUBCASES = [("A_e0_x0_fout1", 0, 1, 0),
            ("B1_e1_x0_fout2", 0, 2, 1)]
COSTCAP, ORBCAP = 26, 28


def build():
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(BIN), str(SRC)], check=True)


def done_keys():
    if not JSONL.exists():
        return set()
    return {(json.loads(l)["subcase"], json.loads(l)["b"])
            for l in JSONL.read_text().splitlines() if l.strip()}


def summarise():
    rows = [json.loads(l) for l in JSONL.read_text().splitlines() if l.strip()]
    verdicts = {}
    for r in rows:
        verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
    rep = dict(round=117, cell=[4, 1], costcap=COSTCAP, orbcap=ORBCAP,
               node_cap=NODECAP, runs=len(rows), verdicts=verdicts,
               all_unsat_complete=all(r["verdict"] == "UNSAT_COMPLETE" for r in rows),
               total_nodes=sum(r["nodes"] for r in rows),
               total_seconds=round(sum(r["seconds"] for r in rows)),
               max_passes_reached=max(r["best_passes"] for r in rows),
               rows=rows)
    (OUT / "rr_f1_k4_117.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def main():
    build()
    have = done_keys()
    fh = open(JSONL, "a", buffering=1, encoding="utf-8")
    for label, xcap, foutcap, ecap in SUBCASES:
        for b in range(1, 6):
            if (label, b) in have:
                print(f"  skip {label} b={b} (already recorded)", flush=True)
                continue
            t0 = time.time()
            r = subprocess.run([str(BIN), str(b), str(COSTCAP), str(ORBCAP),
                                str(xcap), str(foutcap), str(ecap), str(NODECAP)],
                               capture_output=True, text=True, check=True)
            lines = [x for x in r.stdout.splitlines() if x.strip()]
            d = json.loads(lines[0])
            d.update(subcase=label, seconds=round(time.time() - t0, 1),
                     splits=[b, 6 - b])
            if len(lines) > 1:
                d["witness"] = json.loads(lines[1])
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")
            print(f"  {label} b={b}: {d['verdict']} best_passes={d['best_passes']} "
                  f"nodes={d['nodes']:,} {d['seconds']}s", flush=True)
            summarise()
            if d["verdict"] == "SAT":
                print("  *** SAT — stopping; see section 11 handling ***", flush=True)
                fh.close()
                return
    fh.close()
    rep = summarise()
    print(f"verdicts: {rep['verdicts']}  total nodes {rep['total_nodes']:,}  "
          f"max passes {rep['max_passes_reached']}")


if __name__ == "__main__":
    main()
