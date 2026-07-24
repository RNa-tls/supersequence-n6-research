# Critical-restart ancestry, 왜 ell_A2=4인가, 5-state tree 비교, escape-transition lemma

## 4. Ancestry theorem 후보 C1–C4

Five-state 데이터(R target=0, critical restart target=138, A2
source/target: U4는 (3,1), outlier는 (0,120))로 직접 판정한다.

| 후보 | 정확한 명제 | 판정 |
|---|---|---|
| **C1** | critical restart orbit(138)이 A2 source orbit의 직접 parent다 | **반증됨** — U4의 A2 source는 orbit 3이지 138이 아니다(리터럴 불일치, 최소 반례: `17a42b24ccfb`) |
| **C2** | critical restart가 A2 legality에 필요한 weight-2 overlap을 처음 생성한다 | **미완료** — "weight-2 overlap"을 이 코드베이스의 어떤 기존 필드로 정확히 정의할지 결정하지 못해 검정을 구성하지 못했다 |
| **C3** | unrelated restart는(reuse 대비) A2 source-target component LCA를 하나 증가시킨다 | **미완료** — `RA2_ORBIT_REUSE_CHARGE.md`(이전 라운드)에서 이미 A2 자신의 source orbit이 그 시점에 union-find에 전혀 등록돼 있지 않음(unresolved)을 확인했다 — "LCA"라는 개념 자체가 등록되지 않은 노드에는 적용되지 않는다 |
| **C4** | unrelated critical restart 뒤 ell_A2=4가 선택되면 특정 ancestry edge가 repair되지 않은 채 남는다 | **참, 하지만 이미 알려진 사실의 재진술** — ell_A2=4가 만드는 debt=1(fragment)이 바로 그 "repair되지 않은 edge"이며, 이는 `RA2_ZERO_CHARGE_HISTORY.md`에서 이미 확립된 Φ=6-debt 항등식과 동일한 내용이다 |

**정직한 결론**: C1–C4 중 어느 것도 새로운 독립적 ancestry 구조를
발견하지 못했다 — C1은 반증됐고, C2/C3는 정의 부재로 미완료,
C4는 이미 알려진 사실의 재진술이다.

## 5. 왜 ell_A2=4인가 — **강제됨, 선택이 아니다(손증명, 5개 상태 전부 확인)**

`RA2_FIVE_STATE_COMPARISON.md`의 ell-sweep 결과: **critical
restart 직후 지점에서 ell=0..5 전부를 조사했을 때, 각 상태마다
legal한 A2 옵션은 정확히 1개뿐이며, 그 ell 값은 상태별로 고정돼
있다** —

- U4 4개 전부: **ell=4에서만** A2가 legal(다른 5개 ell 값 전부에서
  0개).
- outlier: **ell=0에서만** A2가 legal(다른 5개 ell 값 전부에서
  0개).

**이는 "witness가 우연히 ell=4를 선택했을 뿐"이라는 가설을
반증한다** — U4의 경우 ell=4가 **유일하게 legal한 선택지**이므로
선택의 여지가 없었다. 동시에 **"critical restart가 만든 boundary
때문에 사실상 강제된다"는 가설도 정확히는 아니다** — critical
restart 자체는 outlier와 리터럴로 동일한데도 강제되는 ell 값은
다르다(4 대 0). **진짜 강제 요인은 critical restart "그 자체"가
아니라, critical restart에 도달하기까지의 누적 orbit-touch
이력(outlier는 3개의 추가 준비 block을 더 거침, `U_BRANCH_RESTART_BLOCKS.md`)이다.**

## 6+7. Five-state continuation tree 비교 및 escape-transition lemma

`outputs/ra2_five_state_tree_comparison.json`(depth<=6, edge_cap
30,000/상태)에서 `remaining_cover_capacity_impossible`(Φ 기반
prune) 발생 횟수를 depth별로 집계했다:

| 상태 | depth 0 | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|---:|
| U4(4개 전부) | 0 | 0 | 0 | 0 | 0 | 0 |
| outlier | 0 | 0 | 0 | 0 | **3** | **1** |

**U4 4개 전부는 이 depth 범위 안에서 단 하나의 capacity-failure도
보이지 않는 반면, outlier는 depth 4에서 처음 3개, depth 5에서
1개 더 나타난다.** 이는 이미 알려진 사실(Φ=5 대 Φ=1)의 직접적
결과이며, 새로운 메커니즘은 아니다 — 그러나 **"identical critical
restart"라는 통제된 비교 안에서 이 차이를 직접 재확인**했다는
점에서 의미가 있다.

### Escape-transition lemma (요청된 형태로 정식화)

> **동일한 critical restart(unrelated fresh orbit 138 개방) 뒤에
> ell_A2=4를 선택하면, 그 결과 상태는(적어도 depth<=5, edge_cap
> 30,000 범위 안에서) 기존 Φ 기반 capacity-failure prune을 전혀
> 만나지 않는다 — 반면 동일한 critical restart 뒤 ell_A2=0을
> 선택하면 depth 4에서 이미 3개의 prune을 만난다.**

**증명 상태: 제한 실험(bounded, 5개 상태에 대해서만, depth<=6까지만
확인)** — 이 lemma는 완주 obstruction이 아니라(요청이 명시했듯),
"왜 U4만 기존 prune을 피하는가"에 대한 정량적 서술이다. 근본
원인은 여전히 Φ=1+ell_A2 항등식이며, 이 lemma는 그것을 5-state
통제 비교로 재확인한 것이지 새로운 독립 메커니즘은 아니다.

## 성공 기준 (2), (3) 평가

"U4와 C20 outlier를 가르는 causal boundary theorem"(2)은
**부분 달성** — 최소 차이는 정확히 ell_A2 하나로 좁혀졌고(§`RA2_FIVE_STATE_COMPARISON.md`),
그 ell_A2 자체가 각 상태에서 유일하게 legal한 값(강제, 선택
아님)임을 증명했다(§5). 하지만 "왜 누적 이력이 다른 ell을
강제하는가"에 대한 완전한 인과 사슬은 미완료로 남는다.
"escape-transition lemma"(3)은 **제한 실험 수준에서 달성**됐다.
