# Round 175 — 일반 row-run 보조정리 LL: 증명과 반례

**목표.** Round 174가 다음 문제로 남긴 보조정리 LL 하나만 다룹니다.

> **LL (R174 §9).** 외부 row 모형의 모든 trail에서, charge ≤ 1인 row만으로 된 최대 연속 구간은 row가 최대 n−2개다.

**결론 요약.**

| 진술 | 상태 |
|---|---|
| **LL, 문자 그대로** (외부 모형 = marked row 포함 `ModelTrail`) | **거짓. 모든 n ≥ 4에서 길이 n−1의 명시적 반례** (§5, 정리 B′) |
| LLᵘ: marked row를 쓰지 않는 trail로 제한 | **모든 n ≥ 4에서 증명** (정리 A). 등호 성립 |
| LL\*: 정정된 진술 "charge ≤ 1 구간은 row가 최대 n−1개" (marked 포함) | **모든 n ≥ 4에서 증명** (정리 B). 등호 성립 |
| capacity: `M(g) ≤ (n−2) + (n−1)⌊g/2⌋ + (g mod 2)` (marked). unmarked는 마지막 항 없음 | **증명** (정리 C). 모형 안에서 무조건 |
| C1 (`M(g) ≤ (n−2) + (n−3)g/2`) | LL\*에서 **따라나오지 않음**. 추가 보조정리 필요 (§6) |
| Δ(n) 하한 | `Bridge(n) ⇒ Δ(n) ≥ ⌈2(n−2)((n−3)!−1)/(n²−2n−1)⌉`. **Bridge(n)을 가정한 조건부 결과.** n=5..40 전체에서 문헌의 Liu 하한 **이하** (§7) |

**작업 범위.**
- 이번 라운드는 기호 증명이 중심입니다. 계산은 작은 반증 테스트뿐입니다(n ≤ 8 전수는 최대 7.7만 노드).
- capacity 전수, EXTREE, n=7/8 census, 대량 인증서는 하지 않았습니다.
- 작업 브랜치는 `claude/round175-row-run-lemma`입니다. n=6 production 브랜치와 인증 산출물은 건드리지 않았습니다.

## 0. 읽은 출처

- `jlebar/superperm7-ge-5898` @ `f516e19`:
  - `Superperm7/Basic.lean`: `R`, `F`, `rClass`, `fBlock`
  - `Rows.lean`: `Row`, `alpha`, `Rinv`, `Row.beta`, `Row.classMask`, `row_endpoint_table`, `length_five_row_is_loop`, `G`, `full_block_successor`
  - `RowModel.lean`: `RowCompatible`, `RowDisjoint`, `CompatibleTrail`, relabelling
  - `Coarsen.lean`: `MarkedRow`, `OmissionsInterior`, `visibleMask`, `charge`, `MarkedCompatible`, `MarkedDisjoint`, `CoarsenedInstance`, `chain_erase_loops`
  - `SearchSound.lean`: `Admissible`, `ModelTrail`, `chargeSum`
  - `CapTab.lean`, `CapTabs.lean`: n=7 capacity 표
- 우리 쪽: `r174/UNIVERSAL_STRUCTURE_REPORT.md` 정리 2·3과 §9, `r174/src/loopruns174.py`, `r174/src/trailcap174.py`
- Liu 하한 수치: `Haruhiyuki/superpermutations-preimage-chain-lower-bounds` @ `23fdbc5`, `PreimageChain/Numerics.lean`(`hunterBound`, `gamma`)

## 1. 정확한 정의 (Lean 정의를 일반 n으로 읽음)

기호 집합은 n개입니다. 순열 = 단어 `s₁…sₙ`.

| 용어 | 정의 | Lean 이름 |
|---|---|---|
| `R`, 육각형(hexagon) | `R(s₁…sₙ) = s₂…sₙs₁`. 육각형 = R-궤도(순환 단어 ⟨s₁…sₙ⟩, 원소 n개) | `R`, `rClass` |
| `F`, block | `F(s₁…sₙ) = s₂…s_{n−1}s₁sₙ`(앞 n−1개 회전, 마지막 고정). block = F-궤도(원소 n−1개) | `F`, `fBlock` |
| row | `(start p, 길이 ℓ ∈ 1..n−1)`. 상태는 `Fⁱp` (i < ℓ) | `Row` |
| α, β | `α(q) = q`의 앞 n−3글자. `β(row) = drop 3 (Rinv (F^{ℓ−1}p))`, `Rinv(s) = sₙs₁…s_{n−1}` | `alpha`, `Row.beta` |
| full row | ℓ = n−1(block 전체) | `fullRow` |
| loop row | ℓ = n−2. `β = α(start)` (R174 정리 2(b)) | `length_five_row_is_loop` |
| marked row | `(row, omitted)`. omitted 위치 i는 `0 < i`, `i+1 < ℓ` (내부) | `MarkedRow`, `OmissionsInterior` = `Admissible` |
| charge | `(n−1−ℓ) + |omitted|` | `MarkedRow.charge` |
| visible mask | omitted가 아닌 상태들의 육각형 집합 | `visibleMask` |
| 허용 전이 | 연속한 두 row x, y에 대해 `β(x) = α(y.start)` | `MarkedCompatible` |
| 반복 금지 | trail의 **모든** 두 row: block이 다르고 visible mask가 서로소 | `MarkedDisjoint` |
| trail | 모든 row가 Admissible, 연속 쌍이 호환, 모든 쌍이 서로소 | `ModelTrail` |
| trail 경계 | 첫 row와 마지막 row에 추가 조건 없음(열린 목록). `CoarsenedInstance`에서는 여러 trail이 전역적으로 서로소 | `CoarsenedInstance.disjoint` |
| 연속 구간(run) | trail의 연속 부분 목록 | — |

