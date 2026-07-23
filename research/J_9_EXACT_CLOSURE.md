# 9개 seed exact closure 시도 — 결과와 그 이유

산출: `src/search_j_9_exact.py`(canonical-memoized exhaustive search
엔진), 프로파일링 결과.

## 설계 결정: charge-word별 subproblem 분할을 하지 않았다

지시된 "seed × charge-word family" 단위의 독립 subproblem(`J9-S03-W07`
류 ID) 대신, **seed당 하나의 canonical-memoized 탐색**을 구현했다.
이유: 어떤 상태의 남은 Φ는 그 canonical `(P, visited_count)`만으로
완전히 결정되며, **서로 다른 charge-word 이력을 거쳐 같은 canonical
상태에 도달한 두 경로는 이후가 완전히 동일하다.** charge-word별로
탐색을 쪼개면, 서로 다른 word에서 수렴하는 바로 그 canonical state를
중복으로 재탐색하게 되어 canonical memoization의 이점을 스스로
없앤다. 대신 하나의 통합 탐색이 `area_a_prune_reason` + Φ 검사를 통해
**모든** legal charge-word를 동시에 올바르게 반영한다 — 각 상태가
어떤 charge-word 경로로 왔는지는 메타데이터로만 기록했다.

## 실행 결과 — **미완료 (증명도 반증도 아님)**

9개 seed 전부에서 canonical-memoized BFS를 node cap 800(첫 프로파일링,
seed당 약 37~39초)으로 실행했다. **9개 전부 `INCOMPLETE`**다:

| seed(16자) | expanded | canonical 기록 | frontier 잔여 | 경과(초) | 상태 |
|---|---:|---:|---:|---:|---|
| `45929408de25b866` | 800 | 2437 | 1637 | 37.5 | INCOMPLETE |
| `624257c39b75859d` | 800 | 2468 | 1668 | 38.7 | INCOMPLETE |
| `6b42cfe0deafcfa4` | 800 | 2465 | 1665 | 37.3 | INCOMPLETE |
| `ad74dbc3a5f5c987` | 800 | 2440 | 1640 | 37.8 | INCOMPLETE |
| `c652843b153b6c7b` | 800 | 2474 | 1674 | 38.4 | INCOMPLETE |
| `e0f8ed14b4832a72` | 800 | 2448 | 1648 | 39.7 | INCOMPLETE |
| `eaa42caf37c5f6ad` | 800 | 2461 | 1661 | 39.5 | INCOMPLETE |
| `f4e71fe28ebaa10b` | 800 | 2446 | 1646 | 37.9 | INCOMPLETE |
| `f95ab0147fb90de8` | 800 | 2440 | 1640 | 38.2 | INCOMPLETE |

전체 9개 모두 완료했다(더 이상 "본문 참고"로 남겨둘 데이터 없음).
`outputs/j_9_subproblem_profile.json`, `outputs/j_9_exact_search.json`에
동일한 데이터가 있고, `src/verify_j_9_certificates.py`가 9개 전부의
status/frontier 일관성과 prune 사유의 안전성을 재확인했다(9/9 PASS,
`outputs/j_9_certificates.json`).

**핵심 관측: frontier가 이 규모(800 canonical node)까지 계속
자란다(비율 약 3배) — `canonical_memo_duplicate` prune이 이 depth
범위에서 사실상 발생하지 않는다.** 즉 서로 다른 canonical state가
계속 새로 발견되고 있다는 뜻이며, 아직 "합쳐지기 시작하는" 지점에
도달하지 못했다.

## 왜 이 규모의 exhaustive search가 이번 세션에서 불가능한가

- canonical화 비용(720-relabel/state) 때문에 초당 약 20개 canonical
  node만 처리된다.
- 남은 joint 수는 114~115개, 매 상태마다 legal transition이 3~4개다.
- 800 node에서도 merge 징후가 없다는 것은, **진짜 도달 가능한
  canonical state 수가 수만~수십만(혹은 그 이상) 단위일 가능성**을
  시사한다.
- 이 속도로 그 정도 규모를 완전히 소진하려면 수 시간~수십 시간의
  연속 계산이 필요하다 — 이는 이번 세션의 실현 가능한 범위를 넘는다.

## 정직한 결론

> **9개 seed 중 어느 것도 이번 작업에서 CLOSED로 판정되지 않았다.**
> 전부 INCOMPLETE다 — 이는 실패도 성공도 아니며, "아직 답을 모른다"는
> 뜻이다. 이를 실패로 기록하지 않는다(지시대로). 완전 탐색을 계속하려면
> 훨씬 더 긴(다중 세션, 체크포인트 기반) 계산이 필요하다는 것이 이번
> 프로파일링의 실질적 결론이다.

`src/search_j_9_exact.py`는 checkpoint/resume을 지원하도록 만들어져
있으므로, 향후 세션에서 그대로 이어서 실행할 수 있다.
