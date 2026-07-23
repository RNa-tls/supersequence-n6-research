# 상태 폭발 원인 분석과 forced-ell lemma

산출: `src/analyze_j_state_growth.py` -> `outputs/j_branching_profile.json`.

## 1. Depth별 분해 — **완전 계산 (depth 0–3, 9개 seed 전부)**

9개 seed 전부에서 depth 0부터 3까지 정확히 측정했다. 대표 예시(Φ=0
seed `45929408...`):

| depth | 생성 child | legal child | canonical unique | exact duplicate | distinct endpoint | distinct visited_count | avg branching |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 22 | 4 | 4 | 0 | 4 | **1** | 4.0 |
| 1 | 91 | 14 | 14 | 0 | 4 | **1** | 3.5 |
| 2 | 301 | 46 | 46 | 0 | 4 | **1** | 3.29 |
| 3 | 988 | 149 | 149 | 0 | 4 | **1** | 3.24 |

(9개 전부 같은 패턴 — 정확한 수치는 `outputs/j_branching_profile.json`.)

## 2. Frontier가 왜 ~3배씩 자라는가 — **원인 규명됨**

1. **`exact_duplicate_children`가 이 depth 범위(0–3) 전체에서 정확히
   0이다** — canonicalization이 이 얕은 깊이에서는 전혀 병합 효과를
   내지 못한다. 3배 성장은 순수하게 **branching factor 자체**(평균
   3.2~4)이지, 중복 생성 후 뒤늦게 합쳐지는 게 아니다.
2. **`distinct_visited_counts_among_children`가 매 depth에서 정확히
   1이다** — 즉 어떤 상태의 모든 legal child가 **정확히 같은
   visited_count**를 갖는다. 이는 §3의 forced-ell lemma의 직접적
   결과다: 이 seed들(Φ=0)의 경우 다음 §3에서 증명하듯 `ell=5`가
   완전히 강제되므로, 어떤 joint를 고르든 방문 windows 수(`ell+1=6`)가
   동일하다.
3. **`distinct_endpoints_among_children`가 4로 depth와 무관하게
   일정하다** — 성장은 "더 많은 서로 다른 끝점"에서 오는 게 아니라,
   **어떤 orbit을 목표로 하는가**(Z2 대 Z3, 그리고 어떤 특정
   기존/신규 orbit인가)라는 **joint-target 선택**에서 전적으로 온다.
4. `would_require_new_abandonment_impossible`가 압도적 다수(depth
   3에서 988개 시도 중 823개)를 차지한다 — 이는 이미 증명된 정리
   J-1(abandonment 예산 소진)의 직접적 반영이며 새로운 정보는 아니다.

> **요약: 상태 폭발은 rotation-length 다양성이 아니라 joint-target
> 다양성에서 온다.** ell은 (Φ=0 seed에서는 완전히, 다른 Φ에서는
> 부분적으로) 강제되지만, "어느 orbit으로 점프할 것인가"는 강제되지
> 않는다.

## 효과 평가 — 성공 기준 미달, 정직하게 기록

| 방법 | unique state (depth 3, 대표 seed) | baseline 대비 |
|---|---:|---|
| baseline(정리 없음) | 149 | — |
| forced-ell lemma 적용 | 149 (동일) | **0% 감소** — ell 차원만 없앨 뿐 joint-target branching은 그대로 |
| dominance A/D/E | 적용 불가(미결정, `J_DOMINANCE_RULES.md`) | 해당 없음 |
| dominance B/C | 반증됨(`J_DOMINANCE_RULES.md`) | 사용 불가 |

**어떤 방법도 50% 이상 unique frontier를 줄이지 못했다** — 사실
forced-ell lemma는 rotation-length 자유도만 제거할 뿐 canonical state
수 자체는 전혀 줄이지 않는다(모든 child가 이미 서로 다른
joint-target을 가져 canonical하게 구별됐으므로). 이는 성공 기준 미달의
**정직한 음성 결과**다 — 억지로 성공을 주장하지 않는다.

## 3. Forced-ell lemma — **증명됨 (일반적, Φ=0에 국한되지 않음)**

Φ 단조성 항등식 \(\Phi(S')=\Phi(S)+(\ell-5)\)로부터, 다음 걸음이
합법(즉 \(\Phi(S')\ge0\))이려면:

\[
\ell \ge 5-\Phi(S).
\]

| \(\Phi(S)\) | 강제되는 \(\ell\) 범위(다음 한 걸음) |
|---:|---|
| 0 | \(\{5\}\) — **완전히 강제** |
| 1 | \(\{4,5\}\) |
| 2 | \(\{3,4,5\}\) |
| 4 | \(\{1,2,3,4,5\}\) |
| 5 | \(\{0,1,2,3,4,5\}\) — 제약 없음 |

9개 seed 중 3개(Φ=0)는 **모든 남은 걸음에서 ell=5가 계속 강제된다**
(Φ가 그 값을 유지하는 한 — 실제로 ell=5를 쓰면 Φ는 변하지 않으므로,
한 번이라도 ell<5를 쓰지 않는 한 Φ=0이 계속 유지되고 따라서 ell=5가
계속 강제된다). §1의 관측(`distinct_visited_counts=1`)이 바로 이
사실의 직접적 증거다.

**이 lemma는 rotation-length 차원의 branching은 없애지만, 앞서
`outputs/j_branching_profile.json`이 보이듯 joint-target 차원의
branching(3~4가지)은 전혀 줄이지 못한다** — 이것이 왜 이 lemma만으로는
상태공간이 유의미하게 줄지 않는지에 대한 정직한 이유다.
