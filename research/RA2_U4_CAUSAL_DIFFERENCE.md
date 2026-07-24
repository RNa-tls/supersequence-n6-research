# U4 vs C20: 최소 causal edit, 그리고 RR lemma와의 관계

산출: `outputs/ra2_counterfactual_edits.json`(counterfactual sweep 부분).

## 7. C20과 U4의 counterfactual 비교 — 최소 edit은 "orbit 선택"이 아니라 "rotation 길이 선택"

`17a42b24ccfb`(U4)의 A2 macro-edge 직전 상태에서, **A2에 실제로
쓰인 것과 동일한 move(`w2:10`)를, 그 직전 rotation 길이 `ell`만
0부터 5까지 바꿔가며** 다시 발동해봤다:

| ell | legal? | abandonment | 결과 debt |
|---:|---|---|---:|
| 0 | 예 | True | 5 |
| 1 | 예 | True | **4 (C20의 전형값)** |
| 2 | 예 | True | 3 |
| 3 | **illegal**(그 지점의 target이 이미 방문됨) | — | — |
| 4 | 예 | True | **1 (U4의 실제값)** |
| 5 | 예 | **False**(hex가 이미 FULL — abandon할 것이 없음) | 해당 없음(A2 자체가 성립 안 함) |

**U4의 4개 상태 전부에서 이 sweep 결과가 완전히 동일하다**
(`outputs/ra2_counterfactual_edits.json`) — R과 A2의 boundary
data가 리터럴로 동일하다는 이전 결과(`RA2_FOUR_SURVIVORS.md`)의
직접 귀결이다.

**최소 edit distance = 1(rotation 스텝 하나)**, 위치 = A2 직전
rotation-run 자체, target(=move 자체)은 **바뀌지 않는다** — 이
특정 지점에서 legal한 weight-2 abandoning move는 `w2:10` **단
하나뿐**이다(다른 target을 고를 자유가 없음을 확인). 즉:

> **U4와 전형적 C20(debt=4)을 가르는 최소 causal edit은 "orbit-target
> 선택"이 아니라, 정확히 하나의 rotation 스텝(ell=1 대 ell=4)이다.**

이는 원래 요청이 예시로 든 "단 하나의 orbit-target 선택 차이가
debt를 가른다"는 가설을 **반증**하고, 그보다 단순한 메커니즘으로
대체한다.

Legality 유지 여부: ell=0,1,2,4에서는 legal, ell=3에서는 이 특정
move가 illegal(그 시점 target이 이미 방문됨 — 이 코퍼스의 특정
방문 이력의 우연), ell=5에서는 애초에 abandonment 자체가 성립하지
않는다(hex가 이미 FULL). Φ/orbit slack 변화: ell을 바꾸는 것
자체가 바로 Φ에 `ell-5`만큼 직접 반영되므로(§`RA2_ZERO_CHARGE_HISTORY.md`
§1.3), Φ 변화량 자체가 이 edit의 정의다 — 별도로 부가되는 비용이
없다.

## 9. RR lemma와의 관계 — 공통 구조 시도, 억지 통합은 하지 않음

새로 증명한 RR 정리("chaining이면 둘째 R의 component relation은
`unresolved`가 아니다", `RR_CHAINING_PROOF_STATUS.md`)와 이번 라운드의
RA2 발견("debt는 zero-charge word의 orbit 선택과 무관하고 오직
ell_A2만으로 결정된다")을 같은 틀로 통합할 수 있는지 검토했다.

**공통점(표면적, 주제 차원)**: 둘 다 "중간 이력의 세부 사항(어떤
orbit을 거쳤는가) 대부분이 최종 결과에 무관하고, 아주 좁은 특정
조건(RR: 정확한 orbit index 일치, RA2: 정확한 rotation 길이)만이
결과를 가른다"는 **"history-irrelevance" 패턴**을 보인다.

**차이점(메커니즘 차원, 결정적)**:
- RR 정리는 `orbit_masks` 기반 union-find(어느 orbit이 어느
  hexagon과 연결됐는가)의 **등록 여부**에 관한 것이다 — 이산적
  (등록됨/안됨), 그래프 연결성 문제.
- RA2 발견은 `hex_masks`의 **연속 arc 채움 정도**(popcount)에 관한
  것이다 — 연속적(0~5칸), 단일-아크 강제(§`RA2_ZERO_CHARGE_HISTORY.md`
  §1.2)에서 나온다.

이 둘은 이 모델의 **서로 다른 두 층**(E-orbit 그래프 대 hexagon
연속성)에서 독립적으로 작동하는 다른 수학적 대상이다. 하나의
"defect-between-history lemma"로 합치려면 두 층을 잇는 새로운
연결고리(예: 특정 orbit이 특정 hexagon과 어떻게 겹치는지의 구조)를
증명해야 하는데, 이번 라운드에서 그런 연결을 발견하지 못했다.

**결론: 억지 통합하지 않는다.** 두 결과는 "history 대부분이
무관하다"는 하나의 정성적 직관을 공유할 뿐, 하나의 정리로 묶일 수
있는 공통 수학적 메커니즘을 갖고 있지 않다 — 이를 정직하게
**미완료(통합 시도, 불가 판정)**로 기록한다.

## 성공 기준 재확인

이 문서의 §7은 "U4를 소수의 repair-obligation subcase로 완전 환원"
(성공 기준 4)에 기여한다 — 정확히는, U4 전체가 **단 하나의
subcase**("`ell_A2=4`에서 A2 발동")로 이미 환원됨을 재확인시켜
준다(`RA2_ZERO_CHARGE_HISTORY.md`에서 이미 증명). §9는 RR과의
통합을 시도했으나 정직하게 실패로 기록한다.
