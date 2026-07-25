# Abandonment ell 불변량과 same-component 이분법 (라운드 15)

산출: `src/analyze_rr_abandonment_ell.py` -> `outputs/rr_abandonment_ell_table.json`
(전체 4,470개 RR witness, 기존 `rr_literal_witnesses.json` 재사용, 새 탐색 없음).

## 1. Abandonment ell의 정확한 정의와 hex0 상태표

RR word는 정확히 1개의 abandonment 사건(`Z2abandon`, weight=2,
abandonment=True)을 갖는다(코드 사실, 4,470/4,470 단일 abandonment
검증됨). 이 사건이 hex0의 어느 위치(`ell`, 0-indexed, 0~4)에서
발동하는지가 abandonment ell이다 — hex0는 위치 0(anchor, `t=0`부터
항상 이미 방문됨)부터 시작해 순수 회전으로 위치 `ell`까지 도달한 뒤,
`ell`번째 위치에서 abandonment 조인트가 발동해 hex0를 떠난다. 그 결과
위치 `ell+1, ..., 5`가 미방문(residual)으로 남는다.

hex0의 고정 위치-orbit 대응(라운드 12 확립): `[0, 120, 33, 9, 3, 1]`.

| ell | residual 위치 | residual orbit | 남은 위치 수 | completer 유일 강제? | witness 수(전체) | same-component 수 |
|---:|---|---|---:|---|---:|---:|
| 0 | 1,2,3,4,5 | 120,33,9,3,1 | 5 | 아니오 | 926 | 1 |
| 1 | 2,3,4,5 | 33,9,3,1 | 4 | 아니오 | 923 | 0 |
| 2 | 3,4,5 | 9,3,1 | 3 | 아니오 | 940 | 0 |
| 3 | 4,5 | 3,1 | 2 | 아니오 | 914 | 0 |
| 4 | 5 | 1 | 1 | **예**(조합론적, 라운드14 손증명) | 767 | 9 |

**산출**: `outputs/rr_abandonment_ell_table.json`의 `ell_table`,
`ell_distribution`. ell 분포 자체는 거의 균등(926/923/940/914/767,
ell=4가 약간 적음)하며, same-component만 정확히 ell∈{0,4}에서만
관측된다(ell=1,2,3에서 0/2777) — **유한 완전 검증**(전체 코퍼스가
depth≤6 RR word의 완전한 열거이므로, 이는 표본이 아니라 정확한
전수조사다).

## 2. Hub 완성(completer) 발생률과 orbit 선택 — 새로운 핵심 발견

`hub_completer_found`(hex0가 word 안에서 두 번째로 터치되는지) 비율:
ell=0: 43/926, ell=1: 34/923, ell=2: 45/940, ell=3: 45/914, ell=4:
45/767.

**놀라운 사실(전수 검증, 212/212 hub-완성 사건 전부)**: hub가
완성되는 모든 경우에서, completer의 target orbit은 **항상 정확히
"가장 가까운" residual 위치(`ell+1`)의 orbit**이다 — `ell=0`이면
항상 120, `ell=1`이면 항상 33, `ell=2`이면 항상 9, `ell=3`이면 항상
3, `ell=4`이면 항상 1(이 경우는 어차피 유일한 후보). **다른 residual
orbit(예: ell=0에서 orbit 1,3,9,33)은 corpus에서 단 한 번도
completer로 실현되지 않는다(0/4470)** — 이는 앞서 라운드14가 수동
구성한 합성 상태의 국소 BFS로 "5개 orbit 모두 legal"임을 보였던
것과 모순되지 않는다: **legal(원칙적으로 가능)과 realized(실제
depth≤6 코퍼스에 나타남)는 다른 질문**이다.

### 자원 예산(resource-budget) 설명 — `src/verify_rr_ell4_proof.py`

RR word의 총 macro-edge 수는 정확히 6으로 고정된다(코퍼스 정의:
`f1_n2_defect_words.json`의 `area_a_depth6`). 실제 witness 하나의
post-abandonment 상태에서 국소(bounded, 새 대규모 탐색 아님) BFS로
각 residual orbit까지의 최소 macro-edge 비용을 계산하면:

```
ell=0: {120: 2, 1: 4, 33: 4, 9: 5, 3: 6}
ell=1: {33: 2, 9: 4, 3: 5, 1: 6}
ell=2: {9: 2, 3: 4, 1: 5}
ell=3: {3: 2, 1: 4}
ell=4: {1: 2}
```

**가장 가까운 residual 위치는 항상 비용 2로 도달 가능하지만, 다른
모든 residual orbit은 비용 4 이상이 필요하다.** 총 예산 6에서
abandonment(1) + completer(≥4) + R1 + R2(각 최소 1)를 맞추려면
최소 7이 필요해 예산을 초과한다 — **단, completer가 R1 자신과
일치하는 경우는 1+4+1=6으로 정확히 맞아떨어질 수 있어, 순수
자원회계만으로는 완전한 불가능성 증명이 되지 않는다.** 그럼에도
실제 전수조사(4,470개)에서 이 조합은 단 한 번도 나타나지 않는다 —
**이 잔여 gap은 미완료로 남긴다**(정직하게 명시).

## 판정 요약

| 명제 | 판정 | 근거 |
|---|---|---|
| same-component ⟹ abandonment ell ∈ {0,4} | **유한 완전 검증**(4,470/4,470, 반례 0) | `rr_abandonment_ell_table.json` |
| hub-completed일 때 completer orbit = 가장 가까운 residual 위치 | **유한 완전 검증**(212/212, 반례 0) | 위 표 |
| 위 사실의 depth-6 자원회계에 의한 완전한 필연성 | **미완료**(강한 국소 증거, R1-일치 특수 경우가 예산상 이론적으로 가능하나 실현되지 않는 이유는 규명 못함) | 위 서술 |

이 결과는 Section 2의 목표 정리("same-component ⟹ abandonment
ell∈{0,4}")를 **corpus-exact를 넘어 유한 완전 검증**으로 격상시키며
(코퍼스가 depth≤6 RR word의 완전한 전수조사이므로), 왜 그런지에
대한 자원회계 기반의 강력한 국소 설명을 추가로 제공한다.
