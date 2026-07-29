# Target B segment 모델 (라운드 32 §1–2, §20)

산출: `src/build_rr_target_b_segment_graph.py` -> `outputs/rr_segment_graphs.json`,
`src/analyze_rr_segment_capacity.py` -> `outputs/rr_short_survivor_ledger.json`.
**permutation-level DFS 없음.** N=0 checkpoint 미접촉.

## 1. Segment 분해 (§2)

\(\Phi=0\) continuation을

\[
S_0\,X_1\,S_1\,X_2\cdots X_m\,S_m
\]

로 분해한다. \(S_i\)는 **한 E-orbit 안에서의 orbit-보존 run**,
\(X_i\)는 **orbit-변경 edge**다.

| 생성원 | 역할 | 비용 |
|---|---|---|
| \(E=g(\texttt{w2:10})\) | 보존, phase \(+1\) | 없음 (Z2) |
| \(E^2=g(\texttt{w3:120})\) | 보존, phase \(+2\) | **항상 R** → R 슬롯 1 |
| \(g(\texttt{w3:201})\), \(g(\texttt{w3:210})\) | 변경 | fresh opening(O 슬롯) 또는 R(R 슬롯) |

\(\operatorname{cap}(S_i)\) = 그 segment가 실제로 쓰는 자기 orbit의 port
수(entry port 포함). E-orbit의 port는 5개이고 \(pE^{s}=pE^{s'}\iff
s\equiv s'\pmod5\)이므로 **\(\operatorname{cap}\le5\)**.

## 2. 보존 run 전수표 (§2, §13 지원)

| 길이 | legal word 수 | capacity | \(E^2\) 개수 |
|---:|---:|---:|---|
| 0 | 1 | 1 | {0} |
| 1 | 2 | 2 | {0,1} |
| 2 | 4 | 3 | {0,1,2} |
| 3 | 5 | 4 | {0,1,3} |
| **4** | **3** | **5** | **{0,2,4}** |
| ≥5 | **0** | — | — |

## 3. 세 단계 bound와 각각의 가정 (§20)

### (A) coarse
\[
B+1\le5(m+1),\qquad m\le O_{\mathrm{cap}}+R_{\mathrm{cap}}
\]
**가정**: \(\Phi=0\), 생성원 대수. **등급: 손증명.**

### (B) initial-phase refined
\[
B+1\le c(q_0)+\sum_{\text{unopened }q\text{ 중 }c\text{ 상위 }O_{\mathrm{cap}}}c(q)+5R_{\mathrm{cap}}
\]
\(c(q)=\) hexagon이 미방문인 \(q\)의 port 수.
**추가 가정**: port는 hexagon이 비어 있어야 쓸 수 있다.
**등급: safe segment bound.**

### (B+R) orbit-reuse penalty — **이번 라운드의 새 재료**

> **Lemma (손증명)**: orbit-변경 **R** edge로 진입한 segment는
> **이미 열린** orbit에 있다 — edge가 fresh opening이 아니라 R인
> 이유가 바로 `new_orbit=False`이기 때문이다. 열린 orbit에는 방문된
> port가 최소 하나 있으므로 그 segment의 capacity는 **최대 4**다. ∎

\[
\boxed{\;B+1\le c(q_0)+\sum_{\text{top }O_{\mathrm{cap}}}c(q)+\mathbf{4}R_{\mathrm{cap}}\;}
\]

**등급: 손증명** (§9의 "orbit reuse penalty \(r\ge1\)"이 정확히 이것).

### (C) segment-defect
\[
B+1\le5(m+1)-\sum_i d_i,\qquad d_i=5-\operatorname{cap}(S_i)
\]
**등급: 손증명**(A의 정의적 재서술). survivor는 defect를 refined
margin만큼만 허용한다.

## 4. 결과 — survivor 9 → **7**

| \(\ell\) | \(P_{\mathrm{core}}\) | \(B{+}1\) | (A) | (B) | (B+R) | 판정 |
|---:|---:|---:|---:|---:|---:|---|
| 0 | 2 | 115 | 125 | 123 | 122 | 생존 |
| **0** | **4** | **113** | 115 | 113 | **112** | **제거 — R penalty가 새로 잡음** |
| 4 | 2 | 116 | 125 | 123 | 122 | 생존 (×3) |
| **4** | **4** | **114** | 115 | **113** | 112 | **제거 — (B)에서 이미** |
| 4 | 6 | 112 | 120 | 118 | 117 | 생존 (×3) |

- (B)로 제거: **1**
- (B+R)로 제거: **2** — **R-reentry penalty가 1개 추가 제거**

**최종: SEGMENT_SURVIVOR 7개.**

## 5. 누적 현황

| 단계 | 남은 Target A 경계 |
|---|---:|
| 전체 | 18 |
| capacity theorem (R30–31) | 9 |
| initial-phase refinement (R31) | 8 |
| **orbit-reuse penalty (R32)** | **7** |
