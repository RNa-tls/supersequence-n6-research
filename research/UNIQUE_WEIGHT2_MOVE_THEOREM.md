# 유일한 weight-2 move — 손증명

산출: `src/analyze_unique_weight2_move.py`(코드 재확인, 새 탐색 없음).

## 결론 먼저

> **정리**: `tail_permutations(2)`는 정확히 원소 1개, `(1,0)`(즉
> 앞의 두 자리를 뒤집는 전치)만을 가진다. 따라서 이 모델 전체에서
> weight-2 move는 정확히 하나(`w2:10`, action=`(2,3,4,5,1,0)`)뿐이다.
> 이는 구현의 우연이 아니라 "indecomposable permutation"의 정의로부터
> **일반적으로**(n=6에 국한되지 않고 w=2인 모든 경우에) 성립하는
> 조합론적 필연이다.

## 1. 증명

`is_indecomposable(pi)`(코드 정의, `superperm_port_lift.py:116`)의
정의: 길이 `w`인 순열 `pi`가 **decomposable**하다는 것은, 어떤
`1<=t<=w-1`에 대해 `{pi(0),...,pi(t-1)} = {0,...,t-1}`인
proper prefix가 존재한다는 뜻이다. `indecomposable`은 그 부정이다.

**w=2일 때**: 검사할 `t`는 `range(1,2)={1}` 하나뿐이다. 조건은
`{pi(0)} = {0}`, 즉 **`pi(0)=0`**. `{0,1}`의 순열은 정확히 2개:
`(0,1)`(항등, `pi(0)=0`이므로 **decomposable**)과 `(1,0)`(`pi(0)=1≠0`이므로
**indecomposable**). 검사할 `t`가 하나뿐이므로 이걸로 전부다.

\[
|\text{tail\_permutations}(2)| = 2! - |\{pi : pi(0)=0\}| = 2 - 1 = 1.
\]

**이는 n=6이라는 이 프로젝트의 특정 값에 의존하지 않는다** — `w=2`인
한 이 논증은 항상 정확히 1개를 남긴다(어떤 `N`(전체 길이)에서도
동일). `w=1`도 같은 이유로 항상 1개다(검사할 `t`가
`range(1,1)=∅`이라 공진리적으로 유일한 `pi=(0,)`가 통과).
`w>=3`부터는 검사할 `t`가 2개 이상이 되어 여러 개의 indecomposable
순열이 남는다(예: `w=3`이면 `3!-(2+2-1)=3`개 — 이 프로젝트
전반에서 관측된 "weight-3 move는 항상 여러 개(보통 3개 안팎)"라는
사실과 정확히 일치).

## Source endpoint에서 candidate target 공식

`tail_action(2,(1,0)) = (2,3,4,5,1,0)` — 이것이 이 모델 유일의
weight-2 group 원소(action)다. `word_after(p, action) =
compose(p, action)`, right-action 합성 `(g*h)(i)=g(h(i))`이므로:

\[
\mathrm{target}(\ell)
=\mathrm{word\_after}(p_\ell,\,\mathrm{action})
=\mathrm{compose}(p_\ell,\,\mathrm{action})
=\mathrm{compose}(\mathrm{compose}(p_0,\Sigma^\ell),\,\mathrm{action})
=\mathrm{compose}(p_0,\;\Sigma^\ell*\mathrm{action})
\]

(결합법칙, `compose`가 결합적이므로). **즉 6개의 candidate
target(ell=0..5)은 전부 `p_0`에 6개의 고정된(즉 `p_0`와
무관한) group 원소 `\{\Sigma^\ell * \mathrm{action}: \ell=0..5\}`를
차례로 적용한 것이다 — 이는 이전 라운드에서 경험적으로 확인한
"candidate target은 `S.p`(즉 `p_0`)만의 함수"라는 사실의 **손증명**이다.**

## Canonicalization과 무관한 literal statement인가

**그렇다.** 위 유도는 `core.compose`, `tail_action`, `SIGMA`라는
순수 group-이론적 정의만 사용했고, 이 프로젝트의
`canonicalize()`(left-S6 재라벨링)는 전혀 등장하지 않는다 —
canonicalize는 각기 다른 실제 상태를 비교하기 위한 도구일 뿐,
이 정리 자체는 canonicalization 이전의 리터럴 group 구조에서
성립한다.

## E-orbit quotient에서 이 move가 만드는 orbit map

`target(ell)`의 E-orbit(`ORBIT_PHASE[target(ell)].q`)은 `E_ID[canonical_e_orbit(target(ell))]`이며,
`canonical_e_orbit`은 `E=(1,2,3,4,0,5)` 생성 궤도의 최솟값을 취하는
연산이다. 이 유일한 weight-2 move가 유도하는 orbit map은
\(p_0 \mapsto q(\ell)\)(6개 값, `p_0`가 정해지면 완전히 결정)이며,
이번 라운드는 이 map 자체를 새로 유도하지 않고 그 **정의역이
`p_0` 하나뿐이라는 사실**(위 공식)만 증명했다 — orbit map의
구체적 궤도 구조(어떤 `p_0`가 어떤 6-tuple을 낳는지)는
`A2_TWO_ORBIT_CAUSAL_THEOREM.md`에서 이어서 다룬다.

## 성공 기준 (1) 평가

**달성됨(손증명)** — `tail_permutations(2)`가 정확히 1개 원소를
가진다는 것, 그리고 6개 candidate target이 `p_0` 하나만의 함수라는
것 둘 다 코드 열거가 아니라 순수 조합론/group 이론적 논증으로
증명했다.
