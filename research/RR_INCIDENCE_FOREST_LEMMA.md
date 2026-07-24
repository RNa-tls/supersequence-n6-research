# Incidence forest lemma — RR 4,470개 전체 유한 완전 검증, 일반 그래프 정리는 아님

산출: `src/analyze_rr_chaining.py`(`component_map`이 `redundant` union
횟수를 함께 반환하도록 구현), 직접 집계(아래 §1) — 5개월 밖 재실행
없이 이번 라운드에서 이미 복구한 `outputs/rr_literal_witnesses.json`
(4,470/4,470) 재사용.

## 결론 먼저

> **RR 4,470개 전체의 macro_path를 raw 프레임으로 재생하며, 매
> pre-joint/post-joint 상태(총 53,054개 상태)마다 incidence
> union-find를 처음부터 재구성했을 때, "redundant union"(이미 같은
> root인 두 노드를 다시 합치려는 시도, 즉 사이클을 닫는 edge)은
> **단 한 번도** 발생하지 않았다(0/53,054).** 더 넓게는, 이번
> 라운드에서 별도로 복구한 depth<=6 전체 BFS 노드(85,238개, RR뿐
> 아니라 J/기타 word 전부 포함)에서도 0건이었다.

## F1-F4 후보 판정

### F1: "same-component non-chaining은 component 내부에 두 개의
독립 existing-target edge를 요구한다."

**참, 손증명(집합론적으로 자명)**: union-find에서 두 노드가 같은
root를 가지려면 그 둘을 연결하는 경로가 union 호출들로 이미
존재해야 한다. `RR_SAME_COMPONENT_CHAINING_THEOREM.md` §5가 보인
바와 같이, R2 자신의 source/target이 같은 component에 속하려면
(a) source 쪽 orbit이 어떤 hexagon(관측된 코퍼스에서는 항상 hex 0)에
등록되어 있어야 하고, (b) target 쪽 orbit도 **같은** hexagon(또는
그 component 내 다른 노드)에 등록되어 있어야 한다 — 이는 정확히
"두 개의 독립 existing-target edge"(R2의 source 등록 edge, target
등록 edge)가 **공통 하나의 hexagon 노드를 공유**해야 함을 뜻한다.

### F2: "그 두 edge는 forest에서 cycle을 만든다."

**거짓, 정확히 반대다 — 반증됨.** 두 edge가 **같은** 공유 노드(hex
0)로 수렴하는 것은 **STAR(허브) 구조**이지 cycle이 아니다 — hex
0을 중심으로 여러 orbit이 방사형으로 매달리는 트리 형태이며, union-find
관점에서 이는 매번 **서로 다른 두 트리를 병합**하는 정상적인
forest-growing 연산이다(따라서 §1에서 확인한 대로 redundant union이
0건인 것과 정확히 일치한다). **cycle이 생기려면** 오히려 **같은
두 노드가 (하나가 아니라) 두 개의 서로 다른 경로로 이미 연결된
후에 세 번째 edge가 그 둘을 또 이으려 하는 경우**가 필요하다 — 이는
F1이 기술한 상황과는 다른, 훨씬 드문 사건이다. **F2는 F1을 오해한
후보이며, 실제로는 same-component가 정확히 forest를 "키우는"(cycle을
만들지 않는) 방식으로 발생한다는 것이 이번 라운드의 핵심 발견이다.**

### F3: "cycle을 피하려면 second R가 first R chain을 따라야 한다."

**부분 참, 재구성 필요**: cycle을 "피하는" 것이 목적이 아니라(F2가
반증됐듯 same-component 자체가 cycle을 만들지 않는다), 오히려
**"짧은 word 안에서 같은 component에 도달하는 유일하게 관측된
경로가 hex-0 hub를 거치는 것"**이라는 사실이 맞다. 이는 "second
R가 first R chain을 따라야 한다"는 것과 **논리적으로 동치는
아니다**(§5의 반례: `989d2261b4`는 R2가 R1의 정확한 phase가 아니라
R1 이후의 **다른** 등록 경로를 탄다) — 다시 표시: **F3은 관측된
현상을 대략적으로 가리키지만 정확한 정식화는 아니다. 미완료.**

### F4: "non-chaining second R는 새로운 root를 필요로 하므로
same-component와 모순된다."

**참, 그러나 이유가 F4가 말하는 것과 다르다**: non-chaining인데
same-component인 사례가 전무한 것(0/4,470)은 "새 root가 필요해서
모순"이라기보다, **"이 코퍼스(depth<=6)에서 관측되는 유일한 병합
메커니즘(hex-0 hub)은 항상 chaining되는 orbit(즉 R1의 target을
그대로 재사용하는 orbit)을 통해서만 발생했기 때문"**이다 — 이는
경험적 사실이며, "새 root 요구"라는 것이 일반적으로 참인지는
증명하지 못했다(§8의 abstract countermodel이 그 반대 가능성을
그래프 수준에서 명시적으로 구성한다).

## 정직한 최종 판정

**포레스트 성질 자체는 4,470개 RR 코퍼스(및 광범위한 depth<=6
샘플 85,238개) 전체에서 예외 없이 성립한다 — 유한 완전 검증.**
그러나 이것이 **순수 그래프 공리**(bipartite, 5/6-regular
degree, forest)만으로 강제되는 일반 정리는 **아니다** —
`RR_ABSTRACT_COUNTERMODEL_STATUS.md`가 정확히 같은 차수 제약을
지키면서도 cycle 없이(forest를 유지하면서!) same-component +
non-chaining을 만드는 abstract 모델을 구성한다(그 모델은 F1의
"두 edge가 하나의 공유 노드로 수렴"이라는 조건 자체는 만족하지만,
그 공유 노드가 R1의 target이 **아닌 다른** orbit(C)의 hex라는
점에서 실제 corpus와 다르다). 즉: **forest 성질 자체와 "same
⟹ chaining"은 서로 다른 두 개의 사실이며, forest 성질만으로
"same ⟹ chaining"이 함의되지 않는다 — 후자는 hex-0의 특별한
사전등록 지위(초기 상태부터 등록된 유일 노드)라는 permutation-level
사실에 추가로 의존한다.**
