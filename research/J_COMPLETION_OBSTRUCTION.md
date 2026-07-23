# J-branch 완주 장애물 분석

범위: `F=1,H=0`, charge-2 defect `J`(abandonment weight>=3 -> 기존 E-orbit,
`(ΔF,ΔS,ΔO,ΔN)=(1,1,0,2)`)가 발생한 뒤의 완주 가능성.

증거 등급: **증명됨** / **유한 완전 검증** / **제한 실험** / **추측** / **반증됨**.

## 0. 데이터 가용성에 대한 정직한 전제

`legacy_research/outputs/f1_n2_depth6_decomposition.json`과
`f1_n2_defect_words.json`은 230개의 J 상태 중 **단 하나**의 literal walk만
저장한다 (`representatives_by_word["J"]`). 나머지 229개는 `state_hash`,
`deficit_phase_type`, `legal_macro_tail_count`, `global_visited_mask_fingerprint`
같은 파생 요약값만 가지고 있다. 따라서 이 문서의 literal replay·bounded
continuation 결과는 **그 하나의 대표 상태에 대한 것**이며, 230개 전체에 대한
literal 결과가 아니다. 이 사실은 반복해서 명시한다 — 나머지 229개를 마치
개별적으로 재현한 것처럼 서술하지 않는다.

## 1. 정리 J-1 (abandonment 예산 소진) — **증명됨**

`superperm_partial_f1.py`에서 `TARGET_F=1`이고, `f1_prune_reason`/
`area_a_prune_reason` 모두 `state.F > TARGET_F`를 즉시 prune하며,
`final_target`/`area_a_final`은 `state.F == TARGET_F`를 요구한다.

J 자체가 `ΔF=1`인 abandonment이므로, J가 발생한 직후 상태는 이미
`F=1=TARGET_F`이다. 따라서:

> **정리.** J 이후, 완주까지 남은 어떤 joint도 abandonment일 수 없다
> (`A2`, `A3`, 두 번째 `J`, `Z2_abandon_w2_new` 모두 즉시 불가능).

증명은 정의 그 자체다 — 별도 탐색이 필요 없다. `src/analyze_j_completion.py`의
`post_J_budget`이 이를 구체 상태에 대해 재확인한다
(`abandonment_budget_remaining: 0`).

## 2. 정리 J-2 (N 예산 1잔여) — **증명됨**

`ΔN`이 음수일 수 없다는 (blocked-w2 lemma로 배제됨, §4 참고) 전제 아래,
J 직후 `Ndef=2`이고 전체 slab의 budget은 `Ndef+H<=TARGET_BUDGET=3` (H=0이므로
`Ndef<=3`)이다. J-1에 의해 남은 유일한 `ΔN=+1` joint 유형은 `R_blocked_w3_existing`
뿐이다 (abandonment형 joint는 전부 불가능하므로). 따라서:

> **정리.** J 이후 남은 전체 걸음에서 `R_blocked_w3_existing` joint는
> **최대 1회**만 등장할 수 있다. 그 밖의 모든 non-rotation joint는
> `Z2_blocked_w2_existing` 또는 `Z3_blocked_w3_new` (둘 다 `ΔN=0`)여야 한다.

## 3. 정리 J-3 (강제된 joint 알파벳, 정량) — **증명됨**

J 직후 상태(대표 예시, 좌표 `P=6,F=1,S=3,H=0,O=2,D=4,N=2`)에서:

- 남은 전체 joint 수 = `TARGET_P-P = 115`
- 남은 신규 orbit 필요 수 = `TARGET_O-O = 23` — 이들은 **전부**
  `Z3_blocked_w3_new`여야 한다 (J-1에 의해 신규 orbit을 여는 abandonment형
  joint(`A3`, `Z2_abandon_w2_new`)가 봉쇄되었으므로, 신규 orbit을 여는
  유일한 남은 메커니즘은 non-abandoning weight-3 blocked-into-new, 즉
  `Z3_blocked_w3_new` 하나뿐).
