# Long preparation normal form과 Target A 양립 구조 (라운드 28)

산출: `src/analyze_rr_long_normal_forms.py` ->
`outputs/rr_long_normal_form_classes.json`.

## 1. 분해 \(A_4\cdot U\cdot X_{\mathrm{long}}\cdot V\cdot C\cdot R_2\) (§6)

| # | \(\vert U\vert\) | \(X_{\mathrm{long}}\) | \(\vert V\vert\) | \(V\) 기호 | \(C\) | \(C\) 착지 | \(\vert T_\ell\vert\) | \(R_2\) |
|---:|---:|---|---:|---|---|---|---:|---|
| 0,1 | **0** | `FFEFEFR` (L=7) | **0** | — | `rot^5;w2:10` | **(1,4)** | 0 | `rot^0;w3:120` |
| 2,4 | **0** | `FFFFEFFR` (L=8) | **2** | `EE` | `rot^5;w2:10` | **(1,4)** | 0 | `rot^0;w3:120` |
| 3,5 | **0** | `FFFEFFFR` (L=8) | **2** | `EE` | `rot^5;w2:10` | **(1,4)** | 0 | `rot^0;w3:120` |

**세 가지 구조적 관찰**:

1. **\(U\)는 항상 비어 있다** — excursion이 abandonment port에서 **즉시**
   시작한다. 이는 corpus 구성상 필연이며(prefix가 곧 excursion),
   \(U\ne\emptyset\)인 변종은 이번 범위 밖이다. **scope 제한**으로 기록.
2. **\(V\)는 비어 있거나 `EE`뿐이다** — Class I은 excursion 직후 곧바로
   completer, Class II는 두 개의 E를 거친다.
3. **\(C\)와 \(R_2\)는 여섯 전부 동일**하다.

## 2. 왜 Target A가 살아남는가 (§7) — exact ledger

| # | \(O_*\) phase 사용 순서 | 사용 phase 수 | 마지막이 4인가 | chaining | \(\Phi\) |
|---:|---|---:|:---:|:---:|---:|
| 0,1 | \([0,3,4]\) | 3 | **예** | True | 0 |
| 2–5 | \([0,1,2,3,4]\) | **5 (전부)** | **예** | True | 0 |

> **관측된 메커니즘**: long excursion은 phase winding을 만들지만,
> **\(O_*\)의 phase 4를 마지막까지 남겨 둔다.** completer가 정확히
> \((1,4)\)에 착지해야 하는데, excursion의 return exponent가 무엇이든
> 그 다음 E 걸음이 \(+1\)로 phase 4에 도달하도록 복귀 phase가 맞춰진다.
>
> Class II는 \(O_*\)의 **다섯 phase를 전부** 소비하면서도 순서가
> \(0\to1\to2\to3\to4\)로 정렬되어 phase 4가 마지막이 된다.

**이것은 손증명이 아니다.** 여섯 witness에서 읽은 **exact replay**
관측이며, "long excursion은 terminal normal form에 필요한 phase와
ancestry를 파괴하지 않는다"는 일반 명제는 **미완료**다. 반례를
배제하는 논증이 없다.

또한 \(r_1\) target orbit \(=1=\) \(r_2\) source orbit이 여섯 전부에서
유지되고, component root와 \(\Phi=0\)도 전부 동일하다.

## 3. same-component ⟹ chaining (§10) — 반증되지 않음

여섯 witness 전부 **chaining = True** (\(r_1\)tgt \(=1=\)\(r_2\)src).

> parity conjecture는 무너졌지만 **same-component ⟹ chaining은
> 이 여섯으로 반증되지 않는다.** 오히려 **새로운 확인 사례 6개**다 —
> 그것도 preparation 길이가 기존 최대(7)보다 긴 10까지 확장된 사례다.

따라서 chaining 손증명 시도에는 **이 family를 반드시 포함**해야 한다:
기존 사례는 전부 \(P_{\mathrm{core}}\le6\)였으므로, 길이에 의존하는
논증은 이제 이 6개로 반증될 위험이 있다.

**등급**: **exact replay** (6/6 확인). chaining 일반 정리는 여전히
**미완료**.

## 4. Terminal normal form의 범위 (§11)

> **후보 명제**: \(\ell=4\) same-component Target A boundary는
> **preparation history와 무관하게** 동일한 terminal normal form을
> 갖는다.

이번 범위에서 확인된 좌표:

| 좌표 | 값 | 확인 범위 |
|---|---|---|
| \(O_* = \) orbit 1 | 예 | 6/6 |
| completer 착지 \((1,4)\) = hex0 위치 5 | 예 | 6/6 |
| 마지막 edge `rot^0;w3:120` (즉시 \(R_2\)) | 예 | 6/6 |
| chaining | 예 | 6/6 |
| \(\Phi=0\) | 예 | 6/6 |
| tail 길이 0 | 예 | 6/6 |

**증거 등급 분리**:

- 역사적 9개(\(P_{\mathrm{core}}\le6\)): **root-local exhaustive**
- 새 6개(\(P_{\mathrm{core}}=7,10\)): **witness exact**
- **합쳐서 15개 사례, preparation 길이 2~10 전 범위에서 예외 0**
- **손증명 후보로는 승격 가능하나 아직 손증명이 아니다** — 임의
  preparation history에 대한 논증이 없고, 특히 \(\ell=0\) 분기는
  이 corpus에 포함되지 않았다.

이 명제는 **이번 라운드에서 가장 강해진 살아남은 관측**이다.

## 5. 22개 INCOMPLETE 분류 (§12) — 기존 로그만 사용

| 항목 | 값 |
|---|---|
| 개수 | 22 |
| root \(\ell\)별 | \(\ell=0\): 6, \(\ell=1\): 6, \(\ell=2\): 6, \(\ell=3\): 4 |
| symbolic word별 | `FFEFEFR`: 8, `FFFFEFFR`: 7, `FFFEFFFR`: 7 |
| FOUND와 동일 symbolic class | **22/22 전부 그렇다** |
| 도달한 \(R_2\) 경계 수 | 7,662 ~ 7,825 |
| frontier 소진 | **0건** — 전부 node cap 8,000에서 잘림 |

> **22개는 FOUND 6개와 symbolic excursion class가 동일하고, 오직
> abandonment \(\ell\)만 다르다.** FOUND는 전부 \(\ell=4\)이고
> INCOMPLETE는 전부 \(\ell\in\{0,1,2,3\}\)이다.

이는 기존 **\(\ell\) 이분법**(same-component는 \(\ell\in\{0,4\}\))과
일관되지만, **\(\ell\ne4\)가 불가능하다는 증거가 아니다**:

- 각 root가 7,000개 넘는 \(R_2\) 경계에 도달했으나 same-component가
  없었을 뿐이고,
- frontier는 **전혀 소진되지 않았다**.

**bounded incomplete**로 유지한다. 추가 탐색은 quotient 개선이나
새 안전 prune이 생길 때만 정당하다 — 현재 둘 다 없다.
