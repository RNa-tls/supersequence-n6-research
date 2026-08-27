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

# §16 그룹 표 = 라운드 125 §1 이 살려 둔 **52개 하위경우 전부**를, 각자의 **정확한**
# `(e, x, f_out, 무거운 무게 다중집합)` 으로 돌린다.  극대 상자로 뭉치면 `FOUTMIN` 을 쓸 수
# 없어(상자 안의 더 작은 walk 을 잘못 버린다) 프룬이 크게 약해진다 — 실측으로 극대 상자는
# 2e9 노드에서 캡에 걸리는데, 같은 경우를 정확한 행으로 돌리면 5.0e8 노드에 **완주**한다.
#
# 덮개 논증: 어떤 walk 이든 정확한 `(e*, x*, f*, H*, 다중집합*)` 을 가지며 그것이 61개
# 하위경우 중 하나다.  9개는 라운드 115 조각 용량으로 **탐색 없이** 불가능하고, 나머지 52개는
# 각각 자기 실행에서 잡힌다 (`ECAP=e*`, `XCAP=x*`, `FOUTCAP=FOUTMIN=f*` 로 `f_out` 이
# 정확히 고정되고, `HCAP=HUBMIN=H*` 로 `hub` 가 정확히 고정된다).  **거짓 기각 0.**
def alive_rows():
    import sys as _s
    _s.path.insert(0, str(Path(__file__).resolve().parent))
    from verify_f1_k1_rows_125 import summarise as _rows
    rs = _rows()["alive_subcases"]
    rs.sort(key=lambda r: (sum(w - 3 for w in r["heavy_weights"]),
                           r["e"] + r["x"], r["e"], r["x"], r["f_out"]))
    return [(tuple(r["heavy_weights"]), r["e"], r["x"], r["f_out"]) for r in rs]


GROUPS = alive_rows()
HWBIT = {4: 1, 5: 2, 6: 4}


def label(heavy, e, x, f):
    H = sum(w - 3 for w in heavy)
    h = "H0" if not heavy else "H%d_%s" % (H, "".join(str(w) for w in heavy))
    return f"{h}_e{e}_x{x}_f{f}"


