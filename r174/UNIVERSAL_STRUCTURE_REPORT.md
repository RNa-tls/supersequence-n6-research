# Round 174 — 보편 master 구조와 두 증명 구조의 대응

**목표.** `Δ(n) = L_n − CONST(n)`, `CONST(n) = n!+(n−1)!+(n−2)!+n−3`에 대해, 기존 두 증명 구조가 무엇을 말해 주는지를 정리합니다.

**작업 범위.**
- 이번 라운드는 수학적 분석이 중심입니다. 계산은 작은 반증 테스트만 했습니다(모두 수 초 이내).
- 5040개 순열 capacity 전수, 대형 EXTREE 작업, n=7 재현, 인증서 대량 생성은 하지 않았습니다.
- 작업 브랜치는 `claude/round174-universal-structure`이고, n=6 production 브랜치와 인증 산출물은 건드리지 않았습니다.

## 0. 읽은 출처 (모두 GitHub에서 받아 직접 읽음)

| 저장소 | 커밋 | 무엇 |
|---|---|---|
| `jlebar/superperm7-ge-5898` | `f516e19` (2026-08-13) | `5898 ≤ s(7) ≤ 5906`, Lean + `native_decide` 380개 |
| `BGray-wrl/superperm6` | `d8a932d` (2026-07-29) | `s(6) = 872`, Lean. 위 저장소 reduction의 원본 |
| `urdvr/superpermutations-hunter` | `d452221` (2026-07-28) | Hunter–Raudvere 일반 하한, Lean(`native_decide` 없음) |
| `Haruhiyuki/superpermutations-preimage-chain-lower-bounds` | `23fdbc5` (2026-08-10) | Liu 일반 하한 `hunterBound k + Γ_k`, Lean |
| `urdvr/superperm-coeff2` | `12acadf` (2026-07-17) | Raudvere 계수-2 하한, Lean |
| `superpermutators/superperm` | `7922798` | 문자열 아카이브 |

**검증된 주장과 그렇지 않은 주장의 구분.**
- Lean으로 검증된 것: 위 표의 각 헤드라인 정리. 외부 README들이 적은 `#print axioms` 기록이 근거이고, **이 컨테이너에서 Lean으로 다시 빌드하지는 않았습니다.**
- 미검증이거나 조건부인 것: jlebar README가 인용하는 Kisic 5893(비공식)과 Gheorghe 5896(조건부). 5905 탐색 실패는 증거일 뿐입니다.

## 1. 이전 일반 n 결과의 정정 (Round 173)

| Round 173 진술 | 정정 |
|---|---|
| "Δ(n) ≥ 1 (n ≥ 5)가 문헌에 있는지 확인 못 함" | **알려진 결과입니다.** Houston(2018 말), Tadewaldt(2019), Engen–Vatter(2021). R173의 완전 사슬 논증은 별도의 증명 경로일 뿐 새 결과가 아닙니다. |
| "가장 강한 일반 하한은 1 ≤ Δ(n)" | **틀렸습니다.** 문헌의 Lean 검증 일반 하한: 계수-2 `⌈((n−3)!−1)/(2n−1)⌉`, Hunter–Raudvere `⌈((n−2)!−(n−2))/(n²−3n+1)⌉`, Liu `hunterBound(n)+Γ_n`(현재 최강, 표는 §8). |
| "n=7: 1 ≤ Δ(7) ≤ 22" | **14 ≤ Δ(7) ≤ 22** (`s(7) ≥ 5898`, jlebar Lean). 정확값이 아니라 구간입니다. |
| "L₆ = 872는 프로젝트 결과(재인증 진행 중)" | 외부에서 **Lean으로 형식화 완료**(superperm6). |
| P2(φ 강제 연속), MASTER 항등식, Chaffin 재현, 후보 `(n−3)!−1`의 반례 | **유지.** P2는 jlebar의 `full_block_successor`(n=7, `native_decide`)의 일반 n 기호 증명에 해당합니다(§4). |

## 2. 기준선

