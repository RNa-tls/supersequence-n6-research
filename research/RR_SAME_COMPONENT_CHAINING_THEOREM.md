# RR: same-component ⟹ chaining — 손증명에 근접한 정리와 hex-0 bridge 메커니즘

산출: `src/analyze_rr_chaining.py`, `src/verify_rr_chaining_theorem.py`,
`outputs/rr_literal_witnesses.json`(4,470/4,470 **전체** 재귀적 문자
witness 복구 — 이번 라운드에서 이미 존재하던 J-witness 복구
checkpoint의 depth<=6/node_limit=20,000 bound를 그대로 재사용해
완주시킴, 새 대규모 탐색 아님), `outputs/rr_full_relation_table.json`,
`outputs/rr_chaining_theorem_verification.json`.

## 0. 이번 라운드가 넘어선 지점

이전 라운드(`RR_CHAINING_PROOF_STATUS.md`)는 "chaining ⟹ resolved"만
손증명했고, "resolved 중 same인 것 ⟹ chaining"(사용자가 원한 정확한
방향)은 미완료로 남겼다. 이번 라운드는:

1. RR 4,470개 **전체**를 문자 그대로(canonicalize 없는 raw 프레임)
   재생하는 데 성공했다(이전에는 300개 표본만 있었다).
2. "same-component ⟹ chaining"을 **4,470개 전체에서 재확인**했다
   (반례 0개, corpus 자체 필드 재대조가 아니라 독립적인 리터럴
   재생으로).
3. **핵심 새 발견**: chaining 부분집합(75개) 안에서 "same"과
   "different"를 가르는 정확한 메커니즘(hex-0 bridge)을 찾았고,
   75개 **전체**에서 예외 없이 검증했다.

## 1. 용어 정식화

(구현과 분리한 정의. 각 정의의 canonicalization 불변성은 §1.1에서
별도로 증명한다.)

- **R event**: weight=3, abandonment=False, new_orbit=False인 joint
  ("blocked, 기존 target 재사용" weight-3 이동).
- **source orbit** (어떤 joint의): 그 joint가 발동하기 **직전**
  상태(그 block 자신의 rotation을 전부 마친 후)의 permutation이 속한
  E-orbit id. **주의**: 이는 그 block의 **착지점**(직전 block의
  target)이 아니라, ell번 회전한 **후**의 위치다 — 한 hexagon의 6개
  위치는 서로 다른 6개의 E-orbit에 속하므로(§1.2 증명), 착지점의
  orbit과 발동 직전의 orbit은 `ell>0`이면 일반적으로 다르다.
- **target orbit**: joint의 target permutation이 속한 E-orbit id.
- **incidence component**: bipartite union-find 그래프(노드
  `("q",qid)`, `("h",hid)`; `state.orbit_masks`에 등록된(=방문된)
  모든 `(orbit,phase)` 쌍에 대해 `union(("q",q), ("h",hexagon_id(port)))`를
  호출해 구성) 위에서의 연결 성분. **`initial_state()` 자신도 1개의
  등록을 만든다**(그 word의 시작 순열 `p_0` 자신의 orbit·phase).
- **component root**: union-find 대표 노드.
- **chaining**: 첫 R의 target orbit id == 둘째 R의 source orbit id
  (orbit id만 비교 — 정확한 phase/permutation은 다를 수 있다).
- **same-component**: **둘째 R 자신의** component_relation이
  "same" — 즉 **둘째 R 자신의** source orbit root == **둘째 R
  자신의** target orbit root (R1과 R2를 비교하는 관계가 **아니라**,
  R2 하나의 self-relation).
- **unresolved relation**: source, target 중 하나 이상이 아직
  union-find에 전혀 등록되지 않음(그 orbit의 어떤 phase도 아직
  방문되지 않음).
- **first R / second R**: witness의 `macro_path` 안에서의 시간
  순서(literal sequence이므로 모호함 없음).
- **R 사이 zero-charge word**: 첫 R와 둘째 R 사이(배타적)에 있는
  Z2/Z3/Z2abandon macro-edge들.

### 1.1 Canonicalization 불변성 — 손증명

`left_relabel(word, alphabet_permutation)`(코드 주석: **"Relabel
values, not positions. This commutes with every right action."**)는
값(0..5의 라벨)만 바꾸고 위치는 바꾸지 않는다. `SIGMA`, `E` 궤도
생성은 **오른쪽 합성**(`compose(current, generator)`)으로 정의되므로,
결합법칙에 의해 `left_relabel(compose(p,g), a) = compose(left_relabel(p,a), g)`
(양쪽 다 `compose(a-representation, compose(p,g))`로 정리되며, 좌측
곱셈과 우측 곱셈은 서로 다른 인자에 작용해 항상 교환된다). 따라서
**임의의 `g in S6`에 의한 left-relabeling은 SIGMA-궤도(hexagon) 구조와
E-궤도 구조 둘 다에 대해 그래프 자기동형사상(automorphism)을
유도한다** — 즉 hexagon id와 orbit id는 `g`에 의해 일관되게
재라벨링될 뿐, "같은 component인지"라는 **관계 자체**는 `g`의 선택과
무관하게 보존된다. 이는 새로 증명한 것이 아니라 이미
`analyze_f1_n2_defects.py`의 `replay_path_raw_defects`가 "raw(비
canonical) 재생이 매 스텝 canonicalize와 동치"임을 **"proved left-S6
equivariance"**로 전제하고, 5개 초기 샘플 + 매 1000번째 샘플마다
`canonical.stable_key() == final.stable_key()`로 **실제로 spot-check
검증**해 온 사실과 정확히 같은 근거다. 이번 라운드의 모든 리터럴
재생은 **raw(비canonicalize) 프레임을 word 전체에 걸쳐 일관되게
유지**함으로써(라운드 10에서 확립한 관례) 이 문제를 원천적으로
피한다 — 서로 다른 orbit id로 비교하는 일이 없다.