- 남은 기존-orbit joint 수 = `115-23=92`; 이 중 최대 1개가 `R`, 나머지
  91개 이상은 `Z2_blocked_w2_existing`.
- `D=5O-P` 항등식으로부터 요구되는 `ΔD`와, 위 개수로부터 예측되는 `ΔD`
  (`4*23-92=0`, 실제 필요값도 `TARGET_D-D=4-4=0`)가 정확히 일치함을
  `src/analyze_j_completion.py`가 확인했다.

이 개수 자체는 **산술적으로 모순이 없다** — 즉, 단순 자원 회계만으로는 J의
완주 불가능성을 보일 수 없다. 장애물이 존재한다면 기하적/충돌 수준이어야
한다.

## 4. blocked-w2 lemma — **유한 완전 검증(부분) + 유한 경험적 확인**

8행 joint 진리표는 `ΔN=1_{w>=3}+1_{abandonment}-1_{new orbit}`라는 항등식
(`N:=S+F-O`, 정의 그 자체)에서 순수 유한 나열로 재도출된다 —
`src/analyze_j_completion.py::truth_table()`. 결과: charge-2 행은
정확히 하나(`J`), 음전하 행도 정확히 하나(`forbidden_blocked_w2_new`,
weight2·blocked·new orbit, `ΔN=-1`). **이 두 유일성 주장은 증명됨** (8개
경우를 전수 확인한 것이므로).

`forbidden_blocked_w2_new`가 실제로 도달 불가능하다는 "blocked-w2 lemma"
자체는 이 저장소의 legacy 코드에서도 명문화된 증명을 찾지 못했다 — 여러
파일이 이를 기정사실로 인용/assert할 뿐이다. 독립적으로, identity에서
출발해 실제 엔진(`exact.extend`)으로 **raw(비정준화) BFS**를 깊이 7,
60,000 node 한도로 실행했다 (`bounded_raw_reachability_check`):
244,617개의 서로 다른 raw 상태에 도달했고, 다른 7개 행은 각각 수만~수십만
회 관측된 반면 `forbidden_blocked_w2_new`는 **단 한 번도 관측되지 않았다**.
이는 **경험적 확인**이지 증명이 아니다 — 명시적으로 그렇게 라벨링한다.

## 5. 제한 continuation 실험 (macro depth ≤4, edge cap 100,000) — **제한 실험**

대표 J 상태 하나에서 시작해 `macro_edges`+`area_a_prune_reason`(기존
`AREA_A`, n_limit=3 그대로 재사용— 정확히 §2의 예산과 일치)으로 4
macro-step, 1043 edge를 전개했다. 결과:

```json
{
  "edges_expanded": 1043,
  "prune_counts": {"F_exceeded": 866, "N_exceeded_monotone": 20},
  "immediate_terminal_states": 0,
  "states_with_only_pruned_children": 0,
  "max_survivor_depth_reached": 4
}
```

**해석 (제한적으로만).** 이 얕은 창 안에서 관측된 모든 pruning은 정확히
§1·§2에서 이미 증명한 두 메커니즘(abandonment 예산 소진, N 예산 소진)
뿐이었다 — capacity, D-산술, normal-form, orbit-opening-credit 등 **새로운
장애물은 이 4-step 창에서 전혀 나타나지 않았다.** 모든 상태가 최소 하나의
합법적 zero-charge 후속을 가졌다. 이는 J가 완주 가능하다는 증거도, 불가능
하다는 증거도 아니다 — 남은 115개 joint 중 겨우 4개를 본 것이며, capacity류
장애물은 통상 걸음의 후반부(자원이 소진되어 갈 때)에만 나타난다. **작은
m에 대한 "m-step 안에 반드시 장애물"류 정리는 지지되지 않는다.**

## 6. 후보 정리 판정