- **MASTER는 단어 하나에 대한 항등식입니다.** 고정 대표원 W(trim되어 있고 모든 간격이 최단 overlap)에 대해 `L(W) = CONST(n) + t(W)`, `t = k + Z + H + B*`입니다.
  - 정의역은 n ≥ 3입니다. 아카이브 단어는 전부 고정 대표원이었습니다.
- **`L_n`은 최소화입니다.** `L_n = CONST(n) + min_W t(W)`, 즉 `Δ(n) = min_W t(W)`입니다. 항등식 자체는 Δ(n)에 대해 아무것도 말하지 않고, 하한은 t의 하한에서만 나옵니다.
- **n=7 구간:** `5898 ≤ L₇ ≤ 5906`(하한은 Lean, 상계는 Egan–Houston 문자열), 즉 `14 ≤ Δ(7) ≤ 22`입니다.

## 3. 두 구조의 대응표

외부 변수(n=7 Lean의 정의를 일반 n으로 읽음)는 다음과 같습니다.
- `r = |runStartSet| − HEX`
- `q = |chainStartSet|`
- `p = #(cost ≥ 4) + 1`
- `M = #touched blocks`, `m = M − ORB`
- `k_rot` = rotation graph의 성분 수
- `a = k_rot − ORB − m + r`, `b = q − k_rot`, `η = p − 1`, `D = m + a + b + η`

| 우리 (MASTER) | 외부 (jlebar/superperm6) | 분류 | 근거 |
|---|---|---|---|
| pass 수 `P`, `G = P − HEX` | run start 수 `HEX + r` | **PROVED_EQUIVALENT** (`r = G`) | 정리 1 |
| `S = #{w ≥ 3}` | `q = #chain starts` | **PROVED_EQUIVALENT** (`q = S+1`) | 정리 1 |
| `h = #{w ≥ 4}` | `η = p − 1` | **PROVED_EQUIVALENT** (`η = h`) | 정리 1 |
| `H = Σ(w−3)₊` | capped weight(4 초과 절단) | **PROVED_IMPLICATION** (`H ≥ η`, 차이 `Σ(w−4)₊`) | 정리 1 |
| `O`(pass 진입점의 τ-궤도 수), `k = O − ORB` | touched blocks `M`, `m` | **PROVED_EQUIVALENT** (`M = O`, `m = k`. F = τ) | 정리 1 |
| `Z + B*` | `a + b` | **PROVED_EQUIVALENT** | 정리 1 |
| `Z` 단독, `B*` 단독 | `a` 단독, `b` 단독 | **INCOMPATIBLE** (개별로는 다름) | 말뭉치 651단어 중 484개에서 `a ≠ Z` (§6) |
| `t = k + Z + H + B*` | defect `D` | **PROVED_IMPLICATION** (`t = D + (H − h) ≥ D`) | 정리 1 |
| 육각형(σ-류) | rotation class `rClass` (R-궤도) | **PROVED_EQUIVALENT** | 정의 |
| τ-궤도 | insertion block `fBlock` (F-궤도) | **PROVED_EQUIVALENT** | 정의 (F = τ) |
| incidence graph `B`, `β`, `c`, `d`, `g` | rotation graph, `k_rot` | **UNRESOLVED** | 합 `a+b`만 대응이 증명됨 |
| φ (R173 P2), 완전 사슬 | `G`, `full_block_successor`, `no_six_pairwise_disjoint_full_rows` | **PROVED_EQUIVALENT** (n=7), 우리 쪽은 일반 n 증명 | 정리 2 |
| 사슬/조각 추출, chain capacity (n=6 표) | trail(무게-3 연쇄), marked row, charge, 단일 trail capacity `M_μ(g)` | **ANALOGOUS_ONLY** | 둘 다 "무게-3로 이어진 τ-블록 run의 최대 개수"지만 우리 셀 좌표와 외부 charge는 다른 좌표계 |
| `D_φ = (n−1)O − P` | 총 charge 상한 `u = (n−1)m − r` | **PROVED_EQUIVALENT** (`u = (n−1)k − G = D_φ`) | 정리 1 + 대수 |
| 우리 capacity 상계와 census | superadditive closure, max-plus convolution | **ANALOGOUS_ONLY** | 둘 다 개별 capacity를 합산하는 relaxation |
| 등호 배제(T.eq872) | equality cell 배제(9개 cell, relabel join) | **ANALOGOUS_ONLY** | 둘 다 n별 유한 계산 |
| MASTER 비음성(`H.splice`, `H.samehex`, `H.incidence`, `H.extract`) | `a ≤ r`, `r ≤ (n−1)m`, `k_rot ≤ M`, `k_rot ≤ q` | **PROVED_IMPLICATION**, 합 수준에서만 | `a ≥ 0` ⟸ 성분 수 ≥ 꼭짓점 − 간선. `b ≥ 0` ⟸ `k_rot ≤ q`(외부 Lean, n=7). 그러면 `Z+B* ≥ 0` |

