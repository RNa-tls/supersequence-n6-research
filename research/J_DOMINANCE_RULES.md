# Dominance relation 후보 검증

산출: `src/test_j_dominance_rules.py` -> `outputs/j_reduction_benchmarks.json`.
방법: 9개 seed 주변(depth<=5, seed당 최대 600 raw state)에서 각 후보의
전제를 만족하는 실제 상태쌍을 찾고, 그 쌍의 **실제 1-step legal
continuation signature**(`(weight, new_orbit, ell)` 집합)를 비교했다.
반례를 찾으면 즉시 반증, 못 찾으면 미결정으로만 표시했다(안전하다고
선언하지 않는다).

## 결과

| 후보 | 판정 | 근거 |
|---|---|---|
| A. Superset-visited dominance | **미결정** | 이 pool(6,045개 상태)에서 전제를 만족하는 쌍을 찾지 못함 |
| B. Lower-Φ dominance | **반증됨** | 반례 있음(아래) |
| C. Fewer-unused-orbit dominance | **반증됨** | 반례 있음(아래) |
| D. Phase-mask containment dominance | **미결정** | 전제를 만족하는 쌍을 찾지 못함 |
| E. Same-boundary, larger-used-resource dominance | **미결정** | 전제를 만족하는 쌍을 찾지 못함 |

## B, C 반례

같은 endpoint, 같은 `P`를 가지지만 서로 다른 `Φ`(0과 4)를 가진 두
실제 상태(우연히도 9개 seed 중 둘, `45929408...`과 `c652843b...`)를
비교했다:

- `Φ=0` 상태: 1-step signature = `{(2,false,5), (3,false,5), (3,true,5)}`
- `Φ=4` 상태: 1-step signature = `{(2,false,1), (3,false,1), (3,true,1)}`

둘 다 정확히 3개의 legal 옵션을 갖지만(**개수는 같다**), `ell` 값이
다르다(5 대 1) — `SHORTFALL_BUDGET_THEOREM.md`의 forced-ell lemma의
직접적 결과다(Φ=0은 ell=5 강제, Φ=4는 ell=1도 허용). 어느 한쪽
signature가 다른 쪽을 진짜로 "포함"하지 않으므로(원소 자체가 다르다,
`ell`이 다르므로), "낮은 Φ가 항상 지배한다"거나 "적게 쓴 orbit 수가
항상 지배한다"는 순진한 형태의 dominance는 **이 반례로 반증된다.**

이 반례는 놀라운 새 발견이라기보다, 이미 증명된 forced-ell lemma가
naive dominance 직관과 충돌한다는 것을 실제 데이터로 확인한 것이다 —
그 자체로 "쉬운 지름길은 없다"는 걸 보여주는 유용한 negative result다.

## A, D, E: 왜 미결정인가

이 세 후보는 각각 정확한 **집합 포함 관계**(visited set superset,
phase mask containment)나 **경계 데이터 완전 일치**(같은 O, D, 다른
P)를 요구한다 — 이런 정확한 구조적 일치는 무작위/BFS로 모은
6,045개짜리 pool에서 우연히 나타나기엔 너무 특수한 조건이다. 못
찾았다는 것은 "이런 쌍이 존재하지 않는다"는 증거가 **아니다** — 더
큰 pool이나 의도적으로 구성된 쌍에서는 나타날 수 있다. **안전하다고
선언하지 않는다.**

## 결론

이번에 실제로 확인된 것은 두 개의 **반증**(B, C)뿐이다. 이는
음성 결과이지만 정직한 진전이다 — "이런 단순한 dominance 규칙이
작동하지 않는다"는 것을 실제 반례로 확정했으므로, 앞으로 이 방향의
naive 시도를 반복할 필요가 없다.
