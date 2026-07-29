# Port graph lift와 terminal 조건 (라운드 30 §8–9)

산출: `outputs/rr_target_b_port_graphs.json`.

## 1. 왜 lift가 필요한가

hexagon 층위 edge \(H\to H'\)가 존재해도 **entry port와 exit port가
양립하지 않을 수 있다.** \(\ell=5\) macro-edge에서

\[
\text{exit port} = \text{entry port}\circ\Sigma^5,
\qquad
\text{next entry port} = \text{entry port}\circ g_j ,
\]

즉 **exit이 entry로 완전히 결정**된다. 따라서 \(H\)의 어느 port로
들어왔는지에 따라 갈 수 있는 \(H'\)가 달라진다.

> 그러므로 vertex는 \((H,\text{entry port})\), 즉 **permutation**이어야
> 한다. hexagon 층위 Hamiltonian path는 **false positive를 만든다.**

## 2. Port 그래프 수치

| # | port 수 | edge 수 | out-degree 히스토그램 |
|---:|---:|---:|---|
| 0 | 660 | 1,75x | `{0:1, 1:34, 2:121, 3:504}` |
| 2 | 642 | 1,704 | `{0:5, 1:48, 2:111, 3:478}` |
| 3 | 642 | 1,700 | `{0:4, 1:48, 2:118, 3:472}` |
| 4 | 642 | 1,697 | `{0:5, 1:45, 2:124, 3:468}` |
| 5 | 642 | 1,695 | `{0:4, 1:45, 2:129, 3:464}` |

out-degree 상한이 **3**인 것은 `w3:120`이 항상 R이라 제거되기 때문이다
(손증명).

## 3. Terminal 조건 (§9)

마지막 hexagon은 **5회 pure rotation**으로 완성된다. 그 hexagon이
완전히 미방문이면 5회 rotation이 항상 가능하므로, **모든 미방문
hexagon의 모든 port가 terminal-compatible**이다.

> 따라서 terminal 조건은 **판별력이 없다** — sink 후보를 전혀 줄이지
> 못한다. `TERMINAL_OBSTRUCTION`은 발생하지 않는다.

## 4. degree / SCC / cut 검사의 지위

out-degree 0인 port가 1~5개, in-degree 0인 port가 7~13개 있으나
**이것들은 장애물이 아니다**: hexagon은 다른 port로도 진입할 수 있고,
Hamiltonian path는 hexagon마다 **하나의** port만 쓰면 된다.

SCC·cut 검사는 이번 라운드에 **수행하지 않았다.** 이유는 회피가 아니라
불필요다 — `RR_TARGET_B_STATIC_OBSTRUCTIONS.md`의 계수 장애물이
여섯 상태를 **전부** 제거했으므로, 그래프 탐색 기반 장애물을 찾을
대상이 남아 있지 않다.

> 짧은 preparation 경계(장애물을 통과하는 9/12)에 대해 Target B를
> 묻게 되면 그때 SCC·cut·forced-edge propagation이 필요해진다.
> 그 경우를 위해 port lift와 그래프 빌더는 그대로 남겨 둔다.

**등급**: lift 필요성 **손증명**, 수치 **exact graph reduction**,
terminal 조건의 무판별력 **손증명**, SCC/cut **미완료 (불필요)**.
