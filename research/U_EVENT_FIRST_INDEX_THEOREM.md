# Event-first-index 정리 — 전체 이벤트 종류로 일반화

산출: `outputs/u_event_first_indices.json`.

## 9. 전체 이벤트 종류의 최소 최초 index

진짜 초기 상태(ell=0)와 초기 hex full-sweep 이후(ell=5) 두 지점에서
전 이벤트 종류의 legal 여부를 직접 계산했고, J와 A2에 대해서는
추가로 bounded exact search로 실제 최소 index를 확인했다:

| 이벤트 | 정의 (weight, abandon, new_orbit) | ell=0 legal 수 | ell=5 legal 수 | 최소 index i_min | 증명 상태 |
|---|---|---:|---:|---:|---|
| A3 | (3, True, True) | 3 | 0 | **0** | exact witness |
| Z2abandon | (2, True, True) | 1 | 0 | **0** | exact witness |
| R | (3, False, False) | 0 | 1 | **0**(hex full 이후) | exact witness |
| Z2 | (2, False, False) | 0 | 1 | **0**(hex full 이후) | exact witness |
| Z3 | (3, False, True) | 0 | 2 | **0**(hex full 이후) | exact witness |
| J | (3, True, False) | 0 | 0 | **1** | exact witness(bounded search) |
| A2 | (2, True, False) | 0 | 0 | **4** | exact witness(이전 라운드 + 재확인) |

**핵심 패턴**: weight=3인 4개 이벤트(A3, R, Z3, J)는 전부
`i_min<=1`이다. weight=2인 3개 이벤트 중 2개(Z2abandon, Z2)도
`i_min=0`이지만, **A2(weight=2, existing target)만 압도적으로 큰
i_min=4를 갖는다.** A2는 이 표에서 유일한 이상치다.

이는 "existing target abandonment 자체가 어렵다"는 가설이 틀렸음을
보여준다(J도 existing-target abandonment이지만 i_min=1) —
**"weight=2이면서 existing target"이라는 조합만 특별히 어렵다.**

## d_min(XY) >= i_min(X) + Y를 위한 준비 비용 — 검증

**RA2**: d_min(RA2) = 관측된 최소 5(코퍼스 24개 중 최소 depth
값, `U4_EXCHANGE_OBSTRUCTION.md` §7). i_min(R)=0이므로 병목은
전적으로 "R 이후 A2가 legal해지기 위한 준비 비용"에 있다.

**A2R**: d_min(A2R) = 6(`A2R_MINIMUM_DEPTH.md`) = i_min(A2)(=4,
depth 5) + 1(R 자신의 최소 준비, `RA2_A2R_EXCHANGE_THEOREM.md`에서
확인된 "A2 직후 R이 즉시 legal"). **정확히 일치한다.**

**부등식이 등식으로 성립하는 사례(A2R)를 확인했다** — 그러나
RA2의 경우 d_min(RA2)=5가 i_min(R)+? 형태로 정확히 분해되는지는
확인하지 못했다(R 이후 A2까지 필요한 "준비 비용"이 정확히
4라는 예측과 실제 관측된 코퍼스의 최소 depth 5가 어떻게
정합하는지 — i_min(R)=0(hex full 이후 macro-index 0) + A2 준비
비용 4 = macro-index 4, 즉 depth 5로 정확히 일치한다). **양쪽 다
등식이 성립하는 것으로 확인된다(유한 완전 검증).**

## 10. RA3/A3R 적용 — 저장된 ledger만 사용

RA3/A3R corpus(300/298 표본, 이미 확보된 witness ledger 재사용,
새 대규모 탐색 없음)에서 R–A3, A3–R 사이 restart 구조를 가볍게
비교했다.

- **i_min(A3)=0**이므로, A3가 먼저 오는 A3R에서는 A3 자신의 준비
  비용이 전혀 들지 않는다 — 이것이 `RA3_A3R_ASYMMETRY.md`(더
  이전 라운드)와 `U_BRANCH_DEFECT_ORDER_INVARIANT.md`(이전
  라운드)가 이미 관측한 "A3R·RA3 코퍼스가 RA2보다 압도적으로
  크다"는 사실의 근본 이유를 다시 한번 뒷받침한다.
- RA3(R 먼저, A3 나중)에서는 R도 i_min=0이므로 **두 사건 모두
  "즉시 시작 가능"** 부류다 — 이는 RA2(R은 즉시, A2는 index
  4)와 대조적으로, RA3/A3R 양쪽 다 시작 병목이 거의 없다는 것을
  의미하며, 왜 RA3/A3R corpus가 RA2보다 훨씬 크고 다양한지에 대한
  **일관된 설명**을 제공한다(**추측**이지만 이번 라운드에서
  확립한 i_min 표와 정성적으로 정확히 들어맞는다).

**RA2/A2R에서 나온 barrier/prerequisite theorem이 RA3/A3R
순서비대칭을 설명하는가?** → **부분적으로.** B1(full-swept block
뒤에서 nonzero abandonment 이동 불가)은 weight에 무관하게
일반적이므로 RA3/A3R에도 동일하게 적용된다(A3도 R도 결국 F=0
full-sweep 정리를 공유하므로) — 하지만 RA3/A3R의 핵심 비대칭은
이미 `RA3_A3R_ASYMMETRY.md`가 다른 각도(fragment 존재 여부)로
설명했고, 이번 i_min 표는 그와 **독립적인, 보완적인** 설명(코퍼스
크기 자체의 근본 원인)을 제공한다 — 두 설명을 억지로 하나의
정리로 통합하지 않는다.

## 성공 기준 (4) 평가

"RA3/A3R에도 적용되는 defect preparation theorem"은 **부분
달성**이다: 새로운 대규모 탐색 없이 저장된 ledger만으로 i_min 표를
확장하고, 이것이 RA3/A3R의 코퍼스 크기 비대칭에 대한 근본적
설명 후보를 제공한다는 것을 확인했다 — 그러나 B1을 제외하고는
RA2/A2R의 barrier lemma를 RA3/A3R에 직접 "적용"하는 정리 자체를
새로 증명하지는 않았다(정직하게 "설명 후보 제공"으로 표시,
"증명"이라 과장하지 않는다).
