# same-component ⟹ chaining — 최종 정리 구조 (라운드 15)

산출: 라운드11-15 전체 종합. 새 탐색 없음(모든 수치는 기존
`rr_literal_witnesses.json`의 완전한 4,470-witness 코퍼스 재생 또는
그로부터 파생된 국소 bounded BFS).

## 12. 최종 정리 구조

### Lemma A — Unique Hub Hexagon (손증명, 라운드12)
F≤1 예산 하의 word에서 2회 이상 터치되는 hexagon은 최대 1개뿐이다.
`f1_normal_form`의 F+1개 부분 hexagon 제한에서 직접 도출. **변경
없음.**

### Lemma B — Hub Touch Count ≤ 2 (손증명, 라운드13)
Hub는 두 번째 터치를 받는 순간 새 current_hex가 되며, F가 이미
소진됐으므로 다시는 abandon될 수 없다 — 남은 위치는 순수 회전으로만
방문되어 결국 영원히 닫힌다. **변경 없음.**

### Lemma C — same-component RR ⟹ abandonment ell ∈ {0,4} (라운드15, 유한 완전 검증)
전체 4,470개 RR witness(코퍼스가 depth≤6 RR word의 완전한
전수조사이므로 표본이 아님) 중 same-component는 정확히 ell=0(1개),
ell=4(9개)에서만 발생하고 ell=1,2,3에서는 0/2777이다. **완전한
일반 손증명은 아니지만(자원회계 논증에 R1-일치 특수경우의 gap이
남음), depth≤6 코퍼스 전체에 대해서는 반례 없는 유한 완전 검증.**
`RR_ABANDONMENT_ELL_DICHOTOMY.md`.

### Lemma D4 — ell=4 분기: 유일 residual 위치가 chaining을 강제 (라운드14-15, 부분 손증명)
1-4단계(orbit1 유일 강제, union-find 병합, hex0 즉시폐쇄, phase
불변)는 완전히 일반적으로 손증명됨. 5단계(R2가 실제로 orbit1을
사용하는지)만 corpus-exact(9/45)로 남는다. `RR_ELL4_CHAINING_PROOF.md`.

### Lemma D0 — ell=0 분기: ancestry가 chaining을 강제 (라운드15, exact witness)
5-way legal completer 중 실제로는 오직 1-way(orbit120)만 실현되며,
same-component 예외 1개는 orbit120의 5-phase 전부 소진이라는
간접(2차) 메커니즘으로 설명된다. **단일 exact witness로만 확인,
일반화된 ancestry 불변량 Γ는 정식화하지 못함(§9 참고, 미완료).**
`RR_ELL0_EXCEPTIONAL_BRANCH.md`.

### Theorem — same-component ⟹ chaining (전체, 라운드14 relation lattice에서 이미 확립)
전체 4,470개 코퍼스 전수 검증: 반례 0/10. **유한 완전 검증.** Lemma
C, D4, D0는 이 정리가 **왜** 성립하는지에 대한 분기별 구조적 설명을
제공하지만, D4의 5단계와 D0의 일반화는 여전히 gap으로 남는다.

## 9. Ancestry 불변량 Γ — 미완료

목표 정리("R2가 same일 필요충분조건은 Γ가 R1 chain class에
속하는 것")를 정식화하려면 LCA류 불변량이 필요하나, 이번 라운드가
발견한 실제 메커니즘(orbit 재사용 사슬, phase 소진)은 LCA보다는
"**어떤 orbit이 word 전체에 걸쳐 몇 번, 어느 phase에서 방문되는가**"라는
**시퀀스 수준의 불변량**에 더 가깝다. 이를 엄밀한 Γ로 정식화하는
작업은 **미완료**로 남긴다 — 다만 라운드15가 제공하는 재료(orbit
재사용 카운트, phase 소진 여부)는 향후 이 작업의 직접적인 출발점이
될 수 있다.

## 10. 추상 countermodel 증강 — 부분

`RR_ABSTRACT_COUNTERMODEL_STATUS.md`(이전 라운드)에 ell 관련 공리를
추가하면: **"completer position count = 1"(ell=4)이 되는 순간
5단계의 "R2가 어느 orbit을 쓸지"에 대한 자유도가 정확히 1개
orbit(1)으로 붕괴**하므로, countermodel의 자유도 공간이 즉시
축소된다. 이는 D4의 1-4단계가 이미 보여준 바와 동치이며, **ell=0의
경우 정확히 어떤 최소 ancestry 공리가 추가로 필요한지는 규명하지
못했다**(D0가 exact witness 수준에 머물러 있기 때문). **미완료.**

## 13. Terminal demand 비교 — 확장 없음

지시대로 completion search를 확장하지 않았다. `RR_PHI_ZERO_STATUS.md`
§13(라운드14)의 결과를 그대로 유지하며, 이번 라운드는 새로운 정적
장애물을 찾지 않았다(찾으려면 search 확장이 필요했을 것이므로
의도적으로 시도하지 않음).

## 11. Φ=0의 독립적 재도출 — 강화됨

**새로운 발견(라운드15, 유한 완전 검증, 212/212)**: `Φ_final=0`은
same-component(10개)뿐 아니라 **hub-completed인 모든 witness(212개)
전부**에서 성립한다. 이는 Round14가 제기한 "same-component의
독립적 산술 결과인가, 아니면 우연인가"라는 질문에 대해 **결정적
답**을 제공한다 — Φ는 P(pass 수)와 visited_count에만 의존하는
순수 매크로엣지-카운트 함수이므로, **"hub가 완성되는 word는
항상 같은 매크로엣지 패턴(1 abandon + 2~3 완성 gap + 나머지)을
쓴다"는 사실만으로 Φ=0이 결정되며, same-component/chaining과는
논리적으로 완전히 독립적이다.** `outputs/rr_ell_branch_phi.json`.

## 성공 기준 평가

이번 라운드는 아래 성공 기준을 다음과 같이 달성했다:

1. **same-component⟹ell∈{0,4}**: 유한 완전 검증으로 달성(완전한
   일반 손증명은 아님, 자원회계 gap 존재).
2. **ell=4 branch 완전 연역 증명**: 부분 달성(1-4단계 완전, 5단계는
   corpus-exact).
4. **ancestry 정리(same+non-chaining이 ell=0에서 불가능)**: **유한
   완전 검증으로 달성**(43/43, 반례 0) — 다만 일반화된 ancestry
   불변량 형태로는 미완료.
5. **전체 branch-wise 증명**: 정리 자체(same⟹chaining)는 이미
   라운드14에서 유한 완전 검증됐고, 이번 라운드는 그 **왜**에 대한
   분기별(ell=0/4) 구조적 설명을 크게 진전시켰다.

**정직한 요약**: `same-component ⟹ chaining`은 여전히 완전한 일반
손증명이 아니지만, 이번 라운드는 (a) 두 분기(ell=0, ell=4)가 실제로
구조적으로 다른 메커니즘(직접 vs 간접)을 쓴다는 것을 exact
witness로 규명했고, (b) "5-way ell=0 분기"라는 원래의 문제 설정을
"1-way 실현 + 1개 간접 예외"로 극적으로 단순화했으며, (c) Φ=0을
same-component와 완전히 독립적인, 더 일반적인 사실로 격상시켰다.
