# Long \(O_*\) excursion prefix의 Target A 확장 — **가능하다** (라운드 27)

산출: `src/search_rr_long_prefix_extensions.py` ->
`outputs/rr_long_prefix_extension_results.json`,
`src/verify_rr_long_extension_certificate.py` ->
`outputs/rr_long_prefix_certificates.json`.
전역 RR search를 재시작하지 않았고, N=0 search/checkpoint는 건드리지
않았다. 탐색 대상은 28개 root뿐이다.

## 1. 판정

> **라운드26이 남긴 열린 질문의 답은 "그렇다"이다.**
> \(L\ge7\)인 홀수 지수 \(O_*\) excursion을 포함한 preparation prefix는
> **same-component \(R_2\) 경계(Target A)로 확장된다.**

28개 root 중 **6개가 FOUND**, 22개는 INCOMPLETE(node cap 8,000).
**EXHAUSTED_IMPOSSIBLE은 0개** — 불가능성 certificate는 하나도 얻지
못했고, 얻을 필요도 없어졌다.

FOUND 6개는 전부 **독립 리터럴 replay로 재검증**됐다
(6/6 일치, 0 불일치). **exact witness**.

## 2. 최소 witness — 완전한 리터럴 형태

```
abandonment : ell=4,  rot^4;w2:10        -> (orbit 1, phase 0) = O*
preparation  0: rot^5;w3:201  F  -> (132,2) hex 34
             1: rot^5;w3:201  F  -> (101,1) hex 43
             2: rot^5;w2:10   E  -> (101,2) hex 103
             3: rot^5;w3:210  F  -> (115,4) hex 114
             4: rot^5;w2:10   E  -> (115,0) hex 115
             5: rot^5;w3:210  F  -> ( 75,1) hex 36
             6: rot^5;w3:201  R  -> (  1,3) hex 2      <- O* 복귀, exponent 3 (홀수)
             7: rot^5;w2:10   E  -> (  1,4) hex 0      <- HUB COMPLETER C
R2           8: rot^0;w3:120  R  -> (  0,2) hex 18
```

- excursion: 인덱스 0–6, \(L=7\), \(G=6\), return exponent **3(홀수)**
- hub completer 착지점 **(orbit 1, phase 4)** = hex0 위치 5 —
  기존 terminal normal form과 **정확히 일치**
- 마지막 macro-edge **`rot^0;w3:120`** — 역시 정확히 일치
- \(R_1\) target orbit \(=1=\) \(R_2\) source orbit ⟹ **chaining = True**
- \(\Phi = 0\), \(F_{\text{def}}=1\), \(H=0\), \(N=2\), tail 길이 0
  (\(\ell=4\)에서 Lemma P1과 일치)

즉 이것은 이례적인 변종이 아니라 **기존에 확립된 종결 normal form
그대로**이며, 다른 것은 **preparation 구간뿐**이다.

## 3. 여섯 witness의 parity 원장

계수 단위: \(|P|\) = abandonment 이후 \(R_2\) 직전까지의 macro-edge 수로,
**hub completer \(C\)와 tail을 포함**한다 —
`outputs/rr_preparation_words.json`의 `preparation_length`와 **동일한
convention**이다.

| \(\ell\) | \(L\) | exp | symbolic | \(\vert P\vert\) | tail | \(\#R_{\le C}\) | \((\vert P\vert+\#R)\bmod2\) | \(\#Z_{\to O_*}\) | 패리티 | \(\Phi\) |
|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|
| 4 | 7 | 3 | `FFEFEFR` | **8** | 0 | 1 | **1** | **1** | **홀수** | 0 |
| 4 | 7 | 3 | `FFEFEFR` | **8** | 0 | 1 | **1** | **1** | **홀수** | 0 |
| 4 | 8 | 1 | `FFFFEFFR` | 11 | 0 | 1 | 0 | **3** | **홀수** | 0 |
| 4 | 8 | 1 | `FFFEFFFR` | 11 | 0 | 1 | 0 | **3** | **홀수** | 0 |
| 4 | 8 | 1 | `FFFFEFFR` | 11 | 0 | 1 | 0 | **3** | **홀수** | 0 |
| 4 | 8 | 1 | `FFFEFFFR` | 11 | 0 | 1 | 0 | **3** | **홀수** | 0 |

역사적 \(\ell=4\) 코퍼스(9건)와의 대조:

| | \(\vert P\vert\) | \(\#R_{\le C}\) | \((\vert P\vert+\#R)\bmod2\) | \(\#Z_{\to O_*}\) |
|---|---|---:|---:|---|
| 역사적 9건 | 3, 5, 7 (**전부 홀수**) | 1 | **0** (9/9) | **짝수** (95/95 관측) |
| 이번 6건 | **8**, 11 | 1 | 1 또는 0 | **1 또는 3 — 전부 홀수** |

## 4. 반증되는 명제 — 정확히 네 개

1. **\(\#Z_{\to O_*}\) 짝수** — **반증됨**. 여섯 witness 전부 홀수
   (1 또는 3). 라운드24~26의 최종 목표 명제가 직접 무너진다.
2. **winding number \(k=0\)** — **반증됨**. 손증명된 환원
   \(\#Z_{\to O_*}\equiv k \pmod 2\)에서 \(\#Z\)가 홀수이므로
   \(k\)는 홀수, 즉 \(k\ge1\). 라운드25가 "관측 95/95에서 \(k=0\)"이라
   기록한 것은 depth scope의 결과였다.
3. **\(\ell=4\) preparation length는 홀수** — **반증됨**.
   \(\vert P\vert=8\)인 witness 2개.
4. **\(\vert P\vert+\#R_{\le C}\) 불변량** — **반증됨**. 역사적
   \(\ell=4\) 코퍼스는 9/9에서 0인데 \(\vert P\vert=8\) witness는 1이다.

> 즉 **preparation parity conjecture는 어떤 형태로도 살아남지 못한다.**
> 이것은 새로운 미완료가 아니라 **닫힌 결론**이다.

## 5. 정직한 범위 제한

- 판정한 것은 **Target A**(same-component \(R_2\) 경계)뿐이다.
  **Target B**(그 이후 admissible terminal continuation)와
  **Target C**(전체 NR6 completion)는 **시도하지 않았고 주장하지
  않는다**.
- 그러나 parity 명제 자체가 **\(R_2\) 경계에서 계산되는 양**
  (라운드18 계수 단위 표준)이므로, Target A가 **정확히 올바른
  판정 층위**다. B/C의 미해결이 위 네 반증을 약화시키지 않는다.
- 22개 root의 INCOMPLETE는 **node cap 8,000에서 잘린 것**이며,
  **불가능성으로 읽지 않는다**. `EXHAUSTED_IMPOSSIBLE`은 0개다.
- 6개 witness가 전부 \(\ell=4\)라는 것은 기존 \(\ell\) 이분법
  (same-component는 \(\ell\in\{0,4\}\)에서만)과 **일관**된다.

**등급**: Target A 확장 가능성 = **exact witness**(리터럴 replay
6/6 인증), 네 반증 = **반증됨**, 22개 root = **bounded incomplete**.
