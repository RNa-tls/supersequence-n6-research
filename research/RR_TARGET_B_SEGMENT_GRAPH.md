# Segment / full-block transition graph (라운드 32 §5–6, §12–13)

산출: `outputs/rr_segment_graphs.json`, `outputs/rr_full_block_transitions.json`.

## 1. 노드 정의 (§5)

\[
Q=(\text{orbit},\ \text{entry phase})
\]

를 사용한다. 과제가 제안한 확장 좌표(visited phase mask, R-used bit,
component signature)는 **의도적으로 넣지 않았다** — 그것들을 넣으면
graph가 상태 의존이 되어 "정적 graph"라고 부를 수 없고, 이번 라운드의
목적(정적 장애물 탐지)에 필요하지 않다. 대신 **sound
over-approximation**임을 명시한다: 방문 mask를 무시하므로 실제
transition system은 이 graph의 **부분graph**다.

## 2. Full-block graph \(G_{\mathrm{full}}\) (§6)

edge = "`EEEE` 실행 후 orbit-변경 exit".

| 항목 | 값 |
|---|---:|
| 노드 | 720 |
| 전이 | **1,440** |
| out-degree | **전 노드 정확히 2** (`w3:201`, `w3:210`) |
| in-degree 0 노드 | — |
| **dead end** | **0** |
| hexagon-disjoint 전이 | **720 / 1,440 = 정확히 절반** |
| graph SHA-256 | `outputs/rr_full_block_transitions.json` 참조 |

## 3. 정적 장애물 판정 (§12, §15)

| 검사 | 결과 |
|---|---|
| no outgoing block | **없음** — out-degree가 전부 2 |
| dead end / sink 부족 | **없음** |
| forced short block | **없음** — 모든 노드에서 `EEEE`가 가능(생성원 대수 수준) |
| SCC source/sink 다수 | **검사 불필요** — 2-regular out이고 dead end가 없어 판별력이 없다 |
| terminal suffix incompatibility | **없음** — 모든 미방문 hexagon이 5회 rotation suffix를 허용(라운드30) |

> **\(G_{\mathrm{full}}\)에서 나오는 정적 장애물은 하나도 없다.**
> graph가 지나치게 규칙적이라 판별력이 없다.

이것은 실패가 아니라 정보다: **Target B의 장애물은 graph 위상이 아니라
capacity 회계에서 나온다**는 것이 두 라운드 연속으로 확인됐다.

## 4. Maximum realizable segment chain (§13)

과제는 \(L_{\max}^{\mathrm{segment}}(S)<B+1\)이면 안전한 impossibility
certificate라고 했다. 그러나 \(G_{\mathrm{full}}\)이 dead end 없는
2-regular out graph이므로 **over-approximation 위에서의 최대 chain은
사실상 무제한**이고, 유한성은 오직 **자원 소모(hexagon/orbit/O 슬롯)**
에서 온다 — 그것이 바로 capacity bound다.

따라서 \(L_{\max}^{\mathrm{segment}}\)를 graph 탐색으로 계산하는 것은
capacity bound를 **다시 계산하는 것**과 같고, 더 강한 결과를 주지
않는다. **별도로 계산하지 않았다** — 회피가 아니라 중복이다.

## 5. Saturation contradiction (§14)

defect 예산이 0인 두 survivor(\(\ell=0,P=4\)와 \(\ell=4,P=4\))는
**모든 segment가 capacity 5**여야 한다. 그런데:

- \(\ell=4,P=4\): 초기 segment가 \(c(q_0)=3\)뿐 → **즉시 모순**(bound B).
- \(\ell=0,P=4\): 초기 segment 3 + top 105 + R 슬롯이 5를 줄 수 없음(≤4)
  → **모순**(bound B+R).

두 경우 모두 **capacity 회계에서 직접** 모순이 나오며 graph 경로 탐색이
필요 없다.

**등급**: graph **sound over-approximation**, 장애물 부재 **exact
segment graph** 관측, saturation 모순 **손증명**.
