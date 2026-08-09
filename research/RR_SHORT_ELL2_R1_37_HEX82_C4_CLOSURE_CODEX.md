# Round 61 — short_ell2_r1_37 hex-82 five-route provenance closure

작성자: Codex

범위: `short_ell2_r1_37`의 84개 frozen Stage-D anchor 아래, R1 이후·R2 이전의 Target-A-safe descendant family

방법: 고정 `HEX_POSITION / ORBIT_PHASE` 표, exact no-repeat 손증명, 여섯 immutable parent DAG의 독립 literal replay

## 결론

Round 60에서 남은 다섯 hex-82 C4 route는 모두 막힌다.

```text
q42:p1   -> h82 position 2
q78:p3   -> h82 position 4
q82:p0   -> h82 position 0
q83:p4   -> h82 position 5
q128:p2  -> h82 position 1
```

다섯 route의 local w3 target은 서로 다르지만, `h82`를 `C_R1`에 먼저 넣는
공통 prerequisite는 하나뿐이다. 그것은 orbit 91의 h82 port인

```text
q91:p2 = 513042 = h82 position 3
```

의 incidence를 등록하는 것이다. R2 이전에 이 incidence를 만드는 유일한
허용 transport는 blocked w2(Z2)이고, 그 literal 역상은

```text
245130 --w2--> 513042
```

이다. `245130`은 h40 position 1에 있고, h40은 84개 anchor에서 모두 이미
full이다. 동시에 anchor의 현재 끝점이 `245130`인 경우는 0개다. exact
engine은 방문된 순열창을 다시 target으로 삼을 수 없으므로, 어느 descendant도
다시 `245130`을 현재 끝점으로 만들 수 없다. 따라서 `q91:p2` Z2는 영원히
실행 불가능하고 h82는 R1-target component에 들어가지 않는다.

이것은 bounded absence가 아니라, 고정 anchor family 전체에 대한 literal
no-repeat 귀납이다.

## 1. 다섯 route 명세

각 route는 별도의 exact case로 유지했다. symmetry나 continuation equivalence로
합치지 않았다.

| route | target word | h82 position | 가능한 w3 joint source들 |
|---|---:|---:|---|
| `q42:p1` | `251304` | 2 | `430251`, `043251`, `403251` |
| `q78:p3` | `130425` | 4 | `542130`, `254130`, `524130` |
| `q82:p0` | `042513` | 0 | `351042`, `135042`, `315042` |
| `q83:p4` | `304251` | 5 | `125304`, `512304`, `152304` |
| `q128:p2` | `425130` | 1 | `013425`, `301425`, `031425` |

각 행의 세 source는 각각 `w3:120`, `w3:201`, `w3:210`의 유일한 literal
역상이다. 모든 route가 noncolliding Z3가 되려면 다음이 동시에 필요하다.

1. h82가 q91을 포함하는 incidence component에 있다.
2. target orbit은 아직 등록되지 않았다.
3. w3 source의 rotation successor가 이미 방문되어 joint가 blocked이다.
4. target window는 아직 방문되지 않았다.
5. `F=1, H=0, r_count=1`의 pre-R2 scope를 유지한다.

전체 literal predecessor 표와 rotation-length별 macro-entry word는
`rr_short_ell2_r1_37_hex82_routes.json`에 있다.

## 2. 공통 backward provenance closure

다섯 route에서 역방향으로 필요한 incidence를 따라가면 모두
`q91:p2 -- h82` 하나로 합쳐진다.

### 2.1 왜 q91:p2뿐인가

첫 component-changing Z3가 발생하기 전 `C_R1`의 orbit은 q91뿐이다. 새로운
orbit의 Z3가 h82를 통해 q91 component를 확장하려면, h82 자체가 먼저 그
component에 있어야 한다. 그러려면 q91의 유일한 h82 phase인 p2 incidence가
선행해야 한다.

