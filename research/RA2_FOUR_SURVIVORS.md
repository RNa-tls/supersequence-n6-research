# RA2의 4개 미해결 상태(U4) 대 20개 닫힌 상태(C20) — exact 비교

산출: `src/analyze_ra2_survivors.py` -> `outputs/ra2_24_comparison.json`,
`outputs/ra2_four_survivors.json`.

U4 = {`17a42b24ccfb...`, `1d8b48ab7d56...`, `29f6af1e8aee...`,
`86ec22eaaba4...`} (전부 Φ=5). C20 = 나머지 20개.

## 1. 24개 전 상태에 대한 exact 필드 비교

각 상태에서 R 직전/직후, A2 직전/직후 스냅샷(endpoint, current_hex,
fragment_hex="split hexagon"의 별칭 — 이 코드베이스에는 별도의
"split hexagon" 필드가 없음, `J_BRANCH_CLOSURE_STATUS.md` J5에서 이미
같은 결론에 도달했음을 확인 후 그 관례를 따름), P/F/S/H/O/D/N,
visited_count, Φ, 남은 orbit 수, non-full hexagon mask, legal ell=5
children 수, legal positive-charge children 수, pure-rotation-suffix
가능성을 전부 계산했다. **단순 상관관계 선언이 아니라 원인을 exact
transition 정의에서 추적한다** — 아래 각 항목은 `extend()`/`f1_normal_form`의
정의로부터 직접 설명된다.

### 핵심 발견: R과 A2 이벤트 자체가 U4 4개 전부에서 리터럴로 동일하다

```
R_event (4개 전부 동일): source_orbit_q=1,phase=4 -> target_orbit_q=0,phase=2,hex=18, weight=3
A2_event (4개 전부 동일): source_orbit_q=3,phase=3 -> target_orbit_q=1,phase=0,hex=1, weight=2
before_R endpoint (4개 전부 동일): (5,0,1,2,3,4)
after_R endpoint (4개 전부 동일): (2,3,4,0,1,5)
before_A2 endpoint (4개 전부 동일): (4,5,0,1,2,3)
```

