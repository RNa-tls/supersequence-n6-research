# F=1,H=0,N=2 slab의 U-branch / J-branch 분리

`f1_n2_depth6_decomposition.json`의 25,660개 bounded frontier 상태는
정확히 다섯 개의 ordered defect word로 분해된다 (합계 검증:
`10984+9952+4470+230+24=25660`, `src/verify_j_normal_forms.py`가 J의
230을 독립적으로 재확인; 나머지 넷은 이번 작업 범위 밖).

| word | 개수 | 유형 |
|---|---:|---|
| A3R | 10,984 | U-branch (두 unit defect) |
| RA3 | 9,952 | U-branch |
| RR | 4,470 | U-branch |
| RA2 | 24 | U-branch |
| **J** | **230** | **J-branch (charge-2 단일 이벤트)** |

`A2R`은 0 — U-branch 다섯 가지 순서 중 이 하나만 이 bounded frontier에서
관측되지 않았다. (`PARTIAL_F1_N2_TWO_DEFECT_LEMMA.md`가 이미 `RR, RA2, A2R,
RA3, A3R`을 "unit_charge_words"로 열거했으므로 `A2R`이 이론적으로
불가능하다는 주장은 이 코퍼스에 없다 — 단지 미관측일 뿐이다. 이번 작업은
이를 재확인하지 않았다; 새 탐색을 하지 않는다는 제약 때문에 `A2R`의
이론적 가능성 여부는 열어 둔다.)

## U-branch와 J-branch는 근본적으로 다른 종류의 제약을 받는다

**U-branch (두 unit defect, 총 5종 순서):** 두 개의 별개 이벤트가 존재하고,
`f1_n2_defect_words.json`은 이들에 대해 `component_relation`,
`fragment_relation`, `orbit_relation`, `interaction`(hex/orbit support
overlap 여부) 같은 **쌍대(pairwise) 관계 필드**를 기록한다. 즉 U-branch의
핵심 질문은 "두 이벤트가 서로 간섭하는가"이다 — `independence_status`가
대부분 `"undetermined: exact literal replay is required even when supports
are disjoint"`로 남아 있는 데서 보듯, support가 disjoint여도 swap 가능성이
증명되지 않았다. **U-branch invariant 후보: defect interaction invariant**
— 두 이벤트의 hex/orbit support가 겹치는지, 같은 fragment component를
공유하는지, 그리고 그 관계가 실제 literal replay에서 교환 가능성(swap
independence)으로 이어지는지.

**J-branch (단일 charge-2 이벤트):** 쌍대 관계가 정의상 없다
(`component_relation` 등이 전부 null, `verify_j_normal_forms.py`가 230개
전부에서 확인). 대신 J의 핵심은 그 **단일** 이벤트가 F 예산 전체와 N 예산의
2/3을 동시에 소진한다는 것이다 (`J_COMPLETION_OBSTRUCTION.md` 정리 J-1,
J-2). **J-branch invariant: abandonment/capacity invariant** — J 이후
남은 전체 걸음이 강제되는 좁은 joint 알파벳(`Z2_blocked_w2_existing`,
`Z3_blocked_w3_new`, 최대 1개의 `R`)으로 완전히 결정된다는 것, 그리고 그
알파벳의 개수(§`J_FUTURE_DEMAND_BOUND.md`)가 산술적으로 유일하게 정해진다는
것.

**두 invariant를 억지로 하나로 합치지 않는다** (지시대로). U-branch는
"두 사건의 독립성/교환 가능성"의 문제이고, J-branch는 "하나의 사건이
소진한 예산 아래서 좁아진 스케줄링 문제"다 — 수학적 성격이 다르다.

## 왜 이 분리가 유용한가

U-branch(다섯 word, 25,430개 상태)와 J-branch(230개 상태)는 겹치지 않는
분할이며 (word가 상호배타적), N=2 slab의 완주 불가능성을 보이려면 **둘 다**
닫아야 한다. 이 문서는 그 사실을 명시적으로 기록해, 앞으로 누구든 "N=2를
닫았다"고 주장하려면 U-branch와 J-branch 각각에 대한 독립적 논증(또는
공통으로 작동하는 하나의 논증)이 필요함을 상기시킨다. 지금까지는 어느
쪽도 완전히 닫히지 않았다.
