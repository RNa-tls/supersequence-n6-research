# Rh-free sublanguage 정리 (라운드 22)

산출: `src/verify_rr_rh_free_language.py` ->
`outputs/rr_rh_free_language_check.json`. completion search 없음.

## 9. 두 방향 분리

관측된 언어(자연소진 범위):

- \(\mathcal P_0=\{\texttt{EE},\ \texttt{FEFE},\ \texttt{FFEF},\ \texttt{EEFEEE},\ \texttt{FFFEFF}\}\)
  (마지막 둘은 라운드21의 depth-9 검증에서 확인)
- \(\mathcal P_4=\{\texttt{EE},\texttt{RhE},\texttt{ERh},\texttt{FEFE},\texttt{FFEF},
  \texttt{EEFEEE},\texttt{FFFEFF},\texttt{FEEERhE},\texttt{EFEEERh}\}\)
- \(\mathcal P_4\cap\{E,F\}^*=\{\texttt{EE},\texttt{FEFE},\texttt{FFEF},\texttt{EEFEEE},\texttt{FFFEFF}\}\)

| 포함 | 판정 |
|---|---|
| **Inclusion 1**: \(\mathcal P_0\subseteq\mathcal P_4\cap\{E,F\}^*\) | **성립** (5/5, 모든 관측 길이 2·4·6) |
| **Inclusion 2**: \(\mathcal P_4\cap\{E,F\}^*\subseteq\mathcal P_0\) | **성립**(관측 길이 전부) — 길이 6의 두 단어는 라운드21이 **예측 후 검증**했다 |

> **정리 (exact language identity, 길이 ≤6 범위)**:
> \(\mathcal P_0=\mathcal P_4\cap\{E,F\}^*\).
> 길이 8 이상은 검증하지 않았다 — **미완료**.

## 8. Rh가 ell=0에 없는 이유 — 네 후보 판정

`rh_reachable()`로 각 분기의 preparation prefix에서 `Rh` edge가
국소적으로 legal한지 직접 열거했다.

| 후보 | 판정 | 근거 |
|---|---|---|
| **R1** ancestry를 너무 일찍 소진 | **미완료** | 직접 검사하지 않음 |
| **R2** ell=0에서 \(O_*\)-target R이 preparation에 들어갈 수 없다 | **반증됨** | ell=0에서 `Rh` edge가 국소적으로 legal한 사례가 실제로 존재한다(예: depth 1에 orbit 120 phase 3을 target하는 `w3:120`, hex 90) |
| **R3** `Rh`는 \(O_*=1\)과만 호환된다 | **반증됨** | 위와 동일 |
| **R4** 국소적으로는 legal하나 terminal normal form과 양립 불가 | **지지됨** | `Rh`가 ell=0에서 legal함에도 **어떤 same-component witness에도 나타나지 않는다** — 장애물은 국소 legality가 아니라 종결 구조에 있다 |

## R4의 구조적 이유 (손증명, terminal normal form 전제)

ell=0에서는 **completer가 반드시 R1 자신**이다. 이유: completer는
\(O_*\)에 착지하고(terminal normal form), chaining은 R1이 \(O_*\)를
target할 것을 요구한다. RR word에는 R이 정확히 2개뿐이고 두 번째는
\(R_2\)이므로, \(O_*\)를 target하는 R은 R1 하나뿐 — 따라서
completer = R1이고, **C보다 앞선 `Rh`는 존재할 수 없다.**

\(\ell=4\)에서는 \(O_*=1\)이 hub의 exit 위치(position 5)에 있어,
R1이 orbit 1을 **다른 phase**에서 먼저 target한 뒤 zero-charge가
phase 4까지 걸어가 completer가 될 수 있다 — 그래서 `Rh`를 포함한
\(P\)가 존재한다.

> **이것이 §9 Inclusion 1의 구조적 증명이다**(terminal normal form을
> 전제로 한 손증명). Inclusion 2(ell=4의 Rh-free 단어가 ell=0에서도
> 실현 가능)는 **관측으로만 확인**됐다 — transport map이 없으므로
> 일반 증명은 **미완료**(`RR_BRANCH_TRANSPORT_MAP.md`).

**성공 기준 3 평가: 부분 달성** — Inclusion 1은 손증명, Inclusion 2는
exact language identity(관측 범위), 전체 일반 증명은 미완료.
