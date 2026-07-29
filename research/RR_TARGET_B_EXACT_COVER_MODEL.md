# Target B segment-option exact-cover 모델 (라운드 33 §1–4, §8–13)

산출: `src/build_rr_target_b_exact_cover.py` ->
`outputs/rr_segment_options.json`, `outputs/rr_target_b_ilp_models.json`.
**permutation-level DFS 없음.** N=0 checkpoint 미접촉. long six는 이미
손증명으로 닫혔으므로 재탐색하지 않았다. full-block graph의 degree/SCC는
다시 분석하지 않았다.

산출물 이름 대응: 이 파일들이 §23 이름이고,
`rr_segment_options.json`은 개정판 목록의 `rr_segment_options_r33.json`과
동일한 corpus다.

## 1. 결정 변수 (§1)

각 segment option에 이진 변수

\[
x_{q,\varphi,w,e}\in\{0,1\}
\]

— orbit \(q\), entry phase \(\varphi\), preserving word \(w\),
exit type \(e\).

각 option에 기록한 것: covered hexagons, covered ports, capacity,
defect, \(O\) 소모, \(R\) 소모(\(w\)의 \(E^2\) 개수 포함), exit phase,
kind(initial / fresh / R_entry).

**왜 hexagon이 자원인가**: \(\ell=5\) macro-edge는 자기가 서 있는
hexagon을 정확히 완성하므로, 잔여 hexagon 하나마다 **정확히 하나의**
segment가 대응한다. 따라서 선택된 segment들은 잔여 hexagon을
**분할(partition)** 해야 한다.

## 2. 제약 (§3)

| 제약 | 식 |
|---|---|
| hexagon coverage | \(\sum_{x:h\in C(x)}x=1\) (모든 잔여 hexagon) |
| port uniqueness | \(\sum_{x:p\in P(x)}x\le1\) |
| segment count | \(\sum_x x\le O_{\mathrm{cap}}+R_{\mathrm{cap}}+1\) |
| total capacity | \(\sum_x \operatorname{cap}(x)\,x=B+1\) |
| \(R\) budget | \(\sum_x R(x)\,x\le R_{\mathrm{cap}}\) |
| fresh-opening budget | \(\sum_x O(x)\,x\le O_{\mathrm{cap}}\) |
| initial segment (§9) | \(\sum_{x\in I(S)}x=1\) |
| defect | \(\sum_x d(x)\,x\le M\) |

## 3. Option corpus 실측 (§2, §10–12)

engine 검증: 각 survivor의 post-\(R_2\) 상태에서 `macro.macro_edges()`를
직접 호출해 legal edge를 얻고, 생성원 예측 \(p\mapsto p\circ g_j\)와
비교했다 — **7/7 일치**. 자체 bookkeeping을 재사용하지 않았다(라운드11의
교훈).

| survivor | \(B{+}1\) | 잔여 hexagon | option | initial | fresh | R_entry | option 없는 hexagon |
|---|---:|---:|---:|---:|---:|---:|---:|
| ell0 P2 | 115 | 115 | 9,340 | 2 | 9,338 | 0 | **0** |
| ell4 P2 (×3) | 116 | 116 | 9,529 | 2 | 9,526 | 1 | **0** |
| ell4 P6 (×3) | 112 | 112 | 8,811 | 2 | 8,807 | 2 | **0** |

**잔여 hexagon 수 = \(B+1\)** 정확히 일치한다 — \(\Phi=0\)의 직접적
귀결이며, 분할이 빈틈없어야 함을 뜻한다.

**initial option이 단 2개**라는 것이 §9의 실질적 내용이다.

## 4. Solver 부재 (§14)

이 환경에는 `pulp`·`ortools`·`pysat`·`scipy`가 **전부 없다**. 따라서
모든 층은 손으로 구현한 정확 추론으로 판정하거나 **bounded incomplete**로
표시했다. **검증되지 않은 solver 결과에 위임한 것은 하나도 없다.**

## 5. R5 (component)는 exact model이 아니다 (§6–7)

Target B의 **최종** component 요구 구조가 이 프로젝트에서 아직 정의되지
않았다. 따라서 R5는 항상 **necessary-condition model**로만 표시하고,
component 라벨(attach / extend / merge / revisit / isolate)은
**기록만 하고 제약으로 강제하지 않았다**(§17의 지시).

**등급**: 모델 정식화 **exact allocation model**, option corpus
**exact replay**(engine 검증 7/7), R5 **미완료**.
