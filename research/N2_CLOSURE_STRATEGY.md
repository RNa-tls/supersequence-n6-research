# N=2 slab 폐쇄 전략

## J-branch: 세 선택지 중 결정

지시된 세 선택지:

1. J-branch를 완전히 닫는 유한 정리
2. J-branch가 추가 charge를 강제함을 보이는 정리
3. J-branch를 소수의 exact subcase로 줄이는 reduction

**선택: 3 (reduction).** 이유는 `J_COMPLETION_OBSTRUCTION.md`와
`J_FUTURE_DEMAND_BOUND.md`에서 이미 보였듯, 1과 2는 현재 데이터로 뒷받침되지
않는다 — 대표 상태 하나에 대한 산술은 정확히 **모순 없이 풀리며**
(§`J_FUTURE_DEMAND_BOUND.md` §3), 4-macro-step bounded 실험도 강제된 추가
charge를 보이지 않았다 (§`J_COMPLETION_OBSTRUCTION.md` §5). 이를 "닫혔다"
또는 "추가 charge가 강제된다"고 주장하는 것은 근거 없는 과장이 된다.

대신 실제로 증명된 것(정리 J-1, J-2, J-3)은 정확히 **reduction**의 형태다:

> **J-branch 완주 문제는, J 발생 직후 상태를 새 시작점으로 하고
> `(TARGET_P-P_J, TARGET_O-O_J)=(115,23)`을 새 목표로 하는, `{rotation,
> Z2_blocked_w2_existing, Z3_blocked_w3_new, 최대 1개의 R}`만으로 이루어진
> zero-charge(+최대 1 unit) 스케줄링 문제로 정확히 환원된다. 이는
> `PARTIAL_F1_N0_FLOW_LEMMA.md`의 N=0 완주 문제와 동형인 문제다 — 다른
> 시작 상태·다른 남은 목표값을 가질 뿐, 같은 종류의 collision-회피
> 스케줄링이다.**

**함의:** J를 배제하려면 N=0 완주 문제에 필요한 것과 **같은 수준**의
도구(exact-state exhaustive search 또는 그에 상응하는 기하 논증)가
필요하다 — 그리고 N=0 자체가 아직 미완료다 (`RESEARCH_EXECUTION_STATUS.md`,
`STATUS.md`). 따라서 이 reduction의 실질적 의미는: **J-branch는 지름길로
닫히지 않는다.** 이것이 이번 작업에서 얻은 새로운 obstruction/reduction이다
(사용자가 요구한 성공 기준).

## U-branch: 다음 단계 제안

U-branch(다섯 ordered word, 25,430개 상태, `A2R`은 미관측)의 핵심 미해결
질문은 `independence_status: undetermined`다 — disjoint support를 가진
두 이벤트가 실제로 교환 가능한지가 literal replay 없이는 결정되지 않는다.
제안:

1. **swap 반례 또는 증명 하나만 확보.** `interaction_counts`에서
   `hex_support: disjoint, orbit_support: disjoint`인 조합(예: A3R의
   6,428개)에서 대표 하나를 뽑아, 두 defect의 순서를 바꾼 walk가 실제로
   합법적인지 literal replay로 확인한다. 이는 이번 작업의 범위(J-branch)
   밖이므로 여기서는 시도하지 않았다 — 다음 작업의 구체적 시작점으로
   남긴다.
2. **`A2R`의 이론적 지위 확정.** 다섯 unit-word 중 유일하게 미관측인
   조합이다. `PARTIAL_F1_N2_TWO_DEFECT_LEMMA.md`는 이를 불가능하다고
   증명하지 않았다 — 관측되지 않았을 뿐이라고 명시한다. 작은 유한 논증
   (또는 bounded 반례)으로 이 지위를 확정하는 것이 U-branch의 가장 저렴한
   다음 걸음으로 보인다.
3. 위 두 가지가 끝난 뒤에만 "N=2 slab 전체가 닫혔다"는 문장을 쓸 수 있다
   — 그 전까지는 U-branch와 J-branch 둘 다 열려 있다.

## 이번 작업에서 닫힌 것 / 열린 것 (요약)

**증명됨 (탐색 없이, 정의로부터):**
- charge-2 joint의 유일성 (J 하나뿐)
- J-1: J 이후 abandonment 예산 완전 소진
- J-2: J 이후 `R` 최대 1회
- J-3: J 이후 강제되는 joint 알파벳의 정확한 개수 (대표 상태 기준)
- J-branch → N=0-형 스케줄링 문제로의 reduction

**유한 완전 검증:** 230개 J 상태의 `deficit_phase_type`(13종)·
`legal_macro_tail_count`(2/3/4) 분포, 25,660 합계.

**제한 실험 (증명 아님):** 대표 J 상태로부터의 4-macro-step, 1043-edge
continuation; 60,000-node raw BFS를 통한 blocked-w2 lemma 경험적 확인.

**미결정으로 남김:**
- J-branch가 실제로 완주 가능한지/불가능한지
- U-branch 다섯 word의 독립성/교환 가능성
- `A2R`의 이론적 가능성
- N=2 slab 전체 폐쇄
- (물론) 조건부 `L_6>=872`, 무조건 `L_6=872`