## 4. 정리와 증명

### 정리 1 (Dictionary, 일반 n, 무조건)

**가정.** W는 n ≥ 3 기호 위의 고정 대표원이고, route `v₁…v_N`은 선택 창의 순서, 간선 비용은 `g_j = ω(v_j, v_{j+1})`입니다. 외부 양은 위 정의를 그대로 따릅니다.

**결론.**
- `r = G`, `q = S + 1`, `p = h + 1`, `M = O`, `m = k`, `a + b = Z + B*`, `u = D_φ`
- **`D = t − (H − h)`**, 따라서 `t ≥ D`

**증명.**
1. `runStartSet`은 비용-1 간선의 도착점이 아닌 순열이고, 이는 정확히 pass 진입점입니다(pass = 최대 비용-1 run). 따라서 `|runStart| = P`, `r = P − HEX = G`입니다.
2. `chainStartSet`은 비용 1 또는 2 간선의 도착점이 아닌 순열이므로 `q = N − #(비용 ≤ 2 간선) = N − (N−1−S) = S + 1`입니다. 비용 ≥ 3 간선이 정확히 무게 ≥ 3 joint이기 때문입니다.
3. `p − 1 = #(비용 ≥ 4) = h`입니다.
4. F = τ이므로 touched block은 pass 진입점의 τ-궤도이고, `M = O`, `m = O − ORB = k`입니다.
5. `a + b = (k_rot − O + G) + (S + 1 − k_rot) = G + S + 1 − O`입니다. 우리 정의 `Z = G − c − D2`, `B* = S + 1 + D2 − O + c`에서 `Z + B* = G + S + 1 − O`이므로 둘은 같습니다.
6. `D = k + (Z + B*) + h = t − H + h`입니다. `u = (n−1)m − r = (n−1)(O − ORB) − (P − HEX) = (n−1)O − P = D_φ`입니다(`HEX = (n−1)ORB`). ∎

**반증 테스트** (`r174/src/dict174.py`, `r174/certs/dictionary_174.json`): 아카이브 44,417단어(n=5..9)와 프로젝트 말뭉치 651단어(n=3..5, `Z, B*, D2 > 0` 포함)에서 모든 항등식과 외부 guard가 성립했습니다. 위반은 0입니다.

**따름정리.**
- 외부의 모든 D 하한은 우리 t로 옮겨집니다. 예: n=7에서 모든 단어가 `t ≥ 14`입니다.
- 외부의 capped identity `n + capped = CONST(n) + D`는 우리 (FO)에서 `Σ(w−4)₊`를 뺀 것과 같습니다.

### 정리 2 (row 모형의 기호 보조정리, 일반 n ≥ 4, 무조건)

외부의 n=7 `native_decide` 사실들을 일반 n에서 기호로 증명합니다. `p = c₁…cₙ`, row = `(p, ℓ)`, `1 ≤ ℓ ≤ n−1`로 둡니다.

