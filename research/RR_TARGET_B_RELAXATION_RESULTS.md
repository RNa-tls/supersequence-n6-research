# R0–R5 relaxation 결과 (라운드 33 §5, §15–17, §19)

산출: `src/solve_rr_target_b_relaxations.py` ->
`outputs/rr_target_b_relaxation_results.json`,
`outputs/rr_target_b_reconstructed_solutions.json`.

## 1. 층 정의와 의미 (§14)

| 층 | 내용 | infeasible의 의미 |
|---|---|---|
| R0 | capacity count | Target B 불가능 (라운드32에서 이미 사용) |
| R1 | hexagon exact cover | Target B 불가능 — **단, 탐색이 소진됐을 때만** |
| R2 | port uniqueness | **R1에서 유도됨 — 별도 제약이 아니다** |
| R3 | segment flow / order | Target B 불가능 — cover 전수 열거가 필요 |
| R4 | literal collision (engine replay) | Target B 불가능 |
| R5 | component compatibility | **necessary-condition only** |

**R2 ⟸ R1 (손증명)**: 각 option은 자기가 덮는 hexagon마다 정확히 하나의
port를 쓰고, orbit의 다섯 port는 **서로 다른 다섯 hexagon**에 있다.
따라서 hexagon 분할이면 같은 port가 두 번 쓰일 수 없다. port uniqueness는
R1 위에서 **자동**이다.

## 2. 결과

| survivor | option | R1 | 전략 | segments | capacity | R3 |
|---|---:|---|---|---:|---:|---|
| ell0 P2 | 9,340 | **FEASIBLE** | partition-seeded | 24 | 115 | `NO_ORDER_FOR_THIS_COVER` |
| ell4 P2 #1 | 9,529 | **FEASIBLE** | partition-seeded | 25 | 116 | 〃 |
| ell4 P2 #2 | 9,529 | **FEASIBLE** | partition-seeded | 25 | 116 | 〃 |
| ell4 P2 #3 | 9,529 | **FEASIBLE** | partition-seeded | 25 | 116 | 〃 |
| ell4 P6 ×3 | 8,811 | **INCOMPLETE** | algorithm-X 절단 | — | — | 미도달 |

R1 histogram: `{FEASIBLE: 4, INCOMPLETE: 3}`.
**`EXHAUSTED_INFEASIBLE`은 0건** — 따라서 이 라운드는
**UNSAT certificate를 하나도 발급하지 않는다.**

## 3. 이번 라운드의 핵심 발견 — cover는 판별력이 없다

R1 FEASIBLE인 4개의 cover를 flow 관점에서 보면:

| survivor | segments | successor edge 수 | 후계자 없는 segment | 최장 chain |
|---|---:|---:|---:|---:|
| ell0 P2 | 24 | **0** | 24 | **1** |
| ell4 P2 (×3) | 25 | **1** | 24 | **1** |

> **24–25개 segment 사이의 successor edge가 0개 또는 1개다.**
> exact cover가 만들어 준 segment 집합은 flow 관점에서 **거의 완전히
> 단절**돼 있다.

즉 **R1은 사실상 아무 정보도 주지 않는다** — hexagon 분할은 쉽게
만족되고, 진짜 병목은 **R3(순서/연결)** 이다. 이는 개정판 지시가
"처음부터 순서 있는 모델이어야 한다"고 한 이유를 정량적으로 확인한
것이다.

## 4. 방법론 — R3 실패를 장애물로 쓰지 않았다

각 survivor에서 **cover 하나**만 만들었고 그 cover가 순서를 갖지
않았다. 그것은 **R3 infeasible이 아니다** — 같은 상태의 다른 cover는
순서를 가질 수 있다. 따라서:

- R3 상태는 `NO_ORDER_FOR_THIS_COVER`로 기록했고,
- `first_failing_layer`는 **`None`** 이다 (R3이 아니다),
- R3을 장애물로 만들려면 **cover 전수 열거**가 필요하고 하지 않았다.

`src/verify_rr_target_b_unsat.py`의 감사가 이 규율을 기계적으로
검사한다: **위반 0건**, UNSAT certificate 0건.

## 5. 성공 기준 대비

| 기준 | 결과 |
|---|---|
| 1. segment-option exact-cover 정식화 | **완료** — 7개 전부, engine 검증 7/7 |
| 2. R0–R4 첫 실패 층 | **없음** — 4개는 R1 통과, 3개는 R1 미판정 |
| 3. R0–R4 전부 통과하는 survivor | **없음** (R3에서 undecided) |
| 4. component가 진짜 병목인가 | **아니다 — R3이 먼저 병목이다** |
| 5. 독립 검증 가능한 UNSAT 또는 candidate | **UNSAT 없음.** R1-layer cover 4개를 witness로 저장(단, Target B 해가 **아님**) |

## 6. 명시적 경고

`outputs/rr_target_b_reconstructed_solutions.json`의 cover 4개는
**R1 층의 cover일 뿐**이다. segment 순서(R3), literal collision(R4),
component 양립성(R5)을 전부 무시한다. **이것을 Target B 해라고 부르지
않는다.**

**등급**: R1 FEASIBLE 4개 **exact allocation model**(구성적 증거),
R1 INCOMPLETE 3개 **bounded incomplete**, R2 **손증명**,
R3 **미완료**, R4·R5 **미완료**.
