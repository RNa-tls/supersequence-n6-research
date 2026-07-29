# Long prefix 분류 (라운드 27 §14)

산출: `outputs/rr_long_excursion_prefixes.json`,
`outputs/rr_long_prefix_extension_results.json`,
`outputs/rr_long_prefix_certificates.json`.

## 1. 186 -> 28 -> 6

| 단계 | 수 | 근거 | 등급 |
|---|---:|---|---|
| 홀수 지수 group first-return 단어 (길이 7·8) | 39 | 리터럴 전수 열거 | exact group theorem |
| legal 단어 | 38 | 엔진 replay | exact replay |
| legal `(word, ell)` prefix | **186** | 〃 | exact replay |
| R 예산 통과 (`r_count = 1`) | **28** | Class A로 158개 제거 | **손증명** |
| Target A 확장 성공 | **6** | 리터럴 replay 인증 | **exact witness** |

## 2. Class 정의와 배정

| Class | 정의 | 수 | 등급 |
|---|---|---:|---|
| **A** | **R 예산 obstruction** — prefix가 이미 R을 2개 이상 포함 | **158** | **손증명** |
| **B** | \(O_*\) phase obstruction | **0** | 해당 없음 |
| **C** | component ancestry obstruction | **0** | 해당 없음 |
| **D** | **확장 존재** (Target A FOUND) | **6** | **exact witness** |
| **U** | **incomplete** (node cap에서 잘림) | **22** | **bounded incomplete** |

**Class B와 C는 비어 있다.** 원장 수준에서 \(O_*\) phase나 component
ancestry로 제거되는 prefix는 **하나도 없다**
(`RR_LONG_PREFIX_RESOURCE_LEDGER.md` §5).

## 3. Class D(성공)의 symbolic 특징 — 완전 분리

| symbolic first-return word | \(L\) | exp | prefix 수 | 그중 FOUND | root \(\ell\) |
|---|---:|---:|---:|---:|---|
| `FFEFEFR` | 7 | 3 | 10 | **2** | **4** |
| `FFFEFFFR` | 8 | 1 | 9 | **2** | **4** |
| `FFFFEFFR` | 8 | 1 | 9 | **2** | **4** |

> **분류 정리(관측)**: Class D는 **\(\ell=4\)와 정확히 일치**한다 —
> 28개 중 \(\ell=4\)인 것은 6개이고, 그 6개가 전부 FOUND이며,
> \(\ell\ne4\)인 22개는 전부 U다.

이는 기존 **\(\ell\) 이분법**(same-component RR은 \(\ell\in\{0,4\}\)
에서만 나타난다)과 일관된다. 다만 \(\ell=0\) root가 이 corpus에는
살아남지 못했으므로 \(\ell=0\)에 대해서는 **아무 말도 하지 않는다**.

**주의**: "\(\ell\ne4\)는 불가능"이라고 읽으면 **틀린다**. 22개는
node cap에서 잘린 U이지 EXHAUSTED_IMPOSSIBLE이 아니다. 실제로 그
22개는 각각 7,600~7,800개의 \(R_2\) 경계에 도달했으나 그중
same-component가 없었을 뿐이며, frontier는 전혀 소진되지 않았다.

## 4. Class A의 내부 구조 (손증명으로 제거된 158개)

| prefix의 R 수 | 수 | 이유 |
|---:|---:|---|
| 2 | 52 | 두 번째 R이 excursion **내부**에서 발생 ⟹ word가 거기서 끝나야 하는데 excursion이 그 뒤로 이어진다 ⟹ 그 word의 \(O_*\) walk에는 이 걸음이 애초에 포함되지 않는다 |
| 3 | 106 | 세 번째 R은 RR 정의(정확히 2개) 위반 |

Class A 제거는 **parity 논증에 손실을 주지 않는다** — 제거된
prefix들은 완성된 word 안에서 \(O_*\) excursion을 이루지 못하기
때문이다.

## 5. 최소 impossible certificate — 얻지 못했다

과제 §13이 요구한 "38개가 같은 obstruction으로 묶이는가"의 답은
**아니오**다:

- Class A(158개)는 하나의 손증명으로 묶이지만, 그것은
  **excursion을 죽이는 것이 아니라 corpus에서 배제하는 것**이다.
- 남은 28개 중 6개는 **확장이 실제로 존재**하므로 어떤 obstruction도
  있을 수 없다.
- 22개는 **미판정**이다.

따라서 "long excursion을 제거하는 공통 obstruction"은 **존재하지
않는다** — 라운드26의 결론이 Target A 층위에서도 유지된다.

## 6. 성공 기준 결산

| 과제 성공 기준 | 결과 |
|---|---|
| 1. 38개 long prefix의 exact quotient | **완료** — prefix 186개, 전부 서로 다른 canonical pair (축약 불가) |
| 2. prefix별 Target A 판정 | **부분 완료** — 6 FOUND, 158 손증명 제거, 22 미판정 |
| 3. 최소 성공 witness 또는 완전한 impossible certificate | **최소 witness 확보** (extension 길이 2) |
| 4. depth-cap artifact의 영향 정리 | **완료** — `RR_DEPTH_CAP_ARTIFACTS.md` |
| 5. \(O_*\) parity conjecture의 최종 상태 | **결정됨 — 반증됨** |

**등급**: Class A = **손증명**, Class D = **exact witness**,
Class U = **bounded incomplete**, Class B/C 공집합 = **exact replay** 관측.
