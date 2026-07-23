# 74개 생존 J 상태의 정확한 분류

산출: `src/analyze_shortfall_budget.py` -> `outputs/j_74_survivor_classification.json`.
"74개"는 `outputs/j_capacity_extension_profile.json`에서 depth<=6·edge
cap 20,000 bounded 탐색으로도 capacity 실패 경로를 찾지 못한 J 상태
전체다(230개 중).

## 분류 — **완전 계산**

| Φ 분포(74개 중) | 개수 |
|---:|---:|
| 0 | 3 |
| 4 | 70 |
| 5 | 1 |

| charge-word family 분류 | 개수 |
|---|---:|
| `exactly_one_charge_word_family`(Φ=0) | 3 |
| `multiple_charge_word_families`(Φ=4 또는 5) | 71 |
| `no_charge_word_possible` | 0 |

**74개 전부가 최소 하나의 산술적으로 일관된 charge-word를 가진다** —
즉 이 74개 중 어느 것도 `SHORTFALL_BUDGET_THEOREM.md`의 순수 counting
논증만으로는 즉시 배제되지 않는다(당연하다 — 배제됐다면 애초에 74개
목록에 들어오지 않았을 것이다, `j_capacity_extension_profile.json`의
정의상).

## 가장 좁은 3개(Φ=0)

`624257c3...`, `45929408...`, `ad74dbc3...` 세 상태는 **charge-word가
정확히 하나**(빈 multiset, 즉 총 charge 0)뿐이다. 이는:

> **남은 114개 joint 전부가 예외 없이 `ell=5`(완전한 rotation, 무충돌)
> 여야만 완주가 산술적으로 가능하다.**

이 세 상태는 이 문제 전체에서 가장 taut(팽팽)한 지점이다 — 단 한 번의
조기 충돌도 즉시 치명적이다.

## 나머지 71개(Φ=4 또는 5)

`SHORTFALL_BUDGET_THEOREM.md` §5의 family 수(Φ=4→12개, Φ=5→19개) 안에서
어느 family든 가능하다 — 즉 이 71개는 "최대 4(또는5) 단위"의 누적
shortfall까지는 산술적으로 버틸 수 있다. 이는 114개 안팎의 남은 joint에
비하면 여전히 극단적으로 좁다(96% 이상이 여전히 무충돌이어야 한다).

## 분류 등급 요약

- **없음(no_charge_word_possible): 0개** — 이 74개는 정의상 이미
  산술만으로는 배제되지 않는 것들만 모은 목록이므로 당연하다.
- **하나만 가능: 3개** — 완전히 결정된 단일 family(빈 charge, 전부
  full rotation).
- **여럿 가능: 71개** — `SHORTFALL_BUDGET_THEOREM.md`의 유한 family
  카탈로그(12개 또는 19개) 중 하나에 속한다.
- **zero-charge geometry만 미결정, 혹은 potential 외 다른 obstruction
  필요**: 이 두 등급으로 별도 분류하지는 않았다 — 74개 전부가 "charge
  산술은 통과했으나 기하(실제 collision 여부)가 아직 미결정"이라는
  점에서 사실상 전부 이 상태에 있다. `outputs/j_budget_search.json`
  (더 깊은/넓은 bounded 탐색)이 이 미결정 상태를 얼마나 더 좁히는지
  보여준다 — `J_BRANCH_BUDGET_CLOSURE.md` 참고.