w3로 기존 q91에 들어가면 blocked case는 R이며, 이미 R1이 존재하므로 이것은
R2 boundary다. 검색은 R2를 판정하지만 그 뒤를 traverse하지 않는다. 따라서
pre-R2 incidence 등록에 쓸 수 있는 것은 w2뿐이다.

### 2.2 유일한 w2 역상

weight 2 move는 하나뿐이고 우작용은 bijection이므로 q91:p2의 역상도 하나다.

```text
target                 513042  (q91:p2, h82:3)
unique w2 source       245130  (h40:1)
rotation successor     451302  (q91:p1, h40:2)
```

h40 full이므로 rotation successor는 방문되어 있어 이 w2는 abstract state에서는
blocked Z2가 된다. 그러나 source `245130`도 이미 방문되어 있다. anchor가 그
source에서 끝나지 않았으므로 exact descendant에서 source를 현재 끝점으로 다시
만드는 경로가 없다.

### 2.3 H0–H5 분류

| 층 | 의미 | 결과 |
|---|---|---|
| H0 | locally impossible | 해당 없음 |
| H1 | local route 가능, predecessor illegal | 해당 없음 |
| H2 | predecessor 자체는 local legal, anchor provenance와 불일치 | 공통 q91:p2 Z2 |
| H3 | route prerequisites abstractly compatible | 다섯 route 모두 |
| H4 | exact reachable prerequisite state | 0 |
| H5 | exact noncolliding C4 witness | 0 |

따라서 closure 원장은

```text
5 route classes
-> 1 deduplicated literal predecessor obligation
-> 0 provenance-consistent classes
-> 0 exact reachable classes
-> 0 witnesses
```

에서 안정화된다. 이 closure는 전역 exact state를 임의로 quotient한 것이 아니다.
공통 literal source가 anchor visited set 때문에 도달 불가능하다는 충분한
obstruction certificate다.

## 3. Forward intersection

여섯 immutable Stage-D checkpoint를 모두 literal replay했다.

| seed | exact/decorated nodes | expanded | frontier |
|---|---:|---:|---:|
| `236166` | 3,158 | 3,158 | 0 |
| `12` | 170,773 | 170,773 | 0 |
| `6` | 459,712 | 425,000 | 34,712 |
| `3` | 459,657 | 425,000 | 34,657 |
| `303321` | 5,964 | 5,964 | 0 |
| `13` | 226,128 | 226,128 | 0 |
| **합계** | **1,325,392** | **1,256,023** | **69,369** |

모든 stored node를 replay하고, frontier도 확장하지 않은 채 각 상태에서 다섯
target phase로 향하는 one-step w3 macro를 검사했다.

| route | M1 orbit/phase macro match | M2 structural | M4 legal C4 | M5 FZ1 |
|---|---:|---:|---:|---:|
| `q42:p1` | 43,720 | 0 | 0 | 0 |
| `q78:p3` | 17,403 | 0 | 0 | 0 |
| `q82:p0` | 61,294 | 0 | 0 | 0 |
| `q83:p4` | 18,446 | 0 | 0 | 0 |
| `q128:p2` | 14,675 | 0 | 0 | 0 |
| **합계** | **155,538** | **0** | **0** | **0** |

M1 155,538건의 첫 실패 조건은 전부 `hex82_in_R1_component=false`다.
replay corpus 전체에서 다음도 0이었다.

```text
q91:p2 registered nodes          0
current p = unique Z2 source     0
h82 in R1 component nodes        0
```

각 route의 가장 가까운 exact near-miss는 3–4개의 다른 조건을 만족했지만 모두
h82 component 조건에서 먼저 실패했다. 대표 경로 전체는 MITM JSON에
anchor path hash, node chain, accepted macro edge sequence로 저장했다.

## 4. Hex-82 occupancy 정리

anchor의 h82 mask 분포는 다음과 같다.

```text
mask 0   81
mask 2    1
mask 4    1
mask 63   1
```

