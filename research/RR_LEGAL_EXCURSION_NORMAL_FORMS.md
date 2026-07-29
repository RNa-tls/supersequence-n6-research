# Legal \(O_*\) excursion normal forms (라운드 26)

산출: `src/verify_rr_o_star_gap.py` ->
`outputs/rr_o_star_excursions.json` (`normal_forms` 배열, 40개).

## 1. Excursion 정의

\(O_*\)의 port에서 출발해, 중간 edge는 \(O_*\)에 착지하지 않고,
마지막 edge가 \(O_*\)로 복귀하는 preparation macro-edge 열.
\(L\) = 복귀 edge 포함 총 edge 수, \(G=L-1\).

## 2. Symbolic normal form 목록 (\(L\le8\), 대표형)

| 이름 | symbolic | \(L\) | \(G\) | exponent | \(\#E\) | \(\#F\) | \(\#R\) | 알파벳 준수 |
|---|---|---:|---:|---:|---:|---:|---:|:---:|
| `Imm_E` | `E` | 1 | 0 | 1 | 1 | 0 | 0 | **예** (E 걸음 자체) |
| `Imm_R` | `R` | 1 | 0 | 2 | 0 | 0 | 1 | **예** |
| `D4` | `FERR` | 4 | 3 | 2 | 1 | 1 | 2 | **예** |
| `D5a` | `FEEER` | 5 | 4 | 2 | 3 | 1 | 1 | **예** |
| `D5b` | `FEFER` | 5 | 4 | 4 | 2 | 2 | 1 | **예** |
| `D5c` | `FFEFR` | 5 | 4 | 4 | 1 | 3 | 1 | **예** |
| `D7a` | `FEFERRR` | 7 | 6 | 2 | 2 | 2 | 3 | 예 |
| **`D7odd`** | **`FFEFEFR`** | **7** | **6** | **3** | 2 | 4 | 1 | **아니오** |
| `D7b` | `FFRFFER` | 7 | 6 | 4 | 1 | 4 | 2 | 예 |
| **`D8odd1`** | **`FFRFERFR`** | 8 | 7 | **1** | 1 | 4 | 3 | **아니오** |
| **`D8odd3`** | **`FEFRFFFR`** | 8 | 7 | **3** | 1 | 5 | 2 | **아니오** |
| `D8b` | `FEFREERR` | 8 | 7 | 4 | 3 | 2 | 3 | 예 |

전체 40개 normal form은 JSON에 있다. 여기 실린 것은 각
\((L,\text{exponent})\)의 대표 하나씩이다.

## 3. 구조적 관찰 — 손증명 가능한 부분

**Lemma A (손증명)**: \(L\ge2\)인 excursion은 반드시 `w3:201` 또는
`w3:210`으로 시작한다. 첫 edge가 orbit-보존 조인트면 \(q\to qE\) 또는
\(q\to qE^2\)로 **즉시** \(O_*\)에 착지해 \(L=1\)이 되기 때문이다.

**따름 (손증명)**: 모든 \(L\ge2\) excursion의 첫 기호는 `F` 또는 `R`이며,
관측된 모든 \(L\ge2\) normal form이 실제로 `F`로 시작한다
(root-local exhaustive; `R`로 시작하는 \(L\ge2\) excursion은 관측되지
않았으나 배제하는 논증은 **미완료**).

**\(L=2,3\) 부재 (exact group theorem)**: 군론적으로 first-return이
존재하지 않는다 — `RR_FIRST_RETURN_WORDS.md` §4.

**\(L=6\) 부재 (exact legality obstruction)**: 군론 first-return은 3개
존재하나 legal한 것이 하나도 없다. 이것이 군 그래프와 legality-filtered
그래프가 다른 **두 번째** 방향의 예다.

## 4. 목표 명제 — "모든 legal excursion이 이 유한 목록 중 하나"

\(L\le8\) 범위에서는 **참**이며 목록은 40개다(**root-local exhaustive**).
\(L>8\)은 frontier가 ceiling에서 잘렸으므로 **미완료**.

다만 이 목록은 원래 의도한 용도로는 **쓸 수 없다**: 목록 안에 알파벳을
위반하는 형태(`D7odd`, `D8odd1`, `D8odd3`)가 들어 있기 때문이다.
"모든 legal excursion의 return exponent가 1·2·짝수"라는 명제는
**반증됨**.

## 5. Orbit-changing event 상한 (과제 §10)

| 후보 | 판정 |
|---|---|
| F 예산 때문에 fresh change는 최대 1 | **반증됨** — `FFEFEFR`은 \(\#F=4\) |
| 추가 change는 쌍으로 발생 | **반증됨** — \(\#F=3\)인 legal excursion(`FFEFR`) 존재 |
| component ancestry가 3번째 change 금지 | **반증됨** — 위 두 예가 통과 |
| 각 change가 distinct hub/hex slot 소비 | excursion은 hub에 닿지 않으므로 **무관** |

orbit-changing event 수에 대한 유효한 상한은 이번 라운드에 **하나도
확립되지 않았다**.

## 6. 증명 등급

- normal form 목록(\(L\le8\)): **root-local exhaustive**
- Lemma A: **손증명**
- \(L\in\{2,3\}\) 부재: **exact group theorem**
- \(L=6\) 부재: **exact legality obstruction**
- "모든 excursion이 알파벳 준수": **반증됨**
- \(L>8\) 스펙트럼: **미완료**
