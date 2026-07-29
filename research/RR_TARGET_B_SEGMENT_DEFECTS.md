# Segment defect budget과 orbit reuse penalty (라운드 32 §7–11)

산출: `outputs/rr_segment_defect_budgets.json`,
`outputs/rr_short_survivor_ledger.json`.

## 1. Defect 정의와 예산 (§7)

\(d_i=5-\operatorname{cap}(S_i)\), \(\sum_i d_i\le M\) (refined margin).

| \(\ell\) | \(P_{\mathrm{core}}\) | segment 수 \(m{+}1\) | 필요 full segment \(f_{\min}\) | defect 예산 |
|---:|---:|---:|---:|---:|
| 0 | 2 | 25 | 15 | **7** |
| 0 | 4 | 23 | 21 | **0** |
| 4 | 2 | 25 | 16 | **6** (×3) |
| 4 | 4 | 23 | 22 | **0** |
| 4 | 6 | 24 | 16 | **5** (×3) |

\(f_{\min}=(B{+}1)-4(m{+}1)\): 모든 segment가 capacity 4라도
\(B{+}1\)에 못 미치므로 최소 그만큼은 capacity 5여야 한다.

## 2. Defect-budget 정리 (§8) — 각 비효율의 최소 손실

| 비효율 | 최소 defect | 근거 |
|---|---:|---|
| 보존 run 길이 3 | **1** | capacity 4 (전수표) |
| 보존 run 길이 2 | 2 | capacity 3 |
| entry phase가 이미 방문됨 | ≥1 | 그 port를 쓸 수 없다 |
| port의 hexagon이 이미 방문됨 | ≥1 | §10의 distinct-hexagon 조건 |
| **orbit-변경 R로 진입** | **≥1** | §3 아래 |
| \(E^2\) 사용 | R 슬롯 소모 → 이후 R-변경 불가 | \(R_{\mathrm{cap}}=1\) |

각 항목은 그 segment의 capacity를 5보다 작게 만들고
\(B+1\le\sum\operatorname{cap}(S_i)\)의 우변을 그만큼 줄인다. **손증명.**

## 3. Orbit reuse penalty (§9) — 이번 라운드의 결정적 재료

> **Lemma (손증명)**: orbit-변경 **R** edge로 진입한 segment의
> capacity는 **최대 4**다.
>
> **증명**: 그 edge가 fresh opening이 아니라 R인 이유는 정확히
> `new_orbit=False`, 즉 **target orbit이 이미 열려 있다**는 것이다.
> 열린 orbit에는 방문된 port가 최소 하나 있으므로 남은 사용 가능 port는
> 최대 4다. ∎

따라서 refined bound의 \(5R_{\mathrm{cap}}\) 항은 **과대평가**이며
\(4R_{\mathrm{cap}}\)로 교체해야 한다:

\[
B+1\le c(q_0)+\sum_{\text{top }O_{\mathrm{cap}}}c(q)+4R_{\mathrm{cap}} .
\]

**효과**: \(\ell=0,P_{\mathrm{core}}=4\) survivor가 \(113\le113\)에서
\(113>112\)로 뒤집혀 **제거된다**. survivor 8 → **7**.

## 4. Distinct-hexagon 조건 (§10)

`EEEE`가 capacity 5로 세어지려면 그 orbit의 **다섯 port가 서로 다른
다섯 hexagon에 있고 모두 미방문**이어야 한다.

- 첫 조건은 **항상 참**: 144개 orbit 전부 port가 5개의 서로 다른
  hexagon에 있다(라운드25에서 확인, 재확인함).
- 둘째 조건이 \(c(q)\)의 정의이며, \(c(q)<5\)이면 defect가
  \(5-c(q)\)만큼 생긴다.

**전역 상한**: hexagon 120개, orbit당 5개 ⟹ 서로소 orbit family는
최대 **24**개. 실제로 **완전 분할이 존재**한다(greedy가 24개로 120개를
전부 덮음). 따라서 전역 수준에서는 **모순이 없다**.

**survivor별 안전 판정**:

| \(\ell\) | \(P_{\mathrm{core}}\) | \(f_{\min}\) | greedy(하한) | **안전 상한** \(\lfloor \#\text{미방문 hex}/5\rfloor\) | 차단? |
|---:|---:|---:|---:|---:|:---:|
| 0 | 2 | 15 | 21 | 22 | 아니오 |
| 0 | 4 | 21 | 20 | 22 | 아니오 |
| 4 | 2 | 16 | 21–22 | 23 | 아니오 |
| 4 | 4 | 22 | 20 | 22 | 아니오 |
| 4 | 6 | 16 | 18–21 | 22 | 아니오 |

> **주의 — 방법론**: greedy가 만든 서로소 family는 최대값의 **하한**
> 이므로 **장애물 증명에 쓸 수 없다**. 실제로 \(\ell=0,P=4\)와
> \(\ell=4,P=4\)에서 greedy(20) \(<f_{\min}\)(21, 22)이지만
> 그것은 greedy가 최적이 아닐 뿐이다. 판정에는 **안전 상한**
> \(\lfloor\#\text{미방문 hexagon}/5\rfloor\)만 썼고, 그것은
> **아무것도 차단하지 못한다**.

## 5. Component-compatible capacity (§11) — 여전히 미완료

Target B의 **최종** component 구조가 특성화돼 있지 않으므로
"유용한 opening"을 안전하게 걸러낼 수 없다. 과제가 허용한 안전 조건
(irreversible isolated component, terminal 연결 불가, forced endpoint
2개 이상, hub touch 초과)은 최종 구조를 알아야 판정 가능하다.

**heuristic은 쓰지 않았다. 미완료.**

**등급**: defect 정리와 orbit reuse penalty **손증명**,
distinct-hexagon 전역 상한 **exact segment graph**,
survivor별 판정 **safe segment bound**, component capacity **미완료**.
