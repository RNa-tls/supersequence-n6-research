#!/usr/bin/env python3
"""라운드 125 §1·§2·§11·§12·§15 — 일반 `(k,F) = (1,1)` 자원 표를 **처음부터** 다시 만든다.

라운드 122 의 행/하위경우 수를 **상속하지 않는다.** 전부 다시 센다.

    F = 1, k = 1  ⇒  P = 121, O = 25, D = 5O − P = 4
    L = 844 + F + S + H = 845 + S + H
    r = O + e = 25 + e          (run 개수)
    S = (r − 1) + x − f_out = 24 + e + x − f_out
    N = S + F − O = S − 24 = e + x − f_out
    L = 869 + N + H
    L ≤ 871  ⟺  N + H ≤ 2  ⟺  e + x + H − f_out ≤ 2

보조정리 E: `f_out ≤ 1 + e`.  그리고 `f_out ≤ 2` (짧은 pass 가 둘뿐).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

# 라운드 115 사슬 용량표 (run 결손 s 하나짜리 all-light 사슬의 최대 pass 수)
NTAB = [20, 20, 33, 33, 46, 46, 49, 58, 62, 66, 70, 74, 83, 83, 96, 96, 96,
        103, 103, 103, 103, 120, 120, 120, 120]

K, F = 1, 1
O, P = 24 + K, 120 + F
D = 5 * O - P
LCAP = 871


def bestseg_table(mmax):
    """BESTSEG[m][s] = m 개 조각에 결손 s 를 나눠 줄 때의 최대 pass 수."""
    B = [[0] * len(NTAB) for _ in range(mmax + 1)]
    for m in range(1, mmax + 1):
        for s in range(len(NTAB)):
            B[m][s] = max(NTAB[a] + B[m - 1][s - a] for a in range(s + 1))
    return B


def heavy_compositions(H):
    """H = Σ (w−3)₊ 를 만드는 무거운 이음매 무게 다중집합 전부.

    한 이음매의 기여는 `p = w − 3 ∈ {1,2,3}` (무게 4/5/6).  무게 ≥ 7 은 없다."""
    out = []

    def rec(rem, mx, cur):
        if rem == 0:
            out.append(tuple(cur))
            return
        for p in range(min(rem, mx), 0, -1):
            rec(rem - p, p, cur + [p])

    rec(H, 3, [])
    return [tuple(3 + p for p in c) for c in out]


def rows():
    """`(e, x, f_out, H)` 의 모든 실현 가능한 정수 행 (숨은 여유 없음)."""
    B = bestseg_table(16)
    out = []
    for e in range(0, 9):
        for x in range(0, 9):
            for f in range(0, 3):
                for H in range(0, 9):
                    if f > 1 + e:                       # Lemma E
                        continue
                    N = e + x - f
                    if N + H > LCAP - 869:              # L = 869 + N + H <= 871
                        continue
                    S = 24 + N
                    if S < 0:
                        continue
                    r = O + e
                    shortfall = 5 * r - P               # = D + 5e = 4 + 5e
                    assert shortfall == D + 5 * e
                    for comp in heavy_compositions(H):
                        h = len(comp)
                        # 사슬을 끊는 사건: 짧은 pass 2개 + x + e + 무거운 이음매 h 개
                        breaks = 2 + x + e + h
                        m = breaks + 1
                        cap = B[min(m, 16)][min(shortfall, len(NTAB) - 1)]
                        out.append(dict(
                            e=e, x=x, f_out=f, H=H, N=N, S=S, r=r, t=h + 1,
                            heavy_weights=list(comp), n_heavy=h,
                            run_shortfall=shortfall, breaks=breaks, segments=m,
                            segment_capacity=cap, dead_by_capacity=cap < P))
    return out


def summarise():
    rs = rows()
    distinct = sorted({(r["e"], r["x"], r["f_out"], r["H"]) for r in rs})
    alive = [r for r in rs if not r["dead_by_capacity"]]
    dead = [r for r in rs if r["dead_by_capacity"]]
    alive_rows = sorted({(r["e"], r["x"], r["f_out"], r["H"]) for r in alive})
    byH = {}
    for r in rs:
        byH.setdefault(r["H"], []).append(r)
    negN = sorted({(r["e"], r["x"], r["f_out"], r["H"], r["N"]) for r in rs if r["N"] < 0})
    return dict(
        round=125, cell=[K, F], P=P, O=O, D=D,
        identities=dict(
            L="844 + F + S + H = 845 + S + H",
            S="(r - 1) + x - f_out with r = O + e = 25 + e, so S = 24 + e + x - f_out",
            N="S + F - O = S - 24 = e + x - f_out",
            L_in_N="869 + N + H",
            core="L <= 871  <=>  N + H <= 2  <=>  e + x + H - f_out <= 2",
            lemma_E="f_out <= 1 + e",
            f_out_cap="f_out <= 2 (there are only two short passes)",
            run_shortfall="5r - P = D + 5e = 4 + 5e"),
        n_resource_rows=len(distinct),
        n_subcases=len(rs),
        n_subcases_dead_by_capacity=len(dead),
        n_subcases_alive=len(alive),
        n_rows_with_a_live_subcase=len(alive_rows),
        resource_rows=[dict(e=e, x=x, f_out=f, H=H) for (e, x, f, H) in distinct],
        H_classification={
            str(H): dict(
                compositions=[list(c) for c in heavy_compositions(H)],
                n_compositions=len(heavy_compositions(H)),
                n_rows=len({(r["e"], r["x"], r["f_out"]) for r in byH.get(H, [])}),
                n_subcases=len(byH.get(H, [])),
                n_alive=len([r for r in byH.get(H, []) if not r["dead_by_capacity"]]),
                rows=sorted({(r["e"], r["x"], r["f_out"]) for r in byH.get(H, [])}))
            for H in sorted(byH)},
        max_H=max(byH),
        max_e=max(r["e"] for r in rs), max_x=max(r["x"] for r in rs),
        negative_N=dict(
            rows=[dict(e=e, x=x, f_out=f, H=H, N=n) for (e, x, f, H, n) in negN],
            min_N=min((r["N"] for r in rs), default=0),
            note=("N < 0 requires f_out > e + x, and f_out <= 1 + e, so f_out >= 1 and "
                  "x = 0 and e <= f_out - 1")),
        dead_subcases=[dict(e=r["e"], x=r["x"], f_out=r["f_out"], H=r["H"],
                            heavy_weights=r["heavy_weights"], segments=r["segments"],
                            segment_capacity=r["segment_capacity"]) for r in dead],
        alive_subcases=[dict(e=r["e"], x=r["x"], f_out=r["f_out"], H=r["H"],
                             heavy_weights=r["heavy_weights"], segments=r["segments"],
                             segment_capacity=r["segment_capacity"],
                             run_shortfall=r["run_shortfall"]) for r in alive],
        capacity_model=dict(
            NTAB=NTAB,
            bestseg_at_shortfall_4=[bestseg_table(16)[m][4] for m in range(0, 17)],
            bestseg_at_shortfall_9=[bestseg_table(16)[m][9] for m in range(0, 17)],
            explanation=("a walk with `breaks` chain-breaking events splits into "
                         "breaks + 1 all-light segments; each segment obeys the Round-115 "
                         "capacity NTAB[s] for its share s of the run shortfall, so the "
                         "whole walk holds at most BESTSEG[m][shortfall] passes, and the "
                         "subcase is impossible when that is < P = 121")),
        label="ROUND-125 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED",
        disclaimer="This project has not proved L6 >= 872.")


if __name__ == "__main__":
    r = summarise()
    print(json.dumps({k: v for k, v in r.items()
                      if k not in ("dead_subcases", "alive_subcases", "resource_rows")},
                     indent=1, ensure_ascii=False))
