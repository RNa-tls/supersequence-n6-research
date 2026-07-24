# First R의 component 변화, same-component 후보 열거, R-사이 word의 역할, completion corollary

산출: `outputs/rr_same_component_candidates.json`(10개 same-component
witness 전부, R1 직후 boundary의 전체 legal 후보 열거 — 단일
`macro_edges()` 호출씩, 탐색 아님).

## 4. First R가 component에 만드는 변화

`RR_SAME_COMPONENT_CHAINING_THEOREM.md` §5가 보인 대로, R1의 own
firing이 그 자체로 (a) `ftgt`의 orbit을 union-find 그래프에 새로
등록하고, (b) **그 등록된 phase가 hex 0에 있으면**(=`ftgt`의 orbit이
hex 0에 인접한 6개 orbit `{0,1,3,9,33,120}` 중 하나이고, R1이 하필
그 특정 phase를 target으로 삼으면) 그 즉시 orbit 0의 component와
병합시킨다. 10개 same-component witness 중 **4개는 R1 자신이 바로
이 병합을 수행**(예: `2d88642a05`, R1이 orbit1의 phase4=hex0를
직접 target)하고, **6개는 R1이 아직 병합을 만들지 않고**(R1의
target이 hex0가 아닌 orbit1/120의 다른 phase), 이후 개입 event가
병합을 수행한다.

**정리 후보 "first R는 자신의 target component 안에서 이후 R이 사용할
수 있는 existing-target slot을 하나만 남긴다"에 대한 판정**: **부분
반증됨.** R1 직후 boundary에서 legal R 후보를 전수 열거한 결과(§5),
"하나만 남는다"는 표현은 부정확하다 — 4개 witness에서는 R1 직후
**정확히 1개**의 R 후보만 legal했지만(그리고 그것이 정확히 chaining+same),
다른 3개(`3d74b38661`, `941ba3fda9`, `9a31f2046d`)는 R1 직후
**R 후보가 0개**였고(더 회전해야 나타남), 나머지 3개(`87fd092184`,
`8b4108376f`, `e2c28bc229`)는 R1 직후 **정확히 1개**의 R 후보가
있었지만 그것은 **chaining이 아니고 unresolved**(orbit1을 다시
타겟하는 R 후보, `989d2261b4`도 비슷하게 1개 unresolved 후보)였다.
**"하나만 남긴다"는 명제는 일반적으로 성립하지 않으며, 정확한
형태는 §5의 완전 열거 표로 대체한다.**

## 5. Same-component second R의 선택지 완전 열거

10개 witness 전부, R1 직후 boundary에서 `macro_edges()` 전체 열거
(단일 호출, `outputs/rr_same_component_candidates.json`):

| witness | 총 legal 후보 수 | R 후보 수 | R 후보의 chaining/component_relation |
|---|---:|---:|---|
| `2d88642a05` | 4 | 1 | chaining=True, **same** |
| `49caddbf42` | 4 | 1 | chaining=True, **same** |
| `789ecdd735` | 4 | 1 | chaining=True, **same** |
| `87fd092184` | 23 | 1 | chaining=False, unresolved |
| `8b4108376f` | 23 | 1 | chaining=False, unresolved |
| `e2c28bc229` | 23 | 1 | chaining=False, unresolved |
| `989d2261b4` | 19 | 1 | chaining=False, unresolved |
| `3d74b38661` | 22 | 0 | (없음 — 더 회전 필요) |
| `941ba3fda9` | 22 | 0 | (없음) |
| `9a31f2046d` | 22 | 0 | (없음) |

**목표 명제("같은 component 안의 non-chaining R 후보는 전부 특정
하나의 local legality condition을 위반한다") 판정**: **부분 확인**.
non-chaining R 후보(4건, 표의 `unresolved` 행)는 전부 **동일한
이유**로 "same"이 될 수 없다 — 그 target이 아직 hex-0에 연결되지
않은 orbit(다시 orbit1 자신, 또는 orbit0이 아직 미등록)이기
때문이다. 이는 "특정 하나의 legality condition"이라기보다
"component_relation이 아직 unresolved"라는 **하나의 공통 원인**으로
통일된다는 점에서 목표에 가깝다 — **부분 달성**으로 표시.

## 6. R 사이 zero-charge word의 역할 — "orbit 재사용 streak" 패턴

10개 중 6개(R1 직후 즉시 same-component R 후보가 없는 경우)에서
공통적으로 관측된 패턴: R1이 연 orbit(1 또는 120)이 **여러 차례에
걸쳐 서로 다른 phase로 재사용**된다(Z2 이벤트들이 반복적으로 같은
orbit의 새 phase를 target으로 삼음 — "streak"). 이 streak이 끝나는
지점(정확히는 orbit의 hex-0-인접 phase가 방문되는 지점)에서, 그
직후 R2가 `ell=0`으로 즉시 발동해 "same"을 얻는다.

**"same-component인데 non-chaining이 되려면 어떤 transport
pattern이 필요한가?"**: `RR_ABSTRACT_COUNTERMODEL_STATUS.md` §8의
countermodel이 정확히 이 질문에 답한다 — **제3의 orbit C가 R1의
target(B)과는 무관하게, B가 이미 등록한 것과 **같은** hexagon을
통해 독립적으로 등록되고, R2가 C를 source로 B를 target으로
재사용**하면 same+non-chaining이 abstract하게 가능하다. **이
패턴이 실제 4,470개 코퍼스에서 왜 관측되지 않는지**는
`RR_ABSTRACT_COUNTERMODEL_STATUS.md` §9의 hidden-axiom 논의로
넘긴다(짧은 word 길이 + hex-0의 유일 사전등록 지위 조합, 완전한
연역적 배제 증명은 아님).

## 11. RR 이후 completion obstruction 연결 — corollary 후보

same-component(10개)와 chaining-but-different(65개)를 가르는
hex-0 bridge 메커니즘은 **orbit 0을 "공짜 자원"으로 소비하는
속도**에 직접 영향을 준다: same-component 경로는 R1(또는 그
직후 streak)이 **hex 0에 인접한 orbit의 특정 phase**를 목표로
삼아야 하므로, 그 word는 사실상 **"곧 orbit 0을 R의 target으로
쓸 것"**을 미리 결정한 셈이다. 이는 이전 라운드
(`A2_TWO_ORBIT_CAUSAL_THEOREM.md`)가 발견한 "orbit 0 = word 시작
permutation 자신의 orbit, 항상 공짜로 existing" 자원과 **정확히
같은 자원**을 두 개의 독립적인 조사 트랙(A2의 ell 강제 vs RR의
component 병합)이 똑같이 소비하고 있다는 뜻이다.

**Completion-relevant corollary 후보(다음 라운드로 넘김, 이번
라운드는 폐쇄까지 요구하지 않음)**:

> orbit 0을 이렇게 "일찍" 소비하는 RR word(same-component 10개)는,
> orbit 0을 나중에 다른 defect event(A2, A3, 혹은 또 다른 R)의
> target으로 쓸 수 있는 기회를 그만큼 앞당겨 소진한다 — 만약 완주
> 경로 중 하나가 "orbit 0을 가능한 한 늦게까지 아껴 두는" 전략에
> 의존한다면, same-component RR 경로는 그 전략과 **자원 경쟁**할
> 수 있다.

이 corollary는 **검증되지 않았다**(closure까지 분석하지 않음) —
다음 라운드에서 dedicated하게 다룰 만한, 이번 라운드가 새로 발견한
구체적 가설로 기록한다.