**charge ≤ 1인 row는 정확히 세 종류입니다.**
- full row `F` (charge 0)
- loop row `L` (charge 1)
- marked full row `Mⱼ`: 길이 n−1이고 위치 j ∈ [1, n−3] 하나를 생략 (charge 1)

길이 ≤ n−3인 row는 charge ≥ 2입니다. loop에 생략을 붙이면 charge ≥ 2입니다.

**위치 규약(이하 전부).**
- start `p = w₁…w_{n−1}s`에 대해 W(p) = ⟨w₁…w_{n−1}⟩(순환 (n−1)-단어), s = special이라 둡니다.
- 상태 `Fⁱp`의 육각형은 "W에서 s를 `wᵢ` 바로 뒤에 끼운 것"입니다(`w₀ := w_{n−1}`). 이것을 **위치 i**라 부릅니다.
- 각 row 종류가 보는 위치:
  - full은 {0..n−2}를 봅니다.
  - loop은 {0..n−3}을 봅니다. 위치 n−2(s가 `w_{n−1}` 바로 앞)를 숨깁니다.
  - `Mⱼ`는 j만 숨깁니다.
- block은 (W, s)로 결정됩니다.
- block이 다른 두 row의 공통 육각형은 s ≠ s′일 때만 가능하고, 개수는 최대 2개입니다. 두 기호를 순환 (n−2)-단어에 끼우는 방법으로 결정됩니다(§4 보조정리 4의 증명과 같은 논법).

## 2. LL을 정확히 쓰기와 추가 가정 검토

**문자 그대로의 LL.**
- charge는 Lean에서 `MarkedRow`에만 정의되어 있습니다.
- capacity 표(`capTab`, `modelTrail_length_le_capTab`)와 Bridge의 `CoarsenedInstance`도 marked row의 `ModelTrail`을 대상으로 합니다.
- 따라서 R174의 "외부 row 모형의 trail"은 marked row를 포함하는 `ModelTrail`입니다.

**R174의 검사는 다른 진술을 시험했습니다.** `r174/src/loopruns174.py`는 길이 n−1, n−2의 **생략 없는** row만 탐색했습니다. 그래서 "n=5..8에서 반례 없음"은 LLᵘ에 대한 사실입니다. 문자 그대로의 LL에 대한 사실이 아닙니다(§5).

**추가 가정이 필요한가?**

| 후보 가정 | 판정 | 근거 |
|---|---|---|
| row들이 서로 다름 / 육각형 단순성 | **불필요.** 이미 `ModelTrail`의 쌍별 조건(`MarkedDisjoint`)에 들어 있음 | 정의 |
| 시작 row 고정 | **불필요.** 동시 relabelling에 대해 모든 조건이 불변 | `compatibleTrail_map_relabel_iff` |
| 반복 위상(phase) 금지 | **불필요.** 같은 block의 두 row는 이미 금지 | `MarkedDisjoint`의 block 조건 |
| 최대 구간 vs 임의 구간 | **동치.** trail의 연속 부분 목록은 trail | 조건이 연속 쌍과 쌍별 조건뿐(`modelTrail_tail`과 같은 논법) |
| 주변 trail의 제약 | **무관.** 주변 row는 조건을 더할 뿐이고, 구간 자체가 trail이므로 상계 문제는 "모든 row의 charge ≤ 1인 trail의 최대 길이"와 같음 | 같음 |
| **marked row 허용 여부** | **결정적.** 허용하지 않으면 n−2(정리 A), 허용하면 n−1(정리 B, B′) | §4, §5 |

"합법적 walk의 정의를 조용히 강화하지 않는다"는 요구에 따라, marked row를 허용하는 원래 모형에서의 답(반례)을 주된 결론으로 둡니다. LLᵘ는 별도의 정리로 적습니다.

## 3. 전이 기하 (보조정리 1–3)

