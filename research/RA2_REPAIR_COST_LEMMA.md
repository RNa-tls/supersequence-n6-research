# Repair-cost lemma 후보 R1–R4, 그리고 Ω 결합 invariant

산출: `src/verify_ra2_repair_cost.py` -> `outputs/ra2_counterfactual_edits.json`
(repair-cost 후보 부분); `outputs/ra2_repair_cones.json`(재사용).

## 4. Repair-cost lemma 후보 평가

| 후보 | 정확한 명제 | 판정 | 근거 |
|---|---|---|---|
| **R1** | RA2에서 fragment-debt=1을 해소하려면 최소 하나의 특정 blocked joint가 필요하다 | **손증명** | rotation은 정의상 current hex 안에서만 움직이므로(`FRAGMENT_REPAIR_OBLIGATION.md` §5), non-current fragment에 새 방문을 추가하는 유일한 수단은 joint뿐이다 — 자명하지만 구조적으로 필연적인 사실 |
| **R2** | 그 blocked joint는 최소 1의 orbit slack 또는 shortfall(Φ)을 소비한다 | **반증됨** | U4 4개 전부에서 가장 얕은 repair witness가 `phi_consumed=0, orbit_slack_consumed=0`을 기록 — 최소 반례: `17a42b24ccfb`의 macro_path `["rot^5;w2:10","rot^5;w2:10","rot^5;w3:120"]`(macro_distance=3) |
| **R3** | U4에서는 필요한 repair cost가 현재 available budget보다 크다 | **반증됨** | 필요한 cost가 정확히 0이므로, 어떤 양의 budget보다도 작다 — 대소 관계가 성립할 수 없다 |
| **R4** | repair 가능한 transition은 terminal completion에 필요한 orbit을 재사용하므로 다른 completion demand와 양립할 수 없다 | **미완료** | 이 명제를 평가하려면 "terminal completion에 실제로 필요한 orbit"이 무엇인지 알아야 하는데, 이 슬랩 전체에서 단 하나의 완주 witness도 확보된 적이 없다(`L_6` 자체가 미해결) — 구체적으로 검증할 대상이 없어 판정을 미룬다 |

**R1만 참으로 확정됐고, R2/R3는 구체적 반례로 반증됐다.** 이는
`FRAGMENT_REPAIR_OBLIGATION.md` §6의 결론(repair는 저렴하다)과 완전히
일치하는 결과다 — 서로 다른 두 방법(직접 탐색 vs 명제별 개별 검증)이
같은 결론에 도달했다는 점에서 결과의 신뢰도를 높인다.

## 8. Ω 결합 invariant — 시도했으나 근본적으로 무너짐

요청된 `Ω(S) = (Φ(S), orbit slack(S), fragment debt(S), repair
accessibility(S))`를 시도했다. 그러나 `RA2_ZERO_CHARGE_HISTORY.md`의
중심 항등식 `Φ = 6 - fragment_debt`(24개 전부, 예외 없음)가 이미
보여주듯, **Φ와 fragment debt는 RA2의 post-A2 상태에서 독립적인
두 좌표가 아니라 정확히 같은 정보를 두 번 표현한 것이다.** 따라서
`Ω`의 첫째와 셋째 성분은 **완전히 중복(redundant)** — 이를 결합
invariant의 "두 성분"으로 쓰는 것은 정보량을 늘리지 않는다.

**repair accessibility**(가능한 repair transition 수, repair까지
최소 거리, 필요한 최소 shortfall, repair 후 남는 orbit slack)를
독립적인 넷째 성분으로 정의해 U4에 적용한 결과
(`FRAGMENT_REPAIR_OBLIGATION.md` §6 재사용):

| 상태 | repair transition 수(20k node 이내) | 최소 거리 | 필요 최소 shortfall | repair 후 orbit slack |
|---|---:|---:|---:|---:|
| 17a42b24ccfb | 11 | 3 | 0 | 22 |
| 1d8b48ab7d56 | 15 | 5 | 0 | 20 |
| 29f6af1e8aee | 14 | 5 | 0 | 20 |
| 86ec22eaaba4 | 12 | 3 | 0 | 22 |

**목표 명제("fragment-debt=1이면서 repair accessibility가 부족하면
완주 불가능")를 검증하기는커녕, 애초에 U4 전부에서 accessibility가
전혀 부족하지 않다(11개 이상의 witness, 거리 3~5, cost 0)** — 전제
자체가 U4에 적용되지 않으므로 이 명제는 **공허하게(vacuously) U4에
적용 불가능**이다. C20이나 다른 known legal state를 잘못 제거하는지
검증할 필요조차 없다 — U4 자체가 이미 이 obstruction의 대상이
아니기 때문이다.

## 정직한 결론

Ω는 실질적으로 **Φ와 orbit slack 두 개(이미 알려진, 독립인 것들)로
붕괴**하며, fragment debt·repair accessibility 성분은 (a) Φ와
중복이거나 (b) U4에서 obstruction으로 작동하지 않는 것으로 판명됐다.
**이번 라운드는 fragment-debt 계열의 obstruction을 만들려는 시도
전부(스칼라 debt, Θ 성분, repair-cost lemma, Ω 결합)가 U4에
적용되지 않는다는 일관된 결론에 도달했다** — 이는 하나의 큰 정직한
음성 결과이며, 개별적으로 우연히 실패한 것이 아니라 **fragment
자체가 애초에 U4의 진짜 obstruction이 아니기 때문**이라는 것을
여러 독립적 각도(직접 탐색, closed-form 항등식, 명제별 검증)에서
일관되게 확인했다.

## 성공 기준 (3) 재확인 — Ω 경로에서는 미달성, 하지만 다른 경로(zero-charge invariant)에서는 달성

이 문서 자체의 목표(fragment debt/Θ obstruction 증명)는 미달성이다.
그러나 `RA2_ZERO_CHARGE_HISTORY.md`에서 이미 별도로 성공 기준 (3)을
달성했으므로, 이번 라운드 전체로는 성공 기준을 충족한다.
