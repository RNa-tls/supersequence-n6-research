# Abstract countermodel과 숨은 permutation-level axiom

산출: `src/enumerate_rr_abstract_models.py` -> `outputs/rr_abstract_models.json`.

## 8. Minimal abstract countermodel search — 발견됨

`RR_INCIDENCE_FOREST_LEMMA.md`가 보였듯, RR 코퍼스가 지키는 순수
그래프 공리는 (a) bipartite, (b) orbit-degree<=5/hex-degree<=6,
(c) forest(사이클 없음), (d) R은 existing(이미 등록된) target만
사용, (e) first/second R의 시간 순서다. 이 공리들**만**을 보존하는
작은 abstract 모델을 직접 구성했다:

```
event0: orbit B ---hex X--- (B가 hex X를 통해 처음 등록됨, "fresh"에 해당)
event1(R1): orbit A -> B, hex Y로 등록 (A는 R1의 source, 별도 edge 불필요)
event2: 기존 orbit B가 다시 hex X를 통해 참조되며, 그와 동시에
        **다른** orbit C도 hex X에 등록됨 (하나의 hexagon이 여러
        orbit의 port를 가질 수 있다는 것은 실제 모델의 진짜 성질 —
        하나의 hexagon은 6개의 서로 다른 orbit에 닿는다,
        `RR_SAME_COMPONENT_CHAINING_THEOREM.md` §1.2)
event3(R2): source=C, target=B
```

이 구성은 **모든 나열된 공리를 지킨다**(union-find 시뮬레이션으로
직접 확인: `redundant union == 0`, 즉 여전히 forest다) — 그런데
`R2`의 source(C)가 `R1`의 target(B)과 **다름에도**(non-chaining),
`root(C) == root(B)`(둘 다 hex X를 통해 이미 병합됨)이므로
`R2`의 own component_relation은 **"same"**이다.

```
python3 src/enumerate_rr_abstract_models.py
→ conclusion: "SAME-COMPONENT NON-CHAINING COUNTEREXAMPLE CONSTRUCTED
   (abstract, graph-axioms only)"
```

**결론**: 나열된 그래프 공리(forest 포함)만으로는 "same-component
⟹ chaining"을 강제하기에 **불충분**하다 — corpus가 보여주는
정확한 implication(4,470/4,470)은 이 abstract 모델에는 없는 **추가
정보**에 의존한다.

## 9. 숨은 axiom 식별

abstract countermodel의 event2가 실제 n=6 모델에서 왜 (지금까지
관측된 4,470개 안에서는) 발생하지 않는지 — 즉 "R1의 target이 아닌
**다른** orbit C가, R1의 target(B)이 이미 등록한 것과 **같은**
hexagon을 통해 독립적으로 등록되고, 그 뒤 R2가 정확히 그 C를
source로 삼아 B를 target으로 재사용하는" 경로가 왜 관측되지
않는지 후보를 분리한다.

| 후보 | 그래프 공리인가, permutation 공리인가 | 이 코퍼스에서의 상태 |
|---|---|---|
| phase compatibility (한 orbit의 5개 phase는 서로 다른 5개 hexagon에 정확히 1:1 대응) | **permutation 공리**(§1.2에서 손증명, 144/144 전수 검사) | 이 자체는 abstract 모델에도 이미 반영돼 있음(위반 없음) — 배제 요인 아님 |
| literal overlap (hex 0이 `initial_state()`로부터 t=0에 유일하게 사전등록된다는 사실) | **permutation 공리**(모델 정의 자체) | **핵심 후보.** 코퍼스의 모든 same-component 사례가 예외 없이 hex-0을 경유했다(§5, 10/10) — abstract 모델의 event2는 hex-0이 **아닌** 임의의 hex X를 사용했는데, 실제 코퍼스에서는 hex-0 **외의** hexagon을 통한 "제3의 orbit 우회 bridge"가 4,470개 중 단 한 건도 관측되지 않았다 |
| unique weight-3 target (weight=3 tail은 정확히 3개뿐 — `tail_permutations(3)`) | **permutation 공리**(라운드 10에서 이미 증명: `is_indecomposable` 기반) | R 이벤트가 target으로 삼을 수 있는 permutation의 집합이 이 3개의 고정 group 원소로 제한된다는 사실이, 그런 "우회 bridge"에 필요한 특정 (source,target) 조합을 원천적으로 좁힐 가능성 — **연역적으로 끝까지 추적하지 못함, 추측으로만 기록** |
| hexagon full-sweep / endpoint parity | **permutation 공리** | RR은 F=0에서 시작하지만 숨은 `Z2_abandon_w2_new`로 F가 1이 될 수 있어(`RR_INTERACTION_INVARIANT.md`에서 이미 확인), "F=0 전체에서 매 joint가 fresh hex를 target으로 삼는다"는 이전 라운드의 정리가 RR 전체에 **일반적으로 적용되지 않는다** — 이번 라운드에서 실제로 확인(§10 아래) |
| E-orbit orientation | 미검토 | 이번 라운드 범위 밖 |

### 정직한 결론

**hidden axiom의 가장 강한 후보는 "hex 0(word 시작 hexagon)이
유일하게 t=0부터 사전등록되어 있다"는 사실과 "RR word 길이가
depth<=6로 짧아 등록되는 edge 수가 최대 ~7개에 불과하다"는 사실의
**조합**이다 — 짧은 word에서는 하나의 orbit이 hex-0을 거쳐
병합되는 것이 **유일하게 실현 가능한** 병합 경로이고, abstract
countermodel의 event2(제3의 orbit이 non-hex-0 hexagon을 통해
독립적으로 병합)에 필요한 "동일 hexagon을 두 orbit이 각각 다른
사건으로 등록"이라는 추가 사건이 이 짧은 예산 안에서 실현된 사례가
코퍼스에 없었다는 것이다.** 이것이 **일반적으로 불가능**하다는
연역적 증명은 얻지 못했다 — depth<=6보다 긴 RR word가 존재한다면
(이 코퍼스의 depth 상한 밖) event2 같은 경로가 실현될 수도 있다는
가능성은 **정직하게 열어 둔다**(추측 수준).

## §10 관련 부가 사실: RR이 F=0 전체 구간이 아니다

이번 라운드에서 리터럴 재생 중 직접 확인: RR word 안에 **숨은
`Z2abandon`(weight=2, abandonment=True, new_orbit=True — zero-charge
abandoning) 이벤트가 흔히 섞여 있다**(예:
`2d88642a05...`의 idx=0). 이는 F가 0→1로 바뀔 수 있다는 뜻이며,
이전 라운드들이 "A2 이전 F=0 구간 전체"에 대해 증명한
"모든 joint는 완전히 새 hexagon을 target으로 삼아야 한다"는 정리는
**RR 전체에 일반적으로 적용되지 않는다**(F=1로 전환된 이후에는
fragment 메커닉이 개입한다). 이번 라운드의 모든 결과(§1-9)는 이
사실을 전제하지 않고 직접 리터럴 재생으로 얻었으므로 이 구분과
무관하게 유효하다 — 다만 이 사실 자체를 이번 라운드의 정직한 부가
관측으로 기록해 둔다(이전 라운드 요약에 있던 "F=0 전체 구간에서
ell=5 강제"라는 표현은 RR 전체로 일반화될 수 없다는 것을 이번
라운드가 직접 재생으로 확인·정정했다).
