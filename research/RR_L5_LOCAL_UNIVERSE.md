# Corrected canonical local universe와 L5 ledger (라운드 19)

산출: `src/enumerate_rr_canonical_local.py` -> `outputs/rr_canonical_local_universe.json`,
`src/verify_rr_l5_states.py` -> `outputs/rr_l5_state_ledger.json`,
`outputs/rr_l5_state_ledger_depth7.json`. 새 completion search 없음.

## 1. 진짜 canonical enumerator — 그리고 raw가 이미 옳았다는 확인

라운드18은 라운드17 enumerator가 raw 상태로 dedup했음을 밝혔다(라벨
정정). 이번 라운드는 **진짜 canonical enumerator**를 별도로 작성했다.

### 처리해야 했던 미묘함 (라운드17에는 없던 문제)

`exact.canonicalize()`는 사전순 최소 left-S6 translate를 돌려주지만
**그것을 달성한 alpha는 돌려주지 않는다.** 그런데 history field
(`r1_target_orbit`)는 **raw orbit id**이므로, canonical 상태와 raw
orbit id를 짝지으면 일관성이 깨진다 — 같은 구조적 상황이 탐색이
어느 left-S6 사본에 도달했는지에 따라 다른 key를 받게 된다.

**해결**: **쌍(pair)을 canonicalize한다.** 최소 key를 달성하는 모든
alpha(여러 개일 수 있음 = 비자명 stabilizer)에 대해
`LEFT_ORBIT_ACTION[alpha]`로 history orbit id를 transport하고, 그
alpha들 위에서 사전순 최소를 취한다.

### 결과 — 세 가지 결정적 사실

| ell | expanded | canonical pair key | duplicate | stabilizer tie histogram |
|---:|---:|---:|---:|---|
| 0 | 3,814 | 3,814 | **0** | `{1: 3814}` |
| 1 | 3,657 | 3,657 | **0** | `{1: 3657}` |
| 2 | 3,858 | 3,858 | **0** | `{1: 3858}` |
| 3 | 3,840 | 3,840 | **0** | `{1: 3840}` |
| 4 | 3,834 | 3,834 | **0** | `{1: 3834}` |

1. **duplicate = 0**: canonical dedup으로도 중복이 단 한 건도
   발생하지 않는다 — 이 universe에는 **서로 left-S6 translate인 두
   상태가 아예 존재하지 않는다.**
2. **stabilizer tie가 전부 1**: 어떤 상태도 비자명 stabilizer를
   갖지 않으므로 history transport가 **모호하지 않다**(위 미묘함이
   실제로는 발동하지 않는다).
3. **모든 수치가 raw enumerator와 정확히 동일**(same-component
   1,0,0,0,5 포함). 즉 **라운드17의 raw enumerator는 "안전할 뿐"이
   아니라 이 universe에서는 정확히 옳았다** — 라운드18이 "raw는
   과다확장만 가능"이라 판정한 것보다 강한 결론이다.

### History summary field 필요성 (§1 요구사항)

- `r_count`: **필수.** R 이벤트 0개/1개 상태를 구분하지 못하면 RR
  word 구조(정확히 2개의 R) 자체를 추적할 수 없다.
- `r1_target_orbit`: **필수.** chaining의 정의가
  `R1 target orbit == R2 source orbit`이므로, 이 값 없이는 R2
  경계에서 chaining을 계산할 방법이 없다(§5 손증명 참고).

포함하지 **않은** 필드(전체 경로, hub 정체, abandonment ell)는
상태에서 복원되거나 root마다 고정이므로 quotient를 더 잘게 나눌 뿐
이번 라운드가 계산하는 어떤 relation도 바꾸지 않는다 — **이는
주장이며 증명이 아니다**, `--ablate` 옵션으로 재검증 가능하도록
남겨 두었다.

## 2. L5 다섯 post-R2 state exact ledger (ell=4)

deterministic order = (depth, raw hash).

| # | raw hash | 그룹 | root depth | word edges | R1 (src→tgt) | R2 (src→tgt) | Φ | O | S | trailing | 도달 경로 수 |
|---|---|---|---:|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `5d3f8cb9fdd4` | H3 | 4 | 5 | 0→**1** | **1**→0 | 0 | 2 | 3 | 3 | 1 |
| 2 | `6f1ed828b231` | H3 | 4 | 5 | 121→**1** | **1**→0 | 0 | 2 | 3 | 3 | 1 |
| 3 | `fe82b0cdb512` | H3 | 4 | 5 | 81→**1** | **1**→0 | 0 | 2 | 3 | 3 | 1 |
| 4 | `86195429f1c6` | N2 | 6 | 7 | 63→**1** | **1**→0 | 0 | 4 | 5 | 3 | 1 |
| 5 | `b2898cc223e9` | N2 | 6 | 7 | 87→**1** | **1**→0 | 0 | 5 | 6 | 3 | 1 |

**다섯 상태가 공유하는 불변량(예외 없음)**:

- `r1_target_orbit = 1`, `r2_source_orbit = 1`, `r2_source_phase = 4`,
  `r2_target_orbit = 0`
- hub completer의 착지점 = **(orbit 1, phase 4)** = hex0 위치 5
- 마지막 macro-edge = **`rot^0;w3:120`** (R2가 ell=0으로 즉시 발동)
- **Φ = 0**, legal trailing edge **정확히 3개**, pure-rotation suffix 가능
- 도달 경로 수 = 1 (§5 참고)

**차이나는 좌표는 오직 준비(preparation) 구간뿐**이다 — §3 참고.

