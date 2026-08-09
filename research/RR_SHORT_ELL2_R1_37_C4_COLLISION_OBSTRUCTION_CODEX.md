# Round 60 — `short_ell2_r1_37` C4 exact-collision obstruction audit

작성자: Codex

## 결론

이 라운드는 여섯 immutable Stage-D parent DAG를 literal replay하여 Round 59의
`C4 = 253,537` 시도를 모두 다시 분류했다. 합계는 정확히 보존되었다.

- exact local collision signatures: **86**
- proved left-`S6` canonical signatures: **17**
- nonzero engine mechanism families: **1**
- `K0` (목표 permutation window가 attempted macro 이전에 이미 방문됨): **253,537**
- `K1`–`K6`: **0** (`K5`, current tentative rotation overlap도 0)
- 최초 도입 위치: **253,537/253,537 모두 PRE_STAGE_D_ANCHOR**
- first-touch taxonomy: `T2 = 253,537`, 나머지 `T0/T1/T3/T4 = 0`

따라서 **모든 관측 C4 시도는 exact collision**이라는 Round 59의 결과는 유한
완전 검증되었다. 그러나 미관측 C4 prerequisite state 전체의 유한 closure는
얻지 못했으므로 최종 강도는 `T2`, 즉 관측 corpus 정리다. `T2+`, `T3`, `T4`는
주장하지 않는다.

## 1. 실제 엔진 collision 의미

`superperm_partial_f1.extend(state, move)`는 literal target permutation window가
이미 방문됐을 때만 `None`을 반환한다. 따라서 제안된 taxonomy를 엔진 의미에
맞추면 다음과 같다.

| family | exact 의미 | count |
|---|---|---:|
| K0 | attempted macro 시작 전에 target window 방문 | 253,537 |
| K1 | incidence edge occupied라는 별도 엔진 rejection | 0 |
| K2 | hex registration이라는 별도 엔진 rejection | 0 |
| K3 | orbit registration이라는 별도 엔진 rejection | 0 |
| K4 | component-cycle이라는 별도 엔진 rejection | 0 |
| K5 | 같은 tentative rotation prefix에서 target이 먼저 등장 | 0 |
| K6 | 기타 exact collision | 0 |

K1–K4는 component 해석에서 유용한 설명일 수는 있지만 이 exact engine의 독립
rejection reason은 아니다. 이를 K0과 중복 집계하지 않았다.

## 2. 서명과 provenance

각 C4 대표는 다음을 보존한다.

- candidate/source orbit과 phase
- rotation length, weight-3 joint, target hex/position
- collided permutation window
- 그 window가 처음 도입된 immutable anchor 또는 stored macro edge
- R1 provenance, component partition digest, 자원 좌표
- 최초 도입점부터 rejected C4 joint 직전까지의 full stored macro suffix

exact signature는 이 literal 좌표를 quotient하지 않는다. canonical signature는
오직 증명된 전역 값 재명명 좌 `S6` 작용을 사용하고, literal joint source를
identity로 보내는 유일한 재명명으로 local words를 운반한다. heuristic profile,
임의 orbit relabel, history quotient는 사용하지 않았다.

## 3. candidate별 C4 분포

| orbit | hub touch | C4 | min macro depth | observed C4 target hex |
|---:|:---:|---:|---:|---|
| 36 | no | 16,802 | 53 | 40 |
| 40 | no | 41,712 | 48 | 40 |
| 41 | no | 10,618 | 51 | 40 |
| 42 | no | 34,703 | 53 | 40 |
| 72 | no | 0 | — | — |
| 74 | no | 0 | — | — |
| 78 | no | 24,942 | 49 | 92 |
| 82 | no | 0 | — | — |
| 83 | no | 0 | — | — |
| 90 | no | 0 | — | — |
| 92 | no | 0 | — | — |
| 93 | no | 31,270 | 49 | 92 |
| 95 | no | 0 | — | — |
| 96 | yes | 0 | — | — |
| 98 | no | 0 | — | — |
| 102 | no | 31,699 | 50 | 92 |
| 120 | yes | 0 | — | — |
| 126 | yes | 28,531 | 52 | 40 |
| 128 | yes | 0 | — | — |
| 129 | yes | 33,260 | 52 | 92 |

관측된 C4 target은 hex 40 또는 92뿐이며 두 hex의 mask는 모든 시도에서 63이었다.
후보마다 다른 count와 도달 level이 있으므로 “모든 20 orbit이 같은 reachable
collision class를 갖는다”는 명제는 거짓이다. 다만 발생한 C4 rejection의 exact
mechanism은 모두 K0으로 같다.

