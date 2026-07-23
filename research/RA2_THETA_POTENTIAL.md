# Θ potential 개발 시도 — 정직한 부분 결과

산출: `outputs/ra2_theta_transitions.json` (24개 RA2 최종 상태에서
depth=1 legal continuation 전체에 대한 move-kind별 Φ/orbit slack/phase
slack 변화량 표) 및 `outputs/ra2_fragment_debt.json`(via
`src/verify_fragment_debt.py`).

## 후보 벡터와 각 성분의 상태

요청된 출발 벡터 `Θ(S) = (Φ(S), orbit slack, fragment slack, split slack, phase slack)`를
성분별로 검토했다. **전체 U-branch에 통하는 강제 통합을 시도하지
않고, RA2 corpus(24개 상태 + 그 얕은 후속 상태들)에서 실제로 검증
가능한 것만 보고한다.**

### Φ(S) — 이미 증명됨, 재검증만

기존에 증명된 정리(`J_STATE_SPACE_REDUCTION.md`,
`analyze_j_capacity_failures.py`): `Φ(S') = Φ(S) + (ell-5)`, 항상
비증가. RA2에도 그대로 적용되며 새로 증명할 것이 없다.

### orbit slack = TARGET_O − O(S) — 단조 비증가하지만 이 depth에서 무력함

O(S)는 weight>=2 조인트가 새 orbit을 열 때만 증가하고(`new_orbit`
플래그), 절대 감소하지 않으므로 orbit slack은 자명하게 단조
비증가다. 그러나 RA2의 24개 상태 모두 O=3(TARGET_O=25이므로 slack=22)로,
이 얕은 depth에서는 slack이 0 근처에 전혀 오지 않는다 — 기존에 이미
별도로 구현된 `O_exceeded` prune과 비교해 **이 depth에서는 추가
가지치기 능력이 없다.** 더 깊은 depth에서는 유용할 수 있으나 이번
범위(U4, depth<=18 이미 시도)에서는 확인되지 않았다.

### fragment slack (= −d_frag) — 단조성 미해결 (제한 실험, 미완료로 표시)

`FRAGMENT_DEBT_LEMMA.md` §1에서 증명한 "F=1 이후 blocked-only" 하위
정리로부터, fragment를 다시 current로 만드는 조인트(target이
fragment_hex 안)가 발생할 때 이전 current가 아직 미완성 상태로 남아
**새 fragment**가 되는 "swap" 케이스가 `f1_normal_form`의 단일-fragment
제약상 legal할 수 있음을 분석적으로 확인했다 — 이 경우 새 fragment의
debt는 이전 fragment의 debt와 무관하게 클 수도, 작을 수도 있어
보인다(원리적으로). **그러나 RA2 24개 seed 전부에서 depth<=4,
seed당 edge_cap=8,000 범위 안에서는 이런 swap이 실제로 d_frag를
증가시키는 사례를 한 건도 찾지 못했다.** 즉:

- **단조 비증가라는 증명은 얻지 못했다** (swap 메커니즘이 이론적으로
  존재하므로).
- **반증도 얻지 못했다** (제한 탐색에서 반례가 나오지 않았다).

이 성분은 **미완료**로 남긴다 — 증명되지도 반증되지도 않았다고
정직하게 기록한다.

### split slack — fragment slack과 동일 취급 (별도 개념 없음)

`RA2_FOUR_SURVIVORS.md` §1에서 확인했듯 이 코드베이스에는 별도의
"split hexagon" 개념이 없다. fragment slack과 동일하게 취급되므로
별도 성분으로 다루지 않는다.

### phase slack (= 6 − popcount(current hex mask)) — depth<=4에서 반례 없음, 미완료

fragment slack과 동일한 실험 방법으로 24개 seed × depth<=4 ×
edge_cap 8,000에서 증가 사례를 찾지 못했다 — 그러나 fragment slack과
같은 이유로 일반 단조성은 증명하지 못했다. **미완료.**

## 순서대로 검사한 4단계 결과

1. **Componentwise monotonicity**: Φ, orbit slack만 증명됨. fragment/phase
   slack은 미해결(반증 아님, 증명도 아님).
2. **Lexicographic monotonicity**: (Φ, orbit_slack) 사전식 벡터는
   자명하게 안전하지만(둘 다 개별적으로 단조 비증가), **기존에 이미
   개별 prune으로 구현된 것 이상의 새 가지치기 능력을 이 depth에서
   보여주지 못했다** — U4의 미해결 상태 4개 전부 orbit_slack=22로 전혀
   binding하지 않는다.
3. **Cone invariant**: fragment/phase slack의 단조성이 미해결이므로
   이를 포함하는 cone은 검증할 수 없다.
4. **안전한 선형 결합**: Φ와 orbit_slack만으로 만든 선형 결합
   `α·Φ + β·orbit_slack`(α,β>0)을 U4의 4개 상태에 대해 시험했으나,
   두 성분 모두 U4에서 여유가 크므로(Φ=5, orbit_slack=22) 어떤 양의
   계수 조합도 0 미만으로 떨어뜨리지 못한다 — **이 depth에서는
   무력하다.**

## 5. RA2 전용 potential — 시도했으나 채택 가능한 것 없음

요청은 "RA2 전용 potential도 유효한 성과"라고 명시했다. 이번 라운드에서
RA2 전용으로 시도한 것은 fragment slack/phase slack이었으나, 둘 다
단조성을 증명하지 못해 **potential로 채택할 수 없다.** `Φ` 자체가
이미 RA2에 적용된 유일하게 증명된 potential이며(J-branch에서 재사용),
이번 라운드는 그보다 강한 것을 새로 얻지 못했다.

## 성공 기준 (3) 재확인 — Θ 경로로도 미달성

`FRAGMENT_DEBT_LEMMA.md`에 이어, 이 문서도 "fragment debt 또는 Θ
obstruction 증명"이라는 성공 기준을 Θ 경로로도 달성하지 못했음을
정직하게 기록한다. 대신 두 가지 진짜 성과를 남긴다: (1) F=1 이후
blocked-only라는 증명된 하위 정리, (2) d_frag=1이 U4 전부를 정확히
식별한다는 24/24 관측(§`FRAGMENT_DEBT_LEMMA.md` §3).
