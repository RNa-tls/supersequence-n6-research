# A2R 최소-depth 정리

산출: `src/search_a2r_minimum_depth.py` -> `outputs/a2r_minimum_witnesses.json`
(이전 라운드가 발견한 depth-6 witness의 재확인 + 최소 depth에서의
**유일성** 검증 — depth<=6 bound 안에서의 bounded 재탐색, 새 대규모
탐색 아님).

## 결론 먼저

> **A2R의 정확한 최소 macro-depth는 6이다. 이 depth에서 canonical
> witness는 정확히 1개(유일)다. 이는 depth<=6 전체에 대한 유한 완전
> 검증이다(frontier가 node cap 도달 전에 완전히 소진됨).**

## 판정 결과

`find_all_a2r_at_min_depth`(raw BFS, depth<=6, node_cap=400,000,
"정확히 A2 다음 R"인 이벤트열만 추적): **2,853개 노드만에 frontier가
완전히 소진**됐다(node cap에 도달하지 않음) — 이는 depth<=6 전체에
대한 완전한 exhaustive 탐색이다. 결과: **최소 depth=6에서 정확히
1개의 raw witness, canonical화 후에도 1개**(중복 없음).

## 왜 A2R은 RA2보다 늦게 나타나는가 — 정량적 설명

`RA2_A2R_EXCHANGE_THEOREM.md`에서 확립한 사실을 재사용한다:

- **R이 walk의 첫 counted 이벤트로 등장 가능한 최소 index는 0**
  (24개 RA2 코퍼스 중 1개가 r_idx=0을 보임 — 실제 도달 사례).
- **A2가 walk의 첫 counted 이벤트로 등장 가능한 최소 index는 4**
  (depth 5에서 처음 등장, 이전 라운드 및 이번 라운드 재확인 둘 다
  일치).

이 비대칭의 원인(§`RA2_ORBIT_REUSE_CHARGE.md`, 이전 라운드 자료
재사용): A2(weight=2, existing target)가 "existing" 조건을
만족하려면 walk 초반에 touched된 orbit이 더 많아야 legal한
weight-2 abandoning move가 생긴다 — 초기 상태에서는 정확히
1개의 orbit(초기 permutation 자신의 orbit)만 touched돼 있고, 이
시점에는 weight-2 existing-target 이동 자체가 legal하지 않다(이번
및 이전 라운드에서 직접 계산으로 확인: 초기 상태에서 legal
weight-2 abandoning existing-target move는 0개). R(weight=3,
existing target)은 같은 초기 상태에서도 (일부 경우) 이미 legal한
경우가 있다 — 이는 weight-2와 weight-3 tail action 집합이 서로
다른 조합적 구조를 가진다는 사실의 직접 결과다.

**A2R의 최소 depth 6**은 이 A2-먼저 최소 준비(depth 5, index 4)에
그 뒤 R을 위한 최소 1 추가 macro-edge(R 자신의 조인트)를 더한
것과 정확히 일치한다: **depth(A2R) = depth(A2-first-min, 5) + 1(R
자신의 edge) = 6.** 이는 우연이 아니라, A2가 먼저 등장하는 순간
그 이후 R이 "가장 빠르게" 뒤따를 수 있는 최소 조건(1 macro-edge)이
정확히 충족되기 때문이라는 것을 시사한다(**손증명은 아니고, 두
독립적으로 확립된 사실의 산술적 일치로부터의 강한 추측** — depth(A2-first-min)+1이
정확히 A2R의 진짜 최소와 일치하는 것을 더 깊이 증명하려면 "A2 이후
정확히 1 edge 만에 R이 legal해진다"는 것을 별도로 보여야 하는데,
이는 실제 depth-6 witness의 macro_path 마지막 스텝이 정확히 R임을
확인하는 것으로 뒷받침된다 — `outputs/a2r_search.json`의 기존
witness가 정확히 이 패턴이다).

## 준비 joint 수와 필요 조건

A2 이후 R이 legal해지기 위한 최소 준비 joint 수: 이전 라운드의
witness(`A2_ROTATION_LENGTH_CLASSIFICATION.md`, `outputs/a2r_search.json`)에서
정확히 **R은 A2 직후 바로 다음 macro-edge에서 legal**했다(추가
준비 0개) — A2가 남긴 새 current hex(fresh, mask=1)에서 R이 곧바로
발동 가능했다는 뜻이며, 이는 R이 요구하는 "existing target"이 A2
자신이 방금 만든 새 orbit-touch 이력만으로 충분히 만족됐음을
보여준다.

## 성공 기준 (2) 평가

"A2R의 정확한 최소-depth 정리"는 **달성됐다**: 최소 depth=6, 그
depth에서 유일한 canonical witness, depth<=6 전체에 대한 완전
검증(exhaustive, node cap 미도달), 그리고 R/A2 각각의 "첫 이벤트로
등장 가능한 최소 index" 비대칭(0 대 4)으로부터의 정량적 설명 —
모두 확보됐다.
