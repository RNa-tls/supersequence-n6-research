# Trailing edge 상한과 2-vs-3 판정 predicate (라운드 21)

산출: `src/verify_rr_preparation_parity.py` ->
`outputs/rr_trailing_edge_predicate.json`. completion search 없음.

## 15. 상한 논증 — 그리고 라운드19 설명의 정정

라운드19는 "정확히 3개"의 근거로 다음을 들었다:

> "ell=5의 조인트 4개 중 `w3:120`은 이 상태들에서 **여전히
> abandonment**여서 `F_exceeded`로 제거된다."

**이 설명은 틀렸다.** 이번 라운드가 모든 후보 조인트를 직접
검사한 결과, terminal 상태에서 `ell=5`인 RR 조인트 중
`F_exceeded`로 제거되는 것은 **하나도 없다**(`F_exceeded=[]`,
14/14). `w3:120`이 빠지는 진짜 이유는 **target permutation이 이미
방문됨(literal collision, `exact.extend()`가 `None` 반환)** 이다.

### 정정된 논증

| 단계 | 내용 | 등급 |
|---|---|---|
| 1 | R2 이후 `F=1` 소진 ⟹ `ell<5` macro-edge는 전부 abandonment ⟹ `F_exceeded`로 제거 | **손증명** |
| 2 | 따라서 `ell=5`만 남는다 | **손증명** |
| 3 | 이 모델의 조인트는 정확히 4개(`UNIQUE_WEIGHT2_MOVE_THEOREM.md`) ⟹ **상한 4** | **손증명** |
| 4 | 그중 `w3:120`은 관측된 모든 terminal 상태에서 방문 충돌로 제거 ⟹ 상한 3 | **root-local exhaustive**(14/14), 손증명 아님 |

> **정정된 정리**: legal trailing edge 수는 **손증명 가능한 상한이
> 4**이고, "≤3"은 `w3:120`의 충돌에 의존하는 **관측**이다.
> 라운드19/20의 "손증명된 상한 3"은 이 정도로 약화된다.

## 16. 2-vs-3 판정 predicate — 정확히 하나의 occupancy bit

`ell=5`의 4개 조인트 중 각각의 target permutation이 이미 방문됐는지
검사한 결과:

| 상태 | 충돌하는 RR 조인트 (ell=5) | trailing |
|---|---|---:|
| 11개 (다른 전부) | `{w3:120}` | **3** |
| `cbfdf11e4a79` (ell=4, \|W\|=7) | `{w3:120, w3:210}` | **2** |
| `4cb55a304905` (ell=0, \|W\|=8) | `{w3:120, w3:210}` | **2** |

> **정리(root-local exhaustive, 14/14)**: trailing edge 수가 3인지
> 2인지는 **`w3:210`의 `ell=5` target permutation이 이미 방문됐는가**
> 라는 **단 하나의 occupancy bit**로 결정된다.

### 결정적 확인 — 두 분기에서 같은 symbolic word가 같은 결과를 준다

trailing=2인 두 상태는 서로 다른 분기(ell=4, ell=0)에 속하지만
**before-C symbolic word가 둘 다 `EEFEEE`로 동일**하다. 반대로
`EEFEEE`가 아닌 12개는 전부 trailing=3이다.

> **따라서 이 occupancy bit는 preparation의 symbolic word로 예측
> 가능하다**: \(P=\texttt{EEFEEE}\) ⟺ trailing=2 (2/2, 그리고
> 반대 방향 12/12). 이는 라운드20이 "`fresh_orbit_openings`가
> trailing signature에 필요하다"고 찾은 ablation 결과와 정합적이며,
> 그보다 더 정밀하다.

**주의**: 이 대응은 관측된 14개에서 예외가 없지만, `EEFEEE`가
왜 하필 `w3:210` 충돌을 낳는지에 대한 **구조적 이유는 규명하지
못했다 — 미완료.**

## Decoration에 추가해야 하는가

라운드20의 decoration 필드로는 이 비트를 **계산할 수 없다**(방문
마스크가 decoration에 없음). 그러나 `ExactState`의 `visited` 마스크에서는
직접 읽을 수 있고, 또한 **symbolic preparation word에서 예측
가능**하다(위 대응). 따라서 decoration을 늘리는 대신
**symbolic word를 decoration에 포함**하는 편이 자연스럽다 — 이번
라운드는 그 변경을 구현하지 않았다(**미완료**).

**성공 기준 6(trailing edge 2/3 판정 predicate) 평가: 달성**
— 단, 판정 비트는 찾았으나 그 비트가 발생하는 구조적 이유는
미완료.