## 4. first-touch 및 registration order

C4 prerequisite는 candidate orbit의 pass-start mask가 0임을 요구한다. 따라서
candidate orbit은 아직 **등록되지 않았지만**, 그 qualifying target permutation
window 자체는 과거 rotation/pass에서 이미 방문될 수 있다. 실제로 253,537건
전부가 이 경우다.

| class | count | 판정 |
|---|---:|---|
| T0 wrong phase | 0 | C4 prerequisite가 제거 |
| T1 correct phase, same-macro first touch then collision | 0 | 부재 |
| T2 prior literal touch breaks direct FZ1 | 253,537 | 전수 |
| T3 continuous-residency delayed-Z2 candidate | 0 | candidate가 fresh이므로 부재 |
| T4 realizable FZ1 | 0 | 부재 |

즉 “orbit 미등록”과 “그 orbit의 특정 permutation window 미방문”은 같은 조건이
아니다. 관측 obstruction은 바로 이 차이에서 발생한다.

## 5. 강제 precedence와 네 full-hex 부분정리

84개 Stage-D 시작점의 orbit-91 phase-linked hex mask는 다음과 같다.

- hex 40, 90, 91, 92: **84/84 모두 63**
- hex 82: `0×81, 2×1, 4×1, 63×1`

exact transition은 hex mask의 bit를 제거하지 않는다. 따라서 다음은 손증명된다.

> Stage-D의 84개 시작점의 임의 후손에서, C4 prerequisite target이 hex
> 40·90·91·92 중 하나에 있으면 그 target permutation은 이미 방문됐으므로
> weight-3 joint는 반드시 exact collision한다.

이 명제의 선행사건 `A`는 해당 hex의 Stage-D 이전 완전 방문이다. `A`가 모든
후손에서 유지되고 candidate joint가 그 hex의 한 window를 요구하므로 충돌한다.

### hub-touching five

- `q96`: hub 접촉 후보, R1 접촉 hex 90 — 위 단조성 정리로 C4 route 배제
- `q120`: hex 90 — 동일
- `q126`: hex 40/91 — 동일; 관측 C4 28,531건은 hex 40 K0
- `q129`: hex 92 — 동일; 관측 C4 33,260건
- `q128`: hex 82 — **미해결**

## 6. 남은 hex-82 route

고정 table에서 남는 local route는 정확히 다섯 개다.

| candidate | phase | hex position |
|---:|---:|---:|
| 42 | 1 | 2 |
| 78 | 3 | 4 |
| 82 | 0 | 0 |
| 83 | 4 | 5 |
| 128 | 2 | 1 |

이 다섯 route의 관측 C4 count는 모두 0이다. 일부 candidate(q42, q78)는 다른
full-hex phase에서 C4가 관측됐지만 hex-82 phase에서는 관측되지 않았다.

다섯 local route를 다섯 exact SAT state로 간주할 수는 없다. hex masks,
orbit masks, component partition, R1 provenance 및 macro history가 다른 다수의
전역 상태가 같은 local route로 투영될 수 있고, 그 continuation equivalence는
증명되지 않았다. 따라서 불완전한 local SAT encoding으로 UNSAT를 주장하지 않았다.

## 7. predecessor closure

- observed C4 source nodes: ledger에 branch별 기록
- exact observed-parent-DAG predecessor closure: **712,083 nodes**
- closure는 frozen DAG 안에서 안정화됨
- frozen DAG 밖의 새로운 exact C4-compatible state는 열거하지 않음

이 closure는 관측 C4의 exact ancestry certificate이지, 가능한 모든 C4 prerequisite
state의 역방향 생성기가 아니다. 따라서 `complete_finite_C4_prerequisite_closure=false`다.

## 8. theorem ladder

- **T1:** Stage-D/Stage-E bounded search — 기존 결과
- **T2:** 모든 관측 C4 253,537건 collision — **유한 완전 검증**
- **별도 손증명:** four-full-hex C4 route obstruction
- **T2+:** 미달; hex-82의 exact global provenance closure 없음
- **T3:** 미달; first component-changing Z3 전체 불가능을 증명하지 않음
- **T4:** 미달; pre-R2 bridge 전체 불가능을 증명하지 않음

따라서 현재 정확한 결론은 `C4_COLLISION_FINITE_CLOSURE_INCOMPLETE`다.
