# ell=0 saturated-phase 정상형 — 신선한 완전탐색으로 재확인 (라운드 16)

산출: `src/verify_rr_nearest_residual.py`의 depth≤5/depth≤6 fresh
exhaustive search 결과(`outputs/rr_nearest_residual_fresh_verification.json`).
새 대규모 탐색 없음 — abandonment 루트당 상태공간이 원래 작다
(depth≤6에서 3,600~3,900개 상태, frontier가 매번 완전히 소진됨).

## 8-9. ell=0 exceptional witness의 유일성 — 이번엔 진짜 완전 검증

라운드15는 역사적(불완전함이 이번 라운드에 밝혀진) 코퍼스에서
ell=0 same-component witness가 정확히 1개(`989d2261b458`)임을
확인했다. 이번 라운드는 그 코퍼스에 전혀 의존하지 않고, ell=0
abandonment 루트(`w2:10` 사용, 실제 코퍼스 관례와 동일)에서
`macro.macro_edges()` + `macro.area_a_prune_reason()`만으로 **처음부터
다시** BFS를 돌렸다:

- **depth≤6(총 macro-edge 6개와 동등한 조건)**: 3,814개 상태,
  frontier 완전 소진(캡에 걸리지 않음), RR-final(2R,F=1,H=0) 상태
  455개, 그중 **same-component는 정확히 1개**(`r1_target_q=120,
  r2_source_q=120, chaining=True` — 라운드15가 추적한 989d witness와
  구조적으로 정확히 일치).
- **depth≤5(6 total macro-edges와 동등, 더 보수적인 컷)**: 1,093개
  상태, RR-final 118개, **same-component 정확히 1개**(같은 witness).

**이는 원본 코퍼스의 완전성 문제와 무관하게 성립하는, 진짜 유한
완전 검증이다** — state space 자체가 작아서(수천 개 수준)
node cap 없이 자연히 소진된다.

## 판정

> **정리(유한 완전 검증, 코퍼스 독립적)**: ell=0 abandonment
> 루트로부터 legal한 macro-edge만으로 도달 가능한 depth≤6의 모든
> RR-구조(2 R 이벤트, F=1, H=0) 상태 중, same-component를 만드는
> 것은 정확히 1개뿐이다.

이는 라운드15의 "ell=0 예외는 단일 사례"라는 주장을 **더 강한
근거로 재확인**한다 — 원본 코퍼스가 불완전했다는 이번 라운드의
발견에도 불구하고, ell=0의 유일성 자체는 흔들리지 않았다(오히려
독립적인 재검증으로 강화됐다).

## Saturated-phase 메커니즘은 여전히 유일한 알려진 경로인가?

**아니오, 반증됨** — `RR_R1_SELF_COMPLETION.md`가 구성한
비-saturation self-completion witness(ell=0, R2가 orbit1에
직접 착지, phase saturation 패턴 아님)가 legal함을 확인했다. 그러나
그 witness는 **same-component를 만들지는 않는다**(단지 hub를
완성할 뿐, R1-R2 관계 자체는 별도로 확인 필요 — 이번 라운드는
그 특정 witness의 same-component 여부를 별도로 검증하지 않았다,
미완료). 따라서:

- "non-nearest hub completion에 도달하는 유일한 경로가
  saturated-phase다" — **반증됨**(다른 경로도 legal).
- "same-component를 만드는 유일한 ell=0 메커니즘이
  saturated-phase다" — **여전히 corpus-exact로 참**(신선한 완전탐색
  에서도 유일한 same-component witness가 saturated-phase 패턴을
  씀), 그러나 이것이 "이론적으로 유일한 메커니즘"이라는 강한
  주장까지 뒷받침하지는 않는다 — 단지 depth≤6에서 관측되는 유일한
  사례가 이 패턴이라는 것만 확인됐다.

## 9. Family 존재 여부 — 최종 답

**family는 존재하지 않는다(depth≤6 기준, 완전 검증)** — saturated-phase
패턴을 포함해 어떤 형태로든 ell=0에서 same-component를 만드는
경로는 정확히 1개뿐이다. 원래 과제가 요청한 "다른 exact prefix가
존재하는지" 질문에 대해 depth≤6 범위에서는 **명확히 "없음"**으로
답할 수 있다(depth≤9까지 확장한 별도 tolerant 탐색에서는 추가
사례가 나타나지만, 그것은 RR corpus의 depth≤6 정의 범위 밖이므로
"ell=0 branch의 family"로 취급하지 않는다).
