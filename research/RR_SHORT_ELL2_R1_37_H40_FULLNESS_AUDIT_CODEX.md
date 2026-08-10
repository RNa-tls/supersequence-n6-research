# Round 61 follow-up — h40 literal-fullness audit

작성자: Codex

## 판정

Round 61의 핵심 전제는 원본 six all-13 checkpoints의 84개 frozen Stage-D
frontier state에서 직접 다시 확인됐다.

```text
anchors                                  84
h40 registered in incidence graph       84
h40 literal occupancy mask = 63         84
h40 visited literal windows = 6         84
literal 245130 already visited           84
current endpoint = 245130                 0
```

따라서 모든 anchor에서

```text
h40 mask = 0b111111 = FULL
endpoint != 245130
```

이다.

여기서 `registered`와 `full`은 명시적으로 다른 검사다.

- `registered`: 사용된 E-orbit phase 가운데 h40에 incident한 것이 하나 이상이다.
- `full`: h40의 여섯 literal permutation-window bit가 모두 설정돼 있다.

정리 전제에는 두 번째 조건을 사용했다. 첫 번째 조건을 대신 쓰지 않았다.

## 1. 원본 checkpoint 대조

Round-58 manifest의 84개 `start_domain.records`를 다음 여섯 immutable source
checkpoint의 frontier record와 `source_node_id`로 일대일 대조했다.

| seed | frontier anchors | source SHA-256 |
|---|---:|---|
| `236166` | 9 | `e75da6bdf90c794e83c3ab3c4618f0fbefdefd78e6e9b85bfe106f85e2507c89` |
| `12` | 8 | `c3b2dbde91c6bc5c3ef5fd138d7f173dc5f74c454257d712a4607cf6d9dc9f92` |
| `6` | 20 | `4f0d45d9949071fb1c94263e3cf41855d3277e47b3e4cba571ce476ade75239f` |
| `3` | 21 | `4944c792b4cc7e20352cff2def1a3694697205beb1f6e68f6ab7263338e443f2` |
| `303321` | 12 | `6df21ecb28630e1e078f972be12bb3162d3b0c9546a9f2056a0a330478e69ac5` |
| `13` | 14 | `86a459b38c0ebc28eb13bc290ea9e5cbb673656ceb4a2f1dff8c594c1bb2bc16` |

각 record에서 다음 필드가 manifest와 checkpoint 사이에 정확히 일치해야만
원장에 포함했다.

- exact state JSON과 재계산 state hash
- decoration JSON
- path hash
- depth와 relative depth
- source node ID

per-anchor 84행 전체는
`outputs/rr_short_ell2_r1_37_h40_anchor_fullness.json`에 있다.

## 2. h40 literal occupancy

고정 rotation table에서 h40의 여섯 word를 직접 생성하고, 각 anchor의
`hex_masks[40]` 여섯 bit와 대조했다. 모든 행에서 다음이 성립한다.

```text
hex_masks[40] = 63
bit_count      = 6
six window visited flags = [true,true,true,true,true,true]
```

따라서 `245130 = h40 position 1`도 84/84에서 이미 방문됐다. 별도 endpoint
검사는 0/84를 반환했다.

## 3. Occupancy monotonicity

### 손증명 — engine semantics

`exact.extend`는 현재 `hex_masks`를 list로 복사한 뒤 새 target window에 대해

```python
hm[h] |= 1 << bit
```

만 수행한다. 설정된 bit를 지우는 연산은 없다. 따라서 모든 legal literal
transition에서 각 hex mask는 bitwise inclusion 아래 단조 증가한다.

또한 `extend`는 target bit가 이미 설정돼 있으면 `None`을 반환한다. 따라서
이미 방문된 literal window로 재진입하는 legal transition은 존재하지 않는다.

### 유한 검산

여섯 Stage-D parent DAG의 1,325,308개 non-root parent→child macro edge에서

