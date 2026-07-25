# 비가환 사건 작용 (라운드 25)

## 4-5. 생성원과 비가환성

`ell=5` 강제(손증명)에 의해 preparation 사건은 네 생성원의 우측 곱이다:

| symbol | 생성원 \(g=\Sigma^5\cdot a\) | 부호 |
|---|---|---:|
| `E` (유일 weight-2) | (1,2,3,4,0,5) | +1 |
| `F`/`R` via `w3:120` | (2,3,4,0,1,5) | +1 |
| `F`/`R` via `w3:201` | (2,3,4,1,5,0) | +1 |
| `F`/`R` via `w3:210` | (2,3,4,1,0,5) | −1 |

이들은 **비가환**이며(라운드23에서 명시적 홀수 닫힌 walk 확인),
그것이 §2의 same-count/opposite-landing 쌍 11개가 존재하는 이유다.

## 판정

- **착지 위치는 순서의 함수이지 계수의 함수가 아니다** —
  exact counterexample 11쌍(`outputs/rr_same_count_opposite_order_pairs.json`).
- 그러나 이 비가환 구조에서 **parity를 강제하는 방정식은 유도하지
  못했다.** \(\S5\)가 요구한 commutation table을 계수 수준에서
  parity와 연결하는 데 실패했다 — **미완료.**

주의: symbol `F`와 `R`은 **같은 move label을 공유**할 수 있다
(둘 다 weight-3이고 `new_orbit` 여부로만 갈린다). 따라서 symbol은
생성원을 결정하지 않으며, symbolic word만으로는 군 곱이 정해지지
않는다 — 이것이 순수 symbolic 논증의 근본 한계다.
