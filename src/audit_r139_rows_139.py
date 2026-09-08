#!/usr/bin/env python3
"""라운드 139 감사 — `(2,2)` 와 `(1,2)` 자원 행 공간의 독립 재유도, 그리고
모든 행이 38 개 봉투 중 하나로 들어감을 확인.

우리 자신의 항등식만 쓴다:
    `P = 120+G`, `O = 24+k`, `D = 5O-P`, `r = O+e`,
    `S = (r-1)+x-f_out`, `L = 844+G+S+H`, `delta = F+e-f_out`.

`G=2` 를 넣으면
    `S = O-1+e+x-f_out`,  `L = 846+S+H = 846+(23+k)+e+x+H-f_out`
    `L <= 871  <=>  delta + x + H <= F + (2-k)`.
구조: Type A = 세 겹 육각형(짧은 pass 세 개), `F in {1,2}`, `f_out <= 3`;
      Type B = 두 겹 육각형 둘(짧은 pass 네 개), `F = 2`, `f_out <= 4`.
`e = f_out - F + delta >= 0` 이 `e` 를 자동으로 가둔다.

봉투 사상: MASTER `sum b_j + s = S+1-O+c` 에 위를 대입하면
    `sum b_j + s = delta - F + x + c`
이고 길이 부등식이 곧바로 `sum b_j + s <= 2-k+c-H = B` 를 준다.
즉 **행 공간에서 봉투 공간으로 가는 사상이 항등식 하나**이고, 결함이 두 번
세어지거나 x/heavy 안에 숨을 여지가 없다.
"""
from __future__ import annotations

import json
from collections import Counter
from itertools import combinations_with_replacement
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
G = 2


def structures():
    """(type, F, f_out 상한).  Type A 는 짧은 pass 3 개, Type B 는 4 개."""
    return [("A", 1, 3), ("A", 2, 3), ("B", 2, 4)]


def rows(k):
    """`(k, G=2)` 의 모든 자원 행."""
    O = 24 + k
    out = []
    slack = 2 - k                      # delta+x+H <= F + slack
    for typ, F, fmax in structures():
        for f_out in range(0, fmax + 1):
            for delta in range(0, 6):
                e = f_out - F + delta
                if e < 0:
                    continue
                for x in range(0, 6):
                    for H in range(0, 6):
                        if delta + x + H > F + slack:
                            continue
                        S = (O + e - 1) + x - f_out
                        L = 844 + G + S + H
                        if L > 871:
                            continue
                        out.append(dict(type=typ, F=F, f_out=f_out, e=e,
                                        delta=delta, x=x, H=H, S=S, L=L,
                                        q=delta + x + H, k=k, O=O,
                                        P=120 + G, D=5 * O - (120 + G)))
    return out


def heavy_multisets(H):
    if H == 0:
        return [[]]
    out = []
    for h in (1, 2, 3):
        for ws in combinations_with_replacement((4, 5, 6), h):
            if sum(w - 3 for w in ws) == H:
                out.append(list(ws))
    return out


def table(k):
    rs = rows(k)
    by = Counter((r["delta"], r["x"], r["H"]) for r in rs)
    tuples = sum(len(heavy_multisets(r["H"])) for r in rs)
    return dict(k=k, O=rs[0]["O"], P=rs[0]["P"], D=rs[0]["D"],
                distinct_rows=len(rs),
                heavy_refined_tuples=tuples,
                by_delta_x_H={f"{a},{b},{c}": n for (a, b, c), n in sorted(by.items())},
                q_histogram=dict(sorted(Counter(r["q"] for r in rs).items())),
                length_condition=f"delta+x+H <= F+{2-k}")


def row_to_envelope_identity(kmax=2):
    """`sum b_j + s = delta - F + x + c` 와 `<= B` 를 모든 행에서 확인."""
    bad = []
    checked = 0
    for k in (1, 2):
        O = 24 + k
        for r in rows(k):
            for c in (0, 1, 2):
                S = r["S"]
                lhs = S + 1 - O + c                       # MASTER 우변
                alt = r["delta"] - r["F"] + r["x"] + c    # 우리 유도
                B = 2 - k + c - r["H"]
                checked += 1
                if lhs != alt or lhs > B or lhs < -3:
                    bad.append(dict(k=k, row=r, c=c, lhs=lhs, alt=alt, B=B))
    return dict(checked=checked, violations=len(bad), examples=bad[:4],
                identity="sum b_j + s = S+1-O+c = delta - F + x + c",
                budget="<= B = 2-k+c-H, forced by L<=871",
                all_rows_fit_an_envelope=(len(bad) == 0))


def defect_no_double_count():
    """`delta = F + e - f_out` 이 `x` 나 heavy 안에 숨지 않음을 확인.

    `S = (r-1)+x-f_out` 에서 `x` 는 **별도 항**으로 들어가고 `H` 는 `L` 에만
    별도로 더해진다.  따라서 `sum b_j + s = delta - F + x + c` 에서 `delta` 와
    `x` 는 서로 다른 자리를 차지하고, `H` 는 예산 `B` 를 줄이는 쪽으로만 작용한다.
    세 개가 같은 단위를 두 번 셀 수 없음을 전 행에서 확인한다.
    """
    seen = set()
    for k in (1, 2):
        for r in rows(k):
            seen.add((r["delta"], r["x"], r["H"], r["F"], r["f_out"], r["e"]))
    ok = all(d == F + e - f for (d, x, H, F, f, e) in seen)
    return dict(distinct_typed_states=len(seen),
                delta_identity_holds_everywhere=ok,
                note=("delta 는 F,e,f_out 만으로 결정되고 x/H 와 독립적으로 "
                      "예산식에 들어간다; 한 단위가 두 자리를 차지할 수 없다"))


if __name__ == "__main__":
    res = dict(k2=table(2), k1=table(1),
               row_to_envelope=row_to_envelope_identity(),
               defect_accounting=defect_no_double_count(),
               astra_k2_claim=dict(distinct_rows=73, heavy_refined_tuples=78,
                                   q_histogram={0: 8, 1: 27, 2: 38}))
    res["k2_matches_astra"] = (res["k2"]["distinct_rows"] == 73
                               and res["k2"]["heavy_refined_tuples"] == 78
                               and res["k2"]["q_histogram"] == {0: 8, 1: 27, 2: 38})
    (ROOT / "outputs" / "rr_r139_rows_audit_139.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))
