# ell=4 terminal normal form — 손증명 7개, 관측 3개 (라운드 29)

산출: `src/verify_rr_terminal_normal_form.py` ->
`outputs/rr_terminal_normal_form_ledger.json`. 새 탐색 없음.
N=0 checkpoint 미접촉. 반증된 parity 프로그램은 복원하지 않는다.

## 0. 세 개의 기반 계산 (엔진 표에서 직접, 탐색 무관)

**(H1) hex0 위치 → (orbit, phase)**

| pos | 0 | 1 | 2 | 3 | 4 | **5** |
|---|---|---|---|---|---|---|
| (orbit, phase) | (0,0) | (120,0) | (33,1) | (9,2) | (3,3) | **(1,4)** |

**(H2) \(\Phi\) 증분**. \(\Phi := 5+6(\text{TARGET\_P}-P)-(720-\text{visited})\).
weight-1 rotation은 \(\Delta P=0,\ \Delta\text{visited}=1\) ⟹ \(\Delta\Phi=+1\);
joint은 \(\Delta P=1,\ \Delta\text{visited}=1\) ⟹ \(\Delta\Phi=-5\). 따라서

\[
\boxed{\ \Delta\Phi = \ell-5\ }\quad\text{(rotation run }\ell\text{인 macro-edge)}
\]

그리고 \(\Phi(\text{initial})=6\).

**(H3)** `macro.remaining_window_capacity_prune(state)`가 참인 것은
**정확히 \(\Phi<0\)일 때**다(400개 자식에서 400/400 일치, 정의상 동일).
즉 **\(\Phi\ge0\)은 추가 가정이 아니라 Area A 자신의 capacity prune**이다.

## 1. 여덟 항목, 각각 별도 lemma

| id | 주장 | 등급 |
|---|---|---|
| **T2** | hub completer의 target은 \((\text{orbit }1,\text{phase }4)\) | **손증명** |
| **T4a** | \(C\) 다음 macro-edge의 rotation run은 \(\ell=0\) | **손증명** |
| **T4b** | \(C\) 다음 edge가 R이면 그것은 `rot^0;w3:120` | **손증명** (T4a 하에) |
| **T5** | \(R_2\) source orbit \(=1\) | **손증명** (T3 하에) |
| **T6** | \(R_2\) target orbit \(=\) 초기 orbit 0 | **손증명** (T3, T4b 하에) |
| **T7** | \(R_2\) 경계에서 \(\Phi=0\) | **손증명** |
| **T8** | \(R_2\) 경계는 same-component | **손증명** (T3, T4b 하에) |
| T1 | \(R_1\) target orbit \(=O_*=\) orbit 1 | **bounded observation (15/15)** |
| T3 | \(R_2\)가 \(C\) 직후 발동 (tail \(=0\)) | **bounded observation (15/15)** |
| T9 | chaining | **bounded observation (15/15)** — 부분 손증명은 별도 문서 |

**15/15 관측을 손증명으로 승격하지 않았다.** T3에 의존하는 항목은
"손증명 (T3 하에)"로 조건부 표기했다.

## 2. 증명

**T2 (§3, §4를 함께 해결)**. \(\ell=4\) abandonment의 rotation run은
hex0 위치 0,1,2,3,4를 방문하고 joint이 hex0를 떠난다. rotation run은
**현재 hexagon 안에서만** 움직이므로 hex0는 **joint target으로만**
재진입할 수 있고, completer는 정의상 그런 첫 edge다. 재방문은 불가능하므로
그 target은 **hex0의 유일한 미방문 위치 = 위치 5**이며, (H1)에 의해
\((1,4)\)다. ∎

이것이 §3의 1–3단계와 §4를 동시에 준다: residual position이 하나뿐이고,
그 위치가 orbit 1 phase 4이며, hub completion이 반드시 그것을 쓴다.
**phase 4라는 값은 코드 정의가 아니라 \(\Sigma\)-궤도 위 좌표에서
읽힌다** — 위치 \(p\)는 \(p_{\text{init}}\circ\Sigma^{p}\)이고 그 E-orbit
좌표가 (H1)의 표다. left-S6 relabel은 우측 작용과 가환이므로 이 표는
transport 아래 불변이다.

**T4a**. \(C\) 이후 걸음은 hex0 위치 5에 서 있다. weight-1 rotation은
위치 0으로 이동하는데, 위치 0은 **초기 상태부터 방문**돼 있으므로
`exact.extend`가 `None`을 돌려준다. 따라서 \(\ell=0\). ∎

**T4b (§6)**. post-\(C\) endpoint에서 네 조인트를 전수 검사한 결과:

| 조인트 | legal | kind | target orbit | same-component | \(\Delta\Phi\) |
|---|---|---|---|---|---|
| `w2:10` | 예 | **Z2** | 0 | True | −5 |
| `w3:120` | 예 | **R** | **0** | True | −5 |
| `w3:201` | 예 | **Z3** | 138 | False | −5 |
| `w3:210` | 예 | **Z3** | 32 | False | −5 |

