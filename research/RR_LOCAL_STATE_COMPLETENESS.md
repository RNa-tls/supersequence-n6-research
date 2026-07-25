# Root-local state 표현의 Markov-완전성 (라운드 18)

산출: `src/verify_rr_local_state_completeness.py` ->
`outputs/rr_local_state_completeness.json`. 새 탐색 없음(같은
root-local universe를 dedup key만 바꿔 두 번 재실행).

## 5. 검사한 가설

ell=4 9-vs-5 격차를 발견했을 때 제기된 구체적 버그 가설:

> 라운드17 enumerator의 dedup key가 `state.stable_key()` 하나뿐이라,
> R 이벤트 개수(`r_count`)와 R1의 target orbit(`r1_target_q`)이라는
> **history field가 key에 빠져 있다**. 같은 상태가 서로 다른
> history로 도달되면 뒤에 온 쪽이 중복으로 버려지고, 그 자손이
> 2번째 R 이벤트를 얻지 못해 **undercount**가 발생한다.

## 검사 방법

동일한 root-local 열거를 두 가지 dedup key로 각각 실행:

- **(a) `state_only`**: `state.stable_key()` (라운드17이 실제로 쓴 key)
- **(b) `state_plus_history`**: `(state.stable_key(), r_count, r1_target_orbit)`

(b)가 (a)보다 더 많이 찾으면 history field가 실제로 결과를 바꾸는
것이므로 표현이 Markov-완전하지 않다는 뜻이다.

## 결과 — 가설 반증됨

| ell | (a) rr_final / same | (b) rr_final / same | 일치 | 서로 다른 history로 도달된 상태 수 |
|---:|---|---|:---:|---:|
| 0 | 455 / 1 | 455 / 1 | ✓ | **0** |
| 1 | 415 / 0 | 415 / 0 | ✓ | **0** |
| 2 | 464 / 0 | 464 / 0 | ✓ | **0** |
| 3 | 450 / 0 | 450 / 0 | ✓ | **0** |
| 4 | 450 / 5 | 450 / 5 | ✓ | **0** |

**두 key가 모든 ell에서 정확히 일치한다.** 더 결정적으로,
진단 카운터 `states_reached_with_more_than_one_history`가
**모든 ell에서 0**이다 — 이 universe 안에서는 **어떤 상태도 서로
다른 (r_count, r1_target) 조합으로 두 번 도달되지 않는다**. 즉 이
탐색 트리는 (state, history) 쌍에 대해 실질적으로 트리 구조이며,
history field 누락으로 인한 압축 손실이 **원천적으로 발생하지
않는다**.

## 판정

> **이 root-local universe(depth ceiling 6, root class 1)에 한해,
> 상태 표현은 same-component 질문에 대해 Markov-완전하다** —
> **유한 완전 검증** 등급(두 dedup 모드 각각 frontier 자연소진).
>
> **가설(`HISTORY_FIELD_MISSING`)은 반증됨.** ell=4 격차의 실제
> 원인은 `RR_ELL4_DISCREPANCY_AUDIT.md`가 확정한 계수 단위 +
> depth scope 차이다.

**scope 제한(정직하게 명시)**: 이것은 이 특정 universe에 대한
유한 검사이지, "이 상태 표현이 일반적으로 Markov-완전하다"는
증명이 **아니다.** 더 깊은 depth ceiling이나 다른 root class에서는
같은 상태가 여러 history로 도달될 수 있으며, 그 경우 dedup key에
history를 포함해야 한다. **향후 enumerator는 안전을 위해
`state_plus_history` key를 기본값으로 쓰는 것을 권한다** — 이번
검사에서 비용 차이가 없었기 때문이다(unique key 수가 동일).

## 부수적으로 발견된 라벨 오류 (정정함)

`outputs/rr_uncapped_local_universe.json`의 필드명
`unique_canonical_states`는 실제로는 **raw(비-canonicalize) 상태**를
센 것이었다(`exact.canonicalize()`를 호출하지 않음). raw dedup은
완전성 측면에서 **안전하다** — left-S6 relabeling된 복제본을 중복
확장할 뿐, 도달 가능한 상태를 건너뛰지는 못한다 — 따라서 라운드17의
어떤 결과도 무효화되지 않는다. 다만 필드명이 틀렸으므로
**`unique_raw_states`로 정정**하고 `dedup_key` 필드를 추가했다
(`src/enumerate_rr_uncapped_local.py`, 독립 DFS 검증기도 함께 갱신,
재실행 후 5/5 ell 여전히 일치).
