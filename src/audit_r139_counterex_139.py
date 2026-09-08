#!/usr/bin/env python3
"""라운드 139 감사 §24 — 적극적 반례 탐색 (유한/지역 탐색만).

A. 외부 후계자가 틀린 합법 splice
B. 마스터 계수가 부과하지 않는 공유 궤도
C. 한 사건이 두 번 세어지는 두-결함 배치
D. 분류에서 빠진 H=2 구조
E. splice 정규형 밖의 Type-A 세 겹 진입
F. 지역 규칙을 다 만족하지만 38 봉투에 없는 k=1 배치
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from itertools import combinations_with_replacement, permutations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f2_structure_126 import setup                        # noqa: E402
from audit_r139_rows_139 import rows, heavy_multisets            # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def A_wrong_successor(ns=(4, 5, 6, 7)):
    """`sigma^(n-1)(sigma^l(v)) != sigma^(l-1)(v)` 인 `(n,v,l)` 을 찾는다.

    n=7 까지 넓혀도 반례가 없어야 한다 (항등식은 `sigma^n = id` 뿐이므로 자명).
    """
    bad, tot = [], 0
    for n in ns:
        g = setup(n)
        P, IDX, SGf = g["perms"], g["idx"], g["sig"]

        def sg(w, t):
            for _ in range(t):
                w = IDX[SGf(P[w])]
            return w
        for v in range(len(P)):
            for l in range(1, n + 1):
                tot += 1
                if sg(sg(v, l), n - 1) != sg(v, l - 1):
                    bad.append((n, v, l))
    return dict(checked=tot, counterexamples=bad[:5], found=len(bad),
                refuted=(len(bad) > 0),
                note="n=7 까지 확장; 항등식은 sigma^n = id 만 쓴다")


def B_uncharged_shared_orbit(controls_json):
    """조각별 궤도 집합에서 **내가 직접** `s` 를 세어 기록된 `s` 와 비교."""
    import audit_r139_controls_139 as C
    data = json.loads(Path(controls_json).read_text())
    bad, checked = [], 0
    for ctl in data["controls"]:
        n = ctl["n"]
        g = C.geo(n)
        ORB = g["orbid"]
        r = C.analyse_control(ctl["word"], n)
        if not r["ok"]:
            continue
        p = C.parse(ctl["word"], n)
        entry = [q[0] for q in p["passes"]]
        # 조각 = Astra 가 준 pass 인덱스 묶음 (데이터), 궤도 계산은 내 것
        orbsets = [{ORB[entry[i]] for i in pc["indices"]} for pc in ctl["pieces"]]
        union = set().union(*orbsets) if orbsets else set()
        s_mine = sum(len(o) for o in orbsets) - len(union)
        # O' = O - c 도 독립 확인 (순수 자유 순환 제거가 궤도 하나씩 없앤다)
        O_all = len({ORB[e] for e in entry})
        checked += 1
        if s_mine != ctl["s"]:
            bad.append(dict(word=ctl["word"][:24], mine=s_mine, recorded=ctl["s"]))
        if len(union) != O_all - r["c"]:
            bad.append(dict(word=ctl["word"][:24], why="O' != O - c",
                            union=len(union), O=O_all, c=r["c"]))
        # 조각별 O_j 도 내가 다시 세어 기록과 대조
        for pc, oset in zip(ctl["pieces"], orbsets):
            if pc["metrics"]["O"] != len(oset):
                bad.append(dict(word=ctl["word"][:24], why="piece O mismatch",
                                mine=len(oset), recorded=pc["metrics"]["O"]))
    return dict(checked=checked, mismatches=len(bad), examples=bad[:5],
                refuted=(len(bad) > 0),
                note="s = sum_j |orbits(piece j)| - |union| 를 내가 직접 계산")


def C_double_counted_defect():
    """`delta = F + e - f_out` 이 어떤 자원 상태에서도 깨지지 않는가."""
    bad = []
    seen = set()
    for k in (1, 2, 3, 4):
        for r in rows(k) if k <= 2 else []:
            seen.add((r["F"], r["e"], r["f_out"], r["delta"]))
    # 자원 행에 얽매이지 않고 typed 분해 (a, eta) 도 확인: delta = a + eta
    typed = []
    for delta in range(0, 4):
        parts = [(a, delta - a) for a in range(delta + 1)]
        typed.append(dict(delta=delta, decompositions=parts,
                          count=len(parts), sums_ok=all(a + e == delta
                                                        for a, e in parts)))
    return dict(states=len(seen),
                identity_holds=all(d == F + e - f for (F, e, f, d) in seen),
                typed_decompositions=typed,
                all_typed_sums_ok=all(t["sums_ok"] for t in typed),
                refuted=not all(d == F + e - f for (F, e, f, d) in seen),
                note=("delta 는 (F,e,f_out) 의 함수이고 (a,eta) 분해는 delta 를 "
                      "보존한다; 유료 상승 재진입이 같은 조인트에서 a 하나와 eta "
                      "하나를 내더라도 합은 여전히 delta 다"))


def D_missing_H2(wmax=9):
    """`H = sum(w-3) = 2` 를 주는 heavy multiset 을 전수 열거."""
    found = []
    for h in range(1, 5):
        for ws in combinations_with_replacement(range(4, wmax + 1), h):
            if sum(w - 3 for w in ws) == 2:
                found.append(list(ws))
    astra = [[5], [4, 4]]
    return dict(weight_range=f"4..{wmax}", multisets=found,
                astra_classification=astra,
                complete=(sorted(found) == sorted(astra)),
                refuted=(sorted(found) != sorted(astra)),
                note=("H=2 는 (w-3) 합이 2 이므로 w=5 하나이거나 w=4 둘뿐. "
                      "w>=7 은 H<=3 에서 애초에 불가능"))


def E_typeA_outside_normal_form():
    """Type A 의 `nu` 는 3 원소 위의 3-순환.  그런 순열이 정확히 둘인가."""
    threecycles = []
    for p in permutations(range(3)):
        if all(p[i] != i for i in range(3)):
            # 고정점 없는 3 원소 순열 = 3-순환
            threecycles.append(list(p))
    # 두 겹 육각형 넷의 matching 도 확인
    matchings = []
    for p in permutations(range(4)):
        if all(p[i] != i for i in range(4)) and all(p[p[i]] == i for i in range(4)):
            m = tuple(sorted(tuple(sorted((i, p[i]))) for i in range(4)))
            if m not in matchings:
                matchings.append(m)
    return dict(type_A_three_cycles=threecycles, count_A=len(threecycles),
                type_B_matchings=[list(map(list, m)) for m in matchings],
                count_B=len(matchings),
                total_support_cases=len(threecycles) + len(matchings),
                astra_five=(len(threecycles) + len(matchings) == 5),
                G2_partition_argument=("G = sum_h (m_h - 1) = 2 이므로 "
                                       "한 육각형이 m=3 (3-순환) 이거나 "
                                       "두 육각형이 m=2 (2-순환 둘) 뿐"),
                refuted=(len(threecycles) + len(matchings) != 5))


def F_k1_outside_envelopes(envelope_rows):
    """k=1 의 모든 자원 행이 38 봉투 중 하나에 실제로 들어가는가."""
    env = set()
    for r in envelope_rows:
        env.add((r["k"], r["c"], r["H"], tuple(sorted(r["heavy"])), r["s"], r["b"]))
    escaped, checked = [], 0
    for k in (1, 2):
        for r in rows(k):
            for c in (0, 1, 2):
                for hv in heavy_multisets(r["H"]):
                    lhs = r["delta"] - r["F"] + r["x"] + c     # = sum b_j + s
                    if lhs < 0:
                        continue
                    checked += 1
                    # Astra 는 예산을 **다 쓴** 봉투만 열거한다 (b = B - s).
                    # 그것이 건전한 이유: 실제 (s_act, b_act) 에 대해 s_env = s_act,
                    # b_env = B - s_act >= b_act 인 봉투가 항상 있고, 용량은 b 에
                    # 대해서도 결손에 대해서도 단조 비감소이므로 그 봉투의 상계가
                    # 실제 배치를 **지배**한다.  따라서 정확 일치가 아니라 지배를 본다.
                    B = 2 - k + c - r["H"]
                    hit = any((k, c, r["H"], tuple(sorted(hv)), s_act, B - s_act) in env
                              for s_act in range(0, lhs + 1) if B - s_act >= 0)
                    if not hit:
                        escaped.append(dict(k=k, c=c, H=r["H"], heavy=hv,
                                            delta=r["delta"], F=r["F"], x=r["x"],
                                            need=lhs))
    return dict(checked=checked, escaped=len(escaped), examples=escaped[:5],
                refuted=(len(escaped) > 0),
                domination_rule="s_env = s_act, b_env = B - s_act >= b_act",
                note=("각 행은 sum b_j+s = delta-F+x+c 를 요구한다; 예산을 다 쓴 "
                      "봉투 (s_act, B-s_act) 가 그 배치를 지배해야 한다"))


if __name__ == "__main__":
    ctlsrc = sys.argv[1]
    env = json.loads(Path(ctlsrc).read_text())["bounds"]["rows"]
    res = dict(
        A_wrong_successor=A_wrong_successor(),
        B_uncharged_shared_orbit=B_uncharged_shared_orbit(ctlsrc),
        C_double_counted_defect=C_double_counted_defect(),
        D_missing_H2=D_missing_H2(),
        E_typeA_outside_normal_form=E_typeA_outside_normal_form(),
        F_k1_outside_envelopes=F_k1_outside_envelopes(env))
    res["any_refuted"] = any(v.get("refuted") for v in res.values()
                             if isinstance(v, dict))
    (ROOT / "outputs" / "rr_r139_counterex_139.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))