mask 0이 많으므로 단순한 “h82는 처음부터 full” 정리는 거짓이다. 실제 정리는
점유량이 아니라 provenance에 관한 것이다.

> **Hex-82 provenance lemma.** 84개 frozen Stage-D anchor의 어느 pre-R2
> descendant에서도 q91:p2 incidence는 등록될 수 없다. 따라서 h82는
> `C_R1`에 들어가지 않고, 다섯 hex-82 first-component-Z3 prerequisite는
> exact-unreachable이다.

증명은 다음 네 사실만 쓴다.

1. q91에서 h82를 만나는 phase는 p2 하나다.
2. pre-R2에서 기존 q91 phase를 새로 여는 허용 transport는 blocked w2다.
3. q91:p2의 unique w2 source `245130`은 84개 anchor 모두에서 방문돼 있다.
4. 어느 anchor도 그 source에서 끝나지 않으며 exact transition은 방문 창에
   재진입하지 못한다.

## 5. SAT/CSP 판정

SAT/CSP는 실행하지 않았다. 미해결 finite quotient를 solver에 넘긴 것이 아니라,
다섯 case가 공유하는 유일한 literal predecessor가 exact provenance로 직접
제거됐기 때문이다. solver encoding은 이보다 약하고 복잡하며 추가 결론을 주지
않는다.

## 6. Theorem ladder

| 층 | 상태 | 정확한 범위 |
|---|---|---|
| T2 | **증명됨** | 저장된 C4 253,537건은 모두 충돌 |
| T2a | **증명됨** | h40/h90/h91/h92 route는 root-full + monotonicity로 충돌 |
| T2b | **증명됨** | 다섯 h82 route는 공통 predecessor provenance로 exact-unreachable |
| T2+ | **증명됨** | 84 frozen anchor descendant family의 전체 C4 prerequisite space |
| T3 | **증명됨** | 같은 family에서 first component-changing Z3 없음 |
| T4 | **증명됨** | 같은 family에서 pre-R2 bridge 없음 |

T4는 이전의 fixed-table Z2 lemma와 결합한다. 그 lemma는 q91 component가
확장되기 전 Z2가 hub와 합쳐질 수 없음을 증명했다. 이번 T3가 component-changing
Z3 확장 자체를 배제하므로 그 lemma의 invalidation condition은 발생하지 않는다.

이 결론을 arbitrary short root, arbitrary RR state, 또는 전체 초순열 문제로
확대하면 안 된다.

## 7. 독립 검증

`verify_rr_short_ell2_r1_37_hex82_closure.py`는 분석기의 backward/component
구현을 신뢰하지 않고 다음을 별도 재계산했다.

- 고정 표에서 다섯 route와 15개 w3 literal 역상
- q91:p2와 unique w2 source
- 84 anchor의 h40/full, terminal/source, q91:p2 조건
- 여섯 checkpoint SHA와 모든 stored edge literal replay
- route별 M1 합계 155,538
- M2–M5가 0이라는 count conservation

검증 결과:

```text
verified = true
nodes = 1,325,392
M1 = 155,538
M2-M5 = 0
```

회귀 테스트는 3/3 통과했다.

## 산출물

- `outputs/rr_short_ell2_r1_37_hex82_routes.json`
- `outputs/rr_short_ell2_r1_37_hex82_backward_closure.json`
- `outputs/rr_short_ell2_r1_37_hex82_mitm.json`
- `outputs/rr_short_ell2_r1_37_hex82_occupancy_audit.json`
- `outputs/rr_short_ell2_r1_37_hex82_verified.json`
- `src/analyze_rr_short_ell2_r1_37_hex82_closure.py`
- `src/verify_rr_short_ell2_r1_37_hex82_closure.py`
- `tests/test_rr_short_ell2_r1_37_hex82_closure.py`

최종 판정: `HEX82_ALL_FIVE_OBSTRUCTED`.
