# Round 178 — 보편 coarsening bridge Bridge(n)

## 요약

| 항목 | 결과 |
|---|---|
| C1 (R177) | **재검증 완료.** 모든 의존 단계를 다시 유도했고 빈틈은 없었습니다(§1). 기계 검증은 아닙니다 |
| 외부 Lean 감사 | bridge 구성은 무게 가설을 쓰지 않습니다(`_hweight` 미사용). n = 7 수치는 `720/120/6`과 `D ≤ 13` 레지스트리에만 들어갑니다. `native_decide` 보조정리는 모두 "F가 한 block 위에서 위수 n−1의 회전"이라는 일반 사실의 n = 7 사례입니다(§2) |
| **Bridge(n)** | **모든 n ≥ 4, 모든 정규화 Hamilton route에 대해 증명**(§3–§4). 무게나 defect 제한 없음. row 수는 **등식** |
| 생성 구현 | n에 무관한 구현(`bridge178.py`)이 모든 구조 보조정리를 매 route마다 단언합니다. n = 4..7의 209개 route(n = 4 60개, n = 5..7 149개. D 최대 5911, 세 경우 (i)(ii)(iii) 모두 등장)에서 검증기 A, B 모두 통과했고, 변형 402개는 전부 거부됐습니다(§5) |
| Lean | 핵심 산술·조합 보조정리 6개가 core Lean 4.22에서 **`sorry` 없이 컴파일**됩니다(표준 공리만 사용). 기하 보조정리는 **형식화하지 않았습니다**(§6) |
| **Δ(n) 하한** | Bridge(n) + C1 ⇒ **모든 n ≥ 6에서 `Δ(n) ≥ ⌈2(n−2)((n−3)! − 1)/(n²−4n+1)⌉`**(§7). 6 ≤ n ≤ 300 전체에서 Liu 하한보다 큽니다(정확 계산) |
| 정확 공식까지의 간격 | 상계는 Egan `Δ ≤ (n−3)!`, 하한은 `≈ 2(n−3)!/n`입니다. 약 n/2배의 간격이 남아 있습니다(§8) |

**주의.**
- §7의 하한은 R174–R178에서 제가 쓴 여러 종이 증명의 연쇄에 기대고 있습니다: 정리 3, 정리 B, Lemma U/E, E2\*, E1, K, 그리고 이번 Bridge(n).
- 기계 검증된 것은 §6의 산술 핵심뿐입니다.
- 새 결과로 공표하기 전에 **독립적인 검토 또는 형식화가 필요합니다.**

브랜치는 `claude/round178-coarsening-bridge`입니다. n = 6 인증 산출물은 건드리지 않았습니다.

## 1. C1 감사 (R177)

**재구성할 주장.** n ≥ 6에서 `M_n(g) ≤ ⌊(n−2) + (n−3)g/2⌋`.

| 단계 | 의존 | 확인 내용 |
|---|---|---|
| 분할: 분리자(charge ≥ 2) h개, 최대 charge ≤ 1 구간 `U₀…U_h` | 정의 | 각 분리자는 왼쪽·오른쪽 구간이 서로 달라 `Σ s_U = 2h`. 빈 구간 포함. 끝 구간은 s = 1 |
| 동치식 `Σℓ_U ≥ Σ_σ d(c_σ)` | 산술 | `rows = (h+1)(n−2) + ((n−3)/2)Σc_U − Σℓ + h`로 다시 전개함. `2 − d(c) = (n−3)(c−2)/2 ≥ 0` |
| c = 0, s = 1: ℓ ≥ 1 | Lemma E | 한쪽 이웃만 필요. 이웃 종류 무관 |
| c = 0, s = 2: 두 이웃 길이 ≥ 2이면 ℓ ≥ 2 | E2\* | E2\* 증명은 이웃 charge 하한을 쓰지 않음(길이 ≥ 2만 사용) |
| c = 0, s = 2: 길이 1 이웃 있음 → 부족분 ≤ 1 | Lemma E | 그 길이 1 분리자에 부과 |
| c = 1: `|U| ≤ n−2` | E1 | loop 경우 `U = zR`는 Lemma E, 표시 경우는 R175 보조정리 5(k ≤ n−2) |
| n = 6, c = 1, s = 2 | E1, E2\*, **K** | 표시 경우 `|U| = n−2`는 K가 배제. loop 경우는 R 쪽 이웃에 따라 E2\* 또는 부족분 1/2 부과 |
| c ≥ 2: ℓ ≥ n−4 ≥ 2 | 정리 B | `|U| ≤ n−1` |
| 이중 계산 | — | 각 구간의 부족분은 이웃 **하나**에만 부과되므로, 길이 1 분리자가 받는 양은 ≤ 2. 여유 `(n−3)(n−4)/2 ≥ 3` (n ≥ 6) |
| h = 0 | R174 2(e), E1, 정리 B | c = 0, 1, ≥ 2 각각 C1 이하 |
| 홀짝 | — | 유리수 산술 등식이므로 홀짝 무관. floor는 row 수가 정수라서 성립 |

