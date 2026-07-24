# A2 prerequisite DAG — 이번 라운드에서도 완전한 손증명은 얻지 못함

산출: `src/build_a2_prerequisite_proof.py` (기존 저장 ledger 재사용, 새
탐색 없음).

## 8. i_min(A2)=4 완전한 dependency 증명 — 정직하게 미완료로 재확인

요청된 chain 후보(weight-2-compatible source endpoint 생성 → existing
target orbit 사전 생성 → fresh hex restart → source-target
component/phase alignment → A2 실행)를 이번 라운드의 5-state 데이터로
재검토했다:

- **fresh hex restart**: 모든 A2 이전 joint가 fresh hex를 target함은
  이미 증명됨(`U_BRANCH_RESTART_BLOCKS.md`) — chain의 이 단계는 항상
  자동으로 충족된다(모든 RA2 상태 공통).
- **existing target orbit 사전 생성**: A2가 legal하려면 A2 자신의
  target(orbit 1, U4의 경우)이 이미 touched돼 있어야 한다 — 그러나
  이번 라운드에서 확인했듯(§`RA2_CRITICAL_RESTART_ANCESTRY.md` §4,
  C1 반증), critical restart(orbit 138)는 A2의 target(orbit 1)이
  **아니다** — A2의 target orbit이 정확히 언제, 어떤 joint에 의해
  먼저 touched되는지는 이번 라운드에서 추적하지 못했다.
- **source-target component/phase alignment**: A2 자신의 source
  orbit(3)조차 union-find에 등록돼 있지 않음이 이미 확인됐다
  (`RA2_ORBIT_REUSE_CHARGE.md` H2b) — "alignment"라는 개념이 성립할
  대상 자체가 불명확하다.

**결론: 이번 라운드의 critical-restart 구조 분석으로도, "정확히
4"라는 숫자를 transition-level dependency로 연역 증명하는 데
이르지 못했다.** exhaustive bounded search(depth<=6, 유한 완전
검증)로 4가 최소값임은 여전히 확실하지만, **왜 3이 아니라 4인지에
대한 group-theoretic 설명은 미완료**로 다시 한번 정직하게 남긴다
— 이는 지난 두 라운드에 걸쳐 반복 시도했지만 해결하지 못한
문제이며, 이번 라운드도 실질적 진전을 만들지 못했음을 숨기지 않고
그대로 보고한다.

## 9. General critical-restart 패턴 — RA3/A3R에서는 다른 양상

저장된 ledger만 사용해(RA3 150개 표본, A3R 150개 표본, 새 탐색
없음), "두 번째 defect 직전 critical restart가 첫 번째 defect의
target orbit을 재사용하는가"를 검사했다:

| word | 표본 수 | reuse(재사용) | unrelated(무관) | no_critical(인접) |
|---|---:|---:|---:|---:|
| RA3(R 먼저, A3 나중) | 150 | 38 | 73 | 39 |
| A3R(A3 먼저, R 나중) | 150 | **0** | 104 | 46 |

**RA2와 달리, RA3/A3R에서는 "reuse 대 unrelated"가 깔끔한 이분법을
이루지 않는다**(RA3는 혼재) — 그러나 **A3R에서 reuse가 정확히
0/150이라는 것은 주목할 만한 비대칭**이다: A3가 첫 이벤트일 때,
그 뒤를 잇는 critical restart는 **단 한 번도 A3 자신의 target
orbit을 재사용하지 않는다.**

**이것이 RA2/A2R의 barrier/prerequisite 정리와 같은 메커니즘인지는
판정하지 못했다** — A3R에서 A3가 이미 F=1을 소모했으므로
`RA3_A3R_ASYMMETRY.md`(더 이전 라운드)의 F-budget/fragment
order-lock 정리가 여기에 관여할 가능성이 높지만, 그 연결을
엄밀히 증명하지는 않았다. **추측으로 표시**하고, "두 번째 defect
직전 critical restart의 ancestry class가 defect-order family를
구별하는가"라는 질문에는 **부분적으로 그렇다(A3R의 reuse=0이라는
날카로운 신호가 존재)고 답하되, RA2/A2R barrier lemma의 직접
적용이라는 증명은 하지 못했다**고 정직하게 남긴다.

## 성공 기준 (4) 평가

"i_min(A2)=4의 완전한 prerequisite DAG 손증명"은 **미달성**이다 —
세 라운드에 걸쳐 시도했으나 여전히 완료하지 못한 문제로 남는다.
대신 RA3/A3R에서 발견한 "A3R의 reuse=0"이라는 날카로운 새 관측을
정직한 부분 성과로 기록한다.