**보조정리 1 (끝점. R174 정리 2(a)(b)(c)의 재사용).**
- 길이 n−1 row(F 또는 Mⱼ, start `p = u B y z`, `B = b₁…b_{n−3}`)의 `β`는 `B`입니다.
- loop row(start `p = A x y z`, `A = a₁…a_{n−3}`)의 `β`는 `A = α(p)`입니다.
- 따라서 다음 start는 각각 `B + (u,y,z의 순열)` 또는 `A + (x,y,z의 순열)`의 여섯 후보 중 하나입니다.
- `φ(p) := B u y z`(외부 G), `ψ(p) := B u z y`로 둡니다.

**보조정리 2 (한 단계 전이표 T. 모든 n ≥ 5).** 아래는 "앞 row x와 후보 start q 사이의 block 비교와 공통 육각형"입니다. 괄호는 (x에서의 위치, q에서의 위치)입니다.

*길이 n−1 row `x`, start `p = u B y z`, W = ⟨u B y⟩, s = z:*

| 후보 q | 공통 육각형 (x 위치, q 위치) | 허용되는 q의 row 종류 |
|---|---|---|
| `B u y z = φ(p)` | 없음 (s 같고 W 다름) | 모두 |
| `B u z y = ψ(p)` | ⟨u z B y⟩ (1, n−3) | x = M₁이면 모두. 아니면 q = M_{n−3}만 |
| `B y u z` | 같은 block (⟨B y u⟩ = ⟨u B y⟩) | 없음 |
| `B y z u` | ⟨u B y z⟩ (0, 0), ⟨u z B y⟩ (1, n−2) | 없음 |
| `B z u y` | ⟨u B y z⟩ (0, n−3), ⟨u B z y⟩ (n−2, n−2) | 없음 (q가 n−3과 n−2를 동시에 숨겨야 함) |
| `B z y u` | ⟨u B z y⟩ (n−2, 0) | 없음 |

*loop row `x`, start `p = A x y z`, W = ⟨A x y⟩, s = z:*

| 후보 q | 공통 육각형 (x 위치, q 위치) | 허용되는 q의 row 종류 |
|---|---|---|
| `A x y z = p` | 같은 block | 없음 |
| `A y x z` | 없음 (s 같고 W 다름) | **모두** (long row로 나가는 유일한 일반 출구) |
| `A x z y` | ⟨A x y z⟩ (0, n−2), ⟨A x z y⟩ (n−2, 0) | loop만 |
| `A z y x` | ⟨A x z y⟩ (n−2, n−3), ⟨A z x y⟩ (n−3, n−2) | loop만 |
| `A y z x` | ⟨A x y z⟩ (0, n−3) | M_{n−3}만 |
| `A z x y` | ⟨A z x y⟩ (n−3, 0) | 없음 |

*증명.*
- 각 칸의 공통 육각형은 "q의 W에서 special을 뺀 것 = x의 W에서 q의 special을 뺀 것"이 되도록 두 기호를 끼우는 방법으로 모두 구해집니다.
- 위치는 §1의 규약으로 읽습니다. 예: `B z u y`에서 q의 W = ⟨B z u⟩, s = y이고, ⟨u B y z⟩에서 y는 `b_{n−3} = w′_{n−3}` 바로 뒤이므로 위치 n−3입니다.
- 허용 여부는 각 row 종류가 숨기는 위치(full 없음, loop n−2, Mⱼ j)로 결정됩니다. ∎
- 반증 테스트 결과:
  - `r175/src/witness175.py`가 이 표를 n = 5..10에서 기계적으로 다시 계산했습니다. 표는 n에 대해 동일합니다(`certs/witness_175.txt`).
  - `r175/src/trans175.py`도 허용 종류를 n = 5..10에서 재계산했습니다(`certs/transitions_175.json`). 이 스크립트가 출력하는 "uniform: n=5 False"는 n=5에 Mmid 종류가 없어서 생기는 이름 차이일 뿐입니다.

**R174의 "loop 뒤 후보 셋"의 분류.** 생략 없는 모형에서 살아남는 세 후보는 `A y x z`, `A x z y`, `A z y x`입니다(R174와 일치). 이들은 꼬리 세 자리의 **세 전치**입니다.
- `A y x z` (위치 n−2, n−1 교환): 진짜 자유입니다. 어떤 row 종류로도 이어질 수 있고, loop 뭉치에서 long row로 나가는 유일한 일반 출구입니다.
- `A x z y`, `A z y x`: 다음 row도 loop여야 합니다.
- marked 모형에서는 네 번째 후보 `A y z x`(3-순환)가 `M_{n−3}`으로만 추가됩니다.
- 길이 n−1 row 뒤에서는 `φ`가 유일한 일반 후계입니다. marked 모형에서는 `ψ`가 M₁ 뒤 또는 M_{n−3} 앞에서만 추가됩니다.

