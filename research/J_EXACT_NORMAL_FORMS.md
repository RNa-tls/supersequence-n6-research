# J 상태 230개의 exact normal form 시도와 그 손실성

산출: `outputs/j_exact_normal_forms.json` (recover된 230개 literal 상태로부터
직접 계산).

## 1. 사용한 표현

각 상태에 대해 실제 literal 상태(`exact.f1_normal_form`)로부터:

- `fragment_components`, `fragment_hex`의 존재 여부, `current_components`
  (F<=1 정확한 lossless normal form, `superperm_partial_f1.py::f1_normal_form`)
- `steps_after_J` = macro-path 안에서 J 이후 남은 zero-charge step 수
  (word 분류가 "이후 얼마나 더 갔는지"는 무시하고 "정확히 하나의
  positive-charge 사건 = J"만 요구하므로, 230개는 J로부터 서로 다른
  거리에 있다)

이를 묶어 `coarse_fingerprint = (fragment_components, fragment_hex 존재,
current_components, steps_after_J)`로 정의했다.

## 2. 결과 — **유한 완전 검증**

- 230개 상태가 **21개**의 `coarse_fingerprint` 그룹으로 나뉜다.
- `steps_after_J` 분포: `{0: 51, 1: 40, 2: 38, 3: 24, 4: 77}` — J가 이
  bounded 탐색의 마지막 사건인 경우(0)가 51개, 나머지는 J 이후 1~4개의
  추가 zero-charge macro joint를 거쳤다.
- 19개 그룹이 2개 이상의 원소를 가진다.

## 3. Quotient는 손실적이다 — **반례로 확인됨**

같은 `coarse_fingerprint`를 가진 상태들의 **1-step 합법 continuation
shape** (증명된 post-J 알파벳으로 제한한, `(weight, new_orbit)`별 합법
edge 개수)를 비교했다. 완전히 같은 fingerprint 그룹 안에서도 이 shape가
다른 경우가 **75쌍** 발견됐다 (19개 다중-원소 그룹 전체에서).

**최소 반례쌍** (`outputs/j_exact_normal_forms.json`
-> `minimal_counterexample_pair`):

```json
{
  "fingerprint": "(((2, 3, 2),), True, ((0, 0, 1),), 0)",
  "hash_a": "1a1ac861c6531f75c023a9b3ce98645a7105cfc1aed3d03e99708a2a4ffd9334",
  "shape_a": {"3existing": 1, "3new": 2},
  "hash_b": "00fb30029d49684e5c53f7c1e8c0988e1db9e6b4c72ce556471632e5f5ebf575",
  "shape_b": {"2existing": 1, "3existing": 1, "3new": 2}
}
```

(`shape` keys: `{weight}{"existing" if targets a used orbit else "new"}`,
value = count of legal 1-step continuations of that kind, restricted to
the proven post-J alphabet.)

`hash_a`는 바로 그 유일한 literal representative다. 같은 fragment 모양,
같은 current 모양, 같은 `steps_after_J=0`을 가진 `hash_b`가 존재하지만,
`hash_a`는 1-step에서 weight-2 blocked 옵션이 **없고**, `hash_b`는
있다 — 즉 이 fingerprint만으로는 이후 legal continuation tree가 동형임을
전혀 보장하지 못한다.

> **결론: 이 coarse fingerprint(또는 그와 동등한, fragment/current
> component 모양 + steps_after_J만으로 이루어진 어떤 요약도)로는
> exact canonical normal form을 구성할 수 없다.** 완전한 동형을 보장하려면
> 최소한 각 상태의 **전체 hex_masks/orbit_masks**(즉 사실상 canonical
> state 자체)가 필요하며, 이는 230개를 유의미하게 압축하지 못한다
> (state 자체가 이미 canonical하므로 quotient가 항등에 가깝다).

이는 이 코퍼스가 이미 A3R word에서 발견한 것과 같은 종류의 현상
(`minimum_counterexample_word_phase_to_tail_determinacy`,
`legacy_research/PARTIAL_F1_N2_DEFECT_INTERACTIONS.md`)이 J word에도
그대로 나타남을 **독립적으로 재확인**한 것이다.

## 4. 실용적 함의

230개를 21개의 "family"로 그룹화하는 것은 **국소 fingerprint로는
가능**하지만, 그 grouping이 이후 탐색을 대표하는 유효한 reduction은
아니다. §6(`J_BRANCH_CLOSURE_STATUS.md`)에서 이 사실이 closure 분류에
직접 반영된다 — "소수 family로 완전 환원"(선택지 B)을 주장할 수 없는
이유가 바로 이것이다.
