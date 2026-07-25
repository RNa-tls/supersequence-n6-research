# Nearest Residual Completer 정리 — 손증명된 부분과 반증된 부분 (라운드 16)

산출: `src/analyze_rr_residual_cost.py`, `src/verify_rr_nearest_residual.py`
-> `outputs/rr_residual_cost_table.json`, `outputs/rr_nearest_residual_fresh_verification.json`.

## 이번 라운드의 가장 중요한 발견 먼저: 코퍼스 완전성 정정

라운드15는 "hub가 완성되는 212개 사건 전부에서 completer orbit은
항상 nearest residual position"이라고 결론지었다. 이번 라운드는 이
주장을 손증명하려다가 **결정적 문제를 발견했다**:

`legacy_research/work/analyze_f1_n2_defects.py`의 자체 docstring을
직접 확인한 결과 — `"Its only exploration is a capped continuation"`,
그리고 `area_a_depth6` 처리 함수의 scope 필드: `"finite complete
replay of an existing bounded Area-A frontier; not an N=2
enumeration"`. 즉 **`rr_literal_witnesses.json`의 4,470개 RR
witness가 나온 원본 코퍼스(`f1_n2_defect_words.json`)는
`A_F1_H0_Nle3_macro_depth6.checkpoint.json`이라는, 과거 어느
라운드에서 **65,340개 상태로 캡(cap)된** bounded frontier를
그대로 재생(replay)한 것이지, depth≤6 legal RR-structured state
전체의 수학적으로 완전한 열거가 아니다.**

**직접 반증 witness**: `src/analyze_rr_self_completion.py`가
새로 구성한 state — `ell=0` 낙오, `w2:10`(abandon) → `w3:120`(R,
R1) → `w3:201`(Z3) → `w2:10`(Z2) → `w3:120`(R, R2=completer, hex0의
**가장 먼** residual 위치인 orbit1에 착지) — 는 `area_a_prune_reason`
검사를 통과하고(`None`, 완전히 legal), F=1,H=0,구조상 RR과 정확히
일치하지만, **원본 코퍼스(`f1_n2_defect_words.json`)의 25,660개
전체 레코드 중 어디에도 존재하지 않는다**(해시로 직접 확인).

이는 라운드15(및 그 이전 여러 라운드)가 이 코퍼스를 근거로 내린
"유한 완전 검증" 판정들의 **인식론적 지위를 재검토해야 함**을
의미한다 — "코퍼스 4,470개 전부에서 성립"은 여전히 사실이지만,
"그러므로 depth≤6 전체에서 일반적으로 성립"이라는 확장 추론은
**과잉주장이었다.**

## 대신 이번 라운드가 확립한 것: 신선한(fresh) 완전 재검증

원본 코퍼스에 의존하지 않고, `exact.extend()` + `macro.macro_edges()`
+ `macro.area_a_prune_reason()`만 사용해 각 `ell`의 abandonment
루트부터 **처음부터 다시** BFS를 돌렸다(`verify_rr_nearest_residual.py`).
**frontier가 매번 완전히 소진**(node cap 없이 자연 종료, depth≤5:
약 1,050~1,100개 상태, depth≤6: 약 3,650~3,860개 상태 — 이 state
space는 원래 매우 작다)되어, 이번에는 **진짜** 유한 완전 검증이다.

### 결과 1 — 이분법(dichotomy)은 재확인됨

`same-component`는 depth≤5, depth≤6 두 조건 모두에서 여전히
정확히 `ell∈{0,4}`에서만 나타난다(`ell=1,2,3`에서 0). **독립적인
재검증으로 강화됨.**

### 결과 2 — "nearest만 실현된다"는 주장은 반증됨

신선한 완전탐색에서 **모든 `ell<4`에 대해 non-nearest completer도
legal하게 실현된다**:

| ell | nearest | completer 분포 (depth≤6, 완전탐색) |
|---:|---:|---|
| 0 | 120 | {120:19, 1:10, 33:12, 9:9, 3:3} |
| 1 | 33 | {33:19, 9:12, 3:8, 1:3} |
| 2 | 9 | {9:19, 3:12, 1:9} |
| 3 | 3 | {3:19, 1:12} |
| 4 | 1 | {1:19} (residual 위치가 1개뿐이므로 자명) |

**라운드15의 "nearest만 실현된다"는 명제는 이제 반증됨으로
표시한다.** ell=4를 제외한 모든 ell에서 non-nearest completer가
legal하게, 그리고 드물지 않게(nearest와 같은 자릿수) 발생한다.

## 그래도 손증명으로 남는 것: 최소 비용(cost) 정리

라운드15/16의 "cost" 개념(hub 재완성까지 필요한 macro-edge 수) 중
**최솟값에 관한 주장은 손증명으로 확정된다**:

**정리(손증명, 유한 완전 case analysis)**: 이 모델의 조인트는
정확히 4개뿐이다(`w2:10` 1개, `w3:120/201/210` 3개 —
`UNIQUE_WEIGHT2_MOVE_THEOREM.md`). abandonment 직후 hex0를
재터치하는 데 필요한 macro-edge 수를 `c`라 하면:

1. **`c=1`은 불가능하다** — 5개 ell × 4개 abandonment 선택 × 4개
   step1 조인트 = 80개 분기 전부를 exhaustively 확인(`explore2`
   케이스체크, `outputs/rr_residual_cost_table.json`의
   `cost1_cost2_exhaustive_case_check`), 반례 0.
2. **`c=2`가 legal하다면 반드시 nearest residual 위치에
   착지한다** — 320개(5×4×4×4) 전체 분기를 exhaustively 확인,
   `c=2`로 hex0를 맞추는 15개 분기 전부(ell당 정확히 3개)가
   예외 없이 nearest position에 착지한다.

이 두 명제는 **원본 코퍼스나 이번 라운드의 신선한 재검증
어느 쪽에도 의존하지 않는, 순수하게 이 모델의 4개 조인트만으로
결정되는 유한 케이스체크**이므로 손증명 등급으로 유지한다 —
코퍼스 완전성 문제와 무관하게 성립한다.

## 성공 기준 (1) 평가

**부분 달성**: "nearest residual completer의 최소비용(=2)이
유일 최적이며 다른 어떤 residual도 비용2로 도달 불가능하다"는
**손증명**됐다. 그러나 "nearest만 legal하게 실현 가능하다"는
원래 기대했던 강한 형태는 **반증됨** — 더 높은 비용(`c≥4`)의
non-nearest completion도 legal하며, 실제로 이번 라운드가 발견한
신선한 완전탐색에서 드물지 않게 나타난다. **정리는 "최소 비용"
버전으로 정확히 좁혀서 기술해야 한다.**
