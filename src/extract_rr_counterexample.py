#!/usr/bin/env python3
"""라운드 107 §5 — **유출 차수 가설이 왜 필요한가**를 보여 주는 최소 반례를 하나 보존한다.

정리(선형 숲 계수)는 유출 차수 가설 **없이도 참**이다.  가설이 필요한 것은 구현이 쓰는
**계산된 성분 수** `ĉ(R)` 이다: 정점마다 비용-0 후속을 하나만 병합하므로, 후속이 둘 이상인
정점이 있으면 `ĉ(R) > c(R)` 가 되어 하한 `ĉ(R) − 1` 이 참 최소비용을 넘을 수 있다.

이 스크립트는 그런 그래프를 **가장 작은 것부터** 찾아 `outputs/rr_outdegree_counterexample.json`
에 적는다.  라운드 105 는 무작위 42,052 쌍에서 111건을 찾았고, 여기서는 그중 하나를 사람이
손으로 확인할 수 있는 형태로 남긴다.

사용법:
    python3 src/extract_rr_counterexample.py
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "outputs"


def hat_c(out0, rem, cur=None):
    """구현이 세는 성분 수 (정점마다 비용-0 후속을 **하나만** 병합)."""
    idxs = [i for i in range(len(out0)) if rem >> i & 1]
    par = {i: i for i in idxs}

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    for i in idxs:
        t = out0[i] & rem
        if t:
            j = t.bit_length() - 1          # 가장 높은 비트 하나만 본다
            a, b = find(i), find(j)
            if a != b:
                par[a] = b
    return len({find(i) for i in idxs})


def true_c(out0, rem):
    """참 약연결 성분 수 (비용-0 호 **전부**를 병합)."""
    idxs = [i for i in range(len(out0)) if rem >> i & 1]
    par = {i: i for i in idxs}

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    for i in idxs:
        t = out0[i] & rem
        while t:
            low = t & -t
            j = low.bit_length() - 1
            a, b = find(i), find(j)
            if a != b:
                par[a] = b
            t ^= low
    return len({find(i) for i in idxs})


def min_cost1_arcs(out0, out1, r0, r1, m):
    """ROOT 에서 출발해 모든 정점을 정확히 한 번 지나는 경로의 최소 비용-1 호 개수."""
    best = None
    for perm in itertools.permutations(range(m)):
        first = perm[0]
        if r0 >> first & 1:
            cost = 0
        elif r1 >> first & 1:
            cost = 1
        else:
            continue
        ok = True
        for a, b in zip(perm, perm[1:]):
            if out0[a] >> b & 1:
                pass
            elif out1[a] >> b & 1:
                cost += 1
            else:
                ok = False
                break
        if ok and (best is None or cost < best):
            best = cost
    return best


def search(max_m=5):
    """작은 그래프를 전수로 훑어 `ĉ` 기반 하한이 참 최소비용을 넘는 예를 찾는다."""
    for m in range(3, max_m + 1):
        arcs = [(i, j) for i in range(m) for j in range(m) if i != j]
        full = (1 << m) - 1
        for labels in itertools.product((None, 0, 1), repeat=len(arcs)):
            out0 = [0] * m
            out1 = [0] * m
            for (i, j), lab in zip(arcs, labels):
                if lab == 0:
                    out0[i] |= 1 << j
                elif lab == 1:
                    out1[i] |= 1 << j
            if all(t == 0 or t & (t - 1) == 0 for t in out0):
                continue                       # 가설을 만족 — 반례가 될 수 없다
            for r0, r1 in ((1, 0), (0, 1)):    # ROOT 는 정점 0 으로만 들어간다
                star = min_cost1_arcs(out0, out1, r0, r1, m)
                if star is None:
                    continue
                entry_free = bool(r0)
                ch = hat_c(out0, full)
                bound = (ch - 1 if entry_free else ch)
                if bound > star:
                    return {"m": m, "out0": out0, "out1": out1,
                            "root_zero_cost_entry": entry_free,
                            "hat_c": ch, "true_c": true_c(out0, full),
                            "implementation_bound": bound,
                            "true_min_cost1_arcs": star}
    return None


def main() -> None:
    ex = search()
    if ex is None:
        raise SystemExit("반례를 찾지 못했다 — 예상 밖이다")
    ex["arcs_cost0"] = [[i, j] for i in range(ex["m"]) for j in range(ex["m"])
                        if ex["out0"][i] >> j & 1]
    ex["arcs_cost1"] = [[i, j] for i in range(ex["m"]) for j in range(ex["m"])
                        if ex["out1"][i] >> j & 1]
    ex["reading"] = ("선형 숲 정리 자체는 참이다 (true_c 로 세면 하한이 옳다). 구현이 세는 "
                     "hat_c 가 true_c 보다 커져서 하한이 참 최소비용을 넘는다 — 그래서 "
                     "비용-0 유출 차수 <= 1 가설이 필요하다.")
    (OUT / "rr_outdegree_counterexample.json").write_text(
        json.dumps(ex, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(ex, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
