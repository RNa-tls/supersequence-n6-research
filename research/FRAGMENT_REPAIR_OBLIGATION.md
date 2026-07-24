# Fragment repair: exact 정의, terminal 조건, U4 repair cone — obstruction 가설은 반증됨

산출: `src/search_fragment_repair.py` -> `outputs/ra2_repair_cones.json`.

## 3. Repair transition의 정확한 정의와 분류

각 legal transition을 fragment debt에 대한 효과로 분류한다
(`classify_transition`):

- **debt 감소**: transition의 target이 fragment_hex 안에 있고, 그
  결과 popcount가 늘어난 경우.
- **debt 유지**: fragment와 무관하거나(target이 다른 hex), fragment가
  이미 0인 경우.
- **debt 증가**: (이전 라운드 `RA2_THETA_POTENTIAL.md`에서 이론적으로만
  가능성을 언급했던) fragment-swap 케이스 — 이번 탐색에서 실제
  발생 여부를 아래 §6에서 검사한다.
- **fragment와 무관**: fragment_hex가 아예 없는 경우(F=0 상태, 즉
  A2 발동 전).

### 3의 핵심 질문 답변

1. **F=1 blocked-only 조건 아래 실제 repair transition이 존재하는가?**
   → **그렇다.** U4 4개 상태 전부에서, node cap 20,000 이내에
   11~15개의 서로 다른 repair witness(가장 얕은 것은 macro_distance=3)를
   발견했다 — `outputs/ra2_repair_cones.json`.
2. **필요한 source/target orbit 조건은 무엇인가?** → target은 반드시
   fragment_hex 안의 그 특정 미방문 permutation(debt=1이므로 정확히
   1개)이어야 한다. source는 제약이 없다(어느 orbit에서든, 그
   시점에 legal한 weight-2/3 move가 그 특정 target을 가리키기만
   하면 된다).
3. **repair가 orbit slack 또는 Φ를 반드시 소비하는가?** →
   **아니다 — 반증됨.** 가장 얕은 repair witness들(4개 상태 모두
   macro_distance=3)은 `phi_consumed=0`, `orbit_slack_consumed=0`이다.
   repair는 산술적으로 완전히 "공짜"로 가능하다.
4. **repair 뒤 split/phase debt가 새로 생기는가?** → 가장 얕은
   witness들에서는 새 debt가 생기지 않는다(모든 중간 rotation-run이
   ell=5를 쓰는 패턴이 반복되어, repair 이후에도 새 fragment가
   생기지 않고 debt=0 상태가 유지된다). 더 깊은(그러나 여전히
   저렴한) witness에서도 유사한 패턴이 관측됐다.
5. **repair를 두 번 이상 해야 하는가?** → 아니다, U4의 경우
   debt=1이므로 정확히 1개의 targeted joint로 충분하다(가장 얕은
   witness의 macro_path가 3개의 macro-edge를 쓰지만, 그중 fragment를
   직접 target하는 것은 마지막 1개뿐이다 — 앞의 2개는 단지 legal한
   경로를 만들기 위한 준비 단계다).

## 5. Terminal fragment 조건 — 재유도

`area_a_final`(코드 정의 그대로)은 다음을 요구한다:
`visited_count==720 and P==TARGET_P and O==TARGET_O and D==TARGET_D and
F==TARGET_F and H==0`.

- **fragment가 남아 있어도 완주 가능한가?** → **아니다.**
  `visited_count==720`은 "모든 hexagon이 FULL"과 정확히 동치다(각
  hexagon 6칸씩 120개 = 720칸 전부). fragment_hex도 예외 없이 이
  총합에 포함되므로, fragment debt는 **terminal에서 반드시 정확히
  0이어야 한다.**
- **마지막 pure-rotation suffix가 fragment를 해소할 수 있는가?** →
  **아니다, 구조적으로 불가능하다.** rotation(weight-1)은 정의상
  **현재 hex 안에서만** 움직인다(`HEX_POSITION`이 하나의 hexagon
  안의 6개 permutation을 순환시킬 뿐). fragment는 정의상
  **non-current** hex이므로, rotation은 fragment의 어떤 칸도 절대
  방문할 수 없다. fragment를 다시 방문하려면 반드시 **joint**가
  필요하다(fragment를 target으로 하는 joint가 fragment를 다시
  current로 만든 이후에야 rotation이 그 안에서 이어질 수 있다).
