# ell=0 family 성장과 decorated preparation automaton (라운드 20)

산출: `src/analyze_rr_ell0_family.py` -> `outputs/rr_ell0_depth7_families.json`.
새 completion search 없음(root-local, frontier 자연소진).

## 13. 세 state의 exact ledger

`ell=0` abandonment root, depth ceiling 7(frontier 자연소진, 12,957
노드 확장):

| state | prep 길이 | kind signature | fresh | Φ | completer | R1_t | R2 |
|---|---:|---|---:|---:|---|---:|---|
| `33d70b4249b7` | 4 | `[Z2,Z2,R,Z2] → R2` | 0 | 0 | (120, phase 0), R1 자신 | 120 | (120,4)→(0,3) |
| `4355122f1ad2` | 6 | `[Z3,Z2,Z3,Z2,R,Z2] → R2` | 2 | 0 | (120, phase 0), R1 자신 | 120 | (120,4)→(0,3) |
| `eb4da81d5a4a` | 6 | `[Z3,Z3,Z2,Z3,R,Z2] → R2` | 3 | 0 | (120, phase 0), R1 자신 | 120 | (120,4)→(0,3) |

**세 state가 공유하는 것(예외 없음)**: `R1_target = 120`,
completer = **R1 자신**이 `(120, phase 0)`에 착지,
R2 source `(120, phase 4)`, R2 target `(0, 3)`, Φ=0,
`r1_r2_macro_distance = 2`, trailing edge 3개, chaining=True.

**다른 것**: 준비 길이(4 vs 6), Z3 개수(0 vs 2 vs 3), 배치.

## 판정 — 네 후보 중 어느 것인가

| 후보 | 판정 |
|---|---|
| 하나의 base family에 preparation block 삽입 | **가장 잘 맞는다.** terminal 부분(마지막 2 edge: R1-as-completer → Z2 → R2)이 셋 다 완전히 동일하고, 앞부분만 4 edge에서 6 edge로 늘어난다. |
| 세 개의 독립 family | **아니다.** terminal signature가 완전히 일치한다. |
| phase-equivalent variants | **아니다.** phase가 아니라 준비 길이와 Z3 개수가 다르다. |
| depth 증가마다 계속 새 family 생성 가능 | **배제하지 못했다** — 아래 §14 참고. |

**그러나 "삽입되는 블록"이 유일한 형태는 아니다**: 두 6-길이 state의
Z3 위치·개수가 `{1,3}`/2개와 `{1,2,4}`/3개로 다르므로,
"정확히 정해진 하나의 블록"이 아니라 **여러 가지 준비 확장이 같은
terminal에 도달**한다. 따라서 정확한 서술은:

> **하나의 공통 terminal normal form + 길이·조성이 다양한 준비
> 확장.** 단일 매개변수 family로 정식화하지는 못했다 — **미완료.**

## ell=0과 ell=4의 평행성

두 분기는 **구조적으로 같은 모양**이다:

| | `ell=0` | `ell=4` |
|---|---|---|
| \(O_*\) | 120 (= 위치 1) | 1 (= 위치 5) |
| 관측된 준비 길이 | 4, 6 (짝수) | 3, 5, 7 (홀수) |
| boundary depth parity | **홀수**(5,7) | **짝수**(4,6,8) |
| completer → R2 거리 | 2 | 1 |
| terminal 공유 | ✔ | ✔ |

**두 분기 모두 "하나의 terminal normal form + 임의로 길어지는 준비
구간"** 구조를 보인다.

## 14. Decorated preparation automaton

`ell=0` 준비 구간을 추상 상태

\[
(\text{hub residual mask},\ \text{R1 target ancestry},\ \text{phase saturation},\ \text{fresh orbit count},\ \text{R2 readiness})
\]

로 축약하면, 관측된 세 history는 다음 전이만 사용한다:

- `fresh Z3 opening` — `fresh orbit count`를 +1, hub residual mask
  불변
- `existing-orbit revisit (Z2)` — orbit 120의 phase saturation 진행
- `hub completion (R1)` — hub residual mask를 닫고 R1 target
  ancestry를 확정
- `Z2` — R2 readiness 확보(phase 0 → phase 4 이동)
- `R2` — 종료

### 유한성 판정 — **미완료(무한 가능성 배제 못 함)**

관측 범위(depth ≤ 7)에서는 준비 길이가 4와 6뿐이지만:

1. `fresh orbit count`는 자연수이고 관측값이 0, 2, 3으로 이미
   다양하다 — 상한을 시사하는 구조가 없다.
2. `ell=4` 분기에서는 depth 8로 올리자 준비 길이 7짜리가 **4개
   새로 나타났다**(`RR_TERMINAL_NORMAL_FORM_THEOREM.md` §12), 그중
   하나는 Z3를 5개 쓴다.
3. 따라서 **`ell=0`도 depth 8+ 에서 준비 길이 8짜리가 나타날 것으로
   예상되나 확인하지 않았다.**

> **결론: automaton이 유한한지, 아니면 임의의 preparation insertion
> 으로 무한히 성장 가능한지 판정하지 못했다 — 미완료.**
> 다만 `ell=4`에서 depth를 올릴 때마다 새 family가 나타난 사실은
> **무한 성장 쪽을 시사하는 증거**이며, "유한하다"고 주장할 근거는
> 전혀 없다.

**등급**: root-local exhaustive(depth ceiling 7, frontier 자연소진)
+ 유한성 판정은 **미완료**.
