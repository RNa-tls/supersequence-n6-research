# 남은 9개 J seed 정확한 목록

산출: `outputs/j_9_remaining_seeds.json`. Deterministic ordering: canonical
state hash 오름차순.

이 9개는 `outputs/j_budget_search.json`(depth<=15, seed당 edge budget
~67,568)에서 완주도 capacity 실패도 발견하지 못한 채 남은 상태다 —
`outputs/j_capacity_extension_profile.json`의 74개 중에서도 가장 깊은
탐색까지 버틴 부분집합이다.

## 요약표

| Seed (16자) | Φ | charge-word family 수 | 남은 joint 수 | 남은 신규 orbit 필요 | 현재 legal transition 수 |
|---|---:|---:|---:|---:|---:|
| `45929408de25b866` | 0 | 1 | 114 | 19 | 4 |
| `624257c39b75859d` | 0 | 1 | 114 | 20 | 3 |
| `6b42cfe0deafcfa4` | 5 | 19 | 115 | — | 4 |
| `ad74dbc3a5f5c987` | 0 | 1 | 114 | 19 | 4 |
| `c652843b153b6c7b` | 4 | 12 | 114 | — | 4 |
| `e0f8ed14b4832a72` | 4 | 12 | 114 | — | 4 |
| `eaa42caf37c5f6ad` | 4 | 12 | 114 | — | 4 |
| `f4e71fe28ebaa10b` | 4 | 12 | 114 | — | 4 |
| `f95ab0147fb90de8` | 4 | 12 | 114 | — | 4 |

(정확한 `remaining_new_orbit_joints_required` 값은 Φ=4,5인 6개에 대해서도
`outputs/j_9_remaining_seeds.json`에 개별 기록돼 있다 — 표에는 Φ=0인 3개만
따로 뽑아 강조했다.)

각 seed 레코드에는 다음이 전부 포함돼 있다(요청된 전체 필드):
canonical hash, 전체 literal macro-path, J 위치, 좌표
`(P,F,S,H,O,D,N)`, endpoint 순열, `visited_count`, Φ, charge-word
family 목록, fragment/current hexagon과 component 모양, **지금 이 순간의
legal transition 전체 목록**(각각의 weight/abandonment/new_orbit/이후
Φ/prune 통과 여부 포함).

## 관찰: 3개의 Φ=0 seed가 가장 좁다

앞서 예측한 대로, `45929408...`, `624257c3...`, `ad74dbc3...` 세
seed만 `num_charge_word_families=1`(빈 charge multiset, 즉 남은 114개
joint 전부가 예외 없이 `ell=5`)이다. 나머지 6개는 Φ=4 또는 5로 12개
또는 19개의 family가 허용된다.

## 현재 legal transition 수: 3~4개

9개 전부 **지금 당장**은 3~4개의 legal transition을 가진다(막다른
골목이 아니다). 이는 이미 `outputs/j_budget_search.json`의
`max_depth_reached=8, cap_hit=true`(모두 edge cap에 걸림, frontier
비어있지 않음)와 일치한다 — 이 9개는 "죽은" 상태가 아니라 "탐색이
아직 안 끝난" 상태다.