**4개 상태의 유일한 차이는 R과 A2 사이에 끼어드는 zero-charge 이벤트의
개수(macro_distance 2 또는 3)와 그것이 건드리는, R/A2와 무관한 "다른"
orbit phase다.** `macro_distance_R_to_A2`: {17a42b24ccfb, 29f6af1e8aee}=2,
{1d8b48ab7d56, 86ec22eaaba4}=3. 정확히 이 여분의 zero-charge 조인트
하나가 P를 6→7로, visited_count를 30→36으로 올리면서(ell=5 회전 뒤에
발생하므로 Φ 항등식에 의해 Φ는 6→5로 변하지 않고 유지된다 — Φ(S')=Φ(S)+(ell-5)=Φ(S)+0) 4개 전부 Φ=5로 남는다.

### 이전 R/A2 이후 "before_A2"에서 버려지는 hex — U4 전부 5/6 완성

`before_A2.non_full_hexagon_masks`(A2가 버리기 직전, 현재 진행 중이던
hex): U4 4개 전부 mask 31(=0b011111, 6칸 중 5칸 방문, 단일 arc
`(0,4,5)` — 정확히 1칸만 미방문). C20은 mask ∈ {1,3,15}(1,2,4칸
방문)로 훨씬 덜 채워진 hex를 버린다. 이는 `A2_event`(source_phase=3,
직전 endpoint가 (4,5,0,1,2,3)) 자체가 리터럴로 동일하다는 사실의
직접 귀결이다 — **같은 A2를 쓴다는 것은 같은 hex를, 같은 채움
수준에서 버린다는 뜻이다.** 이 5/6 채움은 A2 이후
`after_A2_final.fragment_components = [[0,4,5]]`(길이-5 단일 arc, 즉
fragment debt=1)로 그대로 이어진다 — U4 4개 전부에서 fragment debt는
정확히 1이다.

### before_A2에서의 legal children 수도 U4 전부 동일 (그러나 C20과 겹치지 않음)

`before_A2.legal_macro_children_total`: U4=8(4개 전부), C20 ∈
{10,16,17,20}. `before_A2.legal_positive_charge_children`: U4=5(4개
전부), C20 ∈ {6,11,12,13,15}. 이는 endpoint/current_hex/fragment 구조가
리터럴로 동일하므로 그 지점에서의 국소 branching이 동일하다는 사실의
직접 결과다 — 새로운 우연이 아니라 이미 확인된 리터럴 동일성의 재확인.

## 2. U4가 서로 독립인가 — exact equivalence 판정

### 시도 1: 기존 left-S6 canonicalization

24개 모두 이미 서로 다른 canonical hash를 가진 상태로 코퍼스에
저장되어 있다 — 즉 기존 canonicalization은 이미 이 4개를 병합하지
않는다(당연히, 병합됐다면애초에 24개가 아니라 더 적은 수로 기록됐을 것).

### 시도 2: abstract depth-1 continuation 서명 비교 — 오해를 부르는 부분 일치

각 상태에서 `macro_edges()`가 낳는 모든 자식을 (rotation ell, weight,
abandonment, new_orbit, ΔP,ΔF,ΔS,ΔO,ΔD,ΔN)로 추상화한 멀티셋(orbit/hex
"이름표"는 제거하고 자원 변화량만 남김)을 비교했다:

```
17a42b24ccfb ~ 86ec22eaaba4  : depth-1 서명 완전 일치 (둘 다 macro_distance=2)
1d8b48ab7d56 ~ 29f6af1e8aee  : depth-1 서명 완전 일치 (둘 다 macro_distance=3)
그 외 모든 교차 쌍                : 불일치
```

**이 시점까지는 정확히 "2+2 family"처럼 보인다.**

### 시도 3: depth-2로 확장 — 시도 2의 부분 일치는 반증됨

같은 방식을 한 단계 더 깊이(각 자식의 자식들까지) 확장하자, **6개
쌍 전부에서 서명이 불일치한다** — depth-1에서 일치했던 두 쌍도 depth-2에서는
갈라진다. `outputs`에는 저장하지 않았지만(순수 진단), 이 비교는
`exact.ExactState`의 P/F/S/H/O/D/Ndef가 이름표(orbit/hex 인덱스)에
의존하지 않는 내재적 좌표이므로, 이 서명이 불일치한다는 것은 —
**두 상태 사이에 미래 legal-continuation-tree를 보존하는 어떤
동치(관계)도 존재할 수 없다는 것을 연역적으로 증명한다.** 어떤
재라벨링(left-S6, endpoint stabilizer, split/fragment role 보존, R/A2
source-target role 보존, exact visited-mask 보존 재라벨링 등 요청된
모든 후보 포함)이든, 완성까지 필요한 자원 좌표(P,F,S,H,O,D,Ndef)의
누적 경로는 보존되어야 하므로, depth-2에서 이미 갈라지는 두 상태는
그런 동치로 묶일 수 없다.

## 3. 최종 분류

**"4개의 독립 exact state"** — 요청된 5개 선택지 중 이것을 채택한다.
depth-1 부분 일치는 우연(자원-델타 멀티셋만 봤을 때의 우연적 겹침)이었고,
depth-2 검사로 반증됐다. "손실 없는 quotient 불가능"도 동시에
성립한다(사실상 같은 결론의 다른 표현) — 시도한 모든 후보
동치에서 4개를 2개 이하의 class로 묶는 손실 없는 quotient를 찾지
못했고, depth-2 불일치가 그것이 원리적으로 불가능함을 보여준다.

**증명 상태: 손증명** (depth-2 자원-델타 서명 불일치는 계산으로
검증됐고, 그 불일치가 동치 배제를 함의한다는 논증은 연역적).

## 4. 성공 기준 (2) 평가

"4개를 소수의 exact finite subcase로 완전 환원"은 **달성하지 못했다** —
정직하게: 4개는 서로 독립이며, 더 이상 줄어들지 않는다. 이는 실패가
아니라 명확한 부정적 결론이다 — 향후 이 4개는 각각 개별적으로
다뤄야 한다(`RA2_COMPLETION_OBSTRUCTION.md` §7 참조).
