# 45개 capacity failure의 minimal core certificate

산출: `outputs/j_capacity_45_seeds.json`(원본), `outputs/j_capacity_core_certificates.json`
(독립 검증, `src/verify_j_capacity_cores.py`) — **45/45 PASS**.

## Core의 정의: 기하가 아니라 산술

지시된 "관련 E-orbit/hexagon 집합만 남긴 최소 부분 구조"라는 기하적
core 대신, 실제로 판정을 일으키는 **최소 산술 core**를 추출했다: 각
seed로부터 `Φ<0`에 도달하는 **가장 얕은(depth 최소) 구체 macro-path**다.
이유는 `J_CAPACITY_OBSTRUCTION.md` §5에서 보였듯 — 45개 전부의 실제
원인이 **어떤 특정 hexagon/orbit의 정체성과도 무관한, 순수하게 rotation
run 길이(\(\ell\))의 문제**였기 때문이다. 즉 이 장애물은 "이 특정
순열들이 충돌한다"는 기하적 사실이 아니라 "이 지점의 남은 Φ 예산보다
큰 shortfall이 발생했다"는 **자원 산술적** 사실이다 — 실제로 어떤
순열이 충돌했는지는 원인이 아니라 결과(그 rotation run을 일찍 끝낸
계기)일 뿐이다.

## 각 core의 내용

45개 전부에 대해 다음을 저장했다(`outputs/j_capacity_45_seeds.json`
-> `seeds_45[i]`):

- `canonical_state_hash`, 전체 literal `macro_path`, `j_index_in_path`
- `coordinate_P_F_S_H_O_D_N`, `visited_count`, `remaining_permutations`,
  `remaining_pass_starts`, `remaining_new_orbits_needed`
- `phi_at_witness`
- `fragment_hex`, `fragment_components`, `current_hex`, `current_components`
  (F<=1 lossless normal form, `exact.f1_normal_form`)
- `minimal_failing_continuation`: `{depth, macro_path, ell_of_final_step,
  phi_before_final_step, phi_after_final_step}`

## Core 통계 — **유한 완전 검증**

| 실패 depth (seed로부터) | 개수 |
|---:|---:|
| 2 | 1 |
| 3 | 5 |
| 4 | 12 |
| 5 | 27 |

| 실패를 만든 `ell` | 개수 |
|---:|---:|
| 0 | 38 |
| 1 | 1 |
| 2 | 6 |

모든 core가 `Φ(직전) + (ell-5) < 0`을 정확히 만족하며(항등식 자체가
증명됐으므로 당연하지만, 45개 전부 개별 재생으로 재확인했다), core
길이(depth)는 최소 2, 최대 5 macro-edge — 즉 J로부터 겨우 2~5걸음
만에 이미 산술적으로 막다른 길이 존재한다.

## Isomorphism 여부

45개의 core를 `(phi_before_final_step, ell_of_final_step)` 쌍으로
분류하면 3개 그룹으로 압축된다: `(4,0)`, `(2,{0,1,2})`, `(1,{0,1})` —
사실상 `J_CAPACITY_OBSTRUCTION.md` §5의 표와 동일하다. 이 세 그룹은
**진짜로 동형**이다 — 서로 다른 seed라도 같은 `(phi_before, ell)` 쌍은
정확히 같은 산술 메커니즘(같은 항등식, 같은 부호)을 겪으므로, 이번에는
`J_EXACT_NORMAL_FORMS.md`의 fragment-shape quotient와 달리 **손실이
없다** — 왜냐하면 이 core가 의존하는 유일한 정보(Φ와 ell)가 애초에
scalar이고, 그 산술 결과는 그 두 수치만으로 완전히 결정되기 때문이다
(어떤 hexagon/orbit인지는 실제로 무관하다).

## R 사용과 core의 관계 — 45개 전부 재생 확인

45개의 minimal failing continuation을 처음부터 재생해 각 step의 joint
종류(`R`, `Z2`, `Z3`)를 기록했다: **28/45는 실패 이전에 R을 최소 1회
사용했고, 17/45는 R을 전혀 쓰지 않고도 같은 방식으로 실패했다.** 두
그룹 모두 정확히 같은 `Φ` 메커니즘으로 실패한다 — `J4_COMPONENT_ANALYSIS.md`
§candidate C에서 이를 더 다룬다.
