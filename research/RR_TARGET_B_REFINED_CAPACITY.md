# Phase/port-aware refined capacity bound (라운드 31 Part B)

산출: `src/build_rr_refined_capacity_bound.py` ->
`outputs/rr_refined_phase_capacities.json`.

## 1. 정의

균일 bound는 segment마다 port 5개를 허용한다. 실제로는 port 하나가
쓸모 있으려면 **그 port의 hexagon이 아직 미방문**이어야 한다(각
hexagon은 정확히 한 macro-edge가 소비하므로).

\[
c(q)\;=\;\#\{\,\text{orbit }q\text{의 port 중 hexagon이 미방문인 것}\,\}
\in\{0,\dots,5\}
\]

**정련된 bound (안전)**:

\[
B+1 \;\le\;
c(q_0)\;+\;\sum_{\text{unopened }q\text{ 중 }c\text{ 상위 }O_{\mathrm{cap}}\text{개}} c(q)
\;+\;5R_{\mathrm{cap}}
\]

\(q_0\)는 걸음이 현재 서 있는 orbit이다. **상위 \(O_{\mathrm{cap}}\)개를
주는 것**이 상한임을 보장한다 — continuation은 어떤 unopened orbit이든
고를 수 있으므로 가장 좋은 것들을 허용한다.

## 2. 결과 — survivor 9개 중 **1개 추가 제거**

| \(\ell\) | \(P_{\mathrm{core}}\) | \(B+1\) | \(c(q_0)\) | 상위합 | \(5R_{\mathrm{cap}}\) | refined | uniform | 개선 | 모순 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 0 | 2 | 115 | 3 | 115 | 5 | 123 | 125 | 2 | 아니오 |
| 0 | 4 | 113 | 3 | 105 | 5 | 113 | 115 | 2 | 아니오 |
| 4 | 2 | 116 | 3 | 115 | 5 | 123 | 125 | 2 | 아니오 (×3) |
| **4** | **4** | **114** | 3 | 105 | 5 | **113** | 115 | 2 | **예** |
| 4 | 6 | 112 | 3 | 110 | 5 | 118 | 120 | 2 | 아니오 (×3) |

> **`REFINED_IMPOSSIBLE` 1개** (\(\ell=4,\ P_{\mathrm{core}}=4\),
> uniform margin이 \(+1\)이던 것). 나머지 8개는
> **`REFINED_SURVIVOR`**.

**개선폭은 9개 전부 정확히 2**이며, 그 2는 전적으로
\(c(q_0)=3\)(현재 orbit의 port 두 개가 이미 소비됨)에서 온다.
unopened orbit들은 거의 전부 \(c(q)=5\)라 상위합에서는 개선이 없다.

## 3. 왜 더 강해지지 않는가 — 정직한 진단

Target A 경계에서 방문된 hexagon은 4~9개뿐이다. hexagon 하나가 훼손하는
orbit-port 쌍은 6개이므로, 훼손되는 (orbit, port) 쌍은 최대 54개
(전체 720개 중). 따라서 **거의 모든 unopened orbit이 여전히 다섯 port를
전부 갖는다** — 정련이 물리지 않는 구조적 이유다.

\(\ell=4,P_{\mathrm{core}}=4\)만 제거된 것은 그 상태의 uniform margin이
이미 \(+1\)이어서 개선폭 2가 부호를 뒤집었기 때문이다.

## 4. §8·§9·§10에 대한 정직한 보고

- **§8 entry-port 분류**: `w3:201`과 `w3:210`이 fresh orbit에 들어갈 때의
  entry phase는 출발 port에 의존하며 고정되지 않는다. 그리고 \(E\)와
  \(E^2\)가 \(\mathbb{Z}_5\)를 생성하므로 **어떤 entry phase에서도
  나머지 네 phase에 도달 가능**하다 — 따라서 entry phase만으로는
  capacity가 줄지 않는다. **정련 효과 없음.**
- **§9 distinct target**: capacity가 서로 다른 hexagon을 센다는 것은
  \(c(q)\) 정의에 이미 들어 있다(각 orbit의 다섯 port는 서로 다른 다섯
  hexagon에 있다 — 라운드25에서 144 orbit 전부 확인).
- **§10 component-compatible capacity**: Target B가 요구하는 **최종**
  component 구조가 특성화돼 있지 않으므로 "유용한 opening"을 안전하게
  걸러낼 수 없다. **미완료** — heuristic으로 세지 않았다.

## 5. 판정

| 상태 | 수 |
|---|---:|
| `REFINED_IMPOSSIBLE` | **1** |
| `REFINED_SURVIVOR` | **8** |
| `INCOMPLETE_BOUND` | 0 |

**heuristic capacity를 prune으로 쓰지 않았다.** 위 bound는 전부
상한이며, 상위 \(O_{\mathrm{cap}}\)개를 주는 선택이 안전성을 보장한다.

**등급**: 정련된 bound **safe capacity bound**, 1개 제거
**exact obstruction**, §10 **미완료**.