**판정: 검증됨(재유도).**
- 추가로 대조한 수치: 외부 인증 `capTab`(n = 7, g ≤ 36), marked `M_5(g ≤ 6)`, `M_6(g ≤ 5)`. 모두 C1 이하입니다.
- 형식 증명은 아닙니다.

## 2. 외부 Lean reduction 감사 (`jlebar/superperm7-ge-5898` @ `f516e19`)

| 정리/정의 | 내용 | n 의존성 |
|---|---|---|
| `RouteStructuralCounts` (Structural.lean) | `r, q, p, M, k, m, a, b, η`와 route 정의(`runStart_card = 720 + r`, `chainStart_card = q`, `p = highCost + 1`, `M = |touchedBlocks|`, `k = rotationComponentCount`), `M = 120 + m`, `k = 120 + m − r + a`, `q = k + b`, `p = η + 1`, 부등식 `a ≤ r ≤ 6m`, `k ≤ M`, `k ≤ q` | 720, 120, 6은 각각 (n−1)!, (n−2)!, n−1. **추가 필드 `budget : r+q+p ≤ 134`, `defect_le : D ≤ 13`은 무게 ≤ 5890에서 온 n = 7 전용이며, bridge에는 필요 없습니다** |
| `routeStructuralCounts_of_weight_at_most_5890` | 존재 증명. 쓰는 route 보조정리는 `runStartSet_card_le_six_mul_touchedBlocks`, `touchedBlocks_card_le_run_excess_add_components`(M ≤ r + k), `rotationComponentCount_le_chains`(k ≤ q), `…_le_touchedBlocks` | 보조정리 자체는 일반 명제입니다. 무게 가설은 `budget`/`defect_le` 필드에만 쓰입니다 |
| `RegistryCandidate`, `valid` (Registry.lean) | `(m,a,b,η,r)`, `D ≤ 13`, `a ≤ r ≤ 6m`, `k = 120+m−r+a`, `τ = η+1+b`, `u = 6m−r` | 유한 레지스트리(D ≤ 13)는 **n = 7 유한 계산**용입니다 |
| `CoarsenedInstance k τ u b` (Coarsen.lean) | trails, `trail_count ≤ τ`, **`row_count = k` (등식)**, compat, 전역 `MarkedDisjoint`, interior, `charge ≤ u`, `runs ≤ b` | 일반 |
| `retained_arc_system_of_structural_counts` | surgery 후 성분마다 한 면을 남기고 나머지를 삭제. trail 수 ≤ η+1+b | `hweight` 인자는 `cheap_profile_for_bridge`로만 전달되고 거기서 `_hweight`로 **미사용** |
| `retained_arc_accounting_outcome`, `coarsen_cases_of_structural_counts`, `coarsen_bridge_cases`, `coarsen_bridge`, `coarsen_bridge_forest` | 전하 `≤ 6m−r`, runs `≤ b`, 삼분법 (i)/(ii)/(iii), 그리고 `∃ u′ ≤ u, CoarsenedInstance k τ u′ b` | 산술만 사용 |
| `native_decide` (CoarsenAccounting 5개, CoarsenAux 1개, Orbit/CheapCover 몇 개) | `F_iterates_fin_six_injective`, `F_cut_interval_disjoint`, `F_apply_iterate_five`, `fBlock_F`, `N₂_eq_F_R`, `rClass_R_iterate` | 모두 "F는 block 위에서 위수 n−1인 회전, `N₂ = F∘R`, R-궤도 성질"이라는 일반 사실의 n = 7 사례입니다. §4에서 기호로 증명 |

