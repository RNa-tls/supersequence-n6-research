# Same-component 10개 exact closure 시도 — INCOMPLETE

산출: `src/search_rr_same_component.py` -> `outputs/rr_same_component_exact_search.json`.

## 11. Exact closure 시도 결과

새 hub lemma(`RR_HUB_TOUCH_COUNT.md`) + Φ=0 제약
(`RR_PHI_ZERO_CONTINUATION.md`)을 적용한 뒤, 10개 same-component
witness 각각의 R2 직후 상태에서 bounded exact search를 실행했다.

허용: `area_a_prune_reason`을 통과하는 모든 legal macro-edge(F≤1
예산이 이미 자동으로 ell<5, 3번째 hub touch, N budget 위반 등을
prune함 — 별도 prune 로직 불필요, 기존 `area_a_prune_reason`이
이미 이 모든 조건을 포함).

```
python3 src/search_rr_same_component.py --node-cap 30000
```

| witness | Φ | nodes_expanded | exhaustive | success | terminal_reasons(주요) |
|---|---:|---:|---|---|---|
| 전체 10개 동일 패턴 | 0 | 30,000(cap 도달) | **False** | **False** | F_exceeded(~52만), N_exceeded_monotone(~1.8만), no_legal_children(93-119) |

**10개 전부 node_cap(30,000)에 도달했고, frontier가 소진되지
않았다(exhaustive=False) — 완주 성공도, 완전한 실패(모든 가지가
dead-end)도 확인하지 못했다.** 이는 이 project의 이전 라운드들이
반복적으로 마주한 것과 같은 패턴이다(예: RA2의 U4 4개 상태는
depth≤18/edge_cap=1.5M까지도 미해결로 남았다) — orbit slack=23이
이미 U4/C20 상태들과 비슷한 규모이므로, 같은 종류의 난이도가
예상된 결과였다.

**정직한 표시: INCOMPLETE.** "완주 불가능"이라고 결론 내리지
않는다 — `no_legal_children`으로 종료된 가지가 93-119개
있었지만(이는 진짜 dead-end), 30,000개 중 나머지 대다수는 단순히
탐색이 못 미친 것(cap 도달)이지 실패로 판정된 것이 아니다.

## 13. Separate-component branch 대비 — 통계만, 새 탐색 없음

`RR_BRANCH_DECOMPOSITION.md`(라운드 12)에서 이미 확립한 분리를
재확인하고 요약한다(재계산 없이 기존 `outputs/rr_full_relation_table.json`,
`outputs/rr_chain_cost_analysis.json` 재사용).

| | Chain branch (75) | 그중 same (10) | 그중 different (65) | Separate branch (4,395) |
|---|---:|---:|---:|---:|
| component 관계 | same 또는 different | same | different | 반드시 different |
| κ_chain(Φ) 평균 | — | **0** | 4.91 | 3.68 |
| hub 관여 | 일부(10/75) | 항상(hub 존재+completer=ftgt orbit) | 대부분 hub 무관 | 없음(hub 개념 자체가 무관 — non-chaining이면 hub 존재 여부가 same 여부에 영향 없음) |
| 다음 obstruction 우선순위 | same(10개)가 유력 후보, 그러나 §11에서 INCOMPLETE로 남음 | (위 참고) | 우선순위 낮음(Φ 여유 큼) | 미결정, 개별 편차 큼(Φ 범위 0-6) |

**이번 라운드에서 separate branch(4,395개) 전체에 대한 새 탐색은
수행하지 않았다**(지시대로) — 이는 다음 라운드의 과제로 남긴다.
same-component(10개) closure가 §11에서 INCOMPLETE로 남았으므로,
"RR은 different-component branch만 남는다"는 corollary는 **아직
활성화되지 않았다** — same-component가 완주 불가능함이 확정돼야
비로소 이 corollary가 의미를 갖는다.
