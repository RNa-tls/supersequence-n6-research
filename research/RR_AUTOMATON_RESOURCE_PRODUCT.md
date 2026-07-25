# Automaton × resource product (라운드 23)

산출: `src/build_rr_automaton_resource_product.py` ->
`outputs/rr_automaton_resource_states.json`.

## 17-18. Resource 좌표 ablation

라운드22의 26-state symbolic automaton에 최소 resource 좌표를 하나씩
곱했다(depth ceiling 5, root-local):

| resource 좌표 | ell=0 상태/전이 | ell=4 상태/전이 |
|---|---|---|
| (없음) | 26 / 97 | 26 / 87 |
| `r_count` | 26 / 97 | 26 / 87 |
| `fresh_count`(≤3로 절단) | 66 / 207 | 62 / 161 |
| `o_star_phase_mask`(\(O_*\)의 방문 phase 수) | 42 / 127 | 40 / 108 |
| `hub_residual`(hub 방문 위치 수) | 26 / 97 | 26 / 87 |
| `r_count`+`o_star_phase_mask` | 42 / 127 | 40 / 108 |
| 넷 전부 | **98 / 243** | **84 / 184** |

**관찰**:

- `r_count`와 `hub_residual`은 **quotient를 전혀 세분하지 않는다**
  (상태·전이 수 불변) — 이미 base state가 그 정보를 담고 있다는 뜻.
  §18이 요구한 최소 quotient 관점에서 **둘 다 제거 가능**하다.
- 실제로 세분하는 것은 `fresh_count`와 `o_star_phase_mask` 둘뿐이다.

## 6. 등급 — 정확해지지 **않는다**

> **어떤 좌표 조합도 exact automaton을 만들지 못한다.**
> 위 좌표 중 어느 것도 **전체 방문 마스크**를 담지 않으므로,
> 곱은 false-positive 집합을 **줄일 뿐** 없애지 못한다.
> 전 조합 **sound over-approximation**으로 표기한다.

지시(§18: "상태 수가 커져도 exactness를 과장하지 마라")에 따라
exactness는 **주장하지 않는다.** \(L_{\text{exact}} =
L_{\text{automaton}} \cap L_{\text{resource}}\) 형태의 분해에서
\(L_{\text{resource}}\)를 유한 상태로 포착하려면 방문 마스크의
어떤 유한 quotient가 충분한지 알아야 하는데, 그것은 규명하지
못했다 — **미완료.**

**성공 기준 5 평가: 부분 달성** — 최소 quotient 방향(제거 가능한
좌표 2개 식별)은 얻었으나, exact product는 얻지 못했다.
