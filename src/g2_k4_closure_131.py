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


def main(nodecap=NODECAP, only=None):
    build()
    have = done()
    gs = groups()
    if only:
        gs = [g for g in gs if g["subcase"] in only]
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


def round130_rows():
    """라운드 130 이 이미 UNSAT_COMPLETE 로 닫은 런들 (같은 셀, 건전한 사후-수정 엔진)."""
    f = OUT / "rr_g2_k4_130.jsonl"
    if not f.exists():
        return []
    return [json.loads(l) for l in f.read_text().splitlines() if l.strip()]


def summarise(controls=None, positive=None, theory=None):
    from collections import Counter
    rs = [json.loads(l) for l in JSONL.read_text().splitlines()] if JSONL.exists() else []
    rs = [r for r in rs if r]
    r130 = round130_rows()
    gs = groups()
    bysub = {}
    for g in gs:
        bysub.setdefault(g["subcase"], dict(planned=0, done=0, unsat=0, unknown=0,
                                            sat=0, nodes=0, seconds=0.0))["planned"] += 1
    for r in rs:
        d = bysub[r["subcase"]]
        d["done"] += 1
        d["nodes"] += r["nodes"]
        d["seconds"] += r["seconds"]
        d["unsat"] += r["verdict"] == "UNSAT_COMPLETE"
        d["unknown"] += r["verdict"] == "UNKNOWN_CAP"
        d["sat"] += r["verdict"] == "SAT"
    for d in bysub.values():
        d["seconds"] = round(d["seconds"], 1)
        d["closed"] = (d["done"] == d["planned"] and d["unsat"] == d["planned"])
    # 라운드 130 이 닫은 두 하위경우를 그대로 이어받는다 (재실행하지 않는다).
    prev = {}
    for r in r130:
        d = prev.setdefault(r["subcase"], dict(runs=0, unsat=0, nodes=0))
        d["runs"] += 1
        d["unsat"] += r["verdict"] == "UNSAT_COMPLETE"
        d["nodes"] += r["nodes"]
    cell = {}
    for sc, planned in (("A_e0", 10), ("B_e0", 25)):
        p130 = prev.get(sc, dict(runs=0, unsat=0, nodes=0))
        cell[sc] = dict(source="round 130", planned=planned, unsat=p130["unsat"],
                        nodes=p130["nodes"], closed=(p130["unsat"] == planned))
    for sc in ("A_e1", "B_e1", "B_e2"):
        d = bysub.get(sc, dict(planned=0, done=0, unsat=0, nodes=0, closed=False))
        cell[sc] = dict(source="round 131", planned=d["planned"], done=d["done"],
                        unsat=d["unsat"], nodes=d["nodes"], closed=d["closed"])
    remaining = [sc for sc, d in cell.items() if not d["closed"]]
    return dict(
        round=131, cell="(k,G) = (4,2)", outer_axis="G (never F)",
        theory=theory,
        engine=dict(
            file="src/g2_cell_131.c",
            derived_from="src/g2_cell_130.c (post-fix: every pass sets the hexagon mask)",
            new_rules=[
                "REVSPEC - Theorem 131.1(b): a repeat run is opened ONLY by the free "
                "omega=2 exit of a designated nu-descent short pass",
                "conditional LOCKSPEC - Theorem 131.1(c): an ascent's locality lock is "
                "applied only when no KNOWN repeat orbit equals its target orbit",
                "LOCK0MODE alpha/beta - exhaustive split for the one undecidable place "
                "(type B opener0 while opener1 is unplaced)",
                "leaf: #repeat runs == e and r == O + e",
            ],
            revspec_off="REVSPEC < 0 reproduces Round-130 behaviour exactly",
            mask_invariant="-DCHECKMASK build asserts #entered hexagons == passes - reentries"),
        parameters=dict(ORBCAP=ORBCAP, COSTCAP=COSTCAP, XCAP=XCAP, DCAP=DCAP,
                        EXCCAP=EXCCAP, SHCAP=SHCAP, HCAP=0, HW=0, node_cap=NODECAP,
                        RMAX="28 + e", FOUTCAP="FOUTMIN = e + 2", TARGET=122),
        n_runs_planned=len(gs), n_runs_done=len(rs),
        by_subcase=bysub,
        branch_counts=dict(A_e1=dict(round130=10, round131=10),
                           B_e2=dict(round130=25, round131=50),
                           B_e1=dict(round130=100, round131=75)),
        cell_status=cell,
        subcases_remaining=sorted(remaining),
        cell_closed=(len(remaining) == 0),
        total_nodes_round131=sum(r["nodes"] for r in rs),
        total_seconds_round131=round(sum(r["seconds"] for r in rs), 1),
        max_passes=max((r["best_passes"] for r in rs), default=0),
        cap_hits=[r["label"] for r in rs if r["verdict"] == "UNKNOWN_CAP"],
        sat_found=[r["label"] for r in rs if r["verdict"] == "SAT"],
        verdicts=dict(Counter(r["verdict"] for r in rs)),
        controls=controls, positive_control=positive,
        coverage_matrix={g["label"]: next((r["verdict"] for r in rs
                                           if r["label"] == g["label"]), "NOT_RUN")
                         for g in gs},
        ledger_note=("the (4,2) cell counts toward the outer ledger only if EVERY one of "
                     "the five subcases and every branch is UNSAT_COMPLETE"),
        label="ROUND-131 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
        ledger={"INDEPENDENTLY_AUDITED_Q2_RESIDUAL": 4782,
                "CLAUDE_FULL_JOINT_Q2": "6396/6396",
                "NR6": "ASSUMED"},
        disclaimer="This project has not proved L6 >= 872")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "plan":
        from collections import Counter
        gs = groups()
        print(json.dumps(dict(total_runs=len(gs),
                              by_subcase=dict(Counter(g["subcase"] for g in gs))),
                         indent=1))
    elif len(sys.argv) > 1 and sys.argv[1] == "report":
        print(json.dumps(summarise(), ensure_ascii=False, indent=1))
    else:
        # 사용법: g2_k4_closure_131.py [subcase[,subcase...]] [nodecap]
        only = None
        cap = NODECAP
        for a in sys.argv[1:]:
            if a.isdigit():
                cap = int(a)
            else:
                only = set(a.split(","))
        main(cap, only)
