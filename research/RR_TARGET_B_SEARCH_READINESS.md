# Target B search readiness 체크리스트 (라운드 29 §20–21)

**이번 라운드에서 대형 Target B DFS는 실행하지 않았다.** 아래는 준비
상태 점검이다.

## 1. 체크리스트

| 항목 | 상태 | 근거 |
|---|---|---|
| exact state key | **준비됨** | `ExactState.stable_key()`; 여섯 root 전부 서로 다르고 stabilizer tie 1 |
| history decoration | **준비됨** | \((r_{\text{count}}, r_1\text{tgt})\)로 충분함이 라운드19 §5에서 손증명 — 단 Target B는 R을 추가하지 않으므로 decoration이 **불변**이다 |
| safe prunes | **부분** | 5개 손증명 완료(repeated permutation, \(F_{\mathrm{def}}\), N/H, \(\Phi<0\), unavailable phase). 3개 미완료 |
| remaining-cost lower bound | **부분** | permutation coverage 하한만 안전. slack이 정확히 0이라 판별력이 **없다** |
| terminal recognizer | **미완료** | "pure-rotation suffix 허용 상태"의 판정기는 있으나(5회 rotation 시도) 여섯 전부 통과해 판별력이 없다 |
| certificate format | **준비됨** | 라운드27의 FOUND/EXHAUSTED_IMPOSSIBLE/INCOMPLETE + 독립 replay 인증 형식 재사용 |
| checkpoint/resume | **미준비** | 필요할 것으로 예상됨(\(B=110\) 깊이) |
| FOUND/EXHAUSTED/INCOMPLETE 구분 | **준비됨** | 라운드27 규약: frontier 자연소진일 때만 EXHAUSTED |

## 2. 지금 탐색하면 안 되는 이유

\(\Phi=0\)이므로 분기 인자는 매 단계 **최대 3**(§11의 transition
universe)이고 깊이는 **110**이다. 상한 \(3^{110}\)은 물론 실제로는
collision이 대부분을 죽이겠지만, **판별력 있는 하한이 하나도 없는
상태**에서 시작하면 라운드27의 22개 INCOMPLETE를 훨씬 큰 비용으로
반복할 뿐이다.

> **먼저 필요한 것**: `RR_TARGET_B_REMAINING_COST.md` §6의 hexagon
> Hamiltonian 그래프. slack이 0이므로 그 그래프의 **아주 약한 장애물
> 하나**(차수 1인 정점, 분리 정점, 이분성 불일치 등)만 있어도
> 즉시 정적 모순이 된다.

## 3. NR6 dependency graph — 현재 상태 (§21)

### 반증됨

| 노드 | 반증 라운드 |
|---|---|
| \(P_{\mathrm{core}}\) parity invariant | 27–28 |
| \(O_*\) zero-charge evenness | 27–28 |
| 단순 환원 \(\#Z\equiv k\) | 28 |
| short-alphabet closure (gap \(\le6\)) | 26 |

### 살아남음

| 노드 | 등급 |
|---|---|
| generator action theorem (\(g_j=\Sigma^5\circ a_j\)) | exact group computation |
| \(F_{\mathrm{sym}}\) restriction (F는 `w3:201`/`w3:210`뿐) | 손증명 |
| phase \(+1\) theorem | 손증명 |
| **corrected unconditional phase identity** | **손증명** |
| **T2 completer target \((1,4)\)** | **손증명 (신규)** |
| **T4a \(\ell=0\) forced, T4b R2 move 유일** | **손증명 (신규)** |
| **T7 \(\Phi=0\)** | **손증명 (신규)** |
| **T8 same-component 자동** | **손증명 (신규)** |
| **\(\Phi=0\) continuation theorem** | **손증명 (신규)** |
| **Target B ≡ hexagon Hamiltonian path** | **손증명 (신규)** |
| **CH1 (C가 R이면 chaining)** | **손증명 (신규)** |
| same-component ⟹ chaining (전체) | bounded observation 15/15 |
| terminal normal form (T1, T3, T9) | bounded observation 15/15 |

### open

- terminal normal form hand proof — **T3만 남음** (나머지 7개는 손증명)
- same-component ⟹ chaining hand proof — **CH2만 남음** (5/15는 손증명)
- Target B
- Target C
- RR branch closure

## 4. 이번 라운드의 순수 이득

| 성공 기준 | 결과 |
|---|---|
| 1. \(\ell=4\) terminal normal form 손증명 | **7/10 항목 손증명** (T2, T4a, T4b, T5, T6, T7, T8). T1·T3·T9는 관측 유지 |
| 2. long preparation 포함 chaining 증명 | **부분** — CH1로 15개 중 5개 손증명, CH2 미완료 |
| 3. corrected phase identity 정식화 | **완료 — 손증명** |
| 4. Target B transition universe exact 분류 | **완료** — 여섯 signature 동일, legal edge 3개 |
| 5. Target B remaining-cost 안전 하한 | **부분** — permutation coverage만, slack 0 |
| 6. 대형 탐색 전 정적 모순 판정 | **완료 — "lower bound incomplete"** (모순 없음을 단정하지 않음) |

**parity conjecture 복구 시도는 없었다.** 중심은 terminal structure와
Target B 비용으로 옮겨졌다.