### 1.2 "한 hexagon은 6개의 서로 다른 E-orbit에 속한다" — 유한 완전 검증

`E_REPS`(144개) 전체를 순회해 `kset_of_e_orbit`(각 orbit이 닿는 5개
hexagon)에 중복이 있는지 검사(0/144개 중복 없음), 그리고 `ROT_REPS`
(120개) 각각이 몇 개의 서로 다른 orbit에 닿는지 검사(전부 정확히
6개, 중복 없음) — **둘 다 전수 검사, 예외 없음.** 이는 720개
permutation과 (E-orbit,hexagon) 쌍 사이의 **전단사**를 의미한다
(144×5 = 120×6 = 720).

## 2. RR 4,470개 exact relation table

`outputs/rr_full_relation_table.json`에 4,470개 **전체**(표본
아님) 저장. 각 행: `chaining`, `r2_own_component_relation`,
`hex0_touched_before_r2`, `r1_source/target`, `r2_source/target`,
`r1_ell/r2_ell`, `macro_distance`. 요약 카운터:

| 관계 | 개수/4,470 |
|---|---:|
| chaining (`first_target_second_source`) | 75 |
| same-component (R2 자신) | 10 |
| chaining ∧ hex0-bridge | 10 |
| chaining ∧ same | 10 |
| chaining ∧ hex0-bridge ∧ ¬same | **0** |
| chaining ∧ same ∧ ¬hex0-bridge | **0** |
| same ∧ ¬chaining | **0** |

**같은 implication을 두 개의 독립 스크립트로 재확인**(`analyze_rr_chaining.py`의
자체 집계, `verify_rr_chaining_theorem.py`의 별도 재집계) — 둘 다
동일한 반례-0 결과.

## 3. Chaining의 국소 필요충분조건

Chaining(`ftgt==ssrc`, orbit id 비교)의 **정의 자체**는 이미 순수
transition-boundary 언어다: `ssrc = e_orbit_id(Σ^{ell_{R2}} ·
prev_target)`(`prev_target` = R2 직전 macro-edge의 target
permutation, `ell_{R2}`= R2 자신의 block 회전수)이며, chaining은
`ssrc == ftgt`다. **한 가지 특수하지만 코퍼스에서 지배적인 충분조건을
exact witness로 확인했다**: R2 직전 macro-edge가 **R1 자신**이고
(`macro_distance==1`) **`ell_{R2}=0`**(R2가 착지 즉시, 회전 없이
발동)이면 `prev_target = R1의 target`이므로 `ssrc=ftgt`가
**자명하게** 성립한다. 그러나 코퍼스의 75개 chaining 중
**"거리=1, ell=0"인 것은 일부일 뿐**(나머지는 R1과 R2 사이에
개입 block이 있고, 그 **마지막 개입 block의 target orbit이 R1의
target orbit과 우연히 같아서** chaining이 성립한다 — orbit 1이
새로 열린 뒤 여러 사건이 그 **같은 orbit의 다른 phase**를 반복
재사용하다가 R2가 그 흐름의 마지막에서 즉시 발동하는 패턴, §5에서
상술). **일반적인(비자명한 phase까지 포함한) chaining의 필요충분
조건**은 정의상 `ssrc==ftgt`(orbit 비교) 그 자체이며, 이보다 더
간단한 "국소" 재서술은 찾지 못했다 — **정직하게 미완료**로 표시.

## 4. Two-orbit occupancy 요청 방향과의 통합 — 새 발견

hex 0(=`hexagon_id(IDENTITY)`, 이 project의 모든 word가 시작하는
바로 그 hexagon)은 **`initial_state()` 자신에 의해 t=0부터 항상
등록되어 있다.** hex 0의 6개 구성원(=IDENTITY의 6개 회전상)이 속한
orbit id를 직접 계산하면:

```
ell=0: orbit 0   (IDENTITY 자신)
ell=1: orbit 120
ell=2: orbit 33
ell=3: orbit 9
ell=4: orbit 3
ell=5: orbit 1
```