**(a) 끝점 공식.** `β(p, ℓ) = c_{ℓ+2} … c_{n−1} c₁ … c_{ℓ−1}` (길이 n−3)입니다. `ℓ = n−1`이면 `β = c₂…c_{n−2}`입니다.

*증명.* `F^{ℓ−1}p = c_ℓ…c_{n−1} c₁…c_{ℓ−1} cₙ`이고, 이를 오른쪽으로 한 칸 회전하면 `cₙ c_ℓ … c_{n−1} c₁ … c_{ℓ−1}`입니다. 앞 세 글자를 버리면 됩니다.

외부의 `row_endpoint_table`(n=7)이 이 공식의 사례입니다. 우리 구현으로 n=5..8의 모든 p를 확인했습니다.

**(b) loop 보조정리.** `ℓ = n−2`이면 `β = c₁…c_{n−3} = α(p)`입니다. (a)에 대입하면 됩니다. 외부의 `length_five_row_is_loop`에 해당합니다.

**(c) 완전 row 후계.** `β(p, n−1) = α(q)`이고 두 완전 row의 육각형 집합이 서로소이면 `q = φ(p) = c₂…c_{n−2} c₁ c_{n−1} cₙ`입니다. 역도 성립합니다.
- 증명은 R173의 P2 표와 같습니다(다섯 후보마다 공통 육각형 D를 명시).
- 역은 이렇습니다. `φ(p)`의 특수 기호는 `cₙ`으로 같고, 순환 `(c₂…c_{n−2} c₁ c_{n−1})`은 n ≥ 4에서 `(c₁…c_{n−1})`과 다릅니다. 따라서 육각형 집합이 서로소입니다.
- 외부의 `full_block_successor`(n=7)에 해당하고, φ가 외부의 `G`입니다.

**(d) φ의 위수는 정확히 n−2.** φ는 위치 1..n−2의 순환 이동이므로 위수가 n−2입니다. n=7에서 외부의 `G_order_five`와 같습니다.

**(e) `M_n(0) = n−2` (정확).**
- 상계: charge 0인 row는 완전 row뿐이고, (c)에 의해 `p, φp, …`로 강제됩니다. (d)에 의해 `φ^{n−2}p`는 p와 같은 block이라 block 서로다름에 위배됩니다.
- 하계: `φ^i p` (i < n−2)는 특수 기호 `cₙ`이 같고 순환 `(c₁…c_{n−2}`의 회전`, c_{n−1})`이 서로 다르므로 육각형 집합이 서로소입니다.

**(f) 구간 보조정리와 기울기.**
- **주장:** 모든 trail에서 charge 0인 row가 연속된 구간은 최대 n−2개이고, 따라서 `M_n(g) ≤ (n−2) + (n−1)g`입니다.
- **증명:** charge ≥ 1인 row는 최대 g개입니다. 이들이 완전 row 구간을 최대 g+1개로 나누고, 각 구간은 (e)에 의해 ≤ n−2개입니다. 합하면 `≤ (n−2)(g+1) + g`입니다. marked row(생략 위치가 있으면 charge ≥ 1)에도 그대로 성립합니다. ∎

### 정리 3 (capacity → defect 전이, 일반 n. 가정: Bridge(n))

**가정 Bridge(n).** 외부 `coarsen_bridge`의 일반 n판입니다. defect가 D인 정규화 route마다 다음이 존재합니다.
- `(m, a, b, η, r)`: `a ≤ r ≤ (n−1)m`
- CoarsenedInstance: row 수 `ORB + m − r + a`, trail 수 `≤ η + 1 + b`, 총 charge `≤ (n−1)m − r`

jlebar은 이것을 n=7(D ≤ 13)에서 Lean으로 증명했고, reduction은 상수 치환만으로 이식되었습니다(PORT_LOG). **일반 n 진술로 증명된 적은 없습니다.**

**정리.** Bridge(n)이 성립하고, 단일 trail capacity가 모든 g에서 `M_n(g) ≤ (n−2) + α g` (α ≥ 1)이면

`D ≥ (n−2)((n−3)! − 1) / max(n−2, α(n−1) − 1)`.