**보조정리 3 (loop 뭉치 ≤ 2). 겉보기 자유는 진짜가 아닙니다.**
- 연속한 loop들은 모두 같은 `α = A`를 가집니다(보조정리 1).
- start를 `A + τᵢ`(τᵢ는 세 기호의 배열)라 하면 block이 달라야 하므로 τᵢ는 서로 다릅니다.
- 두 loop의 τ가 **3-순환**만큼 다르면 충돌합니다. relabelling으로 한쪽을 `xyz`로 두면 다른 쪽은 `A y z x`(loop 불가) 또는 `A z x y`(불가)이기 때문입니다.
- 따라서 τᵢ들은 쌍마다 전치만큼 다릅니다. 즉 짝홀성이 서로 달라야 하므로 **연속 loop는 최대 2개**입니다. ∎

## 4. 일반 n 증명 (보조정리 4–7, 정리 A, 정리 B)

**불변량: 틀(frame).**
- 길이 n−1 row의 start `p = w₁…w_{n−2} a σ`에 대해 다음을 정의합니다.
  - 틀 = (순환 (n−2)-단어 `E = ⟨w₁…w_{n−2}⟩`, 쌍 `{a, σ}`)
  - **틈 번호** `e(p) := w₁` (W에서 a 바로 뒤에 오는 E의 원소)
  - special `σ`
- 이 row의 block은 "E에서 `e` 앞에 a를 끼운 W, special σ"로 결정됩니다.
- `φ(p) = w₂…w_{n−2}w₁ a σ`: 틀이 같고, 틈이 `e ↦ succ_E(e)`로 한 칸 전진하며, special이 같습니다.
- `ψ(p) = w₂…w_{n−2}w₁ σ a`: 틀이 같고, 틈이 한 칸 전진하며, special이 바뀝니다.
- **즉 long row의 전이는 틀 E를 보존하고 틈을 정확히 한 칸 전진시킵니다.** 이것이 R174 φ-사슬 논증을 marked row까지 넓히는 불변량입니다.
- 같은 틀의 loop도 같은 좌표 (틈 e, special σ)를 가지며, **위상**이 둘입니다.
  - 전방 loop: start `e … a σ`. 위치 n−2 = "σ a" 순서를 숨깁니다.
  - 후방 loop: start `F(전방 start) = succ(e) … a e σ`. "a σ" 순서를 숨깁니다.

**보조정리 4 (틀 규칙).** 같은 틀의 두 row x = (eₓ, σₓ), y = (e_y, σ_y)와, E를 따라 e에서 e′까지의 걸음 수 `d(e,e′) ∈ [1, n−3]`에 대해 다음이 성립합니다.
- (a) σₓ = σ_y이면: eₓ = e_y일 때 같은 block, 아니면 block이 다르고 서로소입니다.
- (b) σₓ ≠ σ_y이고 eₓ ≠ e_y이면: 공통 육각형은 정확히 하나, `E + aₓ@eₓ + a_y@e_y`입니다.
  - 이 육각형은 전방 long row x에서 위치 `d(eₓ, e_y)`에 있습니다.
  - loop은 위상과 관계없이 이 육각형을 항상 봅니다.
  - 따라서 **충돌하지 않을 조건**은 long row 중 하나가 자기 쪽 위치를 숨기는 것입니다(x가 `d(eₓ,e_y)`를 숨기거나, y가 `d(e_y,eₓ)`를 숨김).
  - 두 loop이면 항상 충돌합니다.
- (c) σₓ ≠ σ_y이고 eₓ = e_y이면: 공통 육각형은 "aₓa_y"와 "a_yaₓ" 두 개입니다. long row는 둘 다 봅니다(위치 0과 n−2). 전방 loop과 후방 loop은 서로 다른 하나씩을 봅니다.
  - 따라서 **같은 위상의 두 loop일 때만 서로소**이고, 나머지는 모두 충돌합니다.

*증명.*
- 공통 육각형 H는 `H∖σₓ = Wₓ`와 `H∖σ_y = W_y`를 만족해야 합니다.
- σₓ = σ_y이면 Wₓ = W_y일 때만 가능하고, 이는 틈이 같다는 뜻입니다. 이것이 (a)입니다.
- σₓ ≠ σ_y이면 `H∖{a,σ} = E`이고, aₓ는 eₓ 앞에, a_y는 e_y 앞에 있어야 합니다.
  - 틈이 다르면 H는 유일합니다. x의 start `eₓ …`에서 a_y 앞의 E-원소는 `w_{d(eₓ,e_y)}`이므로 위치는 `d(eₓ,e_y) ∈ [1, n−3]`입니다.
  - 후방 loop에서는 위치가 하나 당겨진 [0, n−4]로, 역시 보입니다. 이것이 (b)입니다.
  - 틈이 같으면 두 기호의 순서 두 가지가 나옵니다. 전방에서는 위치 0과 n−2, 후방에서는 n−2와 n−3입니다. 이것이 (c)입니다. ∎
- 반증 테스트: `framecheck175.py` part 1이 n = 5..11에서 틀 안의 모든 row 쌍(long 전부, 전방·후방 loop 전부)에 대해 예측과 실제를 비교했습니다. **불일치 0**입니다(n=11에서 19,503쌍).

