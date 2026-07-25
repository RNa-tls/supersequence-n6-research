# Word-state multiplicity — 정확한 counting identity (라운드 19)

산출: `src/analyze_rr_word_state_multiplicity.py` ->
`outputs/rr_word_state_multiplicity.json`. 새 탐색 없음(역사적 9개
witness의 exact replay + 각 post-R2 상태에서의 macro-edge 전수 열거).

## 4. Counting identity

\[
\#\text{words}
=
\sum_{S\in\text{post-R2 states}}
\#\text{allowed trailing completions}(S)
\]

**"allowed trailing completion"의 엄밀한 정의**(이 정의에서만
항등식이 정확하다): post-R2 상태 `S`에서 나가는 macro-edge 중
자식이 `area_a_prune_reason`을 통과하고, **word를 역사적 코퍼스가
정한 길이(6 macro-edge)까지 정확히 채우는** 것. "임의 길이의 legal
continuation"으로 읽으면 집합이 더 커져 항등식은 깨진다 — 이
구분이 라운드18 계수 단위 정정의 실질적 내용 전부다.

**실측 (exact counting identity)**:

```
9 = 3 + 3 + 3
```

| post-R2 state | 역사적 word 수 | legal trailing edge 수 | 사용된 edge == 가용 edge |
|---|---:|---:|:---:|
| `fe82b0cdb512` | 3 | 3 | **True** |
| `6f1ed828b231` | 3 | 3 | **True** |
| `5d3f8cb9fdd4` | 3 | 3 | **True** |

**모든 가용 trailing edge가 실제 역사적 word로 실현된다**(누락된
조합 없음) — 이것이 항등식이 "≤"가 아니라 "="인 이유다.

## 왜 정확히 3개인가 — 완전한 구조적 설명

세 상태 모두에서 legal trailing edge는 **동일한 3개**다:

| edge | kind | 착지 |
|---|---|---|
| `rot^5;w2:10` | Z2 | hex4, orbit0 phase3 |
| `rot^5;w3:201` | Z3 | hex10, orbit11 phase4 |
| `rot^5;w3:210` | Z3 | hex7, orbit6 phase4 |

그리고 세 상태 모두에서 **pruned edge가 19개, 사유는 전부
`F_exceeded`**이며, **빠진 조인트는 항상 `w3:120`**이다.
**[라운드21-22 정정] 그 19개는 `ell<5` edge들이고, `w3:120`이 빠지는
이유는 `F_exceeded`가 아니라 방문 충돌이다** — 아래 정정 절 참고.

**설명(손증명 수준의 구조적 논증)**:

1. R2 시점에 `F=1`이 이미 소진되어 있다(abandonment는 word당 1회,
   idx 0에서 이미 발생).
2. 따라서 이후 어떤 조인트도 abandonment일 수 없다 —
   abandonment이면 `state.F`가 2가 되어 `area_a_prune_reason`이
   `F_exceeded`로 즉시 제거한다.
3. `ell<5`인 macro-edge는 현재 hex를 다 훑지 않고 떠나므로 전부
   abandonment가 되어 제거된다 ⟹ **`ell=5`만 살아남는다.**
4. `ell=5`에서 이 모델의 조인트는 정확히 4개뿐이다
   (`UNIQUE_WEIGHT2_MOVE_THEOREM.md`: weight-2는 `w2:10` 하나,
   weight-3은 `w3:120/201/210` 셋).
5. 그 4개 중 `w3:120`은 이 상태들에서 **여전히 abandonment**여서
   `F_exceeded`로 제거된다.
6. 남는 것이 정확히 **3개**다.

즉 3이라는 숫자는 우연이 아니라 **"F 소진 후에는 ell=5만 legal" ×
"조인트는 4개뿐" − "그중 1개는 여전히 abandoning"**의 결과다.

## N2에도 같은 multiplicity가 있는가

**있다(단, 라운드20 정정: "항상 정확히 3개"는 반증됨 — 아래
참고).** `outputs/rr_l5_state_ledger.json`의 L5 ledger에서 다섯
상태 전부 `legal_trailing_edge_count = 3`이다 — H3의 3개뿐 아니라
N2의 2개도 정확히 3개의 trailing edge를 갖는다. 위 1-6단계 논증이
`F=1` 소진 이후의 임의의 post-R2 상태에 대해 동일하게 적용되므로
이는 예상되는 결과다.

**다만 주의**: N2의 word는 총 7 macro-edge이므로, N2에 대해
"3개의 trailing completion"을 곱해 word 수를 세는 것은
**역사적 코퍼스(depth≤6)와 다른 word 길이 집합**을 세는 것이다.
따라서 `9 = 3+3+3` 항등식은 **역사적 ell=4 same-component 집합에
한정된 정확한 항등식**이며, N2까지 포함해 확장하려면 word 길이
scope를 함께 바꿔 명시해야 한다.

## 일반 공식의 지위

위 항등식은 **정의상 자명한 분해**(각 word는 정확히 하나의 post-R2
상태를 지나고, 그 이후 부분이 trailing completion이다)이며,
비자명한 내용은 **각 상태의 trailing completion 수가 실제로
얼마인가**이다. 이번 라운드는 그 수가 `F` 소진 구조로부터 3으로
결정됨을 보였다.

**증명 등급**:
- 항등식 `9 = 3+3+3`: **exact counting identity**(9개 witness exact
  replay + 3개 상태에서 macro-edge 전수 열거).
- "왜 3인가"의 1-6단계: **손증명**(F 예산과 조인트 유일성만 사용,
  코퍼스 무관).
- "N2도 3개": **root-local exhaustive**.


## 라운드20 정정 — "항상 정확히 3개"는 반증됨

depth ceiling 8까지 확장하면 `ell=4` same-component state가 9개가
되는데, 그중 `cbfdf11e4a79`는 trailing edge가 **2개**뿐이다
(`rot^5;w3:210`이 추가로 사라진다). 원인은 `F_exceeded`가 아니라
**방문 충돌(visited collision)** — 준비 구간이 길어져 더 많은
permutation이 이미 방문된 결과다.

**정정된 명제**: 위 1-6단계 논증은 **상한(최대 3개)의 손증명**으로는
그대로 유효하지만, "정확히 3개"는 **반증됨**(exact counterexample:
`cbfdf11e4a79`). `RR_TERMINAL_NORMAL_FORM_THEOREM.md` §10 참고.


## 라운드21 추가 정정 — `w3:120` 제거 사유는 F_exceeded가 아니다

위 5단계는 "`w3:120`은 이 상태들에서 여전히 abandonment여서
`F_exceeded`로 제거된다"고 했다. 라운드21이 모든 후보 조인트를 직접
검사한 결과 **terminal 상태에서 `ell=5`인 RR 조인트 중 `F_exceeded`로
제거되는 것은 하나도 없다**(14/14). `w3:120`이 빠지는 진짜 이유는
**target permutation이 이미 방문됨(literal collision)** 이다.

따라서 손증명 가능한 상한은 **3이 아니라 4**(= 조인트 개수)이고,
"≤3"은 `w3:120` 충돌에 의존하는 관측이다.
`RR_TRAILING_EDGE_PREDICATE.md` 참고.
