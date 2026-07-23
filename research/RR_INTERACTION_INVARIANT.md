# RR (두 R 이벤트) interaction invariant

산출: `src/analyze_rr_interaction.py` -> `outputs/rr_interaction_analysis.json`.
전체 4,470개 RR 레코드에 대한 정확한(표본 아님) 집계 +
300개 표본에 대한 리터럴 재생 교차검증.

## 결론 먼저

RR에서 "두 R이 같은 incidence-component에 속한다"는 사건은 **전체
4,470개 중 정확히 10개(0.22%)**에서만 일어나며, 이 10개는 **예외 없이
모두** "첫 R의 target이 둘째 R의 source가 되는" chaining 사건의
부분집합이다 — 이는 코퍼스 전체(표본이 아님)에 대해 성립하는 **정확한
포함 관계**다. 역은 성립하지 않는다: chaining 75개 중 65개는
component가 unresolved로 남는다. 이것이 이번 조사에서 확인한 RR의
핵심 구조적 규칙성이지만, **완전한 이론(정리)으로 증명하지는
못했다** — 아래 §3에서 정직하게 그 한계를 밝힌다.

## 1. Orbit-relation 한계 통계 — 전체 코퍼스, 정확

| 관계 | 개수/4470 | 비율 |
|---|---:|---:|
| same_source (두 R의 source orbit 동일) | 12 | 0.27% |
| same_target (두 R의 target orbit 동일) | 1200 | 26.8% |
| first_source_second_target | 5 | 0.11% |
| first_target_second_source (**chaining**) | 75 | 1.68% |

`support`(두 R이 건드리는 orbit phase 집합의 겹침): overlap 1289,
disjoint 3181.

## 2. Component/Fragment 관계 — 전체 코퍼스, 정확

`component_relation`은 union-find 기반 "현재까지 방문된 orbit-hexagon
결합 성분"의 (첫 R 시점, 둘째 R 시점) 스냅샷 쌍이다. 4,470개 중
`('unresolved','unresolved')`가 4,170개(93.3%)로 압도적 — 이는 얕은
depth(macro depth<=6)에서 대부분의 orbit이 아직 전혀 방문되지 않아
union-find 상에 등록조차 안 됐기 때문이며, RA3/RA2에서 관측된
"fragment_hex가 F<=1 예산에 의해 구조적으로 강제된다"는 정리
(`RA3_A3R_ASYMMETRY.md` 참조)와는 **다른 메커니즘**이다 — 여기서
`unresolved`는 "아직 방문 안 됨"이지 "abandonment 예산 때문에 불가능"이
아니다. 이 둘을 섞어 하나의 이론으로 합치지 않는다.

`fragment_relation`(F<=1 예산 기반, RA3/A3R과 같은 필드)은 RR에서
**이질적**이다: slot0 2892 `no_observable_fragment` / 1536
`different_or_unresolved` / 36 `target_is_fragment_hex` / 6
`target_component_of_fragment`; slot1은 더 고르게 분산된다. 이는 두 R
모두 abandonment를 쓰지 않으므로 F 예산이 전체 walk 동안 계속
"미사용" 상태로 남아, 숨은 zero-charge `Z2_abandon_w2_new` 이벤트가
walk의 어느 지점에서든 자유롭게 발생할 수 있기 때문이다 — 이 메커니즘은
`RA3_A3R_ASYMMETRY.md`에서 리터럴 재생으로 **직접 검증**했다(같은
checkpoint, 같은 스크립트군의 `analyze_ra3_a3r_asymmetry.py`가 RR
표본에서 100% 이 메커니즘을 확인).

## 3. 후보 상관관계: "same component ⟹ chaining"

```
component_relation에 'same'이 포함된 레코드: 10개(전체 4,470 중)
  - 그중 chaining(first_target_second_source=True)인 것: 10/10 (100%)
  - 그중 support='overlap'인 것: 10/10 (100%)
  - same_target=True인 것: 0/10
  - same_source=True인 것: 0/10

chaining 레코드: 75개
  - component_relation 분포: ('unresolved','different') 65,
    ('unresolved','same') 7, ('different','same') 3
  - 전부 support='overlap'
```

**정방향 함의("same-component ⟹ chaining")는 전체 코퍼스에 대해
예외 없이 성립한다(반례 0개)** — 이는 표본이 아니라 전체 4,470개에
대한 정확한 계산이므로 **유한 완전 검증**으로 표시한다.

**역방향("chaining ⟹ same-component")은 성립하지 않는다** — chaining
75개 중 65개(86.7%)는 component가 `unresolved`로 남는다. 이는
"chaining이 일어나도 union-find가 그 사실을 통계적으로 확정하기에
충분한 방문 이력이 아직 쌓이지 않은 경우가 대부분"이라는 뜻이며, depth
제약(macro depth<=6) 때문일 가능성이 높다 — 더 깊은 depth에서는 이
65개 중 일부가 `same`으로 resolve될 수도 있다는 것이 자연스러운
추측이지만, 이는 **검증되지 않았다** (미관측/추측으로 표시).

## 4. 왜 완전한 "정리"로 승격하지 못했는가 — 정직한 한계

이 상관관계가 도출 가능한 이유(예: "두 R이 같은 성분에 속하려면 첫
R의 target이 둘째 R의 source가 되어야만 하는 구조적 필연성이 있다")를
**연역적으로 증명하지 못했다.** `component_relation`이 `unresolved`인
것은 "아직 그 orbit이 전혀 방문되지 않았다"는 얕은-depth 아티팩트와
"실제로 다른 성분에 속한다"는 구조적 사실을 구별하지 못하는 필드이므로,
이 필드 자체의 한계 때문에 정방향 함의가 우연히 강하게 나타났을
가능성을 배제할 수 없다. 따라서 이 결과는:

- **성립 사실 자체**(same-component ⟹ chaining, 4470개 전체에서 반례
  0개): **유한 완전 검증**.
- **그 이유에 대한 구조적 설명**(왜 이런 함의가 성립하는가): **미증명 —
  추측**으로만 표시한다. RA3/A3R처럼 F<=1 예산에서 연역적으로 도출되는
  정리와는 증명 수준이 다르다는 점을 명확히 구분해 기록한다.

## 5. 리터럴 교차검증

300개 RR 표본 전부에 대해 `analyze_interaction`으로 독립 재생한 결과,
`word_reconstructed == "RR"`이 300/300 일치했다 — 코퍼스 자신의
`word` 라벨이 신뢰할 수 있음을 재확인.

## 성공 기준 (3) 평가

"RR interaction invariant"라는 성공 기준은 **부분 달성**으로 기록한다:
정확한(표본 아님) 상관관계 하나(same-component ⟹ chaining, 반례 0/4470)를
찾았지만, 이를 뒷받침하는 구조적 정리는 아직 증명하지 못했다. 이는
정직한 중간 결과이며, "RR 정리 완성"이라고 과장하지 않는다.
