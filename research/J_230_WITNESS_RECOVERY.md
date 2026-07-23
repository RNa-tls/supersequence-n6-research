# J 상태 230개 literal witness 복구

산출: `src/recover_j_witnesses.py` -> `outputs/j_230_literal_witnesses.json`.
검증: `src/verify_j_witnesses.py` -> `outputs/j_230_witness_verification.json`.

## 방법

230개 J 상태의 `state_hash`는 SHA-256이라 역산이 불가능하다. 유일하게
정직한 복구 방법은, 그 해시들을 원래 만들어낸 **바로 그 bounded 탐색**을
그대로 재현하는 것이다 — 이 코퍼스 자신의 `checkpoint_header`에 이미
기록된 설정 그대로: `node_limit=20000, max_macro_depth=6,
canonical_children=True` (`legacy_research/outputs/f1_n2_depth6_decomposition.json`
-> `checkpoint_header.config`). 이는 새로운/더 큰 탐색이 아니라, 이미
한 번 완료된 이 bounded 계산을 재현해 보존되지 않은 literal 세부사항을
복구하는 것이다.

`src/recover_j_witnesses.py`는 이 탐색을 재현하면서 모든 accepted canonical
state에 대해 parent pointer(부모 hash + macro edge label + 그 transition의
weight/abandonment/new_orbit/delta)를 기록한다. 실행은 두 라운드로 나뉘어
resumable checkpoint(저장소 밖 스크래치 디렉터리)를 통해 이어졌다:

| 라운드 | expanded | node_records | found |
|---|---:|---:|---:|
| 1 (9분 예산 소진) | 11,017 | 46,198 | 57/230 |
| 2 (동일 node_limit=20000까지 재개) | 19,971 | 85,238 | **230/230** |

**두 번째 라운드가 `node_limit=20000`에 도달하기 직전(19,971 expanded)에
230개 전부를 찾았다** — 이는 이 코퍼스 자신이 기록한 원래 탐색의 bound와
정확히 같은 지점이며, 그 이상으로 탐색을 확장하지 않았다.

## 결과 — **유한 완전 검증**

- 230개 전부 복구됨, 누락 0개.
- `src/verify_j_witnesses.py`가 **독립적으로** (recover 스크립트의 북키핑을
  재사용하지 않고, macro-path label을 직접 파싱해 `exact.extend`를
  다시 호출) 230개 전부를 재생했다. 결과: **230/230 PASS**.
  - 저장된 `state_hash`와 재계산 hash 일치
  - 매 step의 (weight, abandonment, new_orbit, ΔF, ΔS) 기록값과 재생값 일치
  - J 직전 `Ndef<2`, J 및 그 이후 `Ndef==2`
  - J의 `(ΔF,ΔS,ΔO,ΔN)=(1,1,0,2)` 정확히 일치
  - 최종 `(F,H,Ndef)=(1,0,2)`
- 기존에 알려진 유일한 literal representative(hash
  `1a1ac861...`)가 이 230개 안에 그대로 존재하며, 그 macro-path
  (`rot^5;w3:201, rot^5;w2:10, rot^5;w2:10, rot^5;w2:10, rot^1;w3:120`)가
  이전 `analyze_j_completion.py` 결과와 정확히 일치한다 — 두 개의 서로
  다른 세션/스크립트가 같은 상태에 대해 동일한 재생 결과를 낸 것으로,
  교차검증이 된 셈이다.

## 이번 복구가 보장하지 않는 것

- 이 230개는 depth-6 bounded 탐색의 "canonical" 대표다 — 즉 각 상태는
  실제로는 **left-S6 등가류 전체를 대표하는 하나의 표준형**이다. 등가류의
  다른 원소들의 literal walk는 복구하지 않았다(필요하지도 않다 — 정리
  J-1/J-2/J-3과 이후 분석 전부 canonical 표준형에 대한 것이면 등가류
  전체에 대해 성립한다, left-S6 equivariance가 이미 증명되어 있으므로).
- 이 복구는 이 230개 상태가 "완주 가능한지"에 대해 아무것도 말하지 않는다
  — 단지 그 상태들이 **어떻게 도달됐는지**를 재생 가능하게 만들었을 뿐이다.
  완주 가능성은 `J_DECISIVE_EVENT_SEARCH.md`, `J_BRANCH_CLOSURE_STATUS.md`
  참고.
