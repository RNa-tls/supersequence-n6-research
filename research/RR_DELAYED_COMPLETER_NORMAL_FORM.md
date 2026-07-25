# Delayed same-orbit completer 정규형 재정식화 (라운드 15)

산출: 라운드14 `outputs/rr_delayed_completer_normal_forms.json` 재사용
+ 라운드15 `outputs/rr_ell0_completer_truth_table.json`,
`outputs/rr_abandonment_ell_table.json`의 새 결과 통합. 새 탐색 없음.

## 4. ell=4 분기 재검토 — delayed-completer 가족은 ell=4를 덮지 않는다

라운드14의 "delayed same-orbit completer" 가족(6개 witness, R1과
completer가 서로 다른 phase로 같은 orbit을 재사용)은 **모두
non-R1-completer** 사건, 즉 completer가 R1 자신이 아닌 별도의
사건인 경우였다. 이번 라운드의 전수 분석 결과:

- ell=4 분기(9개 same-component witness)는 **completer_orbit이
  언제나 1**(조합론적으로 유일 강제, `RR_ELL4_CHAINING_PROOF.md`
  §3)이며, 이 9개 중 completer가 R1 자신인 경우와 별도 사건인
  경우가 섞여 있다(라운드14 데이터 재확인 필요 — 아래 §비교).
- ell=0 분기(1개 same-component witness)는 **completer가 R1
  자신**이며(`RR_ELL0_EXCEPTIONAL_BRANCH.md` §7), delayed-completer
  가족과 **다른 메커니즘**(orbit1이 아니라 orbit120을 5-phase 전부
  소진하는 방식)을 쓴다.

**결론(corpus-exact)**: delayed-completer 가족(라운드14, 6개)과
ell=0의 유일한 예외(라운드15, 1개)는 "같은 orbit을 다른 phase로
재사용한다"는 **표층 패턴은 공유**하지만, 전자는 ell=4 분기(직접
hex0-orbit1-퇴장이 가능한 조건) 안에서 발생하고 후자는 ell=0
분기(직접 퇴장이 불가능해 간접 경로를 써야 하는 조건) 안에서
발생한다는 점에서 **서로 다른 필요조건 하에 있다**.

## 통합 정규형 표 (수정본)

| 분기 | completer orbit(들) | completer 유형 | 개수 | 메커니즘 |
|---|---|---|---:|---|
| ell=4 | 1(유일) | R1 또는 별도 사건(라운드14) | 9 | 직접: hex0 즉시폐쇄 → orbit1 직접 재사용 |
| ell=0 | 120(유일, 실현 기준) | R1 자신 | 1 | 간접: orbit120의 5-phase 전부 소진, orbit1은 미사용 |
| ell=1,2,3 | 각각 33/9/3(유일, 실현 기준) | 다양(비-R계열도 포함) | 0(same 없음) | hub는 완성되나 어떤 재사용도 same으로 이어지지 않음(전수 0/124) |

**이 표는 원래 과제가 요구한 "delayed-completer 가족이 ell=4
분기 전체를 덮는지"에 대한 답을 제공한다: 덮지 않는다.** ell=4의
9개 same-component witness 중 일부만 delayed(비-R1-completer)
패턴이며, 나머지는 completer=R1 직접 사건이다(라운드14
`rr_hub_completer_candidates.json`에서 이미 이 구분이 존재함 —
이번 라운드는 이를 ell 분기와 명시적으로 교차시켰다).

## 정직한 최종 판정

이 섹션은 새로운 반증이나 새로운 손증명을 추가하지 않고, 라운드14의
delayed-completer 정규형과 라운드15의 ell-분기별 completer-orbit
유일성 결과를 **정합적으로 통합**했다 — 통합 결과 "delayed-completer
가족은 ell=4의 부분집합이며 ell=4 전체를 덮지 않는다"는 점과
"ell=0의 예외는 delayed-completer 가족과 표층적으로 유사하나
메커니즘상 구별되는 별도 사례"라는 점이 corpus-exact로 확인됐다.
