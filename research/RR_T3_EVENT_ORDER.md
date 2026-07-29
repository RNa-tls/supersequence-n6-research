# T3의 정확한 명제와 구조적 지위 (라운드 31 Part E)

## 1. T3 정의 (문서 첫머리 고정)

> **T3**: \(\ell=4\) same-component Target A word에서, hub completer
> \(C\) **직후의 macro-edge가 \(R_2\)** 다 — 즉 tail \(T_\ell\)의 길이가
> 0이다.

## 2. T3은 국소 legality 명제가 **아니다**

post-\(C\) endpoint에서 네 joint이 **전부 legal**하고 그중 셋은 R이
아니다(라운드29 §6, 라운드31 Part D §2에서 재확인):

| joint | kind | R? |
|---|---|:---:|
| `w2:10` | Z2 | 아니오 |
| `w3:120` | **R** | **예** |
| `w3:201` | Z3 | 아니오 |
| `w3:210` | Z3 | 아니오 |

> 따라서 T3은 **local legality 명제가 아니라 RR event-order /
> terminal-compatibility 명제**다. "다음 edge가 R2여야 한다"를 강제하는
> 것은 legality가 아니라 word 전체의 R 개수·순서 제약이다.

## 3. \(C\) 직후 non-R edge를 고르면 어떻게 되는가 (§23)

| 질문 | 답 |
|---|---|
| Target A가 지연되는가 | **예** — \(R_2\)가 더 뒤로 밀린다 |
| R 예산이 남는가 | **예** — 그 edge는 R이 아니므로 \(N\)이 늘지 않는다 |
| later \(R_2\) 경계가 가능한가 | **미판정** — Part D의 탐색이 depth 9까지 찾지 못했으나 frontier 미소진 |
| capacity bound에 어떤 영향 | \(\Phi\)는 어차피 그 edge에서 0이 되고, non-R edge가 Z3면 \(O\)를 1 늘려 \(O_{\mathrm{cap}}\)이 줄어든다 — **capacity가 나빠진다** |

**마지막 항목이 T3의 유일한 실질적 단서**다: \(C\) 직후에 Z3를 고르면
\(O\)가 늘어 \(O_{\mathrm{cap}}\)이 1 줄고, capacity bound
\(B\le5(O_{\mathrm{cap}}+R_{\mathrm{cap}})+4\)의 우변이 5 줄어든다.
그런데 좌변 \(B\)도 1 줄어든다. 순변화는 \(-4\) — **capacity가
확실히 나빠진다.**

> **T3의 부분 논증 (safe capacity bound)**: \(C\) 직후에 \(R_2\)가
> 아닌 Z3 edge를 고르면 그 상태의 capacity margin이 4 줄어든다.
> margin이 4 이하인 경계에서는 그런 선택이 **Target B를 불가능하게
> 만든다.**

다만 이것은 **Target B에 대한 논증**이지 Target A에 대한 논증이 **아니다**
— \(R_2\) 경계 자체는 여전히 도달 가능할 수 있다. 따라서 T3을
capacity에서 유도하려면 "Target A word는 Target B로 확장돼야 한다"는
추가 전제가 필요한데, 그것은 **참이 아니다**(라운드30이 여섯 경계에서
Target B 불가능을 증명했으나 그 경계들은 여전히 Target A였다).

## 4. 판정

| 질문 | 답 |
|---|---|
| T3이 local legality에서 나오는가 | **아니오 — 반증됨** |
| T3이 RR two-R 제약에서 나오는가 | **미완료** — Part D의 R-free prefix가 두 R을 \(C\) 이후에 두는 것을 배제하지 못한다 |
| T3이 Target B capacity에서 나오는가 | **아니오** — Target A는 Target B를 요구하지 않는다 |
| T3의 현재 등급 | **exact observation (15/15)** |

**T3은 여전히 미완료**이며, 이번 라운드는 그것이 **어디서 나올 수
없는지**를 세 가지 확정했다. 그 자체가 다음 시도의 범위를 좁힌다.
