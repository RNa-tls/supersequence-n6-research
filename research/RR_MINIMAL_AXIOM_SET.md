# 최소 axiom 집합과 최종 증명 아키텍처

산출: `src/enumerate_rr_initial_axioms.py` -> `outputs/rr_initial_axiom_ablation.json`.

## 6. Minimal axiom ablation 강화

라운드 12의 axiom ablation(M0/M1/M2)을 이번 라운드의 정정(§`RR_HUB_SECOND_TOUCH_THEOREM.md`)에
맞춰 다시 구성했다 — **M2의 axiom 자체(orbit-level)는 원래도
정확했다**, 다만 라운드 12의 **설명**("이벤트가 R1 자신이어야
한다")이 부정확했을 뿐이다. abstract graph model은 애초에 event
identity를 구분하지 않고 orbit/hex 노드만 다루므로, M2가 인코딩한
것은 항상 "completer orbit == R1's target orbit"이었다.

| 모델 | 추가 axiom | countermodel 생존? |
|---|---|---|
| M0 | (없음) | **생존** |
| M1 | + unique hub hexagon(그래프 cardinality 제약, 이번 라운드 §`RR_HUB_TOUCH_COUNT.md`에서 **손증명**으로 승격) | **생존** |
| M2 | + hub touch count ≤ 2(이번 라운드 손증명, `RR_HUB_TOUCH_COUNT.md`) | **생존**(M1과 동일 — 순수 cardinality 제약만으로는 여전히 부족) |
| M2 | + "hub completer의 orbit == R1의 target orbit"(**orbit-identity** axiom, event-identity 아님) | **제거됨** |

```
python3 src/enumerate_rr_initial_axioms.py
M0_graph_axioms_only                              -> countermodel_survives: True
M1_plus_unique_hub_hexagon                        -> countermodel_survives: True
M2_plus_hub_completer_orbit_matches_r1_target     -> countermodel_survives: False
```

### 이번 라운드에서 손증명으로 승격된 것과 여전히 미완료인 것

| 공리 | 라운드 12 상태 | 라운드 13 상태 |
|---|---|---|
| Unique Hub Hexagon(hub 최대 1개) | 손증명(`f1_normal_form`에서 도출) | **불변, 여전히 손증명** |
| Hub touch count ≤ 2 | corpus-exact(4,470/4,470), **증명 없음** | **손증명으로 승격**(`RR_HUB_TOUCH_COUNT.md` §2, `current_hex` 정의 + F≤1 예산에서 완전 연역) |
| "hub second touch = R1" | corpus-exact(10/10)라고 주장 | **반증됨**(6/10 반례, `RR_HUB_SECOND_TOUCH_THEOREM.md`) |
| "hub completer orbit == R1 target orbit" | (미제기) | **corpus-exact(10/10)**, 부분 설명(orbit reuse streak) 있으나 일반 손증명 아님 |
| same-component ⟹ chaining (목표 정리 자체) | corpus-exact(4,470/4,470) | **corpus-exact 유지 + depth≤9 exhaustive 국소 재확인**(10/10 seed, 반례 0) — 여전히 완전 일반 손증명은 아님 |

## 12. Theorem architecture — 최종

### Lemma A — **손증명**
Unique Hub Hexagon: F≤1 word에서 2회 이상 target되는 hexagon은
최대 1개. (`RR_ANCESTRY_PROOF.md` §3-4, `f1_normal_form`에서 직접
도출.)

### Lemma B — **손증명(이번 라운드에서 새로 완성)**
Hub touch count ≤ 2: hub가 존재하면 정확히 2회(first touch + second
touch)만 target되고, 3번째는 구조적으로 불가능하다.
(`RR_HUB_TOUCH_COUNT.md` §2, `current_hex` 정의 + F≤1 예산에서
완전 연역.)

### Lemma C — **반증됨(라운드 12의 형태), corpus-exact로 대체**
"hub second touch = R1"은 **거짓**(6/10 반례). 대체 명제 "hub
completer orbit == R1's target orbit"은 **corpus-exact(10/10)**이나
일반 손증명 아님. (`RR_HUB_SECOND_TOUCH_THEOREM.md` §3-5.)

### Lemma D — **corpus-exact + 손증명(충분성 방향)**
same-component R2 ⟹ chaining, hub를 통해: 충분성(hub touch가 있고
completer orbit이 R1 target과 같으면 same이 나옴)은 union-find
정의로부터 손증명. 필요성은 corpus-exact + depth≤9 exhaustive 국소
재확인(`RR_HUB_SECOND_TOUCH_THEOREM.md` 마지막 절).

### Lemma E — **corpus-exact(10/10)**
same-component R2 상태는 R2 직후 Φ=0. (`RR_CHAINING_COMPLETION_COST.md`,
라운드 12.)

### Lemma F — **손증명**
Φ=0 이후 completion은 ell=5-only: F=1이 이미 소진되어 추가
abandon이 불가능(`area_a_prune_reason`의 `F_exceeded` 체크로 직접
확인)하므로 모든 후속 조인트가 강제로 ell=5(완전 스윕)여야 한다.
(`RR_PHI_ZERO_CONTINUATION.md` §7.)

### Lemma G — **미완료(INCOMPLETE, bounded search로 판정 못함)**
ell=5-only continuation이 남은 hub/orbit demand를 만족할 수 없다:
node_cap=30,000 bounded search가 10개 witness 전부에서 cap에
도달했고(exhaustive 아님), 완주 성공도 명확한 실패도 확인하지
못했다. (`RR_SAME_COMPONENT_CLOSURE.md` §11.)

### Theorem — **corpus-exact(4,470/4,470) + depth≤9 exhaustive 국소
재확인 + Lemma A/B는 완전 손증명, Lemma C/D 필요성 방향은 미완료**
same-component RR branch ⟹ chaining.

**Lemma G까지 못 갔으므로(§13 목표대로), "same-component RR branch는
완주 불가능하다"는 최종 정리는 이번 라운드에서 확립하지 못했다** —
그러나 Lemma A, B가 완전한 일반 손증명으로 승격됐고, Lemma C의
정확한 형태가 바로잡혔으며, Lemma D의 필요성 방향이 훨씬 넓은
탐색(corpus 자신의 경로가 아니라 도달 가능한 전체 R1/R2 선택
공간)으로 재확인된 것은 실질적 진전이다.

## 성공 기준 평가

- **기준 1(hub second-touch = R1 손증명)**: **미달성 — 오히려
  반증됨.** 대신 더 정확한 형태(orbit-identity)를 corpus-exact로
  확립.
- **기준 2(same-component ⟹ chaining 완전 손증명)**: **미달성**,
  그러나 Lemma A/B가 완전 손증명으로 승격되고 필요성 방향의 증거가
  depth≤9 exhaustive 국소 탐색으로 크게 강화됨.
- **기준 3(same-component 10개 exact closure)**: **미달성
  (INCOMPLETE)** — `RR_SAME_COMPONENT_CLOSURE.md` 참고.
- **기준 4(Φ=0 + hub capacity completion obstruction)**: **미완료** —
  Lemma F까지는 손증명, Lemma G는 판정 못함.
- **기준 5(최소 공리 집합 완성)**: **달성** — M2(orbit-identity
  형태)가 정확한 최소 공리이며, abstract countermodel로 직접 검증.
