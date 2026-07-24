# Orbit-demand matching, existing-target automaton, family-local 검증 결정

산출: `src/analyze_ra2_orbit_demand.py` -> `outputs/ra2_orbit_demand_analysis.json`,
`outputs/ra2_existing_target_automaton.json`.

## 8. Orbit-demand bipartite/Hall-type obstruction — 시도, 제한적 결과만

전체 완주 문제를 완전한 bipartite matching으로 모델링하는 것은
"남은 모든 미완료 hexagon/phase/fragment 의무"(수백 개) 대 "남은 모든
legal target slot"(마찬가지로 수백 개)을 요구하며, 이는 사실상 전체
완주 탐색과 같은 규모다 — 이번 라운드의 "새 대규모 전체 탐색 금지"
제약과 정면으로 충돌한다. 따라서 **가장 작은 demand set(fragment
hole 하나)만 모델링했다:**

- demand set \(X\) = {fragment의 유일한 미방문 윈도우}
- neighborhood \(N(X)\) = 이미 발견된 repair witness 집합
  (`FRAGMENT_REPAIR_OBLIGATION.md`에서 상태당 11~15개 발견)

**Hall 조건 \(|N(X)|\ge|X|\)는 4개 상태 전부에서 자명하게
성립한다**(11~15 ≥ 1) — 위반 subset을 찾지 못했다.

**정직한 범위 한계**: 이는 "가장 쉬운 demand 하나가 매칭 가능하다"는
것만 보여줄 뿐, 전체 완주에 필요한 수백 개 demand 전부에 대한
matching 존재를 증명하거나 반증하지 않는다. **미완료로 명시한다** —
"obstruction을 찾지 못했다"를 "obstruction이 없다"로 과장하지
않는다.

## 10. Existing-target branch automaton — U4 분류

요청된 7-튜플 automaton 대신(`RA2_ONE_HOLE_LEMMA.md` §7과 같은 이유로
개별 상태 지오메트리가 공유되지 않음), U4를 요청된 5가지 분류
카테고리 중 하나로 최종 배치한다:

- 즉시 불가능? → 아니다.
- repair 후 불가능? → 아니다(repair는 항상 legal 필요조건을 통과함,
  `RA2_ONE_HOLE_LEMMA.md` H1 반증).
- 특정 fresh-opening word 필요? → 이 라운드가 시도한 어떤 조건도
  이를 뒷받침하지 못했다(§4, §6, §7 전부 non-binding 또는 정의
  불안정).
- 소수 exact subcase로 환원? → 이미 이전 라운드에서 "4개 독립
  상태"로 최대한 환원됐고, 이번 라운드는 그 이상의 세분화를 만들지
  못했다.
- **여전히 대형 geometry search가 필요함** → **이것이 가장 정직한
  분류다.** 이번 라운드가 시도한 국소적 obstruction(ρ_A, Hall-type,
  H2a-d, Λ)이 전부 non-binding이거나 반증됐으므로, ell/novelty
  기반 국소 지오메트리 논증으로는 U4를 더 좁히지 못한다는 것이
  이번 라운드의 핵심 결론이다.

## 11. Family-local 검증 — 수행하지 않음(원칙에 따름)

이번 라운드에서 검증된 새 obstruction이나 abstraction이 없으므로
(모든 후보가 non-binding 또는 반증), 요청의 명시적 지침("새
obstruction 또는 potential이 나온 뒤에만 검증하라", "30% 미만
개선이면 cap을 늘리지 마라")에 따라 **U4에 대한 추가 대규모
family-local 재탐색을 수행하지 않는다.** §3, §8에서 수행한 소규모
검증(전역 orbit credit 평가, hole demand Hall 체크)이 이번 라운드의
실질적 탐색 전부다.

## 성공 기준 (3), (5) 재확인 — 미달성

"U4를 제거하는 orbit-demand 또는 Hall-type obstruction"(3)과 "U4를
유한한 existing-target subcase로 완전 환원"(5) 둘 다 **미달성**이다.
이번 라운드는 성공 기준 (1)(가능한 (ℓ,ν) truth table)만 명확히
달성했고, 나머지는 시도했으나 일관되게 non-binding/반증되는 패턴을
확인했다 — 이는 "existing-target abandonment"라는 축 자체가 이
지점에서 유용한 새 obstruction의 원천이 아니라는, 정직한 음성
결과다.