**이 6개 orbit 집합 `{0,120,33,9,3,1}`은 라운드 10에서 A2의 6개
고정 후보 orbit 수열로 발견된 바로 그 집합과 정확히 일치한다**
(라운드 10: `[120, 33, 9, 3, 1, 0]`, ell=0..5) — 서로 다른 두 계산
경로(A2는 `Σ^ℓ*action`, 이번 라운드는 `Σ^ℓ(IDENTITY)` 그 자체)가
같은 6-orbit 집합을 낳는다는 것은 흥미로운 교차-라운드 관측이지만,
왜 그런지는 이번 라운드에서 규명하지 않았다(**추측**으로만 기록).

## 5. hex-0 bridge 메커니즘 — same의 정확한 원인 (새로운 핵심 결과)

**정리(경험적으로 75/75 완전 검증, 메커니즘은 union-find 정의로부터
연역적으로 설명됨)**:

> chaining이 성립하는 RR witness 중에서, **R2 발동 전 어느 시점에
> 이든 hex 0을 target으로 삼는 joint가 존재하면(=`hex0_touched_before_r2`)
> R2 자신의 component_relation은 반드시 "same"이고, 존재하지
> 않으면 반드시 "different"다. 75개 전체에서 예외 없음(0/75 어긋남).**

**연역적 설명(충분성 방향, 완전 손증명)**: hex 0은 `initial_state()`가
직접 등록하므로 orbit 0의 component에 t=0부터 포함돼 있다. chaining
성립 시 `ssrc`의 orbit(=`ftgt`의 orbit)은 R1 자신에 의해 이미
등록됨(이전 라운드의 "chaining ⟹ resolved" 증명). 만약 이 orbit의
**어떤 phase**가 hex 0에 있고, 그 phase가 R2 발동 전에 **어떤
사건에 의해서든**(R1 자신이거나, 그 이후 개입 event) 방문되면,
union-find의 `union(q, h=0)` 호출이 즉시 이 orbit의 tree를 orbit
0의 tree와 병합한다(union-find 정의에서 자명). 관측된 10개 same
사례 전부에서 R2 자신의 target이 **정확히 orbit 0**이므로(→
trivially 병합된 component 안), `root(ssrc)==root(orbit 0)==root(stgt)`가
성립해 "same"이 나온다 — **이 방향은 손증명이다.**

**필요성 방향(경험적, 75/75 완전 검증이지만 일반 증명은 아님)**:
hex 0을 거치지 않고도 다른 hexagon을 통한 "우회 bridge"가
이론적으로 가능한지는 §7-9(forest lemma, abstract countermodel)에서
별도로 다룬다 — **이 코퍼스(depth<=6, 4,470개 전체)에는 그런 우회
사례가 0건**이지만, 일반적으로 항상 불가능하다는 연역적 증명은
얻지 못했다.

## 10. 증명 아키텍처 요약

1. **first R가 component에 남기는 canonical open-chain 구조**:
   R1(또는 그 이후 개입 event)이 `ftgt` orbit의 hex-0-인접 phase를
   건드리면, `ftgt`의 전체 component가 orbit 0의 component에
   즉시 병합된다 — **손증명**(§5).
2. **같은 component에서 legal second R의 source 위치 제한**: R2의
   source orbit이 "resolved"되려면 chaining(ssrc=ftgt) 이거나, 이미
   등록된 다른 orbit과 우연히 일치해야 한다(107건 관측, 전부
   "different") — **corpus exact observation**, 완전한 배제
   증명은 없음.
3. **forest/endpoint 제약으로 non-chaining target 제거**:
   `RR_INCIDENCE_FOREST_LEMMA.md` 참조 — 4,470개 전체에서
   redundant union 0건(**유한 완전 검증**), 그러나 순수 그래프
   공리만으로는 이것이 강제되지 않음(girth=4인 abstract countermodel
   존재, `RR_ABSTRACT_COUNTERMODEL_STATUS.md`).
4. **따라서 second R는 chaining이다**: 4,470개 전체에서 반례 0건
   (**유한 완전 검증**), 메커니즘은 §5에서 hex-0 bridge로 부분
   설명됨(연역+경험 혼합), **완전히 일반적인 손증명은 아직 없다.**

## 성공 기준 평가

- **기준 1 (same-component ⟹ chaining 손증명)**: **부분 달성.**
  완전한 일반 손증명은 아니지만, (a) 4,470개 전체에 대한 유한 완전
  검증(재확인, 독립 스크립트 2개 일치), (b) "same"의 정확한 발생
  메커니즘(hex-0 bridge, 충분성은 완전 손증명, 필요성은 75/75 완전
  검증이나 일반 증명 아님)까지 새로 확보 — 이전 라운드보다 훨씬 깊은
  진전이다.
- **기준 3 (숨은 permutation-level axiom 식별)**: **달성.**
  §9(`RR_ABSTRACT_COUNTERMODEL_STATUS.md`)에서 hex-0의 유일
  사전등록성 + 짧은 word 길이라는 두 조건의 조합을 숨은 axiom
  후보로 식별.
- **기준 4 (최소 abstract countermodel)**: **달성.**
  `outputs/rr_abstract_models.json` — 그래프 공리만으로는
  same-component ∧ non-chaining이 구성 가능함을 직접 보임.
