# A3R target-reuse 관측의 orbit-history 재정식화 — 반증

산출: `src/search_a3r_reuse_witness.py`, `outputs/a3r_reuse_search.json`
(A3R 저장 corpus 298개 **전체**, bounded depth=1 검색 — 새 large-scale
continuation search 아님: 상태당 `macro_edges()` 단 1회 호출).

## 배경 — 이전 라운드의 관측

`research/RA3_A3R_ORBIT_HISTORY_ASYMMETRY.md`(이전 라운드, 재실행
없이 참조만)가 확립한 사실: **298개 저장 A3R witness 전부에서, 그
witness 자신의 실제 recorded macro_path 안에서는 A3 이후 R이
발동하기 전까지 A3 자신이 방금 연 target orbit을 재사용하는
critical restart가 한 번도 나타나지 않는다(0/298).** 이번
라운드의 사실 목록 #7이 이를 다시 확인했다.

## Orbit-history 언어로 재정식화

`b_reuse(S) := existing(A3가 연 orbit)`를 R 발동 시점에서 평가하는
비트라고 하면, 이전 관측은 "**저장된 298개 witness 고유의 실제
경로에서** `b_reuse`가 R 발동 순간에 한 번도 True로 관측되지
않았다"는 뜻이다. 이번 라운드가 요청한 것은: (1) 그 orbit이
R-target 후보가 되기 위한 최소 준비(preparation)가 무엇인지, (2)
즉시 재사용이 endpoint/phase로 인해 막히는지, (3) 이것이 저장된
depth bound의 artifact인지 아니면 transition 정의 자체에서 오는
일반적 사실인지.

## 작은 bounded 검색 — 결과: 반증

**연역적 증명이 실패했으므로(§10 지시대로), A3 발동 직후 상태에서
`macro_edges()`를 단 1회 호출하는 깊이-1 bounded 검색을 298개
저장 witness 전체에 대해 실행했다**(대규모 탐색 아님 — 상태당
한 번의 지역 열거일 뿐).

> **결과: 298/298 전체에서, A3 직후 상태로부터 깊이 1(단 한 번의
> 추가 macro-edge)만에 A3 자신이 방금 연 orbit을 재사용하는
> **합법적이고 area_a에 의해 pruning되지 않는** R-kind joint가
> 존재한다.**

예시(`0005118bb977`): `Z2 → Z3 → A3`(target orbit `q=24`)까지
저장된 macro_path를 재생한 뒤, 그 직후 상태에서
`macro_edges()`가 내놓는 후보 중 `rot^5;w3:120`이 정확히
`abandonment=False, new_orbit=False, target_orbit_q=24`(A3와
동일)이며 `area_a_prune_reason`이 `None`(안 잘림)이다 — 즉 실제로
그 다음 한 걸음에 R이 A3의 orbit을 재사용하는 것이 완전히
합법적인 이동이다.

### 이것이 뜻하는 바

**"A3R에서 R 이전 orbit 재사용은 불가능하다"는 가설은 이제
반증됐다(298/298 exact witness).** 이전 라운드가 관측한 0/298은
**endpoint/phase가 재사용을 막아서가 아니라**, 이 298개 저장
witness들이(이 코퍼스를 만든 이전 검색 과정에서) **우연히 또는
다른 선택 기준 때문에** 재사용 경로를 택하지 않았을 뿐이라는
것이 이제 exact witness로 확인됐다. 질문 (1)("R-target 후보가
되기 위한 최소 준비")에 대한 답은 이제 **"준비가 전혀 필요 없다
— 깊이 1이 이미 충분하다"**이고, 질문 (2)("즉시 재사용이
endpoint/phase로 막히는가")의 답은 **"아니오, 막히지 않는다
(반증됨)"**, 질문 (3)("저장된 depth bound의 artifact인가")의 답은
**"그렇다 — 정확히 그것이었다"**로 확정된다.

## 목표 정리 재판정

> "A3R에서 A3와 R 사이의 pre-R orbit reuse는 불가능하다."

**증명 상태: 반증됨(exact, 298/298 완전 검증, 깊이 1 bounded
search).** 이전 라운드가 "corpus exact observation, 아직
반증되지 않음"으로 열어 둔 질문이, 이번 라운드의 작은 bounded
검색으로 **명확히 반증**됐다. 저장된 298개 witness의 recorded
macro_path 자체는 여전히 재사용을 보이지 않는다는 사실(그
자체로는 참, 그 witness들의 특정 경로에 대한 사실)과, "재사용이
구조적으로 불가능하다"는 일반 주장(거짓, 반증됨)은 이제
명확하게 분리된다.

## 성공 기준 (6) 평가

**달성됨(반증 형태)**: "A3R target-reuse 관측의 일반 정리"는
당초 기대했던 "불가능성 정리"가 아니라 **"불가능성 가설의
반증"**으로 확립됐다 — 이것도 이번 라운드 성공 기준 6이 요구한
"일반 정리"에 해당한다(반증도 정리다: "reuse는 항상 깊이 1
안에서 가능하다, 298/298"). 저장된 witness들이 왜 하필 재사용을
피하는 경로를 택했는지(이 코퍼스를 생성한 이전 탐색의 선택
기준)는 이번 라운드의 범위 밖이며 별도 조사가 필요하다 —
**미완료로 남김**.
