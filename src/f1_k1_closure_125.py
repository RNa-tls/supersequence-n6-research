#!/usr/bin/env python3
"""라운드 125 §16·§19·§20 — 일반 `(k,F) = (1,1)` **끝까지 한 번에** 도는 폐쇄 드라이버.

### 왜 이렇게 나누는가

라운드 125 §1 이 다시 센 자원 표는 **행 50개 / 하위경우 61개**, 그 중 라운드 115 조각 용량으로
**9개가 탐색 없이 죽고 52개가 살아남는다.**  살아남는 52개는 `(무거운 무게 다중집합, e, x)`
34가지이고, `(e,x)` 는 다중집합마다 **극대원소**만 잡으면 componentwise 지배로 전부 덮인다.
그렇게 **14개 그룹**이 나온다.

### 왜 `f_out` 하한을 두지 않는가 (건전성)

엔진은 `cost` 를 정확히 추적하고 `cost = S` 다.  그리고

    L = 845 + S + H = 845 + cost + hub  ≤ 871  ⟺  cost + hub ≤ 26

이므로 `SHCAP = 26` 하나가 길이 조건 **전부**다.  `e`, `x`, `f_out` 은 `S` 를 분해하는
**장부**일 뿐 독립 제약이 아니다.  따라서 `(e,x)` 상자는 순수하게 **프룬을 조이기 위한
분할**이고, 상자의 합집합이 모든 실현 가능한 `(e,x)` 를 덮으면 **거짓 기각이 0** 이다.
`FOUTMIN` 을 상자의 캡 값으로 두면 상자 안의 더 작은 `(e',x')` walk 을 잘못 버리므로
**두지 않는다.**

### 정확한 엔진 인자

    ORBCAP = 25   (잎에서 orbits == 25 를 정확히 요구)
    DCAP   = 4    (D = 5O − P = 4)
    EXCCAP = 5    (EXC = 5k = 5)
    SHCAP  = 26   (cost + hub ≤ 26  ⟺  L ≤ 871)
    RMAX   = 25 + e      ⇒ SHRUNCAP = 5·RMAX − 121 = 4 + 5e  (정확한 run 결손)
    FOUTCAP= min(2, 1+e) (보조정리 E)
    HW / HCAP / HUBMIN / HJCAP 로 무거운 무게 다중집합을 **정확히** 고정한다
    (`hub` 는 잎에서 `HUBMIN ≤ hub ≤ HCAP` 이고 둘이 같으므로 `hub = H` 가 강제된다).

라운드 120 의 반전 `Φ` 로 `b ≤ 3` 접기는 **하지 않는다** (§10: 증명된 범위 밖).
`SEAM`·`PMAX`·`SYMCUT`·`REVONLY`·`YFRESH`·`YGAP` 도 전부 끈다 — 증명 부담을 지지 않는다.
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
JSONL = OUT / "rr_f1_k1_125.jsonl"
NODECAP = 60_000_000_000

# (무거운 다중집합, e, x) — 각 다중집합의 극대 (e,x) 만.  §16 의 그룹 표.
GROUPS = [
    ((), 1, 3), ((), 2, 2), ((), 3, 1), ((), 4, 0),
    ((4,), 1, 2), ((4,), 2, 1), ((4,), 3, 0),
    ((5,), 1, 1), ((5,), 2, 0),
    ((4, 4), 1, 1), ((4, 4), 2, 0),
    ((6,), 1, 0),
    ((5, 4), 1, 0),
    ((4, 4, 4), 1, 0),
]
HWBIT = {4: 1, 5: 2, 6: 4}


def label(heavy, e, x):
    h = "H0" if not heavy else "H%d_%s" % (sum(w - 3 for w in heavy),
                                           "".join(str(w) for w in heavy))
    return f"{h}_e{e}_x{x}"


def argv_of(heavy, e, x, b, nodecap=NODECAP):
    H = sum(w - 3 for w in heavy)
    hw = 0
    for w in set(heavy):
        hw |= HWBIT[w]
    return [str(v) for v in [
        b,                       # 1  b
        26 - H,                  # 2  costcap  (cost + hub <= 26, hub finishes at H)
        25,                      # 3  orbcap   O = 25 exactly
        x,                       # 4  xcap
        min(2, 1 + e),           # 5  foutcap  (Lemma E)
        e,                       # 6  ecap
        0,                       # 7  foutmin  -- deliberately 0, see the module docstring
        0,                       # 8  ygap
        25 + e,                  # 9  rmax  => shruncap = 4 + 5e
        H,                       # 10 hcap
        4,                       # 11 dcap   D = 4
        0, 0, 0, 0,              # 12-15 bforce revonly hregion yfresh
        5,                       # 16 exccap  EXC = 5k = 5
        0, 0, 0,                 # 17-19 seam pmax symcut
        26,                      # 20 shcap  cost + hub <= 26  <=>  L <= 871
        hw,                      # 21 hw
        len(heavy),              # 22 hjcap
        H,                       # 23 hubmin  (with hcap = H this forces hub = H)
        1,                       # 24 fod
        0,                       # 25 ygapmin
        nodecap,                 # 26 nodecap
    ]]


def build():
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(BIN), str(SRC)], check=True)


def done():
    if not JSONL.exists():
        return set()
    return {json.loads(l)["label"] for l in JSONL.read_text().splitlines() if l.strip()}


def run(heavy, e, x, b, nodecap=NODECAP, record=True):
    args = [str(BIN)] + argv_of(heavy, e, x, b, nodecap)
    t0 = time.time()
    p = subprocess.run(args, capture_output=True, text=True, check=True)
    lines = p.stdout.strip().splitlines()
    row = json.loads(lines[0])
    row["label"] = f"{label(heavy, e, x)}_b{b}"
    row["group"] = label(heavy, e, x)
    row["heavy"] = list(heavy)
    row["e_cap"] = e
    row["x_cap"] = x
    row["seconds"] = round(time.time() - t0, 1)
    if row["verdict"] == "SAT" and len(lines) > 1:
        row["witness"] = json.loads(lines[1])
    if record:
        with JSONL.open("a") as fh:
            fh.write(json.dumps(row) + "\n")
    return row


def pilots(nodecap=2_000_000_000):
    """§19 — 그룹마다 b = 1 파일럿 하나."""
    build()
    out = []
    for (heavy, e, x) in GROUPS:
        r = run(heavy, e, x, 1, nodecap=nodecap, record=False)
        r["nodes_per_sec"] = int(r["nodes"] / max(r["seconds"], 0.05))
        out.append(r)
        print("%-16s nodes=%15s  passes=%3d  %-14s %8.1fs  %s/s"
              % (r["group"], f'{r["nodes"]:,}', r["best_passes"], r["verdict"],
                 r["seconds"], f'{r["nodes_per_sec"]:,}'), flush=True)
    return out


def main(splits=(1, 2, 3, 4, 5)):
    build()
    have = done()
    for (heavy, e, x) in GROUPS:
        for b in splits:
            lab = f"{label(heavy, e, x)}_b{b}"
            if lab in have:
                continue
            r = run(heavy, e, x, b)
            print("%-20s nodes=%15s passes=%3d %-14s %8.1fs"
                  % (lab, f'{r["nodes"]:,}', r["best_passes"], r["verdict"], r["seconds"]),
                  flush=True)
            if r["verdict"] == "SAT":
                print("!!! SAT in", lab, "- stopping this group", flush=True)
                return


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "pilot":
        pilots()
    else:
        main()