**보조정리 5 (long 블록).** 모든 row의 charge가 ≤ 1인 trail에서 다음이 성립합니다.
- long row(F, Mⱼ)들은 **연속한 하나의 블록**을 이룹니다.
- 블록의 row들은 모두 **같은 틀**에 있고, 틈이 `g₀, g₀+1, …, g₀+k−1`로 연속합니다.
- 따라서 k ≤ n−2입니다.

*증명.*
- long row p 다음 long row p′ 사이에 loop들이 있을 수 있습니다. loop는 α를 보존하므로 `α(p′) = β(p)`입니다.
- p′는 p와 서로소이므로 보조정리 2에 의해 p′ ∈ {φp, ψp}입니다. 즉 틀이 같고 틈은 `succ(e(p))`입니다.
- p 바로 다음이 loop ℓ이면, 보조정리 2에 의해 ℓ의 start도 φp 또는 ψp입니다. 즉 ℓ은 같은 틈의 전방 loop입니다.
- 그러면 p′와 ℓ은 같은 틈이므로 보조정리 4(a)/(c)에 의해 같은 block이거나 충돌합니다. 따라서 long row 사이에는 loop가 없습니다.
- 틈이 같은 두 long row는 같은 block이거나 충돌합니다(4(a)(c)). 따라서 틈은 서로 달라서 k ≤ n−2입니다. ∎

**보조정리 6 (양옆 loop의 위치).** k ≥ 1이라 합니다.
- 블록 뒤 첫 loop μ₁은 **틈 `g₀+k`의 전방 loop**입니다. start가 φ(p_last) 또는 ψ(p_last)이기 때문입니다(보조정리 2).
- 블록 앞 마지막 loop λ는 **틈 `g₀−1`의 후방 loop**입니다.
  - loop에서 long row로 가는 길은 `A x y z → A y x z`(교환 경로) 또는 `→ A y z x`(3-순환 경로, `p_first = M_{n−3}`)뿐입니다(보조정리 2).
  - 두 경우 모두 `p_first`의 틀은 `E = ⟨A y⟩`, 틈은 `a₁`입니다.
  - λ의 W = ⟨A x y⟩는 "E에서 y 앞(= `pred(a₁)` 앞)에 x"이고, special은 z입니다.
  - λ의 start `A x y z = F(y A x z)`이므로 후방 위상입니다. ∎

**보조정리 7 (둘째 loop, k ≥ 1).**
- 블록 앞 뭉치가 loop 2개이면 첫 loop λ′는 **λ와 같은 틈, 반대 special, 같은(후방) 위상**의 loop입니다.
- 블록 뒤 뭉치가 2개이면 μ₂는 **μ₁과 같은 틈, 반대 special, 같은(전방) 위상**의 loop입니다.

*증명.* 연속 loop는 꼬리 전치로 이어집니다(보조정리 2, 3). λ = `A x y z`에 대해 λ′ ∈ {`A y x z`, `A x z y`, `A z y x`}입니다.
- `A y x z`:
  - 교환 경로에서는 p_first와 같은 block입니다.
  - 3-순환 경로에서는 ⟨A y x z⟩ (λ′ 위치 0, p_first 위치 n−2)에서 충돌합니다.
- `A x z y`: ⟨A y x z⟩에서 충돌합니다. 교환 경로는 (n−3, 0), 3-순환 경로는 (n−3, n−2)입니다.
- `A z y x`: W = ⟨A z y⟩ = "E에서 y 앞에 z", special x입니다. 이것이 주장한 짝입니다.

μ₁ = `A x y z`(틀 ⟨A x⟩, 틈 a₁)에 대해 μ₂ ∈ {`A x z y`, `A y x z`, `A z y x`}입니다. `p_last = x A y z`(φ 경로) 또는 `x A z y`(ψ 경로)입니다.
- `A x z y`: 주장한 짝입니다.
- `A y x z`:
  - φ 경로에서는 p_last와 같은 block입니다.
  - ψ 경로에서는 ⟨A z y x⟩ (n−3, 0)에서 충돌합니다.
- `A z y x`:
  - φ 경로에서는 ⟨A z y x⟩ (0, n−2)에서 충돌합니다.
  - ψ 경로에서는 ⟨A z y x⟩ (0, 0)에서 충돌합니다.

여기 나온 모든 위치는 loop가 보는 {0..n−3}과 charge ≤ 1 long row가 반드시 보는 위치(0, n−2)에 속하므로 충돌은 확정입니다. ∎
- 반증 테스트:
  - `witness175.py`의 Lemma 7 표가 n = 5..10에서 동일합니다.
  - `framecheck175.py` part 2가 n = 5..8의 **모든** charge ≤ 1 trail(83,387개)에서 보조정리 5–7의 결론을 확인했습니다. 위반 0입니다.