따라서 `Δ(n) ≥` 같은 값입니다(정리 1에 의해 `t ≥ D`).

*증명.*
1. 각 trail의 row 수는 `≤ M(c_i)`이므로 `ORB + m − r + a ≤ Σ M(c_i) ≤ (η+1+b)(n−2) + α((n−1)m − r)`입니다.
2. 정리하면 `ORB − (n−2) ≤ (n−2)(η + b) + (α(n−1) − 1)m − (α−1)r − a`입니다.
3. `α ≥ 1`, `r ≥ 0`, `a ≥ 0`이므로 우변은 `≤ max(n−2, α(n−1)−1)·(m + b + η) ≤ max(…)·D`입니다.
4. `ORB − (n−2) = (n−2)((n−3)! − 1)`을 대입하면 끝납니다. ∎

**(f)의 α = n−1을 대입한 따름정리:** `Bridge(n) ⇒ Δ(n) ≥ ⌈((n−3)! − 1)/n⌉`.
- 이 capacity 구조가 가장 초보적인 기호 보조정리만으로 Hunter–Raudvere(`≈ ((n−3)!−1)/(n−1)`)와 거의 같은 차수를 재현합니다.
- 두 구조가 같은 현상을 보고 있다는 교차 확인이지만, 문헌보다 강한 새 하한은 **아닙니다.**

### "추가 τ-궤도 = 지름길"의 최대 절약량 (§4 요구사항)

정리 3의 2단계에 `η ≤ H`, `b ≤ a + b = Z + B*`를 쓰면 다음을 얻습니다.

`H + Z + B* ≥ F(n,k) := [ (n−2)! − (n−2) − (α(n−1) − 1)·k ] / (n−2)`

그러므로 `Δ(n) ≥ min_k (k + F(n,k))`입니다. F는 원래 최소화를 다시 쓴 것이 아니라, capacity 기울기 α 하나로 정해지는 식입니다.

**추가 궤도 하나가 줄일 수 있는 "trail 끊김"(무게≥4 joint와 b)의 수는 최대 `(α(n−1) − 1)/(n−2)`입니다.**

| 기울기 α | 근거 | 궤도당 절약 상한 |
|---|---|---|
| n−1 | 증명됨 (정리 2(f)) | ≤ n |
| (n−1)/2 | LL 가정 시 | ≈ n/2 |
| (n−3)/2 | C1 가정 시 | ≈ n/2 |
| (관찰) | n=7: 궤도 22개 ↔ 무게-4 joint 23개. n=8: 119↔119. n=9: 720↔719 | ≈ **1** |

## 5. R173 완전 사슬 결과의 감사 (§5 요구사항)

- **φ 독립 재구성.** φ는 첫 n−2 기호를 왼쪽으로 한 칸 회전하고 마지막 두 기호를 고정합니다. 위수는 n−2이고 R173 주장이 맞습니다. 외부 `G`와 같습니다(n=7, `gIndex` = 앞 다섯 회전, `G_order_five`).
- **n ≥ 5 불가능 논증.** 올바릅니다. 다만 "새 결과"는 아닙니다(§1).
- **부분 사슬(추가 τ-궤도 포함)로 확장되는가?** 부분 사슬은 정확히 외부의 **charge가 있는 trail**입니다.
  - charge 0 구간에서는 φ 논증이 그대로 통합니다(정리 2(e), (f)).
  - charge ≥ 1인 row에서는 강제가 풀립니다. loop row(길이 n−2) 뒤에 가능한 시작점이 셋입니다(n=7, 8에서 추적. `…c_{n−2}cₙc_{n−1}`, `…c_{n−1}c_{n−2}cₙ`, `…cₙc_{n−1}c_{n−2}`).
  - 그래서 R173 논증은 **charge 0 구간까지만** 확장되고, 그 이상은 아래 누락 보조정리 LL/C1이 필요합니다.

## 6. 제약 조건과의 대조 (§6 요구사항)

