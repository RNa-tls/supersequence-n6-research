# H3 준비 정상형 (라운드 20)

산출: `src/analyze_rr_ell0_family.py` -> `outputs/rr_ell0_depth7_families.json`,
`outputs/rr_h3_n2_decorated_comparison.json`. 새 completion search 없음.

## 7. 세 state의 decorated preparation history

`ell=4` abandonment root에서 preparation length **3**인 세 state:

| state | kind signature | completer index | completer kind | completer is R1 | fresh | O |
|---|---|---:|---|:---:|---:|---:|
| `5d3f8cb9fdd4` | `[R, Z2, Z2] → R2` | 3 | Z2 | False | 0 | 2 |
| `6f1ed828b231` | `[Z2, R, Z2] → R2` | 3 | Z2 | False | 0 | 2 |
| `fe82b0cdb512` | `[Z2, Z2, R] → R2` | 3 | R | **True** | 0 | 2 |

## 정상형 — 하나의 parameterized family

> **H3 normal form (root-local exhaustive, depth≤8에서 정확히 3개)**:
> `ell=4` abandonment 직후, 준비 구간은 **정확히 3개의 macro-edge**로
> 이루어지며 그중 **정확히 하나가 R(=R1)**, 나머지 둘은 **Z2**(새
> orbit을 열지 않는 zero-charge 조인트)다. R1의 위치
> \(i\in\{1,2,3\}\)가 이 family의 **유일한 매개변수**이고, 세 state는
> \(i=1,2,3\)에 정확히 대응한다.

즉 H3는 "같은 symbolic event word의 phase/orbit 변형"이 아니라
**같은 multiset `{R, Z2, Z2}`의 세 가지 배치**다 — §7이 물은
"세 state가 같은 symbolic word의 변형인가"에 대한 정확한 답이다.

## 공유 불변량 (세 state 전부)

- `fresh_orbit_openings = 0` — **Z3를 한 번도 쓰지 않는다**, `O=2` 고정
- `hub_completer_macro_index = 3` = **준비 구간의 마지막 edge**
  (**이 문서는 ell=4 전용이므로 유효**; ell=0에서는 거짓이다 —
  `RR_PREPARATION_PARITY_THEOREM.md` §2 Lemma P1)
- `r1_r2_macro_distance = 1` — R2는 hub 완성 **직후** edge에서 발동
- completer 착지점 = `(orbit 1, phase 4)`, R2 source = `(1,4)`,
  R2 target = `(0,2)`, Φ=0

## 메커니즘 — orbit-1 phase walking

R1이 orbit 1을 (마지막이 아닌) 어떤 phase에서 target하고, 이어지는
Z2들이 orbit 1의 남은 phase를 걸어 hex0의 phase 4(위치 5)에 도달해
hub를 닫는다. \(i=3\)일 때만 R1 자신이 phase 4에 직접 착지해
completer가 된다(`hub_completer_is_r1 = True`).

**따라서 "completer가 R1인가"는 별도의 구조가 아니라 매개변수
\(i\)의 함수**다: \(i=3 \iff\) completer는 R1.

**증명 등급**: root-local exhaustive (depth ceiling 8까지 frontier
자연소진, preparation length 3인 state는 정확히 3개이며 위 배치가
전부).
