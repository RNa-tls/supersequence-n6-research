# A2 최소 index 4의 prerequisite 구조

## 5. 왜 A2는 정확히 index 4가 최소인가

`A2R_MINIMUM_DEPTH.md`(이전 라운드)와 이번 라운드의 재확인:
**A2(weight=2, abandonment, existing target)가 walk의 첫 counted
사건으로 등장 가능한 최소 macro-index는 4다(depth 5).** 이번
라운드에서 같은 방법으로 **J(weight=3, abandonment, existing
target)의 최소 index는 1**(depth 2)임을 추가로 확인했다 — 두
"existing-target abandonment" 이벤트(A2, J) 사이에도 **weight에
따라 큰 차이(4 대 1)**가 있다.

### Prerequisite chain (관측된 구조, 정식 DAG 증명은 부분적)

진짜 초기 상태(orbit_masks에 1개 orbit만 touched)에서: **"existing
target"이 가능하려면 그 target orbit이 이미 touched돼 있어야
한다.** 초기에는 touched orbit이 1개뿐이므로, existing-target
이동이 가능하려면 그 하나의 orbit으로 다시 돌아오는 매우 특수한
tail action이 필요하다 — 이것이 존재하는지는 순수하게 weight별
tail-action 집합의 조합론적 사실이다:

- weight=3 tail action 집합은 이미 초기 상태에서 R(existing,
  blocked)이 ell=5(hex full) 이후 legal해지는 것을 허용한다.
- weight=3의 "existing+abandon"(J)은 index 1에서 가능 — 단 1개의
  선행 zero-charge 준비만으로 충분.
- weight=2의 "existing+abandon"(A2)은 index 4까지 필요 —
  **weight=2 tail action 집합이 "이미 touched된 orbit으로 되돌아가는"
  경우의 수가 weight=3보다 훨씬 적다**는 조합론적 사실을 시사한다
  (직접 증명하지 않음, §9의 전체 표에서 일관되게 관측되는 패턴으로
  뒷받침되는 **추측**).

**"최소 chain 길이가 왜 4인가"에 대한 완전한 연역적 증명(정확히
왜 3이 아니고 4인지, group-theoretic하게)은 이번 라운드에서
얻지 못했다 — depth<=4까지 bounded 탐색으로 A2가 legal하지 않음을
전량 확인했고(exhaustive, `A2R_MINIMUM_DEPTH.md`의 재확인), depth
5에서 처음 legal해짐을 witness로 확인했다(**유한 완전 검증** +
**exact witness**), 하지만 "왜 정확히 4"라는 group-theoretic 설명은
**미완료**로 남긴다.

### depth-6 A2R witness가 유일한 이유

A2R = [A2 준비 최소 depth 5] + [R 자신의 macro-edge, 최소 1] = 6.
`RA2_A2R_EXCHANGE_THEOREM.md`에서 이미 확인했듯 A2 이후 R은 A2의
착지 hex를 그대로 사용해(추가 준비 0) legal해진다 — 따라서 depth
6이 최소이고, 그 depth에서의 witness가 유일한 이유는: **depth 5에서
A2가 legal해지는 경로 자체가 (bounded 탐색 결과) 정확히 1개
canonical class뿐이기 때문**이다(`outputs/a2r_search.json`,
`a2_only_states_found: 1`, 이전 라운드에서 이미 확인).

### RA2에서는 R이 어떤 prerequisite를 대신 충족하는가

R 자신이 "existing target"(weight=3)을 필요로 하므로, **R이 먼저
발동한다는 것 자체가 이미 최소 1개의 orbit-existing 조건을
증명한 셈이다** — 하지만 A2(weight=2)의 existing-target 요구는
R이 만든 조건과 **독립적**이다(§`RA2_ORBIT_REUSE_CHARGE.md`에서
이미 확인: repair가 A2 자신의 target/source orbit을 재사용하지
않는 것과 같은 패턴). 즉 R이 A2의 prerequisite를 "대신" 충족해
주지 않는다 — 그럼에도 RA2가 A2R보다 훨씬 이른 depth(5~6)에서
A2에 도달하는 이유는, **R 이전과 R-A2 사이에 발생하는
zero-charge 준비 joint들이 A2R에서 A2 스스로 필요로 하는 것과
동일한 종류의 준비(여러 orbit touch)를 우연히 병행 제공하기
때문**이다 — RA2와 A2R이 서로 다른 겉보기 구조임에도 내부적으로는
"A2가 필요로 하는 준비량"이라는 같은 병목을 공유한다는 것을
시사한다(**추측**, 완전히 증명하지 않음).

### U4에서는 prerequisite DAG가 C20과 다른가

**그렇다 — `U_BRANCH_RESTART_BLOCKS.md`에서 확인한 정확한 패턴**:
U4는 A2 직전에 "R의 orbit과 무관한 fresh orbit(138)을 여는" 준비
단계를 반드시 거치는 반면, 전형적 C20(9개)은 "R의 orbit을 그대로
재사용"하는 준비만으로 충분하다. 이는 **U4가 C20보다 더 다양한
orbit-touch 이력(R의 orbit + 별도의 fresh orbit)을 만든 뒤에야
A2가 legal해진다는 것**을 보여준다 — 준비 DAG의 노드 수 자체가
다르다는, 정성적이지만 정확한 차이다.

## 성공 기준 (1) 평가 — 부분 달성

"A2 최소 index 4를 설명하는 prerequisite DAG 정리"는 **정성적으로는
달성**(J와의 비교, weight별 tail-action 조합론 차이라는 그럴듯한
원인, U4/C20 준비 구조 차이)했으나, **완전한 연역적 DAG 증명(정확히
"4"라는 숫자를 group-theoretic하게 도출)은 미완료**로 정직하게
남긴다.
