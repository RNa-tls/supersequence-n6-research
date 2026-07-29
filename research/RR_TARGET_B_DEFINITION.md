# Target B 정의와 안전 prune (라운드 28 §13, §15)

## 1. Target A / B / C — 흐리지 않는다

| | 내용 | 이번 라운드 |
|---|---|---|
| **Target A** | same-component \(R_2\) 경계 도달 (라운드27 정의 그대로) | **달성 — exact witness 6개** |
| **Target B** | 그 경계 이후 admissible terminal continuation | **정의만 고정. 탐색 없음** |
| **Target C** | 전체 NR6 completion (720 permutation 전부) | **손대지 않음** |

> **Target A 성공은 NR6 completion과 아무 관계가 없다.** Target B는
> Target C보다 **엄격히 약하고**, Target A는 Target B보다 엄격히 약하다.

## 2. Target B 정의 (고정)

> same-component \(R_2\) 경계 상태 \(S\)에서 출발하는 legal macro-edge
> 열로서 다음을 **모두** 만족하는 것:
>
> 1. permutation을 재방문하지 않는다,
> 2. 다시 abandonment하지 않는다(\(F_{\mathrm{def}}\)는 1 유지)이고
>    hub defect를 추가하지 않는다(\(H=0\) 유지),
> 3. **R 사건을 추가하지 않는다**(\(N_{\mathrm{def}}=2\) 유지 — RR word는
>    \(R_2\)에서 이미 닫혔다),
> 4. 모든 상태가 `area_a_prune_reason`을 통과한다,
> 5. **pure-rotation suffix를 허용하는 상태**에서 끝난다 — 즉 Area A가
>    이미 사용하는 의미의 legal terminal boundary.

명시 제약:

| 항목 | 값 |
|---|---|
| \(F_{\mathrm{def}}\) | 1 (고정) |
| \(H\) | 0 (고정) |
| \(N_{\mathrm{def}}\) | 2 (고정) |
| `TARGET_P` | 121 |
| `TARGET_O` | 25 |
| `TARGET_D` | 4 |
| \(\Phi\) | \(\ge0\) 유지 |
| 허용 macro-edge 수 | \(\Phi\) slab이 결정 (상한 별도 고정 안 함) |
| final endpoint | pure-rotation suffix 허용 상태 |

**\(F_{\mathrm{def}}\)와 \(F_{\mathrm{sym}}\)은 다른 양이다**(라운드27
§8). 위 제약은 전부 \(F_{\mathrm{def}}\)에 대한 것이다;
\(F_{\mathrm{sym}}\)(fresh opening 사건 수)은 \(O\le\)`TARGET_O`를 통해서만
제한된다.

## 3. 안전 prune 준비 (§15) — 손증명 등급별

이번 라운드에서는 **Target B 대형 DFS를 돌리지 않는다.** 아래는 향후
targeted search에 쓸 수 있는 prune만 미리 증명해 둔 것이다.

### 손증명 완료 (즉시 사용 가능)

| prune | 명제 | 증명 |
|---|---|---|
| **repeated permutation** | `exact.extend`가 `None`을 반환 | walk는 각 permutation을 최대 한 번 방문한다(모델 정의). 그런 후계 상태는 존재하지 않는다 |
| **\(F_{\mathrm{def}}\) budget** | 두 번째 abandonment는 \(F_{\mathrm{def}}=2>1\) | `area_a_prune_reason`이 `F_exceeded`; 단조 증가라 회복 불가 |
| **N/H budget** | \(N_{\mathrm{def}}=2,\ H=0\)이고 `TARGET_BUDGET`\(=N+H=3\) | 둘 다 단조 비감소이므로 초과는 회복 불가 |
| **\(\Phi<0\)** | \(\Phi=5+6(\text{TARGET\_P}-P)-(720-\text{visited})\ge0\) | Area A가 이미 쓰는 slab shortfall functional; 음수는 남은 permutation을 slab 안에서 덮을 수 없음을 뜻한다 |
| **unavailable required phase** | 필요한 (orbit, phase) port가 이미 방문됨 | `orbit_masks`가 방문 port를 기록하며, 방문된 port는 재진입 불가 |

### 손증명 후보 — 아직 미완료

| prune | 부족한 것 |
|---|---|
| **component merge deficit** | 각 macro-edge가 component 쌍을 최대 하나 병합한다는 것은 참이나, **남은 사건 수의 상한**이 아직 없다 |
| **no legal terminal endpoint** | terminal 특성화가 없다 |
| **impossible remaining cost** | 남은 비용의 비자명한 하한이 없다 |

**경험적 prune은 하나도 준비하지 않았다.** 위 다섯 개만이 exact search에
사용 가능하다.

## 4. 왜 지금 탐색하지 않는가

Target B 탐색은 \(\Phi\) slab 전체를 걸어야 하므로 라운드27의 targeted
Target A 탐색보다 훨씬 크다. 그리고 손증명된 prune 다섯 개 중
**\(\Phi<0\) 외에는 깊이에 따라 강해지는 것이 없다** — 즉 지금
탐색하면 라운드27의 22개 INCOMPLETE와 같은 결과를 훨씬 큰 비용으로
반복할 가능성이 높다.

먼저 필요한 것은 위 "손증명 후보" 셋 중 최소 하나, 특히 **남은 비용의
하한**이다. 그것 없이 시작하면 node cap에 부딪히고, node cap은
불가능성 증거가 **아니다**.

**등급**: Target B 정의 = **손증명**(기존 술어 재사용), prune 다섯 개 =
**손증명**, 나머지 셋 = **미완료**, Target B 자체 = **미완료**.
