# Zero-charge transition graph 구조

## 1. Cycle은 존재할 수 없다 — **증명됨 (탐색 불필요)**

`exact.extend(state, move)`는 목표 창(target window)이 **이미
방문됐으면 즉시 `None`을 반환**한다(`superperm_partial_f1.py::extend`).
따라서 어떤 legal 이행이든 `visited_count`가 정확히 1(rotation) 또는
그 이상(joint, `ell+1`) 증가한다 — **`visited_count`는 모든 legal
이행에서 엄격히 증가한다.**

> **정리.** `visited_count`를 rank function으로 쓰면, 어떤 legal
> transition graph(zero-charge만이든 전체든)도 사이클을 가질 수
> 없다 — 사이클은 같은 상태로 돌아옴을 뜻하는데, `visited_count`가
> 그 경로를 따라 엄격히 증가하므로 불가능하다.

이는 canonicalization이나 exact-state 세부사항과 무관하게, `extend`의
정의 그 자체에서 즉시 따라 나온다. 탐색으로 확인할 필요조차 없다 —
이미 증명됐다.

## 2. Rank function

`visited_count`(증가) 또는 동등하게 `720-visited_count`(감소), 또는
남은 joint 수 `TARGET_P-P`(감소, joint에서만 — rotation에서는
불변이지만 rotation도 `visited_count`는 올린다)가 모두 유효한 rank
function이다. 가장 세밀한 것은 `visited_count` 자체다.

## 3. SCC — **자명하게 전부 singleton**

사이클이 없으므로 모든 강한 연결 요소(SCC)는 크기 1이다. "SCC가
있다면 visited mask가 달라서 실제 반복 불가능한가"라는 질문은
답할 필요가 없다 — SCC 자체가 처음부터 존재하지 않는다.

## 4. 이것이 상태 폭발을 설명하지 못하는 이유

DAG라는 사실은 탐색이 **유한하다**(최대 깊이 ~114~115)는 것만
보장하지, **좁다**는 것은 전혀 보장하지 않는다.
`J_STATE_SPACE_REDUCTION.md`에서 실측한 대로, 폭발은 사이클/재방문이
아니라 순수한 **너비**(매 depth 3~4의 branching, depth 3에서 이미
149개 canonical state, 병합 없음)에서 온다. DAG 구조는 "탐색이
무한히 순환하지 않는다"는 안전성만 주지, 너비 문제에는 도움이 되지
않는다 — 이것이 정직한 negative 결론이다.

## 5. Diamond(재합류) 구조 — **미결정, 근거 부족**

서로 다른 branch가 몇 단계 뒤 같은 canonical state로 재합류하는
"diamond" 구조가 있는지 조사했으나, depth 0–3(9개 seed 전부)에서
`exact_duplicate_children=0`이었다 — 즉 이 얕은 범위에서는 diamond가
전혀 관측되지 않았다. 더 깊은 depth에서 나타날 수도 있지만(이전
`search_j_9_exact.py` 프로파일링에서도 node cap 800까지
`canonical_memo_duplicate`가 사실상 없었다), 이번 범위에서는 증거가
없다 — 있다고도 없다고도 결론 내리지 않는다.
