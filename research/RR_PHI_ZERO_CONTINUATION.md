# Φ=0 이후의 continuation 구조

산출: `src/search_rr_same_component.py` -> `outputs/rr_same_component_exact_search.json`.

## 7. Φ=0 exact consequences

이미 증명된 `Φ(S') = Φ(S) + (ell-5)`를 사용해 다음 질문에 답한다.

**1. R2 이후 모든 joint가 ell=5로 강제되는가?** — **그렇다, 그러나
Φ 자체 때문이 아니라 F≤1 예산 때문이다.** 직접 코드 검증(post-R2
상태에서 `macro_edges()` 전체 열거): ell<5인 모든 후보(Z2abandon,
A3 등 abandoning 이동)는 전부 `area_a_prune_reason`에 의해
`F_exceeded`로 pruning된다(F=1이 이미 소진, 추가 abandon 시도
자체가 F=2를 만들어 불법). ell=5인 후보(Z2, Z3)만 legal하게
남는다. **Φ=0은 이 사실과 정확히 호환되는 결과이지, Φ 자체가
독립적으로 이 강제를 만드는 것은 아니다** — F≤1이 이미 ell=5를
강제하고 있으므로, ell=5 이동에서 Φ가 불변(`+0`)이라는 사실이
Φ=0을 그대로 유지시켜 줄 뿐이다.

**2. Pure-rotation suffix 예외는 어떻게 처리되는가?** — 완주
직전의 "순수 회전으로만 끝나는" 구간(area_a_final 판정 직전 마지막
hex를 조인트 없이 회전만으로 완성)은 이 project의 `area_a_final`
정의(P, O, D, F가 목표값에 도달)에 이미 포함된 개념이며, 별도
처리가 필요 없다 — `bounded_closure_search`가 매 상태마다
`area_a_final`을 직접 체크한다.

**3. ell=5 transition의 event type은 무엇인가?** — F=1이 이미
소진됐으므로 abandonment=False(blocked)인 이동만 가능하다: 이는
Z2(weight=2, existing) 또는 Z3(weight=3, new_orbit) 둘 중 하나다
(R/A2/A3/J는 이 시점에서 전부 배제 — R도 이미 두 번 다 썼으므로
"charged N budget"이 소진됨, `N_exceeded_monotone`으로 pruning
관측됨).

**4. ell=5만으로 남은 completion demand를 만족할 수 있는가?** —
**미결정.** 필요한 것: P를 6→121(115회 pass-start), O를 2→25(23개
새 orbit), 그리고 D=4 도달. §11의 bounded search가 이를 직접
검증하려 했으나 node_cap에 도달해 판정하지 못함.

**5. hub/chaining component를 다시 touch해야 하는가?** — **아니오,
불가능하다.** `RR_HUB_TOUCH_COUNT.md`의 손증명에 의해 hub(hex0)는
이미 2회 touch로 영구히 닫혔다 — 어떤 미래 조인트도 hex0을 다시
target으로 삼을 수 없다. §8-9에서 이것이 정확히 무엇을 의미하는지
분석한다.

## 8-9. Φ=0 zero-charge continuation graph — hub 재접촉 금지와의 결합

`bounded_closure_search`(node_cap=30,000, 10개 witness 전부)의 실측
결과:

```
python3 src/search_rr_same_component.py --node-cap 30000
→ 10개 전부: nodes=30000(cap 도달), exhaustive=False, success=False,
  non_ell5_transitions_ever_legal=0, hub_hexagon_touches_seen=0
```

**`non_ell5_transitions_ever_legal=0`**은 §7의 답 1을 30,000개
상태 전체에서 직접 재확인한다(예외 없이 ell=5만 legal). **`hub_
hexagon_touches_seen=0`**은 §7의 답 5를 재확인한다 — 30,000개 상태
동안 단 한 번도 hex0이 다시 target이 되지 않았다(당연히,
Lemma B가 이를 구조적으로 배제하므로).

### P1-P4 후보 판정

**P1("R2 이후 완주하려면 hub component를 다시 사용해야 한다")**:
**미결정.** 이것이 참인지는 이 project의 완주 조건(P=121, O=25,
D=4)이 정확히 어떤 orbit들을 필요로 하는지에 달려 있는데, 이는
경로에 따라 다르며 일반적으로 답할 수 없었다.

**P2("hub는 이미 두 번 touched되어 추가 touch가 불가능하다")**:
**손증명**(`RR_HUB_TOUCH_COUNT.md` §2).

**P3("hub를 피하면 remaining component/orbit demand를 충족할 수
없다")**: **미결정.** orbit slack(TARGET_O - O = 23)이 남아있고,
hub 외에도 143개의 다른 orbit이 있으므로 원칙적으로 hub 없이도
23개를 채울 수 있어 보이지만, 이것이 실제로 legal한 ell=5-only
경로로 실현 가능한지는 검증하지 못했다.

**P4("Φ=0이라 우회용 short transition을 사용할 수 없다")**:
**손증명**(§7 답 1 — 이미 F≤1이 그 자체로 강제하며, Φ=0은 이와
일관된 결과다).

### 결합 결론

P1, P3이 미결정이므로, **"same-component RR branch는 완주
불가능하다"는 목표 정리는 확립하지 못했다** — P2, P4는 확실히
참이지만, 이것만으로는 완주 불가능성을 도출하기에 부족하다(P2/P4는
"어떻게 진행해야 하는지"를 강하게 제한할 뿐, "진행이 불가능하다"는
것을 보이지 않는다).

## 10. Chaining 이후 orbit demand — κ

**κ(S) = remaining required fresh openings - available ell=5-compatible
fresh openings** 형태의 정량화를 시도했으나, "available ell=5-compatible
fresh openings"를 일반적으로 계산하는 것 자체가 이 project 전체의
미해결 난제(J/U-branch capacity 문제, 이전 라운드들에서 반복
확인됨)와 동일한 난이도이므로, 이번 라운드에서 새로운 정량화를
완성하지 못했다. `RR_CHAINING_COMPLETION_COST.md`(라운드 12)의
**κ_chain = Φ**가 이미 이 자리를 차지하는 가장 정확하고 증명된
양이며, same-component 10개 전부에서 κ_chain=0임을 재확인한다.
`κ_hub`(hub-dependent demand 특화 버전)는 P1/P3이 미결정이므로
정의를 시도하지 않았다 — **미완료**로 남긴다.
