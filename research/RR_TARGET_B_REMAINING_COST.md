# Target B remaining cost — 안전 하한과 정확한 packing 항등식 (라운드 29 §13–19)

산출: `outputs/rr_target_b_demand_vectors.json`,
`outputs/rr_target_b_lower_bounds.json`. **탐색 없음.**

## 1. Demand vector (§13)

\[
D_{\mathrm{rem}}=(U_{\mathrm{perm}},U_{\mathrm{orbit}},U_{\mathrm{phase}},
M_{\mathrm{component}},E_{\mathrm{endpoint}},R_{\mathrm{suffix}})
\]

| 좌표 | 계산 | Class I (w0,1) | Class II (w2–5) |
|---|---|---:|---:|
| \(U_{\mathrm{perm}}\) | \(720-\text{visited}\) | **665** | **647** |
| \(B\) (남은 pass start) | `TARGET_P`\(-P\) | **110** | **107** |
| \(O\) 여유 | `TARGET_O`\(-O\) | 19 | 17 |
| \(M_{\mathrm{component}}\) | 현재 component 수 | (JSON) | (JSON) |
| \(E_{\mathrm{endpoint}}\) | pure-rotation suffix 허용 상태 | — | — |
| \(R_{\mathrm{suffix}}\) | 5 | 5 | 5 |

## 2. 정확한 packing 항등식 — \(\Phi=0\)의 진짜 의미

\(\Phi=5+6(\text{TARGET\_P}-P)-(720-\text{visited})=0\)은 정확히

\[
\boxed{\;U_{\mathrm{perm}} = 6B+5\;}
\]

| # | \(U_{\mathrm{perm}}\) | \(B\) | \(6B+5\) | 일치 |
|---:|---:|---:|---:|:---:|
| 0,1 | 665 | 110 | **665** | ✓ |
| 2–5 | 647 | 107 | **647** | ✓ |

> **\(\Phi=0\)은 "여유가 적다"가 아니라 "여유가 정확히 0"이다.**
> Target B continuation은 **완전 packing**이어야 한다:
> 남은 \(B\)개의 macro-edge가 **전부 \(\ell=5\)**이고 **각각 미방문
> permutation 6개**를 덮으며(= hexagon 하나씩 완성), 마지막에
> **정확히 5회의 순수 rotation**으로 끝나고, 남는 permutation이 **없어야**
> 한다.

한 번이라도 이미 방문한 permutation을 지나거나 \(\ell<5\)를 쓰면
\(\Phi<0\)이 되어 즉시 prune된다.

## 3. 안전 하한 (§14–17)

| 하한 | 값 | 유도 | 등급 |
|---|---:|---|---|
| **permutation coverage** | \(\lceil (U-5)/6\rceil\) = 110 / 107 | \(\Phi=0\)에서 모든 macro-edge는 \(\ell=5\)(§12 정리)이고 6개를 덮으며, 마지막 suffix가 최대 5개 | **safe lower bound (손증명)** |
| orbit/phase coverage | — | joint target이 이미 열린 orbit에 착지할 수 있으므로 phase 수요만으로 비자명한 안전 하한이 **나오지 않는다** | **미완료** |
| component merge | — | Target B가 요구하는 **최종** component 구조가 특성화돼 있지 않아 deficit을 계산할 수 없다 | **미완료** |

\[
C_{\min} = \max(110,\ -,\ -) = 110 \quad(\text{Class I}),\qquad
107 \quad(\text{Class II})
\]

\[
\text{slack} = B - C_{\min} = \mathbf{0}\quad\text{(양쪽 모두)}
\]

**주의(§15의 경고)**: 여기서 세는 것은 **macro-edge 수**이지
length/cost가 아니다. \(B\)는 남은 pass start 수 \(=\)`TARGET_P`\(-P\)이며,
macro-edge 하나가 pass start 하나를 소비한다.

## 4. Pure-rotation suffix (§18)

여섯 post-\(R_2\) 상태 **전부**에서 지금 당장 5회의 rotation이 가능하다
(`rotations_available_now = 5`). 즉 **suffix를 여기서 바로 붙일 수는
있으나**, 그러면 \(U_{\mathrm{perm}}\)이 660/642개 남아 Target B가
아니다.

> suffix 불가능성으로 상태를 제거하는 lemma는 **이번 라운드에
> 만들지 못했다** — 여섯 전부 통과하므로 판별력이 없다. **미완료.**

## 5. 정적 모순 판정 (§19)

| # | 판정 | slack |
|---:|---|---:|
| 0–5 | **lower bound incomplete** (permutation coverage 하한만 가용) | 0 |

- **즉시 모순: 없음.** 여섯 전부.
- 그러나 **"no contradiction"이 아니라 "lower bound incomplete"** 로
  분류한다 — 세 하한 중 둘이 미완료이므로, 모순이 없다고 단정할 근거가
  없다.
- **모순을 억지로 만들지 않았다.** slack이 정확히 0이라는 것은
  모순이 **아니며**, 동시에 실현 가능성의 증거도 **아니다**.

## 6. 다음에 필요한 것

slack이 0이므로 **아주 약한 추가 하한 하나만 있어도 모순이 된다.**
가장 유망한 후보:

> 남은 110개 hexagon 중 **어떤 hexagon도 두 번 진입할 수 없고**, 각
> macro-edge의 joint이 진입 가능한 hexagon은 조인트 4종에 의해 제한된다.
> 따라서 hexagon 그래프에서 **Hamiltonian 경로가 존재해야** 한다.
> 그 그래프의 차수·연결성에서 나오는 임의의 장애물이 즉시 모순을 준다.

이것이 `RR_TARGET_B_TRANSITIONS.md` §3의 재서술이 실질적으로 중요한
이유다. 다만 이번 라운드에서는 그 그래프를 구성하지 않았다 — **미완료**.

**증명 등급**: packing 항등식 **손증명**, permutation coverage 하한
**safe lower bound**, 나머지 두 하한 **미완료**, 정적 모순 판정
**lower bound incomplete**.
