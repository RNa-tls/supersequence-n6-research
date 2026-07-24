# Existing-target abandonment의 후속 의무, U4 특수성, novelty counterfactual, Λ potential

산출: `outputs/ra2_target_novelty_counterfactuals.json`(재사용),
`outputs/ra2_ell_counterfactuals.json`(이전 라운드 재사용, §6).

## 4. Existing-target abandonment의 exact 후속 의무

A2(항상 ν=0, `ABANDONMENT_TARGET_NOVELTY.md`)가 발동한 직후 반드시
필요한 작업을 검사했다:

| 후보 의무 | 반드시 필요한가 | 판정 근거 |
|---|---|---|
| 추가 신규 orbit 개방 | **아니다, 강제 아님** | §3의 전역 slack(92~93)이 보여주듯 남은 여유가 막대해 "보상"이 강제되지 않는다 |
| source orbit 재방문 | 미완료 | A2 source orbit(q=3)이 그 시점에 등록조차 안 돼 있어(§9 H2b), "재방문"을 요구할 근거 자체가 불명확 |
| target orbit 재이탈 | 해당 없음 | A2 이후 current hex(=target)는 정상적으로 계속 채워질 수 있다(`FRAGMENT_REPAIR_OBLIGATION.md` §5의 terminal 조건과 무관하게, target hex 자체는 fragment가 아니라 current다) |
| component merge | 미완료 | 검증 안 함(범위 밖) |
| **hole repair** | **필요(terminal 전까지)** | `FRAGMENT_REPAIR_OBLIGATION.md` §5에서 이미 증명 — 재확인만 |
| phase compensation | 근거 없음 | 정의된 검정 없음 |
| 추가 path 생성 | 해당 없음 | 이 모델에서 "path"는 매 joint가 자동으로 만드는 것이지 별도 의무가 아니다 |

**hole repair를 제외하면, "existing-target abandonment이기 때문에"
강제되는 후속 의무는 발견되지 않았다.** hole repair 자체는 이미
저렴함이 증명됐다(`FRAGMENT_REPAIR_OBLIGATION.md`).

## 5. U4 대 non-U4 existing-target 비교 — U4의 특수성은 순수하게 ℓ=4다

RA2 24개 전부가 이미 existing-target(ν=0)이므로(`ABANDONMENT_TARGET_NOVELTY.md`),
"existing-target이면서 ℓ≠4"인 집합은 정확히 C20(20개)이고, "ℓ=4이면서
existing-target"인 집합은 정확히 U4(4개)다 — **RA3·A3R에는 애초에
existing-target 이벤트가 하나도 없으므로(§`ABANDONMENT_TARGET_NOVELTY.md`
§1), "ℓ=4, fresh-target"과 "ℓ≠4, fresh-target" 두 집합과의 비교는
different word(RA3/A3R)로 넘어가야 하며 직접 비교 대상이 아니다.**

**질문에 대한 답:**
1. U4의 특수성은 ℓ=4인가? → **그렇다**(`RA2_ZERO_CHARGE_HISTORY.md`,
   `RA2_ELL4_BOUNDARY_GEOMETRY.md`에서 이미 확인).
2. existing target인가? → **RA2 24개 전부가 이미 existing target이므로,
   이것만으로는 U4를 C20과 구별하지 못한다**(둘 다 existing).
3. 둘의 결합인가? → 결합이라기보다, **existing-target은 RA2라는
   word 자체의 정의적 속성이고, U4를 C20에서 가르는 것은 순수하게
   ℓ**다.
4. RA2라는 defect ordering 때문인가? → **아니다, ordering이 아니라
   naming(어떤 weight의 abandoning move인가) 때문**이다 — RA3(R
   다음 A3)도 defect ordering은 다르지만 abandonment이 두 번째로
   오는 것은 같다; 진짜 차이는 A2 대 A3라는 **어떤 weight의 joint를
   썼는가**다.

**결론: 이번 라운드가 세운 "existing-target abandonment"라는 개념
자체가, RA2 코퍼스 안에서는 이미 상수(항상 참)이므로, U4의 특수성을
설명하는 데 아무런 추가 정보를 주지 않는다 — 특수성은 여전히
순수하게 ℓ=4다(이전 라운드에서 이미 확립).**

## 6. Controlled novelty counterfactual — legal하지 않음, 이유는 정의 자체

"동일 pre-A state, 동일 weight/ℓ을 유지하면서 target만 existing↔fresh로
바꾸는" counterfactual을 시도했으나, **§3에서 이미 보였듯 이 counterfactual은
legal하지 않다** — 주어진 pre-A state와 ℓ에서 legal한 weight-2
abandoning move가 많아야 1개뿐이므로, "같은 ℓ에서 novelty만 바꾼
대안"이 애초에 존재하지 않는다. **왜 강제되는가**: 특정 ℓ만큼
회전한 뒤 도달하는 permutation은 유일하게 결정되고, 그 permutation이
어느 orbit에 속하는지(이미 방문됐는지)는 순수한 조합론적 사실이며
선택의 여지가 없다 — "같은 곳에 도달하되 다른 orbit에 속하게 하라"는
요청은 애초에 논리적으로 모순이다(target permutation이 유일하면
그 orbit도 유일하다).

**이전 라운드(`RA2_ELL4_BOUNDARY_GEOMETRY.md`)의 ℓ-sweep counterfactual이
이미 이 역할을 대신했다**: ℓ을 바꾸면 도달하는 permutation이 바뀌고,
그에 따라 novelty도 함께 바뀐다 — ℓ과 novelty는 **같은 자유도의 두
관측치**이지, 독립적으로 조작 가능한 두 변수가 아니다.

## 7. Λ potential — 시도했으나 붕괴

`Λ(S) = (Φ, fresh-orbit slack, component-root slack, phase-slot
slack)`를 시도했다. §3에서 이미 확인했듯:

- **fresh-orbit slack**은 U4에서 92~93으로 전혀 binding하지 않는다.
- **component-root slack**(§9 H2b)은 A2 source조차 등록 안 된 상태라
  정의하기도 애매하다.
- **phase-slot slack**은 `RA2_THETA_POTENTIAL.md`(이전 라운드)에서
  이미 시도해 단조성을 증명도 반증도 하지 못한 채 남아 있다.

**Λ의 네 성분 중 셋(orbit slack 제외)이 정의조차 불안정하거나
비article-binding이므로, 벡터 potential로서 실질적인 새 정보를
주지 못한다.** 이는 이전 라운드의 Ω 붕괴와 같은 패턴이다 — 다시
한번, 전체 branch에 억지로 통합하지 않고 이 사실을 그대로 기록한다.
