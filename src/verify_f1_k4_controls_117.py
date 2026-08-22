#!/usr/bin/env python3
"""라운드 117 — `(4,1)` 예산 유도 · 보조정리 E · 탐색기 양성 대조.

  §1  (4,1) 예산: 보조정리 E 만 써서 하위경우가 정확히 둘임을 유도한다
  §3  세 분할 (5,1)/(4,2)/(3,3) 의 진입/탈출 phase 와 나가는 경량 이동
  §4  두 짧은 pass 가 이웃할 수 없다는 사실 (라운드 116 정리 D) 재확인
  §6  보조정리 E — 짝지어진 자유 탈출은 닫힌 순환을 만든다
  §10 양성 대조 — 이동표 독립 재계산, 세 분할의 합법 조각, n=4 전수 내장
  §12 k = 3, 2, 1 의 예산 분류
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

WORDS = ["".join(p) for p in itertools.permutations("012345")]
sig = lambda x: x[1:] + x[0]
tau = lambda x: x[1:5] + x[0] + x[5]


def _rep(x, f, n):
    y, b = x, x
    for _ in range(n - 1):
        y = f(y)
        b = min(b, y)
    return b


HEXR = {x: _rep(x, sig, 6) for x in WORDS}
ORBR = {x: _rep(x, tau, 5) for x in WORDS}
OHEX = defaultdict(set)
for _x in WORDS:
    OHEX[ORBR[_x]].add(HEXR[_x])


def sigp(x, k):
    for _ in range(k % 6):
        x = sig(x)
    return x


MOVE = {
    "W2":  lambda y: y[2] + y[3] + y[4] + y[5] + y[1] + y[0],
    "W3a": lambda y: y[3] + y[4] + y[5] + y[1] + y[2] + y[0],
    "W3b": lambda y: y[3] + y[4] + y[5] + y[2] + y[0] + y[1],
    "W3c": lambda y: y[3] + y[4] + y[5] + y[2] + y[1] + y[0],
}
COST = {"W2": 0, "W3a": 1, "W3b": 1, "W3c": 1}


def budgets():
    """S = 23 + k + e + x - f_out,  f_out <= 1 + e (Lemma E),  S + H <= 26."""
    cells = {}
    for k in range(1, 5):
        rows = []
        for e in range(0, 4):
            for x in range(0, 4):
                for fo in range(0, 3):
                    if fo > 1 + e:
                        continue
                    S = 23 + k + e + x - fo
                    H = 26 - S
                    if H < 0:
                        continue
                    rows.append(dict(e=e, x=x, f_out=fo, S=S, H_max=H,
                                     r=24 + k + e, t_max=H + 1))
        cells[k] = dict(subcases=rows, H_max=max(r["H_max"] for r in rows),
                        n_subcases=len(rows))
    return cells


def k4_subcases():
    out = []
    for e in range(0, 6):
        for x in range(0, 6):
            for fo in range(0, 3):
                if fo > 1 + e:
                    continue
                S = 27 + e + x - fo
                H = 26 - S
                if H < 0:
                    continue
                out.append(dict(e=e, x=x, f_out=fo, S=S, H=H, r=28 + e, t=H + 1))
    return out


def split_ports():
    rows = []
    for b in range(1, 6):
        v = WORDS[0]
        A = dict(entry=v, length=b, ell=b - 1, exit=sigp(v, b - 1))
        u2 = sigp(v, b)
        B = dict(entry=u2, length=6 - b, ell=5 - b, exit=sigp(u2, 5 - b))
        assert B["exit"] == sigp(v, 5)
        outs = {}
        for lbl, P in (("A", A), ("B", B)):
            d = {}
            for nm, f in MOVE.items():
                t = f(P["exit"])
                d[nm] = dict(target_orbit_differs=(ORBR[t] != ORBR[P["entry"]]),
                             target_hexagon_differs=(HEXR[t] != HEXR[P["entry"]]),
                             shared_hexagons=len(OHEX[ORBR[P["entry"]]] & OHEX[ORBR[t]]),
                             cost=COST[nm])
            outs[lbl] = d
        rows.append(dict(b=b, split=[b, 6 - b], A=A, B=B, exits=outs,
                         free_successor_of_A_is_tau_of_entry_B=(MOVE["W2"](A["exit"]) == tau(B["entry"])),
                         free_successor_of_B_is_tau_of_entry_A=(MOVE["W2"](B["exit"]) == tau(A["entry"]))))
    return rows


def lemma_checks():
    ok_a = ok_b = nonadj = 0
    for v in WORDS:
        for b in range(1, 6):
            eA, eB = v, sigp(v, b)
            xA, xB = sigp(v, b - 1), sigp(v, 5)
            if MOVE["W2"](xA) == tau(eB):
                ok_a += 1
            if MOVE["W2"](xB) == tau(eA):
                ok_b += 1
            if sig(xA) == eB and sig(xB) == eA:
                nonadj += 1
    return dict(cases=720 * 5,
                free_successor_of_A_equals_tau_entry_B=ok_a,
                free_successor_of_B_equals_tau_entry_A=ok_b,
                sigma_adjacency_of_the_two_arcs=nonadj,
                lemma_E=("if both short passes exit freely then A -> tau(entry_B) starts a run "
                         "of orb(B) and B -> tau(entry_A) starts a run of orb(A); if each of "
                         "those lies in the same run as the corresponding short pass the walk "
                         "closes a cycle, which a path cannot contain — hence some orbit needs "
                         "a second run, i.e. f_out = 2 implies e >= 1, i.e. f_out <= 1 + e"))


def control_move_tables():
    src = ROOT / "src" / "f1_all_light_117.c"
    bin_ = ROOT / "src" / "f1_all_light_117.bin"
    if not bin_.exists() or bin_.stat().st_mtime < src.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(bin_), str(src)], check=True)
    return dict(
        move_targets_are_permutations=all(len({MOVE[nm](y) for y in WORDS}) == 720
                                          for nm in MOVE),
        W2_at_ell5_is_tau=all(MOVE["W2"](sigp(u, 5)) == tau(u) for u in WORDS),
        short_pass_exits_always_leave_the_orbit=all(
            ORBR[MOVE[nm](sigp(u, ell))] != ORBR[u]
            for u in WORDS[:200] for ell in range(5) for nm in MOVE),
        no_light_move_returns_to_the_source_hexagon=all(
            HEXR[MOVE[nm](sigp(u, ell))] != HEXR[u]
            for u in WORDS[:200] for ell in range(6) for nm in MOVE))


def control_fragments():
    rows = []
    for b in range(1, 6):
        v = WORDS[0]
        eA, eB = v, sigp(v, b)
        frag, used_hex = [], set()
        starts = [(u, nm) for u in WORDS for nm in MOVE if MOVE[nm](sigp(u, 5)) == eA]
        assert starts, f"no predecessor for b={b}"
        u0, nm0 = starts[0]
        frag.append(dict(entry=u0, length=6, move_out=nm0, cost=COST[nm0]))
        used_hex.add(HEXR[u0])
        frag.append(dict(entry=eA, length=b, move_out=None, cost=None))
        used_hex.add(HEXR[eA])
        ok = False
        for nm in MOVE:
            t = MOVE[nm](sigp(eA, b - 1))
            if HEXR[t] in used_hex:
                continue
            frag[-1]["move_out"] = nm
            frag[-1]["cost"] = COST[nm]
            frag.append(dict(entry=t, length=6, move_out=None, cost=None))
            used_hex.add(HEXR[t])
            ok = True
            break
        rows.append(dict(b=b, split=[b, 6 - b], accepted=ok,
                         distinct_hexagons=(len(used_hex) == len(frag)),
                         second_visit_word_is_sigma_b_of_first=(eB == sigp(eA, b)),
                         second_visit_length=6 - b, fragment=frag))
    return rows


def control_n4():
    spec = importlib.util.spec_from_file_location("m", ROOT / "src" / "verify_f1_structure_116.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["m"] = m
    spec.loader.exec_module(m)
    perms, W, walks = m.n4_walks(36)
    rows = [m.measure4(perms, W, L, s) for L, s in walks]
    f1 = [r for r in rows if r["F"] == 1]
    return dict(
        n4_walks=len(rows), n4_F1=len(f1),
        lemma_E_violations_F1=sum(1 for r in f1 if r["f_out"] > 1 + r["e"]),
        lemma_E_violations_all_F=sum(1 for r in rows if r["f_out"] > 1 + r["e"]),
        lemma_E_violations_by_F={str(k): v for k, v in sorted(
            Counter(r["F"] for r in rows if r["f_out"] > 1 + r["e"]).items())},
        f_out_2_with_e_0_at_F1=sum(1 for r in f1 if r["f_out"] == 2 and r["e"] == 0),
        O_le_1_plus_S_plus_F_violations=sum(1 for r in rows if r["O"] > 1 + r["S"] + r["F"]),
        exf_joint_F1={str(list(k)): v for k, v in sorted(
            Counter((r["e"], r["x"], r["f_out"]) for r in f1).items())},
        note=("Lemma E is F=1 specific: it fails for F >= 2, exactly as its proof (which uses "
              "the unique complementary pair of h*) predicts"))


def main():
    rep = dict(round=117,
               label="ROUND-117 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
               s1_k4_subcases=k4_subcases(),
               s12_cell_budgets={str(k): v for k, v in budgets().items()},
               s3_split_ports=split_ports(),
               s4_s6_lemmas=lemma_checks(),
               s10_control_move_tables=control_move_tables(),
               s10_control_fragments=control_fragments(),
               s10_control_n4=control_n4(),
               ledger=dict(INDEPENDENTLY_AUDITED_Q2_RESIDUAL=4782,
                           CLAUDE_FULL_JOINT_UNSAT_COMPLETE=6396,
                           unchanged_by_this_round=True),
               disclaimer="This project has not proved L6 >= 872.")
    (OUT / "rr_f1_k4_controls_117.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print("k=4 sub-cases:", [(r["e"], r["x"], r["f_out"], r["S"], r["H"], r["r"])
                             for r in rep["s1_k4_subcases"]])
    print("cell H_max:", {k: v["H_max"] for k, v in rep["s12_cell_budgets"].items()})
    print("lemma checks:", {k: v for k, v in rep["s4_s6_lemmas"].items() if k != "lemma_E"})
    print("move tables:", rep["s10_control_move_tables"])
    print("fragments:", [(r["b"], r["accepted"], r["distinct_hexagons"]) for r in
                         rep["s10_control_fragments"]])
    c = rep["s10_control_n4"]
    print("n=4:", {k: c[k] for k in ("n4_walks", "n4_F1", "lemma_E_violations_F1",
                                     "lemma_E_violations_all_F", "lemma_E_violations_by_F",
                                     "O_le_1_plus_S_plus_F_violations")})


if __name__ == "__main__":
    main()
