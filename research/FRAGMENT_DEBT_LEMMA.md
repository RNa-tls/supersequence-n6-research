# Fragment debt: definition, a proven sub-lemma, and why the naive scalar lemma fails

산출: `src/verify_fragment_debt.py` -> `outputs/ra2_fragment_debt.json`.

## 0. 정의

- **fragment repair**: fragment_hex(현재가 아닌, 유일한 partial
  hexagon)의 target 윈도우를 향하는 weight-2/3 joint. weight-1
  rotation은 언제나 CURRENT hex 안에서만 움직이므로, fragment의
  미방문 윈도우를 채울 수 있는 것은 오직 joint뿐이다.
- **d_frag(S)** = `6 - popcount(hex_masks[fragment_hex])` (fragment_hex가
  없으면 0). fragment는 `f1_normal_form`의 구조적 제약(전체 arc 수
  <= F+1 = 2)에 의해 **항상 단일 연속 arc**이므로, d_frag는 그
  arc의 길이 보완치와 정확히 같다(단일 arc가 아니면 fragment 자체가
  불가능 상태로 pruned된다).
- **abandonment이 fragment에 미치는 효과**: fragment를 만드는 것은
  abandonment 자체다(F: 0→1). 이 모델은 F<=1을 강제하므로 abandonment은
  전체 walk에서 정확히 한 번만 허용된다.
- **R이 fragment에 미치는 효과**: R(weight-3, abandonment=False,
  existing orbit)은 F 예산을 소모하지 않으므로, fragment_hex를 target으로
  갖는 R은 항상 legal하다 — fragment를 다시 "current"로 되돌리는 유일한
  안전한 메커니즘이다.
- **split hexagon**: `RA2_FOUR_SURVIVORS.md` §1과 동일하게 fragment_hex의
  별칭으로 취급한다(이 코드베이스에 별도 정의 없음, 기존 연구 관례 유지).
- **terminal에서 필요한 fragment 상태**: `area_a_final`은
  `visited_count==720`을 요구하므로, 완주하려면 fragment_hex를 포함한
  **모든** hex가 최종적으로 FULL이어야 한다 — fragment도 예외 없다.

## 1. 증명된 하위 정리 — F=1 이후에는 항상 "blocked"(collision 유발) joint만 legal (**손증명, 계산 검증됨**)

`extend()`의 abandonment 계산: `abandonment = not state.visited(sigma-successor of pre-joint p)`.
F<=1이 강제되므로, F가 이미 1인 상태에서 abandonment=True인 어떤
transition도 F=2를 요구해 `area_a_prune_reason`의 `F_exceeded`에 의해
즉시 제거된다. 따라서:

> **F=1 이후, legal한 모든 joint는 abandonment=False여야 한다 —
> 다시 말해, 그 시점 이후 어떤 hex를 떠나는 것도 오직 자연스러운
> rotation collision(그 hex의 남은 부분이 이미 방문됐기 때문에
> 막히는 경우)을 통해서만 가능하다. 임의로 일찍 떠나는(abandon) 것은
> F=1 이후 전혀 legal하지 않다.**

24개 RA2 상태 전부에서(F=1 이후, depth<=6, seed당 edge_cap=20,000) 이를
직접 재생·검증했다: **legal 전이 중 abandonment=True인 것은 0개
(모든 seed, 모든 legal transition)** —
`outputs/ra2_fragment_debt.json`의 `proven_sublemma_post_f1_blocked_only.sublemma_holds: true`.
(주의: `macro_edges()`는 F<=1을 스스로 강제하지 않는 raw 구조적
전이 그래프를 반환한다 — `area_a_prune_reason`으로 illegal한 전이를
먼저 걸러낸 뒤에만 이 하위 정리를 검사해야 하며, 첫 시도에서 이를
빠뜨려 거짓 반례가 나왔던 것을 발견하고 수정했다.)

## 2. 요청된 명제 — **d_frag(S)>0 ⟹ 완주 불가능** — 이 명제는 **성립하지 않는다 (반증됨)**

### 왜 실패하는가: 최소 반례 모델 (실제 exact state 아님, transition axiom만 만족)

