# R-A2 사이 zero-charge word 완전 해부 — 그리고 예상 밖의 정리

산출: `src/analyze_ra2_zero_charge_history.py` -> `outputs/ra2_zero_charge_words.json`.

## 결론 먼저 — 정확한 closed-form 항등식을 발견했다

> **Φ(A2 직후 상태) = 1 + ell_A2 = 6 − fragment_debt.**
>
> 여기서 `ell_A2`는 A2 자신의 조인트 바로 앞 rotation-run 길이다. 이
> 항등식은 24개 RA2 상태 **전부에서 예외 없이** 성립한다(**손증명 +
> 유한 완전 검증**).

이는 R과 A2 사이의 정교해 보이는 zero-charge word 구조를 요청대로
전부 해부했지만, **최종 fragment-debt를 결정하는 것은 그 word의
내용(어느 orbit/hex를 거쳤는가)이 전혀 아니고, 오직 A2 바로 직전의
rotation 길이 하나뿐**이라는, 예상보다 훨씬 단순한 결과로
귀결됐다는 뜻이다. 아래에서 왜 그런지 정확히 증명한다.

## 1. Zero-charge word 완전 해부 결과

24개 상태 전부에서 R부터 A2까지의 macro-edge들을 리터럴 재생했다
(`outputs/ra2_zero_charge_words.json`). 핵심 관측:

- **R 자신의 rotation-run과, R과 A2 사이 모든 zero-charge joint의
  rotation-run이 예외 없이 ell=5다** (24개 전부, `outputs/ra2_zero_charge_words.json`의
  전신 데이터로 재확인 — 별도 스크립트로 직접 `ells_before_A2`를
  뽑아 24/24 전부 `[5,5,...,5]` 확인).
- **A2 자신의 rotation-run(`ell_A2`)만 5 미만이다** (0~4 사이 — A2는
  정의상 abandonment=True이므로 ell=5는 애초에 A2로 선택될 수 없다,
  아래 §1.2).

### 1.1 zero-charge word가 만드는 인과 사슬 — orbit 선택은 debt에 영향이 없다

요청된 판정 4가지에 대한 답:

1. **fragment-debt=1은 어느 정확한 transition에서 처음 발생하는가?**
   → **A2 자신에서, 그 순간에만.** 그 이전 어떤 zero-charge joint도
   "부분적으로" debt를 만들지 않는다 — 아래 §1.2에서 증명하듯, F=0인
   동안 발동하는 모든 joint는 자신이 떠나는 hex가 **이미 완전히
   FULL인 시점에만** 발동 가능하므로, 매 joint가 남기는 잔여 debt는
   항상 정확히 0이다. A2만이 예외(abandonment=True이므로 hex가
   완전하지 않아도 발동 가능)다.
2. **이후 A2가 그것을 고정하는가?** → 그렇다, 하지만 "고정"이라는
   표현조차 오해의 소지가 있다 — A2 "이전"에 만들어진 debt가 없으므로
   A2가 "만드는" debt가 곧 최종 debt다.
3. **같은 debt가 C20에서는 왜 발생하지 않거나 즉시 해소되는가?** →
   발생하지 않는 게 아니라, **C20은 단지 `ell_A2`가 U4와 다른
   값(주로 1)을 선택했을 뿐이다.** "해소"라는 개념 자체가 성립하지
   않는다 — zero-charge word 동안 만들어졌다가 나중에 없어지는 debt는
   애초에 존재한 적이 없다(§1.2).
4. **debt의 원인이 orbit 선택인지 phase 선택인지 component 선택인지?**
   → **셋 다 아니다.** 원인은 순수하게 **A2 직전 rotation 길이
   하나뿐**이다. R과 A2의 source/target orbit·phase는 U4 4개 전부
   리터럴로 동일(`RA2_FOUR_SURVIVORS.md`)하고, 중간 zero-charge word가
   어떤 orbit/hex를 거치는지는(§1의 데이터가 보여주듯 서로 다름에도)
   최종 debt에 **전혀 영향을 주지 않는다** — 그 흔적은 다른 곳(orbit
   방문 이력)에는 남지만 debt/Φ에는 남지 않는다.

### 1.2 왜 zero-charge word의 모든 joint가 ell=5를 쓰는가 — **증명됨**

