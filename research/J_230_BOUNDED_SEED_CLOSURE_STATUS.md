# 230개 J seed(depth-6 bounded) 종합 폐쇄 상태

## 최종 표

| Seed | Word families | Fully exhausted | Success | Status |
|---|---:|---:|---:|---|
| 221개 (`outputs/j_budget_search.json` + 이전 라운드에서 실패 발견) | — | 해당 없음(일부 branch 실패 확인) | 0 | **일부 branch 실패 확인됨** (seed 전체 CLOSED 아님, §주의 참고) |
| 남은 9개(`research/J_9_SEED_LEDGER.md`) | 1~19 | **아니오** (canonical BFS, node cap 800, 전부 INCOMPLETE) | 0 | **INCOMPLETE** |

**9개 전부 CLOSED가 아니므로**, 아래 boxed 문장은 쓸 수 없다:

> ~~imported bounded J seed set 230개 전체가 exact continuation search에서
> 실패했다.~~ ← **쓸 수 없음. 9개가 INCOMPLETE로 남아 있다.**

## 반드시 구분해야 할 두 개의 다른 주장

1. **"이 seed에서 어떤 branch가 Φ<0에 도달한다."** — 221/230에 대해
   확인됨(`outputs/j_budget_search.json`, `outputs/j_capacity_extension_profile.json`,
   `outputs/j_capacity_45_seeds.json`).
2. **"이 seed의 모든 branch가 결국 실패한다(=이 seed 자체가 완주
   불가능하다)."** — **어느 seed에 대해서도 아직 증명되지 않았다.** 221개도
   "적어도 하나의 branch가 실패"만 확인한 것이지, "모든 branch가
   실패"를 보인 게 아니다. 9개 남은 seed에 대한 이번 exhaustive 시도가
   바로 2번을 겨냥한 것이었고, canonical state 공간이 너무 커서(§
   `J_9_EXACT_CLOSURE.md`) node cap 800에서 전부 INCOMPLETE로 끝났다.

**따라서 엄밀히 말하면, 이번까지의 모든 작업에서 단 하나의 J seed도
"완주 불가능"이 증명되지 않았다** — 221개에 대해서도 마찬가지다. 이는
지금까지의 요약들이 종종 함의했을 수 있는 것보다 더 보수적인
결론이며, 명시적으로 바로잡는다.

## 이번 작업에서 실제로 확립된 것

- **증명됨:** Φ 잠재량과 그 단조성, 완주 경계조건(수정된 버전),
  charge-word의 유한 분류.
- **유한 완전 검증:** 230개 전부의 literal witness, 독립 재생, Φ 계산;
  45개(그리고 확장하여 65개 더, 총 221/230 branch 수준)의 최소 실패
  경로.
- **제한 실험:** 221/230 branch-level 실패 관측; 9개 seed의 canonical
  exhaustive 시도(모두 INCOMPLETE).
- **미완료(실패 아님):** 9개 seed의 seed-level closure. canonical
  state 수가 node cap 800에서도 계속 늘어나(merge 조짐 없음) 완전
  탐색이 이번 세션 규모를 넘어선다.
- **범위를 벗어나 확대하지 않음:** 230개는 `AreaAConfig(n_limit=3,
  max_macro_depth=6)` bounded 탐색에서 나온 특정 frontier일 뿐이다.
  이 230개(또는 그 부분집합)에 대한 어떤 결론도 F=1,H=0 slab 전체나
  n=6 초순열 하한(`L_6`)에 대한 일반 정리로 확대하지 않는다.

## 다음 단계

- `src/search_j_9_exact.py`는 checkpoint/resume을 지원한다 — 다음
  세션에서 훨씬 더 큰 node cap(수만~수십만)으로 이어서 실행하는 것이
  가장 직접적인 다음 걸음이다.
- 그전에, "일부 branch 실패"와 "전체 seed 실패"의 간극(위 §"반드시
  구분해야 할 두 주장")을 메우는 것이 canonical exhaustive search보다
  더 근본적인 다음 이론적 과제일 수 있다 — 예컨대 "이 seed의 모든
  legal branch가 유한 depth 안에 Φ<0에 도달한다"는 것을 개별 branch가
  아니라 **전체 subtree에 대한 귀납**으로 보이는 방법을 찾는 것.
