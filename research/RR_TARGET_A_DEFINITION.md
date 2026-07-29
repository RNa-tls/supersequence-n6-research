# Target A / B / C 정의 고정 (라운드 27)

과제 §3의 지시대로 "완성"을 모호하게 쓰지 않는다. 이 문서가 이번
라운드에서 사용하는 유일한 정의다.

## 1. 용어 충돌 해소 — 두 개의 "F" (과제 §8)

이 프로젝트에는 **F가 두 개** 있고, 섞으면 모든 budget 논증이 조용히
망가진다.

| 이름 | 정의 | 예산 |
|---|---|---|
| **\(F_{\text{def}}\)** | `ExactState.F` — **defect/abandonment 카운터** | `TARGET_F = 1` |
| **\(F_{\text{sym}}\)** | fresh-orbit-opening **이벤트 기호** (Z3 조인트, `tr.new_orbit is True`) | `TARGET_F`와 무관. `O <= TARGET_O = 25`를 통해서만 제한 |

> **라운드26의 "#F=4"는 \(F_{\text{sym}}=4\)이며 \(F_{\text{def}}\le1\)의
> 위반이 아니다.** 두 값은 서로 다른 양이다.

corpus의 모든 필드는 `f_def_*` / `f_sym_*`로 이름이 갈려 있어 실수로
비교할 수 없다. **검증**: 186개 prefix 전부 \(F_{\text{def}}=1\)
(`by_f_def = {1: 186}`) — abandonment 예산은 온전하다. **exact replay**.

## 2. Target A — 이번 라운드의 판정 대상

> **Target A**: 다음을 모두 만족하는 macro-edge에 도달하는 것.
>
> 1. 그 조인트가 word의 **두 번째 R 사건**이다 (= \(R_2\)),
> 2. 자식 상태가 \(F_{\text{def}}=1\) **그리고** \(H=0\),
> 3. \(R_2\)의 **source orbit**과 **target orbit**이
>    `orbit_masks`로 구성한 orbit/hexagon 접합 forest에서
>    **같은 component**에 속한다.

이는 `src/analyze_rr_ell0_family.py`가 same-component \(R_2\) 경계를
수집할 때 쓰는 **바로 그 술어**이며, 새로 만든 정의가 아니다.
chaining(\(R_1\) target orbit \(=R_2\) source orbit) 여부는 **별도로
기록**하되 Target A의 조건에 넣지 않는다.

## 3. Target B / C — 이번 라운드 범위 밖

| | 내용 | 이번 라운드 |
|---|---|---|
| **Target B** | 그 \(R_2\) 경계 이후의 admissible terminal continuation | **시도하지 않음** |
| **Target C** | 전체 NR6 completion | **시도하지 않음** |

B와 C에 대해서는 **어떤 주장도 하지 않는다**. Target A 성공이
곧 RR witness의 존재를 뜻하지 않으며, 그 구분을 흐리지 않는다.

## 4. 왜 Target A가 parity 질문에 충분한가

라운드26이 남긴 열린 질문은

> \(L\ge7\)인 홀수 지수 \(O_*\) excursion을 포함한 prefix가
> **완성된 same-component RR word** 안에 나타나는가?

이다. \(O_*\)-phase walk와 zero-charge parity는 **\(R_2\) 경계에서
계산**된다(라운드18~25의 계수 단위 표준). 따라서 Target A 도달
여부가 곧 그 질문의 답이며, Target B/C는 필요하지 않다.

## 5. 탐색 범위 제한 — 전역 RR search가 아닌 이유

corpus의 살아남은 prefix는 **전부 \(R\) 사건을 정확히 1개** 갖는다.
따라서 확장 중 **다음에 나타나는 R이 곧 \(R_2\)**이다. 탐색은
zero-charge edge(E, F)만 확장하고 모든 R edge를 \(R_2\) 후보로
평가한 뒤 **그 너머로는 확장하지 않는다**. 이 때문에 frontier가
일반 RR 탐색과 달리 유한하게 소진될 수 있다 — 전역 탐색을 다시
시작하는 것이 아니라 **28개 root의 targeted 분석**이다.

**등급**: 정의 고정은 **손증명**(기존 술어 재사용),
\(F_{\text{def}}=1\) 확인은 **exact replay**.