**결론.**
- Lean의 n = 7 bridge는 논리적으로 n에 무관한 구성의 사례입니다. 그러나 **Lean 정리 자체가 n에 대해 증명된 것은 아닙니다.**
- 숫자 7을 변수로 바꾸는 것으로 일반화할 수 없고, 일반화의 근거는 §4의 기호 증명입니다.
- 원 논문(Grayzel, superperm6 `paper/superperm6.tex` §5)의 서술도 상수만 빼면 n에 무관합니다.

## 3. Bridge(n)의 정확한 진술

**기호와 정의.**
- `N = n!`, `HEX = (n−1)!`(순환류 수), `ORB = (n−2)!`, `CONST(n) = N + HEX + ORB + n − 3`.
- **route**: `S_n`의 모든 순열을 한 번씩 방문하는 순서.
- 간선 비용 `d(x,y) = n − (x의 접미사와 y의 접두사가 겹치는 최대 길이)`. route의 무게는 간선 비용의 합이고, route 길이는 `n + 무게`입니다.
- **정규화 route**: 간선 `x → R²x`가 없는 route.
- 구조량 (모두 route에서 직접 정의):
  - `S` = cost-1 간선으로 들어오지 않는 순열, `r := |S| − HEX`
  - `q` = cost 1 또는 2 간선으로 들어오지 않는 순열의 수(chain 수)
  - `p` = cost ≥ 4 간선 수 + 1
  - `M` = S와 만나는 F-block 수, `k` = 그 block들을 A-순환(각 순환류의 run start를 R-순서로 잇는 것)으로 이어 만든 그래프의 성분 수
  - `m := M − ORB`, `a := r − (M − k)`, `b := q − k`, `η := p − 1`, `D := m + a + b + η`

**정리 (Bridge(n)).** 모든 n ≥ 4와 모든 정규화 route에 대해 다음이 성립합니다.
- (0) `m, a, b, η ≥ 0`, `a ≤ r ≤ (n−1)m`, `k ≤ q`, `1 ≤ p ≤ q`.
- (1) 상한을 씌운 길이 `L_c := n + Σ_{비용 ≤ 3} 비용 + 4(p−1)`는 **`L_c = CONST(n) + D`**를 만족하고, `L_c ≤ n + 무게`입니다.
- (2) 다음 조건을 만족하는 marked-row trail 목록이 존재합니다. 즉 `CoarsenedInstance_n(k*, τ, u, b)`입니다.
  - row 수 **정확히** `k* = ORB + m − r + a` (= k)
  - trail 수 ≤ `τ = η + 1 + b`
  - 연속 row 호환
  - 모든 row 쌍의 block이 다르고 visible 순환류가 서로소
  - 생략 위치는 내부
  - 총 charge ≤ `u = (n−1)m − r`
  - 생략 run 총수 ≤ `b`
- (3) 삼분법: (i) 생략 run이 있거나, (ii) 총 charge ≤ u−1이거나, (iii) 생략이 없고 charge = u이며, row block이 아닌 touched block `r − a`개가 보이지 않는 모든 순환류와 만난다.

외부 정의와의 대응은 다음과 같습니다.
- `720 + r ↔ HEX + r`, `120 + m ↔ ORB + m`, `6m − r ↔ (n−1)m − r`.
- R174 dictionary와는 `r = G`, `q = S+1`, `η = h`, `M = O`, `m = k_master`, `a+b = Z+B*`, `t = D + (H−h)`로 대응합니다. 개별 등식 `a = Z`, `b = B*`는 **쓰지 않습니다.**

## 4. 기호 증명 (모든 n ≥ 4)

**B1 (비용 구조).**
- cost-1 후계는 `Rx` 하나뿐이고, cost-2 후계는 `R²x`와 `N₂x = x₃…xₙx₂x₁` 두 개입니다.
- 이는 겹침이 n−1, n−2일 때의 정의에서 바로 나옵니다.
- `N₂ = F∘R`: `F(Ry) = F(y₂…yₙy₁) = y₃…yₙy₂y₁`.

