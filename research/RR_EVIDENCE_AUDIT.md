# RR 연구 증거 기반 전면 재감사 (라운드 17)

산출: `src/audit_rr_claims.py` -> `outputs/rr_claim_audit.json`,
이번 라운드의 나머지 스크립트 결과 종합. 새 대규모 탐색 없음.

## 1. Evidence audit table

라운드11~16의 RR 핵심 주장 15개를 전수 재분류했다. 전체 표는
`outputs/rr_claim_audit.json`에 있으며, 핵심 요약:

| 주장 | 최초 등장 | 원래 label | cap 존재 | corpus 의존 | 현재 상태 |
|---|---|---|:---:|:---:|---|
| same-component ⟹ chaining | Round11/14 | 유한 완전 검증 | 예 | 예 | **capped-corpus exact** |
| chaining ⟹ not unresolved | Round9/14 | 유한 완전 검증 | 예 | 예 | **capped-corpus exact** |
| hub completer=R1 target(일반) | Round13→14 | 반증됨 | — | — | 반증됨(불변, 이미 정확) |
| abandon_ell=4⟹completer 유일(orbit1) | Round14 | 손증명 | 아니오 | 아니오 | **손증명(불변)** — 순수 조합론 |
| nearest만 실현(전체 ell) | Round15 | 유한 완전 검증 | 예 | 예 | **반증됨**(이번 라운드) |
| hub-completed⟹Φ=0(전체) | Round15 | 유한 완전 검증 | 예 | 예 | **반증됨**(7개 반례, 이번 라운드) |
| same-component⟹ell∈{0,4} | Round15 | 유한 완전 검증 | 예 | 예 | **uncapped local exhaustive**(재확인, 독립 재검증 통과) |
| ell=0 witness 유일 | Round15/16 | 유한 완전 검증 | 아니오(16부터) | 아니오 | **uncapped local exhaustive**(독립 재검증 통과) |
| forest acyclicity(0 redundant union) | — | 유한 완전 검증 | 예 | 예 | **capped-corpus exact**, 재검증 안 함 |
| delayed completer family(6개) | Round14/15 | corpus-exact | 예 | 예 | **capped-corpus exact**, 기반 수치(9) 자체가 불확실 |
| relation lattice(7개 implication) | Round14 | 유한 완전 검증 | 예 | 예 | **capped-corpus exact**(반증된 5개는 여전히 유효한 반증) |
| abandonment은 항상 w2:10 | Round16 | 유한 완전 검증 | 예 | 예 | **capped-corpus exact**, 재검증 안 함 |
| Unique Hub Hexagon | Round12 | 손증명 | 아니오 | 아니오 | **손증명(불변)** |
| Hub Touch Count≤2 | Round13 | 손증명 | 아니오 | 아니오 | **손증명(불변)** |
| Hub Exit Source Lemma | Round15 | 손증명+검증 | 부분 | 부분 | **손증명(연역 부분 불변)**, 검증 수치(212/212)만 capped-corpus exact로 재분류 |

**핵심 패턴**: 순수 코드 정의에서 연역적으로 도출된 4개 정리(Unique
Hub, Touch Count≤2, abandon_ell=4 유일성, Hub Exit Source의 연역
핵심)는 이번 감사에서 전혀 흔들리지 않았다. corpus 수치에 의존한
주장들은 전부 "capped-corpus exact"로 강등되었고, 그중 2개(nearest-only,
hub-completed⟹Φ=0)는 명시적으로 **반증**됐다.

## 13. Forest lemma scope audit

`RR_INCIDENCE_FOREST_LEMMA.md`를 재확인한 결과, 0/53,054(RR 코퍼스)와
0/85,238(broader depth≤6 샘플) 둘 다 **capped 65,340-frontier**에서
나온 수치였다 — 문서 자체가 이미 "순수 그래프 공리만으로 강제되는
일반 정리는 아니다"라고 정직하게 밝히고 있었으므로, 이번 감사가
새로 반증한 것은 아니다. **이번 라운드는 이를 uncapped local
universe에서 재검증하지 않았다** — 시간 제약으로 미완료. code
정의(union-find의 `find`/`union` 로직 자체)에서 직접 손증명하는
시도도 하지 않았다 — **미완료로 명시.**

## 14. Phi 전면 정정

`outputs/rr_corrected_phi_distributions.json`: fresh exhaustive
local search(root class 1, depth ceiling 5, frontier 완전 소진)에서
hub-touched RR-final 상태 290개 중 283개(97.6%)만 Φ=0, 7개는
Φ=ell+1. 반대 방향(hub 안 만지면 Φ≠0)은 991/991(100%) 성립 — 이
방향이 더 견고한 후보다. **7개 반례를 개별 구조로 추적하지는
못했다(미완료)** — 새로운 억지 일반 명제를 만들지 않고 정직하게
"약 98%, 완전한 필연 아님"으로만 기록한다.

## 정직한 요약

이번 감사의 최우선 목적("잘못된 완전 검증 표기를 모두 고치는 것")은
달성했다. 새 강한 정리를 만드는 대신, 기존 15개 핵심 주장의 증거
등급을 재분류하고 그중 2개의 명시적 반증을 확정했다. forest
lemma의 code-definition 손증명 시도는 이번 라운드에 완료하지
못한 채 남는다.
