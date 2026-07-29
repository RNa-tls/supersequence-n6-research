# 여섯 exact counterexample — 정규 형태와 최소성 (라운드 28)

산출: `src/verify_rr_counterexample_certificates.py` ->
`outputs/rr_six_counterexamples.json`,
`outputs/rr_counterexample_certificates.json`.
새 탐색 없음 — 라운드27 결과의 exact replay와 유한 quotient 계산뿐이다.
전역 NR6 completion search는 시작하지 않았고 N=0 checkpoint는 건드리지
않았다.

## 1. 길이 기호 분리 (§1) — 다섯 개는 서로 다른 수다

word 구조: \(A_\ell \cdot P_{\mathrm{core}} \cdot C \cdot T_\ell \cdot R_2\)

| 기호 | 정의 |
|---|---|
| \(P_{\mathrm{core}}\) | abandonment 이후 **completer 직전까지**. JSON의 `edges_before_completer` |
| \(C\) | hub completer edge (정확히 1) |
| \(T_\ell\) | \(C\) 이후 \(R_2\) 직전까지 (Lemma P1: \(\ell=4\)에서 0, 그 외 1) |
| \(P_{\mathrm{reported}}\) | JSON의 `preparation_length` \(=P_{\mathrm{core}}+1+\vert T_\ell\vert\) |
| \(L,\ G\) | \(O_*\) excursion first-return 길이 / gap, \(G=L-1\) |

**감사 결과 (12개 역사적 record)**:

| convention | \((\cdot)+\#R_{\le C} \bmod 2\) |
|---|---|
| \(P_{\mathrm{reported}}\) | \(\ell=0\)에서 1, \(\ell=4\)에서 0 — **비균일** |
| \(P_{\mathrm{core}}\) | **12/12 전부 1 — 균일** |

> **따라서 Conjecture A는 \(P_{\mathrm{core}}\)에 대한 명제다.**
> 라운드27 문서는 \(P_{\mathrm{reported}}\)로 서술했다. 위반 witness는
> 동일하게 식별했으나 역사적 baseline을 비균일 convention으로 인용했다.
> 이후 모든 표는 **둘 다** 병기한다.

## 2. 여섯 witness (deterministic order: \((L, P_{\mathrm{core}}, \text{literal word})\))

| # | \(\ell\) | \(L\) | \(P_{\mathrm{core}}\) | \(C\) idx | tail | \(P_{\mathrm{rep}}\) | \(\#R_{\le C}\) | A(\(P_{\mathrm{core}}\)) | A(\(P_{\mathrm{rep}}\)) | \(\#Z_{\to O_*}\) | \(k\) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4 | 7 | **7** | 7 | 0 | 8 | 1 | **0** | 1 | **1** | 0 |
| 1 | 4 | 7 | **7** | 7 | 0 | 8 | 1 | **0** | 1 | **1** | 0 |
| 2 | 4 | 8 | 10 | 10 | 0 | 11 | 1 | 1 | 0 | **3** | 0 |
| 3 | 4 | 8 | 10 | 10 | 0 | 11 | 1 | 1 | 0 | **3** | 0 |
| 4 | 4 | 8 | 10 | 10 | 0 | 11 | 1 | 1 | 0 | **3** | 0 |
| 5 | 4 | 8 | 10 | 10 | 0 | 11 | 1 | 1 | 0 | **3** | 0 |

전체 필드(canonical root hash, literal full word, excursion subword,
\(O_*\) visit/phase sequence, component ancestry, \(\Phi\) ledger,
post-\(R_2\) state hash 등)는 JSON에 있다.

## 3. 최소성 (§3) — witness 0이 모든 기준에서 동시에 최소

| 기준 | 값 | 달성 witness |
|---|---:|---|
| shortest long excursion \(L\) | 7 | 0, 1 |
| shortest total extension | 2 | 0, 1 |
| fewest \(R\) before \(C\) | 1 | 전부 |
| fewest \(F_{\mathrm{sym}}\) | 4 | 0, 1 |
| smallest \(k\) | 0 | 전부 |
| smallest total macro depth | 10 | 0, 1 |
| lexicographically minimal literal word | — | **0** |

> **witness 0이 일곱 기준 전부에서 동시에 최소다.** 이것을
> **정준 최소 반례(canonical minimal counterexample)** 로 고정한다.

```
A_4  : rot^4;w2:10                 -> (orbit 1, phase 0) = O*
X_long (L=7, exponent 3, 홀수):
  rot^5;w3:201  F -> (132,2)
  rot^5;w3:201  F -> (101,1)
  rot^5;w2:10   E -> (101,2)
  rot^5;w3:210  F -> (115,4)
  rot^5;w2:10   E -> (115,0)
  rot^5;w3:210  F -> ( 75,1)
  rot^5;w3:201  R -> (  1,3)       <- O* 복귀, delta 3 (홀수)
C    : rot^5;w2:10   E -> (  1,4)  hex 0   <- hub completer
R2   : rot^0;w3:120  R -> (  0,2)
```

## 4. Quotient (§5) — 최소 counterexample normal form은 **하나**

| 동치 수준 | class 수 | 분할 |
|---|---:|---|
| exact post-\(R_2\) state | 6 | 전부 다름 |
| left-S6 canonical pair | 6 | 전부 다름 (stabilizer tie 전부 1) |
| **decorated \(R_2\) boundary** | **1** | `[0,1,2,3,4,5]` |
| symbolic excursion | 3 | `FFEFEFR`:[0,1], `FFFFEFFR`:[2,4], `FFFEFFFR`:[3,5] |
| \(O_*\) phase word | 2 | `[0,1]`, `[2,3,4,5]` |
| resource ledger | 2 | `[0,1]`, `[2,3,4,5]` |

> **decorated \(R_2\) boundary 층위에서는 여섯이 전부 하나의 class다** —
> \((r_1\text{tgt}, r_2\text{src}, r_2\text{tgt}, \text{chaining}, \Phi)
> = (1, (1,4), (0,2), \text{True}, 0)\).
> 즉 **counterexample은 종결 구조가 아니라 준비 구조에서만 갈린다.**

가장 거친 유의미한 분할은 **2개 class**(phase word = resource ledger):

- **Class I** (witness 0,1): \(L=7\), \(\#Z_{\to O_*}=1\),
  \(O_*\) phase word \([0,3,4]\), \(P_{\mathrm{core}}=7\)
- **Class II** (witness 2–5): \(L=8\), \(\#Z_{\to O_*}=3\),
  \(O_*\) phase word \([0,1,2,3,4]\), \(P_{\mathrm{core}}=10\)

**등급**: witness corpus와 최소성 = **exact replay**,
quotient = **exact quotient**, 반례 지위 = **exact counterexample**.