def argv_of(heavy, e, x, f, b, nodecap=NODECAP):
    H = sum(w - 3 for w in heavy)
    hw = 0
    for w in set(heavy):
        hw |= HWBIT[w]
    return [str(v) for v in [
        b,                       # 1  b
        24 + e + x - f,          # 2  costcap = S exactly for this row
        25,                      # 3  orbcap   O = 25 exactly
        x,                       # 4  xcap
        f,                       # 5  foutcap
        e,                       # 6  ecap
        f,                       # 7  foutmin  -> with foutcap = f this pins f_out = f
        0,                       # 8  ygap
        25 + e,                  # 9  rmax  => shruncap = 4 + 5e (exact run shortfall)
        H,                       # 10 hcap
        4,                       # 11 dcap   D = 4
        0, 0, 0, 0,              # 12-15 bforce revonly hregion yfresh
        5,                       # 16 exccap  EXC = 5k = 5
        0, 0, 0,                 # 17-19 seam pmax symcut
        26,                      # 20 shcap  cost + hub <= 26  <=>  L <= 871
        hw,                      # 21 hw
        len(heavy),              # 22 hjcap
        H,                       # 23 hubmin  (with hcap = H this pins hub = H)
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


def run(heavy, e, x, f, b, nodecap=NODECAP, record=True):
    args = [str(BIN)] + argv_of(heavy, e, x, f, b, nodecap)
    t0 = time.time()
    p = subprocess.run(args, capture_output=True, text=True, check=True)
    lines = p.stdout.strip().splitlines()
    row = json.loads(lines[0])
    row["label"] = f"{label(heavy, e, x, f)}_b{b}"
    row["group"] = label(heavy, e, x, f)
    row["heavy"] = list(heavy)
    row["e_row"] = e
    row["x_row"] = x
    row["f_out_row"] = f
    row["H_row"] = sum(w - 3 for w in heavy)
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
    for (heavy, e, x, f) in GROUPS:
        r = run(heavy, e, x, f, 1, nodecap=nodecap, record=False)
        r["nodes_per_sec"] = int(r["nodes"] / max(r["seconds"], 0.05))
        out.append(r)
        print("%-16s nodes=%15s  passes=%3d  %-14s %8.1fs  %s/s"
              % (r["group"], f'{r["nodes"]:,}', r["best_passes"], r["verdict"],
                 r["seconds"], f'{r["nodes_per_sec"]:,}'), flush=True)
    return out


def main(splits=(1, 2, 3, 4, 5)):
    build()
    have = done()
    for (heavy, e, x, f) in GROUPS:
        for b in splits:
            lab = f"{label(heavy, e, x, f)}_b{b}"
            if lab in have:
                continue
            r = run(heavy, e, x, f, b)
            print("%-20s nodes=%15s passes=%3d %-14s %8.1fs"
                  % (lab, f'{r["nodes"]:,}', r["best_passes"], r["verdict"], r["seconds"]),
                  flush=True)
            if r["verdict"] == "SAT":
                print("!!! SAT in", lab, "- stopping this group", flush=True)
                return


def summarise():
    import sys as _s
    _s.path.insert(0, str(Path(__file__).resolve().parent))
    from verify_f1_k1_rows_125 import summarise as rowsum
    from verify_f1_k1_w6_125 import summarise as w6sum
    from f1_k1_controls_125 import controls

    rows = rowsum()
    rs = [json.loads(l) for l in JSONL.read_text().splitlines() if l.strip()]
    by = {}
    for r in rs:
        by.setdefault(r["group"], []).append(r)
    groups = {}
    for g, lst in by.items():
        groups[g] = dict(
            runs=len(lst), nodes=sum(r["nodes"] for r in lst),
            seconds=round(sum(r["seconds"] for r in lst), 1),
            max_passes=max(r["best_passes"] for r in lst),
            verdicts=sorted({r["verdict"] for r in lst}),
            heavy=lst[0]["heavy"], e=lst[0]["e_row"], x=lst[0]["x_row"],
            f_out=lst[0]["f_out_row"], H=lst[0]["H_row"],
            closed=all(r["verdict"] == "UNSAT_COMPLETE" for r in lst) and len(lst) == 5)
    capped = [r["label"] for r in rs if r["verdict"] == "UNKNOWN_CAP"]
    sat = [r["label"] for r in rs if r["verdict"] == "SAT"]
    expected = {label(*g) for g in GROUPS}
    complete = all(groups.get(g, {}).get("closed") for g in expected)
    w6 = w6sum()
    rep = dict(
        round=125, cell=[1, 1], P=25 * 5 - 4, node_cap=NODECAP,
        model=("end-to-end exact DFS from the initial state; the first short pass X is a "
               "STATE TRANSITION inside the DFS (sstate 0 -> 1 -> 2), never an enumerated "
               "root, so the Round-123 root explosion does not occur"),
        budget=rows["identities"],
        resource_table=dict(
            n_resource_rows=rows["n_resource_rows"], n_subcases=rows["n_subcases"],
            n_dead_by_capacity=rows["n_subcases_dead_by_capacity"],
            n_alive=rows["n_subcases_alive"],
            n_rows_with_a_live_subcase=rows["n_rows_with_a_live_subcase"],
            max_H=rows["max_H"], max_e=rows["max_e"], max_x=rows["max_x"],
            dead_subcases=rows["dead_subcases"],
            recount_matches_round_122=(rows["n_resource_rows"] == 50
                                       and rows["n_subcases"] == 61
                                       and rows["n_subcases_dead_by_capacity"] == 9),
            H_classification=rows["H_classification"],
            negative_N=rows["negative_N"]),
        weight6_correction=w6["weight6_degeneracy"],
        heavy_census={w: dict(n_tails=d["n_tails"], n_classes=d["n_classes"],
                              all_or_nothing=d["all_or_nothing"],
                              never_returns_to_source_hexagon=d["never_returns_to_source_hexagon"],
                              intra_orbit=d["intra_orbit_all_720"])
                      for w, d in w6["by_weight"].items()},
        n_final_groups=len(GROUPS), n_runs_planned=len(GROUPS) * 5, n_runs_done=len(rs),
        by_group=groups,
        engine_parameters=dict(
            ORBCAP=25, DCAP=4, EXCCAP=5, SHCAP=26,
            COSTCAP="24 + e + x - f_out (= S exactly for the row)",
            RMAX="25 + e  => SHRUNCAP = 4 + 5e",
            FOUTCAP="f_out", FOUTMIN="f_out (pins f_out exactly)",
            HCAP="H", HUBMIN="H (pins hub exactly)", HJCAP="number of heavy joints",
            HW="bitmask over the weights in the multiset", FOD=1,
            symmetry_cuts_used="none - SEAM, PMAX, SYMCUT, REVONLY, YFRESH, YGAP, YGAPMIN "
                               "are all OFF, and b is NOT folded to b <= 3 (section 10)"),
        total_nodes=sum(r["nodes"] for r in rs),
        total_seconds=round(sum(r["seconds"] for r in rs), 1),
        max_passes_reached=max((r["best_passes"] for r in rs), default=0),
        cap_hits=capped, sat_found=sat,
        cell_closed=(complete and not capped and not sat),
        coverage_argument=(
            "every walk in the cell has an exact (e, x, f_out, H, heavy multiset); that is one "
            "of the 61 subcases; 9 are impossible with no search by the Round-115 chain-capacity "
            "bound and the other 52 each get their own run with those exact values, so the union "
            "of the 52 runs (x 5 splits) covers the cell with zero false rejection"),
        controls=dict(reproduction=controls(budget_seconds=90)),
        label="ROUND-125 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
        ledger={"INDEPENDENTLY_AUDITED_Q2_RESIDUAL": 4782,
                "CLAUDE_FULL_JOINT_UNSAT_COMPLETE": 6396,
                "unchanged_by_this_round": True},
        disclaimer="This project has not proved L6 >= 872.")
    (OUT / "rr_f1_k1_125.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    return rep


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "pilot":
        pilots()
    elif len(sys.argv) > 1 and sys.argv[1] == "summarise":
        r = summarise()
        print(json.dumps({k: r[k] for k in ("n_final_groups", "n_runs_done", "total_nodes",
                                            "total_seconds", "max_passes_reached",
                                            "cap_hits", "sat_found", "cell_closed")},
                         indent=1))
    else:
        main()