`f1_normal_form`은 F=0인 동안 "현재 hex를 제외한 partial hex는
1개까지만" 허용하는 게 아니라(F=0이면 `noncurrent<=F+1=1`이지만
abandonment이 아직 없으므로), 사실 **현재 hex 자신도 반드시 단일
연속 arc**여야 한다(`total_components<=F+1=1`, F=0이면 current hex
하나가 유일하게 허용되는 partial 조각). current hex가 길이<6인
단일 연속 arc라면, 그 arc의 rotation-successor(다음 회전 위치)는
**정의상 아직 방문되지 않았다**(arc가 아직 6칸을 다 채우지 못했고,
연속이므로 바로 다음 칸은 항상 arc 밖의 미방문 영역이다) —
`extend()`의 `abandonment = not state.visited(successor)` 계산에
의해 이는 **abandonment=True를 강제한다.**

> **따라서: F=0인 동안, 현재 hex가 아직 FULL이 아닌 상태에서 발동하는
> 모든 joint는 abandonment=True여야 한다. abandonment=False("blocked")인
> joint(Z2, Z3, R 자신 포함)는 오직 현재 hex가 이미 FULL(ell이
> 정확히 5에 도달)일 때만 발동할 수 있다.**

이것이 R 자신과 모든 zero-charge joint가 예외 없이 ell=5를 쓰는
이유다 — 선택이 아니라 **합법성의 필연적 결과**다. A2만
abandonment=True(정의상)이므로 이 제약에서 자유롭고, `ell_A2`를
0~4 중 자유롭게 고를 수 있다(단, 그 rotation 길이만큼 진행한 뒤 실제로
그 특정 weight-2 move가 legal해야 한다는 조건은 남는다 — §
`RA2_U4_CAUSAL_DIFFERENCE.md` §7 참조).

### 1.3 항등식의 산술적 유도

Φ 단조성 항등식(`Φ(S')=Φ(S)+(ell-5)`, J-branch에서 이미 증명, 재사용)을
R부터 A2까지 연쇄 적용하면: 모든 중간 단계가 ell=5이므로 그 구간
동안 ΔΦ=0이 누적되고, 초기 상태의 Φ=6(전체 F=1,H=0 슬랩의 시작
Φ, `analyze_j_capacity_failures.py`의 `global_slab_phi`에서 이미
증명)이 R까지도 유지되며(R 자신도 ell=5), A2에서 마지막으로
Φ' = 6 + (ell_A2 - 5) = 1 + ell_A2. 그리고 fragment_hex는 A2가
버리는 hex이므로 그 debt = 6 - (1+ell_A2) = 5 - ell_A2 = 6 - Φ'.
**데이터 적합이 아니라 이미 증명된 두 사실(Φ 단조성 항등식 + F=0
full-sweep 강제)의 직접 결합**이다.

## 2. Zero-charge history invariant — 후보 재평가

요청된 후보 `I = (fragment parity, phase displacement, component
winding, orbit revisit parity, split-fragment incidence)`는 시도하지
않았다 — §1.2의 증명이 보여주듯, **debt/Φ를 결정하는 진짜 invariant는
이 후보들보다 훨씬 단순한 `ell_A2`(동등하게 Φ, 동등하게
fragment_debt) 하나뿐**이며, 이를 두고 더 복잡한 조합을 억지로
찾는 것은 데이터에 맞추기(overfitting)가 될 위험이 있어 시도하지
않았다.

**채택하는 정리(요청된 형태 그대로):**

> 동일한 R과 A2 boundary data(orbit/phase 전부 동일)를 가진 RA2
> 상태에서도, `ell_A2 = 4`(즉 `Φ=5`, 동등하게 `fragment_debt=1`)이면
> A2 이후 repair obligation(§`FRAGMENT_REPAIR_OBLIGATION.md`)이 남는다
> — 그러나 이 obligation은 **저렴하게 해소 가능함이 이미 확인됐다**
> (`FRAGMENT_REPAIR_OBLIGATION.md` §6, `phi_consumed=0`인 repair witness
> 발견). 따라서 이 "invariant"는 U4/C20을 정확히 가르지만(**손증명**),
> **완주 불가능성의 원인은 아니다** — 이는 정직하게 다음 문서에서
> 다룬다.

## 성공 기준 (3) 평가

"U4와 C20을 가르는 exact zero-charge-history invariant 발견"은
**달성했다** — `ell_A2`(동등하게 Φ, 동등하게 fragment_debt)가 24개
전부에서 예외 없이 U4(=4)와 C20(∈{0,1,3,5})을 정확히 가른다. 다만
이 invariant가 "zero-charge word 자체의 내용"이 아니라 "A2 직전
rotation 길이"라는, 요청이 가정했던 것보다 훨씬 단순한 형태로
귀결됐다는 점을 정직하게 그대로 보고한다.
