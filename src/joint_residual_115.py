#!/usr/bin/env python3
"""라운드 115 — 사슬별 용량으로 닫히지 않은 F=0 하위경우를 **결합 탐색**으로 마무리한다.

사슬별 상한은 사슬들이 서로 육각형-서로소이고 합쳐서 120개 육각형을 정확히 덮어야
한다는 전역 제약을 쓰지 않는다.  `src/joint_walk_115.c` 는 그 제약을 그대로 넣고
walk 뼈대 전체를 찾는다.

`found = false` 이고 `capped = false` 여야만 그 하위경우가 닫힌다.
캡 도달은 UNSAT 이 아니라 UNKNOWN 이다.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
BIN = ROOT / "src" / "joint_walk_115.bin"
SRC = ROOT / "src" / "joint_walk_115.c"
CAP = 60_000_000_000

# (label, k, e, x, t) -> RTOT = 24+k+e, OTOT = 24+k, TCH = t
RESIDUAL = [("k2_e0_x0_t3", 2, 0, 0, 3),
            ("k2_e1_x0_t2", 2, 1, 0, 2),
            ("k3_e0_x0_t2", 3, 0, 0, 2)]

# 양성 대조: greedy 873 의 형태 (r=24, O=24, t=6) 와 그 완화들 — 반드시 FOUND
POSITIVE = [(24, 24, 6), (24, 24, 7), (24, 24, 8), (25, 24, 6), (25, 25, 6), (26, 26, 6)]

# 격자 열거가 이미 닫은 하위경우 — 결합 탐색도 같은 답을 내야 한다
NEGATIVE = [(24, 24, 5), (28, 28, 1), (25, 25, 4)]


def run(r, o, t, cap=CAP):
    t0 = time.time()
    d = json.loads(subprocess.run([str(BIN), str(r), str(o), str(t), str(cap)],
                                  capture_output=True, text=True, check=True).stdout)
    d["seconds"] = round(time.time() - t0, 1)
    return d


def main():
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(BIN), str(SRC)], check=True)
    rep = {"round": 115, "node_cap": CAP, "residual": {}, "positive_control": [],
           "negative_control": []}
    for label, k, e, x, t in RESIDUAL:
        d = run(24 + k + e, 24 + k, t)
        d.update(label=label, k=k, e=e, x=x, t=t,
                 closed=(not d["found"]) and (not d["capped"]))
        rep["residual"][label] = d
        print(f"  residual {label}: found={d['found']} capped={d['capped']} "
              f"nodes={d['nodes']:,} {d['seconds']}s", flush=True)
    for r, o, t in POSITIVE:
        d = run(r, o, t)
        d["accepts_real_shape"] = d["found"]
        rep["positive_control"].append(d)
        print(f"  positive (r={r},O={o},t={t}): found={d['found']} "
              f"nodes={d['nodes']:,}", flush=True)
    for r, o, t in NEGATIVE:
        d = run(r, o, t)
        rep["negative_control"].append(d)
        print(f"  negative (r={r},O={o},t={t}): found={d['found']} "
              f"capped={d['capped']} nodes={d['nodes']:,} {d['seconds']}s", flush=True)
    rep["all_residual_closed"] = all(v["closed"] for v in rep["residual"].values())
    rep["false_rejection"] = sum(1 for d in rep["positive_control"] if not d["found"])
    rep["negative_disagreements"] = sum(1 for d in rep["negative_control"]
                                        if d["found"] or d["capped"])
    (OUT / "rr_joint_residual_115.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"all residual closed: {rep['all_residual_closed']}  "
          f"false rejection: {rep['false_rejection']}  "
          f"negative disagreements: {rep['negative_disagreements']}")


if __name__ == "__main__":
    main()
