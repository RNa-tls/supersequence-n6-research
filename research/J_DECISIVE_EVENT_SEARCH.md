# J 이후 decisive-event 탐색 (230개 전체, bounded)

산출: `src/search_j_afterstate.py` -> `outputs/j_afterstate_profile.json`.

## 설정

230개 전부에서 각각 독립적으로: macro depth 6까지, 상태당 edge cap 3,000
(총 690,000 edge 상한). 증명된 post-J 알파벳(rotation, `Z2_blocked_w2_existing`,
`Z3_blocked_w3_new`, 최대 1개의 `R`)만 legal로 취급 — abandonment형 edge는
즉시 `would_require_new_abandonment_impossible`로, 두 번째 `R`은
`would_use_second_R_impossible`로 기각한다. **속도를 위해 canonicalize를
생략한 raw 탐색이다** (좌표/개수는 canonical state 수의 상한이지, 정확한
canonical count가 아니다 — left-S6 equivariance는 이미 증명되어 있으므로
raw 탐색이 "어떤 decisive event가 가능한가" 자체를 바꾸지는 않는다).
체크포인트 없음, 새 Area-A 전체 탐색 아님 — 230개 seed 각각에 대한
독립적인 bounded 실험.

## 결과 — **제한 실험 (증명도 반증도 아님)**

```json
{
  "seeds_profiled": 230,
  "seeds_that_hit_edge_cap": 230,
  "completions_found": 0,
  "completions_using_R": 0,
  "completions_not_using_R": 0,
  "max_live_depth_reached_distribution": {"5": 198, "6": 32},
  "terminal_reason_counts_aggregate": {
    "would_require_new_abandonment_impossible": 573899,
    "would_use_second_R_impossible": 14622,
    "remaining_cover_capacity_impossible": 156
  }
}
```

**230개 전부가 edge cap(3,000)에 걸렸다** — 즉 어느 하나도 depth 6
안에서 자연스럽게 (합법 후속 없음, 혹은 완주) 종료되지 않았다. 완주
(`area_a_final`)는 하나도 관측되지 않았다 — 이는 예상된 결과다: 완주까지
남은 joint 수는 (대표 예시 기준) 115개인데, depth 6은 그 20분의 1도 안
된다.

**새로 관측된 것: `remaining_cover_capacity_impossible`가 156회 발생했다**
— **230개 중 45개 seed**에서 이 capacity prune이 depth 5~6 부근에서 최소
한 번 이상 나타났다 (이전 `analyze_j_completion.py`의 depth-4 실험에서는
단 한 번도 나타나지 않았던 것과 대비된다 — 더 깊이 보니 나타난 것으로,
모순이 아니라 depth 4가 그것을 보기에 너무 얕았던 것뿐이다). 나머지
185개 seed는 이 bounded window 안에서 capacity prune을 전혀 만나지
않았다. 45개와 185개를 좌표(P, O)만으로 나눠 봤을 때 깔끔한 분리는
없었다 (두 그룹의 P·O 범위가 겹친다) — 더 깊은 원인 규명은 이번 범위
밖이다.

**해석의 한계.** 이것은:

- J가 완주 불가능하다는 증거가 **아니다** — capacity prune은 이 45개
  seed의 **일부 branch**에서만 발생했고, 같은 seed의 다른 branch는 depth
  6까지 살아남았다(`states_with_only_pruned_children`류 완전 봉쇄는 이번
  집계에 없다 — 개별 seed 전부가 최소 하나의 생존 branch를 가졌다는
  뜻은 아니고, 집계를 좀 더 세밀히 해야 확정할 수 있다. 이 점은 미결정으로
  남긴다).
- capacity prune이 이렇게 이른 depth(5~6)에서 **일부**나마 나타난다는
  것은, 산술만으로는 안 보이던 장애물이 실제로 존재할 수 있음을 시사하는
  최초의 실증적 신호다 — 다만 표본이고 완전하지 않다.

## 다음 단계로 남기는 것

45개 seed 각각에서 capacity prune이 정확히 어떤 (deficit_phase_type,
steps_after_J) 조합에서 발생하는지, 그리고 나머지 branch들이 그 이후
어떻게 되는지는 이번 bounded 실험의 edge cap(3,000) 안에서는 답할 수
없다. 이 45개만 별도로 더 깊은(더 큰 edge cap) bounded 실험을 하는 것이
자연스러운 다음 단계이지만, 이번 작업 범위(새 장기 실행 금지)에서는
수행하지 않는다.
