# |P| 짝수성 — 제안된 증명 경로의 반증 (라운드 22)

산출: `src/verify_rr_preparation_parity.py`(라운드21) +
라운드22의 불변량 탐색. `outputs/rr_preparation_parity_certificates.json`.

## 0. 자기 정정 — 첫 측정이 잘못된 경계를 봤다

이번 라운드의 첫 불변량 탐색은 `visited_count`, `n_hexes`,
`popcount_orbits`, `P` 넷이 모든 preparation edge에서 뒤집힌다고
보고했다. **그 측정은 틀렸다** — `edge.run.state`(회전 **후**)와
`joint.state`를 비교해 **macro-edge 전체가 아니라 joint 한 칸만**
쟀기 때문이다.

올바른 macro-edge 경계로 다시 재면(48개 preparation edge 전수):

| 양 | 증분 | 짝수성 |
|---|---:|---|
| `visited_count` | **+6** (48/48) | 뒤집지 **않음** |
| `n_hexes`(터치된 hexagon 수) | **+1** (48/48) | 뒤집음 |
| `P`(pass 수) | **+1** (48/48) | 뒤집음 |
| 사용된 `ell` | 항상 **5** (48/48) | — |

## 3-4. 2-색칠 경로는 반증됐다

§3이 제안한 \(\pi(Q)\in\mathbb Z/2\) 불변량 후보 15개를 올바른
경계에서 전수 검사했다: `sign(p)`, hexagon/orbit/phase parity,
`p_0,p_1,p_5` parity, `O`, `S`, 방문 orbit 수, incidence graph에서
hub까지의 hexagon/orbit 거리 parity, orbit 내 위치 parity, 그리고
그 합들.

> **결과: 모든 preparation edge에서 뒤집히는 것은 `n_hexes`와 `P`
> 둘뿐이며, 이 둘은 macro-edge마다 정확히 +1인 순수 계수기다.**

따라서 "start와 completer-ready가 같은 색이다"라는 명제는
**"edge 수가 짝수다"의 동어반복**이 되어 증명이 되지 못한다.
`n_hexes`는 root에서 2, completer-ready에서 4/6/8이므로
\(|P| = n_{\text{hex}}^{\text{CR}} - 2\)이고, 짝수성은
"completer-ready의 `n_hexes`가 짝수"와 **동치**일 뿐이다.

§4의 bipartite 질문도 같은 이유로 무너진다: preparation 전이 그래프는
`n_hexes`로 **등급화(graded)** 되어 있어 자동으로 bipartite이지만,
그 bipartition이 곧 edge 수 parity이므로 새 정보를 주지 않는다.

> **판정: §3·§4가 제안한 증명 전략은 반증됨.** 비자명한 mod-2
> 불변량은 존재하지 않는다(검사한 15개 후보 범위 안에서).

## 남은 정확한 형태

\(|P|\) 짝수성은 다음과 **동치**로 축약됐다:

> **completer-ready 경계에서 터치된 hexagon 수가 짝수다.**

이를 독립적으로 특징짓지 못했다 — **성공 기준 1은 미달성**이며,
제안된 경로가 왜 작동할 수 없는지를 정확히 규명한 것이 이번
라운드의 결과다.

## 여전히 유효한 손증명 (라운드21)

분기별 **차이**는 이미 손증명돼 있고 이번 결과에 영향받지 않는다:
tail 길이 \(|T_\ell|\)는 \(\ell=4\)에서 0, \(\ell\ne4\)에서 1이며
(Hub Exit Source Lemma + \(O_*=\mathrm{HEX0POS}[\ell+1]\)),
\(\Phi(R_2)=0\)은 \((5-\ell)+(1+\ell)=6\)에서 \(\ell\)과 무관하게
자동이다. 즉 **공통 인자 \(|P|\)의 짝수성 하나만이 미완료로 남는다.**
