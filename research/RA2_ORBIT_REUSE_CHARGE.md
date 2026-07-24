# Orbit-reuse charge ρ_A, 그리고 H2의 강화 시도

산출: `src/verify_orbit_reuse_charge.py` -> `outputs/ra2_target_novelty_counterfactuals.json`.

## 3. Orbit-reuse charge ρ_A — 국소·전역 두 정의 모두 U4에서 0/non-binding

`ABANDONMENT_TARGET_NOVELTY.md`에서 확인했듯 ν는 자유 선택이 아니므로,
"existing target을 선택해서 잃은 것"이라는 국소적(local) ρ_A는 오직
**같은 지점에서 existing과 fresh 둘 다 legal한 대안으로 존재했을
때만** 의미가 있다. 이를 직접 검사했다.

### 국소 정의: 각 ℓ에서 실제로 "선택"이 있었는가

U4 4개 상태 전부(같은 R/A2 boundary를 공유하므로 동일 결과)에서, ℓ=0..4
각각에 대해 legal한 weight-2 abandoning move를 전수 조사했다:

| ℓ | existing(ν=0) 개수 | fresh(ν=1) 개수 | 진짜 선택지였는가 |
|---:|---:|---:|---|
| 0 | 0 | 1 | 아니오 |
| 1 | 0 | 1 | 아니오 |
| 2 | 0 | 1 | 아니오 |
| 3 | 0 | 0 | 아니오(둘 다 illegal) |
| 4 | 1 | 0 | 아니오 |

**모든 ℓ에서 legal한 weight-2 abandoning move는 많아야 1개뿐이고, 그
novelty는 ℓ에 의해 완전히 결정된다 — 4개 전부 동일.** 즉 **국소
ρ_A = 0**이다: U4의 A2는 "existing을 선택해 fresh를 포기한" 것이
아니라, **그 지점에 애초에 fresh라는 대안이 없었다.**

### 전역 정의: 남은 orbit-opening 수요 대 남은 기회

`area_a_prune_reason`이 이미 구현한 필요조건
(`insufficient_future_orbit_opening_credit`, `new_needed >
future_joint_count + future_abandonments`)을 그대로 재유도해
U4에서 직접 평가했다:

| 상태 | 남은 orbit 수요 | 남은 joint 기회 | slack |
|---|---:|---:|---:|
| 17a42b24ccfb | 22 | 115 | **93** |
| 1d8b48ab7d56 | 22 | 114 | **92** |
| 29f6af1e8aee | 22 | 114 | **92** |
| 86ec22eaaba4 | 22 | 115 | **93** |

**전역 slack이 92~93으로 극단적으로 커서, 이 조건은 전혀 binding하지
않는다.** 목표 정리 "ρ_A>0이면 보상 orbit-opening이 강제된다"는
**U4에 적용할 대상 자체가 없다**(전제 ρ_A>0이 국소·전역 두 정의 모두에서
거짓이므로 공허하게 참).

## 9. H2 강화 시도 — H2a, H2b, H2c 전부 반증, H2d 미완료

이전 라운드에서 증명된 H2("repair는 특정 E-orbit 재사용을 수반한다")를
강화하려 했으나, 4개 후보 중 강화에 성공한 것은 없다:

| 후보 | 판정 | 근거 |
|---|---|---|
| **H2a**: repair가 반드시 **A2의 target orbit**을 재사용 | **반증됨** | 12개(4상태×3 witness) repair 전부, target orbit이 A2 자신의 target(q=1)이 아니라 **다른 orbit(q=0)**을 재사용했다 |
| **H2b**: repair가 반드시 **A2의 source component**를 재사용 | **반증됨** | A2 자신의 source orbit(q=3)조차 그 시점에 union-find에 **등록돼 있지 않다**(unresolved) — 재사용할 "A2 source component"라는 대상 자체가 없다 |
| **H2c**: repair 이후 fresh-orbit slack이 1 감소 | **반증됨** | 12/12 repair witness 전부 `new_orbit=False` — orbit slack은 **불변**이다(1 감소가 아니라 0 변화) |
| **H2d**: repair와 fresh-orbit opening을 동시에 할 수 없다 | **미완료** | 12/12 관측에서는 항상 배타적이었지만, hex와 orbit이 서로 다른 분할이라는 사실만으로 이것이 **원리적으로 불가능**하다는 증명을 구성하지 못했다 |

**정직한 요약: H2 자체("존재하는 어떤 orbit을 재사용한다")는 여전히
참이지만, "어떤 특정 orbit인지"를 A2 자신의 source/target과 연결
지으려는 모든 시도가 실패했다** — repair가 재사용하는 orbit(q=0)은
A2와 무관하게, **repair 경로 자신의 첫 준비 단계가 우연히 건드린
orbit**일 뿐이었다. 이는 H2를 완주 obstruction으로 강화하려는
방향이 이번 라운드에서도 성립하지 않는다는 것을 보여준다.

## 성공 기준 (4) 재확인 — 미달성

"H2를 completion-relevant cost 정리로 강화"는 **미달성**이다 — 4개
강화 후보 전부 반증되거나 미완료로 남았다. 이는 이전 라운드부터
이어지는 일관된 패턴(fragment-debt 계열의 어떤 obstruction 시도도
U4에 적용되지 않는다)의 연장선이며, 억지로 성공을 주장하지 않고
그대로 기록한다.