**B2 (run).**
- route는 경로이므로 한 순환류의 n개 회전 간선을 모두 쓸 수 없습니다. 따라서 모든 순환류가 S와 만나고, `r ≥ 0`, `|S| = HEX + r`입니다.
- s에서 시작한 run은 `R^{−1}A(s)`에서 끝납니다. 끝점 y 다음의 `Ry`는 cost-1 간선으로 들어오지 않으므로 S에 속하고, s와 y 사이의 원소들은 cost-1로 들어오므로 S에 속하지 않습니다.

**B3 (T와 chain).**
- run 끝점의 proper cost-2 후계는 `N₂(R^{−1}A s) = F(A s) = T(s)`입니다.
- 따라서 chain은 T를 따르는 run start들의 열입니다.
- `T = F∘A`(구멍에서 A = id)는 U 위의 순열입니다. F는 각 block의 순환이고, A는 S 위의 순열이면서 구멍을 고정하기 때문입니다.

**B4 (계수).**
- `S ⊆ U`이므로 `HEX + r ≤ (n−1)M`, 즉 `r ≤ (n−1)m`입니다. HEX = (n−1)·ORB를 씁니다.
- 구멍 수는 `(n−1)M − |S| = (n−1)m − r = u`입니다(Lean `holes_identity`).
- A는 전치 r개의 곱이고(순환류마다 j−1개), 이 전치들이 M개 block을 잇는 그래프의 간선입니다. 따라서 `M − k ≤ r`, 즉 `a ≥ 0`입니다.
- 이 그래프의 성분은 `⟨F, A⟩`의 궤도와 같습니다. chain은 T-궤도 안에 있고 각 성분에는 run start가 있으므로 `k ≤ q`입니다.

**B5 (길이 항등식).**
- 비용별 간선 수는 `x₁ = N − |S|`, `x₂ = |S| − q`(정규화이므로 cost-2 간선은 모두 proper), `x₃ = q − p`입니다.
- `L_c = n + x₁ + 2x₂ + 3x₃ + 4(p−1) = CONST + D`입니다(Lean `capped_length_identity`).
- cost ≥ 4 간선을 4로 셌으므로 `L_c ≤ n + 무게`입니다.

**B6 (gap).**
- 구멍만으로 된 T-순환은 없습니다. 있다면 F-순환, 즉 block 전체가 구멍인데, 그런 block은 U에 없습니다.
- 모든 T-순환에는 gap이 적어도 하나 있습니다. 없다면 사용된 route 간선이 닫힌 순환을 이루는데, route는 경로이므로 불가능합니다.
- gap은 두 종류입니다.
  - 구멍의 최대 T-run: A가 구멍을 고정하므로 T = F이고, 따라서 한 block 안에 있습니다.
  - 인공 gap: chain의 마지막 run start s 뒤의 `T s`가 S에 속하는 경우.
- 한 순환의 gap 수는 그 순환의 chain 수와 같으므로 전체 gap 수는 q입니다.

**B7 (보완 row).**
- 구멍 run gap (구멍 `x, …, F^{d−1}x`)의 보완 row는 `(F^d x, …, F^{n−2}x)`로, 길이 `n−1−d ≥ 1`입니다.
- 인공 gap (s 다음)의 보완 row는 `T s`에서 시작하는 full row입니다.
- 두 경우 모두 다음이 성립합니다.
  - `α(row) = α(gap 다음 chain의 머리)`
  - `β(row) = drop 3(R^{−1}(마지막 상태)) = drop 3(R^{−1}A(s′)) = gap 앞 chain의 꼬리`. 여기서 마지막 상태는 `F^{n−2}x = F^{−1}x = A(s′)`입니다.
- 길이 n−3짜리 머리·꼬리를 쓰므로 경로 위의 cost-3 간선은 정확히 `β = α` 호환입니다.

**B8 (surgery와 삭제).**
- 초기 trail은 경로 p개이고, 각 경로는 chain(arc)들의 열입니다.
- 한 순환에서 cyclic하게 인접한 arc I, J가 서로 다른 trail에 있거나 같은 trail에서 I < J이면, 둘을 `(head I → tail J)`로 합칠 수 있습니다. 이때 trail은 최대 1개 늘어납니다(논문 보조정리 5.2).
- 그런 쌍은 항상 존재합니다. 모든 인접 쌍이 불가능하면 같은 trail 위 위치가 순환을 따라 엄격히 감소해야 하는데, 이는 모순입니다(Lean `cyclic_not_all_decreasing`).
- 순환마다 `c−1`번 합치면 병합은 `q − cyc(T)`번입니다. 성분마다 순환 하나를 남기고 나머지 arc를 지우면 삭제마다 trail이 최대 1개 늘어나 `cyc(T) − k`개가 추가됩니다.
- 따라서 trail 수 ≤ `p + q − k = η + 1 + b`입니다(Lean `trail_budget`).
- 남은 arc는 성분당 하나로, 그 순환의 **남긴 gap**의 보완 row(B7)가 됩니다. 따라서 row 수는 **정확히 k**입니다. 호환성은 바깥 끝점만 쓰므로 보존됩니다.

