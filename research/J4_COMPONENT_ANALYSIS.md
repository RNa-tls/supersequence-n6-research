# J4 후보: component/R 관계가 capacity loss를 강제하는가

원래 후보 J4: "J와 이후 R의 source/target component 관계가 incidence
forest에서 재사용 cycle 또는 capacity loss를 강제한다."

## 핵심 결과: capacity(Φ) 메커니즘은 R 사용 여부와 완전히 무관하다 — **증명됨**

`R_blocked_w3_existing`과 `Z2_blocked_w2_existing`을 비교하면:

| | ΔF | ΔS | ΔO | ΔP | ΔD | ΔN |
|---|---:|---:|---:|---:|---:|---:|
| `R_blocked_w3_existing` | 0 | 1 | 0 | +1 | -1 | +1 |
| `Z2_blocked_w2_existing` | 0 | 0 | 0 | +1 | -1 | 0 |

**`ΔP`가 둘 다 정확히 +1로 같다** (둘 다 weight>=2 joint 하나가 `P`를
1 늘리는 것뿐이며, weight 자체는 `Φ`에 들어가지 않는다 — `Φ`는 오직
`P`와 `visited_count`의 함수다, `J_CAPACITY_OBSTRUCTION.md` §1). 그리고
`Φ`의 단조성 항등식 `Φ(S')=Φ(S)+(ell-5)`은 joint의 **종류가 아니라
그 뒤에 오는 rotation run 길이 `ell`에만** 의존한다. 따라서:

> **정리 (R/Z2 orthogonality).** 어떤 스케줄에서 `R`을 `Z2`로(또는 그
> 반대로) 바꿔도, 그 스케줄의 `Φ` 궤적은 **한 치도 변하지 않는다**
> (같은 `ell` 시퀀스를 유지한다면). 유일한 차이는 `ΔN`(및 `ΔS`, 완주
> 시점의 D-무관 카운트)뿐이다.

이는 §`J_CAPACITY_OBSTRUCTION.md`에서 이미 증명·검증된 항등식의 즉각적
따름정리이며, 별도 증명이 필요 없다.

## 45개 capacity failure에서 R 사용 여부 분리 — **유한 완전 검증**

45개의 minimal failing continuation을 처음부터 재생해(`R`,`Z2`,`Z3`
분류) 확인한 결과:

- **28/45**: 실패 이전에 `R`을 최소 1회 사용.
- **17/45**: `R`을 전혀 쓰지 않고도 정확히 같은 방식(짧은 rotation
  run)으로 실패.

## 후보 C 판정: "R 사용/미사용에 따라 capacity failure 원인이 다르다"

→ **반증됨.** 위 정리와 실측 둘 다, R 사용 여부가 capacity 실패의
**원인이나 메커니즘을 전혀 바꾸지 않음**을 보인다 — 두 그룹 모두
정확히 같은 `Φ(S)+(ell-5)<0` 조건으로 실패했고, 그 조건 자체가 R의
존재를 언급하지 않는다. R은 capacity 문제에 대해 **완전히 orthogonal**
하다 — R이 실제로 중요한 곳은 별도의 N-예산(`J_COMPLETION_OBSTRUCTION.md`
정리 J-2)이지 capacity가 아니다.

## 후보 A, B, D 판정

**A. "J 이후 특정 component 재진입이 발생하면 남은 신규 orbit demand를
충족할 수 없다."** → **미결정, 그리고 불필요해 보임.** 45개 전부의
실제 실패 원인(§`J_CAPACITY_OBSTRUCTION.md` §5)은 순수 rotation-length
산술이었다 — orbit demand 자체(`remaining_new_orbits_needed`, 45개
전부에서 기록됨)는 실패 시점까지 도달 불가능해진 적이 없다(`Z3` 개수
요구치는 `insufficient_future_orbit_opening_credit`류 별도 prune이며,
45개의 관측된 prune 사유는 전부 `remaining_cover_capacity_impossible`
하나뿐이었다 — 다른 prune 사유는 이 45개의 minimal failing path에서
전혀 나타나지 않았다). 즉 component 재진입에 의한 orbit demand 부족은
**이 45개를 설명하는 데 필요하지 않다** — 있을 수도 있지만, 관측된
현상이 아니다.

**B. "split hexagon이 특정 phase 상태일 때 J 이후 남은 cover capacity가
1 부족하다."** → **미결정.** `fragment_hex`/`fragment_components`를
45개 전부에서 기록했지만(`outputs/j_capacity_45_seeds.json`), 이들과
`phi_at_witness` 사이의 직접적 함수 관계는 확인하지 않았다 — `Φ`는
fragment 정보를 전혀 참조하지 않는 정의(`P`, `visited_count`만 사용)이므로,
"split hexagon phase가 Φ를 결정한다"는 주장은 있다면 **간접적**(예:
어떤 fragment 모양이 통계적으로 낮은 Φ와 상관되는지)일 텐데, 이번에는
그 상관을 계산하지 않았다.

**D. "capacity failure 직전에는 특정 orbit 또는 hexagon이 두 역할을
동시에 요구한다."** → **미결정, 근거 없음.** `Φ`의 정의와 항등식
어디에도 "두 역할" 개념이 들어가지 않는다 — 실패는 순전히 스칼라 자원
부족이지, 특정 orbit/hexagon의 이중 역할 충돌이 아니다. 이 후보를
지지할 메커니즘을 찾지 못했다.

## 결론

J4(component 기반)는 **45개의 capacity failure를 설명하는 데 필요하지
않다** — 훨씬 단순한, component와 무관한 `Φ` 산술(§`J_CAPACITY_OBSTRUCTION.md`)
이 45개 전부를 완전히, 예외 없이 설명한다. 후보 C는 명시적으로
반증됐다. A, B, D는 반증되지도 필요하지도 않은 상태로 미결정으로
남는다 — 있다면 그것은 이번에 발견한 것과는 **별개의** 장애물일
것이다.
