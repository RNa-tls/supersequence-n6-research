# One-hole geometry lemma (H1–H4) 및 ell-conditioned automaton

산출: `outputs/ra2_ell4_transition_table.json`(H1–H4 depth-1 시도),
`outputs/ra2_repair_cones.json`(재사용, 실제 repair witness 검사),
`outputs/ra2_ell4_automaton.json`.

## 6. One-hole geometry lemma — H1–H4 판정

ell_A2=4가 남기는 "hole"은 `RA2_ZERO_CHARGE_HISTORY.md`에서 이미 정확히
특정됐다: fragment_hex의 단일 연속 arc 중 정확히 1칸(arc 길이 5/6)이
미방문. 실제 최단 repair witness(이전 라운드
`FRAGMENT_REPAIR_OBLIGATION.md` §6, macro_distance=3, U4 4개 전부)를
직접 재생해 H1/H2를 검증했다(depth-1만으로는 repair edge 자체가
없어 판정 불가했으므로, 실제 repair가 일어나는 지점까지 재생).

### H1: "repair 후 endpoint가 terminal-compatible class에서 벗어난다" — **반증됨**

4개 U4 전부의 최단 repair witness는 `repair_cone_search`가
**`area_a_prune_reason`을 통과한 상태만 기록**한 결과다 — 즉 이미
알려진 모든 필요조건(F_exceeded, H_positive, P_exceeded, O_exceeded,
N_exceeded_monotone, D 도달가능성, remaining window capacity,
F1 fragment normal form, 미래 orbit 개방 신용) **전부를 통과했다.**
repair가 알려진 어떤 필요조건도 위반하지 않으므로, "terminal-compatible
class에서 벗어난다"는 주장은 **반증됨**이다.

### H2: "hole repair는 zero-cost지만 특정 E-orbit를 재사용하게 만든다" — **손증명(4/4 재확인)**

4개 U4 전부의 최단 repair witness에서, **repair를 수행하는 마지막
joint 자체가 예외 없이 `new_orbit=False`**(기존 E-orbit 재사용)임을
직접 재생으로 확인했다. `FRAGMENT_REPAIR_OBLIGATION.md`에서 이미
확인한 `orbit_slack_consumed=0`이 바로 이 사실의 결과였다 — 이번에
그 원인(어떤 joint가, 왜)을 리터럴로 특정했다. **H2는 참이다** —
4개 U4 전부, 최단 repair witness에서 예외 없이 확인.

### H3: "hole을 유지하면 이후 모든 legal transition이 특정 phase class에 갇힌다" — **반증됨**

A2 직후 depth-1의 non-repair(=hole 유지) legal transition들에서 서로
다른 target orbit q 값이 여러 개 관측됐다(`outputs/ra2_ell4_transition_table.json`) —
단일 phase/orbit class로 갇히지 않는다. 4개 U4 전부 동일하게
반증됨.

### H4: "hole 위치와 A2 target phase가 결합되어 incidence parity를 고정한다" — **미완료**

"incidence parity"가 이 코드베이스에 명시적으로 정의된 개념이 아니다
(`component_map`의 union-find 결과를 "parity"로 재정의하려는 시도를
했으나, 이산적 등록/미등록 상태만 있을 뿐 "패리티"라 부를 만한
이진 불변량을 정의로부터 유도하지 못했다) — 정직하게 미완료로
남긴다.

## 7. ell-conditioned continuation automaton — 부분적으로만 구성 가능

요청된 7-튜플 `(ell_A2, Φ, hole position, endpoint phase, target orbit
relation, repair status, split status)` 전체를 U4 4개가 공유하는
단일 automaton으로 만들려 했으나, **hole position/endpoint
phase/target orbit relation은 4개 상태마다 다른 zero-charge history의
잔재(어떤 "다른" orbit을 거쳤는지)에 의존하는 개별 필드**이지,
공유 가능한 추상 좌표가 아니다(`RA2_FOUR_SURVIVORS.md`에서 이미 4개가
서로 독립임을 증명한 바로 그 차이). 따라서 **더 거친(coarse) 3-튜플
`(Φ, hole_present, repair_status)`만 4개 상태에 안전하게 공유되는
automaton**으로 구성했다(`outputs/ra2_ell4_automaton.json`):

```
(Φ=5, hole=True,  unrepaired) --[hole repair edge]--> (Φ=5, hole=False, repaired)   -- REALIZED (4/4)
(Φ=5, hole=True,  unrepaired) --[non-repair blocked edge]--> (Φ<=5, hole=True, unrepaired) -- REALIZED (지배적 분기)
(Φ, hole=False, repaired) --[...]--> 이후 완주 여부       -- 이번 범위 밖 (전체 완주 탐색 아님)
```

**목표였던 "ell=4 branch를 유한 개의 geometry subcase로 환원"은
부분 달성**이다: 거친 3-튜플 수준에서는 유한(2개 상태: hole 있음/없음)
automaton이 만들어지지만, 세부 지오메트리(정확히 어떤 orbit이
관련되는지)까지 포함한 완전한 automaton은 4개 상태 각각 별도로
남는다 — 이는 억지로 통합하지 않고 정직하게 그렇게 기록한다.

## 8. Family-local 재탐색 — 이번에도 새 prune 없음, cap 확장 보류

이번 라운드에서 얻은 것은 **geometry에 대한 서술적 사실**들이지(new
prune이 아니라), U4의 legal continuation을 실제로 줄이는 새로운
안전한 조건이 아니다(H1–H4 중 참으로 확정된 것은 H2뿐이고, H2 자체가
"debt를 줄이는 게 쉽다"는 이전 라운드의 결론을 재확인할 뿐 새 배제
조건을 주지 않는다). 요청 §8의 지침("새 obstruction 또는 abstraction을
얻은 뒤에만 재탐색하라", "30% 미만 개선이면 cap을 키우지 마라")에
따라, **이번 라운드는 U4에 대한 추가 대규모 재탐색을 수행하지
않는다** — `RA2_ELL4_BOUNDARY_GEOMETRY.md`의 controlled ell-sweep(각
ell당 edge_cap 20,000, U4 4개 × ell 3개 = 이미 상당한 탐색을 수행)만이
이번 라운드의 실질적 탐색이었다.
