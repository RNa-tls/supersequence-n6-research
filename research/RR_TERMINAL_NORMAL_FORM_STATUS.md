# Terminal normal form 최종 proof-status 표 (라운드 30 §20)

## 0. 명제 번호 정의 (문서 첫머리에 고정)

\(\ell=4\) RR root class에서 same-component \(R_2\) 경계에 도달했다고
할 때:

| id | 명제 |
|---|---|
| **T1** | \(R_1\)의 target orbit이 \(O_*=\) orbit 1이다 |
| **T2** | hub completer의 target이 \((\text{orbit }1,\text{phase }4)\)이다 |
| **T3** | \(R_2\)가 \(C\) 직후 macro-edge에서 발동한다 (tail \(=0\)) |
| **T4a** | \(C\) 다음 macro-edge의 rotation run이 \(\ell=0\)이다 |
| **T4b** | 그 edge가 R이면 그것은 `rot^0;w3:120`이다 |
| **T5** | \(R_2\)의 source orbit이 1이다 |
| **T6** | \(R_2\)의 target orbit이 초기 orbit 0이다 |
| **T7** | \(R_2\) 경계에서 \(\Phi=0\)이다 |
| **T8** | \(R_2\) 경계가 same-component다 |
| **T9** | chaining (\(R_1\) target \(=R_2\) source) |

## 1. 최종 표

| id | 등급 | 비고 |
|---|---|---|
| **T2** | **손증명** | \(\ell=4\)만 사용 |
| **T4a** | **손증명** | \(\ell=4\)만 사용 |
| **T4b** | **손증명** (T4a 하에) | post-\(C\) endpoint에서 R은 `w3:120` 하나뿐 |
| **T7** | **손증명** | \(\Phi\) slab + 모든 preparation edge \(\ell=5\) |
| **T8** | **손증명** (T3, T4b 하에) | orbit 0·1이 둘 다 hex0에 접합 ⟹ **자동**. same-component는 \(\ell=4\)에서 제약이 아니다 |
| **T5** | **손증명** (T3 하에) | |
| **T6** | **손증명** (T3, T4b 하에) | |
| **T1** | **CH1에서만 증명** | \(C\)가 R인 5/15에서 손증명. 나머지는 exact observation |
| **T9** | **CH1에서만 증명** | 동일. CH2(10/15)는 **미완료** |
| **T3** | **exact observation (15/15)** | legality로 강제되지 않음 — post-\(C\)에서 네 조인트가 전부 legal이고 셋은 R이 아니다. 후보 obstruction 6개 전부 실패 |

**반증됨** 항목: 이 표에는 없다. 반증된 것은 parity 계열이며
`RR_PARITY_CONJECTURE_REFUTATION.md`에 별도로 있다.

## 2. 라운드30에서 바뀐 것

| 항목 | 이전 | 지금 |
|---|---|---|
| CH2-B (orbit 1 first-opener \(=R_1\)) | 미검사 | **반증됨** — opener는 abandonment |
| CH2 chaining | 미완료 | **미완료** (구조는 규명, 장애물 특정) |
| CH2의 진짜 장애 | 불명 | **\(\#R_{\le C}=0\)인 legal completion이 존재** |

## 3. RR branch closure 현황

| 목표 | 상태 |
|---|---|
| parity 논증으로 RR 닫기 | **폐쇄** (라운드26–28에서 반증) |
| terminal normal form | **7/10 손증명**, T1·T3·T9 남음 |
| same-component ⟹ chaining | **5/15 손증명 (CH1)**, CH2 미완료 |
| 여섯 counterexample state의 Target B | **불가능 — 손증명** (라운드30) |
| 짧은 preparation 경계의 Target B | **미완료** — 계수 장애물이 9/12를 통과시킨다 |
| Target C / NR6 | **손대지 않음** |

## 4. NR6 영향 (§22)

| 구분 | 판정 |
|---|---|
| Target B graph obstruction 발견 | **예 — 여섯 long witness state 전부** (계수 장애물, 그래프 탐색 아님) |
| no static obstruction | **짧은 preparation 9/12** — 여전히 열림 |
| CH2 chaining proof status | **미완료** |
| RR branch closure | **미완료** — parity 경로는 닫혔고 terminal/chaining 경로만 남음 |

> **NR6 completion 가능성에 대해서는 어떤 주장도 하지 않는다.**
> 여섯 state에서 Target B가 불가능하다는 것은 **그 여섯 경계가 slab
> continuation을 갖지 않는다**는 뜻일 뿐이며, \(L_6\ge872\)나
> \(L_6\ge867\)과는 무관하다. 반대로 짧은 preparation 경계에 장애물이
> 없다는 사실도 **Hamiltonian path의 존재를 뜻하지 않는다.**

## 5. Target B search decision (§21)

여섯 long-witness state는 **정적 장애물로 제거**됐으므로 대형 DFS
대상에서 빠진다. 남은 대상(짧은 preparation 9개)을 위해 다음이
준비돼 있다:

| 항목 | 상태 |
|---|---|
| port-state Hamiltonian solver | **미작성** — 그래프 빌더는 있음 |
| forced-edge propagation | **미작성** |
| memoization key | `(stable_key, depth)` 규약 확정 |
| certificate format | 라운드27 형식 재사용 확정 |

이번 라운드에서 깊이 107~110 탐색은 **돌리지 않았다** — 그리고 여섯
state에 대해서는 **영원히 돌릴 필요가 없다.**
