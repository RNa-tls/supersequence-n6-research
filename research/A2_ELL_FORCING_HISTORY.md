# A2 legality의 최소 충분 통계, 그리고 ell-forcing invariant

## 4. Minimal sufficient statistic — 손증명 가능한 형태로 확보

`A2Legal(S,ell)`의 predicate(`A2_LEGALITY_PREDICATE.md` §2)를
다시 보면, `target(ell)`과 `q(ell)`은 **오직 `S.p`와 `ell`만의
함수**다(고정된 단일 weight-2 move `w2:10`과 rotation action
SIGMA를 적용한 결과이므로, history와 무관하게 `S.p`만 알면
결정됨). 따라서:

> **H_A2(S) := (S.p, {(target(ell) 방문 여부, q(ell)이 existing인지) : ell=0..5})**
>
> 이 minimal sufficient statistic이다 — `S.p`가 같은 두 상태는
> **candidate orbit 집합 {q(0),...,q(5)} 자체가 리터럴로
> 동일**하며(전체 orbit_masks나 hex_masks 전부가 아니라 이
> 6개 orbit/permutation에 대한 정보만 있으면 `A2Legal(S,·)`
> 벡터 전체를 결정할 수 있다.

**손증명**: `A2Legal(S,ell)`은 정의(§2)상 정확히 이 필드들의
함수이므로, 같은 `H_A2`를 가진 두 상태는 정의에 의해 같은
`A2Legal` 벡터를 갖는다 — 반례를 찾을 필요가 없다(구성상
자명하게 참). **U4 4개와 outlier가 전부 같은 `S.p`(=identity 근처
canonical 값)를 가진다는 사실**(`A2_LEGALITY_PREDICATE.md` §3
데이터)이 바로 이들의 candidate orbit 집합이 리터럴로 동일한
이유이기도 하다.

**전체 visited mask가 정말 필요한가?** → **아니다** — `H_A2`는
전체 720비트 hex_masks/720비트 orbit_masks 중 오직 이 6개
candidate와 관련된 소수의 비트만 필요로 한다. 이는 완주
가능성(전체 문제)이 아니라 **A2 legality라는 국소 질문에 한해**
전체 visited 이력이 불필요함을 보여준다 — 완주 obstruction에는
당연히 전체 이력이 필요할 수 있다(이 결과가 그것까지 함의하지는
않는다).

## 5. Ell-forcing invariant e(S)

\[
e(S) = \text{그 유일한 } \ell \in \{0,...,4\} \text{ 이 존재한다면, 즉 } \mathrm{orbit\_masks}[q(\ell)] \neq 0 \text{ 이고 } \mathrm{target}(\ell) \text{이 미방문인 } \ell.
\]

이는 **정의에서 직접 유도된 것**이지 데이터 fitting이 아니다 —
`A2Legal`의 predicate 자체가 이 값을 정의한다. 요청된 "congruence
형태"(`e(S) ≡ g(S) mod 6`)나 "ancestry path length" 같은 더 깊은
독립적 공식은 이번 라운드에서 찾지 못했다 — `e(S)`는 `S.p`가
결정하는 6개 candidate orbit 중 **어느 것이 과거에 touched됐는지**에
의해 결정되며, 이 "과거에 touched됐는지"라는 사실 자체를 더 압축된
닫힌 형태(ancestry depth 같은 단일 정수)로 표현하는 데는
이르지 못했다(**미완료**) — `U4_HISTORY_CAUSAL_CERTIFICATES.md`
§6에서 이를 "어느 두 orbit의 existing 상태가 반전됐는가"라는
구체적(그러나 닫힌 공식은 아닌) 형태로 답했다.

## 성공 기준 (2) 평가

"ell_A2를 강제하는 최소 충분 history invariant"는 **부분
달성**이다: `H_A2(S)`라는 정확하고 증명 가능한 minimal sufficient
statistic은 확보했다(성공 기준의 "최소 충분 통계" 부분). 하지만
이를 하나의 **독립적으로 유도되는 닫힌 형태 공식**(congruence,
ancestry depth 등)으로 더 압축하는 데는 이르지 못했다.