## 5. Post-R2 state만으로 판정 가능한가 — 손증명으로 아니오

**경험적 검사는 공허(vacuous)하다**: depth 6에서 서로 다른 post-R2
상태 **2,234개 전부가 정확히 1개의 R2 boundary로만 도달**된다
(collision 0건). 비교할 두 history가 없으므로 이 검사는
Markov-완전성을 확인할 수도 반증할 수도 없다. **"multiple-history
state가 0개"라는 사실을 증명으로 쓰지 않는다**(과제 §5의 요구와
동일한 판단).

**연역적 답 — 손증명, 결론은 "아니오"**:

`chaining ≡ (R1 target orbit == R2 source orbit)`이다. post-R2
`ExactState`는 `(p, hex_masks, orbit_masks, F, S, H)`뿐이며,
`orbit_masks`는 **어떤 (orbit,phase)가 방문됐는지**만 기록할 뿐
**어느 edge가 R1이었는지**는 전혀 담지 않는다. 따라서
`r1_target_orbit`은 post-R2 상태의 함수가 **아니며**, chaining은
post-R2 상태만으로 결정될 수 **없다**. same-component도 마찬가지로
**pre-R2** component map에서 계산되는데 post-R2 상태는 이미 R2
자신의 target을 병합해 버렸으므로 직접 읽어낼 수 없다.

> **두 relation은 상태(state) 데이터가 아니라 경계(edge/boundary)
> 데이터다.** 그러므로 enumerator는 `(r_count, r1_target_orbit)`을
> 반드시 탐색 상태에 실어야 한다 — 이 universe에 collision이 0건인
> 것은 universe의 성질일 뿐 필드를 버려도 된다는 허가가 아니다.

## 9. Local universe coverage statement

> **이 local universe가 정확히 덮는 것**: `initial_state()`에서
> 시작해 hex0를 rotation offset `ell∈{0,1,2,3,4}`에서 유일한
> abandonment 조인트 `w2:10`으로 떠난 직후의 5개 root state 각각에서,
> `macro.macro_edges()`가 생성하고 `macro.area_a_prune_reason(·,
> macro.AREA_A)`를 통과하는 macro-edge만으로, **abandonment 이후
> depth ≤ 6**(비교용 실행은 ≤7) 안에 도달 가능하고 **R 이벤트가
> 2개 이하**인 **모든** legal state. frontier는 두 depth 모두에서
> 자연소진됐고, node/edge/time cap은 사용되지 않았으며, dedup은
> canonical `(state, history)` 쌍 기준(raw 기준과 결과 동일)이고,
> 구조적으로 독립한 DFS 검증기가 5/5 ell에서 일치를 확인했다.

**coverage 밖에 있는 RR state**(명시):

- abandonment가 `w2:10`이 아닌 조인트로 일어나는 word
  (역사적 코퍼스에서는 4,470/4,470이 `w2:10`이지만, 이것은
  capped-corpus exact이지 일반 필연이 아니다)
- abandonment 이후 depth > 6(비교 실행에서는 >7)인 word
- R 이벤트가 3개 이상인 word (RRR 등, 정의상 RR 밖)
- abandonment가 hex0가 **아닌** hexagon에서 일어나는 word
- `area_a_prune_reason`이 걸러내는 상태 — 이는 필요조건 prune이므로
  안전하지만, 그 필요조건 자체의 완전성은 이 문서 범위 밖

"전체 RR"이라는 표현은 사용하지 않는다.

## 10. Depth 확장 안정성 (completion search 아님, coverage 확인 목적)

depth ceiling 6 → 7로 **한 단계만** 늘려 재실행했다. frontier는
depth 7에서도 **자연소진**됐다(cap 사용 없음).

| ell | post-R2 states (6→7) | same-component states (6→7) | chaining states (6→7) | same+non-chaining |
|---:|---|---|---|---:|
| 0 | 455 → 1,572 | **1 → 3** | 2 → 7 | 0 → 0 |
| 1 | 415 → 1,433 | 0 → 0 | 0 → 4 | 0 → 0 |
| 2 | 464 → 1,587 | 0 → 0 | 1 → 5 | 0 → 0 |
| 3 | 450 → 1,560 | 0 → 0 | 1 → 5 | 0 → 0 |
| 4 | 450 → 1,572 | **5 → 5** | 6 → 10 | 0 → 0 |

**세 가지 안정성 결과**:

1. ~~**ell=4의 L5는 완전히 안정적**이다 — depth 7에서도 정확히 5개,
   H3/N2 분할도 동일.~~ **[라운드20에서 반증됨]** depth ceiling 8로
   올리면 preparation length 7짜리 state가 **4개 더** 나타나
   5→9가 된다. depth 6→7에서 변화가 없었던 이유는 안정성이 아니라
   **parity**다: `ell=4`의 same-component boundary는 abandonment
   root로부터 **짝수 depth**에서만 발생하므로 홀수인 7에서는 아무것도
   추가되지 않는다. `RR_TERMINAL_NORMAL_FORM_THEOREM.md` §12 참고.
2. **ell∈{0,4} 이분법이 depth 7에서도 유지**된다(ell=1,2,3에서
   여전히 0). ell=0만 1→3으로 늘어난다.
3. **same-component ⟹ chaining이 depth 7에서도 반례 0**
   (event level 8/8, state level 0 violation).

이는 bounded observation이 아니라 **root-local exhaustive**다
(frontier 자연소진). 다만 depth 8 이상은 시도하지 않았으므로
"임의 depth에서 안정적"이라고는 말하지 않는다.
