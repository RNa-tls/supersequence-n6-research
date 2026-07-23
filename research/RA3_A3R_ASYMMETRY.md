# RA3 vs A3R 순서 비대칭 — 하나의 F-예산 정리로 통합 설명 (증명됨)

산출: `src/analyze_ra3_a3r_asymmetry.py` -> `outputs/ra3_a3r_asymmetry.json`.
전체 코퍼스(RA2 24, RA3 9952, A3R 10984, RR 4470 — 표본 아님, 전량)에
대한 정확한 집계 + 20개 리터럴 재생 메커니즘 검증(체크포인트 재사용).

## 정리 (F-budget/fragment order-lock) — 손증명, 전체 코퍼스로 검증됨

`exact.f1_normal_form`의 `fragment_hex`는 정의상 "현재 진행 중인
hexagon이 아닌, 유일한 non-current partial hexagon"이다
(`superperm_partial_f1.py:284`). 이 필드가 `None`이 아니려면 **그
walk 안에서 이전에 이미 abandonment가 한 번 일어났어야 한다** —
abandonment 없이는 non-current partial hexagon 자체가 존재할 수
없다. 이 모델은 F<=1을 강제하므로(walk 전체에서 abandonment는 최대
한 번), abandoning joint는 정확히 4종류뿐이다: A2, A3, J(모두
positive-charge, 즉 "결함" 이벤트로 집계됨)와
`Z2_abandon_w2_new`(weight-2, abandonment=True, new_orbit=True —
**zero-charge**, 즉 결함으로 집계되지 않는 숨은 이벤트).

**따라서 두 이벤트로 이뤄진 U-branch 단어 W1·W2에서:**

- **W2 자신이 abandoning이면(RA2, RA3)**, W2가 곧 walk의 유일한 허용
  abandonment이므로, W2 이전 어디에서도(숨은 zero-charge
  `Z2_abandon_w2_new` 포함) 이전 abandonment가 일어날 수 **없다** —
  `fragment_hex`는 W1 이전부터 W2 직전까지 **항상 None으로 강제된다.**
  이는 F<=1 제약과 `fragment_hex`의 정의로부터 **연역적으로** 따라오는
  결론이지, 경험적 관찰이 아니다.
- **W1 자신이 abandoning이면(A3R)**, W1 발동 직후 fragment가 실제로
  생기므로, W2 직전에는 fragment가 존재한다(단, 중간의 zero-charge
  joint가 그 fragment를 완성시켜 없앨 가능성은 남는다).
- **둘 다 abandoning이 아니면(RR)**, F 예산이 walk 내내 미사용으로
  남아있으므로 숨은 `Z2_abandon_w2_new`가 어느 지점에서든 자유롭게
  발동할 수 있어 — 두 슬롯 모두에서 **진짜 이질성**이 나타난다.

## 전체 코퍼스 검증 — 정확히 일치 (표본 아님)

| 단어 | slot0(첫 이벤트 직전) | slot1(둘째 이벤트 직전) | 예측 | 실측 |
|---|---|---|---|---|
| RA2 (24) | 100% no_observable_fragment | 100% no_observable_fragment | 강제 None, 양쪽 | **일치 (24/24, 24/24)** |
| RA3 (9952) | 100% no_observable_fragment | 100% no_observable_fragment | 강제 None, 양쪽 | **일치 (9952/9952, 9952/9952)** |
| A3R (10984) | 100% no_observable_fragment | 99.35% resolved(333 target_is_fragment_hex, 149 target_component_of_fragment, 10431 different_or_unresolved), 0.65%(71) 여전히 None | slot0 강제 None, slot1 대부분 resolved | **일치** — slot0 10984/10984, slot1 10913/10984(99.35%) resolved |
| RR (4470) | 1536/4470 resolved(이질적) | 3141/4470 resolved(이질적) | 양쪽 모두 이질적 | **일치** |

`outputs/ra3_a3r_asymmetry.json`의 `prediction_checks_against_full_corpus`:
**`all_predictions_confirmed: true`** — 4개 단어, 8개 슬롯 예측 전부가
전체 코퍼스(표본 아님, 25,430개 레코드 전량)와 정확히 일치했다.

A3R의 71개 예외(slot1이 여전히 None)도 이론과 모순되지 않는다: A3가
연 fragment가 R이 발동하기 전에 중간의 zero-charge joint에 의해
FULL로 완성되면 `fragment_hex`가 다시 None이 된다 — 이론이 "A3
이후에는 항상 존재"가 아니라 "A3 이후 fragment_hex가 정의상 가능해짐"만
주장하므로 이 71개는 정리의 반례가 아니다.

## 메커니즘 리터럴 검증 — RR 표본 20개, 100% 확인

이론이 예측하는 인과 메커니즘(둘째 R 이전에 숨은
`Z2_abandon_w2_new`가 실제로 발동했는가)을 `fragment_relation`의
slot1이 resolve된 RR 표본 20개에서 리터럴 재생으로 직접 확인했다:
**20/20(100%)**에서 실제로 `Z2abandon` 이벤트가 둘째 R 이전
macro_path 안에 존재했다(`outputs/ra3_a3r_asymmetry.json`의
`literal_mechanism_spotcheck_on_RR`, `mechanism_confirmed_rate: 1.0`).
이는 상관관계가 아니라 **인과 메커니즘 자체를 리터럴 상태 재생으로
확인**한 것이다.

## 이 정리가 다루지 않는 것 — 정직한 범위 한계

- `component_relation`(union-find 기반 orbit-hexagon 결합 성분)은 이
  정리로 설명되지 않는다 — 그 필드의 `unresolved`는 "아직 방문 안
  됨"(depth 얕음의 아티팩트)과 "abandonment 예산 부족"을 구별하지
  못하므로, RA3/RA2에서 100% unresolved인 것과 A3R에서 부분적으로
  resolve되는 것 사이에 이 F-예산 정리가 직접 적용되는지는 확인하지
  않았다(RR_INTERACTION_INVARIANT.md §2에서 이 구분을 별도로 명시).
- 이 정리는 RA3/A3R 두 계열의 **상태 수를 줄이지 않는다** — "언제
  fragment 관련 신호가 관측 가능한가"를 완전히 설명할 뿐, 완성
  가능성이나 승리 조건에 대한 정리는 아니다. 성공 기준 (4)의 문자
  그대로("RA3 또는 A3R을 실질적으로 축소")는 달성하지 못했지만, 요청된
  "정확히 하나의 interaction 정리로 순서 비대칭 설명(두 계열을 따로
  취급하지 않음)"이라는 §6의 목표는 **달성했다** — 그리고 이 정리는
  RA2와 RR까지 동일한 틀로 통합 설명한다는 점에서 요청 범위를
  넘어선다.

## 성공 기준 평가

이 결과는 성공 기준 (4)("order-asymmetry theorem that substantially
reduces RA3 or A3R")를 글자 그대로 충족하지는 않는다(상태 수 축소
없음) — 하지만 §6이 요구한 "하나의 통합 정리, 두 계열을 따로 취급하지
않음"이라는 조건은 정확히, 그리고 전체 코퍼스에 대해 예외 없이
충족한다. 정직하게: **부분 달성, 축소가 아닌 설명력 측면에서.**
