# Hub second-touch 사건 분류와 정정된 필요조건

산출: `src/analyze_rr_hub_touches.py`, `src/verify_rr_hub_theorems.py`
-> `outputs/rr_hub_touch_truth_table.json`.

## 정직한 정정 — 라운드 12의 "hub second-touch = R1" 주장은 반증됨

라운드 12는 10개 same-component witness 전부에서 "hub의 2번째
touch가 정확히 R1 자신의 사건"이라고 주장했다(`RR_ANCESTRY_PROOF.md`
§7). 이번 라운드에서 그 주장을 재검증하기 위해 hub touch ledger를
event-index 단위로 다시 추출한 결과, **이 주장은 거짓이었다** —
정정 사항:

| witness | hub completer event index | R1 event index | 일치? |
|---|---:|---:|---|
| `2d88642a05`, `49caddbf42`, `789ecdd735`, `87fd092184`, `8b4108376f`, `989d2261b4` | 3 | 3, 3, 3, 1, 1, 3 | **일치(4/10)** |
| `3d74b38661`, `941ba3fda9`, `9a31f2046d`, `e2c28bc229` | 3 | 2, 2, 2, 1 | **불일치(6/10)** |

**6/10에서 hub completer는 R1이 아니라 별도의 zero-charge(Z2)
이벤트다.** 예를 들어 `3d74b38661`: `[Z2abandon(orbit1,hex1),
Z2(orbit1,hex72), R1(orbit1,hex2), Z2(orbit1,hex0!=hub completer),
R2(orbit1→orbit0), Z2(orbit0,hex4)]` — R1(idx2)의 target은
orbit1이지만 hex2를 통해서다(hub인 hex0이 아니다). Hub(hex0)를
완성하는 것은 idx3의 **별도 Z2 이벤트**다.

## 3. Hub second-touch event 분류 — 정확한 truth table

전체 4,470개 코퍼스에서 hub가 존재하는 526개 witness의 hub
completer event type 분포:

```
python3 src/analyze_rr_hub_touches.py
hub second-touch event type distribution: {'R': 388, 'Z2': 138}
```

| event type | structurally possible? | 근거 |
|---|---|---|
| R (weight=3, existing, blocked) | **예(388/526)** | hub completer는 반드시 blocked(§`RR_HUB_TOUCH_COUNT.md` 증명 4번)이고 existing target(hub는 이미 등록된 orbit들만 가짐) 이어야 한다 — R은 정확히 이 조건(weight=3, existing, blocked)과 일치 |
| Z2 (weight=2, existing, blocked) | **예(138/526)** | 마찬가지로 weight=2도 existing+blocked 조건을 만족할 수 있다 |
| Z2abandon, A2, A3, J | **불가능** | 전부 abandonment=True를 요구하는데, hub completer는 정의상(§`RR_HUB_TOUCH_COUNT.md` 증명 4번) 반드시 blocked(비-abandon)여야 한다 — F 예산이 이미 소진됐으므로 |
| Z3(weight=3, fresh) | **불가능** | hub의 남은 위치는 이미 "existing"(그 orbit이 최소 1개 phase는 등록됨)이므로 new_orbit=True(fresh)가 될 수 없다 — 유일한 예외는 hub-anchor 자신이 아직 한 phase도 없는 경우인데, anchor는 t=0부터 최소 1 phase(자신의 home position)가 있으므로 이 경우도 배제 |

**목표였던 "R1만 가능"이라는 event-type 수준 진리표는 반증됐다** —
실제로는 R과 Z2 둘 다 가능하고, 심지어 R인 경우에도 그것이 R1인지
R2인지에 따라 세분화된다(§`RR_ANCESTRY_PROOF.md`류 raw data 재분석,
`(kind, is_r1, is_r2, r2_relation, chaining)` 6개 조합 관측: 상세는
아래 §4).

## 4. 정확한 필요조건 — orbit-level, event-identity 아님

