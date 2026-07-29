# 정정된 무조건 phase 항등식 (라운드 29 §10)

산출: `src/verify_rr_corrected_phase_identity.py` ->
`outputs/rr_corrected_phase_identity.json`.
**이 정리는 terminal normal form 증명에 사용되지 않으며 분리해 둔다.**

## 1. 정리

\[
\boxed{\;
\#Z_{\to O_*}
\;\equiv\;
k+\#R_{\mathrm{odd\text{-}}\delta}
\pmod 2
\;}
\]

**등급: 손증명.**

## 2. 정의 — 이전 실패가 정의 문제였으므로 정밀하게

| 기호 | 정의 |
|---|---|
| \(O_*\) phase walk | word 순서로 방문한 \(O_*\)의 phase 열. **abandonment joint이 착지한 phase에서 시작**하고, 이후 target orbit이 \(O_*\)인 모든 사건의 target phase가 이어진다 |
| \(\delta_i\) | \((\text{phase}_{i+1}-\text{phase}_i)\bmod 5\). **직전 \(O_*\) phase에 상대적**이며 사건의 국소 성질이 **아니다** |
| \(\#R_{\mathrm{odd\text{-}}\delta}\) | **\(O_*\) walk의 걸음** 중 사건이 R이고 \(\delta\)가 홀수인 것의 수. \(O_*\)를 target하지 않는 R은 **세지 않는다** |
| \(k\) | \(\sum_i\delta_i = A+5k\), \(A=(\text{마지막}-\text{처음})\bmod5\) |
| \(\#Z_{\to O_*}\) | \(P_{\mathrm{core}}\cdot C\) 구간에서 \(O_*\)를 target하는 zero-charge(E 또는 F) 사건 수 |

## 3. 증명 (손증명)

1. **F는 \(O_*\)를 target하지 않는다** — F는 새 orbit을 여는데 \(O_*\)는
   abandonment가 이미 열었다. 따라서 \(\#Z_{\to O_*}=\#E_{\to O_*}\).
2. **모든 E 걸음의 \(\delta\)는 정확히 \(+1\)** — \(\ell=5\)인 `w2:10`
   macro-edge는 정확히 \(E\)의 우측 합성이다. 검증:
   \(\Sigma^5\circ\tau=(1,2,3,4,0,5)=E\) ✓.
   따라서 \(O_*\)의 port \(q\)에서 \(q\circ E\)에 착지한다.
3. \(\sum_i\delta_i = A+5k\) — \(k\)의 정의.
4. 3을 mod 2로 내리고 좌변을 사건 종류로 분해:
   \(\#E\cdot 1+\sum_{R\text{ 걸음}}\delta \equiv A+5k\), 즉
   \(\#E+\#R_{\mathrm{odd\text{-}}\delta}\equiv A+k\).
   \(A=4\)(\(\ell\)-무관 총 전진, 손증명)이므로 결론. ∎

## 4. 역사적 특수 경우

95개 완성(depth ≤6)에서:

| 항목 | 값 |
|---|---|
| 항등식 성립 | **95 / 95** |
| \(\#R_{\mathrm{odd\text{-}}\delta}\) 히스토그램 | `{0: 95}` — **전부 0** |
| \(\#Z_{\to O_*}\) 히스토그램 | `{0: 45, 2: 45, 4: 5}` |
| 축약형 \(\#Z\equiv k\) 유효 | **예 (이 scope 안에서만)** |

> \(\#R_{\mathrm{odd\text{-}}\delta}=0\)이었기 때문에 축약형이
> **정리처럼 보였다.** 정리가 아니다.

## 5. 여섯 반례에서의 적용

| # | phases | deltas | 걸음 기호 | \(\#Z\) | \(k\) | \(\#R_{\mathrm{odd}}\) | 항등식 |
|---:|---|---|---|---:|---:|---:|:---:|
| 0,1 | \([0,3,4]\) | \([3,1]\) | R, E | 1 | 0 | 1 | ✓ |
| 2–5 | \([0,1,2,3,4]\) | \([1,1,1,1]\) | R, E, E, E | 3 | 0 | 1 | ✓ |

**6/6 성립.** 축약형 \(\#Z\equiv k\)는 **여섯 전부에서 실패**한다.

주목: witness 2–5의 R 걸음은 \(\delta=1\)이다 — 라운드26이 찾은
\(\delta=3\)과는 다른 종류의 알파벳 위반이며, 홀수라는 점만 같다.

## 6. 이 정리로 무엇을 할 수 있고 없는가

**할 수 있는 것**: parity가 왜 깨졌는지 정확히 지목한다 —
\(\#Z_{\to O_*}\)의 홀짝은 winding number와 **odd-\(\delta\) R 걸음 수의
합**이 결정한다. 짧은 word에서 후자가 0이었을 뿐이다.

**할 수 없는 것**: 어떤 짝수성도 증명하지 못한다. \(k\)와
\(\#R_{\mathrm{odd\text{-}}\delta}\) 둘 다 상한이 없기 때문이다.
**이 항등식으로 반증된 parity 명제를 되살리려 해서는 안 된다.**
