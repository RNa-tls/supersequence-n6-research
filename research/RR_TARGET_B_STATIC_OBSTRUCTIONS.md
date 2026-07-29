# Target B 정적 장애물 — 여섯 상태 전부 **불가능** (라운드 30)

산출: `src/analyze_rr_target_b_obstructions.py` ->
`outputs/rr_target_b_obstruction_certificates.json`.
**DFS를 돌리지 않았다. 돌릴 필요도 없다** — 장애물이 계수 논증이다.

## 1. 정리

> **정리 (손증명)**: \(\Phi=0\)인 Target A 상태에서 Target B
> continuation이 존재하면
> \[
> B \;\le\; 5\bigl(\text{O\_capacity}+\text{R\_capacity}\bigr)+4 .
> \]
> 여섯 Target A 상태는 **전부 이 부등식을 위반한다.**

여기서 \(B=\)`TARGET_P`\(-P\) (남은 pass start),
O\_capacity \(=\)`TARGET_O`\(-O\), R\_capacity \(=\) `AREA_A.n_limit`\(-N\).

## 2. 증명

1. \(\Phi=0\)에서 모든 macro-edge는 \(\ell=5\) (라운드29).
2. \(\ell=5\) macro-edge는 \(g_j\)의 우측 곱 (라운드26).
3. \(E\)와 \(E^2\)는 E-orbit을 **보존**하므로 `w2:10`과 `w3:120`은
   **절대 새 orbit을 열 수 없다**. `w2:10`(weight 2)은 Z2,
   `w3:120`(weight 3)은 **항상 R**이다.
4. `w3:201`/`w3:210`은 orbit을 바꾸므로 각각 **fresh opening(\(O{+}{=}1\))
   또는 R**이다.
5. **orbit 보존 edge는 연속 최대 4개.** 연속 구간의 entry port는
   \(p, p E^{s_1}, p E^{s_2},\dots\)이고 \(s\)는 1과 2의 부분합이다.
   \(pE^{s}=pE^{s'} \iff s\equiv s' \pmod 5\)이므로 부분합이 mod 5로
   서로 달라야 하고, 잔여류가 5개뿐이므로 **최대 4개**.
   (유한 확인: 1·2의 부분합이 mod 5로 모두 다른 최대 길이 = **4**.)
6. \(m\)을 orbit-**변경** edge 수라 하면 보존 edge 구간은 최대 \(m+1\)개,
   각 최대 4개이므로
   \[
   B=(\text{보존})+m\;\le\;4(m+1)+m=5m+4 .
   \]
7. \(m\le\) O\_capacity \(+\) R\_capacity (각 변경 edge는 orbit 슬롯
   하나 또는 R 슬롯 하나를 소비). ∎

## 3. 여섯 상태의 certificate

| # | \(B\) | O\_cap | R\_cap | \(m_{\max}\) | \(B_{\max}\) | 모순 | 여유 |
|---:|---:|---:|---:|---:|---:|:---:|---:|
| 0 | 110 | 19 | 1 | 20 | 104 | **예** | **+6** |
| 1 | 110 | 19 | 1 | 20 | 104 | **예** | **+6** |
| 2 | 107 | 17 | 1 | 18 | 94 | **예** | **+13** |
| 3 | 107 | 17 | 1 | 18 | 94 | **예** | **+13** |
| 4 | 107 | 17 | 1 | 18 | 94 | **예** | **+13** |
| 5 | 107 | 17 | 1 | 18 | 94 | **예** | **+13** |

> **여섯 전부 `BUDGET_OBSTRUCTION`.**
> §10의 분류에서 `NO_STATIC_OBSTRUCTION`이나 `INCOMPLETE`는 **하나도
> 없다.**

R\_capacity로 **1을 허용**했다는 점에 유의하라 — Target B 정의는 추가
R을 금지하지만, 더 관대한 `AREA_A.n_limit = 3`을 써도 모순이 유지된다.
즉 이 결과는 Target B 정의에 의존하지 않는다.

## 4. slack=0을 모순으로 쓰지 않았다

라운드29의 \(U_{\mathrm{perm}}=6B+5\)(slack 0)는 **이 논증에 전혀
등장하지 않는다.** 여기서 쓰인 것은 \(B\), \(O\), \(N\)뿐이다.
과제의 경고를 지켰다.

## 5. 적용 범위 — 짧은 preparation에는 적용되지 **않는다**

같은 부등식을 역사적 12개 same-component 경계에 적용하면:

| | 모순 발생 |
|---|---|
| 긴 witness 6개 (\(P_{\mathrm{core}}=7,10\)) | **6 / 6** |
| 역사적 12개 (\(P_{\mathrm{core}}=2,4,6\)) | **3 / 12** |

\(O\)가 작은 짧은 word(\(O=2,3,4\))는 부등식을 만족하므로
**장애물이 없다**. 닫힌 형태로:

\[
\text{모순} \iff B > 5(\text{O\_cap}+\text{R\_cap})+4
\iff 5O-P>13-5\,\text{R\_cap}.
\]

\(D=5O-P\)(라운드24의 항등식)이므로 **\(D\)가 클수록 위험**하다 —
긴 preparation이 fresh orbit을 많이 열어 \(D\)를 키운 것이 직접적
원인이다.

## 6. 결론과 그 한계

> **여섯 counterexample state에서 Target B는 불가능하다.** 깊이
> 107~110 탐색은 **연기된 것이 아니라 불필요**하다.

주장하지 **않는** 것:

- Target C나 NR6에 대해서는 아무 말도 하지 않는다.
- **짧은 preparation의 same-component 경계에 대해서는 아무 말도 하지
  않는다** — 9/12는 이 장애물을 통과한다.
- Target A witness의 지위는 그대로다. 그것들은 여전히 legal한
  same-component \(R_2\) 경계이며, parity 명제들을 반증한 사실도
  그대로다.

**등급**: 정리 **손증명**, 여섯 certificate **exact obstruction**,
적용 범위 표 **exact replay**.
