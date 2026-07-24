# R–A2 word를 restart-block으로 분해

산출: `src/analyze_restart_blocks.py` -> `outputs/ra2_restart_blocks.json`.

## 1. Restart label — hex 층위에서는 자명, orbit 층위에서 실질적

**증명(연역적, 그리고 107개 조인트 전부 계산으로 재확인)**: A2가
발동하기 전(F=0 구간 전체 — R 자신 포함)에 발동하는 모든 joint는
반드시 **완전히 새(fresh) hexagon**을 target으로 삼는다.

이유: `f1_normal_form`은 F=0인 동안 "partial hex는 최대 1개
(=current)"를 강제한다. joint의 target hex가 (a) 이미 부분적으로
방문됐다면 — target이 아직 current가 되기 전이므로 그 순간 2개의
partial hex가 동시에 존재하게 돼 즉시 불법이고, (b) 이미 FULL이라면
— 애초에 방문할 미방문 윈도우가 없어 target이 될 수 없다. 남는
유일한 가능성은 **target hex가 정확히 0비트(완전히 새것)**뿐이다.
24개 코퍼스의 107개 non-abandoning joint 전부(R 자신 포함) 이를
만족한다(0 예외).

**따라서 hex 층위의 6개 요청 label 중 실제로 나타나는 것은 F(fresh
restart)뿐이다** — E(existing-hex re-entry), S/G(split/fragment
관련)는 **정의상 불가능**(F=0 구간에서 fragment 자체가 없음, 이미
`RA2_ZERO_CHARGE_HISTORY.md`에서 확립). C(같은 hex 내부 진행)는
joint가 아니라 rotation의 역할이다 — 각 block은 "joint로 새 hex
착지(F) + rotation으로 그 hex 진행 + 다음 joint 전 full sweep으로
종료(X)"라는 동일한 구조를 반복한다.

**의미 있는 변별력은 hex가 아니라 orbit/component 층위에 있다** —
새로 착지한 hex가 속한 **E-orbit**이 기존에 touched된 orbit인지(ν=0),
새 orbit인지(ν=1), 그리고 그 orbit이 R의 target과 같은
incidence-component에 속하는지가 실질적인 block 분류 기준이다.

## 2+3. Block decomposition — U4와 C20을 가르는 정확한 패턴 발견

24개 전부를 `R [block_1 ... block_m] A2` 형태로 분해했다(각 block =
1 macro-edge). **block 수(m)로 그룹화하면 뚜렷한 패턴이 나온다:**

| block 수(m) | 개수 | 그룹 | 패턴 |
|---:|---:|---|---|
| 0 | 10 | C20 전부 | R과 A2 인접(이미 `RA2_A2R_EXCHANGE_THEOREM.md`에서 다룸) |
| 1 | 11 | **C20 9개 + U4 2개** | 아래 참조 — **완벽히 갈린다** |
| 2 | 2 | U4 전부 | 아래 참조 |
| 4 | 1 | C20 1개(e2b44997e783) | 별도 outlier |

### m=1 그룹(11개, 같은 크기 비교 가능) — 정확한 이분

**C20의 9개(13ae04d9f7a5, 15186b558afe, 24378473d599, 2d8f56bd04e0,
528ceea70a6d, 587d7a77e0ef, 6ebc7a68a8ec, d5ab8253bc8d, e59ee0038f25)
전부**: 유일한 word block은 **weight-2(Z2), R 자신의 target
orbit(q=0)을 리터럴로 그대로 재사용(target_orbit_q=0=R_target_q),
component_relation="same"**.

**U4의 2개(17a42b24ccfb, 29f6af1e8aee) 전부**: 유일한 word block은
**weight-3(Z3), R과 무관한 완전히 새 orbit(q=138), novelty=fresh,
component_relation="unresolved"**.

**11/11개 전부 예외 없이 이 이분법을 따른다** — C20은 "R의 orbit을
바로 재사용", U4는 "R과 무관한 새 orbit을 연다."

### m=2 그룹(U4 2개) — m=1 U4 패턴을 정확히 포함

`1d8b48ab7d56`, `86ec22eaaba4` 둘 다: **block 1 = C20과 정확히
같은 패턴(Z2, target_q=0, same-component) + block 2 = m=1 U4와
정확히 같은 패턴(Z3, target_q=138, unresolved-component).**

**즉 U4의 4개 상태 전부에서, A2 바로 직전 block은 예외 없이
"weight-3, R과 무관한 fresh orbit(q=138), component 미해결"이다 —
C20 9개(m=1)는 이 마지막 block이 없고 대신 "weight-2, R의 orbit
재사용" 하나로 끝난다.**

### Outlier(e2b44997e783, C20, m=4) — 부분적으로만 U4 패턴과 유사

이 상태의 마지막 block도 "Z3, target_q=138, unresolved"로 **U4와
동일한 마지막-block 시그니처를 갖는다** — 그러나 이 상태는 U4가
아니라 C20(capacity_failure_found)이다. 이는 "마지막 block =
Z3-fresh-138"이 **U4를 식별하는 필요조건이지 충분조건은 아니라는
것**을 보여준다(정직하게 기록) — 최종 구별은 여전히 `ell_A2`(이전
라운드에서 이미 확립: 이 상태는 ell_A2=0)에 달려 있다.

## 정직한 요약

**새로 발견한 것**: U4 4개 전부(그리고 그들만 — outlier 1개 제외)의
A2 직전 마지막 word-block은 "weight-3, R과 무관한 fresh orbit,
component 미해결"이라는 **정확한 공통 패턴**이다(`m=1`,`m=2` 그룹
6개 전부에서 검증). 이는 U4가 단순히 "ell_A2=4"라는 것 이상으로,
**그 직전 준비 단계의 구조도 C20과 체계적으로 다르다**는 것을
보여주는 새로운 사실이다. 다만 이 패턴이 U4를 **완전히**
식별하지는 못한다(outlier 1개 반례) — 최종 판별자는 여전히
`ell_A2`다.
