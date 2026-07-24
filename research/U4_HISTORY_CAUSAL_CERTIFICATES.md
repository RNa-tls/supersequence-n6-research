# U4 vs C20 outlier — 최소 causal history certificate

산출: `outputs/a2_rotation_candidate_tables.json`(재사용).

## 1. Five-state prefix divergence — 공유되는 prefix는 없다

U4 4개와 outlier의 macro_path를 index별로 정렬해 canonical-hash가
마지막까지 동일한 지점을 찾았다: **`last_common_step_index = 0`**
— 즉 가장 이른 단계(첫 macro-edge 이후)부터 이미 canonical state가
서로 다르다. **5개 상태가 공유하는 의미 있는 prefix는 초기 상태
자체뿐이다** — 이들은 서로 완전히 다른 탐색 경로에서 왔으며, 오직
"critical restart + 그 이후 A2까지의 국소 구조"만 우연히(혹은
구조적으로) 수렴한다. 이는 §6의 발견과 일관된다: 중요한 것은
"경로 전체의 공통점"이 아니라 "critical restart 이후 도달하는
정확한 6개 candidate orbit(120,33,9,?,1,0) 목록과, 그중 어느
것이 이미 touched됐는가"라는 국소적 사실이다.

## 6. U4 대 outlier — 최소 causal certificate (핵심 발견)

`A2_LEGALITY_PREDICATE.md`의 candidate table을 U4 4개와 outlier에
대해 나란히 놓으면:

| ell | candidate target orbit | U4(4개 전부, 리터럴 동일) | outlier |
|---:|---:|---|---|
| 0 | 120 | fresh(불법) | **existing(legal)** |
| 1 | 33 | fresh(불법) | fresh(불법) |
| 2 | 9 | fresh(불법) | fresh(불법) |
| 3 | (U4: 이미 방문된 리터럴 permutation, 충돌) / (outlier: 3) | 충돌(불법) | fresh(불법) |
| 4 | 1 | **existing(legal)** | fresh(불법) |
| 5 | 0 | existing(hex full이라 rotation 자체 불법) | (ell=5 도달 못함, outlier는 ell=4에서 이미 hex가 다르게 진행) |

**U4 4개 전부(리터럴로 완전히 동일한 candidate table)와 outlier
사이의 최소 causal 차이는 정확히 두 orbit의 existing/fresh 상태
반전이다:**

> **orbit 1이 U4의 누적 이력에서는 이미 touched(existing)됐지만
> outlier의 누적 이력에서는 아직 touched되지 않았다(fresh). 반대로
> orbit 120은 outlier의 누적 이력에서는 이미 touched됐지만 U4의
> 누적 이력에서는 아직이다.**

이것이 요청된 "U4에서 ell=4 target을 legal하게 만든 과거 방문
사건"과 "outlier에서 ell=4가 막히는 최초 이유"에 대한 **정확한,
리터럴 답**이다 — U4의 이력 어딘가에서 orbit 1의 한 phase가
touched됐고(어느 이전 joint인지는 U4 4개마다 다를 수 있다 — 이
자체가 U4 4개가 서로 독립임을 보여주는 또 다른 각도다), outlier의
이력에는 그 사건이 없다. 반대로 outlier의 이력 어딘가에서 orbit
120이 touched됐지만, U4의 이력에는 없다.

**증명 상태: exact witness(5개 상태 리터럴 후보 테이블로 직접
확인, 유한 완전 검증) — 이것이 "왜"에 대한 완전한 answer는
아니다**(어느 구체적 joint가 orbit 1/120을 열었는지까지는
추적했지만 그 자체가 "왜 U4의 검색 경로가 정확히 orbit 1을
열게 됐는가"를 설명하지는 않는다 — 이는 원래 탐색이 만든 경로의
우연/구조를 그대로 반영할 뿐이다).

## 9. History perturbation — 시도, 명시적 최소 edit은 미완료

"U4와 outlier의 공통 suffix 이전 history에서 joint 하나만 교체해
ell-forcing vector가 바뀌는 최소 edit"을 명시적으로 구성하는
것은 이번 라운드에서 시도했으나 완료하지 못했다 — §6의 candidate
table 비교가 이미 "어떤 두 orbit의 existing 상태가 반전됐는가"를
정확히 답했으므로, 원리적으로 "U4의 이력에서 orbit 1을 처음 여는
그 joint를 제거하면 ell=4가 다시 illegal해질 것"이라 예측할 수
있지만, 이를 실제로 legal한 대안 이력으로 구성해 검증하지는
않았다. **미완료**로 정직하게 남긴다.

## 10. Capacity 차이와의 연결 — 이전 라운드 결과 재확인

`RA2_CRITICAL_RESTART_ANCESTRY.md`(이전 라운드)에서 이미 확인한
"U4는 depth<=6까지 capacity failure 0개, outlier는 depth 4부터
발생"이라는 결과를, 이번 라운드가 밝힌 orbit-existing 반전과
연결한다: **outlier가 ell=0에서 A2를 발동한다는 것은 Φ를
6→1(가장 낮은 값)로 떨어뜨리는 것과 동일**(`RA2_ZERO_CHARGE_HISTORY.md`의
Φ=1+ell 항등식) — 이는 orbit 120이 미리 열려 있었기 때문에
**가능해진 선택**이지, capacity failure의 직접 원인은 아니다.
즉 **"orbit 120이 미리 열림" → "ell=0이 유일하게 legal" →
"Φ=1(최소)" → "capacity failure가 얕은 depth에서 발생"**이라는
인과 사슬이며, 이번 라운드는 그 첫 번째 화살표(어떤 orbit
existing 여부가 어떤 ell을 강제하는가)를 정확히 규명했다는 점에서
이전 라운드의 결과를 한 단계 더 깊이 설명한다.
