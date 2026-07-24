# Abandonment 2축 (ℓ, ν) 분류 — ν는 자유 축이 아니라 정의의 결과다

산출: `src/analyze_abandonment_target_novelty.py` -> `outputs/abandonment_length_novelty_table.json`
(RA2 24개 + RA3 300개 표본 + A3R 298개 표본, 총 622개 abandonment 이벤트 재추출 — 새 탐색 없음, 기존 witness 재사용).

## 결론 먼저 — 핵심 재발견

**\((\ell_A,\nu_A)\)는 독립적인 2차원 공간이 아니다.** 이 프로젝트가
세션 초반부터 사용해 온 joint 분류 자체가 이미 \(\nu\)를 고정한다:

- **"A2"는 정의상 `(weight=2, abandonment=True, new_orbit=False)`,
  즉 \(\nu_A=0\)이 항상 성립한다.**
- **"A3"는 정의상 `(weight=3, abandonment=True, new_orbit=True)`,
  즉 \(\nu_A=1\)이 항상 성립한다.**
- `(weight=2, abandonment=True, new_orbit=True)`는 **"Z2abandon"**이라는
  **별도의, zero-charge** joint 종류다(U-branch의 두 결함 이벤트로
  카운트되지 않음).
- `(weight=3, abandonment=True, new_orbit=False)`는 **"J"**라는
  **charge+2**의 J-branch 이벤트다(U-branch 코퍼스와 애초에 분리된
  다른 corpus).

이는 세션 시작 시점부터 이미 확립돼 있던 joint taxonomy(`joint_kind`
함수, 이 연구 전체에서 반복 사용됨)의 직접적 귀결이며, 이번 라운드는
이를 622개 실제 이벤트로 **재확인**했다(새로운 사실이 아니라, 이번
요청이 가정한 "ν가 자유 선택"이라는 전제가 성립하지 않음을 명시적으로
검증한 것).

## 1. 2축 분류표 — 622개 이벤트 전량

| (ℓ,ν) | 개수 | word 분포 | Φ(A 이후) | debt(A 이후) |
|---|---:|---|---:|---:|
| (0,0) | 1 | RA2 | 1 | 5 |
| (0,1) | 129 | A3R 60, RA3 69 | 1 | 5 |
| (1,0) | 18 | RA2 | 2 | 4 |
| (1,1) | 128 | A3R 71, RA3 57 | 2 | 4 |
| (2,0) | **0** | — | — | — |
| (2,1) | 133 | A3R 76, RA3 57 | 3 | 3 |
| (3,0) | 1 | RA2 | 4 | 2 |
| (3,1) | 82 | A3R 37, RA3 45 | 4 | 2 |
| (4,0) | 4 | RA2(=U4) | 5 | 1 |
| (4,1) | 126 | A3R 54, RA3 72 | 5 | 1 |

**모든 ν=0(existing) 이벤트는 예외 없이 RA2에서만 나온다(1+18+1+4=24,
RA2 전체와 정확히 일치). RA3·A3R 598개 표본 전부가 ν=1이다.** 이는
"RA2라는 defect ordering 때문"이 아니라(§5에서 재확인), **"이 이벤트가
A2라는 이름표를 갖는가, A3라는 이름표를 갖는가"라는, 이미 정의로
고정된 사실 때문**이다.

## 2. Local truth table — 정의로부터 직접 도출

| (weight, ν) | 대응 joint 이름 | ℓ=0 | ℓ=1 | ℓ=2 | ℓ=3 | ℓ=4 | ℓ=5 |
|---|---|---|---|---|---|---|---|
| (2, ν=0) | **A2** | exact witness | exact witness | exact witness(depth=7, `A2_ROTATION_LENGTH_CLASSIFICATION.md`) | exact witness | exact witness(=U4) | **정의상 불가능**(F=0 full-sweep 정리) |
| (2, ν=1) | Z2abandon(zero-charge, "A2"로 카운트되지 않음) | — | — | — | — | — | 정의상 불가능(동일 정리) |
| (3, ν=1) | **A3** | exact witness | exact witness | exact witness | exact witness | exact witness | 정의상 불가능(동일 정리) |
| (3, ν=0) | J(charge+2, U-branch corpus 밖) | — | — | — | — | — | 정의상 불가능(동일 정리) |

**"동일 source boundary에서 두 novelty가 모두 가능한가?"**라는 질문에
대한 답은 §`RA2_ORBIT_REUSE_CHARGE.md`에서 직접 계산으로
확인한다 — 미리 답을 말하면: **아니다, 매 ℓ마다 legal한 weight-2
abandoning move는 많아야 1개뿐이고, 그 하나의 novelty가 ℓ에 의해 이미
결정돼 있다(선택의 여지가 없다).**

## 성공 기준 (1) 평가

"가능한 \((\ell_A,\nu_A)\) 조합의 완전 local truth table"은
**달성됐다** — 단, 요청이 가정한 "2×2 자유 조합"이 아니라 "weight로
이미 고정된 ν, 그 안에서 ℓ만 자유"라는 더 단순한 구조로
귀결된다는 것을 정직하게 함께 보고한다. 이는 데이터 부족이 아니라
이 모델의 정의 자체에서 나오는 구조적 사실이다.