**B9 (생략과 charge).**
- row 구간 안의 구멍을 생략 위치로 둡니다. 구간의 첫 상태와 마지막 상태는 선택 상태이므로 생략은 내부에 있습니다.
- 구간 밖은 남긴 gap의 구멍 d개이므로 **charge(row) = row block의 구멍 수**입니다.
- row block은 성분마다 다르므로 **총 charge ≤ 전체 구멍 수 = u**입니다.

**B10 (생략 run ≤ b).**
- 한 block 안에서 구멍의 최대 F-run은 최대 T-run과 같습니다(T = F on holes, `T^{−1}` 계산).
- 따라서 row 안의 각 생략 run은 그 block의 gap 가운데 **남긴 gap이 아닌** 것이고, 구멍 run은 한 block에만 속하므로 서로 다른 run은 서로 다른 gap입니다.
- 남기지 않은 gap은 `q − k = b`개이므로 생략 run 총수는 ≤ b입니다.

**B11 (서로소).**
- row block들은 서로 다른 성분에 있으므로 서로 다릅니다.
- visible 상태는 구간 안의 선택 상태입니다. 한 순환류의 run start들은 A로 연결되어 한 성분에 속합니다.
- 따라서 서로 다른 성분의 row는 visible 순환류를 공유하지 않습니다.
- 구멍(생략된 상태)의 순환류는 공유될 수 있으며, 그래서 모형은 visible만 추적합니다.

**B12 (삼분법).**
- 남기지 않은 gap 가운데 row block 안에 있는 구멍 gap이 있으면 (i)입니다.
- 없고 row block 밖에 구멍 gap이 있으면, 그 구멍은 u에 들어가지만 어느 row에도 들어가지 않으므로 (ii)입니다.
- 둘 다 아니면 모든 구멍이 남긴 gap에 있어 charge = u이고 생략이 없으므로 (iii)입니다.
  - 이때 row block의 선택 상태는 모두 보이므로, 보이지 않는 순환류의 run start는 row block 밖의 touched block(`M − k = r − a`개)에 있습니다.
- b = 0이면 남기지 않은 gap이 없으므로 (iii)만 가능합니다. ∎

**n에 대한 가정.**
- n ≥ 4가 필요한 곳은 두 군데입니다: α, β의 길이 n−3 ≥ 1, 그리고 비용 3이 머리·꼬리 등식과 일치한다는 것.
- 다른 곳에서는 n에 대한 가정을 쓰지 않습니다.
- 국소 카탈로그(표)도 쓰지 않습니다. 논문의 (C4) "row당 run 2개 이하"는 n = 6 전용이며, `CoarsenedInstance`의 정의에 없으므로 필요하지 않습니다.

## 5. 독립 검증 (반증 목적)

**`bridge178.py`의 구성.**
- n에 무관한 구현으로, B1–B12의 모든 명제를 route마다 **단언**합니다: run 끝점, `N₂ = T`, 계수, gap 수 = q, 보완 row의 α/β, surgery 존재와 trail 증가, charge = 구멍 수, 생략 내부, trail 예산.
- 인스턴스는 R176의 두 독립 검증기로 확인합니다: A는 직접 육각형 계산, B는 Lemma U.

| n | route 종류 | 수 | a > 0 | b > 0 | D 최대 | A, B 통과 |
|---|---|---|---|---|---|---|
| 4 | greedy 30 + 무작위 순서 30 | 60 | 있음 | 있음 | — | 60/60 |
| 5 | archive / greedy / 교란 | 60 / 10 / 40 | 0 / 5 / 28 | 0 / 8 / 37 | 2 / 94 / 226 | 전부 |
| 6 | archive / greedy / 교란 | 12 / 10 / 12 | 0 / 5 / 12 | 0 / 10 / 12 | 5 / 435 / 1536 | 전부 |
| 7 | archive / 교란 | 3 / 2 | 0 / 2 | 1 / 2 | 28 / 5911 | 전부 |

