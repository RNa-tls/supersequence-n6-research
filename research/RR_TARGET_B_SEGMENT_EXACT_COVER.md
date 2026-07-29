# Segment exact-cover — 개정판 층 구조 R0–R5 (라운드 33)

개정판 지시의 층 이름으로 정리한 요약. 상세는
`RR_TARGET_B_EXACT_COVER_MODEL.md`(모델),
`RR_TARGET_B_RELAXATION_RESULTS.md`(결과),
`RR_TARGET_B_UNSAT_CERTIFICATES.md`(검증)에 있다.
산출 JSON은 `outputs/rr_segment_options.json`(= 개정판의
`rr_segment_options_r33.json`)과
`outputs/rr_target_b_relaxation_results.json`(= `..._r33.json`)이다.

## 층과 상태

| 층 | 내용 | 7개 survivor의 상태 |
|---|---|---|
| **R0** | capacity count only | 라운드32에서 통과(그래서 survivor) — 재계산 안 함 |
| **R1** | hexagon exact cover | **FEASIBLE 4 / INCOMPLETE 3** |
| **R2** | port uniqueness | **R1에서 유도 — 손증명** |
| **R3** | segment flow / order | **미판정** (cover 하나만 시험, 순서 없음) |
| **R4** | literal collision | **미도달** |
| **R5** | component compatibility | **necessary-condition 전용, 제약 미적용** |

## 이번 라운드가 확정한 것

1. **R1은 판별력이 없다.** 4개에서 명시적 cover가 구성됐고, 잔여
   hexagon 수가 정확히 \(B+1\)이라 분할이 빈틈없어야 하는데도
   쉽게 만족된다.
2. **진짜 병목은 R3이다.** 구성된 cover들의 successor edge가
   24–25개 segment 중 **0–1개**뿐 — flow 관점에서 거의 완전 단절이다.
3. **component(R5)는 아직 병목 후보가 아니다.** R3이 먼저다.
4. **새 손증명 하나**: initial segment capacity는 port 가용성이 아니라
   **phase-walk 도달성**으로 제한된다(실제 2, 이전 bound 3).

## 지키지 않으면 안 되는 규율 (이번 라운드에서 실제로 지킨 것)

- greedy hexagon-disjoint family를 상한으로 쓰지 **않았다**.
- capped corpus를 exhaustive라 부르지 **않았다**.
- 대형 permutation-level DFS로 돌아가지 **않았다** — 모든 작업이
  segment 층에서 이루어졌다.
- N=0 checkpoint를 건드리지 **않았다**.
- T3을 이번 결과로 "증명됐다"고 하지 **않았다** — T3은
  exact observation 15/15로 그대로다.
- cover 하나가 순서를 못 갖는 것을 R3 장애물로 쓰지 **않았다**.

## 남은 7개를 못 줄였다

**정직한 결과로 기록한다.** 7개 중 하나도 이번 라운드에서 제거되지
않았다. 얻은 것은 (i) 명시적 R1 cover 4개, (ii) 병목이 R3이라는
정량적 확인, (iii) initial capacity 손증명, (iv) 라운드32의 두 제거에
대한 독립 재확인이다.
