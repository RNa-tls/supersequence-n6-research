# RA2 5-state focused comparison — U4 4개 + critical-restart-signature 공유 C20 outlier

산출: `src/analyze_ra2_five_states.py` -> `outputs/ra2_five_state_ledger.json`,
`outputs/ra2_five_state_tree_comparison.json`.

## 방법론 수정 사항 — 정직하게 먼저 기록

이전 라운드의 `analyze_restart_blocks.py`가 계산한 block별
`component_relation`은 각 block의 "source"를 **그 block 자신의
rotation 이전 위치**(`pre_rotation_state.p`)의 ORBIT_PHASE로
정의했다. 그런데 canonicalize()는 매 macro-edge 이후 위치를 항상
literal identity `(0,1,2,3,4,5)`로 재정규화하므로, **이
"source"는 어느 block을 보든 항상 orbit 0(항등원 자신의
orbit)으로 계산된다** — 이는 그 block 고유의 정보가 아니라
canonicalization 관례의 artifact다. 이번 라운드는 이를 발견하고
수정했다: 이제는 **각 block이 겨냥하는 target E-orbit의 리터럴
인덱스를 R 자신의 target orbit 인덱스와 직접 비교**하는, 모호함
없는 기준을 쓴다(`src/verify_critical_restart_classifier.py`).

**중요: 이 수정에도 불구하고 이전 라운드의 핵심 관측(C20의 단일
block은 R의 target orbit을 재사용, U4는 무관한 orbit을 연다)은
그대로 유지된다** — 이번 라운드에서 24개 전체를 직접 리터럴
orbit 인덱스로 재확인했다(§`RA2_CRITICAL_RESTART_CLASSIFIER.md`).
`component_relation` 라벨의 계산 방식에 결함이 있었을 뿐, 원
발견 자체는 견고했다.

## 1. Five-state 통합 ledger — critical restart는 리터럴로 완전히 동일

U4의 4개 상태와 outlier(`e2b44997e783`)의 critical restart(A2 직전
마지막 word-block)는 **완전히 동일한 리터럴 transition**이다:

```
kind=Z3, ell=5, source_orbit_q=1, source_phase=4,
target_orbit_q=138, target_phase=2, component_relation(구식 계산)=unresolved
```

5개 상태 전부 예외 없이 일치(`outputs/ra2_five_state_ledger.json`).
**처음 달라지는 필드는 그 다음 단계, 즉 A2 자신의 `ell_A2`뿐이다**
(U4: 4, outlier: 0) — 그리고 이로부터 파생되는 A2 자신의
source/target orbit(U4: source=3,target=1; outlier: source=0,
target=120)도 당연히 달라진다.

## 3. Outlier와 U4의 최소 차이 — ell_A2 하나

**critical restart가 리터럴로 완전히 동일함에도 A2 자신의 ell이
다르다는 것은, 이 둘을 가르는 최소 차이가 "critical restart 자체"가
아니라 "critical restart 이후, A2가 legal해지는 지점"이라는 것을
의미한다.** §5(`RA2_CRITICAL_RESTART_ANCESTRY.md`)에서 이를 더
깊이 판정한다 — 특히, outlier는 이 identical critical restart에
도달하기까지 **3개의 추가 준비 block**(Z3, target orbit 32와 138을
두 번 더)을 거치는 반면, U4는 많아야 1개(선택적)만 거친다는 것이
이미 알려진 사실이다(`U_BRANCH_RESTART_BLOCKS.md`) — **누적된
준비 이력의 양이 다르다는 것이, 동일한 critical restart 이후에도
서로 다른 ell_A2가 legal해지는 이유일 가능성이 높다**(정밀 검증은
다음 문서에서).
