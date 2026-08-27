#!/usr/bin/env python3
"""라운드 125 §3·§4 — 무거운 tail 목록 재확인과 **무게-6 461개의 완전 census**.

무게-6 tail 은 지금까지 어느 `F = 1` 칸에서도 하중을 받지 않았다 (`(4,1)`·`(3,1)`·`(2,1)`
전부 `H ≤ 2`).  일반 `(1,1)` 은 `H = 3` 을 허용하고 `[6]` 조성이 실제로 살아남으므로
(라운드 125 §1 표), 무게-6 을 **와일드카드로 두지 않고** 무게-4/5 와 같은 기준으로
전부 분류한다.

각 tail `f` 와 각 `ell = 0..5` 에 대해 720개 단어 전부에서:

  * 궤도 내부인가 (그렇다면 phase 이동은 얼마인가)
  * 원천/표적 육각형이 같은가
  * 원천/표적 궤도의 육각형 겹침 크기 분포
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f1_k2_budget_121 import (  # noqa: E402
    WORDS, IDX, HEXID, ORBID, ORBPH, HEXOF_ORB, indecomposable, tails, omega, sigk)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


def catalogue():
    """550 tail 목록의 무게별 분포를 다시 센다."""
    counts = {w: len(indecomposable(w)) for w in range(1, 7)}
    return dict(counts_by_weight=counts, total=sum(counts.values()),
                expected=[1, 1, 3, 13, 71, 461], expected_total=550,
                matches=(list(counts.values()) == [1, 1, 3, 13, 71, 461]))


def realized_weight(a):
    """이 index action 이 720개 단어 **전부**에서 실제로 내는 이음매 무게."""
    f = lambda q: tuple(q[j] for j in a)
    ws = {omega(y, f(y)) for y in WORDS}
    assert len(ws) == 1, (a, sorted(ws))     # 글자가 전부 다르므로 언제나 all-or-nothing
    return ws.pop()


def w6_split():
    """### 라운드 125 정정 — 무게-6 목록은 **퇴화한다**.

    `w < 6` 이면 action 이 `z[:6-w] = y[w:]` 를 강제하므로 `omega = w` 가 **항상** 성립한다
    (실측: 13/13, 71/71).  그런데 `w = 6` 은 강제 접두가 **비어 있어서** `z = y∘pi` 이고,
    `pi` 가 `{0..5}` 에서 분해불가여도 `omega(y,z) < 6` 일 수 있다.

    `omega(y,z) = k < 6` 은 `pi(i) = k+i  (i <= 5-k)` 와 동치이고, 그러면 `pi` 의 마지막
    `k` 자리가 정의하는 안쪽 순열 `sigma` 에는 `pi` 의 분해불가성이 **아무 제약도 주지 않는다**
    (실측: `k! = 1,2,6,24,120` 개가 전부 나타난다).  따라서 461 개는 셋으로 갈린다.

      * **308 개** — `omega = 6` 인 **진짜** 무게-6 이음매.
      * **89 개** — `sigma` 가 분해불가라 실제로는 더 가벼운 **진짜** 이음매다.
        `1+1+3+13+71 = 89` 로 `w <= 5` 목록과 **정확히 일치**하고, 같은 `y` 에서 같은 `z` 를
        낸다.  가벼운 목록이 이미 올바른 비용으로 제공하므로 무게-6 목록에서 빼도 잃는 것이 없다.
      * **64 개** — `sigma` 가 분해가능해서 12글자 창 안에 **중간 순열이 들어간다**.
        단일 이음매가 아니라 pass 두 개다.  `k! - indec(k)` 로 `1+3+11+49 = 64`.

    엔진은 **308 개만** 제공한다.  거짓 기각은 0 이다(진짜 무게-6 이음매를 하나도 잃지 않는다).
    """
    indec = {k: set(indecomposable(k)) for k in range(1, 6)}
    gen, light, illegal = [], [], []
    for i, a in enumerate(tails(6)):
        k = realized_weight(a)
        if k == 6:
            gen.append(i)
            continue
        inner = tuple(a[6 - k + j] for j in range(k))
        (light if inner in indec[k] else illegal).append(dict(index=i, omega=k, inner=list(inner)))
    return dict(
        n_actions=461, n_genuine_weight6=len(gen),
        n_lighter_duplicates=len(light), n_illegal_non_joints=len(illegal),
        genuine_indices=gen,
        lighter_by_omega={str(k): sum(1 for r in light if r["omega"] == k) for k in range(1, 6)},
        illegal_by_omega={str(k): sum(1 for r in illegal if r["omega"] == k) for k in range(1, 6)},
        lighter_matches_w5_catalogue=(
            [sum(1 for r in light if r["omega"] == k) for k in range(1, 6)]
            == [len(indecomposable(k)) for k in range(1, 6)]),
        illegal_matches_factorial_minus_indec=(
            [sum(1 for r in illegal if r["omega"] == k) for k in range(1, 6)]
            == [__import__("math").factorial(k) - len(indecomposable(k)) for k in range(1, 6)]),
        w_lt_6_never_degenerates={str(w): (sorted({realized_weight(a) for a in tails(w)}) == [w])
                                  for w in range(2, 6)},
        engine_offers=len(gen),
        false_rejection="0 - no genuine weight-6 joint is dropped",
        affects_round_123="root counts for H = 3 cells are OVER-counts (superset); the "
                          "completeness claim is unaffected because a superset is still complete",
        affects_round_124="no - every Round-124 subfamily had H <= 2, so hub <= 2 and no "
                          "weight-6 tail was ever offered")


def census(w):
    """무게 w tail 을 전부 분류한다."""
    acts = tails(w)
    rows = []
    for i, a in enumerate(acts):
        f = lambda q, a=a: tuple(q[j] for j in a)
        wt = {omega(y, f(y)) for y in WORDS}
        intra, samehex, phase, overlap = {}, {}, {}, {}
        for ell in range(6):
            s = h = 0
            ph, ov = Counter(), Counter()
            for u in WORDS:
                y = sigk(u, ell)
                z = f(y)
                iu, iz = IDX[u], IDX[z]
                if ORBID[iz] == ORBID[iu]:
                    s += 1
                    ph[(ORBPH[iz] - ORBPH[iu]) % 5] += 1
                if HEXID[iz] == HEXID[iu]:
                    h += 1
                ov[len(HEXOF_ORB[ORBID[iu]] & HEXOF_ORB[ORBID[iz]])] += 1
            intra[ell] = s
            samehex[ell] = h
            phase[ell] = {str(k): v for k, v in sorted(ph.items())}
            overlap[ell] = {str(k): v for k, v in sorted(ov.items())}
        rows.append(dict(name=f"W{w}_{i}", action=list(a), weights_observed=sorted(wt),
                         intra_orbit=intra, same_hexagon=samehex,
                         phase_shift_when_intra=phase,
                         source_target_hexagon_overlap=overlap))
    return rows


def classify(rows):
    """같은 (intra, samehex, overlap) 프로필을 가진 tail 을 하나의 클래스로 묶는다."""
    classes = {}
    for r in rows:
        key = (tuple(r["intra_orbit"][e] for e in range(6)),
               tuple(r["same_hexagon"][e] for e in range(6)),
               tuple(tuple(sorted(r["source_target_hexagon_overlap"][e].items()))
                     for e in range(6)),
               tuple(tuple(sorted(r["phase_shift_when_intra"][e].items()))
                     for e in range(6)))
        classes.setdefault(key, []).append(r["name"])
    out = []
    for key, names in sorted(classes.items(), key=lambda kv: (-len(kv[1]), kv[1][0])):
        intra, samehex, overlap, phase = key
        out.append(dict(size=len(names), members=names[:6],
                        truncated=len(names) > 6,
                        intra_orbit=list(intra), same_hexagon=list(samehex),
                        overlap_by_ell=[dict(o) for o in overlap],
                        phase_by_ell=[dict(p) for p in phase]))
    return out


def summarise(weights=(4, 5, 6)):
    split = w6_split()
    keep6 = set(split["genuine_indices"])
    rep = dict(round=125, catalogue=catalogue(), weight6_degeneracy=split, by_weight={})
    for w in weights:
        allrows = census(w)
        if w == 6:      # 진짜 무게-6 이음매 308개만 census 한다 (§4 정정)
            allrows = [r for i, r in enumerate(allrows) if i in keep6]
        rows = classify(allrows)
        # 궤도 내부가 될 수 있는 tail (720/720 전부, 부분은 없어야 한다)
        intra_any, partial = [], []
        for r in allrows:
            for ell in range(6):
                n = r["intra_orbit"][ell]
                if n == 720:
                    intra_any.append((r["name"], ell,
                                      list(r["phase_shift_when_intra"][ell])))
                elif n:
                    partial.append((r["name"], ell, n))
        never_same_hex = all(r["same_hexagon"][e] == 0 for r in allrows for e in range(6))
        rep["by_weight"][str(w)] = dict(
            n_tails=len(allrows), n_classes=len(rows), classes=rows,
            intra_orbit_all_720=[dict(tail=t, ell=e, phase_shift=p)
                                 for (t, e, p) in intra_any],
            partially_intra_orbit=partial,
            all_or_nothing=(partial == []),
            never_returns_to_source_hexagon=never_same_hex,
            overlap_distribution_at_ell5=Counter(
                tuple(sorted(r["source_target_hexagon_overlap"][5].items()))
                for r in allrows).most_common())
    rep["label"] = "ROUND-125 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED"
    rep["disclaimer"] = "This project has not proved L6 >= 872."
    return rep


if __name__ == "__main__":
    r = summarise()
    print(json.dumps(r["catalogue"], indent=1))
    print(json.dumps({k: v for k, v in r["weight6_degeneracy"].items()
                      if k != "genuine_indices"}, indent=1))
    for w, d in r["by_weight"].items():
        print(f"--- weight {w}: {d['n_tails']} tails, {d['n_classes']} classes, "
              f"all_or_nothing={d['all_or_nothing']}, "
              f"never_same_hex={d['never_returns_to_source_hexagon']}")
        print("   intra-orbit (720/720):", d["intra_orbit_all_720"])
        print("   overlap dist at ell=5:", d["overlap_distribution_at_ell5"])
