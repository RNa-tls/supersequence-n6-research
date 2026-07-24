# Occupancy automaton (b_ell4, b_ell0) — 5-witness 재구성과 i_min(A2)=4 재검토

산출: `src/build_a2_occupancy_automaton.py`,
`outputs/a2_occupancy_automaton.json` (기존 5개 focus witness 재사용,
새 탐색 없음).

## 6. Occupancy automaton

요청된 자동자는 `(endpoint phase, b_A, b_B, candidate-target-visited,
current-hex-status)`라는 5-성분 상태였다. 이번 라운드는 이를 **5개
focus witness(U4 4개 + outlier)의 실제 macro-edge 이벤트 시퀀스에서
직접 재구성**했다(새로운 상태공간 열거가 아니라, 이미 아는 경로를
`(b_ell4, b_ell0)` 2-비트로 태깅한 것) — `endpoint phase`,
`candidate-target-visited`, `current-hex-status`는 이번 재구성에서
생략했는데, 그 이유는 §7에서 설명한다.

### 관측 — 자동자가 사실상 퇴화(degenerate)한다

5개 witness 전부에서, `(b_ell4, b_ell0)`는 **A2 직전까지 단 한
번도 전이하지 않는다** — U4 4개 전부 `(True, False)`로 시작해서
끝까지 그대로, outlier는 `(False, True)`로 시작해서 끝까지 그대로.
(§5의 "두 orbit 다 오프닝 사건이 없다"는 발견과 정확히 같은
사실의 재확인.) **즉 이 2-비트만 놓고 보면, 이 자동자에는 실질적
전이(transition)가 전혀 없다** — 상태는 word 시작 시점에 이미
고정되고, 그 뒤로는 상수다.

이것은 §6이 기대했던 "depth 0부터 첫 A2까지 abstract history를
전부 열거"라는 목표에 대해 **정직한 부정적 결과**다: 이 2-비트
통계만으로 만든 자동자는 사실상 1-상태(그룹별로 고정된 상수)이므로,
"depth별 abstract history 전이 규칙"이라는 것 자체가 이 5-witness
표본 안에서는 존재하지 않는다.

## 7. i_min(A2)=4의 조건부 재접근 — 이번 라운드는 시도하지 않음, 정직한 이유

이번 라운드의 명시적 지시: *"H_A2 occupancy automaton만 사용해서
... 자동자가 자연스럽게 index<4 불가능을 보여줄 때만 lower bound로
승격하라."*

**위 §6에서 재구성한 자동자로는 이 승격이 불가능하다** — 이유는
구조적이다:

1. 이 자동자는 **5개의 이미 알려진 witness의 실제 경로만** 태깅한
   것이지, depth 0-3에서 **도달 가능한 모든** `H_A2` 상태를 열거한
   것이 아니다. "index 0-3의 모든 realizable 상태가 all-false
   legality를 갖는다"는 완전성 주장을 하려면 이 5개 경로가 아니라
   **도달 가능한 전체 상태공간**을 봐야 하는데, 그건 정확히
   이전 라운드들이 이미 시도했고(`src/verify_a2_minimum_index.py`,
   구 라운드 산출 `outputs/a2_depth4_abstract_histories.json`:
   `a2_first_legal_at_depth_index=4`, exact exhaustive BFS로 이미
   확인) **이번 라운드가 "정면으로 반복하지 말라"고 명시적으로
   금지한 바로 그 시도**다 — 그래서 이번 라운드는 그 BFS를 다시
   돌리지 않았다(기존 산출물을 재확인만 함, 재실행 없음).
2. 5개 witness만으로 자동자를 만들면 "전이가 없다"는 관측 자체가
   **완전성 결여를 그대로 드러낸다** — 만약 다른(이 5개 안에 없는)
   RA2 경로가 있어서 두 비트가 도중에 실제로 바뀐다면, 이 자동자는
   그 경우를 놓친다. 따라서 이 자동자에서 관측된 "전이 없음"을
   "일반적으로 전이가 불가능하다"로 확대 해석하면 **근거 없는
   과장**이 된다.

### 정직한 결론

**이번 라운드는 §7의 조건(자동자가 자연스럽게 보여줄 때만
승격)을 만족하지 못했으므로, `i_min(A2)=4`에 대해 어떤 새로운
lower-bound 주장도 하지 않는다.** 기존에 확인된 사실
(`a2_first_legal_at_depth_index=4`, exact search, 이전 라운드
산출, 이번 라운드에서 재실행하지 않고 값만 재확인)은 여전히
"exact search 결과"일 뿐 "연역적 lower-bound 증명"은 아니라는
이전 라운드의 정직한 라벨을 그대로 유지한다 — **미완료**.

## 성공 기준 (4) 평가

**미달성**: `H_A2` quotient(2-비트 축약)로 만든 자동자가 이번
5-witness 재구성에서는 퇴화(무전이)했고, 이는 완전성을 증명하지
못하는 근본적 한계 때문에 lower-bound로 승격할 수 없다 — 정직하게
미완료로 남긴다(직접 재시도 금지 지시를 준수).
