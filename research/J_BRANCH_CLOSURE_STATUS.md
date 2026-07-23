# J-branch 폐쇄 상태 판정

## 후보 J1–J5

**J1. "J 이후 반드시 R이 필요하다."** → **반증됨 (산술적으로, 전체
230개에 대해 일반적으로).** `R_blocked_w3_existing`과
`Z2_blocked_w2_existing`은 `(ΔF,ΔO,ΔD,ΔP)`에 대해 **완전히 동일한 효과**
`(0,0,-1,+1)`를 갖는다 — 차이는 오직 `ΔN`(+1 대 0)뿐이다. 따라서 `r`개의
`R`을 쓰는 어떤 자원 분해든, `r`을 0으로 낮춘 분해로 항상 대체 가능하다
(N이 줄어드는 방향이므로 어떤 상한도 위반하지 않는다). 이는 상태에 무관한
**일반 논증**이므로 230개 전부에 적용된다: **어떤 J 상태도 자원 산술만
으로는 `R` 사용이 강제되지 않는다.** J1이 참이라면 그 이유는 반드시
기하적(충돌 회피)이어야 하며, 지금까지 그런 이유는 발견되지 않았다.

**J2. "R을 사용하면 이후 zero-charge 흐름으로는 완주할 수 없다."** →
**미결정.** J1의 R/Z2 상호교환성 논증은 R 사용이 "선택"이지 "필요"가
아님을 보일 뿐, R을 실제로 사용했을 때 이후가 막히는지는 말해주지 않는다.
`J_DECISIVE_EVENT_SEARCH.md`의 bounded 실험은 R 사용/미사용을 구분해
추적했지만 두 경우 모두 depth 6 안에서 완주가 전혀 관측되지 않아(0건),
비교할 데이터가 없다.

**J3. "J 이후 R을 쓰지 않으면 cover-capacity가 부족하다."** →
**미결정.** 45/230 seed에서 capacity prune이 관측됐지만(`J_DECISIVE_EVENT_SEARCH.md`),
이것이 R 미사용과 상관관계가 있는지는 이번에 분리해서 확인하지 않았다.

**J4. "J와 R의 target/source component 관계가 incidence forest에서
재사용 cycle을 강제한다."** → **미결정.** incidence-component(같은
E-orbit 그래프 component 재사용) 분석은 이번 범위에서 수행하지 않았다 —
`component_relation` 필드 자체가 J(단일 이벤트)에는 정의되지 않는다
(`J_NORMAL_FORMS.md` §0). R을 실제로 사용한 이후의 component 관계를
보려면 추가 코드가 필요하며, 이번 작업에서는 작성하지 않았다.

**J5. "J는 split hexagon completion에 필요한 유일 phase를 소모한다."** →
**미결정.** `f1_normal_form`상 J 이후 상태는 항상 정확히 하나의
fragment_hex(단일 arc)를 갖는다(230개 전부, `J_EXACT_NORMAL_FORMS.md`) —
이는 F<=1의 일반적 귀결이지 J에 고유한 현상이 아니다. "split hexagon"이
J의 target/source와 정확히 어떤 관계인지에 대한 이번 코퍼스의 명시적
정의를 찾지 못했고, 새로 정의해 검증하는 것은 이번 범위 밖이다.

## 최종 분류

지시된 세 선택지 A/B/C 중:

> **C. 저장 정보 부족 또는 상태폭발로 아직 reduction 불충분.**

**A가 아닌 이유:** 230개 exact 상태를 복구·검증한 것(`J_230_WITNESS_RECOVERY.md`)
은 완료됐지만, 그 이후의 decisive-event 탐색은 depth 6·edge cap 3,000의
bounded 실험이었을 뿐 — 완주까지 필요한 나머지 ~110개 이상의 joint에
대해서는 아무것도 밝혀지지 않았다. 230개 중 단 하나도 이 bounded window
안에서 완주 또는 확정적 불가능 판정을 받지 않았다(`completions_found: 0`,
그러나 완전 봉쇄도 확인되지 않음). **finite exhaustive search로 닫힌
것은 하나도 없다.**

**B가 아닌 이유:** `J_EXACT_NORMAL_FORMS.md`가 정확히 이를 반증한다 —
230개를 21개의 coarse fingerprint로 묶을 수는 있지만, 그 quotient는
**증명 가능하게 손실적**이다(같은 fingerprint, 다른 1-step legal
continuation shape의 반례 75쌍, 최소 반례쌍 명시됨). 따라서 "소수
normal-form family로 완전 환원되어 각 family의 남은 search specification이
고정됨"이라는 B의 조건이 성립하지 않는다.

**따라서 C.** 다만 이번 작업이 "아무 진전 없음"은 아니다 — 다음은 이번에
실제로 얻은, 재현 가능한 새 사실들이다:

1. **230/230 exact literal witness 복구 및 독립 검증** (이전에는 1/230
   뿐이었다).
2. **J1의 일반적 반증** (R/Z2 상호교환성 — 산술적으로 R은 결코 강제되지
   않는다, 230개 전부에 대해).
3. **coarse-fingerprint 정규형이 손실적임을 반례로 확정** — 즉 230개를
   "가능한 한 적은 family로" 압축하려는 시도가 국소 정보만으로는 성립하지
   않는다는 것을 실제 데이터로 보였다. 이는 향후 시도가 국소 fingerprint가
   아니라 전체 canonical state(사실상 압축 불가능한 개별 상태)를 다뤄야
   함을 의미한다.
4. **depth 5~6에서 capacity prune이 실제로 나타남을 최초로 관측**
   (45/230 seed) — 산술만으로는 안 보이던 장애물의 첫 실증적 신호.

## 남은 일 (다음 세션 시작점)

- 45개 capacity-prune-관측 seed에 대한 더 깊은(더 큰 edge cap) 개별 실험.
- J4(component/incidence 관계)를 실제로 계산하는 코드 작성.
- J2/J3(R 사용 여부와 완주 가능성의 관계)를 구분해서 추적하는 실험 설계.
- U-branch(다섯 unit-defect word)의 독립성 문제는 이번에 전혀 다루지
  않았다 — `N2_CLOSURE_STRATEGY.md`에 남겨진 채로다.

조건부 `L_6>=872`, 무조건 `L_6=872`는 여전히 열려 있다. 이번 작업은 그
전체 목표에 대해 어떤 결론도 내리지 않는다 — J-branch라는 좁은 하위
문제 하나에 대한 정직한 진전 보고다.
