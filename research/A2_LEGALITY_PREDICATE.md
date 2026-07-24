# A2 legality의 exact predicate

산출: `src/analyze_a2_legality_history.py` -> `outputs/a2_rotation_candidate_tables.json`.

## 핵심 단순화 사실 — 이 모델에는 weight-2 move가 정확히 1개뿐이다

`exact.ALL_MOVES`를 직접 조사한 결과: **weight=2인 move는 전체
모델에 정확히 1개(`w2:10`)뿐이다.** 이는 지난 여러 라운드에서
반복 관측된 "주어진 지점에서 legal한 weight-2 abandoning move는
많아야 1개"라는 현상의 **근본 원인**이었다 — 선택의 여지가
없었던 게 아니라, 애초에 후보가 하나뿐이었다.

## 2. A2Legal(S, ell)의 정확한 필요충분조건

critical restart 착지 직후(ell=0) 상태를 `S`라 하고,
`p_ell = SIGMA^ell(S.p)`라 하면(즉 `ell`번 순수 회전한 위치),
`extend()`의 코드 정의로부터 직접 유도한다:

\[
\operatorname{A2Legal}(S,\ell)
\iff
\underbrace{\neg\,\mathrm{visited}(\mathrm{target}(\ell))}_{\text{(a) target 미방문}}
\;\land\;
\underbrace{\neg\,\mathrm{visited}(\sigma(p_\ell))}_{\text{(b) abandonment=True}}
\;\land\;
\underbrace{\mathrm{orbit\_masks}[q(\ell)]\neq 0}_{\text{(c) target orbit가 existing}}
\]

여기서 `target(ell) = word_after(p_ell, w2_10.action)`,
`q(ell) = ORBIT_PHASE[target(ell)].q`, `σ`는 rotation(SIGMA) 액션이다.

**세 조건은 서로 독립적으로 실패할 수 있다**(24개 코퍼스 전체에서
관측된 `fail_reason` 분포):

- `target_already_visited` — (a) 위반.
- `abandonment_false_hex_already_full_or_blocked` — (b) 위반(주로
  ell=5, hex가 이미 FULL이라 자연 발생).
- `target_orbit_fresh_not_existing` — (c) 위반, **U4/C20을 가르는
  실질적 조건**.

## 3. 24개 전체 후보 테이블 — 정확히 1개의 legal ell

24개 RA2 전부에서 ell=0..5를 전수 조사한 결과 **예외 없이 정확히
1개의 ell만 legal**하다(이전 라운드의 5-state 결과가 24개 전체로
확장, 유한 완전 검증):

| ell | 어떤 상태들이 여기서 legal한가 |
|---:|---|
| 0 | outlier(`e2b44997e783`) 1개 |
| 1 | C20 대부분(19개 중 다수) |
| 3 | `d92abc8c8e61` 1개 |
| 4 | **U4 4개 전부** |

(24개 = 위 합. `outputs/a2_rotation_candidate_tables.json`의
`legal_ells` 필드가 각 상태마다 정확히 1개 값을 가짐을 직접 확인
가능.)

## 방법론 참고 — 이번 라운드에서 발견하고 수정한 두 개의 버그

1. 초기 버전은 A2가 항상 macro_path의 **마지막** 항목이라고
   가정했다(`path[:-1]`) — 틀렸다. 일부 witness(예:
   `15186b558afe`)는 A2 이후에도 추가 zero-charge joint를 가진다.
   A2의 실제 index를 joint kind로 직접 찾도록 수정했다.
2. 수정 후에도, "pre-A2 상태"를 A2 **자신의 실제 ell만큼 이미 회전한
   지점**으로 잘못 반환해, ell-sweep이 엉뚱한 원점에서 시작하는
   2차 버그가 있었다 — critical restart의 **착지 직후(ell=0)**
   지점을 반환하도록 다시 수정했다. 두 수정 모두
   `outputs/a2_rotation_candidate_tables.json`에 기록된, 실제
   코퍼스가 기록한 ell_A2 값과 정확히 일치하는 결과로 검증했다.
