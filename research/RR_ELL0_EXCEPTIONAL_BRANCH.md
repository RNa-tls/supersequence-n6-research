# ell=0 예외 분기의 정확한 유한 정규형 (라운드 15)

산출: `src/analyze_rr_ell0_branch.py` -> `outputs/rr_ell0_completer_truth_table.json`,
`outputs/rr_ell0_normal_forms.json`. 새 탐색 없음(기존 코퍼스 재생만).

## 5-6. ell=0 분기 corpus 추출 — "5-way 분기"는 실제로 실현되지 않는다

Round 14는 (수동 구성한 합성 상태에서) 국소 BFS로 ell=0의 5개
residual orbit(1,3,9,33,120)이 모두 **legal** completer 후보임을
보였다. Round 15는 이번에 **실제 depth≤6 RR 코퍼스 전체(926개
ell=0 witness)를 재생**하여, hub가 실제로 완성되는 43개 사건 전부를
검사했다:

**43/43 전부 completer_orbit = 120 (가장 가까운 residual 위치)이다.
orbit 1, 3, 9, 33은 단 한 번도 completer로 실현되지 않는다.**

즉 "5-way ell=0 분기"는 **legal 가능성** 차원에서는 존재하지만,
**실제로 실현되는 정규형은 정확히 1개뿐**이다 — `RR_ABANDONMENT_ELL_DICHOTOMY.md`
§2의 자원회계(가장 가까운 위치만 비용2, 나머지는 비용≥4)로 설명됨.

### 완성-관계 진리표 (Section 8)

| completer orbit | hex0 완전폐쇄 | r2_relation | chaining | 개수 |
|---:|---|---|---:|---:|
| 120 | 예(항상) | unresolved | False | 42 |
| 120 | 예(항상) | **same** | **True** | **1** |

`same+non-chaining` 셀은 **구조적으로 공집합**이다 — 이는
`RR_RELATION_LATTICE.md`의 `same-component⟹chaining`(유한 완전
검증)의 직접적 재확인이며, ell=0 하위집합에서도 예외 없이 성립한다.

## 7. 유일한 예외 witness의 완전한 인과 사슬

해시: `989d2261b4587843f75e052e2d2d4909601bdeac1f36222610d59046898e0afa`.
전체 macro_path 6단계:

```
idx0 ell=0 Z2abandon  hex0(orbit0,ph0)   -> hex33(orbit120,ph1)   [abandonment]
idx1 ell=5 Z2         hex33(orbit33,ph0) -> hex64(orbit120,ph2)
idx2 ell=5 Z2         hex64(orbit64,ph0) -> hex90(orbit120,ph3)
idx3 ell=5 R          hex90(orbit90,ph0) -> hex0 (orbit120,ph0)   [= R1, hub completer]
idx4 ell=4 Z2         hex0 (orbit1, ph4) -> hex96(orbit0, ph1)    [hex0 완전폐쇄 후 퇴장]
idx5 ell=5 R          hex96(orbit120,ph4)-> hex4 (orbit0, ph3)    [= R2]
```

**메커니즘(손증명, 이 특정 witness에 대해 완전히 재생·검증됨)**:
R1(idx3) 자신이 hub completer이며, hex0가 아닌 다른 위상(phase0,
hex0 자신의 orbit120 인스턴스)에 착지한다. 그러나 idx0-2에서 이미
orbit120의 phase1,2,3이 각각 hex33, hex64, hex90에서 방문되어
있었다 — union-find 노드 `("q",120)`는 phase를 구분하지 않으므로
(`RR_PHASE_FREEDOM.md`), R1이 hex0에서 orbit120(phase0)에 착지하는
순간 hex0, hex33, hex64, hex90이 **모두 하나의 컴포넌트**로
병합된다.

이후 hex0는 (Hub Touch Count≤2에 의해) 강제로 완전폐쇄되어
위치5(orbit1,phase4)에 도달하고, Hub Exit Source Lemma(라운드15
신규 발견, 아래 §참고)에 따라 idx4의 퇴장 조인트는 정확히
orbit1(위치5)을 source로 삼아 hex96으로 향한다. 마지막으로
R2(idx5)는 hex96 **자신의** orbit120 phase4(orbit120의 5개 phase
중 마지막 남은 phase)를 source로 삼는다 — **orbit1이 아니라
orbit120을 재사용**함으로써 R2는 idx0-3이 만든 거대 컴포넌트에
합류한다.

**핵심 통찰**: 이 witness는 orbit120의 **5개 phase 전부**(idx0:ph1,
idx1:ph2, idx2:ph3, idx3:ph0, idx5:ph4)를 word 전체에 걸쳐
소진한다. 이는 ell=4 분기의 "직접적 hex0-orbit1-퇴장" 메커니즘과는
**완전히 다른, 간접적(2차) 메커니즘**이다 — R2는 orbit1을 전혀
직접 사용하지 않는다.

### Hub Exit Source Lemma (라운드15 신규, 손증명 + 전수 검증)

F=1이 소진된 후 hex0를 "떠나는"(source가 hex0 내부인) 모든 조인트는
반드시 source orbit=1(위치5)이어야 한다 — hex0의 순환 위치 순서
`[0,1,2,3,4,5]`에서 위치0(anchor)은 `t=0`부터 항상 이미 방문되어
있으므로, 회전 후계자가 이미 방문된 상태(=조인트가 legal한 "blocked"
조건)를 만족하는 유일한 위치가 위치5(후계자가 위치0으로 wrap)이기
때문이다. **전체 코퍼스에서 F=1 소진 후 hex0를 떠나는 조인트
212개 전부(0 예외)로 전수 검증됨.**

## 정직한 최종 판정

| 명제 | 판정 |
|---|---|
| ell=0 hub-completed의 completer orbit은 유일(120)하다 | **유한 완전 검증**(43/43) — 자원회계로 강하게 설명되나 완전한 불가능성 증명은 아님 |
| same+non-chaining은 ell=0에서 공집합이다 | **유한 완전 검증**(43/43, 위반 0) |
| 유일한 same-component 예외의 정확한 인과 메커니즘 | **exact witness**(완전히 재생·검증됨) — 일반화 여부는 미검증(코퍼스에 이 패턴의 두 번째 사례가 없어 일반 정리로 승격 불가) |
| 이 간접 메커니즘이 "정규형"을 이루는가 | **미완료**(단일 사례만 존재, 통계적 일반화 근거 없음) |
