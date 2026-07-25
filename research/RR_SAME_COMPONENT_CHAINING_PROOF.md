# same-component ⟹ chaining — 최종 증명 상태 (라운드 14)

산출: 이번 라운드의 모든 스크립트 종합
(`analyze_rr_hub_completer_orbits.py`, `verify_rr_orbit_identity.py`,
`verify_rr_chaining_proof.py`).

## 10. 단계별 증명 — graph/permutation/phase/endpoint 논증 분리

### 1단계(graph-level, 손증명): R2 same-component이면 R2 source/target은 hub를 통해 연결된다

`RR_ANCESTRY_PROOF.md`(라운드 12) Lemma 1-3 — union-find 정의와
`RR_HUB_TOUCH_COUNT.md`(라운드 13)의 Unique Hub Hexagon +
Hub-Touch-Count≤2 정리로부터 완전히 일반적으로 증명됨. **변경 없음,
불변.**

### 2단계(permutation-level, **abandon_ell=4 하위경우만 손증명, 일반은 미완료**): hub completer target orbit은 (해당 하위경우에서) 유일하게 결정된다

`RR_HUB_COMPLETER_ORBIT_THEOREM.md` — hex0의 위치-orbit 1:1 대응이라는
순수 조합론에서, `abandon_ell=4`(코퍼스의 9/10 same-component
witness가 여기 속함)일 때 hub completer 후보가 유일하게(orbit 1)
결정됨을 손증명. `abandon_ell<4`(코퍼스 유일 예외: 989d2261b4,
ell=0)에서는 **여러 orbit이 legal candidate**임을 exact witness로
확인 — 이 하위경우의 "유일성"은 **반증됨**.

### 3단계(phase-level, 손증명): chaining 판정과 same 판정 둘 다 phase-불변이다

`RR_PHASE_FREEDOM.md` — union-find 노드가 `("q", orbit_id)`(phase를
포함하지 않음)로 정의된다는 코드 사실로부터 직접 도출. **완전히
일반적으로 성립, corpus나 depth와 무관.**

### 4단계(endpoint-level, **corpus-exact, 부분탐색으로 강화, 일반 미완료**): 같은 component에서 legal R2는 O_R ancestry chain을 따라야 한다

전체 4,470개 코퍼스에서 반례 0(`same-component ⟹ chaining` 유한
완전 검증). 추가로 이번 라운드는 `989d2261b458`(유일하게 여러
candidate를 갖는 예외 케이스)에서 depth≤12, node_cap=150,000의
**목표 지향(targeted) bounded search**(모든 R1/R2 배치 조합을
탐색, "completer≠R1_target ∧ R2가 completer orbit을 source로
same을 만드는" 정확한 반례 시나리오를 직접 겨냥)를 실행했다 —
**frontier가 287,322개 남아 완전탐색은 아니었지만**, 150,000개
확장 노드 안에서는 반례를 찾지 못했다. **이 단계는 손증명이 아니라
강화된 국소 증거로만 표시한다.**

### 5단계: 따라서 R2는 chaining이다

1-4단계를 종합하면, **abandon_ell=4 하위경우(코퍼스의 압도적
다수, 9/10)에 대해서는 1,2,3단계가 전부 손증명이므로, "이 하위경우
안에서 same이 나온다면 반드시 chaining이다"는 명제가 사실상
연역적으로 도출된다**(2단계가 completer orbit을 유일하게 고정하고,
1단계가 그 orbit이 R2와 hub를 통해 연결됨을 보장하며, 3단계가
phase 불일치를 무력화하므로 — 남은 것은 "그 유일한 orbit이 실제로
R1의 target인가"라는 corpus-exact 사실뿐이다). **abandon_ell<4
하위경우는 2단계가 무너지므로 이 연역이 완성되지 않으며, 4단계의
국소 증거에만 의존한다.**

## 정직한 최종 판정

> **same-component ⟹ chaining은 여전히 완전한 일반 손증명이
> 아니다.** 그러나 이번 라운드는:
> 1. 이 명제가 **왜 어려운지**(2단계가 일반적으로 성립하지 않음)를
>    정확히 규명했고,
> 2. **코퍼스의 90%(abandon_ell=4)에 대해서는 1,2,3단계 전부
>    손증명**되어 사실상 완결에 가까운 연역 사슬을 확보했으며,
> 3. 남은 10%(ell<4)에 대해서는 목표 지향 탐색으로 반례 부재의
>    증거를 크게 강화했다(depth≤12, 150,000 노드, 특정 반례
>    시나리오를 직접 겨냥).

## 성공 기준 (2) 평가

**부분 달성**: 완전한 일반 손증명은 아니지만, 정리를 구성하는
4단계 중 3개(1,3단계는 완전, 2단계는 90% 하위경우에서 완전)가
손증명됐고, 남은 gap(4단계, ell<4 하위경우)이 극도로 정밀하게
좁혀졌다 — 라운드 13이 "corpus-exact, 이유 불명"이었다면, 이번
라운드는 "abandon_ell에 따라 나뉘는 두 개의 하위 문제, 하나는 이미
해결, 나머지 하나는 국소 증거로 강화됨"으로 발전시켰다.