- **삼분법 분포:** (i) 25, (ii) 44, (iii) 80. 세 경우가 모두 실제로 나타납니다.
- **dictionary:** 변경 없는 archive route와, 단어 복원이 일치한 교란 route 84개에서 `r=G, q=S+1, η=h, M=O, m=k, a+b=Z+B*, t = D+(H−h)`가 모두 성립합니다.
  - B* > 0인 경우는 5개였습니다.
  - archive 전체(n ≤ 9, R174)에서 `a = Z`가 항상 성립하므로, Z > 0인 route는 이 범위에서 얻을 수 없었습니다.
  - bridge는 개별 대응을 쓰지 않습니다.
- **변형 402개를 A와 B가 모두 거부했습니다:** row 누락, 중복 row(순환류 중복), charge 주장 −1, 끝점 생략(위치 0), 불법 전이(trail 역순), trail 예산 −1, defect 변경(a+1 → row 수 불일치), trail 과다.
  - 처음 넣은 "b−1" 변형은 인스턴스가 실제로 더 작은 예산도 만족하는 경우라 **유효한 변형이 아니었고**, 제거했습니다.
- `L_c = CONST + D`는 모든 route에서 성립했고, 단어 길이 ≥ L_c도 성립했습니다.

## 6. 증명 산출물 (Lean)

`r178/lean/BridgeCore.lean`은 core Lean 4.22.0에서 Mathlib 없이 컴파일됩니다. `sorry`가 없고, `#print axioms`는 모두 `[propext, Quot.sound]`입니다(`certs/lean_BridgeCore.txt`).

| 정리 | 내용 |
|---|---|
| `cyclic_not_all_decreasing` | surgery 존재 부분(B8) |
| `capped_length_identity` | `L_c = N + HEX + ORB + n − 3 + D` (B5) |
| `holes_identity` | `(n−1)M − |S| = (n−1)m − r` (B4) |
| `trail_budget` | `p + (q−cT) + (cT−k) ≤ η+1+b` (B8) |
| `delta_core` | 인스턴스 부등식에서 `2·ORB ≤ 2(n−2) + ((n−1)(n−3)−2)·D`로 가는 단계(§7) |
| `two_c1_le_c2` | n ≥ 5에서 `2(n−2) ≤ (n−1)(n−3) − 2` |

B2, B3, B6, B7, B9–B11(기하 보조정리)과 C1의 사슬은 **형식화하지 않았습니다.** 따라서 "커널 검증된 Bridge(n)"이라고 주장하지 않습니다.

## 7. Δ(n) 하한의 유도 (Bridge(n) + C1)

1. **route 선택.** 최소 superpermutation에서 route를 뽑고 정규화합니다. 경로 공식과 정규화 보조정리(일반 n, 삼각부등식)에 의해 무게가 늘지 않으므로 `s(n) = n + 무게 ≥ L_c = CONST + D`, 즉 `Δ(n) ≥ D`입니다.
2. **인스턴스에 C1 적용.** Bridge(n)이 인스턴스를 줍니다. 각 trail은 `ModelTrail`입니다(interior, 호환, 전역 서로소가 trail 안에서도 성립).
   - trail i의 charge를 `cᵢ`라 하면 C1(n ≥ 6)에 의해 `rowsᵢ ≤ (n−2) + ((n−3)/2)cᵢ`입니다.
   - 빈 trail도 이 부등식을 만족합니다. k ≥ 1이므로 trail이 0개인 경우는 없습니다.
3. **합산.** `ORB + m − r + a ≤ (n−2)(η+1+b) + ((n−3)/2)((n−1)m − r)`.
4. **정리.** n ≥ 5이면 r의 계수 `1 − (n−3)/2 ≤ 0`이고 −a ≤ 0이므로 두 항을 버립니다.
   - `β_n := ((n−1)(n−3) − 2)/2 = (n²−4n+1)/2 ≥ n−2`입니다(n ≥ 5).
   - 따라서 `(n−2)! − (n−2) ≤ β_n·(η + b + m) ≤ β_n·D`입니다(Lean `delta_core`, `two_c1_le_c2`).
