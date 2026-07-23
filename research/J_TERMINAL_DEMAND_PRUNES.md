# 추가 대칭, bit-dropping, meet-in-the-middle, terminal prune — 정직한 음성 결과 모음

이 문서는 섹션 2, 6, 7, 8(강화된 대칭·상태 압축·역방향 탐색·더 강한
terminal prune)을 다룬다. 결론부터: **이번 조사에서 새로운 안전한
축소 기법을 확립하지 못했다.** 각각 무엇을 시도했고 왜 안 됐는지
기록한다 — 시도하지 않은 척하지 않는다.

## 2. Left-S6보다 강한 안전한 stabilizer — **조사됨, 발견 못함**

`canonicalize()`는 이미 전체 left-`S6` 작용(720개 원소) 중
lexicographically 최소인 대표를 고른다 — 이는 **그 군 작용에 대해
이미 가장 세밀한 quotient**다. 더 강한 축소를 얻으려면 global
relabeling이 아닌, **이 특정 상태의 국소 구조**(어느 orbit이
unused인지 등)에서만 나오는 별도의 대칭이 필요하다.

가장 유력한 후보(unused E-orbit들 사이의 교환 대칭)를 검토했다: 두
개의 완전히 미사용(mask=0)인 orbit이 있다면 서로 바꿔도 무방한가?
하지만 이런 교환이 실제로 안전하려면 그 교환이 **global left-S6
relabeling으로 realizable**해야 canonicalize()가 이미 처리한
것이므로 새롭지 않다. Global relabeling이 **아닌** 방식의 국소
교환은, `J_EXACT_NORMAL_FORMS.md`(75개 반례쌍)와
`J_DOMINANCE_RULES.md`(B, C 반증)가 이미 보여준 대로, "같은 국소
모양이면 같은 미래"라는 가정 자체가 거짓임이 반복적으로 확인됐다 —
이런 국소 대칭이 안전하게 존재할 가능성은 낮아 보인다. **추가 대칭을
찾지 못했다 — 있다고도 없다고도 증명하지 않는다.**

## 6. Visited bit 일부 폐기 — **안전성 증명 못 함, 사용하지 않음**

오래전에 방문한 permutation 중 일부를 "더 이상 영향 없음"으로 보고
폐기할 수 있는지 조사했다. 이를 위해서는 다음을 증명해야 한다:

> 어떤 이전에 방문한 permutation \(w\)가, 남은 걸음의 **어떤** 미래
> joint의 target으로도 다시는 나올 수 없다.

이는 거짓일 가능성이 높다 — joint의 target은 `word_after(현재
p_after_rotation, move.action)`으로, 남은 walk 전체에 걸쳐 `p`가
계속 바뀌므로, 이론적으로 720개 permutation 중 상당수가 여러 단계
뒤에도 여전히 어떤 joint의 target 후보가 될 수 있다. "공간적으로
멀리 떨어진 permutation은 다시 안 나온다"는 국소성 논증은 이
model에서 성립한다는 근거를 찾지 못했다. **증명되지 않은 bit-dropping은
사용하지 않았다**(지시대로).

## 7. Meet-in-the-middle — **전면적 역탐색은 시도하지 않음, 이미 있는
필터로 대체**

정확한 역전이(inverse transition) 정의 없이 억지로 역탐색을 만들지
말라는 지시에 따라, 전면적인 backward search는 만들지 않았다. 대신
"terminal에서 반드시 만족해야 하는 필요조건 필터"는 이미 이전
작업에서 확립돼 있다:

- `Φ(S)>=0`(`SHORTFALL_BUDGET_THEOREM.md`)
- `can_complete_via_pure_rotation`(`verify_pure_rotation_suffix.py`,
  5/5 경계 케이스 검증됨)
- 정확한 `(P,O,D,F,H,Ndef)` 목표값

이것이 사실상 요청된 "terminal-compatible boundary signature"다 —
이미 있는 것을 다시 만들지 않고 재사용한다.

## 8. Φ보다 강한 terminal-demand prune — **이미 시도, 이미 음성 결과**

`FUTURE_SHORTFALL_LOWER_BOUND.md`(이전 라운드)에서 이미 permutation
수, path 수, orbit 수, phase deficit(D), strand 수(S) 전부를 relaxation
후보로 검토했고, 어느 것도 `Φ>=0`보다 엄격히 강한 새 산술적 하한을
주지 못함을 보였다. 이번 라운드에서 split/fragment 정보를 추가로
검토했으나(`J_EXACT_NORMAL_FORMS.md`의 fragment_components 등), 이를
정량적 하한으로 바꿀 방법을 다시 찾지 못했다 — 같은 결론을 반복
확인했을 뿐 새로운 강화는 없다.

## 종합

이번 라운드에서 확립된 새로운 축소 기법은 없다(섹션 2, 6, 7, 8
전부 negative). 실제로 유용했던 발견은 `J_STATE_SPACE_REDUCTION.md`
(forced-ell lemma, 폭발 원인이 joint-target 선택임을 규명)와
`J_DOMINANCE_RULES.md`(naive dominance 두 개 반증)이며, 이 문서는 그
반대편 — **시도했지만 안 된 것들**을 감추지 않고 기록한 것이다.
