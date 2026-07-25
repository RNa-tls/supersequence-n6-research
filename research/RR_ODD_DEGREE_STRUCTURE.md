# Preparation incidence graph의 degree 구조 (라운드 23)

산출: `src/analyze_rr_preparation_graph.py` ->
`outputs/rr_parity_graph_certificates.json`. completion search 없음.

## 0. 자기 정정 — 예측한 degree ledger가 틀렸다

이 라운드는 먼저 "모든 preparation edge가 `rot^5`로 hexagon을 완전
sweep하므로 지나온 hexagon의 degree는 6"이라고 예측했다.
**측정이 이를 반증했다.**

`orbit_masks`는 **joint로 등록된 (orbit,phase) 쌍만** 기록하고
회전 스텝은 기록하지 않는다. 따라서 실제 incidence graph는 훨씬
성기다.

## 1-2. 측정된 degree ledger (12/12 전수)

| 양 | 값 | 확인 |
|---|---|---|
| incidence 간선 수 \(\vert E\vert\) | **\(k+2\)** | 4·6·8 (\(k=2,4,6\)) |
| 터치된 hexagon 수 | **\(k+2\)** | 4·6·8 |
| 각 hexagon의 degree | **1** (전부 홀수) | `odd_degree_hexagons`가 항상 전체 hexagon 집합 |
| 터치된 orbit 수 \(n_O\) | 2~7로 다양 | — |
| 컴포넌트 수 \(c\) | **항상 \(n_O\)와 동일** | 12/12 |
| forest 여부 | **참** | 12/12 |

즉 preparation incidence graph는 **각 orbit이 자기 컴포넌트를 이루고
각 hexagon이 정확히 하나의 orbit에 매달린 별(star)들의 분리합집합**
이다.

## 3-5. 세 경로 모두 parity를 주지 못한다 (반증됨)

### Handshake
모든 hexagon의 degree가 1이므로 \(\vert E\vert = k+2\) —
**\(k\)의 선형함수**라 parity 정보가 새로 나오지 않는다.

### Odd-degree 정리
홀수 degree 정점은 **모든** hexagon(각 degree 1)이므로 개수는
\(k+2\)다. §3이 제안한 "홀수 degree 정점이 고정된 짝수 개"라는
형태가 **성립하지 않는다.**

### Forest 항등식
\(\vert E\vert = \vert V\vert - c\)에 대입하면
\(k+2 = (k+2)+n_O-c\), 즉 **\(n_O=c\)** 라는 항등식으로 퇴화한다 —
\(k\)가 양변에서 소거되어 parity에 대해 아무 말도 하지 않는다.

> **§1-§5·§6-§7이 제안한 degree/handshake/forest/pairing 경로는
> 전부 반증됨.** 근본 이유는 공통이다: **모든 preparation edge가
> 동일한 degree 변화(간선 +1, hexagon +1)를 만들므로, degree 기반
> 어떤 양도 edge 수의 선형함수가 되어 parity를 새로 제약하지
> 못한다** — 라운드22가 `n_hexes`/`P`에서 지적한 순환과 같은 구조다.

## 9. Witness별 certificate

12개 witness 전부의 degree ledger·forest 판정·컴포넌트 수를
`outputs/rr_parity_graph_certificates.json`의
`section1_5_degree_ledger.per_witness`에 기록했다.

**추출된 공통 증명 패턴은 degree가 아니다** — 실제로 parity를
만드는 것은 "completer까지 R이 정확히 하나"라는 조건이며,
`RR_PREPARATION_GRAPH_PARITY.md`가 이를 다룬다.

**성공 기준 2 평가: 달성(결과는 부정적)** — odd-degree 구조를
정확히 특징지었고(모든 hexagon이 degree 1), 그것이 parity를 줄 수
없음을 확정했다.
