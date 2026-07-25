# 계수 단위(counting unit) 영구 표준 (라운드 19)

라운드18에서 확인된 대로, RR 연구 전체에서 발생한 유일한 실질적
혼동은 **서로 다른 대상을 같은 숫자로 취급한 것**이었다(9 vs 5).
이 문서는 그 재발을 막기 위한 **영구 표준**이다.

## 네 가지 계수 단위 — 절대 섞지 말 것

| 단위 | 정의 | 대표 사례 | 전형적 크기 |
|---|---|---|---|
| **word-level** | 완결된 macro-edge word 하나 | 역사적 코퍼스의 `state_record` 하나, "H9=9개" | ell=4 same-component: **9** |
| **post-R2-state-level** | R2가 발동하는 순간의 서로 다른 `ExactState` 하나 | 라운드17-19 enumerator의 단위, "L5=5개" | ell=4 same-component: **5** |
| **event-level** | R2 boundary 발생 1회 | predicate ablation의 표본 단위 | depth6 전체: **2,234** |
| **history-level** | `(state, history)` 쌍 하나 | canonical enumerator의 dedup key | depth6 ell=4: **3,834** |

**같은 현상이 단위에 따라 9, 5, 2234로 보인다.** 이것이 라운드18
불일치의 전부였다.

## 표기 규칙 (의무)

1. **모든 숫자에 단위를 붙인다.** "same-component 5개"가 아니라
   "same-component **post-R2 state** 5개".
2. **JSON 필드명에 단위를 넣는다.** 이번 라운드의
   `post_r2_state_count_same_component`,
   `event_level_antecedent_count`,
   `historical_word_count` 처럼.
3. **한 표에 두 단위를 섞지 않는다.** 꼭 필요하면 열 머리글에
   단위를 명시한다.
4. **implication을 기술할 때 scope와 단위를 함께 적는다**
   (`outputs/rr_local_implication_lattice.json`이 이 형식을 따른다).
5. **raw인지 canonical인지 명시한다**(라운드18 정정 사항):
   `unique_raw_states` vs `unique_canonical_pair_keys`.

## 단위 사이의 정확한 변환 관계

**exact counting identity (라운드19 §4에서 확립)**:

\[
\#\text{words}
=
\sum_{S\in\text{post-R2 states}}
\#\text{allowed trailing completions}(S)
\]

여기서 "allowed trailing completion"은 **"word를 코퍼스가 정한
길이(6 macro-edge)까지 정확히 채우는 legal macro-edge"**로 엄밀히
정의해야 한다 — "임의 길이의 legal continuation"으로 읽으면 이
항등식은 성립하지 않는다. 실제 사례: `9 = 3 + 3 + 3`.

**event-level → post-R2-state-level**: 이번 universe에서는 2,234개
post-R2 상태 각각이 정확히 1개의 event로 도달되므로 두 단위가
우연히 일치한다(§`RR_L5_LOCAL_UNIVERSE.md` §5). **이는 이 universe의
성질일 뿐 일반 규칙이 아니다** — 일반적으로는
event-level ≥ post-R2-state-level이다.

## 과거 문서 재검토 (§13)

라운드11~18 문서에서 다음 표현을 전수 검색해 현재 scope/단위와
대조했다: "전체 4,470개", "완전 전수", "canonical states",
"witness count", "same-component 9개", "local exhaustive".

**라운드18에서 이미 정정한 7건 외에 추가로 필요한 수정은 발견되지
않았다.** 근거:

- "전체 4,470개"류 표현은 전부 **word-level**이고, 라운드16-18이
  이미 "capped-corpus exact"라는 scope 단서를 붙였다 —
  `RR_EVIDENCE_AUDIT.md`의 15항목 표가 이를 이미 반영한다.
- "canonical states" 표현은 라운드18에서 `unique_raw_states`로
  정정 완료(2개 파일, 2개 스크립트).
- "same-component 9개"는 라운드18 `RR_ELL4_DISCREPANCY_AUDIT.md`가
  word-level임을 명시하고 state-level 3개와 병기했다.
- "local exhaustive"는 라운드17 `RR_EXHAUSTIVENESS_STANDARD.md`가
  이미 6개 용어로 분리해 정의했다.

**따라서 §13의 결과는 "추가 정정 0건"이다** — before/after 표를
새로 만들 대상이 없다. (라운드18 표는
`RR_ELL4_DISCREPANCY_AUDIT.md` §13에 그대로 보존된다.)

## 이 표준의 지위

**손증명이나 정리가 아니라 서술 규약**이다. 그러나 라운드18의
경험상, 이 규약의 부재가 실제로 여러 라운드에 걸친 혼동을
만들었으므로 정리와 동등한 비중으로 유지한다.