**정리 A (LLᵘ, 모든 n ≥ 4).** marked row가 없는 trail에서, charge ≤ 1인 연속 구간은 **최대 n−2개**의 row입니다. 등호는 full row의 φ-사슬 `p, φp, …, φ^{n−3}p`에서 성립합니다(R174 정리 2(e)).

*증명 (n ≥ 5).*
- k = 0이면 구간은 loop 뭉치 하나이므로 ≤ 2 ≤ n−2입니다(보조정리 3).
- k ≥ 1이면 구간은 `L^{c₀} (long)^k L^{c₁}`, c₀, c₁ ≤ 2입니다(보조정리 3, 5).
- 생략이 없으므로 보조정리 4(b)에 의해 special이 다른 두 long row는 충돌합니다. 따라서 모든 long row의 special은 σ 하나입니다.
- λ, μ₁도 4(b)에 의해 special이 σ여야 합니다.
- 보조정리 7의 짝 loop는 special이 σ가 아니므로 long row와 충돌합니다. 따라서 c₀, c₁ ≤ 1입니다.
- 틈 점유를 봅니다.
  - long row들은 서로 다른 k개의 틈에 있습니다.
  - λ, μ₁은 long row와 같은 틈일 수 없습니다(4(a)(c)).
  - λ(후방)와 μ₁(전방)은 서로 같은 틈일 수 없습니다. special이 같으면 같은 block이고, 다르면 위상이 달라 충돌합니다(4(c)).
  - 따라서 `k + c₀ + c₁ ≤ n−2`입니다. ∎
- n = 4는 전수 확인했습니다(최대 2).

**정리 B (LL\*, 모든 n ≥ 4).** marked row를 허용한 원래 모형에서, charge ≤ 1인 연속 구간은 **최대 n−1개**의 row입니다.

*증명 (n ≥ 5).*
- k = 0이면 ≤ 2입니다.
- k ≥ 1이면 정리 A의 틈 점유 논증은 special과 무관하게 성립하므로 `k + [c₀≥1] + [c₁≥1] ≤ n−2`입니다. 따라서 `row 수 ≤ n−2 + [c₀=2] + [c₁=2]`입니다.
- c₀ = c₁ = 2라고 가정합니다. 보조정리 7에 의해 틈 `g₀−1`에는 두 special을 모두 가진 후방 loop 짝이 있습니다.
  - μ₁의 틈이 이것과 다르면, 4(b)에 의해 special이 다른 쪽과 충돌합니다.
  - μ₁의 틈이 같으면(k = n−3) special이 같은 쪽과 같은 block입니다.
  - 모순입니다. 따라서 row 수 ≤ n−1입니다. ∎
- n = 4는 전수 확인했습니다(최대 3).

**전수 교차 검증 (`llsearch175.py`, 항등 start에서 WLOG).**

| n | unmarked 최대 | marked 최대 | marked 탐색 노드 |
|---|---|---|---|
| 4 | 2 | 3 | 23 |
| 5 | 3 | 4 | 112 |
| 6 | 4 | 5 | 655 |
| 7 | 5 | 6 | 5,893 |
| 8 | 6 | 7 | 76,727 |

n−1을 이루는 모양은 n = 5..8에서 정확히 두 가지입니다: `L L M_{n−3} … M₁`와 그 역순 `M_{n−3} … M₁ L L`.

## 5. 반례 (정리 B′: 문자 그대로의 LL은 모든 n ≥ 4에서 거짓)

`A = c₁…c_{n−3}`, `x = c_{n−2}`, `y = c_{n−1}`, `z = cₙ`으로 두고, 다음 n−1개의 row를 봅니다. 모두 charge 1입니다.

1. loop, start `A x y z`
2. loop, start `A z y x`
3. k = 0..n−4에 대해: 길이 n−1, start `qₖ = φᵏ(A y x z)`, **위치 n−3−k 생략** (`M_{n−3−k}`)

*증명.*
- **호환.**
  - loop 뒤 다음 start는 α = A를 가져야 하고, 2번과 `q₀`는 그렇습니다.
  - 길이 n−1 row 뒤는 φ입니다(보조정리 1).
- **틀 좌표.**
  - `q₀…q_{n−4}`는 틀 E = ⟨A y⟩, 쌍 {x, z}, special z, 틈 `a₁, a₂, …, a_{n−3}`(연속)입니다.
  - 1번은 "E에서 y 앞에 x, special z"입니다. 즉 틈 y(= `pred a₁`), 같은 special이므로 4(a)에 의해 모든 `qₖ`와 서로소입니다.
  - `qₖ`끼리도 4(a)에 의해 서로소입니다.
- 2번의 W는 ⟨A z y⟩, special x입니다. 이것은 "틈 y, special x"의 후방 loop이고, 1번과 같은 틈, 반대 special, 같은 위상이므로 4(c)에 의해 서로소입니다.
- 2번과 `qₖ`: special이 다르고 틈이 다르므로 공통 육각형은 하나이고, `qₖ`에서의 위치는 `d(e(qₖ), y) = n−3−k`입니다. **정확히 그 위치를 생략**했으므로 서로소입니다(4(b)).
- block은 모두 다릅니다(틈 또는 special이 다름). ∎

