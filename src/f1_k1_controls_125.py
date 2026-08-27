#!/usr/bin/env python3
"""라운드 125 §17 — 재생 대조.

새 긴 실행 전에 **이전 라운드의 정확한 노드 수를 새 엔진으로 다시 낸다.**
라운드 125 엔진은 라운드 121 엔진에 무게-6 (HW 비트 4) 만 더한 것이므로, `hw` 에
비트 4 가 없으면 노드 수가 **한 자리도 다르지 않아야** 한다.

라운드 117/118/119/120 의 기록은 인자 개수가 더 적었으므로, 각 기록의 인자를 그대로
읽어 라운드 121/125 인자 순서로 채운다 (없는 인자는 그 라운드의 기본값 = 0/-1/기본).
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
BIN = ROOT / "src" / "f1_cell_125.bin"
SRC = ROOT / "src" / "f1_cell_125.c"

# 인자 순서 (argv[1..26])
ARGS = ["b", "costcap", "orbcap", "xcap", "foutcap", "ecap", "foutmin", "ygap", "rmax",
        "hcap", "dcap", "bforce", "revonly", "hregion", "yfresh", "exccap", "seam",
        "pmax", "symcut", "shcap", "hw", "hjcap", "hubmin", "fod", "ygapmin"]
# 기록에 없는 인자의 기본값 = 그 라운드 엔진이 실제로 쓴 값
DEFAULT = dict(foutmin=0, ygap=0, hcap=0, dcap=-1, bforce=0, revonly=0, hregion=0,
               yfresh=0, seam=0, pmax=0, symcut=0, shcap=-1, hw=1, hjcap=999,
               hubmin=0, fod=0, ygapmin=0)

SOURCES = [
    ("round117", OUT / "rr_f1_k4_117.jsonl", "subcase"),
    ("round118", OUT / "rr_f1_k3_118.jsonl", "group"),
    ("round119", OUT / "rr_f1_k3_hard_119.jsonl", "case"),
    ("round120", OUT / "rr_f1_k3_bii_120.jsonl", "branch"),
    ("round121", OUT / "rr_f1_k2_121.jsonl", "label"),
]


def build():
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(BIN), str(SRC)], check=True)


def argv_of(rec):
    exccap = rec.get("exccap")
    if exccap is None:                       # 라운드 120 이전에는 EXC 프룬이 없었다
        exccap = -1
    vals = []
    for a in ARGS:
        if a == "exccap":
            vals.append(exccap)
        else:
            vals.append(rec.get(a, DEFAULT.get(a, 0)))
    return [str(v) for v in vals]


def pick(path, keyfield, budget_seconds):
    """그 라운드에서 가장 싼 완주 실행을 고른다 (대조는 빨라야 한다)."""
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    ok = [r for r in rows if r.get("verdict") == "UNSAT_COMPLETE"
          and r.get("seconds", 1e9) <= budget_seconds]
    if not ok:
        ok = sorted(rows, key=lambda r: r.get("seconds", 1e9))[:1]
    ok.sort(key=lambda r: r.get("seconds", 1e9))
    return ok[0], keyfield


def run(rec, nodecap=200_000_000_000):
    args = [str(BIN)] + argv_of(rec) + [str(nodecap)]
    t0 = time.time()
    p = subprocess.run(args, capture_output=True, text=True, check=True)
    out = json.loads(p.stdout.strip().splitlines()[0])
    out["seconds"] = round(time.time() - t0, 1)
    return out


def controls(budget_seconds=90):
    build()
    res = []
    for (name, path, keyfield) in SOURCES:
        if not path.exists():
            res.append(dict(round=name, status="SOURCE_MISSING"))
            continue
        rec, kf = pick(path, keyfield, budget_seconds)
        got = run(rec)
        res.append(dict(
            round=name, case=rec.get(kf), args=argv_of(rec),
            recorded_nodes=rec["nodes"], replayed_nodes=got["nodes"],
            recorded_verdict=rec["verdict"], replayed_verdict=got["verdict"],
            recorded_best_passes=rec.get("best_passes"),
            replayed_best_passes=got["best_passes"],
            seconds=got["seconds"],
            matches=(rec["nodes"] == got["nodes"]
                     and rec["verdict"] == got["verdict"]
                     and rec.get("best_passes") == got["best_passes"])))
    return res


if __name__ == "__main__":
    r = controls()
    for c in r:
        print("%-9s %-22s recorded=%-16s replayed=%-16s %s (%ss)"
              % (c["round"], str(c.get("case"))[:22],
                 f'{c.get("recorded_nodes", 0):,}', f'{c.get("replayed_nodes", 0):,}',
                 "MATCH" if c.get("matches") else "MISMATCH", c.get("seconds")))
