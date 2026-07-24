# Unique hub hexagon lemma와 necessity 증명

산출: `src/analyze_rr_hex0_ancestry.py`, `src/verify_rr_hex0_necessity.py`
-> `outputs/rr_ancestry_patterns.json`, `outputs/rr_hex0_causal_certificates.json`.

## 3-4. R2 same-component의 exact 필요조건 — Unique Hub Hexagon Lemma

### Lemma (Unique Hub Hexagon) — **손증명 + 4,470/4,470 유한 완전 검증**

> **F<=1 예산을 지키는 임의의 word(RR 포함, R은 절대 abandon하지
> 않으므로 RR 전체가 F<=1)에서, word 전체 역사에 걸쳐 **2개 이상의
> 서로 다른 joint의 target이 된 hexagon은 최대 1개뿐**이다.**

**증명**: `f1_normal_form`(코드, `superperm_partial_f1.py:303`)이
이미 선언하고 유지하는 불변식 — *"partial(0비트도 6비트도 아닌)
hexagon의 수는 최대 F+1개이며, 그중 `current`가 아닌 것은 최대
1개(`fragment`)"*. F<=1이므로 partial hexagon은 최대 2개(현재
hexagon + 최대 1개의 fragment)다. **current가 아니고 fragment도
아닌 모든 hexagon은 완전히 미방문(0비트)이거나 완전히
방문됨(6비트)이어야 한다.** 완전히 방문된 hexagon은 `extend()`의
`visited(target)` 체크에 의해 **다시는 어떤 joint의 target도 될 수
없다**(모든 6개 permutation이 이미 방문됨). 그리고 어떤 hexagon이
"current"였다가 한 joint에 의해 떠나지면, 그 순간 그 hexagon은 (a)
완전히 방문됐거나(joint가 ell=5에서 발동, 이제 CLOSED) (b) 부분
방문 상태로 남아 **fragment**가 된다(joint가 ell<5에서 abandon).
**즉 "current"라는 지위는 일시적이며, 한 번 떠난 hexagon이 "다시
current가 되는" 일은 없다 — 오직 fragment만 나중에 다시 target이 될
수 있다.** F<=1이므로 fragment는 word 전체에서 최대 1개뿐이다. □

**전체 코퍼스 재확인**: 4,470개 RR witness 전부(문자 재생, 표본
아님)에서, 2회 이상 target이 된 hexagon이 2개 이상 동시에 존재하는
경우는 **0건**이었다(`unique_hub_hexagon_lemma.violations = 0`).

### R2 same의 필요조건(따름정리, 손증명)

union-find에서 서로 다른 두 노드가 같은 root를 가지려면 이들을
잇는 union 연쇄가 존재해야 한다. Lemma에 의해, **word 전체에서 두
개의 서로 다른 orbit-등록 사건이 하나의 공통 노드를 공유할 수 있는
유일한 방법은 그 공통 노드가 hub hexagon(H*, 2회 이상 접촉된
유일한 hexagon)인 경우뿐이다**(다른 모든 hexagon은 정확히 1개의
orbit 등록에만 관여하는 "leaf"이므로, 그 자체로는 서로 다른 두
orbit을 이어줄 수 없다). 따라서:

> **정리(손증명)**: R2 자신의 component_relation이 "same"이려면,
> H*(hub hexagon, word 전체에서 유일하게 존재 가능)가 **존재해야
> 하고**, R2의 source orbit과 target orbit이 **둘 다** H*를 통해
> (직접 또는 그 orbit이 지닌 다른 leaf-hexagon을 거쳐 간접적으로)
> 연결돼 있어야 한다.

## 5. Hex-0(word-origin hex) 미접촉 상태의 component 분리 — 대우 방향

`word-origin orbit`(orbit 0)은 t=0부터 `word-origin hex`(hex 0)를
통해서만 등록된다(§1). Lemma에 의해, hex 0이 **H*가 아니라면**(즉
word 전체에서 hex 0이 단 1회만 접촉된다면 — 초기 등록 그 한
번뿐), orbit 0의 component는 **영원히 `{q_0, hex_0}` 둘뿐인
고립된 쌍**으로 남는다 — 어떤 다른 orbit도 여기 합류할 수 없다
(hex 0이 leaf이므로). 이는 정확히 요청된 대우 명제다:

> **hex 0이 R2 이전까지 H*가 되지 못하면(=hex-0이 2번째 접촉을
> 받지 못하면) ⟹ orbit 0의 component는 고립 상태를 유지하고, R2가
> orbit 0을 target으로 삼는 한 "same"이 될 수 없다(target=orbit0의
> component가 다른 어떤 orbit과도 연결되지 않았으므로).**

**손증명, Lemma의 직접 따름정리.** (단, 이는 "R2의 target이 orbit
0인 경우"에 국한된 대우다 — R2의 target이 orbit 0이 **아닌** 다른
orbit인 일반적 경우까지 포괄하는 완전히 일반적인 대우는 §6-7에서
추가로 다룬다.)

## 6. Hidden abandonment 위치별 분류 — 전체 코퍼스, 정확

`hidden_abandonment_timing_relative_to_r1_r2`(none/before_r1/between_r1_r2/after_r2)로
전체 4,470개를 R2 relation과 교차 집계했다:

