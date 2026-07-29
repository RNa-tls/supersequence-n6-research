# \(O_*\) revisit gap — 목표 명제는 **반증됨** (라운드 26)

산출:
`src/verify_rr_o_star_gap.py` -> `outputs/rr_o_star_excursions.json`,
`outputs/rr_gap_certificates.json`.
**completion search 없음** — legal preparation prefix만 열거하며, 어떤
prefix가 완성된 RR word로 확장되는지는 묻지 않는다. N=0 search/checkpoint는
건드리지 않았다.

## 1. 계수 단위 확정 — 그리고 라운드25 서술 정정

연속한 \(O_*\) 방문 \(v_i, v_{i+1}\)에 대해:

- **\(L\)** = \(O_*\)의 port \(v_i\)에서 출발해 **다시 \(O_*\)에
  착지하는 edge를 포함한** macro-edge 수 (first-return **word length**)
- **\(G = L-1\)** = 그 사이에 \(O_*\)에 착지하지 **않은** macro-edge 수
  (**gap**)

즉 즉시 복귀는 \(L=1,\ G=0\).

> **정정**: 라운드25 문서는 관측 gap 값 `0,3,4`(= \(G\))를 군론적
> 임계값 `6`(= \(L\))과 **단위를 밝히지 않고** 비교했다. 결론은
> 영향받지 않았으나(\(L=1,4,5\)는 모두 \(\le6\)) 서술은 단위를 섞었다.
> 이 문서가 그 정정이며, 이후 모든 표는 \(L\)과 \(G\)를 병기한다.

