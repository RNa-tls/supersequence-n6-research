# H_A2 필요충분성 — 충분성 손증명, 필요성은 부분적으로만 실제 witness로 확인

## 2. H_A2 정의 재확인

\[
H_{A2}(S) = \bigl(S.p,\ \{(\mathrm{visited}(\mathrm{target}(\ell)),\ \mathrm{existing}(q(\ell))) : \ell=0,\dots,5\}\bigr)
\]

## 충분성 — 손증명

`UNIQUE_WEIGHT2_MOVE_THEOREM.md`가 증명했듯 `target(ell)`과
`q(ell)`은 순수하게 `S.p`와 `ell`의 함수(고정된 group 원소
`Σ^ℓ∘action`을 통해)이며, `A2Legal(S,ell)`의 predicate
(`A2_LEGALITY_PREDICATE.md` §2) 자체가 정확히
`¬visited(target(ell)) ∧ ¬visited(σ(p_ell)) ∧ existing(q(ell))`로
정의된다. **`H_A2`에 포함된 성분만으로 이 predicate의 우변 전체를
평가할 수 있으므로**(단, `¬visited(σ(p_ell))`는 `ell<5`일 때
자동 참이고 `ell=5`일 때만 결정적인데, 이는 `S.p`만으로 결정되는
별도 사실 — 아래 ablation에서 다룸), `H_A2(S)=H_A2(T)`이면
`A2Legal(S,·) = A2Legal(T,·)`이다. **손증명, 구성에 의해 자명.**

## 각 성분의 필요성 — Ablation

| 제거한 성분 | 필요성 증명 방법 | 결과 |
|---|---|---|
| `existing(q(4))`(orbit 1) | **실제 witness 쌍** | U4(`17a42b24ccfb` 등)와 outlier(`e2b44997e783`)는 `visited(target(4))=False`로 동일하지만 `existing(q(4))`가 각각 True/False다 — 제거하면 두 상태가 같은 축약 통계를 갖지만 `A2Legal(·,4)`는 True/False로 다르다. **필요성 확인(exact witness).** |
| `visited(target(ell))`(임의 ell) | **추상 논증만**(실제 24개 corpus에는 이 필요성을 보여주는 쌍이 없음 — `existing=True`이면서 `visited`가 다른 두 witness가 코퍼스에 없음) | predicate 정의상 `visited(target(ell))=True`이면 `existing` 값과 무관하게 즉시 `A2Legal=False`가 되므로, 이 비트가 논리적으로 독립적 정보를 담는다는 것은 predicate 구조에서 **연역적으로 자명**하다 — 그러나 이를 보여주는 **실제 corpus witness 쌍은 이번 라운드에서 찾지 못했다**(abstract over-approximation으로만 표시). |
| `S.p` 전체 | **추상 논증만** | 24개 corpus 전부가 동일한 `S.p`(=identity)를 공유하므로 이 성분의 실제 필요성을 보여주는 쌍 자체가 존재하지 않는다 — `p_0`가 다르면 6개 candidate target 전체가(고정 group 원소를 통해) 완전히 달라진다는 것은 `UNIQUE_WEIGHT2_MOVE_THEOREM.md`의 공식에서 연역적으로 자명하지만, exact witness로 뒷받침하지 못했다. |

## 정직한 결론

**충분성은 완전히 손증명됐다.** **필요성**은 `existing`-비트에
대해서는 실제 corpus witness로 확인됐지만, `visited`-비트와
`S.p`에 대해서는 predicate 구조로부터의 연역적 논증뿐이며 이
24개 코퍼스 안에 그 필요성을 "보여주는" 실제 반례 쌍이 없다 —
**"minimal sufficient"라는 표현을 완전한 정리로 승격하려면
`visited`/`S.p` 필요성의 exact witness가 더 필요하며, 이번
라운드는 그 exact witness를 확보하지 못했다.**

## 성공 기준 (2) 평가

**부분 달성**: 충분성(손증명) 완료, 필요성은 1/3 성분만 exact
witness로 확인, 나머지 2/3는 연역적이지만 witness 없는
논증(abstract over-approximation)으로 남는다.
