#!/usr/bin/env python3
"""라운드 131 — `(k, G) = (4, 2)` 남은 세 하위경우의 폐쇄 드라이버.

라운드 130 이 `A/e=0` (10/10) 과 `B/e=0` (25/25) 를 닫았다.  남은 것은
`A/e=1`, `B/e=1`, `B/e=2` 이고 §17 의 우선순위대로 그 순서로 돈다.

정리 131.1 (`src/verify_g2_ae1_131.py`) 이 각 하위경우의 **자유/lock/반복-run 패턴**을
확정한다.  등호 `f_out = F + e` 아래에서

  (a) `ν`-상승인 짧은 pass 는 전부 자유 탈출 — FREESPEC 이 정확히 그것;
  (b) 자유 하강이 정확히 `e` 개이고 **모든** 반복 run 을 연다 — REVSPEC;
  (c) 상승 lock 은 목표 궤도가 (b) 의 반복 궤도일 때만 깨질 수 있다 — 조건부 LOCKSPEC,
      판정 불가한 자리는 `LOCK0MODE` 의 α/β 두 갈래가 **망라적으로** 덮는다.

### 라운드 130 대비 갈래 수

| 하위경우 | 라운드 130 | 라운드 131 | 이유 |
|---|---|---|---|
| `A/e=1` | 10 | 10 | 갈래 수 동일, 반복-run 핀만 추가 |
| `B/e=2` | 25 | 50 | opener₀ lock 의 α/β 분기 (라운드 130 은 lock 자체가 없었다) |
| `B/e=1` | 100 | 75 | opener 를 비자유로 둔 두 갈래는 **정리로 공집합**; closer₁ 갈래만 α/β |

`B/e=1` 의 네 갈래 중 “opener 가 자유가 아니다” 인 둘은 정리 131.1(a) 로 공집합이므로
**돌리지 않는다** (돌려도 즉시 UNSAT 이지만 근거는 계산이 아니라 증명이다).
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
BIN = ROOT / "src" / "g2_cell_131.bin"
SRC = ROOT / "src" / "g2_cell_131.c"
JSONL = OUT / "rr_g2_k4_131.jsonl"
NODECAP = 60_000_000_000

ORBCAP, COSTCAP, XCAP, DCAP, EXCCAP, SHCAP = 28, 25, 0, 18, 20, 25

ASC = {0: [0, 1], 1: [0, 2]}          # mtype -> ascent sids
DESC = {0: [2], 1: [1, 3]}            # mtype -> descent sids


def type_a_splits():
    return [(a, b, 6 - a - b) for a in range(1, 5) for b in range(1, 6 - a)]


def type_b_splits():
    return [(b1, b2) for b1 in range(1, 6) for b2 in range(1, 6)]


def _lock0_needed(mtype, revspec):
    """opener₀ 의 lock 판정에 **미배치 opener** 가 필요한가 (α/β 분기가 필요한가)."""
    if mtype == 0:
        return False                     # nu(arc2) = arc0 은 언제나 이미 배치됨
    return bool(revspec >> 3 & 1)        # closer1 이 자유이면 slot 1 의 opener 가 필요


def groups():
    out = []
    # ---- 1. A/e=1 ------------------------------------------------------------
    for (l0, l1, l2) in type_a_splits():
        out.append(dict(label=f"A_e1_l{l0}{l1}{l2}", mtype=0, e=1, fout=3,
                        p1=l0, p2=l1, freespec=0b111, lockspec=0b011, revspec=0b100,
                        lock0mode=2, subcase="A_e1", split=f"{l0}{l1}{l2}"))
    # ---- 2. B/e=2 ------------------------------------------------------------
    for (b1, b2) in type_b_splits():
        for lm, tag in ((1, "a"), (0, "b")):
            out.append(dict(label=f"B_e2_b{b1}{b2}_{tag}", mtype=1, e=2, fout=4,
                            p1=b1, p2=b2, freespec=0b1111, lockspec=0b0101,
                            revspec=0b1010, lock0mode=lm,
                            subcase="B_e2", split=f"{b1}{b2}", branch=tag))
    # ---- 3. B/e=1 ------------------------------------------------------------
    for (b1, b2) in type_b_splits():
        for cs in (1, 3):                       # which closer is the free descent
            rev = 1 << cs
            free = 0b0101 | rev
            if _lock0_needed(1, rev):
                for lm, tag in ((1, "a"), (0, "b")):
                    out.append(dict(label=f"B_e1_b{b1}{b2}_c{cs}{tag}", mtype=1, e=1,
                                    fout=3, p1=b1, p2=b2, freespec=free,
                                    lockspec=0b0101, revspec=rev, lock0mode=lm,
                                    subcase="B_e1", split=f"{b1}{b2}", closer=cs,
                                    branch=tag))
            else:
                out.append(dict(label=f"B_e1_b{b1}{b2}_c{cs}", mtype=1, e=1, fout=3,
                                p1=b1, p2=b2, freespec=free, lockspec=0b0101,
                                revspec=rev, lock0mode=2, subcase="B_e1",
                                split=f"{b1}{b2}", closer=cs))
    return out


def build():
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(BIN), str(SRC)], check=True)


def argv_of(g, nodecap=NODECAP):
    return [str(v) for v in [
        g["mtype"], ORBCAP, COSTCAP, XCAP, g["fout"], g["fout"], g["e"], DCAP, EXCCAP, 1,
        g["p1"], g["p2"], SHCAP, ORBCAP + g["e"], 0, 0, 0, 0, nodecap, 1,
        g["freespec"], 1, g["lockspec"], g["revspec"], g["lock0mode"]]]


def done():
    if not JSONL.exists():
        return set()
    return {json.loads(l)["label"] for l in JSONL.read_text().splitlines() if l.strip()}


def run(g, nodecap=NODECAP, record=True):
    t0 = time.time()
    p = subprocess.run([str(BIN)] + argv_of(g, nodecap), capture_output=True,
                       text=True, check=True)
    lines = p.stdout.strip().splitlines()
    row = json.loads(lines[0])
    row.update({k: g[k] for k in ("label", "subcase", "split")})
    row["seconds"] = round(time.time() - t0, 1)
    if row["verdict"] == "SAT" and len(lines) > 1:
        row["witness"] = json.loads(lines[1])
    if record:
        with JSONL.open("a") as fh:
            fh.write(json.dumps(row) + "\n")
    return row


def main(nodecap=NODECAP):
    build()
    have = done()
    gs = groups()
    print(f"{len(gs)} runs planned", flush=True)
    for g in gs:
        if g["label"] in have:
            continue
        r = run(g, nodecap)
        print("%-24s nodes=%15s passes=%3d %-14s %8.1fs"
              % (r["label"], f'{r["nodes"]:,}', r["best_passes"], r["verdict"],
                 r["seconds"]), flush=True)
        if r["verdict"] == "SAT":
            print("!!! SAT in", r["label"], flush=True)
            return


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "plan":
        from collections import Counter
        gs = groups()
        print(json.dumps(dict(total_runs=len(gs),
                              by_subcase=dict(Counter(g["subcase"] for g in gs))),
                         indent=1))
    else:
        main()