| 진술 | L₆ = 872 | n=7 Lean 14 ≤ Δ | 5906 구성 (t = D = 22) | R173 말뭉치 | 판정 |
|---|---|---|---|---|---|
| 정리 1 (dictionary) | 44,125단어 성립 | 139단어 성립 | D = 22 ≥ 14 ✓ | 651단어 성립 | 유지 |
| 정리 3 + α = n−1 | 1 ≤ 5 ✓ | 4 ≤ 14 ✓ | ✓ | — | 유지 (조건부) |
| C1 가정 시 하한 | 4 ≤ 5 ✓ | 11 ≤ 14 ✓ | ✓ | — | 모순 없음 |
| "a = Z, b = B* 개별 대응" | — | — | — | 484/651 반례 | **폐기** |
| 후보 `Δ(n) = (n−3)! − 1` (R173) | ✓ | 23 > 22 | **반례** | — | 폐기 유지 |
| C1: `M_n(g) ≤ (n−2) + (n−3)g/2` | n=6 g≤16 ✓ | 외부 Lean 표 g≤56 ✓ | — | n=5 g≤12, n=8 g≤5 ✓ | 가설 (반례 없음) |
| LL: charge ≤ 1 row 연속 ≤ n−2 | n=6 ✓ | n=7 ✓ | — | n=5, 8 ✓ | 가설 (반례 없음) |

**단일 trail capacity 표** (`r174/src/trailcap174.py`). 외부와 같은 row 모형을 일반 n으로 구현했습니다. n=7 값 `M(0..14)`는 외부의 Lean 인증 표와 전부 일치합니다.

| n | M(g), g = 0, 1, 2, … |
|---|---|
| 5 | 3, 3, 5, 5, 6, 6, 7, 7, 7, 8, 8, 8, 9 |
| 6 | 4, 4, 7, 7, 10, 10, 11, 13, 14, 15, 16, 17, 19, 19, 22, 22, 22 |
| 7 | 5, 5, 9, 9, 13, 13, 16, 16, 20, 20, 24, 24, 27, 27, 31 |
| 8 | 6, 6, 11, 11, 16, 16 |

네 n 모두 `M(0) = M(1) = n−2`, `M(2) = M(3) = 2n−5`입니다. g=2에서 기울기가 정확히 (n−3)/2로 tight합니다.

## 7. 외부 Lean 증명의 기호 부분과 유한 인증 부분 (§7 요구사항)

| 부분 | 성격 | 근거 |
|---|---|---|
| 단어 ↔ Hamilton route, 정규화, cheap cover, orbit 부등식, defect 항등식, surgery bridge (reduction 20개 파일) | **n에 대해 균일한 수학.** 다만 Lean 진술은 n=7 고정이고 상수가 박혀 있음. 쌍 단위 `native_decide`를 없앤 뒤 단일 순열 단위 `native_decide`는 남아 있음 | PORT_BRIEF, PORT_LOG |
| `row_endpoint_table`, `length_five_row_is_loop`, `full_block_successor`, `G_order_five` | n=7에서는 `native_decide`. **일반 n 기호 증명은 정리 2** | 이번 라운드 |
| 단일 trail capacity 표 `M_μ(g)`, closure, direct query, convolution sweep, equality cell 9개, 최적 trail 목록 | **n=7 전용 유한 인증** (248개 shard 등) | README, AUDIT |

**reduction을 n을 매개로 한 정리로 쓸 수 있는가?** 수학적으로는 n=6에서 n=7로 기계적 치환만으로 이식되었으므로 그럴 가능성이 높습니다. 하지만 ∀n 진술로 증명된 것은 **없습니다.** 이것이 정리 3의 가정 Bridge(n)입니다(UNRESOLVED).

## 8. 가장 강한 일반 하한

