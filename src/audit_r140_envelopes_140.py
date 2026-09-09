#!/usr/bin/env python3
"""라운드 140 감사 — G=3 봉투(capacity envelope) 표의 독립 재구성.

MASTER-G (보고서 §6/§8) 로부터:
    `B = 4-G-k+c-H`  (G=3 이면 `1-k+c-H`)
    `m <= G+1-c+h = 4-c+h`,  `0 <= c <= K-1`,  `K+R <= G+1`,  `K = G+1 (mod 2)`
    `P_req = 120+G-5c = 123-5c`,  `Dsum = 5k-G+5s = 5k-3+5s`
    `s in 0..B` (조각이 하나면 `s=0`),  `b = B-s`
"""
from __future__ import annotations

import json
from collections import Counter
from itertools import combinations_with_replacement
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
G = 3

# 내가 독립 계산한 값 (라운드 138/139 감사 + 이번 라운드).  None = 아직 미계산.
NSTAR = {
    0: {0: 20, 1: 20, 2: 33, 3: 33, 4: 46, 5: 46, 6: 49, 7: 58, 8: 62, 9: 66,
        10: 70, 11: 74, 12: 83, 13: 83},
    1: {0: 35, 1: 35, 2: 48, 3: 48, 4: 61, 5: 61, 6: 64, 7: 73, 8: 77},
    2: {0: 50, 1: 50, 2: 63, 3: 63, 4: 76, 5: 76, 6: 79, 7: 88, 8: 92},
    3: {0: 65, 1: 65, 2: 78, 3: 78},
}
INHERITED = {(1, 13): 98, (0, 18): 103}          # 이전 라운드 값 (출처 기록)


def cap(b, d, missing):
    """`N*(b,0,d)` 상계.  단조성(`d`, `b` 둘 다 비감소)을 써서 보수적으로."""
    tab = NSTAR.get(b, {})
    if d in tab:
        return tab[d]
    known = [dd for dd in tab if dd <= d]
    if known:
        lo = tab[max(known)]
    else:
        lo = None
    for (bb, dd), v in INHERITED.items():
        if bb == b and dd >= d:
            missing.add((b, d, f"uses inherited N*({bb},0,{dd})={v}"))
            return v
    missing.add((b, d, "NO BOUND AVAILABLE"))
    return None


def heavy_multisets(Hmax=3):
    out = [([], 0)]
    for h in (1, 2, 3):
        for ws in combinations_with_replacement((4, 5, 6), h):
            H = sum(w - 3 for w in ws)
            if H <= Hmax:
                out.append((list(ws), H))
    return out


def best_convolution(m, b, dsum, missing):
    """`m` 개 조각에 `b` 토큰과 `dsum` 결손을 나누는 최대 합."""
    best = 0
    def rec(i, bl, dl, acc):
        nonlocal best
        if i == m - 1:
            v = cap(bl, dl, missing)
            if v is not None:
                best = max(best, acc + v)
            return
        for bb in range(bl + 1):
            for dd in range(dl + 1):
                v = cap(bb, dd, missing)
                if v is None:
                    continue
                rec(i + 1, bl - bb, dl - dd, acc + v)
    rec(0, b, dsum, 0)
    return best


def envelopes():
    rows = []
    for K in (2, 4):                       # K = G+1 (mod 2), K+R <= G+1
        for c in range(0, K):              # 0 <= c <= K-1
            for k in (1, 2, 3, 4):
                for heavy, H in heavy_multisets():
                    B = 1 - k + c - H
                    if B < 0:
                        continue
                    h = len(heavy)
                    m = 4 - c + h
                    for s in range(0, B + 1):
                        if m == 1 and s > 0:
                            continue
                        rows.append(dict(K=K, k=k, c=c, H=H, heavy=heavy,
                                         B=B, s=s, b=B - s, max_pieces=m,
                                         D_sum=5 * k - G + 5 * s,
                                         required_passes=123 - 5 * c))
    return rows


def evaluate():
    rows = envelopes()
    missing = set()
    for r in rows:
        bound = best_convolution(r["max_pieces"], r["b"], r["D_sum"], missing)
        r["capacity_bound"] = bound
        r["margin"] = r["required_passes"] - bound if bound else None
        r["closure"] = ("STRICT" if bound and bound < r["required_passes"]
                        else "EQUALITY" if bound == r["required_passes"]
                        else "OPEN")
    return rows, sorted(missing)


if __name__ == "__main__":
    rows, missing = evaluate()
    byk = Counter(r["k"] for r in rows)
    eq = [r for r in rows if r["closure"] == "EQUALITY"]
    op = [r for r in rows if r["closure"] == "OPEN"]
    res = dict(total_envelopes=len(rows), by_k=dict(sorted(byk.items())),
               astra_claims=dict(total=40, by_k={4: 1, 3: 3, 2: 10, 1: 26}),
               matches_40=(len(rows) == 40),
               by_k_matches=(dict(sorted(byk.items())) == {1: 26, 2: 10, 3: 3, 4: 1}),
               strict=sum(1 for r in rows if r["closure"] == "STRICT"),
               equality=len(eq), open=len(op),
               equality_rows=[{kk: r[kk] for kk in
                               ("K", "k", "c", "H", "heavy", "s", "b",
                                "max_pieces", "D_sum", "required_passes",
                                "capacity_bound")} for r in eq],
               open_rows=[{kk: r[kk] for kk in
                           ("K", "k", "c", "H", "heavy", "s", "b", "max_pieces",
                            "D_sum", "required_passes", "capacity_bound")}
                          for r in op],
               capacity_cells_needed_but_not_independently_computed=[
                   list(x) for x in missing],
               rows=rows)
    (ROOT / "outputs" / "rr_r140_envelopes_140.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "rows"},
                     ensure_ascii=False, indent=1)[:3500])
