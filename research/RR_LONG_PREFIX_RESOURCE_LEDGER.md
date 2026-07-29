# Long prefix resource ledger 및 손증명 제거 (라운드 27)

산출: `src/build_rr_long_excursion_roots.py` ->
`outputs/rr_long_excursion_prefixes.json`,
`outputs/rr_long_prefix_quotient.json`.

## 1. Corpus 계수 단위 — 38 vs 186

라운드26의 **38**은 **단어(word)** 수다(적어도 한 root에서 legal).
그러나 자원 원장을 가지려면 **상태**가 있어야 하고, 상태를 갖는 단위는
`(word, root ell)` **쌍**이다.

| 단위 | 수 |
|---|---:|
| 홀수 지수 group first-return **단어** (길이 7·8) | 39 |
| 그중 legal한 **단어** (라운드26의 "38") | **38** |
| legal한 `(word, root ell)` **prefix** | **186** |

replay 실패 사유는 전부 area_a prune(step 6에서 5건, step 7에서 4건).
두 숫자를 섞지 않기 위해 이후 모든 표는 **prefix** 단위다.

## 2. Quotient (과제 §2) — 축약 불가

| 분류 | 수 |
|---|---:|
| literal prefix | 186 |
| 서로 다른 **exact state** | **186** |
| 서로 다른 **left-S6 canonical pair** | **186** |
| 서로 다른 resource signature만 | 30 |
| stabilizer tie 히스토그램 | `{1: 186}` |

canonicalization은 `(state, decoration)` **쌍**을 대상으로 하며,
구별된 \(O_*\)와 \(R_1\) target orbit을 모든 tied alpha에 대해
`LEFT_ORBIT_ACTION`으로 transport한 뒤 사전순 최소를 취한다.

> **186개가 전부 서로 다른 canonical pair다 — 탐색 root 수를 대칭성으로
> 줄일 수 없다.** resource signature만 같은 30개 그룹은 상태가 다르므로
> 탐색 단위로 쓸 수 없다.

## 3. 손증명 ledger obstruction — R 예산

> **명제 (손증명)**: RR word는 R 사건이 **정확히 2개**이고 \(R_2\)는
> word의 **마지막** 사건이다. 따라서 \(R_2\)보다 **앞에 놓인**
> preparation prefix는 R을 **최대 1개** 가진다.

| \(R\) 수 | prefix 수 | 판정 |
|---:|---:|---|
| 1 | **28** | Target A 탐색 대상 |
| 2 | 52 | **즉시 불가능** — 두 번째 R이 excursion 내부에서 이미 발생 |
| 3 | 106 | **즉시 불가능** — 세 번째 R은 RR 정의 위반 |

**186개 중 158개가 손증명 하나로 제거된다.** 남는 것은 **28개**.

\(r=2\)인 52개에 대한 주석: 그 두 번째 R이 \(R_2\)라면 word는 거기서
끝나야 하는데 excursion은 그 뒤로 이어진다. 즉 **excursion이 word 안에서
완결되지 않으므로** 그 word의 \(O_*\)-phase walk에는 이 걸음이
애초에 포함되지 않는다 — parity 논증에 영향이 없다.

## 4. 살아남은 28개의 원장

| 항목 | 값 |
|---|---|
| \(L\) | 7 (10개), 8 (18개) |
| return exponent | **3** (10개), **1** (18개) — 전부 홀수 |
| symbolic word | `FFEFEFR` 10, `FFFEFFFR` 9, `FFFFEFFR` 9 |
| \(F_{\text{sym}}\) | 4 (10개), 6 (18개) |
| \(F_{\text{def}}\) | **1** (전부) |
| \(N_{\text{def}}\) | **1** (전부) — 남은 R 예산 정확히 1 |
| \(H\) | **0** (전부) |
| hub touch | **0** (전부) — excursion은 hub에 닿지 않는다 |
| \(O\) | 6 (10개), 8 (18개) |
| \(P\) | 9 (10개), 10 (18개) |
| visited | 44~54 |
| \(\Phi\) | 1~5, **전부 양수** |
| component 수 | 6 (10개), 8 (18개) |

## 5. 즉시 불가능 판정을 시도했으나 **적용되지 않는** 원장 항목

과제 §4·§5·§6이 제안한 나머지 obstruction은 **28개 중 하나도 제거하지
못한다**:

| 후보 | 결과 |
|---|---|
| \(F_{\text{def}}\) 초과 | \(F_{\text{def}}=1\) — **여유 0이지만 위반 아님** |
| \(\Phi<0\) | \(\Phi\in\{1..5\}\) — **전부 양수** |
| \(H\) (hub touch) 초과 | hub touch 0 — **여유 최대** |
| \(N\) monotone 하한 | \(N_{\text{def}}=1\), 목표 2 — **정확히 1 남음, 위반 아님** |
| \(O\) 예산 | \(O\le8 \ll\) `TARGET_O=25` — **여유 큼** |
| 남은 permutation | visited \(\le54\) / 720 — **여유 큼** |

> 즉 **R 예산 외에 원장 수준에서 28개를 죽이는 것은 없다.**
> 나머지는 실제 확장 탐색으로만 판정된다.

**등급**: corpus와 원장은 **exact replay**, quotient는 **exact
canonicalization**, R 예산 제거는 **손증명**, 나머지 원장 항목의
비적용은 **exact replay** 관측.