- **split hexagon과 fragment가 같을 때 예외가 있는가?** → 이
  코드베이스에서 둘은 같은 개념(별칭)이므로 예외가 없다.
- **마지막 path의 endpoint가 debt를 흡수할 수 있는가?** →
  **아니다.** endpoint(현재 위치 p)는 하나의 permutation일 뿐이며,
  fragment의 미방문 칸들은 endpoint가 무엇이든 **명시적으로 방문
  기록에 추가되어야만**(hex_masks 비트 설정) 카운트된다 — "끝나는
  위치"라는 사실 자체는 아무 것도 자동으로 채우지 않는다.

**결론: fragment-debt obstruction이 성립하려면 최소한 이 부분(terminal에서
반드시 0이어야 한다는 것)은 명확하다 — 문제는 그것이 "obstruction"인지,
즉 "0으로 만드는 것이 실제로 어렵거나 불가능한가"이며, 이는 §6에서
직접 반증된다.**

## 6. U4의 repair cone — **repair는 쉽고 저렴하다: obstruction 가설 반증**

`repair_cone_search`(node cap 20,000/상태, 종료 사건: debt=0, Φ<0,
orbit slack 위반, collision, legal transition 없음, debt 증가, node
cap)를 U4 4개 전부에서 실행했다.

| 상태 | witness 발견 수 | 최소 macro_distance | 최소 witness의 Φ 소비 | 최소 witness의 orbit slack 소비 |
|---|---:|---:|---:|---:|
| 17a42b24ccfb | 11 | 3 | **0** | **0** |
| 1d8b48ab7d56 | 15 | 5 | **0** | **0** |
| 29f6af1e8aee | 14 | 5 | **0** | **0** |
| 86ec22eaaba4 | 12 | 3 | **0** | **0** |

**debt-increase 사건은 이번 탐색(총 4개 상태 × 20,000 node)에서 단
한 번도 관측되지 않았다** — `debt_increase_events_seen: 0` (전
상태). `RA2_THETA_POTENTIAL.md`에서 이론적으로만 가능성을 논했던
fragment-swap에 의한 debt 증가는, 적어도 이 bounded 범위 안에서는
발생하지 않았다(여전히 일반적으로 증명되지는 않았다 — §4 문서에서
그대로 미완료로 남긴다).

가장 흔한 종료 사유는 `abandonment_illegal_post_f1`(97% 이상) — F=1
이후 abandonment 시도는 항상 즉시 제거된다는 기존 하위 정리의
재확인이며, 그 다음은 `N_exceeded_monotone`(Ndef 예산 초과)이다 —
**Φ가 아니라 N(charge) 예산이 이 근방에서 더 자주 작동하는
prune이라는 새로운 관측**이다(이번 라운드의 성공 기준과 직접
관련되지는 않지만, 다음 단계 탐색에 유용할 수 있어 기록해 둔다).

### 중요: debt=0 달성 ≠ 완주 가능 — 정직하게 구분

**repair witness를 찾았다는 것은 fragment를 없앨 수 있다는 것일 뿐,
전체 완주가 가능하다는 뜻이 아니다.** repair 이후에도 남은 완주
과제(120개 중 남은 joint들, 남은 22개 orbit 등, `RA2_COMPLETION_OBSTRUCTION.md`
§5)는 전혀 줄어들지 않았다 — repair는 그 방대한 남은 과제 중 아주
작은 한 조각(6칸 중 1칸)을 해결했을 뿐이다. **이 라운드는 "fragment가
완주를 막는 원인"이라는 가설을 반증했을 뿐, "완주가 가능하다"는
것을 증명하지 않았다** — 그 질문은 여전히 완전히 열려 있다.

## 성공 기준 (1), (2) 재평가 — 이번 라운드에서도 미달성, 그리고 방향이 바뀜

- **(1) U4 불가능 증명**: 미달성. 오히려 fragment 차원에서는 repair가
  "쉽다"는 반대 방향 증거를 얻었다.
- **(2) repair 최소 cost가 budget 초과 증명**: **반증됨** — 최소
  cost는 0이다, budget을 초과하기는커녕 전혀 소비하지 않는 경로가
  존재한다.