```text
parent.hex_masks[h] & ~child.hex_masks[h] = 0
```

을 모든 h에 대해 검사했다. 실패는 0개다.

### 245130 귀납

1. 84개 anchor 모두에서 `245130`은 visited이다.
2. 어느 anchor의 현재 endpoint도 `245130`이 아니다.
3. 이후 endpoint가 `245130`이 되려면 어떤 literal transition의 target이
   `245130`이어야 한다.
4. 그러나 no-repeat membership test가 그 transition을 거부한다.

따라서 모든 legal descendant에서 `245130`은 visited 상태로 남지만 현재
endpoint가 될 수 없다.

## 4. Hex-82 implication chain

고정표로 다음을 다시 계산했다.

```text
q91:p2 = 513042 = h82 position 3
245130 --the sole engine w2 move--> 513042
```

engine에 weight-2 move가 하나뿐이고 그 action이 bijection이므로 literal 역상이
하나인 것은 일반적인 사실이다. 이것 자체는 substantive obstruction이 아니다.
실제 obstruction은 그 역상 `245130`이 모든 anchor에서 이미 방문됐고 어느
anchor의 endpoint도 아니라는 provenance 사실이다.

따라서:

```text
h82 joins C_R1 before R2
=> q91:p2 incidence must be registered
=> the pre-R2 Z2 must start at 245130
=> 245130 would have to be re-entered
=> exact no-repeat rejects that re-entry
=> q91:p2 cannot be newly registered
=> h82 cannot join C_R1
```

## 5. Route completeness

h82의 rotation hexagon에는 정확히 여섯 word가 있다.

| position | orbit:phase | word |
|---:|---|---:|
| 0 | `q82:p0` | `042513` |
| 1 | `q128:p2` | `425130` |
| 2 | `q42:p1` | `251304` |
| 3 | `q91:p2` | `513042` |
| 4 | `q78:p3` | `130425` |
| 5 | `q83:p4` | `304251` |

q91 자체의 position 3을 제외하면 정확히 Round 60의 미해결 다섯 route가
남는다. 다른 h82 route는 없다. fresh orbit의 Z3가 R1 component를 확장하려면
그 target hexagon이 이미 `C_R1`에 있어야 하므로, 다섯 route 모두 위의
q91:p2 선행 incidence를 요구한다.

## 6. 정리 범위와 가정

T2b–T4의 가정은 다음과 같다.

1. `short_ell2_r1_37`의 정확히 84개 frozen Stage-D anchor descendant family.
2. R1 이후, R2 이전의 상태와 Target-A-safe traversal semantics.
3. literal permutation windows에 대한 exact no-repeat semantics.
4. anchor에서 R1-target component가 q91을 포함하고 h40/h92에 incident한다는
   저장 상태 사실.
5. fixed `ORBIT_PHASE / HEX_POSITION` table과 한 개의 engine w2 move.
6. 이전에 검증된 direct-Z2 lemma의 조건과 Round-60 T2a full-hex obstruction.

사용하지 않은 가정:

- Phi bound
- 일반 phase-capacity helper
- 미증명 full-pass 정상형
- 모든 short root 또는 NR6 전체에 대한 가정

`h40 full`은 full-pass 추측이 아니라 각 anchor의 6-bit exact occupancy를 직접
검사한 결과다.

## 7. 재확인된 ladder

| 단계 | 상태 | 범위 |
|---|---|---|
| T2b | 재확인 | 다섯 h82 route exact-unreachable |
| T2+ | 재확인 | 84-anchor family의 전체 C4 prerequisite obstruction |
| T3 | 재확인 | 같은 family에서 first component-changing Z3 불가능 |
| T4 | 재확인 | direct-Z2 lemma와 T3를 결합한 pre-R2 bridge 불가능 |

이 결과는 `short_ell2_r1_37`의 frozen anchor family 밖으로 일반화하지 않는다.
