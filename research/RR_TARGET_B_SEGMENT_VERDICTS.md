# Segment-level 판정과 solver readiness (라운드 32 §15–17)

산출: `src/verify_rr_segment_certificates.py` -> `outputs/rr_segment_verdicts.json`.

## 1. 판정 (§15)

| \(\ell\) | \(P_{\mathrm{core}}\) | defect 예산 | 판정 |
|---:|---:|---:|---|
| 0 | 2 | 7 | `SEGMENT_SURVIVOR` |
| **0** | **4** | **0** | **`SEGMENT_CAPACITY_IMPOSSIBLE`** |
| 4 | 2 | 6 | `SEGMENT_SURVIVOR` (×3) |
| **4** | **4** | **0** | **`SEGMENT_CAPACITY_IMPOSSIBLE`** |
| 4 | 6 | 5 | `SEGMENT_SURVIVOR` (×3) |

**히스토그램**: `SEGMENT_SURVIVOR` **7**, `SEGMENT_CAPACITY_IMPOSSIBLE` **2**.

`FULL_BLOCK_GRAPH_IMPOSSIBLE`, `COMPONENT_CAPACITY_IMPOSSIBLE`,
`INCOMPLETE`는 **0건**이다.

## 2. Certificate (§16)

| \(\ell\)=0, \(P_{\mathrm{core}}\)=4 | 값 |
|---|---|
| 필요 segment 수 | 23 |
| 필요 full segment | 21 |
| defect 예산 | **0** |
| 최초 불가피 defect | **R 슬롯이 capacity-5 segment를 공급할 수 없다** — orbit-변경 R은 이미 열린 orbit에 착지하므로 capacity ≤4 |
| \(B{+}1\) / (A) / (B) / (B+R) | 113 / 115 / 113 / **112** |

| \(\ell\)=4, \(P_{\mathrm{core}}\)=4 | 값 |
|---|---|
| 필요 segment 수 | 23 |
| 필요 full segment | 22 |
| defect 예산 | **0** |
| 최초 불가피 defect | **초기 segment가 \(c(q_0)=3\) port만 공급** |
| \(B{+}1\) / (A) / (B) / (B+R) | 114 / 115 / **113** / 112 |

full-block graph SHA-256은 두 certificate에 함께 기록돼 있다.

## 3. 방법론 준수

- **"graph 경로를 못 찾음"을 불가능으로 쓰지 않았다.** 두 제거는 전부
  **capacity 회계**에서 나왔고 graph 탐색을 쓰지 않았다.
- **greedy hexagon-disjoint family는 최대값의 하한**이므로 장애물
  증명에 쓰지 않았다. 안전 상한
  \(\lfloor\#\text{미방문 hexagon}/5\rfloor\)만 판정에 썼고 그것은
  아무것도 차단하지 않는다.
- **unopened orbit이 많다는 이유로 capacity 5를 자동 부여하지
  않았다** — \(c(q)\)를 hexagon 가용성에서 실제로 계산했다.
- permutation-level depth-100 DFS **없음**.

## 4. Solver readiness (§17) — 남은 7개

| \(\ell\) | \(P_{\mathrm{core}}\) | segment 수 | 필요 full segment | defect 예산 |
|---:|---:|---:|---:|---:|
| 0 | 2 | 25 | 15 | 7 |
| 4 | 2 | 25 | 16 | 6 (×3) |
| 4 | 6 | 24 | 16 | 5 (×3) |

**다음 라운드용 판단**: full-block graph는 720 노드·1,440 전이로
**충분히 작다**. 그러나 §12에서 보았듯 위상적으로 판별력이 없으므로,
exact DP/SAT를 건다면 **graph 위가 아니라 자원 배분 위**에 걸어야 한다:

> 변수 = "어느 unopened orbit을 어느 순서로 열고 각 segment가 몇 개의
> port를 쓰는가", 제약 = O/R 슬롯, hexagon 서로소성, defect 예산 ≤ M,
> 총 port = \(B+1\).

이는 **exact cover / 다중집합 배분 ILP**이며 depth-100 DFS보다 훨씬
작다. 다만 component 조건이 미특성화라 완전한 인코딩은 아직 불가능하다.

## 5. 누적 결과

| 단계 | 남은 Target A 경계 |
|---|---:|
| 전체 | 18 |
| capacity theorem (R30) | 9 |
| initial-phase refinement (R31) | 8 |
| **orbit-reuse penalty (R32)** | **7** |

**등급**: 두 제거 **exact obstruction**, 나머지 7개 **safe segment
bound 통과 — 존재 주장 아님**, graph 장애물 **없음**, component 조건
**미완료**.
