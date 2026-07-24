# Restart-barrier lemma (B1–B4)

인접 exchange obstruction(이전 라운드)을 block 단위로 일반화한다.

## B1: full-swept block 뒤에서는 nonzero abandonment를 즉시 왼쪽으로 넘길 수 없다

**손증명, 이전 라운드 정리의 직접 일반화.** 임의의 block이 full
sweep(label X)으로 끝난다는 것은 정의상 그 block의 hex가 FULL이라는
뜻이고, `RA2_ZERO_CHARGE_HISTORY.md` §1.2의 논증(단일 연속 arc가
길이 6에 도달하면 rotation-successor가 이미 방문됨)이 그대로
적용된다 — **그 지점에서 어떤 추가 rotation(ell≥1)도 불가능**하므로,
바로 다음 자리에 "ell≥1을 요구하는 abandonment"를 끼워 넣는 것은
불가능하다. `RA2_A2R_EXCHANGE_THEOREM.md`의 인접 exchange 반증은
이 정리의 R 자신에 대한 특수 사례였다 — 이제 **모든 X-block에
대해 일반화됐다.**

## B2: fresh restart를 하나 건너면 abandonment 이동이 가능해질 수 있다

**참, 구체적 witness로 확인됨.** `RA2_A2R_EXCHANGE_THEOREM.md` §4에서
이미 확인한 사실을 이 틀로 재해석: A2를 R의 자리가 아니라 그
DIRECTLY 다음 zero-charge block(fresh restart, mask=1 시작)의
자리로 옮기는 시도는 **legal했다**(U4 witness `17a42b24ccfb`에서
직접 검증). fresh restart 직후는 아직 FULL이 아니므로(mask=1) 추가
rotation이 가능하고, 이것이 B1의 장벽을 우회하는 유일한 방법이다.
**단, 이는 "A2가 그 자리로 이동 가능"할 뿐, R과 A2의 전체 순서를
바꾸는 것과는 다른 질문이다** — 이미 `RA2_A2R_EXCHANGE_THEOREM.md`에서
지적한 한계를 그대로 재확인.

## B3: existing-hex re-entry block은 defect-order 교환의 영구 barrier를 만든다

**적용 대상 없음 — E label 자체가 이 구간에서 정의상 불가능함이
증명됐다**(`U_BRANCH_RESTART_BLOCKS.md` §1). F=0 구간에서는 모든
block이 fresh-hex restart(F)뿐이므로, "existing-hex re-entry"라는
전제 자체가 성립하는 사례가 코퍼스에 없다. 이 후보는 검증도
반증도 할 수 없다 — **미완료(전제 부재)**로 표시한다.

## B4: A2가 legal해지기 위해서는 R 이후 최소한 특정 restart pattern이 필요하다

**부분 확인, 완전한 필요조건 증명은 아님.** `U_BRANCH_RESTART_BLOCKS.md`에서
확인한 정확한 사실: U4 4개 전부(그리고 outlier 1개)는 A2 직전에
"weight-3, fresh orbit을 여는" block을 반드시 거친다. 그러나
**이것이 A2 legal성의 필요조건이라는 연역적 증명은 얻지 못했다** —
단지 관측된 코퍼스(24개)에서 A2가 legal해지는 경로들이 공통적으로
이 패턴을 보인다는 것뿐이다. C20의 9개(m=1)는 이 패턴 없이도(단지
R의 orbit 재사용만으로) A2에 도달했으므로, **"특정 restart
pattern이 반드시 필요하다"는 일반 명제로서는 반증됨**(C20의 9개가
반례) — 다만 **U4라는 부분집합에 한정하면 그 특정 패턴이 예외
없이 관측된다**는 것은 정확한 관측(유한 완전 검증, U4 4개 전부)이다.

## 성공 기준 (2) 평가

"인접 obstruction을 일반화한 restart-barrier lemma"는 **B1에서
달성됐다**(모든 full-swept block에 대해 정확히 일반화, 손증명).
B2/B3/B4는 각각 확인/전제 부재/부분 반증으로 정직하게 기록하며,
전체를 하나의 단일 강력한 lemma로 억지로 통합하지 않는다.