5. **결론.** 분모 `n²−4n+1 > 0`이고 D는 정수이므로 다음이 성립합니다.

> **정리 (n ≥ 6).** `s(n) ≥ n! + (n−1)! + (n−2)! + n − 3 + ⌈ 2(n−2)((n−3)! − 1) / (n² − 4n + 1) ⌉`.

- **값:** n = 6, 7, 8, 9, 10, 11, 12에서 4, 11, 44, 219, 1322, 9305, 74821입니다. Liu는 2, 8, 33, 172, 1073, 7747, 63555입니다.
- **알려진 값과의 일관성:** `Δ(6) = 5 ≥ 4`, `14 ≤ Δ(7)`, `Δ(8) ≤ 119`, `Δ(9) ≤ 720`.
- **Liu와의 비교:** 6 ≤ n ≤ 300 **모두에서 Liu보다 큽니다**(정확 정수 비교, `certs/bound_vs_liu_178.txt`).
  - 비율은 1로 수렴하며, `n(비율−1)`은 약 1.5로 보입니다. 이 점근은 수치 관찰일 뿐입니다.
  - n > 300에 대한 우월성은 주장하지 않습니다.
- **n = 7:** 외부 정리 `Δ(7) ≥ 14`가 더 강합니다. 정확한 capacity 표와 레지스트리 소거를 쓰기 때문입니다.
- **숨은 가정 점검:** 경로 공식, 정규화, `L_c ≤ L`은 모두 일반 n에서 증명됩니다. 남은 의존은 C1(R175–R177)과 Bridge(n)(이번)뿐이고, 둘 다 종이 증명입니다.

## 8. 정확 공식까지의 간격

| | 차수 | 출처 |
|---|---|---|
| 하한 (이번) | `≈ 2(n−3)!/n` | Bridge(n) + C1 |
| 상한 | `Δ(n) ≤ (n−3)!` | Egan 구성. 기록값은 n = 7: 22, n = 8: 119, n = 9: 720 |
| 정확값 | n = 6: 5. n = 7: 14 ≤ Δ ≤ 22 | Lean |

**간격은 약 n/2배이고, 정확 공식과는 거리가 멉니다.** 원인은 R174 §9에서 본 것과 같습니다.
- capacity 완화에서는 구멍 하나당 row 약 (n−3)/2개가 가능하고, 이 크기는 C1 등호 사례에서 실제로 달성됩니다.
- 실제 cover는 이보다 훨씬 적게 절약합니다.
- 인증서는 **visible 순환류만** 추적하고, 숨겨진 순환류의 덮기 조건(삼분법 (iii)의 payload)을 capacity에 쓰지 않습니다.

## 9. 다음 수학적 의무 (하나)

**덮기 조건을 반영한 capacity 보조정리(P1)를 세우고 증명하는 것입니다.**
- 대상: 삼분법 (iii)의 `ForestInstance`(생략 없음, 보이지 않는 모든 순환류가 `r − a`개의 payload block과 만남). (i), (ii)에 대해서는 대응하는 조건을 새로 정식화해야 합니다.
- 목표: row 수를 `(n−2)τ + λ·u` 꼴로 묶되, λ를 C1의 `(n−3)/2`보다 **차수적으로 작게**(목표 O(1)) 만드는 것.
- 이것이 이 틀에서 하한을 `(n−3)!` 차수 쪽으로 옮길 수 있는 유일한 경로입니다.
- 첫 단계는 n = 6, 7의 작은 u에서, payload가 붙은 단일 trail capacity를 반증 도구로 계산하는 것입니다.

## 파일

- `r178/src/bridge178.py`: n에 무관한 coarsening 구성과 모든 구조 단언, `CoarsenedInstance` 검사
- `r178/src/run178.py`: route 생성(archive, 교란, greedy), dictionary 대조, 변형 시험 → `certs/run178.json`, `run178_full.log`
- `certs/n4_178.txt`: n = 4 검증
- `r178/lean/BridgeCore.lean` → `certs/lean_BridgeCore.txt`
- `certs/bound_vs_liu_178.txt`: Liu와의 정확 비교(n ≤ 300)

BRIDGE_UNIVERSALLY_PROVED
