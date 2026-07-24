# orbit 1 / orbit 120의 정확한 의미와 two-bit causal theorem

산출: `src/verify_a2_history_statistic.py`,
`outputs/a2_two_orbit_truth_table.json` (기존 24-witness
`outputs/a2_rotation_candidate_tables.json` 재사용, 새 탐색 없음).

## 3. orbit 1 / orbit 120은 구조적으로 의미 있는가, 구현 인덱스일 뿐인가

`UNIQUE_WEIGHT2_MOVE_THEOREM.md`가 증명한 공식
`target(ell) = compose(p_0, g_ell)`, `g_ell = Σ^ℓ * action`을 그대로
계산하면(코드 열거가 아니라 이 공식 자체를 평가), 모든 24개 RA2
witness가 공유하는 `p_0 = IDENTITY`에서:

```
g_ell의 E-orbit id, ell=0..5:  [120, 33, 9, 3, 1, 0]
```

이는 매 witness의 raw candidate table에서 관측된 순서와 정확히
일치한다 — **"orbit 1"과 "orbit 120"이라는 이름은 구현 인덱스가
맞지만, 그 인덱스가 지시하는 대상은 임의가 아니라 이 고정 수열의
ell=4, ell=0 위치라는 특정 구조적 역할이다.**

### orbit 120 (ell=0 후보)

`E_REPS[120] = (1,2,3,4,5,0)`. 코드에서 직접 확인: 이 값은
**`SIGMA` 그 자체**다. 즉 **"orbit 120"은 다름 아닌 회전
생성자 `Σ`의 canonical E-orbit 표현** — `ell=0`에서
`g_0 = Σ^0 * action = action`이 되어야 하는데, 그 결과 값이 우연히도
`Σ`의 대표원과 일치하는 것이 아니라, `action`의 정의(`tail_action(2,(1,0))`)
자체가 이 위치에서 `Σ`의 canonical rep와 같은 E-orbit에 속한다는
사실을 반영한다. 이 orbit이 건드리는 hexagon 5개: `(0,33,64,90,96)`
(port 5개, `ports_of_e_orbit`/`kset_of_e_orbit` 직접 계산).

**불변 이름**: `weight-2 후보 orbit (ell=0)`, 또는 "unique-weight2-action의
own E-orbit."

### orbit 1 (ell=4 후보)

`E_REPS[1] = (0,1,2,3,5,4)`. 이 값은 `g_4 = Σ^4 * action`의 canonical
표현 그 자체다(별도 구조적 지름길 없이, 6개 고정 원소 중 하나일
뿐 — `Σ`처럼 이미 이름 붙은 다른 생성자와 우연히 일치하지 않는다).
건드리는 hexagon 5개: `(1,72,12,2,0)` — **hexagon 0을 orbit 120과
공유**한다(두 orbit의 유일한 교집합점).

**불변 이름**: `weight-2 후보 orbit (ell=4)`, 또는 "R이 생성한 orbit과
공통 hexagon 0을 공유하는 orbit."

### 결론

숫자 1과 120 자체에는 의미가 없다(단지 `E_REPS`를 정렬해 만든
사전순 인덱스). 하지만 그것들이 **어느 것인지**는 의미가 있다 —
"6개 고정 후보 orbit 수열의 ell=0 자리(= action 자신의 orbit)"와
"ell=4 자리"라는 순수 group-이론적 위치다. 아래 정리들은 이 두
좌표 불변적 이름(`ell=0 후보 orbit`, `ell=4 후보 orbit`)만 사용한다.

## 4. Two-bit causal theorem

정의(좌표 불변): `b_{ell=4} := existing(ell=4 후보 orbit)`,
`b_{ell=0} := existing(ell=0 후보 orbit)` — 각각 A2 이전
fresh-landing 지점에서 평가.

24개 RA2 witness 전수(재탐색 없이 기존 corpus 재대조) 분류:

| `(b_{ell=4}, b_{ell=0})` | 관측 개수 | legal ell(들) | 그룹 |
|---|---|---|---|
| `(True, False)` | 4/24 | `{4}` (유일) | **U4 전체, 정확히 일치** |
| `(False, True)` | 1/24 | `{0}` (유일) | **outlier, 정확히 일치** |
| `(False, False)` | 10/24 | 대부분 `{1}`, 예외 1개 `{3}` (`d92abc8c8e61`) | C20 대부분 |
| `(None, False)`\* | 9/24 | 전부 `{1}` | C20 나머지 |
| `(True, True)` | **0/24 (미관측)** | — | — |

\* `None`은 "existing"보다 강한 세 번째 상태 — `ell=4` 후보의
**target 자체가 이미 visited** — 이는 `existing` 여부와 무관하게
predicate에서 즉시 `A2Legal(·,4)=False`를 강제하는 별도 차단
조건이다(라운드 9의 `H_A2` 정의가 `visited`와 `existing`을 별도
비트로 둔 이유가 바로 이것).

### 정리 (손증명, 24/24 corpus 전수 재대조 — "제한 실험/유한 완전
검증", 코퍼스 안에서는 예외 없음)

> **`(b_{ell=4}=True, b_{ell=0}=False)` ⟺ 유일 legal ell이
> 존재하며 그 값은 4다 — 이 코퍼스에서 정확히 U4의 4개 상태와
> 일치(4/4, 역방향도 4/4)한다.**
>
> **`(b_{ell=4}=False, b_{ell=0}=True)` ⟺ 유일 legal ell이
> 존재하며 그 값은 0이다 — 이 코퍼스에서 정확히 outlier
> 1개와 일치(1/1, 역방향도 1/1)한다.**

이 두 방향 함의 모두 **완전한 24-state corpus 위에서는 예외 없이
성립**하지만(따라서 이 코퍼스에 대해서는 "유한 완전 검증"), **일반
정리로 승격하려면**:
1. `(True, True)` 조합이 관측되지 않아 그 경우의 legal ell을 예측할
   수 없다 — **미완료**.
2. `(False, False)`(및 `None,False`) 조합에서 legal ell이 항상
   유일하게 결정되지 않는다(`{1}`이 압도적이지만 `d92abc8c8e61`은
   `{3}`) — 즉 이 두 비트만으로는 **충분하지 않다**, 나머지
   4개 후보(ell=1,2,3,5)의 existing/visited 상태가 추가로 필요하다.

### "U4의 ell=4 forcing은 정확히 특정 two-bit pattern과 동치이다" 평가

**이 코퍼스 내에서는 참(24/24 완전 검증)**: `ell=4`가 강제되는 것은
정확히 `(b_{ell=4}=True, b_{ell=0}=False)`인 4개 상태뿐이고, 다른
20개 상태는 전부 이 패턴이 아니다. 그러나 이것이 **일반 정리**(모든
가능한 exact state에 대해)인지, 아니면 이 24-witness corpus라는
특정 표본의 우연인지는 `(True,True)` 미관측 때문에 확정할 수
없다 — **"corpus exact observation"으로 표시, "일반 정리"로
과장하지 않는다.**

## 성공 기준 (3) 평가

**부분 달성**: `(b_{ell=4},b_{ell=0})=(T,F) ⟺ 유일 legal ell=4`
방향은 24/24 완전 재대조로 확인됐고, U4를 정확히 재현한다. 그러나
이 두 비트가 legal ell을 **일반적으로** 결정한다는 주장은
`(False,False)` 그룹 내 비유일성과 `(True,True)` 미관측 때문에
성립하지 않는다 — "두 orbit의 occupancy pattern이 U4의 경우를
정확히 특징짓는다"는 좁은 형태로만 손증명됐다.
