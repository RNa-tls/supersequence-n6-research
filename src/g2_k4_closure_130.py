#!/usr/bin/env python3
"""라운드 130 — `(k,G) = (4,2)` 칸 폐쇄 드라이버.

라운드 129 가 얼린 다섯 하위경우를 **처음부터 다시 유도**한 뒤 각 분할 모양마다 정확 탐색을
돌린다.  바깥 좌표는 `(k, G)` 이고 `F` 는 내부 좌표일 뿐이다.

### 다섯 하위경우의 재유도

    k = 4, G = 2  ⇒  P = 122, O = 28, D = 5k − G = 18
    L = 869 + k + e + x + H − f_out ≤ 871  ⇒  **f_out ≥ e + x + H + 2**
    라운드 129 정리 129.1: f_out ≤ F + e,  그리고 F ≤ G = 2
      ⇒ e + x + H + 2 ≤ f_out ≤ F + e ≤ 2 + e
      ⇒ **x = H = 0, F = 2, f_out = e + 2, S = 23 + k + e + x − f_out = 25**
    f_out ≤ #짧은 pass = G + m
      ⇒ 유형 A(m=1, 3개): e ≤ 1     유형 B(m=2, 4개): e ≤ 2

    ⇒ (A,e=0) (A,e=1) (B,e=0) (B,e=1) (B,e=2)  — 정확히 다섯.

### 강제되는 자유 탈출 패턴 (증명된 것만 쓴다)

`e = 0` 이면 분열 궤도가 없으므로 자유 탈출은 **전부 경우 (i)** 이고, 경우 (i) 는
`p < ν(p)` 즉 **`ν`-상승**이다.  `F = 2` 이므로 상승은 정확히 둘이다.

* **A/e=0** — 상승은 arc0·arc1 이므로 **arc0·arc1 이 자유, arc2 는 자유가 아니다.**
  그리고 둘 다 경우 (i) 이므로 **국소성 lock**: arc0 의 자유 후속이 여는 run 이 arc1 을
  담아야 하고(그 궤도의 유일한 run 이다), arc1 의 것이 arc2 를 담아야 한다.
* **B/e=0** — 각 2-순환의 상승은 슬롯을 **여는** pass 이므로 **두 opener 가 자유, closer 는
  아니다**, 그리고 둘 다 경우 (i) 이므로 lock 이 걸린다.
* **A/e=1** — `f_out = 3` 이라 세 arc 이 전부 자유.  경우 (ii) 는 목표 궤도가 셋 다 달라
  많아야 하나이고 `#경우(ii) ≥ f_out − F = 1` 이므로 **정확히 하나**, 그리고 경우 (i) 는
  상승뿐이라 `{arc0, arc1}` — 따라서 **경우 (ii) = arc2**, lock 은 arc0·arc1 에 걸린다.
* **B/e=1** — `f_out = 3`: 네 pass 중 셋이 자유.  어느 것이 자유가 아닌지는 강제되지
  않으므로 **네 갈래로 나눠** 각각 정확히 돌린다.  lock 은 증명되지 않아 쓰지 않는다.
* **B/e=2** — 넷 다 자유.  경우 (i) 은 상승(=opener)뿐이지만 opener 가 경우 (ii) 일 수도
  있어 lock 은 **증명되지 않았다** — 쓰지 않는다.

`FREEON = 1` 이면 마스크에 없는 짧은 pass 는 자유로 나갈 수 **없다**; 위 각 경우에서
`f_out` 이 마스크 크기와 같으므로 이는 정확한 등식이지 추가 가정이 아니다.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
BIN = ROOT / "src" / "g2_cell_130.bin"
SRC = ROOT / "src" / "g2_cell_130.c"
JSONL = OUT / "rr_g2_k4_130.jsonl"
NODECAP = 30_000_000_000

ORBCAP, COSTCAP, XCAP, DCAP, EXCCAP, SHCAP = 28, 25, 0, 18, 20, 25


def type_a_splits():
    """arc 길이 (l0, l1, l2), l0+l1+l2 = 6, 전부 >= 1 — 순서 있는 분해 10가지."""
    return [(a, b, 6 - a - b) for a in range(1, 5) for b in range(1, 6 - a)]


def type_b_splits():
    return [(b1, b2) for b1 in range(1, 6) for b2 in range(1, 6)]


def groups():
    """다섯 하위경우 × 분할 모양 × (필요한 경우) 자유-패턴 갈래."""
    out = []
    for (l0, l1, l2) in type_a_splits():
        out.append(dict(label=f"A_e0_l{l0}{l1}{l2}", mtype=0, e=0, fout=2,
                        p1=l0, p2=l1, freespec=0b011, lockspec=0b011,
                        subcase="A_e0", split=f"{l0}{l1}{l2}"))
        out.append(dict(label=f"A_e1_l{l0}{l1}{l2}", mtype=0, e=1, fout=3,
                        p1=l0, p2=l1, freespec=0b111, lockspec=0b011,
                        subcase="A_e1", split=f"{l0}{l1}{l2}"))
    for (b1, b2) in type_b_splits():
        out.append(dict(label=f"B_e0_b{b1}{b2}", mtype=1, e=0, fout=2,
                        p1=b1, p2=b2, freespec=0b0101, lockspec=0b0101,
                        subcase="B_e0", split=f"{b1}{b2}"))
        for nf in range(4):                      # which short pass is NOT free
            out.append(dict(label=f"B_e1_b{b1}{b2}_nf{nf}", mtype=1, e=1, fout=3,
                            p1=b1, p2=b2, freespec=0b1111 & ~(1 << nf), lockspec=0,
                            subcase="B_e1", split=f"{b1}{b2}", notfree=nf))
        out.append(dict(label=f"B_e2_b{b1}{b2}", mtype=1, e=2, fout=4,
                        p1=b1, p2=b2, freespec=0b1111, lockspec=0,
                        subcase="B_e2", split=f"{b1}{b2}"))
    order = {"A_e0": 0, "B_e0": 1, "A_e1": 2, "B_e2": 3, "B_e1": 4}
    out.sort(key=lambda g: (order[g["subcase"]], g["label"]))
    return out


def build():
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(BIN), str(SRC)], check=True)


def argv_of(g, nodecap=NODECAP):
    return [str(v) for v in [
        g["mtype"], ORBCAP, COSTCAP, XCAP, g["fout"], g["fout"], g["e"], DCAP, EXCCAP, 1,
        g["p1"], g["p2"], SHCAP, ORBCAP + g["e"], 0, 0, 0, 0, nodecap, 1,
        g["freespec"], 1, g["lockspec"]]]


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
        print("%-22s nodes=%15s passes=%3d %-14s %8.1fs"
              % (r["label"], f'{r["nodes"]:,}', r["best_passes"], r["verdict"],
                 r["seconds"]), flush=True)
        if r["verdict"] == "SAT":
            print("!!! SAT in", r["label"], flush=True)
            return


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "plan":
        gs = groups()
        from collections import Counter
        print(json.dumps(dict(total_runs=len(gs),
                              by_subcase=dict(Counter(g["subcase"] for g in gs))), indent=1))
    else:
        main()


def subcase_derivation():
    """§1 — 다섯 하위경우를 라운드 129 표를 믿지 않고 처음부터 다시 유도한다."""
    k, G, LCAP = 4, 2, 871
    P, O, D = 120 + G, 24 + k, 5 * k - G
    rows = []
    for typ, m, nshort in (("A", 1, 3), ("B", 2, 4)):
        for Fi in (1, 2):
            for e in range(0, 6):
                for x in range(0, 6):
                    for H in range(0, 6):
                        for f in range(0, nshort + 1):
                            if f > Fi + e:                    # Theorem 129.1
                                continue
                            if typ == "B" and Fi != 2:        # type B forces F = 2
                                continue
                            if k + e + x + H - f > LCAP - 869:
                                continue
                            rows.append(dict(type=typ, F=Fi, e=e, x=x, H=H, f_out=f,
                                             S=23 + k + e + x - f,
                                             N=(23 + k + e + x - f) - 22 - k,
                                             r=O + e, t=1,
                                             L=869 + k + e + x + H - f))
    return dict(k=k, G=G, P=P, O=O, D=D,
                budget="f_out >= e + x + H + 2 from L <= 871 with k = 4",
                theorem="f_out <= F + e (Round 129) with F <= 2",
                forced="x = H = 0, F = 2, f_out = e + 2, S = 25, N = -1",
                n_subcases=len(rows), subcases=rows,
                matches_round_129=(len(rows) == 5),
                typeA_F1_contributes=len([r for r in rows if r["type"] == "A" and r["F"] == 1]))


def summarise(controls=None, positive=None):
    from collections import Counter
    rs = [json.loads(l) for l in JSONL.read_text().splitlines()] if JSONL.exists() else []
    rs = [r for r in rs if r]
    gs = groups()
    bysub = {}
    for g in gs:
        bysub.setdefault(g["subcase"], {"planned": 0, "done": 0, "unsat": 0,
                                        "unknown": 0, "sat": 0, "nodes": 0,
                                        "seconds": 0.0})["planned"] += 1
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
    closed = [s for s, d in bysub.items() if d["closed"]]
    remaining = [s for s, d in bysub.items() if not d["closed"]]
    rep = dict(
        round=130, cell="(k,G) = (4,2)", outer_axis="G (never F)",
        derivation=subcase_derivation(),
        engine=dict(
            file="src/g2_cell_130.c",
            target="#define TARGET 122 (P = 120 + G)",
            heavy_tails_offered="none - H = 0 is exact, so only omega in {2,3} joints",
            x="XCAP = 0 - no intra-orbit cost-1 joint",
            short_state_machine=("rewritten for G = 2: type A is a 3-arc machine on ONE "
                                 "hexagon whose arcs appear in nu-order (equivalent to "
                                 "F = 2); type B is two independent 2-arc slot machines on "
                                 "two DIFFERENT hexagons, interleaving allowed"),
            free_exit_forcing=("FREESPEC/FREEON pin exactly which short passes exit freely; "
                               "for e = 0 that pattern is PROVED (every free exit is case (i), "
                               "hence a nu-ascent, and F = 2 gives exactly two ascents)"),
            locality_lock=("LOCKSPEC: a case-(i) pass's free successor starts the very run "
                           "containing nu(p), so the walk cannot leave that orbit until nu(p) "
                           "is placed.  Applied only where case (i) is PROVED: A/e=0, B/e=0 "
                           "and A/e=1 (where exactly one pass is case (ii) and it must be arc2)"),
            reused_unchanged=["geometry build()", "light move tables M2/M3a/M3b/M3c",
                              "EXC orbit-cover excess", "fod fresh-orbit deficit",
                              "NTAB/BESTSEG chain capacity", "capacity_ok/dcommitted/dfeasible"]),
        parameters=dict(ORBCAP=ORBCAP, COSTCAP=COSTCAP, XCAP=XCAP, DCAP=DCAP,
                        EXCCAP=EXCCAP, SHCAP=SHCAP, HCAP=0, HW=0, node_cap=NODECAP,
                        RMAX="28 + e", FOUTCAP="FOUTMIN = e + 2"),
        n_runs_planned=len(gs), n_runs_done=len(rs),
        by_subcase=bysub,
        subcases_closed=sorted(closed), subcases_remaining=sorted(remaining),
        cell_closed=(len(remaining) == 0),
        total_nodes=sum(r["nodes"] for r in rs),
        total_seconds=round(sum(r["seconds"] for r in rs), 1),
        max_passes=max((r["best_passes"] for r in rs), default=0),
        cap_hits=[r["label"] for r in rs if r["verdict"] == "UNKNOWN_CAP"],
        sat_found=[r["label"] for r in rs if r["verdict"] == "SAT"],
        verdicts=dict(Counter(r["verdict"] for r in rs)),
        controls=controls, positive_control=positive,
        coverage_matrix={g["label"]: next((r["verdict"] for r in rs
                                           if r["label"] == g["label"]), "NOT_RUN")
                         for g in gs},
        ledger_note=("the (4,2) cell counts toward the ledger only if EVERY one of the five "
                     "subcases and every split shape is UNSAT_COMPLETE"),
        label="ROUND-130 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
        ledger={"INDEPENDENTLY_AUDITED_Q2_RESIDUAL": 4782,
                "CLAUDE_FULL_JOINT_UNSAT_COMPLETE": 6396,
                "unchanged_by_this_round": True},
        disclaimer="This project has not proved L6 >= 872.")
    (OUT / "rr_g2_k4_130.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    return rep
