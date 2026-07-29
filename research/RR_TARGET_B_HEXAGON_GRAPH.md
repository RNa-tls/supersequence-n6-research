# Target B 잔여 hexagon / port 그래프 — 정확한 모델 (라운드 30 Part A)

산출: `src/build_rr_target_b_hexagon_graph.py` ->
`outputs/rr_target_b_hexagon_graphs.json`,
`outputs/rr_target_b_port_graphs.json`. **대형 DFS 없음.**
N=0 checkpoint 미접촉.

## 1. 그래프 정의 (§1)

\(\Phi=0\)에서 모든 macro-edge는 \(\ell=5\)다(라운드29 손증명).
entry permutation \(p\)에서 그런 edge는 \(p\Sigma,\dots,p\Sigma^5\)로
\(p\)의 hexagon을 **완성**하고 \(p\Sigma^5\)에서 joint을 쏘아

\[
p\circ\Sigma^5\circ a_j \;=\; p\circ g_j
\]

에 착지한다. 라운드26의 합성 생성원:

| 조인트 | \(g_j\) | \(\langle E\rangle\) |
|---|---|---|
| `w2:10` | \(E\) | **보존** |
| `w3:120` | \(E^2\) | **보존** |
| `w3:201` | — | 아니오 |
| `w3:210` | — | 아니오 |

> 따라서 자연스러운 대상은 **permutation 위의 port 그래프**
> \(p\to p\circ g_j\)이며, 이는 **완전히 정적**이다.

## 2. 그래프는 정적인가 (§2) — 정확한 모델 선언

| 층위 | 성질 |
|---|---|
| **port 그래프** \(p\to p\circ g_j\) | **static digraph** (out-degree 4) |
| **hexagon 그래프** \(H\to H'\) | **static이 아니다** — 도달 가능한 \(H'\)는 \(H\)의 **어느 port로 진입했는지**에 의존 |
| legality | **vertex deletion** — target hexagon이 전부 미방문이어야 함(5회 rotation이 충돌하면 안 됨) |

> **정확한 모델**: *정적 port digraph + hexagon 층위 vertex deletion*.
> Target B continuation은 **남은 hexagon마다 정확히 하나의 port를
> 쓰는 self-avoiding path**다.
>
> "hexagon-level Hamiltonian path"만 쓰면 **false positive가 생긴다** —
> 이것이 §8의 port lift가 필요한 이유이고, 이 문서가 그 lift를
> 처음부터 사용하는 이유다.

## 3. 안전한 over-approximation

edge는 **정적으로 불가능할 때만** 제거한다. 따라서 여기서 발견되는
장애물은 **진짜 장애물**이다.

제거 규칙(전부 손증명):

| 규칙 | 근거 |
|---|---|
| target hexagon이 미방문이 아님 | 5회 rotation 충돌 |
| `w3:120` | \(E^2\)는 orbit 보존 ⟹ 절대 new_orbit 아님 ⟹ weight-3이므로 **항상 R** |
| `w3:201`/`w3:210`이면서 target orbit이 **시작 시점에 이미 열림** | orbit은 열리기만 하므로 영원히 fresh가 될 수 없다 ⟹ 항상 R |

## 4. 실측 (§3, §11)

| # | 미방문 hexagon | port | edge | start hexagon | start out-degree |
|---:|---:|---:|---:|---:|---:|
| 0,1 | **110** | 660 | ≈1,75x | 18 | **3** |
| 2–5 | **107** | 642 | ≈1,70x | 18 | **3** |

start의 세 edge는 여섯 상태 전부 동일하게
`w2:10`, `w3:201`, `w3:210`이다 — `w3:120`은 위 규칙으로 항상 제거된다.

port out-degree 히스토그램(예: w0) `{0:1, 1:34, 2:121, 3:504}`,
제거 사유 `{w3:120 always R: 607, target hexagon not untouched: 213,
orbit already open: 33}`.

각 그래프에 **SHA-256**을 붙여 `outputs/rr_target_b_hexagon_graphs.json`에
기록했다(vertex/edge 수, degree 히스토그램, start edge, 제거 사유 포함).

## 5. 이 문서가 주장하지 않는 것

port 그래프의 degree 분포만으로는 **어떤 장애물도 주장하지 않는다**.
out-degree 0인 port가 1~5개 있으나, hexagon은 다른 port로도 진입할 수
있으므로 그 자체로는 장애물이 아니다. 실제 장애물은
`RR_TARGET_B_STATIC_OBSTRUCTIONS.md`의 **계수 논증**에서 나온다.

**등급**: 모델 선언 **손증명**, over-approximation 규칙 **손증명**,
그래프 수치 **exact graph reduction**.
