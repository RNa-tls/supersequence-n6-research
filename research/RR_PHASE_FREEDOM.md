# Phase 자유도와 non-R1 completer의 일반형

산출: `outputs/rr_delayed_completer_normal_forms.json`
(`src/analyze_rr_hub_completer_orbits.py`의 event-ledger 재사용,
`src/analyze_rr_hub_touches.py`의 라운드 13 데이터 재구성).

## 2. Event identity와 orbit identity 분리 — truth table

| 비교 대상 | hub completer와 R1 사이에서 항상 같은가? |
|---|---|
| same event(사건 그 자체) | **아니오**(6/10 반례) |
| same target permutation | **아니오** — completer와 R1이 별개 사건이면 서로 다른 리터럴 순열을 target한다 |
| same target hexagon | **아니오** — R1의 target hex는 보통 hub가 아니다(6/10 케이스에서 R1은 hub 아닌 다른 hex를 target) |
| **same target E-orbit** | **예(10/10)** — 유일하게 항상 성립하는 것 |
| same target phase | **아니오** — orbit은 같지만 phase(hex0-연결 phase 대 다른 phase)가 다르다 |
| same incidence edge(정확히 `(q,h)` 쌍) | **아니오** — completer는 `(O, hex0)`, R1은 흔히 `(O, 다른 hex)` |

**결론**: event identity, target permutation, target hexagon, target
phase, incidence edge 전부 불필요하다 — **오직 target E-orbit만
불변으로 유지된다.** 이는 §1(섹션 5)의 "orbit transport map" 시도가
왜 성공하지 못하는지도 설명한다 — completer가 유일한 orbit으로
결정되는 것은 (§`RR_HUB_COMPLETER_ORBIT_THEOREM.md`가 보였듯)
`abandon_ell=4`일 때만 성립하는 조합론적 사실이며, 일반적으로
"orbit transport"라는 순수 group-이론적 사상은 존재하지 않는다
(989d2261b4에서 이미 5개의 서로 다른 orbit이 completer 후보가
됨을 확인했으므로, `O_complete`를 `O_R`의 함수로 표현하는 사상
자체가 성립하지 않는다 — **§5의 원래 목표는 반증됨**).

## 6. Phase 자유도 설명

- **가능한 phase offset 전체 집합**: orbit이 5개 phase를 가지므로,
  이론적으로 최대 4가지 offset이 가능하다(하나는 hub-connecting
  phase 자신이므로 offset=0). 관측된 10개에서는 R1과 completer가
  서로 다른 phase를 쓰는 경우(6개)와 같은 사건이라 offset이 무의미한
  경우(4개, R1=completer)로 나뉜다.
- **phase offset이 event type을 바꾸는가?**: **아니오** — event type
  (Z2/R/Z3)은 weight(2 또는 3)와 abandon/new_orbit 여부로 결정되며,
  phase 자체와는 무관하다. 동일 orbit의 서로 다른 phase가 서로 다른
  event type(예: 한 phase는 R로, 다른 phase는 Z2로)에 의해 방문될 수
  있다 — 실제로 989d2261b4의 후보 열거에서 orbit 1이 R, Z2, Z3 세
  가지 타입 전부로 도달 가능했다.
- **phase가 달라도 component merge가 같은 이유**: union-find 노드는
  `("q", orbit_id)`이지 `("q", orbit_id, phase)`가 아니다(코드
  확인, `component_map`). **하나의 orbit은 그 자체로 하나의 노드이며,
  어느 phase를 통해 등록되든 그 노드 전체가 하나의 component에
  속하게 된다** — phase는 union-find 구조에서 아예 등장하지 않는
  정보다.
- **chaining 판정에는 왜 phase identity가 필요 없는가**: `chaining`
  자체가 `first_target_second_source`(orbit id 비교, 코드 확인)로
  정의되기 때문이다 — phase는 애초에 이 정의에 들어가지 않는다.
- **phase offset이 full-sweep와 어떻게 양립하는가**: 무관하다 —
  full-sweep(ell=5)은 hex 내부의 위치 개수(6개)에 대한 것이고,
  phase는 E-orbit 내부의 위치(5개)에 대한 것이다 — 서로 다른
  quotient 구조(SIGMA-orbit 대 E-orbit)이므로 독립적이다.

### 구조적 설명: event-identity 오류가 왜 발생했는가

라운드 12는 union-find가 **orbit 단위로만** 노드를 등록한다는
사실(위 `component_map` 구현)을 놓치고, "hub의 2번째 touch가
등록하는 것은 그 사건 자체"라고 암묵적으로 event 단위로 생각했다.
실제로는 등록되는 것은 **orbit이라는 추상 단위**이며, 그 orbit이
어떤 사건(R1 자신이든 별개의 Z2든)을 통해 등록되는지는 union-find
구조 자체에 아무 영향이 없다 — 이것이 정확히 이번 라운드가
"이벤트가 아니라 orbit 정체성을 추적하라"는 지시에 부합하는
근본 원인이다.

## 7. Non-R1 completer 6개의 일반형

6개 반례(`3d74b38661, 941ba3fda9, 9a31f2046d, 87fd092184,
8b4108376f, e2c28bc229`)를 exact normal form으로 분류:

| witness | R1 index | completer index | 개입 word | target orbit |
|---|---:|---:|---|---:|
| `3d74b38661`, `941ba3fda9`, `9a31f2046d` | 2 | 3 | R1 직후 정확히 1개의 Z2가 즉시 hub를 완성 | 1 |
| `87fd092184`, `8b4108376f`, `e2c28bc229` | 1 | 3 | R1 이후 2개의 Z2가 개입, 두 번째가 hub를 완성 | 1 |

**공통 구조(단일 family)**: 6개 전부 `[abandon, ..., R1(orbit1의
한 phase), ..., completer(orbit1의 다른 phase, hex0), R2(source=1,
target=0), ...]` 형태다 — R1과 completer는 서로 다른 사건이지만
**둘 다 정확히 orbit 1을 재사용하는, 하나의 "same-orbit delayed
completer" 패턴의 인스턴스**다. 이는 라운드 11에서 처음 관측한
"orbit 재사용 streak"(하나의 orbit이 word 안에서 여러 차례 다른
phase로 재사용됨)의 특수 사례이며, 6개는 예외가 아니라 **이 하나의
family가 6번 실현된 것**이다.

**일반형 정의(제안)**: "same-orbit delayed completer" =
`(R1_event, completer_event)` 쌍으로, 둘 다 동일 orbit `O`를
target하지만 서로 다른 phase를 쓰고, `R1_event`가 시간상 먼저 오며,
`completer_event`가 hub(hex0)의 남은 위치를 채운다. 이 family
내에서는 항상 `chaining`(orbit 비교이므로 자명)과 `same`(§`RR_HUB_COMPLETER_ORBIT_THEOREM.md`의
필요조건 충족)이 성립한다 — 그러나 이 family가 **왜 항상 형성되는지**
(왜 R1이 완전히 무관한 orbit을 쓰는 시나리오가 나타나지 않는지)의
연역적 이유는 여전히 미완료다.
