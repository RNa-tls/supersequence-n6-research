# `rr_word_lift_archive` — 라운드 99/100 단어-lift 감사 아카이브

**Codex 감사가 불가능한 상태에서 만든 것이다.** 여기 담긴 폐쇄는 전부 **잠정**이며, 이
아카이브는 나중에 누구든 독립적으로 재판정할 수 있도록 입력·판정·인증서를 모두 남긴다.

생성: `python3 src/replay_rr_word_lift.py` (표준 라이브러리만, 이 저장소의 탐색/probe 코드를
하나도 import 하지 않는다).

## 입력

라운드-93c 아카이브 `outputs/rr_port_path_hall_archive/` 만 쓴다 — `geometry.jsonl.gz`,
`states.jsonl.gz`, `covers.jsonl.gz`, `hall_results.jsonl.gz`.
Hall 판정(`deficit == 0`)은 그 아카이브의 값을 쓰고, 그 뒤의 **층 A · B2 · D1 · D4b 와
단어 조건은 전부 이 파일 안에서 새로 구현**한다.

## 기하 재구성 (아카이브의 `joint_targets` 를 쓰지 않는다)

* 육각형 = 단어의 **순환 회전류**. `hexagon` 필드와 대조만 하고 신뢰하지 않는다.
* `x = x0x1x2x3x4x5` 에서 joint 네 개:

```
T1 = x2 x3 x4 x5 x1 x0
T2 = x3 x4 x5 x1 x2 x0
T3 = x3 x4 x5 x2 x0 x1
T4 = x3 x4 x5 x2 x1 x0
```

* `ℓ` 회전 뒤의 joint 는 `x ← σ^ℓ(u)` 로 두고 같은 식.
* `ℓ` 은 강제된다 — 빈 육각형 5, fragment 수리 `5 − c_f` (라운드 90/91, 감사 완료).

## 파일

| 파일 | 행 | 내용 |
|---|---|---|
| `pairs.jsonl.gz` | 헤더 + **19,176** | 층 A·B2·D1·D4b 를 통과한 (상태, cover) 쌍 전부와 W-A 판정. `pair_verdict ∈ {PASS, W_A_FAIL, W_B2_FAIL, W_IN_FAIL}`. 실패 쌍에는 `certificate` |
| `closures.jsonl.gz` | 헤더 + **564** | 모든 잔여 cover 가 실패한 상태. `state_verdict`, `all_surviving_covers_fail`, `unique_path`, cover별 판정 |
| `summary.json` | — | 기하 정리 인증서, 교차 검사, 쌍/상태 집계 |

`pairs.jsonl.gz` 의 19,176 과 `closures` 의 564 는 **라운드 97 에서 이미 감사된 4개 상태를
포함한** 값이다. 라운드 99 의 19,172 / 560 은 그 4개를 제외한 값이므로 차이는 정확히 4다.

## 폐쇄 규칙

```
state_verdict = UNSAT  ⟺  모든 잔여 cover 가 PASS 가 아님
```

`any(cover fails)` 는 절대 쓰지 않는다.

## 인증서 (`certificate`)

W-A 실패 쌍마다:

* `unreachable_obligation` — 현재 구체 단어에서 닿지 않는 의무 하나
* `unreachable_count` — 닿지 않는 의무 총수
* `candidate_words_in_that_obligation` — 그 의무의 후보 단어 전부
* `reachable_word_count` — 도달 가능한 구체 단어 수
* `sample_reachable_sources` — 도달 가능한 단어 표본과 그 `ℓ`, joint target 네 개

재판정 방법: 위 문자열 규칙으로 후보 단어마다 `{목표 의무: 목표 단어}` 를 만들고 현재 단어
`p_id` 에서 BFS 하면 된다. 그래프를 저장하지 않았으므로 **결정적으로 재구성**된다.

## 알려진 의존성 (중요)

이 폐쇄들은 **`ℓ` 강제 정리에 전적으로 의존한다.** 모든 단어에서 `ℓ ∈ {0..5}` 를 전부
허용하는 과대허용 대조를 돌리면 564개 폐쇄가 **전부 사라진다**(생존 0). 즉 W-A 의 힘은
단어 기하 자체가 아니라 "각 pass 의 회전 수가 강제된다"는 라운드 90/91 의 감사된 정리에서
나온다.