| n | 계수-2 | HR | **Liu (최강, Lean)** | 정리 3 (Bridge, 증명된 α=n−1) | LL 가정 시 | C1 가정 시 | 상계 (Egan (n−3)! / 기록) |
|---|---|---|---|---|---|---|---|
| 6 | 1 | 2 | 2 | 1 | 2 | 4 | 6 / **5** (정확) |
| 7 | 2 | 4 | 8 (Lean n=7 전용: **14**) | 4 | 7 | 11 | 24 / 22 |
| 8 | 8 | 18 | 33 | 15 | 31 | 44 | 120 / 119 |
| 9 | 43 | 92 | 172 | 80 | 163 | 219 | 720 / 720 |
| 10 | 266 | 568 | 1073 | 504 | 1021 | 1322 | 5040 |
| 14 | 1478400 | 3090333 | 5942830 | 2851200 | 5736546 | 6794349 | 39916800 |

(`r174/certs/bound_comparison_174.txt`)

**무조건적으로 증명된 가장 강한 일반 하한은 문헌의 Liu 하한입니다.** 이번 라운드는 무조건적인 새 일반 하한을 **얻지 못했습니다.**

C1과 Bridge(n)이 모두 성립하면 n ≥ 6 전체에서 Liu보다 강한 하한이 나옵니다. 하지만 **두 가정 모두 미증명**입니다.

## 9. 정확한 장애물과 다음 문제

**장애물.** Egan 상계는 `(n−3)!` 차수이고, 모든 알려진 일반 하한은 `≈ c·(n−3)!/n` 차수입니다. 격차 인자는 약 n입니다. 두 구조에서 그 원인이 같은 곳에 있습니다.
- (i) **capacity relaxation은 추가 궤도 하나가 최대 n−1개의 charge(구멍)를 자유롭게 만든다고 봅니다.** 그런데 한 trail 안에서도 charge 2마다 row가 n−3개 늘 수 있습니다(`M(2) = 2n−5`, 표에서 확인). 그래서 **단일 trail 모형은 궤도당 약 n/2개의 무게-4 joint 절약을 허용**하고, 실제 기록은 궤도당 약 1개를 절약합니다.
- (ii) 따라서 capacity를 정확히 알아도 이 구조만으로는 `≈ 2(n−3)!/n`을 넘기 어렵습니다. n=7에서 정확한 표로도 14이고, 진실은 ≤ 22입니다.
- (iii) 넘으려면 **추가 궤도의 나머지 pass들(trail에 쓰이지 않은 부분)도 어딘가에 배치되어야 한다**는 전역 제약, 즉 궤도의 "이중 사용 비용"을 정량화하는 새 보조정리가 필요합니다.

**다음 수학 문제 하나 (이것이 풀리면 장애물이 실질적으로 줄어듭니다).**

> **보조정리 LL (일반 n).** 외부 row 모형의 모든 trail에서, charge ≤ 1인 row만으로 된 최대 연속 구간은 row가 최대 n−2개다.

- 반례: n=5..8 전수에서 없음(탐색 노드 12/16/20/24개).
- 증명 상태: loop row의 1단계 후계가 세 가지로 갈린다는 것까지 확인했고, 전역 서로소 논증이 빠져 있습니다.
- 효과: LL이 증명되면 `M_n(g) ≤ (n−2) + (n−1)⌊g/2⌋`(기울기 (n−1)/2)가 됩니다. Bridge(n)과 합치면 `Δ(n) ≥ (n−2)((n−3)!−1)/((n−1)²/2 − 1) ≈ 2(n−3)!/n`, 즉 Hunter–Raudvere의 약 2배입니다.
- 그다음 단계는 C1(기울기 (n−3)/2)과 Bridge(n)의 일반 n 진술입니다.

## 파일
- `r174/src/dict174.py`, `r174/certs/dictionary_174.json`: 정리 1 반증 테스트
- `r174/src/trailcap174.py`, `r174/certs/trailcap_n{5,6,7,8}.json`: 단일 trail capacity (외부 모형, 일반 n)
- `r174/src/loopruns174.py`: LL 반증 테스트
- `r174/certs/bound_comparison_174.txt`: 하한 비교표

UNIVERSAL_STRUCTURE_PARTIAL
