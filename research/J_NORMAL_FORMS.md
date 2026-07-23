# J 상태 230개의 분류 — 가능한 범위까지

산출 코드: `src/verify_j_normal_forms.py` -> `outputs/j_normal_forms.json`.

## 데이터 한계 (반드시 먼저 읽을 것)

`legacy_research/outputs/f1_n2_defect_words.json`의 `state_records`에는
230개의 J 레코드가 있고, 각각 다음 필드만 있다.

```
state_hash, deficit_phase_type, legal_macro_tail_count,
global_visited_mask_fingerprint, word
component_relation, fragment_relation, orbit_relation, defect_macro_distance  (전부 null)
```

null인 네 필드는 두 이벤트짜리 word(RR, RA3, A3R, RA2)를 위한 pairwise
관계 필드다. J는 이벤트가 하나뿐이므로 정의상 null이며, `verify_j_normal_forms.py`가
230개 전부에서 이를 재확인했다.

**따라서 "source E-orbit / target E-orbit / split hexagon 위치 / fragment
위치 / open component 구조 / visited-mask support / legal-tail signature"
같은 완전한 exact canonical normal form은 230개 중 단 1개(literal
representative)에서만 재구성 가능하고, 나머지 229개는 재구성할 수 없다.**
이는 이 코퍼스에 그 데이터가 원래 저장되지 않았기 때문이며, 이번 작업은
(지시에 따라) 새 대규모 탐색을 하지 않으므로 이를 다시 만들어낼 수도 없다.
아래 분류는 이 한계 안에서 할 수 있는 최선이다: 실제로 저장된 두 개의
per-state 정확값(`deficit_phase_type`, `legal_macro_tail_count`)에 대한
**정확한, 완전한** 재집계다.

## 1. deficit_phase_type에 의한 그룹 — **완전 검증**

230개 전부가 정확히 13개의 `deficit_phase_type` 값 중 하나로 떨어진다
(재검증: 합계 230 일치).

| deficit_phase_type | 개수 |
|---|---:|
| (3, 3, 4, 4, 4) | 46 |
| (2, 3, 4, 4) | 44 |
| (3, 4, 4, 4, 4) | 25 |
| (2, 4, 4, 4, 4) | 17 |
| (1, 3, 4) | 16 |
| (3, 4, 4, 4, 4, 4) | 16 |
| (3, 3, 3, 4) | 14 |
| (3, 3, 4, 4) | 13 |
| (2, 4, 4, 4) | 12 |
| (1, 4, 4, 4) | 12 |
| (2, 2, 4) | 8 |
| (1, 4, 4) | 6 |
| (1, 3) | 1 |

가장 좁은(짧은) 그룹은 `(1,3)` (단 1개 상태) — 이 상태가 남은 deficit
phase가 가장 적어, 완주까지 "구조적으로 필요한 남은 phase 슬롯"이 가장
작은 경우다. `(3,3,4,4,4)`가 최다(46개)로, phase 3부터 시작해 4로
채워지는 형태가 다수를 차지한다.

## 2. legal_macro_tail_count 분포 — **완전 검증**

| legal_macro_tail_count | 개수 |
|---:|---:|
| 2 | 22 |
| 3 | 30 |
| 4 | 178 |

**중요:** 230개 중 **단 하나도 0이 아니다** — 즉 depth-6 bounded frontier
안에서는 J 상태 전부가 최소 2개의 합법적 macro-tail 계속을 가졌다. 이는
"이 bounded window 안에서 즉시 죽는 J는 없었다"는 뜻이지, "J가 완주
가능하다"는 뜻이 아니다 (그 frontier 자체가 macro-depth 6에서 멈춘
bounded replay이기 때문).

## 3. 교차표 — **완전 검증**

`deficit_phase_type x legal_macro_tail_count`는 `outputs/j_normal_forms.json`에
전체가 있다. 예: `(2,3,4,4)`형(44개) 중 35개가 `legal_macro_tail_count=4`로,
이 그룹이 상대적으로 여유 있는 후속 상태들임을 시사한다(다만 이는
관측일 뿐, 정리 아님).

## 4. 대표(literal) 예시와의 교차 확인 — **완전 검증**

`f1_n2_depth6_decomposition.json`의 representative는
`deficit_phase_type=(1,3)`, `legal_macro_tail_count=3`이다 — 즉 위 §1에서
가장 좁은 그룹(개수 1)의 바로 그 유일한 원소다. 따라서
`src/analyze_j_completion.py`의 모든 literal replay·bounded-continuation
결과는 **230개 중 가장 제약이 강한(가장 적게 남은) 케이스 하나**에 대한
것이며, 일반적인/전형적인 J 상태를 대표한다고 볼 수 없다. 이는 결과를
해석할 때 반드시 감안해야 한다 — 예컨대 `research/J_COMPLETION_OBSTRUCTION.md`의
§3 산술(23개 신규 orbit 필요 등)은 이 특정 좁은 케이스의 수치이며, 다른
229개는 각기 다른 (P,O,D,N) 좌표를 가져 다른 산술을 낳을 것이다 — 그
산술 자체는 데이터가 없어 재현할 수 없다.

## 5. 국소 fingerprint 반례쌍 요청에 대하여

지시된 "국소 fingerprint가 같은데 legal-tail 집합이 다른 상태쌍의 최소
반례" 요청은, J의 경우 fingerprint로 쓸 수 있는 유일한 저장 필드가
`deficit_phase_type`뿐이므로, 이를 fingerprint로 채택하면 §3의 교차표
자체가 답이다: 예를 들어 `deficit_phase_type=(2,3,4,4)` 그룹(44개)은
`legal_macro_tail_count`가 2, 3, 4로 **갈린다** — 즉 같은
deficit-phase-type 안에서도 legal-tail 집합 크기가 다른 상태들이 실제로
존재한다(반례: 이 그룹 안에서 tail_count=2인 4개 상태와 tail_count=4인
35개 상태). 다만 이것이 "같은 국소 fingerprint, 다른 legal-tail 집합"이라는
원래 질문(A3R 등 2-이벤트 word에서 이미 발견된
`minimum_counterexample_word_phase_to_tail_determinacy`)과 완전히 같은
현상인지는, J가 1-이벤트라 그 counterexample에 쓰인 fingerprint 정의
(joint + deficit_phase + component-relation summary)를 그대로 적용할 수
없어 **미결정**으로 남긴다.