**검증.**
- `r175/src/cex175.py`가 n = 4..14에 대해 이 walk를 만들어 정의에서 직접 다시 검사했습니다. `verify`는 탐색 표를 쓰지 않는 독립 구현입니다.
- 모든 n에서 통과했습니다(`certs/counterexample_175.json`).
- 음성 대조군: 생략을 지우거나, 한 칸 밀거나, 첫 mark를 지운 변형은 모두 "class" 충돌로 **거부**됩니다(n = 5, 7, 9).

n = 7의 예(기호 a..g):

`abcdefg:loop  abcdgfe:loop  abcdfeg:mark4  bcdfaeg:mark3  cdfabeg:mark2  dfabceg:mark1`

**뜻.**
- R174의 LL은 **charge 1짜리 marked row를 빠뜨린 모형에서만 참**이었습니다.
- 반례의 모든 row는 charge 1입니다(총 charge n−1). 따라서 capacity 표와 모순되지 않습니다. 예: n=7 `capTab[6] = 16 ≥ 6`.

## 6. capacity에 대한 결과

**정리 C (단일 trail capacity, 모든 n ≥ 4, 모형 안에서 무조건).** total charge ≤ g인 모든 `ModelTrail`의 row 수는 다음을 넘지 않습니다.

- marked 포함: `(n−2) + (n−1)⌊g/2⌋ + (g mod 2)`
- 생략 없는 trail: `(n−2) + (n−1)⌊g/2⌋`

*증명.*
- charge ≥ 2인 row h개(2h ≤ g)가 trail을 charge ≤ 1인 구간 최대 h+1개로 나눕니다.
- 구간 i의 charge를 cᵢ라 하면, row 수 ℓᵢ는 다음과 같습니다.
  - cᵢ = 0이면 ℓᵢ ≤ n−2 (R174 정리 2(e))
  - 아니면 ℓᵢ ≤ n−1 (정리 B)
- `Σcᵢ + 2h ≤ g`이므로 `row ≤ (h+1)(n−2) + h + min(h+1, g−2h)`입니다. 이는 h에 대해 증가하고, `h = ⌊g/2⌋`에서 위 식이 됩니다.
- unmarked의 경우는 정리 A로 ℓᵢ ≤ n−2입니다. ∎

**기존 기호 상계와의 비교.**

| 상계 | 기울기(g당) | 상태 |
|---|---|---|
| R174 정리 2(f): `(n−2) + (n−1)g` | n−1 | 증명(R174) |
| **정리 C** | **(n−1)/2** | **증명(이번)** |
| C1: `(n−2) + (n−3)g/2` | (n−3)/2 | 가설 |

알려진 값과 대조했습니다.
- R174의 정확한 unmarked 표(n=5..8)와 외부의 n=7 marked 인증 상계 `capTab`(g ≤ 36) 모두 정리 C 이하입니다.
- 예: n=7에서 `M(2) = 9 ≤ 11`, `capTab[36] = 66 ≤ 113`.

**C1은 따라나오지 않습니다.**
- g = 2에서 정리 C는 `2n−3`을 주지만, 정확한 값은 `M_n(2) = 2n−5`입니다(n=5..8. R174 표, n=7은 외부 표와 일치).
- 차이 2는 "charge 2짜리 row 하나가 양옆 구간에서 row 2개를 빼앗는다"는 상호작용에서 옵니다. LL\*는 구간 하나만 보므로 이 효과를 볼 수 없습니다.
- C1에는 다음 두 추가 보조정리가 필요합니다(둘 다 **미증명**).
  - **(S1) 분리자 보조정리:** charge 2 row x와 그 양옆의 최대 charge ≤ 1 구간 R, R′에 대해 `|R| + |R′| ≤ 2n−6`. g = 2일 때 `M_n(2) = 2n−5`와 동치입니다.
  - **(S2) 상각(amortization):** S1의 손실이 여러 분리자에 걸쳐 중복 없이 합쳐진다는 것.

## 7. Δ(n)에 대한 함의 (Bridge(n) 구분)

R174 정리 3은 다음을 말합니다.
- 가정: Bridge(n)(외부 `coarsen_bridge`의 일반 n판)이 성립하고, 모든 g에서 `M(g) ≤ (n−2) + αg`.
- 결론: `D ≥ (n−2)((n−3)!−1)/max(n−2, α(n−1)−1)`.

정리 C의 두 식은 n ≥ 3에서 `≤ (n−2) + ((n−1)/2)g`이므로 **α = (n−1)/2가 무조건 성립**합니다.
- 홀수 g에서는 `(n−1)(g−1)/2 + 1 ≤ (n−1)g/2`입니다.
- Bridge가 쓰는 `CoarsenedInstance`는 marked row를 포함하므로 marked 판이 필요하고, 정리 C가 그것을 줍니다.

