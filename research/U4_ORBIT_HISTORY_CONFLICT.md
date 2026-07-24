# U4 orbit-history와 completion demand의 충돌 여부

산출: `src/build_a2_occupancy_automaton.py`,
`outputs/a2_orbit_opening_histories.json`,
`outputs/u4_two_bit_capacity_comparison.json`
(5개 focus witness — U4 4개 + C20 outlier 1개 — 재사용, 새 대규모
탐색 없음: 최대 depth=4, node_cap=20000의 소규모 bounded BFS만 사용).

## 5. 두 orbit의 생성 역사 — 예상과 다른 결과

당초 가설은 "두 orbit이 각각 언제 열리는지 추적하고, 그 오프닝을
제거하는 counterfactual을 만든다"였다. **실제로 5개 focus
witness(U4 4개 + outlier) 전부를 raw(비-canonicalize) 프레임으로
단어 시작부터 A2 직전까지 재생한 결과, 두 candidate orbit 중
어느 쪽도 추적된 역사 도중에 "열리는" 사건이 전혀 없었다:**

| witness | `existing(ell=4 후보)`(word 시작 시점) | `existing(ell=0 후보)`(word 시작 시점) | 이후 역사 중 변화 |
|---|---|---|---|
| U4 (4개 전부) | **True**(단어 시작부터) | False | **둘 다 A2 직전까지 변화 없음** |
| outlier | False | **True**(단어 시작부터) | **둘 다 A2 직전까지 변화 없음** |

**핵심 발견**: `initial_state()`(전체 단어의 절대 시작점)는 정확히
1개의 orbit만 existing 상태이며, 그것은 `E_REPS[0]`
(`ORBIT_PHASE[IDENTITY]=(0,0)`) — **단어 자신의 시작 순열이 속한
E-orbit**이다. **raw 프레임에서 U4의 `ell=4` 후보 orbit id는
정확히 이 orbit 0과 일치하고(4/4), outlier의 `ell=0` 후보 orbit id
역시 정확히 orbit 0과 일치한다(1/1)** — 즉 두 그룹 모두, 두 비트 중
하나는 "단어 역사 중 열린 것"이 아니라 **"단어 시작부터 공짜로
이미 존재하는 자원"**이며, 나머지 하나는 A2 직전까지 **단 한 번도
방문되지 않는다**(둘 다 미방문 → 결코 existing이 되지 않음).

**따라서 section 5가 예상한 형태의 "오프닝 사건과 그 제거
counterfactual"은 이 5개 witness에는 적용되지 않는다** — 열리는
사건 자체가 없기 때문이다(정직하게 보고: 가설의 전제가 이
코퍼스에서는 성립하지 않았다). 대신 실제 causal question은:
**"왜 이 특정 raw 순열 역사에서, `ell=4`(U4) 혹은 `ell=0`(outlier)
후보 슬롯이 우연히 단어의 시작 orbit과 일치하는가?"**로 바뀐다.
이는 `target(ell)=compose(raw_p0, g_ell)`(고정 원소) 공식에서,
`raw_p0`가 마침 `g_4^{-1}` 또는 `g_0^{-1}`의 E-orbit에 속한다는
사실과 동치다 — **5개 witness 전부에서 검증됐지만(정확), 이것이
일반적으로 항상 성립하는지(즉 임의의 RA2-도달 가능 상태에 대해
두 후보 중 정확히 하나가 항상 시작 orbit과 일치하는지)는 이
코퍼스만으로는 결정할 수 없다 — "corpus exact observation"으로만
표시한다.**

`one_step_alternatives`(오프닝 시점의 단일 지역 대안 개수) 필드는
스크립트에 구현돼 있으나, 오프닝 사건 자체가 없으므로 이번
5-witness 데이터에서는 한 번도 발동하지 않았다(정직하게 기록).

## 8. Post-A2 capacity와의 인과 연결

요청된 "동일 local boundary, 동일 A2 move, 서로 다른 두-bit orbit
history"라는 **완전히 통제된 비교는 이 코퍼스에 존재하지 않는다**
— U4는 `ell=4`에서, outlier는 `ell=0`에서 A2가 발동하므로 이미
**move 자체가 다르다**(같은 local boundary를 공유하지 않음, 애초에
critical restart 이후 서로 다른 상태로 갈라진다). 따라서 아래는
**cross-sectional 비교**(같은 A2 move가 아님, 통제되지 않음)이며,
"통제된 비교"로 과장하지 않는다.

A2 발동 직후 상태에서 depth 0-3까지 bounded exhaustive 탐색
(node_cap=20000, 전부 4/5-witness 모두 depth 3 이내에 frontier
소진 — exhaustive):

