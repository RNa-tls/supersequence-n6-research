# Preparation grammar (라운드 21)

산출: `src/analyze_rr_preparation_grammar.py` -> `outputs/rr_preparation_words.json`,
`outputs/rr_grammar_parse_results.json`(depth-9 검증 실행, 별도 경로).
completion search 없음.

## 2. Symbolic alphabet

literal orbit id 대신 \(O_*\)(= abandonment 직후 hub의 nearest
residual orbit, `HEX0POS[ell+1]`)에 상대적으로 정의한다.

| symbol | 정의 | ΔO | Δfresh | Δ\(\Phi\)cost | hub residual |
|---|---|---:|---:|---:|---|
| `Rh` | target orbit이 \(O_*\)인 R 사건 | 0 | 0 | 0 (ell=5) | 불변 |
| `Rx` | 다른 orbit을 target하는 R | 0 | 0 | 0 | 불변 |
| `F` | fresh Z3 orbit opening | +1 | +1 | 0 | 불변 |
| `E` | 기존 orbit zero-charge 전이(source가 hub 밖) | 0 | 0 | 0 | 불변 |
| `Xh` | source가 hub 내부인 zero-charge 전이(hub exit) | 0 | 0 | **1+ℓ** | — |
| `C` | hub completer | 0/+0 | 0 | 0 | **닫음** |

(관측된 모든 준비 edge는 `ell=5`라 \(\Phi\) 기여가 0이고, 유일한
예외가 `Xh`와 abandonment다 — `RR_PREPARATION_PARITY_THEOREM.md` §2 P2.)

## 9. 문법

\[
\mathcal G_\ell \;=\; A_\ell \;\cdot\; P \;\cdot\; C \;\cdot\; T_\ell \;\cdot\; R_2
\]

- \(T_4=\varepsilon\), \(T_{\ell\ne4}=\texttt{Xh}\) (**손증명**, P1)
- \(P\): `before_C` 단어, 알파벳 \(\{E,F,Rh\}\), **짝수 길이**(관측)

관측된 \(P\) 집합:

| \|P\| | ell=4 | ell=0 |
|---:|---|---|
| 2 | `EE`, `RhE`, `ERh` | `EE` |
| 4 | `FEFE`, `FFEF` | `FEFE`, `FFEF` |
| 6 | `EEFEEE`, `FFFEFF`, `FEEERhE`, `EFEEERh` | `EEFEEE`, `FFFEFF` |

## 핵심 관계 — 예측하고 검증한 결과

세 길이 전부에서:

\[
P_{\ell=0} \;=\; \{\,w\in P_{\ell=4} \;:\; w \text{ 안에 } Rh \text{ 없음}\,\}
\]

**이것은 사후 관찰이 아니라 예측 후 검증이다.** \|P\|=2,4에서 이
관계를 발견한 뒤, ell=4의 \|P\|=6 집합에서 `Rh`가 없는 두 단어
(`EEFEEE`, `FFFEFF`)가 ell=0의 depth-9에서 나타나야 한다고
예측했고, §19가 허용하는 문법 검증용 depth-9 실행(root-local,
frontier 자연소진, 출력 경로 분리)에서 **정확히 그 두 개만**
나타났다.

### 왜 ell=0에는 `Rh`가 없는가 (구조적 이유)

ell=0에서는 **completer가 항상 R1 자신**이다(5/5). chaining이
성립하려면 R1이 \(O_*\)를 target해야 하는데, ell=0에서 \(O_*\)에
착지하는 것은 곧 hub를 닫는 것이므로 R1 = C가 된다. 따라서 C보다
앞선 `Rh`가 존재할 여지가 없다.

ell=4에서는 \(O_*=1\)이 hub 위치 5이고, R1이 orbit 1을 **다른
phase**에서 먼저 target한 뒤(=`Rh`) zero-charge가 phase 4까지 걸어가
C가 될 수 있다 — 그래서 `Rh`를 포함한 \(P\)가 존재한다.

## 상태 판정

| 항목 | 판정 |
|---|---|
| \(T_\ell\) 규칙 | **손증명** |
| \(P_{\ell=0}=Rh\text{-free}(P_{\ell=4})\) | **root-local exhaustive + 예측 검증 성공**(\|P\|≤6) |
| \(P\)가 짝수 길이 | root-local exhaustive, **손증명 미완료** |
| \(P\) 집합의 생성 규칙 | **미완료** — 아래 |

## 생성 규칙을 찾지 못했다 (정직한 보고)

\(P\) 집합을 base + 삽입으로 생성하려 했으나 **실패했다**:

- `EE` → `FEFE`: `EE`에 어떤 연속 2-block을 삽입해도 `FEFE`가
  나오지 않는다(`FE`+`EE`=`FEEE`, `EE`+`FE`=`EEFE`, `E`+`FE`+`E`=`EFEE`).
- `FEFE` → `EEFEEE`: `FEFE`에서 2-block을 지워도 `EE`가 아니라
  `FE`/`EE`가 나오는데, 길이 4 집합에는 `EEFE`도 `FEEE`도 없다.

즉 **§7의 목표 정리("모든 non-minimal preparation history는
제거 가능한 2-edge block을 포함한다")는 symbolic 수준에서
반증된다** — 자세한 반례는 `RR_PREPARATION_INSERTION_BLOCKS.md`.

따라서 현재 문법은:

> **exact grammar가 아니라, 관측된 \(P\) 집합을 길이별로 나열한
> 유한 목록 + 손증명된 \(T_\ell\) 규칙의 결합**이다.
> 등급: **bounded observation**(\(P\) 부분) + **손증명**(\(T_\ell\) 부분).
> `\bigcup_i B_i(Q_1|Q_2)^*CR_2` 형태의 반복 문법은 **얻지 못했다.**

## 11. Completeness

자연소진한 범위(ell=4 depth≤8, ell=0 depth≤9) 안에서 **모든**
same-component history가 위 \(A_\ell P C T_\ell R_2\) 형태로 정확히
분해된다(14/14, parse 성공률 100%, 분해가 유일). 그러나 이는
**bounded coverage이지 전역 completeness가 아니다** — 더 깊은
depth에서 새로운 \(P\)가 계속 나타나고 있으므로(길이 2→4→6),
\(P\) 목록은 열려 있다.


## depth-9 검증 실행의 부가 결과

`outputs/rr_ell0_depth9_verification.log`(§19 조건 준수: root-local,
cap 없음, 출력 경로 분리, 기존 출력 덮어쓰기 없음):

- `ell=0` depth≤9: same-component **5개** — 기존 3개 + `EEFEEECXh`,
  `FFFEFFCXh`. **예측과 정확히 일치**(다른 것은 나오지 않았다).
- `EEFEEECXh`(=`4cb55a304905`)의 trailing edge가 **2개** — `ell=4`의
  `EEFEEEC`(=`cbfdf11e4a79`)와 동일. **분기를 넘어 symbolic word가
  trailing 개수를 결정**한다는 §16의 결과를 재확인.
- `ell=1`, `ell=2`도 depth≤9에서 same-component **0개** — ell∈{0,4}
  이분법이 depth 9까지 유지된다.

(`ell=3`, `ell=4`의 depth-9 구간은 시간 예산으로 중단했다 —
필요했던 `ell=0` 예측 검증은 완료된 뒤였다. **부분 실행임을
명시**하며, 중단된 구간에 대해서는 아무 주장도 하지 않는다.)