| R2 relation | before_r1 | between_r1_r2 | after_r2 | 없음 |
|---|---:|---:|---:|---:|
| unresolved | 1,538 | 1,529 | 1,221 | — |
| different | 30 | 142 | 0 | — |
| **same** | **10** | 0 | 0 | 0 |

**판정**:

1. **hidden abandonment가 necessity proof를 깨는가?** — **아니오.**
   Hidden abandonment의 **존재 자체**는 Lemma(§3-4)의 전제
   조건(F<=1)과 완전히 호환된다 — Lemma는 애초에 "최대 1회의
   abandonment"만 가정하며, hidden abandonment는 그 1회를 구성하는
   구체적 사건일 뿐이다.
2. **오히려 hex 0 touch를 강제하는가?** — **부분적으로 그렇다.**
   same-component 10개 전부가 `before_r1`(word의 첫 joint가 바로
   그 hidden abandonment)이다 — 이는 강제는 아니지만(다른
   timing에서는 단 1건도 same이 안 나옴, 즉 **필요조건처럼
   작동함**), "왜 before_r1이 아니면 same이 전혀 안 나오는가"는
   §7의 hub-multiplicity 논증으로 설명된다: word의 첫 joint가 hex
   0에서 abandon해야만 hex 0 자체가 fragment가 되고(§3-4의 Lemma에
   의해 그것이 hex 0이 H*가 될 수 있는 유일한 경로), 그래야
   orbit 0의 component가 성장할 수 있다.
3. **hidden abandonment 없이도 같은 정리가 성립하는가?** —
   **그렇다, 자명하게**: abandonment가 전혀 없으면(F=0 유지)
   Lemma에 의해 H*가 아예 존재하지 않으므로(어떤 hexagon도 2회
   접촉될 수 없음), "same"은 애초에 불가능하다 — 이는 별도 case가
   아니라 §3-4 정리의 자명한 특수 경우다.
4. **proof를 case split해야 하는가?** — **아니오**, §3-4의 통합
   Lemma가 이미 abandonment 유무·위치를 모두 포괄한다. Case split은
   **설명을 위한 것**(§7의 8-패턴 분류)이지 증명 구조상 필수는
   아니다.

## 7. 75 chaining witness의 canonical proof certificate

75개 chaining witness 전부를 `(hub_is_word_origin_hex,
hidden_abandonment_timing, macro_distance, r2_own_component_relation)`
로 quotient한 결과 **정확히 8개의 distinct ancestry pattern**으로
축약된다(`outputs/rr_ancestry_patterns.json`의
`distinct_ancestry_patterns`). same-component에 해당하는 것은 그중
**단 1개 패턴**이며, 10개 witness 전부가 **문자 그대로 동일한
서명**을 공유한다:

```
hub_hexagon = word-origin hex (hex 0)
hub_first_touch_event_index  = -1 (initial_state() 자신의 등록)
hub_second_touch_event_index = R1의 own index (예외 없이, 10/10)
hidden_abandonment_timing    = before_r1 (10/10)
r2_own_component_relation    = same
```

**Canonical certificate(일반형)**: hex 0이 word의 첫 joint(hidden
abandonment)에 의해 fragment가 되고 → R1 자신이 그 fragment의
유일한 남은 자리를 완성(hub의 2번째이자 **마지막** 접촉, §7
데이터에서 multiplicity는 항상 정확히 2 — `outputs/rr_ancestry_patterns.json`의
hub_hexagon_stats 참고) → 이로써 H* = {orbit 0, R1의 target
orbit}의 2-orbit component가 만들어짐 → R2는 (target=orbit 0,
source=R1의 target orbit)을 택함으로써 H*의 두 구성원을 정확히
매칭시켜 "same"을 얻는다(§8의 axiom ablation이 보이듯, 이 마지막
단계가 정확히 "R2는 H*에 연결되려면 H*의 두 구성원 중 하나씩을
source/target으로 써야 한다"는 §3-4 정리의 직접 적용이다).

**일반 proof template으로의 승격**: 이 단일 패턴이 corpus 검증을
넘어 **일반 정리**로 승격되려면, "H*의 multiplicity가 항상
정확히 2다"(즉 3번째 orbit이 H*에 결코 합류하지 않는다)라는
사실이 depth<=6의 artifact가 아니라 일반적으로 성립함을 보여야
한다 — 이는 **미완료**(§`RR_INITIAL_ROOT_AXIOM.md` §2의 axiom
ablation이 정확히 이 지점을 "necessary but not generally proved
axiom"으로 표시한다).

## Bounded local search — same+non-chaining witness가 존재하는가

10개 same-component witness 전부의 **post-R1 상태**에서 depth<=5
bounded exhaustive search(각 witness당 220-284 node, **frontier
전부 소진 — 이 국소 범위 안에서는 완전 탐색**)를 실행해, R1의
target과 다른 source를 갖는 "same" R2 후보를 찾았다.

```
python3 src/verify_rr_hex0_necessity.py
→ 10/10 witness 전부 exhaustive_within_bound=true, counterexamples_found=0
```

**결론**: 이 10개의 구체적 시작점에서는 same+non-chaining 후보가
**국소적으로 완전히 배제**된다(exhaustive, 반례 0). 이는 일반
정리의 증명은 아니지만(다른 witness, 다른 depth에서는 검증되지
않음), 매우 강한 국소 증거다.