> **따름정리 (조건부).** `Bridge(n) ⇒ Δ(n) ≥ ⌈2(n−2)((n−3)!−1) / (n²−2n−1)⌉`.
>
> - **Bridge(n)을 가정합니다.** 일반 n에 대해 증명된 적이 없으므로 이것은 **무조건적 일반 하한이 아닙니다.**
> - R174에서는 같은 식이 "LL 가정 시"였습니다. 이번에 capacity 쪽 가정이 제거되어, 남은 가정은 Bridge(n) 하나입니다.

**무조건 하한과의 비교** (`certs/bound_comparison_175.txt`. Liu = `hunterBound + Γ − CONST`, Lean 정의를 옮김):

| n | Liu (무조건, 문헌) | 위 따름정리 (Bridge 가정) | 비율 |
|---|---|---|---|
| 7 | 8 | 7 | 0.875 |
| 8 | 33 | 31 | 0.939 |
| 9 | 172 | 163 | 0.948 |
| 10 | 1073 | 1021 | 0.952 |
| 14 | 5,942,830 | 5,736,546 | 0.965 |
| 20 | ≈3.656·10¹³ | ≈3.567·10¹³ | 0.976 |
| 40 | ≈6.973·10⁴¹ | ≈6.886·10⁴¹ | 0.988 |

**이번 결과는 Bridge(n)을 가정해도 Liu보다 약합니다**(n = 5..40 전부. 비율은 아래에서 1로 수렴). 가장 강한 무조건 일반 하한은 여전히 **Liu**입니다. C1 수준의 기울기 (n−3)/2가 있으면 Bridge 하에서 Liu를 넘습니다(n=40에서 비율 1.04).

## 8. 남은 장애물

1. **Bridge(n):** reduction 전체를 n에 대한 정리로 증명하는 것. 이것이 없으면 capacity 쪽의 어떤 결과도 Δ(n)의 무조건 하한이 되지 않습니다.
2. **capacity 기울기:** 정리 C의 (n−1)/2로는 Bridge를 가정해도 Liu를 넘지 못합니다. (n−3)/2 근처(C1)가 필요합니다. 정확한 첫 관문은 **분리자 보조정리 S1** `M_n(2) = 2n−5` (모든 n)입니다.
   - 이번의 틀 좌표(보조정리 4)는 charge 2 row(길이 n−3 row, 생략 있는 loop, 생략 2개인 full row)에도 그대로 적용됩니다.
   - 따라서 S1은 정리 A/B와 같은 방식의 틈 점유 논증으로 공격할 수 있는 형태입니다.
3. **R174 §9의 근본 격차**(capacity 완화는 궤도당 ≈ n/2개의 무게-4 이음매 절약을 허용하지만 실제는 ≈ 1)는 그대로입니다. 정리 C는 그 완화 안에서의 개선일 뿐입니다.

## 9. R174 진술의 정정

| R174 진술 | 정정 |
|---|---|
| "LL: n=5..8 반례 없음" | **생략 없는 row만 탐색한 결과입니다.** marked row를 포함하면 모든 n ≥ 4에서 반례가 있습니다(§5). LLᵘ는 이번에 모든 n에서 증명했습니다(정리 A). |
| "LL이 증명되면 `M_n(g) ≤ (n−2) + (n−1)⌊g/2⌋`" | unmarked에서는 정확합니다(정리 C). marked 모형에서는 `+ (g mod 2)`가 붙지만 기울기는 같고, **이제 증명되었습니다.** |
| "loop 뒤 후보 셋" | 맞습니다(생략 없는 모형). marked 모형에서는 `A y z x → M_{n−3}`이 추가됩니다. 길이 n−1 row 뒤에는 `ψ`가 추가됩니다(보조정리 2). |
| 정리 3 표의 "LL 가정 시" 열 | 값은 그대로이고, 이제 **Bridge(n)만 가정**합니다. |

## 파일

- `r175/src/llsearch175.py`: LL 전수 탐색(unmarked, marked)과 독립 검증기 `verify` → `certs/ll_{unmarked,marked}_n{4..8}.json`
- `r175/src/trans175.py`: 보조정리 2의 허용 표 → `certs/transitions_175.json`
- `r175/src/witness175.py`: 보조정리 2와 7의 공통 육각형과 위치(기호 표기, n에 대해 동일) → `certs/witness_175.txt`
- `r175/src/framecheck175.py`: 보조정리 4 규칙(n=5..11)과 보조정리 5–7의 구조(n=5..8의 모든 trail) → `certs/framecheck_175.txt`
- `r175/src/cex175.py`: §5 반례 생성과 검증(n=4..14) → `certs/counterexample_175.json`
- `r175/src/bounds175.py`: §7 하한 비교 → `certs/bound_comparison_175.txt`

LL_COUNTEREXAMPLE_FOUND
