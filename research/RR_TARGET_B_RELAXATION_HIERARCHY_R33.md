# Relaxation hierarchy R33 — 층별 판정과 다음 모델 (라운드 33)

## 1. 층별 판정 요약

```
survivor            options  R1                  R3                       first failing layer
ell0_P2_33d70b42      9340   FEASIBLE (24 seg)   NO_ORDER_FOR_THIS_COVER   none
ell4_P2_5d3f8cb9      9529   FEASIBLE (25 seg)   NO_ORDER_FOR_THIS_COVER   none
ell4_P2_6f1ed828      9529   FEASIBLE (25 seg)   NO_ORDER_FOR_THIS_COVER   none
ell4_P2_fe82b0cd      9529   FEASIBLE (25 seg)   NO_ORDER_FOR_THIS_COVER   none
ell4_P6_9bd7590e      8811   INCOMPLETE          not reached               none
ell4_P6_cbfdf11e      8811   INCOMPLETE          not reached               none
ell4_P6_ec9025e8      8811   INCOMPLETE          not reached               none
```

`first failing layer`가 전부 `none`이다 — **어느 층도 소진되지
않았으므로 어느 층도 실패로 기록하지 않는다.**

## 2. 왜 cover-first 모델이 틀린 접근인지 — 정량적 근거

| survivor | segments | successor edges | 후계자 없는 segment | 최장 chain |
|---|---:|---:|---:|---:|
| ell0 P2 | 24 | **0** | 24 | 1 |
| ell4 P2 ×3 | 25 | **1** | 24 | 1 |

exact cover는 hexagon 분할만 요구하므로, 얻어지는 segment 집합은
**연결성을 전혀 고려하지 않는다.** 24–25개 중 후계 관계가 0–1개라는
것은 cover 공간이 flow 공간보다 **압도적으로 크다**는 뜻이다.

> **다음 모델은 flow-first여야 한다**: segment를 고르고 나서 순서를
> 붙이는 것이 아니라, **순서 있는 경로를 직접 성장시키면서** hexagon
> 자원을 소모하는 모델.

구체적으로: 노드 = (entry port, 사용된 hexagon 집합의 요약, \(O/R\)
잔량), 전이 = "preserving word + exit joint". full-block graph가
2-regular out이므로 분기 인자는 작다(≤2 exit × ≤5 word 선택). 깊이는
24–25 segment. 즉 **segment 층에서의 DFS는 permutation 층 depth-115
DFS보다 훨씬 작다** — 다음 라운드의 올바른 대상이다.

## 3. 이번 라운드에서 강해진 bound

\[
B+1\le
\underbrace{\operatorname{cap}^{\mathrm{walk}}_{\mathrm{init}}}_{=2,\ \text{이전 }3}
+\sum_{\text{top }O_{\mathrm{cap}}}c(q)+4R_{\mathrm{cap}}
\]

7개의 margin: 6 → 5 (ell0 P2), 5 → 4 (ell4 P6 ×3) 등. **부호는 바뀌지
않았다.**

## 4. 성공 기준 대비 (개정판 §9)

| 기준 | 결과 |
|---|---|
| 1. 7개 전부 exact-cover 정식화 | **완료** |
| 2. R0–R4 각각의 첫 실패 층 | **없음** — 소진된 층이 없다 |
| 3. R0–R4 전부 통과하는 survivor | **없음** (R3 미판정) |
| 4. 없다면 7개 전부 UNSAT인가 | **아니다** — UNSAT 0건. 이 결론은 이 7개 상태에 한정되며 Target B 전체에 대한 것이 **아니다** |

**7개를 못 줄인 것을 억지로 줄이지 않았다.**
