# i_min(A2)=4 — 네 번째 라운드에서도 완전한 lower-bound 증명은 미완료

## 7+8. 시도와 정직한 실패 보고

`A2_ELL_FORCING_HISTORY.md`의 `H_A2(S)`를 이용해 lower bound를
시도했다. 목표는: index `k < 4`에서 도달 가능한 **모든** 상태
`S`(zero-charge joint `k`개로 도달)에 대해, `S.p`가 유도하는 6개
candidate orbit `{q(0),...,q(5)}` 중 어느 것도 그 시점까지의
orbit-history(크기 `k+1` 이하)와 겹치지 않음을 **BFS 없이** 보이는
것이었다.

**막힌 지점**: `q(0),...,q(5)`는 `S.p`(즉 index `k`까지의 구체적
경로가 착지한 정확한 위치)에 의해 결정되는데, index `k`에서
도달 가능한 `S.p`의 전체 집합을 **BFS 없이** 특정하려면 이
모델의 E-orbit 액션(`core.E`)과 hexagon 액션(`core.SIGMA`) 사이의
정확한 group-theoretic 관계(어느 tail action이 어느 원소를
생성하는지)를 알아야 한다 — 이는 레거시 코드(`superperm_port_lift.py`)의
심층 구조이며, 이번 라운드에서 그 수준까지 역공학하지 못했다.

**정직한 결론**: 이번(4번째) 라운드도 `i_min(A2)=4`의 완전한
연역적 lower-bound 증명을 만들지 못했다. 확보한 것은:

- **Upper bound(exact witness)**: index 4에서 legal한 구체적
  상태 존재(수 라운드에 걸쳐 반복 확인, 유한 완전 검증).
- **Lower bound(exhaustive BFS)**: index 0,1,2,3에서 legal한 상태가
  전혀 없음을 **bounded exhaustive search**로 확인(`A2R_MINIMUM_DEPTH.md`,
  frontier 완전 소진) — 이는 증명이지만, 요청된 "BFS가 아닌
  transition-level dependency theorem"의 형태는 아니다.

**abstract over-approximation 시도**: "index `k`에서 존재하는
orbit-history 크기는 최대 `k+1`"이라는 사실만으로 lower bound를
얻으려 했으나, 이것만으로는 "6개 candidate 중 어느 것도 그 `k+1`개
안에 없다"를 보장할 수 없다(over-approximation이 너무 느슨해
안전하지만 무용하다 — `k+1`개의 궤적이 정확히 어떤 orbit들인지
알아야 진짜 논증이 되는데, 그 정보 자체가 BFS의 산출물이다). 이
시도는 실패로 정직하게 기록하며, 억지로 "증명됨"이라 부르지
않는다.

## 성공 기준 (3) 평가

"i_min(A2)=4의 deductive lower-bound proof"는 **4개 라운드
연속으로 미달성**이다. Exhaustive search 기반 증명(유한 완전
검증)은 확고하지만, 요청된 순수 연역적(BFS-독립적) 형태는 이
프로젝트가 가진 도구와 시간 안에서 얻지 못했다 — 이 사실을
숨기지 않고 그대로 기록한다.
