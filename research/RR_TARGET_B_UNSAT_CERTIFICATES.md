# UNSAT certificate — 이번 라운드는 **하나도 발급하지 않는다** (라운드 33 §15–16)

산출: `src/verify_rr_target_b_unsat.py` ->
`outputs/rr_target_b_unsat_certificates.json`.

## 1. 결론부터

| 항목 | 값 |
|---|---:|
| 발급된 UNSAT certificate | **0** |
| `EXHAUSTED_INFEASIBLE`로 판정된 층 | **0** |
| 감사한 층 상태 | 7 |
| 규율 위반 | **0** |

어떤 층도 소진되지 않았으므로 **불가능성 증명을 주장하지 않는다.**
truncated search를 infeasible로 보고하는 것이 바로 이 감사가 잡아내려는
오류다.

## 2. 독립 검증 1 — phase-walk initial capacity refinement

`verify_rr_target_b_unsat.py`는 solver를 전혀 참조하지 않고 상태에서
직접 initial capacity를 재계산한다.

| \(\ell\) | \(P_{\mathrm{core}}\) | port bound \(c_0\) | **실제 phase-walk capacity** | 최적 word | 새 bound | \(B{+}1\) | 모순 |
|---:|---:|---:|---:|---|---:|---:|:---:|
| 0 | 2 | 3 | **2** | `E` | 121 | 115 | 아니오 |
| **0** | **4** | 3 | **2** | `E` | **111** | 113 | **예** |
| 4 | 2 | 3 | **2** | `E` | 121 | 116 | 아니오 (×3) |
| **4** | **4** | 3 | **2** | `E` | **111** | 114 | **예** |
| 4 | 6 | 3 | **2** | `E` | 116 | 112 | 아니오 (×3) |

> **라운드32가 (B)와 (B+R)로 제거한 두 상태를, 완전히 다른 경로로
> 재확인한다.** 두 제거는 이제 **독립적인 두 증명**을 갖는다.
>
> 남은 7개에는 새 제거가 없다 — bound가 1 강해졌을 뿐이다.

## 3. 독립 검증 2 — 층 상태 감사

감사 규칙:

- `EXHAUSTED_INFEASIBLE`인데 `R1_truncated`가 참이면 **위반**
- `INCOMPLETE`인데 `first_failing_layer`가 `R1`이면 **위반**

**7개 전부 통과, 위반 0건.** R1 histogram은
`{FEASIBLE: 4, INCOMPLETE: 3}`이고 infeasible은 없다.

## 4. R3에 대한 명시적 자기 정정

초안에서는 `NO_HAMILTONIAN_ORDER`를 `first_failing_layer = "R3"`으로
기록했다. **그것은 틀렸다** — cover 하나가 순서를 갖지 않는다는 것은
R3 infeasible이 아니다. 같은 상태의 다른 cover가 순서를 가질 수 있다.

수정 후:

- 상태 이름을 `NO_ORDER_FOR_THIS_COVER`로 바꿨고,
- `first_failing_layer`를 **`None`** 으로 되돌렸고,
- "cover 전수 열거만이 이것을 R3 장애물로 만들 수 있고, 하지 않았다"를
  결과에 명시했다.

## 5. Certificate 형식 (§16) — 발급 조건

향후 UNSAT을 발급할 때 포함해야 할 것:

| 항목 | 상태 |
|---|---|
| required segment count | 기록됨 |
| available full blocks | 기록됨 |
| maximum chain length | 기록됨 (현재 1) |
| defect budget | 기록됨 |
| first unavoidable defect | **없음** (아무 층도 소진 안 됨) |
| graph hash | full-block graph SHA-256 기록됨 |
| exhaustion 증거 | **없음 — 그래서 발급하지 않는다** |

solver 라이브러리가 없으므로 DRAT/LRAT나 ILP infeasibility
certificate는 생성할 수 없다. 대신 **독립 verifier**를 작성했고
(이 스크립트) 그것이 위 두 검증을 수행한다.

**등급**: refinement **손증명**, 층 감사 **exact replay**,
UNSAT **미완료**(발급 없음).

## Round 39 correction

The phase-walk table is preserved as a historical calculation, but its
generic upper-bound interpretation is withdrawn. It is not used by the
corrected proof. The helper-free 18-boundary re-audit closes all states via
coarse/B+R bounds and exact macro DFS; see
`RR_TARGET_B_18_BOUNDARY_REAUDIT_CODEX.md`.
