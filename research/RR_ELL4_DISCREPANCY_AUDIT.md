# ell=4 same-component 불일치 완전 해소 (라운드 18)

산출: `src/audit_rr_ell4_discrepancy.py` -> `outputs/rr_ell4_historical_9.json`,
`outputs/rr_ell4_local_5.json`, `outputs/rr_ell4_set_difference.json`.
새 탐색 없음(9개 witness의 exact replay + 기존 L5 재사용).

## 결론 먼저

> **불일치는 "누락된 witness"가 아니라 계수 단위(counting unit)와
> depth scope의 차이였다. 양방향 모두 누락이 없다.**
>
> - **H9 = 9개의 완결된 6-macro-edge WORD**(역사적 코퍼스의 단위는
>   "완결된 word/최종 상태").
> - **L5 = 5개의 서로 다른 post-R2 STATE**(라운드17 enumerator의
>   단위는 "R2가 발동하는 순간의 상태").
>
> H9의 9개를 현재 엔진으로 전부 재생하면 **정확히 3개의 서로 다른
> post-R2 상태로 축약**되고, 그 3개 각각이 **정확히 3개의 legal
> 후속 macro-edge**를 가진다 — **3 × 3 = 9**로 역사적 개수와 정확히
> 일치한다. 그리고 그 3개 상태 전부가 L5에 들어 있다.
> L5의 나머지 2개는 abandonment 이후 depth 6(총 7개 macro-edge)에
> 있어, 역사적 코퍼스의 depth≤6 word scope **밖**이다.

## 1-2. 두 집합과 집합 관계

| 항목 | 값 |
|---|---:|
| H9 word 개수 | 9 |
| H9의 서로 다른 post-R2 상태 | **3** |
| L5 상태 개수 | 5 |
| H9-states ∩ L5 | **3** |
| **H9-states \ L5** | **0 (공집합)** |
| L5 \ H9-states | 2 (둘 다 depth 6, scope 밖) |

**H9 ⊆ L5**(post-R2 상태 기준)가 정확히 성립한다.

### 후속 edge 산술 (3 × 3 = 9)

| post-R2 상태 | 공유하는 역사적 word | legal 후속 macro-edge |
|---|---|---:|
| `fe82b0cdb512` | `2d88642a`(w3:201), `49caddbf`(w3:210), `789ecdd7`(w2:10) | 3 |
| `6f1ed828b231` | `3d74b386`(w2:10), `941ba3fd`(w3:210), `9a31f204`(w3:201) | 3 |
| `5d3f8cb9fdd4` | `87fd0921`(w3:210), `8b410837`(w2:10), `e2c28bc2`(w3:201) | 3 |

세 상태 모두 후속 edge가 정확히 3개이고, 역사적 word 3개가 그
3개 선택지에 정확히 1:1 대응한다. **`accounts_for_all_words: True`
(3/3).**

## 3. H9 9개의 현재 엔진 literal replay

| 검사 | 결과 |
|---|---|
| 모든 move legal | **9/9** |
| `area_a_prune_reason` 전 단계 통과 | **9/9** (divergence 0) |
| same-component 판정 재현 | **9/9** |
| abandon_ell=4 재현 | **9/9** |
| 최초 divergence step | **없음** |

**증명 등급: exact replay.** 역사적 record가 무효(`HISTORICAL_RECORD_INVALID`)
이거나 엔진이 표류(`CURRENT_ENGINE_DRIFT`)한 정황은 전혀 없다.

## 9. Depth/index 정의 대조

| | 역사적 코퍼스 | 라운드17 enumerator |
|---|---|---|
| depth 단위 | word 전체의 macro-edge 수 (scope: ≤6) | **abandonment root 이후**의 macro-edge 수 |
| 변환식 | — | `fresh_depth = (R2까지의 총 edge 수) − 1` (H9는 전부 abandonment가 idx 0) |
| H9의 R2 depth(변환 후) | — | **전부 4** |
| L5의 depth | — | **4와 6** |

L5의 depth-6 항목은 총 7개 macro-edge를 뜻하므로 역사적 depth≤6
scope 밖 — 역사적 코퍼스가 담을 수 **없었던** 것이다.

## 10. 원인 코드 (witness 단위)

9개 전부 동일 코드:

| 원인 코드 | 개수 | 설명 |
|---|---:|---|
| `EXACT_REPLAY_PRESENT_IN_L5` | **9/9** | 이 역사적 word의 post-R2 상태가 L5에 실제로 존재한다. 9-vs-5 격차는 계수 단위 차이일 뿐 누락이 아니다. |
| `INCOMPLETE` | 0 | — |

