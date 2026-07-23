# Minimum future shortfall 하한 시도 — 정직한 음성 결과

## 목표와 결과 요약

목표: \(m_{LB}(S)>0\)인 비자명한 하한을 찾아 \(m_{LB}(S)>\Phi(S)\)이면
즉시 불가능하다고 판정하는 강화된 안전 prune을 얻는 것.

**결과: 순수 (P, visited_count) counting relaxation 안에서는
\(m_{LB}(S)=0\)이 이미 타이트하다 — 즉 \(\Phi(S)\ge0\) 자체가 이
relaxation이 낼 수 있는 가장 강한 조건이며, 더 강화할 수 없다.**
(`SHORTFALL_BUDGET_THEOREM.md` §3에서 증명, 처음의 틀린 "Φ≥5" 시도와
그 정정 과정 포함.)

## 시도한 relaxation들과 그 결과

| relaxation | 결과 |
|---|---|
| 남은 permutation 수 (`720-visited`) | 이미 Φ의 정의에 포함됨 — 새 정보 없음 |
| 남은 path/pass-start 수 (`TARGET_P-P`) | 이미 Φ의 정의에 포함됨 |
| 남은 신규 orbit 수 (`TARGET_O-O`) | Φ에는 안 들어가지만, 이미 별도 prune(`insufficient_future_orbit_opening_credit`)으로 존재하고, post-J(F 예산 소진) 상황에서는 자동으로 만족됨(`n_new<=n`은 항상 성립) — Φ보다 타이트한 조건을 추가로 주지 못함 |
| unfinished hexagon arc / split completion | fragment/current component 정보는 Φ와 독립이지만, 이를 정량적 하한으로 바꾸는 공식을 찾지 못했다 |
| fragment completion | 위와 동일 |
| phase deficit (D) | `D=5O-P` 항등식은 Φ와 **선형 종속**이다(§`SHORTFALL_BUDGET_THEOREM.md`의 charge 표에서 신규-orbit joint가 D에 +4, 기존-orbit joint가 -1을 주는 것과 Φ의 정의가 같은 뿌리에서 나옴) — 독립된 새 제약을 주지 않는다 |
| required strand count (S) | `S`는 weight>=3 joint 수를 세는 파생량이며, `n`(Φ에 이미 포함)과 직접 연동돼 새 정보를 주지 않는다 |

## 결론

- 위 relaxation들 중 어느 것도 Φ보다 엄격한 새로운 산술적 하한을 주지
  못했다 — **반증됨**(단순한 추가 산술 하한이 존재한다는 가설).
- 강화하려면 순수 counting을 넘어서는 정보, 즉 **구체적으로 어떤
  hexagon/orbit이 이미 부분적으로 방문됐고 그것이 향후 rotation run의
  \(\ell_{\max}\)를 어떻게 제한하는가**(기하적 사실)가 필요하다. 이는
  이번 작업 범위 밖이며, 사실상 원래의 exact-state exhaustive search
  문제 그 자체로 돌아간다.

## Vector potential 시도 — **반증됨/근거 없음**

\(\Psi=(\Phi,\ \text{orbit slack},\ \text{phase slack},\ \text{split
slack},\ \text{fragment slack})\)을 시도했다.

- `orbit slack` := \(TARGET_O-O\): Φ와 함께 감소하지만, 위에서 보인
  대로 Φ에 종속적이며 독립적인 단조성을 추가하지 않는다.
- `phase slack`(D 기반): 역시 Φ와 선형 종속.
- `split slack`, `fragment slack`: 정량적 정의 자체를 얻지 못했다 —
  fragment/current component "모양"은 있지만 이를 스칼라 slack으로
  바꿀 표준적 방법을 찾지 못했다.

**componentwise nonincrease, lexicographic order, cone 판정 중 어느
것도 비자명하게 성립시키지 못했다** — 임의로 맞춘(fitted) potential을
정리로 선언하지 않는다는 지시에 따라, 이 시도는 여기서 **음성
결과로만** 기록한다. 기존 `J_FUTURE_DEMAND_BOUND.md`에서 이미 관측된
것과 같은 결론이다: 이 문제의 벡터 potential은 (있다면) 아직
발견되지 않았다.
