# N2 준비 정상형 — 단일 family로 확립되지 않음 (라운드 20)

산출: `outputs/rr_ell0_depth7_families.json`,
`outputs/rr_h3_n2_decorated_comparison.json`. 새 completion search 없음.

## 8. N2 두 state의 decorated preparation history

`ell=4`에서 preparation length **5**인 두 state:

| state | kind signature | Z3 위치 | fresh | O | completer |
|---|---|---|---:|---:|---|
| `86195429f1c6` | `[Z3, Z2, Z3, Z2, R] → R2` | {1,3} | 2 | 4 | R1 (index 5) |
| `b2898cc223e9` | `[Z3, Z3, Z2, Z3, R] → R2` | {1,2,4} | 3 | 5 | R1 (index 5) |

## §8의 다섯 질문에 대한 판정

| 질문 | 판정 |
|---|---|
| 두 N2가 하나의 parameterized family인가 | **아니오 — 확립되지 않음.** Z3 개수가 2와 3으로 다르고 배치도 `{1,3}` vs `{1,2,4}`로 공통 패턴이 없다. 사례가 2개뿐이라 매개변수화를 세울 근거가 부족하다. **미완료.** |
| Z3 opening 위치가 유일한가 | **아니오, 반증됨.** 두 사례의 Z3 위치 집합이 다르다. |
| 추가 fresh orbit이 terminal state에 남기는 흔적 | `O`가 2에서 4~5로 증가하고 `fresh_orbit_openings`가 0이 아니게 된다. **그러나 terminal signature(R1 target, R2 source/target, completer 착지점, Φ, chaining)에는 아무 흔적도 남기지 않는다** — 아래 참고. |
| H3와 동일 decorated terminal state가 가능한가 | **아니오.** decoration에 `fresh_orbit_openings`와 `preparation_family`가 포함되므로 H3(0)와 N2(2~3)는 항상 다른 decorated state다. |
| ExactState는 같은데 decoration만 다른 경우가 생기는가 | **이 universe에서는 발생하지 않는다** — 모든 경계가 서로 다른 raw state를 갖는다(라운드19). 따라서 **검사 자체가 공허**하며 미결정으로 남긴다. |

## H3와 공유하는 것 / 다른 것

**공유(정확히 일치)**: `hub_completer_macro_index = preparation length`
(completer는 항상 준비 구간의 **마지막** edge), `r1_r2_macro_distance = 1`,
completer 착지점 `(orbit 1, phase 4)`, R2 `(1,4)→(0,2)`, Φ=0,
chaining=True.

**다름**: 준비 길이(3 vs 5), Z3 사용(0 vs 2~3), `O`(2 vs 4~5),
completer 역할(H3는 R1/Z2 혼재, N2는 항상 R1).

## depth 8에서 드러난 추가 사실 — family 분류 자체가 잠정적

depth ceiling을 8로 올리면 preparation length **7**인 state가
**4개** 더 나타난다:

| state | kind signature | fresh | O | completer |
|---|---|---:|---:|---|
| `9bd7590e3ced` | `[Z3,Z2,Z2,Z2,R,Z2,Z2] → R2` | 1 | 3 | Z2 |
| `cbfdf11e4a79` | `[Z2,Z2,Z3,Z2,Z2,Z2,R] → R2` | 1 | 3 | R1 |
| `d408ede44825` | `[Z3,Z3,Z3,Z2,Z3,Z3,R] → R2` | 5 | 7 | R1 |
| `ec9025e8706b` | `[Z2,Z3,Z2,Z2,Z2,R,Z2] → R2` | 1 | 3 | Z2 |

**이들은 라운드19가 세운 "H3(fresh 0) vs N2(fresh 다수)" 이분법에
깔끔히 들어맞지 않는다** — fresh가 1인 것이 3개다. 따라서

> **준비 family를 "fresh-opening 유무"로 나눈 라운드19의 분류는
> depth 8에서 무너진다.** 더 안정적인 분류 축은 **preparation
> length**(3, 5, 7 — 전부 홀수)이며, 각 길이 안에서 Z3 개수가
> 다양하게 나타난다.

**증명 등급**: root-local exhaustive (depth ceiling 8, frontier
자연소진) — 단, family 구조 자체는 **미완료**(길이별 매개변수화를
세우지 못했다).
