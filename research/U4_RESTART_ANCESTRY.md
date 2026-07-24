# U4의 critical restart, ancestry invariant, 최소 causal difference

## 6. Critical restart — U4는 정확히 하나의 restart에 의존한다

`U_BRANCH_RESTART_BLOCKS.md`의 block decomposition을 재사용한다.
U4 4개 상태는 word-block 수가 다르다(2개는 m=1, 2개는 m=2) — 그러나
**m=1과 m=2 U4 둘 다 정확히 같은 최종 A2 boundary(같은 endpoint,
같은 A2 event)에 도달한다**(`RA2_FOUR_SURVIVORS.md`에서 이미 확립).
이는 다음을 의미한다:

> **m=2 U4의 첫 block("Z2, R의 orbit 재사용")은 최종 결과에 대해
> 선택적(optional)이다 — 제거해도(m=1 U4처럼) 같은 A2 boundary에
> 도달한다. 반면 마지막 block("Z3, fresh orbit 138")은 U4 4개
> 전부에 예외 없이 나타나며, 이것이 critical restart다.**

**목표 질문에 대한 답**: "U4는 정확히 하나의 특정 restart에
의존하는가?" → **그렇다 — "Z3, fresh orbit(코퍼스에서 일관되게
q=138로 관측), component 미해결" 유형의 단일 restart가 critical
하다.** (주의: orbit index "138" 자체가 본질적으로 의미 있는
숫자라기보다 canonicalization 관례의 산물일 수 있다 — 본질은 "R과
incidence 상 무관한 새 orbit을 여는 weight-3 restart"라는 유형이다.)

"U4는 C20보다 더 긴 prerequisite chain을 갖는가?" → **아니다,
길이가 아니라 유형이 다르다.** m=1 U4(2개)는 C20의 전형적
m=1(9개)과 **정확히 같은 길이(1 block)**이지만 그 block의 유형이
다르다(fresh-138 대 existing-reuse-0).

## 7. Restart ancestry invariant Ξ_A — 시도, 완전한 강화는 미완료

각 orbit의 "누가 처음 열었는가"를 추적했다: R이 연 orbit(q=0),
그리고 word block들이 여는 orbit들(C20: 없음 또는 q=0 재사용; U4:
q=0 재사용(optional) + q=138(critical)). A2의 target orbit(q=1,
`RA2_FOUR_SURVIVORS.md`에서 이미 확인)은 **R이 연 orbit(0)도, word
block이 연 orbit(138)도 아닌 제3의 orbit**이다 — A2 자신의 target은
이 ancestry 사슬과 직접 연결되지 않는다(`RA2_ORBIT_REUSE_CHARGE.md`
H2a/H2b의 반증과 일치하는 패턴: A2/repair 모두 R 자신과 직접
연결된 orbit을 사용하지 않는다는 것이 이 연구 전반에서 반복
확인된다).

**R-A2 최소 공통 조상(LCA)**: R의 target(q=0)과 A2의 target(q=1)은
union-find 상 **연결되지 않는다**(A2 발동 시점에 A2 자신의
source(q=3)조차 등록 안 됨, `RA2_ORBIT_REUSE_CHARGE.md` H2b) — LCA
자체가 존재하지 않는다(서로 다른 컴포넌트).

**정직한 결론**: 벡터 `Ξ_A = (A2 source ancestry depth, A2 target
ancestry depth, R–A2 LCA, component-root reuse)`의 개별 성분을
계산할 수는 있었지만, 이를 U4/C20을 가르는 **일반적** invariant로
강화하는 데는 이르지 못했다 — U4/C20을 실제로 가르는 것은 여전히
§6의 critical restart 유형(fresh-138 대 existing-reuse-0)이며, 이는
이미 `U_BRANCH_RESTART_BLOCKS.md`에서 다뤘다. **미완료**로 표시.

## 8. U4의 최소 causal difference — outlier와의 교차검증

U4의 m=1 두 상태(`17a42b24ccfb`, `29f6af1e8aee`)와 가장 가까운
"restart-block word" 이웃은 **C20의 outlier `e2b44997e783`**다 — 이
상태의 마지막 word-block도 정확히 "Z3, fresh orbit 138, component
미해결"이다(`U_BRANCH_RESTART_BLOCKS.md`에서 이미 확인). 차이:

- `e2b44997e783`은 word-block이 4개(추가로 3개의 다른 fresh-orbit
  block), U4는 1~2개.
- **결정적 차이: `ell_A2`가 다르다**(e2b44997e783: 0, U4: 4).

**이 하나의 수정(ell_A2를 0에서 4로 바꾸는 것 — 즉 A2 발동 전
rotation을 4회 더 하는 것)이 debt를 5→1로, Φ를 1→5로, 그리고
capacity-failure 발견 여부를 True→False(미해결)로 바꾼다** — 이는
**이전 라운드에서 이미 확립된 사실의 재확인**이지, 이번 라운드의
restart-block 분석이 발견한 새로운 causal factor는 아니다. 정직하게:
이번 라운드의 block 분석은 **U4의 "준비 구조"가 C20과 체계적으로
다르다는 새 사실**(§6)을 보탰지만, **최종 capacity-failure 여부를
가르는 causal candidate는 여전히 ell_A2 하나뿐**이라는 이전 결론을
뒤집지 못했다.

## 성공 기준 (3) 평가

"U4와 C20을 가르는 restart-block 또는 ancestry invariant"는
**restart-block 층위에서 달성됐다**(§6의 critical restart 유형 —
U4 4개 전부의 exact, 예외 없는 공통점) — 다만 이것이 ell_A2를
대체하는 새로운 독립 causal factor는 아니고, ell_A2와 강하게
공기(共起)하는 **부수적이지만 정확한 구조적 서명**이다. ancestry
invariant(§7) 강화는 미완료로 남는다.
