# J 상태의 global completion demand — 벡터 potential

범위: J 대표 상태(230개 중 `deficit_phase_type=(1,3)`인 유일한 예시,
`P=6,F=1,S=3,H=0,O=2,D=4,N=2`) 하나에 대한 정확한 산술. 산출:
`src/analyze_j_completion.py::post_j_budget` -> `outputs/j_completion_analysis.json`
(`post_J_budget_theorem` 필드).

## 1. 벡터 potential 정의

\[
\Phi = (\Phi_O,\ \Phi_D,\ \Phi_N,\ \Phi_P)
\]

- \(\Phi_O\) = orbit demand = `TARGET_O - O` = 남은 신규 E-orbit 필요 수
- \(\Phi_D\) = phase/D demand = `TARGET_D - D` (D=5O-P 항등식으로부터
  파생, 남은 joint의 신규/기존 orbit 비율을 강제)
- \(\Phi_N\) = 남은 N 여유 = `TARGET_BUDGET - H - Ndef`
- \(\Phi_P\) = 남은 전체 joint 수 = `TARGET_P - P`

대표 상태에서: \(\Phi_O=23,\ \Phi_D=0,\ \Phi_N=1,\ \Phi_P=115\).

## 2. 단조성과 cone order

각 non-rotation joint 유형이 \(\Phi\)에 미치는 영향 (전부 §1의 정의와
`exact.py`의 정의로부터 정확히 유도, 탐색 불필요):

| joint | \(\Delta\Phi_O\) | \(\Delta\Phi_D\) | \(\Delta\Phi_N\) | \(\Delta\Phi_P\) |
|---|---:|---:|---:|---:|
| `Z3_blocked_w3_new` | -1 | -4 | 0 | -1 |
| `Z2_blocked_w2_existing` | 0 | +1 | 0 | -1 |
| `R_blocked_w3_existing` | 0 | +1 | -1 | -1 |
| (모든 abandonment형) | — | — | — | 봉쇄됨 (정리 J-1) |

(\(\Delta\Phi_D\)의 부호는 \(\Phi_D=\text{TARGET\_D}-D\)이고 신규-orbit
joint가 \(D\)를 +4, 기존-orbit joint가 \(D\)를 -1시키므로 그 반대 부호.)

**cone 관찰:** \(\Phi_P\)는 매 non-rotation joint마다 정확히 -1로
**엄격히 단조 감소**한다 (예외 없음 — 모든 non-rotation joint가 P를
정확히 1 늘리므로). 이것이 유일하게 항상 성립하는 단조성이다.
\(\Phi_O,\Phi_D,\Phi_N\)은 어떤 joint 조합을 택하느냐에 따라 서로 다른
속도로 줄어들며, 셋을 동시에 0으로 맞추는 문제(§3)가 정확히 이 slab의
핵심 난제다.

**lexicographic order로 단조 감소하는 단일 스칼라는 찾지 못했다** — 이는
사용자가 미리 배제하라고 명시한 "budget 자체를 제외한 비자명한 후보"
탐색이 (이전 세션 기록, `outputs/FOREST_FAILURE_ARCHETYPES.md` 부근 서술
참고) 이미 실패했다는 사실과 일치한다. 이번 작업도 새로운 스칼라 potential을
찾지 못했다 — **추측조차 제시하지 않는다.**

## 3. 필요조건: required future cost ≤ available future budget

세 개의 남은 자원 방정식을 동시에 풀어야 한다.

\[
\begin{aligned}
n_3 &= \Phi_O = 23 &&\text{(Z3 개수, 강제로 정확히 이 값)}\\
n_2 + n_R &= \Phi_P - n_3 = 92 &&\text{(기존-orbit joint 총수)}\\
n_R &\le \Phi_N = 1 &&\text{(N 예산)}\\
4n_3 - (n_2+n_R) &= \Phi_D = 0 &&\text{(D 항등식, 자동 충족: }4\cdot23-92=0\text{)}
\end{aligned}
\]

이 방정식계는 **일관적이다** (\(n_3=23,\ n_2\in\{91,92\},\ n_R\in\{1,0\}\)).
즉:

> **required future cost (산술 기준) > available future budget은 이 예시에서
> 성립하지 않는다.** 산술만으로는 모순이 없다.

이것이 `J_COMPLETION_OBSTRUCTION.md` §6에서 후보 A·B를 "미결정/근거 없음"
으로 판정한 근거다. 산술 potential로는 J를 배제할 수 없고, 배제하려면
**기하적** 논증(어느 순열이 실제로 몇 번째 joint에서 방문 가능한가, 즉
충돌 회피)이 필요하다.

## 4. 다른 229개 상태에 대해

이 절 전체는 §0(대표 상태)에 대한 것이다. 나머지 229개는 각자 다른
\((P,F,S,H,O,D,N)\) 좌표를 가지며 (예: `deficit_phase_type`이 다르면
좌표도 다르다), 그 좌표들은 이 코퍼스에 저장되어 있지 않다
(`J_NORMAL_FORMS.md` §0 참고). 따라서 이 절의 구체적 수치(23, 92, 1)는
**대표 상태 하나**에 대한 것이고, 일반적인 J 상태에 대한 주장으로 확대할
수 없다. 다만 §2의 정성적 구조(단조 감소하는 \(\Phi_P\), 세 방정식의
형태, `R` 최대 1회라는 제약)는 **모든** J 상태에 대해 정리 J-1·J-2로부터
동일하게 성립한다 — 그 부분은 일반적이다.
