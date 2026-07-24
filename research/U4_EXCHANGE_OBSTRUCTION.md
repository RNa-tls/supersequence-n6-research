# U4와 defect-order exchange — U4는 exchange 판정 대상 밖에 있다

## 6. U4 대 C20 — exchange 가능성 비교

`RA2_A2R_EXCHANGE_THEOREM.md` §1+3의 인접(adjacent) exchange
truth table은 **R과 A2 사이에 zero-charge joint가 없는(zc_len=0)
10개 상태에 대해서만 정의된다.** U4의 4개 상태는 전부
`zero_charge_word_length ∈ {1,2}`다(`RA2_ZERO_CHARGE_HISTORY.md`에서
이미 확립) — **U4는 애초에 "인접 exchange" 판정 대상에 포함되지
않는다.**

**핵심 질문에 대한 답**: "U4는 정확히 defect-order exchange가
막히는 RA2 상태인가?" → **판정 불가(범위 밖).** U4가 인접
사례였다면 §`RA2_A2R_EXCHANGE_THEOREM.md`의 일반 정리(R
pre-boundary가 항상 FULL → collision)가 그대로 적용됐겠지만, U4는
애초에 그 정리가 다루는 사례가 아니다.

**반대 질문**: "U4는 exchange 가능한데 C20은 불가능한가?" → 이
질문도 성립하지 않는다 — C20의 인접 10개 전부가 exchange
**불가능**함이 이미 증명됐고(`RA2_A2R_EXCHANGE_THEOREM.md`), U4는
비인접이라 같은 틀로 비교할 수 없다. **U4와 C20을 가르는 것은
exchange 가능성이 아니라 여전히 `ell_A2`(이전 라운드 결론)다.**

비인접 U4 witness 하나(`17a42b24ccfb`)에 대해 "A2를 마지막
zero-charge joint 위치로 옮기는" 국소 치환을 시도한 결과는
**legal했다**(`RA2_A2R_EXCHANGE_THEOREM.md` §4) — 이는 U4가 C20보다
"교환에 더 유리하다"는 뜻이 **아니다**: 이 국소 치환은 R과 A2의
순서를 실제로 바꾸는 것이 아니라 zero-charge word 내부의 한
joint를 대체하는 것일 뿐이며, 전체 A2R 순서로의 완전한 재배열과는
다른 질문이다.

## 7. Exchange distance χ — 실측값

요청된 정성적 벡터 대신, 실측 가능한 정량 지표로 χ를
근사했다: **A2R의 전역 최소 depth(6, `A2R_MINIMUM_DEPTH.md`) 대비
각 RA2 witness가 A2에 도달하는 depth**:

| 그룹 | RA2 witness의 A2 도달 depth 분포 |
|---|---|
| U4(4개) | {5: 2개, 6: 2개} |
| C20(20개) | {5: 10개, 6: 10개} |

**χ := depth(A2R_min) − depth(RA2 witness to A2) = 6 − {5 or 6} ∈ {0, 1}.**
U4와 C20 사이에 이 지표로는 **차이가 없다**(둘 다 {0,1} 범위에
고르게 분포) — χ는 U4를 구별하는 지표가 아니다. 이는 애초에
예상했던 것보다 훨씬 작은 gap이다(처음에는 RA2의 "가장 짧은"
witness가 A2R보다 훨씬 얕을 것이라 예상했으나, 실측 결과 RA2
자신도 이미 depth<=6 코퍼스 경계에 가깝게 붙어 있다 — R 자신도
walk의 첫 이벤트로 등장하려면 흔히 여러 준비 joint가 필요하다,
r_idx 분포 `{0:1,1:4,2:9,3:8,4:2}`).

**목표 정리 "χ>0인 RA2 상태는 완주 전에 동일한 구조적 cost를
반드시 지불한다"는 시도하지 않는다** — χ 자체가 U4/C20을 가르지
못하는 지표로 판명됐으므로, 이를 completion cost와 연결 짓는
정리를 세울 근거가 없다(**미완료**, 억지로 연결 짓지 않음).

## 성공 기준 (3) 재확인 — 미달성

"U4를 가르는 defect-order exchange obstruction"은 **미달성**이다 —
U4는 애초에 §1의 판정 대상(인접 사례)에 속하지 않고, χ 지표로도
C20과 구별되지 않는다. 이는 정직한 음성 결과다: defect-order
exchange라는 각도는 U4의 특수성(ell_A2=4)을 설명하는 새로운
방법이 되지 못했다.