실제 관측 데이터(10개 same-component 전부 chaining=True)를
재분석하면, **"hub completer 사건이 R1 자신인가"는 무관하고, 오직
"hub completer의 target orbit이 R1의 target orbit과 같은가"만
중요하다**:

> **정리(corpus-exact, 10/10)**: same-component RR witness에서, hub
> completer 사건의 target orbit은 항상 R1의 target orbit과
> **정확히 같다**(orbit id 비교, phase는 다를 수 있다). 이것이
> hub completer 사건이 R1 자신인지(4/10) 아니면 R1과 같은 orbit을
> 재사용하는 별도의 Z2 사건인지(6/10)와 무관하게 성립한다.

이것이 왜 chaining을 강제하는가: hub는 정확히 2개의 orbit만 가진다
(anchor + completer, §`RR_ANCESTRY_PROOF.md` §3-4의 Unique Hub
Hexagon Lemma + touch count≤2 정리의 직접 따름정리). R2가 "same"이
되려면 source와 target이 모두 hub-connected여야 한다(anchor 또는
completer-orbit). 관측상 R2의 target은 항상 anchor(orbit 0)이므로,
R2의 source는 반드시 completer-orbit이어야 한다. Chaining은 "R2의
source == R1의 target"인지 확인하는 것이므로, **completer-orbit ==
R1's target-orbit**이면 자동으로 chaining이 성립한다.

## 5. 왜 "hub completer orbit == R1 target orbit"인가 — 부분 설명

관측된 6개의 "R1 ≠ hub completer" 사례를 보면, 공통 패턴이 있다:
**하나의 orbit(주로 orbit 1 또는 orbit 120, hex-0에 인접한 6개
orbit 중 하나)이 word 안에서 여러 번(2회 이상, 서로 다른 phase로)
재사용되는 "streak"가 있고, R1은 이 streak의 한 원소이며, hub
completer(별도 Z2)는 같은 streak의 다른 원소다.** 이는
`RR_LOCAL_LEGALITY_TABLE.md`(라운드 11)에서 이미 관측된 "orbit
재사용 streak" 패턴과 정확히 같은 메커니즘이다.

**왜 이 streak-orbit이 항상 hub와 연결되는가**(즉 항상 streak 중
하나가 hex-0 위치를 채우는가)는 완전히 답하지 못했다 — 이는 depth≤6
이라는 짧은 word에서 "existing target으로 재사용 가능한 orbit의
메뉴"가 극히 좁다는 조합론적 사실(이동 메뉴가 weight-2 1개 +
weight-3 3개뿐)에서 나오는 경향으로 보이지만, 이를 일반적으로
증명하지는 못했다 — **추측**으로 표시한다.

## 심층 bounded search로 목표 정리 자체는 강하게 재확인됨

event-level 명제("hub completer=R1")는 반증됐지만, **더 중요한
목표 정리("same-component ⟹ chaining") 자체는 다음 심층 검증으로
오히려 더 강하게 뒷받침된다**:

```
python3 src/verify_rr_hub_theorems.py
→ 10개 witness 전부 depth≤9까지 exhaustive(frontier 완전 소진),
  same+non-chaining 반례 0건
```

이 탐색은 각 witness의 post-abandonment 상태에서 **corpus 자신의
기록된 경로에 국한하지 않고 도달 가능한 모든 R1/R2 선택지**를
탐색했다(예: `989d2261b4`는 R이 발동하기 전에 121개의 서로 다른
non-R hub-completing 후보가 있었다) — 그럼에도 **단 하나의
same+non-chaining 쌍도 발견되지 않았다.** 이는 depth≤9라는 이
특정 국소 범위 안에서는 매우 강력한 증거이지만, 여전히 **일반
손증명은 아니다** — `RR_MINIMAL_AXIOM_SET.md`가 정확한 최종 gap을
정리한다.
