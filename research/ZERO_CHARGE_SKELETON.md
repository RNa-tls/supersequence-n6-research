# Zero-charge 구조와 skeleton automaton

## 1. Zero-charge transition의 정체 — **증명됨**

`c=0`인 transition은 정확히 `ell=5`를 쓰는 것이다 — joint 종류는
`Z2_blocked_w2_existing`, `R_blocked_w3_existing`, `Z3_blocked_w3_new`
중 무엇이든 될 수 있다(§`SHORTFALL_BUDGET_THEOREM.md` §1). "zero-charge
joint 타입"은 없다 — zero-charge는 joint 앞의 rotation run이 우연히
(또는 그 상태의 구조상 필연적으로) 정확히 5번까지 충돌 없이 갈 수
있었다는 사실일 뿐이다.

## 2. 연속 zero-charge run의 길이 상한 — **증명됨(§`SHORTFALL_BUDGET_THEOREM.md`
§4로 이미 해결)**

**질문 자체가 잘못 제기됐다는 것이 답이다.** "zero-charge run이 무한히
이어질 수 있는가"라는 우려는 potential(Φ)이 아니라 **훨씬 기본적인
사실**로 이미 해결된다: 남은 전체 joint 수 \(n=TARGET_P-P\)가 유한하고
charge와 무관하게 매 joint마다 정확히 1씩 준다. 따라서 어떤
zero-charge run이든 길이는 최대 \(n\)이다(그 시점에 남은 전체 joint
예산). 별도의 C3/C4 group-theoretic 논증은 필요 없다.

## 3. 같은 E-orbit/incidence component로의 귀환 — **미결정**

zero-charge run이 이전에 사용한 것과 **같은 E-orbit이나 incidence
component로 돌아오는지**는 이번에 확인하지 않았다. 이는 Φ의 정의(오직
`P`, `visited_count`)에 전혀 등장하지 않는 정보이며, 확인하려면 각
zero-charge joint의 실제 target orbit 정체성을 추적해야 한다 — 산술이
아니라 기하이므로, 이번 작업 범위(potential 정식화)에서는 다루지
않았다.

## 4. C3/C4 군론과의 연결 — **반증됨 (불필요함이 증명됨)**

원 질문은 F=0 saturated 가지(맨 처음 연구 요약 §5.1의 카세트 사슬,
\(A^4=1\))의 group-theoretic 메커니즘이 이 F=1 zero-charge 구조에도
적용되는지를 물었다. §2에서 보였듯, zero-charge run의 길이 상한은
`P`-예산 하나로 완전히 설명되며 **어떤 group-theoretic 장치도 필요
없다.** 그 카세트-체인 메커니즘은 F=0(완전 카세트) 가지 고유의
현상이며, F=1의 이 특정 질문("run이 무한히 계속되는가")에는 적용할
필요가 없다는 것이 확인됐다 — 다만 이것이 F=1에서 group theory가
**전혀** 쓸모없다는 뜻은 아니다, 단지 "run 길이가 무한한가"라는 이
특정 우려에는 불필요하다는 것이다.

## 5. Skeleton automaton — **제한적으로 구현, 대부분 미결정**

지시된 추상 상태 \((\Phi, R\text{ 사용 여부}, \text{남은 orbit 수},
\text{split 상태}, \text{fragment 상태}, \text{phase deficit type})\)로
제한한 automaton을, 완전한 산출물로 만들지는 않았다. 이유:

- `Φ`, `R 사용 여부`, `남은 orbit 수`, `phase deficit type`은 이미
  `outputs/j_74_survivor_classification.json`과
  `outputs/j_capacity_45_seeds.json`에 상태별로 기록돼 있다(재사용
  가능).
- `split 상태`, `fragment 상태`를 이 추상 상태에 포함시키려 했으나,
  §`J_EXACT_NORMAL_FORMS.md`가 이미 보인 대로 **fragment/current
  component 모양만으로는 이후 legal continuation이 동형임을 보장하지
  못한다**(반례 75쌍). 따라서 이 automaton의 전이 규칙 자체가, exact
  state 전체를 참조하지 않고는 "이 추상 상태에서 이 전이가 합법인가"를
  정확히 답할 수 없다 — automaton을 만들어도 각 전이 옆에 "exact
  realization 여부: 미결정"이라고 적는 것 이상을 할 수 없다.

> **결론.** 순수 charge/자원 차원(§`SHORTFALL_BUDGET_THEOREM.md`)은
> 완전히 유한하고 닫혀 있다. 그러나 그 위에 fragment/split/component
> 차원을 얹은 "완전한" skeleton automaton은, 이미 증명된 lossy-quotient
> 사실(`J_EXACT_NORMAL_FORMS.md`) 때문에 **exact state 전체를 다시
> 요구하게 되어, 유의미한 압축이 되지 못한다.** 이는 negative result로
> 기록한다 — 강제로 automaton을 만들어 내지 않는다.