> **legal한 R은 `w3:120` 하나뿐이다** (여섯 witness 전부 동일).
> T4a와 합치면 label은 `rot^0;w3:120`. ∎

**T7 (§7) — parity와 무관한 직접 유도**.
\(\Phi(\text{initial})=6\)이고 (H2)에 의해

| 구간 | \(\ell\) | \(\Delta\Phi\) |
|---|---:|---:|
| \(A_4\) | 4 | \(-1\) |
| \(P_{\mathrm{core}}\)의 각 edge | 5 | **0** |
| \(C\) | 5 | **0** |
| \(R_2\) | 0 | \(-5\) |

\[
\Phi_{\text{final}} = 6-1-0\cdots0-5 = \mathbf{0}.
\]

**preparation 길이가 정확히 상쇄된다** — 이것이 짧은 9개와 긴 6개가
같은 \(\Phi\)를 갖는 이유다(§8의 핵심). ∎

**T8**. orbit 0은 hex0 위치 0에 port를 갖고 그것은 초기 상태에서 방문됐다.
T2에 의해 completer가 hex0 위치 5(orbit 1의 port)를 방문한다. 따라서
**두 orbit 모두 hexagon 0에 접합**하여 한 component에 있다. \(R_2\)의
source orbit은 1(T5), target orbit은 0(T6)이므로 same-component 판정은
**자동으로 통과**한다. ∎

> **따름**: \(\ell=4\)에서 \(C\)가 발동한 뒤에는 **same-component가
> 제약이 아니다.** 이는 §9의 chaining 논증이 same-component에서
> 나올 수 없음을 뜻한다 — 실제로 나오지 않는다.

## 3. 가정 최소화 (§2)

| 가정 | T2 | T4a | T4b | T7 | T8 |
|---|:---:|:---:|:---:|:---:|:---:|
| \(\ell=4\) | **필수** | **필수** | 필수 | **필수** | 필수 |
| RR (R 정확히 2개) | 불필요 | 불필요 | 불필요 | 불필요 | 불필요 |
| same-component | 불필요 | 불필요 | 불필요 | 불필요 | — |
| \(F_{\mathrm{def}}\le1\) | 불필요 | 불필요 | 불필요 | 불필요 | 불필요 |
| \(N=2\) | 불필요 | 불필요 | 불필요 | 불필요 | 불필요 |
| Unique Hub | 불필요 | 불필요 | 불필요 | 불필요 | 불필요 |
| Hub Touch \(\le2\) | 불필요 | 불필요 | 불필요 | 불필요 | 불필요 |
| Hub Exit Source Lemma | 불필요 | 불필요 | 불필요 | 불필요 | 불필요 |
| \(\Phi\) slab | 불필요 | 불필요 | 불필요 | **필수** | 불필요 |
| 모든 preparation edge가 \(\ell=5\) | 불필요 | 불필요 | 불필요 | **필수** | 불필요 |

> **최소 공리 집합**: T2·T4a·T4b·T8은 **\(\ell=4\) 하나**만 쓴다.
> T7은 추가로 **\(\Phi\) slab**과 **preparation edge가 전부 \(\ell=5\)**를
> 쓴다. 나머지 여덟 가정은 **전부 불필요**하다.

\(\ell=4\)를 빼면 T2는 즉시 거짓이다 — \(\ell=3\)이면 hex0에 미방문
위치가 2개 남으므로 completer target이 유일하지 않다. 이것이
\(\ell\)-분기가 본질적인 이유다.

## 4. 남은 것 — T3과 T9

**T3(\(R_2\)가 \(C\) 직후)은 legality로 강제되지 않는다.** §6의 표가
보여주듯 post-\(C\) endpoint에서 **네 조인트가 전부 legal**하고 그중
셋은 R이 아니다. 따라서 걸음이 \(C\) 다음에 `w2:10`(Z2)이나
`w3:201`/`w3:210`(Z3)을 택하는 것을 막는 국소 논증이 없다.

후보 obstruction 판정:

| 후보 | 판정 |
|---|---|
| Hub Exit Source Lemma | 적용 안 됨 (hub를 이미 떠남) |
| 유일 residual source 소진 | 거짓 — orbit 1의 phase 1,2가 남아 있는 경우가 있다 |
| R budget | 막지 못함 — 비-R edge를 넣고 나중에 \(R_2\)를 둘 수 있다 |
| same-component ancestry | T8에 의해 이미 자동 만족이라 제약이 아님 |
| target occupancy | 네 조인트 전부 legal |
| \(\Phi=0\) timing | \(C\) 이후 \(\Phi=5\), 어느 edge든 \(\ell=0\)이라 \(\Phi=0\)이 됨 — 어느 것도 배제하지 않음 |

**여섯 후보 전부 실패.** T3은 **미완료**이며, 이번 라운드는 그것을
정직하게 남긴다.

**증명 등급 요약**: T2·T4a·T4b·T7 **손증명(무조건)**,
T5·T6·T8 **손증명(T3 하에)**, T1·T3·T9 **bounded observation**.
