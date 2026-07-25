# ell=4 분기 완전 증명 (라운드 15)

산출: `src/verify_rr_ell4_proof.py` -> `outputs/rr_ell4_dichotomy_verification.json`,
Round 14의 `RR_HUB_COMPLETER_ORBIT_THEOREM.md` 재사용. 새 탐색 없음.

## 3. ell=4 분기의 5단계 연역 사슬

**1단계(조합론적 유일성, 손증명, 라운드14)**: `ell=4`이면 hex0의
residual 위치는 정확히 1개(위치5, orbit1)뿐이다 — hex0의 위치-orbit
1:1 대응(고정 상수 `[0,120,33,9,3,1]`)에서 직접 도출되는 순수
조합론. **completer가 존재한다면 그 target orbit은 반드시 1이다.**
이는 이번 라운드의 전수조사(45/45 ell=4 hub-completed 사건 전부가
`completer_orbit=1`)로 재확인됨.

**2단계(union-find 연결, 손증명, 라운드12-13)**: completer가 hex0의
두 번째 터치를 제공하면, union-find 정의(`("q",orbit_id)`,
`("h",hex_id)` 노드에 대한 union)에 의해 hex0의 컴포넌트와 orbit1의
컴포넌트가 즉시 병합된다. **`RR_ANCESTRY_PROOF.md` Lemma 1-3에서
일반적으로 증명됨, ell과 무관.**

**3단계(hex0 강제 폐쇄, 손증명, 라운드13 Hub Touch Count≤2에서
직접 도출)**: completer가 hex0의 두 번째 터치이므로, 그 순간부터
hex0가 새로운 current_hex가 되고 F 예산이 이미 소진되었으므로 더
이상 abandon할 수 없다 — 하지만 `ell=4`에서는 completer 자체가
이미 마지막 위치(5)를 채우므로, **hex0는 즉시(추가 회전 없이)
완전히 닫힌다.** 이는 라운드15의 새 발견(Hub Exit Source Lemma의
전제조건)과 일치: hex0가 닫히는 순간 orbit1의 위치5-phase가
union-find에 등록된다.

**4단계(phase 불변, 손증명, 라운드14)**: union-find 노드가 phase를
포함하지 않으므로(`RR_PHASE_FREEDOM.md`), R1 또는 R2가 orbit1의
**어느 phase에서든** source 또는 target으로 이를 재사용하면 즉시
같은 컴포넌트에 속한다.

**5단계(R2가 실제로 orbit1을 사용하는가, corpus-exact+국소 증거,
라운드14 4단계와 동일한 gap)**: 4단계까지는 "orbit1이 등록되면
R2가 그것을 사용할 때 같은 컴포넌트가 된다"는 **가능성**만
보장한다. 실제로 R2(또는 R1)가 orbit1을 source/target으로 사용하는
사건은 45개 hub-completed 중 9개뿐이다(36개는 orbit1이 등록되어
있음에도 R2가 그것을 전혀 사용하지 않아 `unresolved`로 남는다).
**"등록되면 반드시 쓰인다"는 명제는 거짓이며, 실제 사용 여부는
corpus-exact 사실로만 확인된다.**

## Section 3 목표 정리 평가

> "RR에서 abandonment ell=4이고 R2가 same-component이면 R2는
> chaining이다."

**이 방향은 정의상 자명하게 참이다** (`same-component`가 `chaining`
관계의 부분집합이라는 것이 Round 14 relation lattice에서 이미
유한 완전 검증됨, `same-component ⟹ chaining` 10/10). ell=4로
좁혀도 이 함의는 그대로 상속된다(9/9, 반례 0) — **유한 완전
검증**.

**premise를 완화할 수 있는가(같은 orbit 등록만으로 충분한가)?**
**아니오, 반증됨**: 45개 hub-completed 중 36개는 orbit1이 등록됐지만
R2가 same이 아니다. "hub 존재 + completer=orbit1"만으로는
불충분하며, R2 자신이 실제로 그 orbit을 source/target으로 사용해야
한다(1-4단계는 **필요조건**, 5단계가 **충분조건을 결정**하며 이
부분만 corpus-exact다).

## 정직한 최종 판정

| 구성요소 | 증명 상태 |
|---|---|
| 1단계(orbit1 유일 강제) | 손증명(일반, ell=4에 한정) |
| 2단계(union-find 병합) | 손증명(완전 일반) |
| 3단계(hex0 즉시 폐쇄) | 손증명(ell=4의 조합론적 결과) |
| 4단계(phase 불변) | 손증명(완전 일반) |
| 5단계(R2가 실제 orbit1 사용) | corpus-exact(9/45, 반례로 36개 unresolved 존재 — "등록⟹사용"은 반증됨) |
| **same-component ⟹ chaining (ell=4 한정)** | **유한 완전 검증**(9/9, same-component 자체가 이미 이 함의를 상속하므로 자명) |

Round 14 대비 이번 라운드는 3단계(hex0 즉시 폐쇄)를 hex0의
"닫힘"이라는 명시적 메커니즘으로 재서술했고, 5단계의 실패율
(36/45가 unresolved로 남는 이유)을 정량화했다 — 그러나 5단계
자체를 일반 손증명으로 완성하지는 못했다(왜 정확히 9개만 orbit1을
쓰는지에 대한 구조적 판별 규칙은 미완료).