| witness | group | depth0 legal children | depth3 legal children (누적) | depth3 capacity_fail_leaves | depth3 fresh_orbit_openings |
|---|---|---|---|---|---|
| `17a42b24ccfb` | U4 | 4 | 153 | **1** | 84 |
| `1d8b48ab7d56` | U4 | 3 | 116 | **1** | 64 |
| `29f6af1e8aee` | U4 | 3 | 119 | **1** | 64 |
| `86ec22eaaba4` | U4 | 4 | 150 | **1** | 84 |
| `e2b44997e783` | outlier | 3 | 110 | **0** | 59 |

모든 5개 witness에서 depth 0-3의 모든 자식 rotation length는
`ell=5`뿐이었다(다른 ell은 이 얕은 깊이에서 전혀 나타나지
않음) — `terminal_reached`도 전부 `False`.

### "동일 occupancy history가 zero-charge 선택지를 늘려 capacity
failure를 지연시킨다" 평가

**확인도 반증도 못 함(미완료) — 통제되지 않은 비교이기 때문에
해석 불가.** U4가 depth 3에서 outlier보다 fail-leaf가 하나 더
많다는 것(153개 중 1개 vs 110개 중 0개, 비율로는 각각 0.65%,
0%)은 U4가 "더 나은" capacity를 갖는다는 가설과 **오히려 반대
방향**의 미세한 신호이지만, 표본이 너무 작고(각 1개 이하) 통제도
안 됐으므로 **이 데이터로는 어느 방향의 결론도 내릴 수 없다** —
가설을 "확인됨"으로 보고하지 않는다. 통제된 비교(같은 이전 상태에서
분기만 다른 두 자매 상태)를 만들려면 이 코퍼스 밖의 새로운 상태
생성이 필요한데, 이는 이번 라운드가 금지한 대규모 탐색에 해당할
위험이 있어 시도하지 않았다.

## 9. U4 closure 후보 O1-O4 평가

| 후보 | 설명 | 판정 |
|---|---|---|
| **O1** | U4 역사가 미래에 필요한 orbit을 조기에 연다 | **적용 안 됨 재해석 필요**: U4의 `ell=4` 후보는 애초에 "조기에 열리는" 사건이 아니라 단어 시작부터 존재하는 자원이다(§5). "조기 오픈"이라는 틀 자체가 이 데이터와 맞지 않아 O1은 **기각(반증)** — 관측된 메커니즘이 아니다. |
| **O2** | post-A2 fresh-orbit 스케줄이 하나 부족 | depth3 누적 `fresh_orbit_openings`는 U4(64-84)와 outlier(59)가 비슷한 규모 — "하나 부족"이라 할 만한 명확한 차이 없음. **판정 불가(증거 부족)**. |
| **O3** | opening 순서가 미래에 필요한 ell=5-only 경로를 한 component에 가둔다 | depth 0-3 전부 `ell=5`만 관측되어(U4, outlier 공통) 이 얕은 깊이에서는 두 그룹이 구별되지 않는다 — **이 depth에서는 판정 불가**, 더 깊은(이번 라운드에서 시도하지 않은) 탐색이 필요. |
| **O4** | A2-legality용 orbit-role과 completion-legality용 orbit-role이 충돌 | `candidate_orbit_reuse` 필드가 유일하게 흥미로운 비대칭을 보인다: U4는 depth3까지 `ell=0` 후보 orbit이 미래 target으로 1-2회 재사용되지만 `ell=4` 후보는 전혀 재사용 안 됨(당연 — 이미 소비); outlier는 반대로 `ell=4` 후보가 2회 재사용, `ell=0`은 0회. 이는 "소비되지 않은 쪽 후보가 나중에 다시 target으로 쓰인다"는 자연스러운 패턴 이상의 **충돌 증거는 아니다** — **판정 불가**. |

**정직한 결론**: 4개 후보 중 O1만 이번 데이터로 명확히
반증됐다(잘못된 프레이밍이었음이 드러남). O2/O3/O4는 이 5-witness,
depth≤3 bounded 데이터로는 **판정할 근거가 부족**하다 — 어느
것도 "U4 closure의 실제 장애물"로 확정할 수 없으며, 전부
**미완료**로 남긴다.

## 성공 기준 (5) 평가

**미달성**: "U4의 orbit-history가 completion demand와 충돌한다"는
정리는 세우지 못했다. 대신 §5에서 원래 가설(동적 오프닝 사건)이
이 코퍼스에 적용되지 않는다는 것을 정직하게 밝혔고, §8-9에서는
후보 메커니즘 O1을 반증했을 뿐, 나머지는 판정 불가로 남겼다 —
이 방향은 이번 라운드로 종결되지 않는다.