`d_frag(S)>0`은 "fragment hex에 아직 방문 안 된 윈도우가 있다"는
말과 정확히 같다 — 이는 **완주 전 어떤 미완성 hex에도 항상 참인
동어반복**이다(fragment든 아니든, 아직 FULL이 아닌 모든 hex는
자명하게 "아직 방문 안 된 윈도우가 있다"). 즉 이 명제는 "아직 끝나지
않았다"는 사실을 재진술할 뿐, 그 자체로 도달 불가능성을 함의하지
않는다.

최소 추상 모델: 6칸 순환 hexagon C, 방문 상태 {0,1,2,4,5}(=arc 길이
5), 미방문은 정확히 {3} 하나(d_frag=1). transition axiom(오직 joint만
비-current hex에 도달 가능, weight<=3의 tail action 집합이 유한하지만
풍부함)을 만족하는 어떤 미래 시점에, 현재 endpoint로부터 위치 3을
정확히 목표로 하는 weight-2 또는 weight-3 tail이 legal move 집합에
존재한다고 가정하면 — 그 joint 하나로 위치 3이 채워지고 hex C는
완성된다. **d_frag(S)=1>0였음에도 완주가 가능하다.** 이는 "d_frag>0
⟹ 불가능"을 직접 반증하는 최소 모델이다.

**진짜 필요한 것은 스칼라 총량이 아니라 도달가능성(reachability)
논증**이다 — "그 특정 미방문 윈도우를 target으로 하는 legal joint가
미래의 어느 시점에 존재하는가"라는 존재 문제이며, 이는 선형/단조
스칼라 potential로 표현할 수 없다. 이것이 왜 scalar debt가 원리적으로
실패하는지에 대한 정직한 이유다 — 임의로 "그럴듯해 보이는" 반례를
만든 게 아니라, 요청 자체(§3)가 "이 명제를 얻지 못하면 왜 실패하는지
최소 반례를 제시하라"고 명시한 실패-보고 조건을 그대로 따른 것이다.

## 3. 그럼에도 발견한 것 — RA2 24개 전체에서 d_frag과 상태의 정확한(전량) 상관관계

*이는 정리가 아니라 관측이다*, 하지만 정확하다(24개 전부, 표본 아님):

| d_frag(after A2) | 개수 | 상태 |
|---:|---:|---|
| 1 | 4 | **전부 unresolved (U4와 정확히 일치)** |
| 2 | 1 | capacity_failure_found |
| 4 | 18 | capacity_failure_found |
| 5 | 1 | capacity_failure_found |

**d_frag=1 ⟺ U4(미해결)이고, d_frag>=2 ⟺ C20(용량 실패 증명됨) — 24개
전부에서 예외 없이 성립한다.** 이는 §1의 "F=1 이후 blocked joint만
legal"이라는 증명된 사실과 결합해 볼 때 **그럴듯한(하지만 증명되지
않은) 설명**이 가능하다: fragment가 정확히 1칸만 모자랄 때는 그 1칸을
채우는 것이 산술적으로 가장 "싸구려"(Φ에 거의 부담을 주지 않는)
수선이므로, `find_minimal_failing_path`의 raw BFS가 얕은 depth에서
Φ<0 위반을 찾지 못했을 가능성이 있다 — 반면 d_frag>=2인 상태는
fragment를 채우는 데 필요한 추가 조인트/회전이 더 비싸서 Φ 위반이
더 빨리, 더 얕게 나타났을 수 있다. **이 설명 자체는 추측이며, 검증되지
않았다.** 상관관계 자체(24/24, 예외 없음)만 유한 완전 검증됐다고
표시한다.

## 4. 성공 기준 (3) 평가

"fragment debt 또는 RA2 전용 Θ obstruction 증명"은 문자 그대로는
**미달성**이다(스칼라 debt 자체는 반증됨). 그러나:

- §1의 하위 정리(F=1 이후 blocked-only)는 **증명되고 계산 검증된
  진짜 정리**다.
- §3의 정확한 24/24 상관관계(d_frag=1 ⟺ 미해결)는 향후 탐색 전략에
  실질적으로 유용한, 정확한(표본 아님) 관측이다 — 원인 설명은
  추측이지만 사실 자체는 그렇지 않다.

`RA2_THETA_POTENTIAL.md`에서 이 재료를 활용해 Θ 벡터 시도를
계속한다.