**A. "모든 J 상태는 유한한 zero-defect continuation 뒤 추가 positive-charge
joint를 강제한다."** → **미결정.** §3의 산술 분해(23 Z3 + 92 existing-orbit
joint, 그중 91개 이상 Z2)는 정확히 `ΔN=0`만으로 완주 개수를 채울 수 있음을
보인다 — 즉 산술은 "추가 charge 없이" 완주하는 스케줄을 배제하지 않는다.
5-step bounded 실험도 강제 charge를 보이지 않았다. 이 후보를 증명하려면
기하/충돌 논증이 필요하고, 현재 갖고 있지 않다.

**B. "J 이후 완주에 필요한 최소 추가 charge는 1이다."** → **반증까지는
아니지만 근거 없음으로 강등.** §3의 산술이 이미 추가 charge 0인 분해를
허용하므로(23+92, 전부 zero-charge), "최소 1"이라는 주장을 지지할 산술적
근거가 없다. 만약 이 후보가 참이라면 그 이유는 순수하게 기하적(충돌)이어야
하며, 현재 미확인이다.

**C. "J는 split hexagon과 동일 incidence component에서만 발생한다."** →
**미결정.** J 레코드에는 `component_relation`/`fragment_relation` 필드가
없다(J는 단일 이벤트라 정의상 null, `src/verify_j_normal_forms.py`가
230개 전부에서 이를 재확인). 대표 하나의 literal 상태에서는
`fragment_before.fragment_hex: null` — 즉 이 대표 예시에서는 J 발생 시점에
**아직 fragment가 없었다** (J 자체가 그 walk의 첫 abandonment였다). 따라서
"split hexagon과 동일 component" 개념이 이 대표 예시에는 적용조차 되지
않는다. 230개 다른 인스턴스들의 사전 상태는 데이터에 없어 확인 불가.

**D. "J가 만든 abandonment는 fragment repair 자원을 소진한다."** →
**부분적으로 재확인, 조건부.** J는 그 자체로 이 walk의 유일한 abandonment
(F=1)이므로 "fragment repair"라는 별도 자원이 존재한다면 그것은 정확히
§1의 abandonment 예산과 같은 것이다 — 새로운 독립된 자원이 아니라 §1의
재서술이다.

**E. "J 상태의 cover-capacity slack은 완주에 필요한 최소량보다 항상
작다."** → **미결정, 반례성 데이터 없음.** 대표 예시의 §3 산술은 slack이
정확히 0(모순 없음)임을 보인다 — 즉 이 예시에서 slack 부족은 관측되지
않았다. bounded 실험(§5)도 `remaining_cover_capacity_impossible` prune을
단 한 번도 만들지 않았다. 이 후보를 지지할 증거가 없다.

## 7. 결론 — 이번 작업에서 얻은 새로운 것

- **새 정리(J-1,J-2,J-3):** J 발생 이후 남은 걸음 전체가 `{rotation,
  Z2_blocked_w2_existing, Z3_blocked_w3_new, 최대 1개의 R}`라는 매우 좁은
  joint 알파벳으로 강제된다는 것, 그리고 그 개수(23개 Z3, 최대 1개 R,
  나머지 Z2)가 산술적으로 유일하게 결정된다는 것을 **증명**했다(정의와
  항등식만으로, 탐색 없이).
- 이 강제된 알파벳은 `PARTIAL_F1_N0_FLOW_LEMMA.md`의 N=0 정리 2·따름정리 3과
  **동형(isomorphic)**이다 — 다른 시작 상태, 다른 남은 P/O 목표값을 가진
  같은 종류의 "zero-charge 스케줄링 문제"다. 이것이 **§8의 reduction**이다.
- 산술만으로는 J를 배제할 수 없다(§3, §6-A/B) — 배제하려면 N=0 문제에
  필요한 것과 같은 수준의 기하/충돌 논증이 필요하다는 것이 이번에 명확해진
  대목이다.
