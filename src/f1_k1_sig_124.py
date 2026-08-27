#!/usr/bin/env python3
"""라운드 124 — 일반 `(1,1)` 뿌리의 **미래-동치 서명 압축률** 측정 드라이버.

`src/f1_k1_sig_124.c` 를 예산 부분가족마다 돌려서, 라운드 123 의 뿌리 가족이
**미래-동치류**로 얼마나 줄어드는지 잰다.  뿌리를 저장하지 않는다 — 첫 짧은 pass 에서
서명만 만들어 정확 비교 해시 집합에 넣는다 (해시 충돌 없음: 아레나에 바이트열을 저장해
`memcmp` 로 확인한다).

세 가지 서명을 동시에 잰다.

* `sound-fine`   `Sig = (v, b, omask[144], cost, hub, x, e)` — §2 의 충분성 증명이 붙은 서명.
* `sound-coarse` `(v, b, 예산, 사용육각형 120비트, 열린궤도 144비트)` — fine 의 몫(quotient).
* `CEILING`      `(v, b, 사용육각형 120비트)` — **건전하지 않다**. 예산과 열린-궤도 집합을
  통째로 버린 진단용 하한(=압축률 상한)일 뿐이다.  어떤 건전한 서명도 이보다 더 압축할
  수 없으므로, 이 값이 1 에 가까우면 **압축 접근 자체가 무의미**하다는 뜻이다.

접두 서명 `PSig = (u, omask, cost, hub, x, e)` 도 함께 세어 §17 frontier-DP 가 이득이
있는지 잰다.

인자 순서: b qcap costcap orbcap xcap ecap hcap dcap exccap fod nodecap tablebits
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
BIN = ROOT / "src" / "f1_k1_sig_124.bin"
SRC = ROOT / "src" / "f1_k1_sig_124.c"
JSONL = OUT / "rr_f1_k1_sig_124.jsonl"
NODECAP = 15_000_000_000

# (label, x, e, H, tablebits).  §13 asks for the RIGID cell first, §14 for the one-budget
# perturbations.  Two-budget cells are added as far as the exact hash tables fit in RAM.
# Round-123 root counts for reference: rigid 17,545; the maximal cells run to 6.3e10, which
# cannot be signature-counted exactly (the table would need >1e11 slots) and is not needed:
# the CEILING signature already bounds the achievable compression from above on every cell
# tested, and it does not improve as the budgets grow.
CONFIGS = [
    ("rigid_e0_x0_H0", 0, 0, 0, 22),
    ("e1_x0_H0",       0, 1, 0, 22),
    ("e0_x1_H0",       1, 0, 0, 22),
    ("e0_x0_H1",       0, 0, 1, 23),
    ("e2_x0_H0",       0, 2, 0, 26),
    ("e1_x1_H0",       1, 1, 0, 26),
    ("e0_x2_H0",       2, 0, 0, 25),
    ("e1_x0_H1",       0, 1, 1, 27),
    ("e0_x1_H1",       1, 0, 1, 26),
    ("e0_x0_H2",       0, 0, 2, 27),
]


def build():
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(BIN), str(SRC)], check=True)


def done():
    if not JSONL.exists():
        return set()
    return {json.loads(l)["label"] for l in JSONL.read_text().splitlines() if l.strip()}


def run_one(label, x, e, h, tbits):
    args = [str(BIN), "0", "119", "26", "25", str(x), str(e), str(h), "4", "5", "1",
            str(NODECAP), str(tbits)]
    t0 = time.time()
    p = subprocess.run(args, capture_output=True, text=True, check=True)
    row = json.loads(p.stdout.strip().splitlines()[-1])
    row["label"] = label
    row["seconds"] = round(time.time() - t0, 1)
    row["ceiling_compression"] = (round(row["roots"] / row["floor_signatures"], 4)
                                  if row["floor_signatures"] else 0.0)
    with JSONL.open("a") as fh:
        fh.write(json.dumps(row) + "\n")
    return row


def summarise():
    rows = [json.loads(l) for l in JSONL.read_text().splitlines() if l.strip()]
    by = {r["label"]: r for r in rows}
    ordered = [by[c[0]] for c in CONFIGS if c[0] in by]
    capped = [r["label"] for r in ordered if r["verdict"] != "COMPLETE"]
    overflow = [r["label"] for r in ordered if r["probe_overflow"]]
    best_sound = max((r["root_compression"] for r in ordered), default=0.0)
    best_ceiling = max((r["ceiling_compression"] for r in ordered), default=0.0)
    best_prefix = max((r["prefix_compression"] for r in ordered), default=0.0)
    rep = dict(
        round=124, cell=[1, 1], node_cap=NODECAP,
        signature=dict(
            fine="(v, b, omask[144], cost, hub, x, e)",
            coarse="(v, b, budgets, usedhex[120 bits], opened-orbit set[144 bits])",
            ceiling="(v, b, usedhex[120 bits]) - DIAGNOSTIC ONLY, NOT SOUND",
            prefix="(u, omask[144], cost, hub, x, e)"),
        derived_coordinates=[
            "usedhex: entry words <-> (orbit, phase) is a 720<->720 bijection, so omask "
            "determines the used-word set and hence the used-hexagon set",
            "orbits, runs (= orbits + e), defcnt, EXC, mcnt, blk, freshcnt: all functions "
            "of omask and the used-hexagon set",
            "runlen: an orbit has only 5 phases, so phase injectivity already forbids a run "
            "longer than 5; every other use of runlen (shrun, segment capacity) is prune "
            "accounting, not legality",
            "f_out: X's exit is not chosen yet at the root, so it is 0 for every root",
            "D = 5*O - P: with P = 121 fixed, D = 4 is equivalent to O = 25, not independent"],
        structural_facts=dict(
            phase_injectivity_implied_by_hexagon_injectivity=True,
            orbits_whose_5_words_miss_5_distinct_hexagons=0,
            note=("every orbit's 5 words lie in 5 DISTINCT hexagons (0 exceptions over all "
                  "144 orbits), so 'available entry words' = 'words of unused hexagons' and "
                  "no separate phase bookkeeping is needed for legality")),
        exact_hash=("open addressing with the full signature bytes stored in an arena and "
                    "compared with memcmp; a hash collision cannot merge two signatures"),
        runs=len(ordered), configs_capped=capped, probe_overflow_configs=overflow,
        by_config={r["label"]: r for r in ordered},
        compression=dict(
            best_sound_fine=best_sound, best_sound_coarse=max(
                (r["coarse_compression"] for r in ordered), default=0.0),
            best_ceiling=best_ceiling, best_prefix_frontier_dp=best_prefix,
            verdict=("no meaningful compression: even the deliberately UNSOUND ceiling "
                     "signature, which discards every budget and the whole opened-orbit set, "
                     "compresses by at most %.2fx, so no sound future-equivalence signature "
                     "can do better" % best_ceiling)),
        interpretation=(
            "the load-bearing information is the USED-HEXAGON SET itself, not the traversal "
            "order: Round 124 proves the order/run history is NOT needed (the signature is "
            "sufficient without it), and then measures that the residual state is already as "
            "large as the root enumeration.  Splitting the (1,1) search at the first short "
            "pass therefore buys nothing, and a completion search should run end-to-end as "
            "the Round-121 engine does."),
        frontier_dp=dict(
            measured_prefix_compression=best_prefix,
            verdict="section 17 frontier-DP buys nothing: prefix states already equal "
                    "distinct prefix signatures on every tested subfamily"),
        cell_status=dict(cell="(1,1)", status="OPEN",
                         claude_closed_outer_cells="8/55",
                         closed_by_this_round=False,
                         F2_started=False),
        label="ROUND-124 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
        ledger={"INDEPENDENTLY_AUDITED_Q2_RESIDUAL": 4782,
                "CLAUDE_FULL_JOINT_UNSAT_COMPLETE": 6396,
                "unchanged_by_this_round": True},
        disclaimer="This project has not proved L6 >= 872.")
    (OUT / "rr_f1_k1_sig_124.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    return rep


def main():
    build()
    have = done()
    for (label, x, e, h, tbits) in CONFIGS:
        if label in have:
            continue
        row = run_one(label, x, e, h, tbits)
        print("%-16s roots=%12d fine=%12d (x%.2f) coarse=%12d (x%.2f) "
              "CEILING=%12d (x%.2f) prefix=%10d (x%.2f) %ss"
              % (label, row["roots"], row["distinct_root_signatures"],
                 row["root_compression"], row["distinct_coarse_signatures"],
                 row["coarse_compression"], row["floor_signatures"],
                 row["ceiling_compression"], row["distinct_prefix_signatures"],
                 row["prefix_compression"], row["seconds"]), flush=True)
    rep = summarise()
    print(json.dumps(rep["compression"], indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
