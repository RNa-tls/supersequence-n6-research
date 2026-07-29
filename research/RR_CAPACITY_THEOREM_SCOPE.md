# Capacity 정리의 적용 범위와 dependency graph (라운드 31 §24)

## 1. 정리와 그 정확한 전제

> **Capacity theorem (손증명)**: \(\Phi=0\)인 Target A 경계 상태에서
> Target B continuation이 존재하면
> \[
> B\;\le\;5\bigl(O_{\mathrm{cap}}+R_{\mathrm{cap}}\bigr)+4 .
> \]

**필요한 전제**(최소):

| 전제 | 필요? |
|---|---|
| \(\Phi=0\) | **필수** — 여기서 모든 후속 macro-edge의 \(\ell=5\)가 나온다 |
| \(\ell=5\) 합성 생성원 구조 | **필수** |
| \(\ell=4\) 분기 | **불필요** — \(\ell=0\) 경계에도 적용된다 |
| same-component | **불필요** |
| chaining | **불필요** |
| terminal normal form (T1~T9) | **불필요** |

닫힌 형태: \(D=5O-P\)라 두면 모순 조건은
\(D>13-5R_{\mathrm{cap}}\)이다. **fresh orbit을 많이 열수록 위험**하다.

## 2. 적용 결과 — 전체 corpus

| class | boundary state | CAPACITY_IMPOSSIBLE | 생존 |
|---|---:|---:|---:|
| long (\(P_{\mathrm{core}}=7,10\)) | 6 | **6** | 0 |
| short (\(P_{\mathrm{core}}=2,4,6\)) | 12 | **3** | 9 |
| **합계** | **18** | **9** | **9** |

정련된 phase/port bound가 여기서 **1개 더** 제거한다 →
**최종 생존 8개** (전부 short, \(\ell=0\) 2개 + \(\ell=4\) 6개).

## 3. Dependency graph 갱신

### Closed

| 항목 | 근거 |
|---|---|
| long six의 Target B 불가능 | **손증명** (라운드30) |
| capacity theorem | **손증명** |
| short 3개의 Target B 불가능 | **safe capacity bound** |
| refined bound로 1개 추가 제거 | **safe capacity bound** |
| `EEEE`가 유일한 사용 가능 saturating block | **손증명** |
| CH2-B (orbit 1 first-opener) | **반증됨** (라운드30) |
| T3이 local legality에서 나온다 | **반증됨** |

### Open

| 항목 | 상태 |
|---|---|
| short survivor 8개의 Target B | **미완료** |
| refined phase capacity의 추가 강화 | **미완료** (component-compatible capacity 미특성화) |
| CH2 chaining | **미완료** — R-free prefix가 Target A로 확장되는지 미판정 (depth ≤9까지 0개, frontier 미소진) |
| T3 | **미완료** — 세 가지 유도 경로가 배제됨 |
| Target C | 손대지 않음 |

### Unaffected

| 항목 | 상태 |
|---|---|
| U/J branch | 변동 없음 |
| N=0 search/checkpoint | **건드리지 않음** |
| NR6 lower bound (\(L_6\ge872\), \(L_6\ge867\)) | **영향 없음** |

## 4. NR6에 대한 정직한 진술

Target B가 18개 경계 중 10개에서 불가능하다는 것은 **그 경계들이 slab
continuation을 갖지 않는다**는 뜻이다. 이는

- Target C(전체 NR6 completion)와 **논리적으로 무관**하고,
- \(L_6\ge872\)나 \(L_6\ge867\)에 **아무 영향이 없으며**,
- 남은 8개가 Hamiltonian continuation을 **가진다는 뜻도 아니다**.

**RR branch closure**: parity 경로는 닫혔고(라운드26–28 반증),
capacity 경로가 18개 중 10개를 제거했으며, 남은 것은
**8개 short survivor + CH2 + T3**이다.

## 5. 이번 라운드에서 지킨 제약

- long six에 DFS를 **돌리지 않았다**.
- 기존 \(5m+4\) bound를 slack=0 논증으로 **약화하지 않았다** —
  정련은 port 가용성만 사용했고, slack은 어디에도 등장하지 않는다.
- N=0 checkpoint **미접촉**, 전역 NR6 search **없음**.
- node cap 도달을 absence로 **쓰지 않았다** (CH2 확장은 INCOMPLETE).
