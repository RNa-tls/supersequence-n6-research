# Decorated boundary state — 정의·transport·최소성 (라운드 20)

산출: `src/enumerate_rr_decorated_local.py` -> `outputs/rr_decorated_l5_ledger.json`,
`src/verify_rr_decorated_markov.py` -> `outputs/rr_decorated_ablation.json`.
새 completion search 없음.

## 1. Decorated boundary state의 invariant 정의

라운드19가 연역적으로 확립한 대로 post-R2 `ExactState`만으로는
chaining을 판정할 수 없다. 이번 라운드는 함께 실어야 할 decoration을
정의한다:

\[
\widehat S=(S,\ \mathcal D),\qquad
\mathcal D=(\text{orbit-transported} \parallel \text{hex-transported} \parallel \text{invariant})
\]

**orbit id로 transport되는 필드(5개)**: `r1_source_orbit`,
`r1_target_orbit`, `r2_source_orbit`, `r2_target_orbit`,
`hub_completer_orbit`.

**hexagon id로 transport되는 필드(4개)**: `hub_id`,
`r1_target_hexagon`, `r2_target_hexagon`, `hub_completer_hexagon`.

**left-S6 불변 필드(18개)** — 구현 인덱스가 아니라 불변량으로 정의:

| 필드 | 불변 정의 |
|---|---|
| `abandonment_ell` | hub의 anchor 위치에서 abandonment 조인트까지의 순수 회전 스텝 수 |
| `r1_macro_index`, `r2_macro_index`, `hub_completer_macro_index` | abandonment root로부터의 macro-edge **개수**(배열 인덱스가 아님) |
| `r1_source_phase` 등 phase 4종 | E-orbit 내 phase — left relabeling은 phase를 보존 |
| `hub_completer_kind` | 조인트 분류(R/Z2/Z3/…) |
| `hub_completer_is_r1` | completer가 R1 자신인지 |
| `r1_target_hub_distance`, `r2_source_hub_distance`, `r2_target_hub_distance` | incidence graph에서 `("h",hub)` 노드까지의 **BFS 거리**(그래프 불변량) — 이것이 "hub ancestry" 좌표 |
| `r2_meet_is_hub` | `("q",R2_s)`→`("q",R2_t)`의 모든 최단경로가 hub 노드를 지나는가(LCA형 좌표) |
| `r1_boundary_orientation` | `sign(r2_source_phase − hub_completer_phase) ∈ {−1,0,+1}` (path orientation) |
| `fresh_orbit_openings` | R2 이전의 Z3(new-orbit) 조인트 **개수** |
| `preparation_family` | `fresh_orbit_openings == 0`이면 `no-fresh-opening`, 아니면 `fresh-opening` |

## 3. Decorated canonicalization과 tie 처리

`exact.canonicalize()`는 최소 translate만 돌려주고 달성 alpha는
돌려주지 않는다. 따라서 **쌍 `(S, D)`를 canonicalize**한다: 최소
key를 달성하는 모든 alpha에 대해 `LEFT_ORBIT_ACTION[alpha]`와
`LEFT_HEX_ACTION[alpha]`로 decoration을 transport하고, 그 위에서
사전순 최소를 택한다.

**출력에 저장된 항목**: `raw_state_hash`, `canonical_state_hash`,
`canonical_decorated_hash`, `chosen_alpha`, `stabilizer_size`,
`tie_variant_count`.

**측정 결과 (2,234개 경계 전부)**:

- `stabilizer_size = 1` — **2,234/2,234**. 비자명 stabilizer가 하나도
  없다.
- `tie_variant_count = 1` — **2,234/2,234**. transport된 decoration
  변종이 항상 1개뿐이다.

> **따라서 "tie가 relation 판정을 바꾸지 않음"은 이 universe에서
> 공허하게(vacuously) 참이다** — 바꿀 tie 자체가 없다. 이를
> "증명했다"고 표기하지 않고 **root-local exhaustive 관측**으로만
> 표기한다. (일반 상황에서 tie가 생기면 위 최소화 절차가
> well-defined한 대표원을 주지만, 그 절차의 relation-불변성은
> 이번 라운드에서 증명하지 않았다 — **미완료**.)

## 2. 최소성 ablation — 설계가 핵심이다

**순진한 설계는 공허하다.** 라운드19가 보인 대로 이 universe의
2,234개 post-R2 `ExactState`는 각각 정확히 1개의 경계로만 도달된다.
따라서 **key에 `ExactState`를 포함시키면** 어떤 decoration을 빼도
모든 경계가 분리되어, 모든 필드가 "불필요"하다는 잘못된 결론이
나온다.

**그래서 이번 ablation은 `ExactState`를 key에서 완전히 제외**하고
다음을 묻는다: **decoration 단독으로 chaining / same-component /
trailing-edge signature가 결정되는가?**

### 결과 1 — decoration 단독으로 세 relation 전부 결정된다

| target | 결정됨 | 서로 다른 key 수 | 충돌 group 수 |
|---|:---:|---:|---:|
| `chaining` | **예** | 2,216 | **0** |
| `same_component` | **예** | 2,216 | **0** |
| `trailing_edge_signature` | **예** | 2,216 | **0** |

2,234개 경계가 2,216개 decoration key로 압축되는데도 충돌이 0이다 —
**decoration은 `ExactState` 없이도 충분하다**. 등급: **exact
decorated quotient**.

### 결과 2 — 필드별 필요성

| 판정 | 필드 |
|---|---|
| **NECESSARY**(exact counterexample 존재) | `fresh_orbit_openings` (제거 시 `trailing_edge_signature` 결정 실패) |
| **필요성 미결정** | 나머지 26개 전부 |

지시대로 **반례가 없다고 해서 "불필요"라고 선언하지 않는다** —
"이 universe에서 필요성 미결정"으로만 표기한다.

### 결과 3 — greedy 최소 부분집합과 그 함정 (중요)

greedy 탐색이 찾은 7개 필드 부분집합:
`r1_target_hexagon`, `r2_source_phase`, `r2_target_phase`,
`r2_target_hexagon`, `r2_macro_index`, `hub_completer_phase`,
`fresh_orbit_openings`.

**이 결과를 "최소 decorated state"로 읽으면 안 된다.** 이 집합에는
`r1_target_orbit`도 `r2_source_orbit`도 없는데, chaining의 정의가
바로 `r1_target_orbit == r2_source_orbit`이다. 즉 이 7개 필드는

- 이 **유한 universe의 경계들을 relation-동질적 그룹으로 분리**할
  뿐이고,
- 정의로부터 relation을 **계산**하게 해주지는 않는다.

> **분리 최소성(separating minimality)과 구조 최소성(structural
> minimality)은 다른 개념이며, greedy 결과는 약한 쪽이다.**
> 구조적으로 반드시 필요한 것은 chaining에 대해
> `r1_target_orbit`, `r2_source_orbit`(정의상), same-component에
> 대해 hub-ancestry 좌표(§`RR_DECORATED_MARKOV_COMPLETENESS.md` §6)다.

이 구분을 명시하지 않으면 "7개 필드면 충분하다"는 과잉주장이 되므로,
**greedy 결과는 참고용 관측으로만 남긴다.**