excursion마다 기록한 항목: departure joint, return joint, 중간 joint
word, symbolic word(E/F/R), return exponent, \(\#R/\#F/\#E\),
abandonment \(\ell\), \(O_*\) id. 전체는
`outputs/rr_o_star_excursions.json`의 `excursions` 배열에 있다.

## 2. Legal excursion 길이 스펙트럼

다섯 abandonment root 각각에서, \(O_*\)에 착지하지 않는 legal
macro-edge만으로 \(L\le8\)까지 전수 열거했다. **ceiling을 8로 둔 것이
핵심**이다 — 군론적 임계값 6보다 크게 잡아야 "6을 넘지 않는다"가
ceiling의 인공물이 아닌 발견이 된다. 라운드25의 측정이 depth-6 word
scope 안에 있었기 때문에 이 질문을 **어느 쪽으로도 결정할 수 없었다**는
점도 여기서 드러난다.

| \(L\) | \(G\) | legal excursion 수 |
|---:|---:|---:|
| 1 | 0 | 10 |
| **2** | 1 | **0** |
| **3** | 2 | **0** |
| 4 | 3 | 10 |
| 5 | 4 | 15 |
| **6** | 5 | **0** |
| 7 | 6 | 55 |
| 8 | 7 | 261 |

**legal 길이 집합 = \(\{1,4,5,7,8\}\)**. \(L\in\{2,3\}\)은 군론적으로
불가능하고(§ `RR_FIRST_RETURN_WORDS.md`), \(L=6\)은 **군론적으로는
가능하지만 legality로 제거된다**.

> 스펙트럼이 **구간이 아니다**. 따라서 "길이가 길어지면 반드시 충돌이
> 생긴다" 형태의 단조 논증(과제 §5의 prefix collision theorem)은
> **존재할 수 없다** — \(L=6\)이 불가능한데 \(L=7,8\)이 가능하기 때문.

## 3. 목표 명제 판정 — 반증됨

| \(L\) | \(G\) | exponent | 패리티 | 수 | symbolic 대표 |
|---:|---:|---:|---|---:|---|
| 1 | 0 | 1 | ODD | 5 | `E` |
| 1 | 0 | 2 | even | 5 | `R` |
| 4 | 3 | 2 | even | 10 | `FERR` |
| 5 | 4 | 2 | even | 5 | `FEEER` |
| 5 | 4 | 4 | even | 10 | `FEFER` |
| 7 | 6 | 2 | even | 20 | `FEFERRR` |
| **7** | **6** | **3** | **ODD** | **10** | **`FFEFEFR`** |
| 7 | 6 | 4 | even | 25 | `FFRFFER` |
| **8** | 7 | **1** | **ODD** | 56 | `FFRFERFR` |
| 8 | 7 | 2 | even | 15 | `FFFRFEFR` |
| **8** | 7 | **3** | **ODD** | 120 | `FEFRFFFR` |
| 8 | 7 | 4 | even | 70 | `FEFREERR` |

(\(L=1,\ \text{exponent }1\)은 유일한 정당한 홀수 — 단일 생성원 \(E\),
즉 알파벳의 E 걸음 그 자체다.)

> **판정: 반증됨.** \(L=7\), return exponent **3**(홀수)인 legal
> excursion이 **다섯 root 전부에서** 존재한다. 따라서
>
> - "legal first-return gap \(\le6\)"도,
> - 그보다 약한 "모든 legal excursion이 알파벳을 지킨다"도
>
> **거짓이다.** \(O_*\)-걸음 알파벳은 군론으로도(라운드25), legality를
> 더해도(이번 라운드) 성립하지 않는다.

최소 반례 해부는 `RR_LENGTH7_GROUP_COUNTEREXAMPLES.md` 참고.

## 4. 왜 라운드25의 관측은 예외가 없었는가

라운드25가 본 excursion은 \(L\in\{1,4,5\}\)뿐이었다. 이유는 구조가
아니라 **scope**다: 그 universe는 abandonment 이후 depth \(\le6\)이므로
\(L=7\) excursion은 word 자체에 **들어갈 자리가 없다**. 즉

> 라운드25의 "0/18,778 위반"은 알파벳의 증거가 아니라
> **depth cap의 그림자**였다.

이것을 명시적으로 기록해 둔다 — 라운드25 문서의 "이것이 알파벳이
성립하는 이유"라는 서술은 **이 scope 안에서만** 옳다.

## 5. 과제 §12 증명 구조의 판정

| Lemma | 내용 | 판정 |
|---|---|---|
| **A** | \(L\ge2\)인 \(O_*\)-excursion은 반드시 `w3:201` 또는 `w3:210`으로 시작한다 | **손증명** |
| **B** | 출발 후 legal endpoint/phase 상태가 유한 chamber \(K\)에 갇힌다 | 자명하게 참(유한 상태공간)이나 **비자명한 내용 없음** |
| **C** | \(K\) 안의 길이 \(\ge7\) 경로는 금지 위치를 재방문하거나 더 일찍 \(O_*\)로 돌아온다 | **반증됨** |
| **정리** | 모든 legal first-return excursion은 \(L\le6\) | **반증됨** |

**Lemma A의 손증명**: 첫 edge가 orbit-보존 조인트(`w2:10`=\(E\),
`w3:120`=\(E^2\))이면 출발 port \(q\in O_*\)에서 \(qE\) 또는 \(qE^2\),
즉 **즉시 \(O_*\)에 착지**하므로 \(L=1\)이다. 따라서 \(L\ge2\)이면
첫 edge는 orbit을 바꾸는 두 조인트 중 하나다. ∎

Lemma C가 무너지므로 §12 architecture 전체가 닫힌다.

## 6. Sharpness (§13)

- \(L=6\) legal excursion은 **존재하지 않는다** — 군론 first-return은
  3개 있으나 전부 legality로 제거된다.
- 알파벳을 지키는 excursion은 \(L=8\)까지 존재한다(길이만으로는
  판별 불가).
- 실제 RR preparation history(depth \(\le6\)) 안의 excursion은
  \(L\in\{1,4,5\}\)뿐 — 이는 **bounded observation**이며 정리가 아니다.

즉 "실제 sharp bound가 4다"라는 기대도 성립하지 않는다: \(L=5\)가
관측되고 \(L=7\)이 legal이다.

## 7. 남은 정확한 미해결

이번 라운드가 **결정하지 못한** 것은 정확히 하나다:

> \(L=7\)의 홀수 excursion이 **완성된 same-component RR word 안에서도**
> 나타나는가?

excursion 열거는 legal preparation **prefix**만 본다. 그 prefix가 hub
completer와 \(R_2\)까지 확장되는지는 completion search가 필요하고,
이번 라운드는 그것을 금지받았다. 따라서:

- "legal preparation prefix에 대한 gap bound": **반증됨**
- "완성된 RR word 안의 gap bound": **미완료**

**증명 등급**: 길이 스펙트럼과 excursion 표는 **root-local exhaustive**
(\(L\le8\), frontier는 ceiling에서 잘림 — 그 너머는 **미완료**),
\(L=7\) 홀수 excursion은 **exact counterexample**, Lemma A는 **손증명**,
목표 명제는 **반증됨**.

## 8. Excursion certificate (§17)

`outputs/rr_gap_certificates.json`.

| 항목 | 값 |
|---|---|
| root 집합 | `initial_state()`에서 `rot^ell` (\(\ell=0..4\)) 후 유일 abandonment 조인트 `w2:10` |
| transition generator | `macro.macro_edges` + `area_a_prune_reason(AREA_A)` |
| dedup key | `(stable_key, depth)` — 상태만으로 dedup하면 최대 excursion 길이를 **과소보고**한다 |
| node/edge/time cap | **없음** |
| excursion 길이 ceiling | \(L\le8\) |
| frontier 자연소진 | **아니오** — ceiling에서 잘림 |
| 확장 노드 | 131,917 (root별 ≈26,4xx) |
| 발견 excursion | 351 |
| engine SHA-256 | `9196dcc1…5801a8` |
| core SHA-256 | `18f75735…e39d60` |

**"whole universe"라는 표현은 쓰지 않는다.** 이것은 정확히
**root-local excursion scope**이며, frontier가 ceiling에서 잘렸으므로
\(L>8\)에 대해서는 아무것도 주장하지 않는다.

라운드25의 `verify_rr_o_star_alphabet.py` 인증서(18,778 legal edge,
위반 0건)는 **여전히 정확한 측정**이지만, §4에서 밝혔듯 그 scope가
depth \(\le6\)이므로 **알파벳의 증거로는 쓸 수 없다**. 두 인증서는
서로 모순되지 않는다 — 서로 다른 scope를 인증한다.
