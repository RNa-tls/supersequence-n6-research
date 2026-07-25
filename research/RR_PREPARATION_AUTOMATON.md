# Preparation symbolic automaton (라운드 22)

산출: `src/build_rr_preparation_automaton.py` ->
`outputs/rr_preparation_automaton.json`. completion search 없음.

## 1. Boundary state 정의 (invariant)

\[
Q=(\text{hub\_side},\ \text{o\_star\_touched},\ \text{r\_used},\ \text{fresh\_mode},\ \text{phase\_class})
\]

- `hub_side`: 현재 endpoint가 hub hexagon 안인가 (bool)
- `o_star_touched`: \(O_*\)가 이미 target된 적 있는가 (bool)
- `r_used`: preparation의 유일한 R(=R1)이 이미 발동했는가 (bool)
- `fresh_mode`: fresh Z3 opening이 한 번이라도 있었는가 (bool)
- `phase_class`: 현재 endpoint의 E-orbit 내 phase (0..4)

구현 orbit id를 쓰지 않고 \(O_*\)에 상대적으로만 정의한다.

## 2. Alphabet — exact action에서 유도

| symbol | exact 조건 | 결정적 사실 |
|---|---|---|
| `E` | zero-charge, 기존 orbit | **반드시 `w2:10`** — weight-3 zero-charge non-fresh는 정의상 R이므로, R도 fresh도 아닌 준비 edge는 유일한 weight-2 move다(`UNIQUE_WEIGHT2_MOVE_THEOREM.md`). **손증명** |
| `F` | zero-charge, new_orbit=True (Z3) | weight-3 |
| `Rh` | R이며 target orbit \(=O_*\) | weight-3 |
| `Rx` | R이며 target orbit \(\ne O_*\) | weight-3 |

§2가 제안한 `E`의 subtype 분할(\(E_0/E_1/E_h\))은 **시도하지
않았다** — `E`가 단일 move로 강제되므로 exact action 차이에서
유도되는 자연스러운 분할이 없다. 데이터에 맞춘 임의 분할은 지시대로
피했다. **미완료.**

## 5. Automaton

depth ceiling 6, root-local, frontier 자연소진:

| ell | \(O_*\) | 상태 수 | 전이 수 | 사용된 symbol | completer-ready 상태 수 |
|---:|---:|---:|---:|---|---:|
| 0 | 120 | 26 | 104 | E, F, Rh, Rx | 18 |
| 4 | 1 | 26 | 97 | E, F, Rh, Rx | 6 |

**주목**: 두 분기의 상태 수가 26으로 동일하다 — `RR_BRANCH_TRANSPORT_MAP.md`
가 다루는 transport 후보의 근거 중 하나다.

## 6. Soundness — 등급 판정

automaton의 각 전이는 **실제 exact preparation edge에서 유도**됐으므로
(`exact_witness_count` 필드에 각 전이를 실현한 exact edge 수가 기록됨)
"허용하는데 실현 불가"인 전이는 구성상 없다. 그러나 **경로 수준에서는
다르다**: \(Q\)는 방문 마스크를 담지 않으므로, automaton이 받아들이는
symbolic word가 exact walk로 실현된다는 보장이 없다.

> **등급: sound over-approximation (necessary-condition automaton).**
> exact automaton이 **아니다.** 실현 조건(literal collision, target
> occupancy, fresh orbit availability, phase provenance, component
> ancestry)은 \(Q\) 밖에 있으며, §11이 요구한 분리
> \(L_{\text{exact}} = L_{\text{automaton}} \cap L_{\text{resource}}\)에서
> \(L_{\text{resource}}\) 쪽에 해당한다 — 그 쪽은 정식화하지 못했다
> (**미완료**).

## 7. Completeness (bounded)

자연소진 범위(ell=4 depth≤8, ell=0 depth≤9)의 same-component
preparation word 14개 전부가 이 automaton에서 accept되고 parse가
유일하다(라운드21 `outputs/rr_grammar_parse_results.json`, 12/12 +
depth-9의 2개). **bounded coverage이며 전역 completeness가 아니다.**

**성공 기준 2 평가: 부분 달성** — automaton은 만들었으나
exact automaton이 아니라 sound over-approximation이다.