`ROOT_SCOPE_OUTSIDE`, `CANONICAL_COLLAPSE_BUG`, `GENERATOR_OMISSION`,
`PRUNE_MISMATCH`, `HISTORY_FIELD_MISSING`, `HISTORICAL_RECORD_INVALID`,
`CURRENT_ENGINE_DRIFT` — **전부 해당 없음**(각각 §3, §5-8에서
개별적으로 검사해 배제).

## 11. 정정된 정확한 문장

과제가 제시한 선택지 중 **B와 E의 정밀화**에 해당한다:

> **역사적 bounded corpus에는 ell=4 same-component 완결 word가
> 9개 있으며, 이들은 정확히 3개의 서로 다른 post-R2 상태로
> 축약된다(3 상태 × 3 legal 후속 edge = 9 word). 그 3개 상태는
> 전부 지정된 root-local universe(root class 1, abandonment 직후
> 상태, depth ceiling 6, frontier 자연소진, 독립 DFS 교차검증
> 통과)에 포함되어 있다. 해당 universe의 ell=4 same-component
> 상태는 총 5개이며, 나머지 2개는 abandonment 이후 depth 6(총 7
> macro-edge)에 있어 역사적 코퍼스의 depth≤6 scope 밖이다.
> 두 집합은 공통 scope 안에서 서로에 대해 아무것도 누락하지
> 않는다.**

"전체 RR"이라는 표현은 여전히 사용하지 않는다 — coverage proof가
없기 때문이다.

## 13. 과거 문서 정정 기록

| # | 파일 | 이전 문장(요지) | 새 문장(요지) | 변경 이유 | 영향받는 정리 |
|---:|---|---|---|---|---|
| 1 | `outputs/rr_old_new_corpus_diff.json` | `UNRESOLVED_DISCREPANCY`: "예상과 반대 방향, 원인 3개 후보 모두 미확인" | `ROUND18_RESOLUTION`: 계수 단위(word vs post-R2 state) + depth scope 차이로 완전 해소, `H9 ⊆ L5` | 후보 3개를 개별 검사: depth-convention은 부분적으로만 맞았고(주 원인은 계수 단위), same-component 계산 불일치와 prune/config 표류는 **직접 반증**(9/9 exact replay 일치) | ell=4 same-component 개수를 인용하는 모든 서술 |
| 2 | 〃 | `ell4_discrepancy_deeper_trace`: "격차는 아마 enumerator 버그가 아니라 …일 것" (추측) | 삭제하고 `ROUND17_SUPERSEDED_TEXT`에 감사 추적용으로 원문 보존 | 추측이 확정된 사실로 대체됨 | 〃 |
| 3 | `STATUS.md` 라운드17 절 | "미해결 불일치로 정직하게 보고" (13줄) | "**RESOLVED in Round 18**" 표시 + 라운드18 절로 유도 (6줄) | 해소됨 | 〃 |
| 4 | `outputs/rr_uncapped_local_universe.json` 필드명 | `unique_canonical_states` | **`unique_raw_states`** + `dedup_key` 필드 추가 | 실제로는 `canonicalize()`를 호출하지 않은 raw 상태 수였음. raw dedup은 완전성에 **안전**(과다확장만 발생)하므로 **수치·결론은 무효화되지 않음**, 라벨만 오류 | 라운드17의 모든 `unique_canonical_states` 인용 |
| 5 | `research/RR_LOCAL_UNIVERSE.md` 표 헤더 | "unique canonical states" | "unique **raw** states" | 위와 동일(본문 §Canonical quotient는 이미 리터럴임을 정확히 서술하고 있었으므로 표 헤더만 불일치했음) | 없음(본문은 이미 정확) |
| 6 | `research/RR_EXHAUSTIVENESS_STANDARD.md` §8 certificate 요구항목 | "unique canonical states" | "unique states (**raw인지 canonical인지 반드시 명시**)" | 향후 같은 라벨 오류 재발 방지 | 없음(표준 강화) |
| 7 | `src/enumerate_rr_uncapped_local.py`, `src/verify_rr_exhaustive_certificate.py` | 필드명·주석 | 정정 후 **양쪽 재실행**, 독립 DFS 교차검증 5/5 ell 여전히 일치 | #4와 동일 | 없음(수치 불변) |

**정정으로 인해 뒤집힌 정리는 없다** — #4-7은 순수 라벨 정정이고
(수치 불변), #1-3은 "미해결"을 "해결됨"으로 바꾼 것이다.

## 라운드17 서술의 정정 (요약)

라운드17 STATUS.md와 `outputs/rr_old_new_corpus_diff.json`은 이
격차를 "예상과 반대 방향의 미해결 불일치"로 기록했다. **그 서술은
이제 폐기된다** — 방향이 반대인 것처럼 보였던 이유는 두 숫자가
서로 다른 대상(word vs state)을 세고 있었기 때문이며, 같은 단위로
맞추면 `H9 ⊆ L5`로 정상 방향이다.
