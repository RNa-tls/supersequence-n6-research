# Parity 명제 반증 certificate와 theorem graph 정정 (라운드 28)

산출: `outputs/rr_counterexample_certificates.json`,
`outputs/rr_long_normal_form_classes.json`.

## 1. 라운드27의 오류 정정 — \(k\ge1\)은 **거짓**이다

라운드27은 다음을 기록했다:

> "손증명된 환원 \(\#Z_{\to O_*}\equiv k\)는 유효하며, 새 witness에서
> 이 환원이 \(k\ge1\)을 검출한다."

**두 부분 모두 틀렸다.** 여섯 witness 전부에서 \(k=0\)이다.

원인: 환원 \(\#Z_{\to O_*}\equiv k\)는 **무조건적이었던 적이 없다.**
그것은 "\(O_*\)로 들어오는 모든 \(R\) 걸음의 phase 변위가 짝수"라는
전제를 썼고, 그 전제가 바로 라운드26에서 **반증된 알파벳**이다.
witness 0의 \(O_*\) 걸음은 `[R(δ=3), E(δ=1)]` — \(R\) 변위가 **홀수 3**
이다.

## 2. 정정된 항등식 — 무조건 손증명

\[
\boxed{\;\#Z_{\to O_*}\;\equiv\;k \;+\; \#R_{\text{odd-}\delta} \pmod 2\;}
\]

여기서 \(\#R_{\text{odd-}\delta}\)는 \(O_*\)로 들어오는 \(R\) 걸음 중
phase 변위가 **홀수**인 것의 개수다.

**손증명**: (i) F는 \(O_*\)를 target하지 않으므로
\(\#Z_{\to O_*}=\#E_{\to O_*}\); (ii) 모든 E 걸음의 변위는 정확히
\(+1\) (\(\Sigma^5\circ\tau=E\)); (iii) \(\sum\delta = \text{advance}+5k
= 4+5k\); (iv) mod 2로 내리면
\(\#E + \#R_{\text{odd-}\delta} \equiv 4+5k \equiv k\). ∎

**검증**: 여섯 witness 전부 성립 (6/6).

| witness | \(\#Z_{\to O_*}\) | \(k\) | \(\#R_{\text{odd-}\delta}\) | deltas | 걸음 기호 |
|---:|---:|---:|---:|---|---|
| 0,1 | 1 | 0 | 1 | [3, 1] | R, E |
| 2–5 | 3 | 0 | 1 | [1,1,1,1] | R, E, E, E |

역사적 95개 완성에서는 \(\#R_{\text{odd-}\delta}=0\)이었으므로
\(\#Z\equiv k\)로 **축약되어 보였을 뿐**이다.

## 3. Certificate — 명제별 정확한 판정

### Conjecture A: \(P_{\mathrm{core}} + \#R_{\le C}\equiv1 \pmod 2\)

| 항목 | 값 |
|---|---|
| convention | \(P_{\mathrm{core}}\) (12/12 균일한 유일 convention) |
| 역사적 baseline | **1** (12/12, 두 \(\ell\) 분기 모두) |
| 위반 witness | **0, 1** — \(7+1=8\equiv0\) |
| 만족 witness | 2–5 — \(10+1=11\equiv1\) |
| **판정** | **반증됨** (exact counterexample 2개) |

### Conjecture B: \(\#Z_{\to O_*}\equiv0 \pmod 2\)

| 항목 | 값 |
|---|---|
| 역사적 baseline | 95/95 짝수 (depth ≤6 scope) |
| 위반 witness | **0,1,2,3,4,5 — 전부** (값 1 또는 3) |
| **판정** | **반증됨** (exact counterexample 6개) |

### Conjecture C: \(k=0\)

| 항목 | 값 |
|---|---|
| 역사적 baseline | 95/95에서 \(k=0\) |
| 위반 witness | **없음** — 여섯 전부 \(k=0\) |
| **판정** | **반증되지 않음** (이 witness들로는) |

### 환원: \(\#Z_{\to O_*}\equiv k\)

| 항목 | 값 |
|---|---|
| 라운드27 기록 | "유효" |
| 위반 witness | **전부 6개** |
| **판정** | **반증됨** — §2의 항등식으로 대체 |

각 certificate는 사용 convention, 좌변 실제 값, mod-2 결과,
exact replay trace, 전제 충족 여부를 JSON에 담고 있다.

## 4. Parity 보상 구조 (§8) — 가정 없이 실측만

| # | \(\#Z_{\to O_*}\) (excursion 내/외) | \(\#Z_{\to\text{other}}\) | \(\#Z\) 총 | \(k\) | \(\#R_{\text{odd}}\) |
|---:|---|---:|---:|---:|---:|
| 0,1 | 1 (0 / 1) | **6** | 7 | 0 | 1 |
| 2–5 | 3 (0 / 3) | **7** | 10 | 0 | 1 |

역사적 짧은 witness (95개, depth ≤6): \(\#Z_{\to O_*}\) 히스토그램
`{0: 45, 2: 45, 4: 5}` — 전부 짝수.

**두 가지 실측 사실을 그대로 기록한다**:

1. \(O_*\)를 target하는 zero-charge 사건은 **excursion 내부에 하나도
   없다**(0/1, 0/3) — 전부 excursion **밖**, 즉 completer 및 \(V\)
   구간에서 발생한다.
2. **\(\#Z_{\to\text{other}}\)도 witness 2–5에서 홀수(7)** 다.
   즉 라운드25~26이 95/95로 관측했던 "non-\(O_*\) 총계 짝수"도
   이 범위 밖에서는 성립하지 않는다.

> "다른 구간에서 보상된다"는 가정은 **하지 않는다.** 실제로 총
> \(\#Z\)는 witness 0,1에서 7(홀수), 2–5에서 10(짝수)로 **일정하지
> 않다** — 어떤 총량 보존도 관측되지 않는다.

## 5. 살아남는 조건부 정리 (§9) — 쓸모 기준으로 걸러냄

| 후보 조건부 정리 | 참? | 자명한 재서술? | 활용 가치 | NR6에 필요? |
|---|---|---|---|---|
| \(\#Z_{\to O_*}\equiv k+\#R_{\text{odd-}\delta}\) (무조건) | **참, 손증명** | 아니오 | **높음** — parity 실패의 정확한 원인을 지목 | 미정 |
| 모든 \(O_*\) excursion이 \(L\le5\)이면 \(\#R_{\text{odd-}\delta}=0\)이고 \(\#Z\equiv k\) | **참** | 아니오 | 중간 — 가설이 강하고 아직 증명 안 됨 | 아니오 |
| depth \(\le7\)이면 반례 없음 | 참 | **예 — 자명한 재서술** | **없음** | 아니오 |
| "\(k=0\)이면 \(\#Z\equiv\#R_{\text{odd}}\)" | 참 | **예** | **없음** | 아니오 |
| 제한된 symbolic alphabet에서 짝수성 | 미정 | — | 낮음 | 아니오 |

**버린 것**: "반례가 없으면 정리가 참" 형태 두 개. 과제 §9의 지시대로
기록만 하고 정리로 승격하지 않는다.

**남기는 것은 하나**: §2의 정정된 항등식. 이것만이 비자명하고,
무조건적이며, parity가 왜 깨졌는지를 정확히 지목한다.

## 6. Theorem graph 정정 (§17)

**삭제 또는 붉은 반증 edge로 전환**:

| 노드 | 상태 |
|---|---|
| preparation parity invariant (Conjecture A) | **반증됨** |
| \(O_*\) zero parity (Conjecture B) | **반증됨** |
| 환원 \(\#Z_{\to O_*}\equiv k\) | **반증됨** |
| gap-bound alphabet closure | **반증됨** (라운드26) |
| \(k=0\) | **미완료** — 반증되지 않았으나 증명도 없음 |

**살아남는 노드** (전부 등급 유지):

| 노드 | 등급 |
|---|---|
| \(\ell=5\) 합성 생성원 \(g_j=\Sigma^5\circ a_j\) 네 값 | exact group computation |
| F는 `w3:201`/`w3:210`만 (\(F_{\mathrm{sym}}\) 생성원 제한) | 손증명 |
| \(O_*\) port에서 `w2:10` ⟹ phase +1 | 손증명 |
| F는 \(O_*\)를 target하지 않는다 | 손증명 |
| 총 전진 4 (mod 5), phase injectivity, \(O_*\)-target R \(\le2\) | 손증명 |
| **정정된 항등식 \(\#Z\equiv k+\#R_{\text{odd-}\delta}\)** | **손증명 (신규)** |
| 길이 \(\le6\) first-return 지수는 1·2·짝수 | exact group theorem |
| long excursion exact witnesses | exact counterexample |
| terminal normal form 관측 | exact replay / root-local exhaustive |
| same-component ⟹ chaining | **반증되지 않음** (6개 새 확인 사례) |

**반증된 명제를 다른 이름으로 되살리지 않는다.** §5의 표에서
"자명한 재서술"로 분류된 두 항목이 정확히 그 시도이며, 버렸다.
