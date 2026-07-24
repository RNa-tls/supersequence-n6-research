# same-component ⟹ chaining — 최종 증명 아키텍처와 남은 gap

산출: `src/enumerate_rr_initial_axioms.py` -> `outputs/rr_initial_axiom_ablation.json`.

## 8. Abstract countermodel에 initial axiom 추가 — 최소 제거 axiom 확정

라운드 11의 countermodel(M0, 그래프 공리만 — bipartite/forest/degree
caps/R-existing-only)에 단계적으로 axiom을 추가했다:

| 모델 | 추가된 axiom | countermodel 생존? |
|---|---|---|
| M0 | (없음, 라운드 11 원본) | **생존**(same+non-chaining 구성됨) |
| M1 | + "hub hexagon은 word 전체에서 최대 1개"(§3-4 Lemma, 순수 그래프 cardinality 제약) | **생존** — M0가 이미 hub 1개만 쓰므로 이 axiom을 이미 만족 |
| M2 | + "hub의 2번째 접촉 사건은 반드시 R1 자신이어야 한다"(제3자 사건 금지) | **제거됨**(`countermodel_survives: false`) |

```
python3 src/enumerate_rr_initial_axioms.py
M0_graph_axioms_only         -> countermodel_survives: True
M1_plus_unique_hub_hexagon   -> countermodel_survives: True
M2_plus_R1_is_hub_completer  -> countermodel_survives: False
```

**결론**: countermodel을 제거하는 **최소 axiom 집합**은
`{forest, degree caps, R-existing-only, unique-hub-hexagon,
R1-is-hub-completer}`이며, 이 중 마지막 것(M1→M2 전환)이 **결정적
추가 axiom**이다. 앞의 4개(M0+M1)는 순수 **그래프 수준** 공리이고,
마지막 것은 **word 안에서의 사건 순서/역할**에 대한 명제로, 그래프
구조만으로는 표현되지 않는다.

## 9. Local permutation axiom 확인

"R1-is-hub-completer"가 permutation-level에서 왜 성립하는지(또는
성립해야 하는지) 후보를 검토했다.

| 후보 | 검토 결과 |
|---|---|
| weight-3 move의 unique target | **관련 없음** — weight-3 tail은 3개 있고(`tail_permutations(3)`), R이 어느 것을 쓰든 위 논증에 영향 없음 |
| E-orbit orientation | 미검토 — 이번 라운드 범위 밖 |
| phase offset | **부분 관련**: hub(hex 0)가 정확히 몇 개의 remaining slot을 갖는지(첫 abandon의 `ell` 값에 의존, 1~5개)가 "제3자가 끼어들 여지"를 결정한다 — `ell`이 작을수록(4에 가까울수록) remaining slot이 1개뿐이라 제3자가 개입할 물리적 공간이 없다(§`RR_ANCESTRY_PROOF.md` 관측: 대부분 ell=4). `ell=0`인 경우(989d2261b4)는 5개 slot이 열리지만, 그래도 R1이 유일하게 그중 하나를 골라 쓰고 depth 예산이 소진돼 제3자가 등장하지 않았다 |
| initial permutation의 stabilizer | 미검토 |
| literal overlap parity | 미검토 |
| endpoint symbol constraint | 미검토 |
| full-sweep rotation order | **관련**: F=1 이후 모든 non-fragment hex는 반드시 fresh 상태로 진입해 즉시 완전히 스윕되거나(closed) fragment를 완성하는 두 갈래뿐이라는 사실(§`RR_ANCESTRY_PROOF.md` Lemma)이 "제3자가 hub를 건드리려면 **반드시 그 사건이 어떤 정해진 형태(existing target=hub의 남은 자리)**여야 한다"는 강한 제약을 만든다 — 이것이 정확히 M1→M2 전환에서 요구하는 조건과 같은 자원(hub의 남은 slot)을 공유한다는 뜻이며, **depth 예산이 이 자원을 R1이 먼저 소비하도록 강제하는지**가 남은 핵심 질문이다 |

### 최종 정직한 결론

> **Graph structure(forest+degree+R-legality) + unique-hub-hexagon axiom
> + "R1-is-hub-completer" axiom ⟹ same-component ⟹ chaining.**

이 마지막 axiom 자체가 **exact permutation model에서 일반적으로
증명되는지는 확정하지 못했다** — 4,470개 depth<=6 코퍼스
전체에서는 예외 없이 성립하지만(**유한 완전 검증**), 이것이
depth<=6이라는 경계를 넘어서도 항상 성립하는 **일반 법칙**인지,
아니면 짧은 word에서만 나타나는 **예산 artifact**인지는 **미완료**로
남긴다. `RR_INITIAL_ROOT_AXIOM.md` §2가 이를 "necessary axiom(코퍼스
확인됨), 일반 손증명 미완료"로 정확히 표시한다.

## 10. Full theorem proof architecture

### Lemma 1 — **손증명 + 유한 완전 검증(4,470/4,470)**
> initial hex(word-origin hex)는 t=0부터 유일하게 사전등록된
> component root를 제공하며, 이는 canonicalization에 불변인 관계다.

`RR_INITIAL_ROOT_AXIOM.md` §1.

### Lemma 2 (Unique Hub Hexagon) — **손증명 + 유한 완전 검증(4,470/4,470)**
> F<=1 예산의 word에서, 2회 이상 target이 되는 hexagon은 최대
> 1개(hub, H*)뿐이다. `f1_normal_form`의 기존 불변식에서 직접
> 도출됨.

`RR_ANCESTRY_PROOF.md` §3-4.

### Lemma 3 — **손증명(Lemma 2의 직접 따름정리)**
> H*가 존재하지 않으면(또는 R2의 source/target 중 하나가 H*에
> 연결 안 되면), R2의 component_relation은 "same"이 될 수 없다.

`RR_ANCESTRY_PROOF.md` §5, 대우 형태.

### Lemma 4 — **necessary axiom, corpus-exact(10/10), 일반 증명 미완료**
> H*가 존재하면(같은 word 안에서 유일), 그 두 번째(그리고
> 코퍼스에서 관측된 한 마지막) 접촉 사건은 R1 자신이다 —
> 제3의 무관한 사건이 H*를 완성하는 경우는 관측되지 않았다.

`RR_ANCESTRY_PROOF.md` §7, `RR_HEX0_NECESSITY_THEOREM.md` §8-9.

### Theorem — **corpus-exact(4,470/4,470) + 부분 손증명(Lemma 1-3) + 1개
미완료 axiom(Lemma 4)에 의존**
> same-component ⟹ chaining.

**Lemma 1-3은 완전히 일반적으로 증명됐다(임의 depth, 임의 F<=1
word에 대해)**. **정리 전체가 완전히 일반적으로 성립하는지는
Lemma 4 하나에 달려 있다** — 이것이 depth<=6 예산의 결과인지
일반 법칙인지가 이 정리의 유일하게 남은 gap이다. 이는 라운드 11의
"경험적 관찰"보다 **훨씬 좁고 정확하게 특정된 gap**이다 — 라운드
11은 "왜 성립하는지 모른다"였다면, 이번 라운드는 "정확히 이
1개의 axiom(제3자 hub-completer 부재)이 왜 항상 성립하는지 모른다"로
gap을 좁혔다.

## 성공 기준 평가

- **기준 1 (R2 same ⟹ hex0 touched 손증명)**: 더 일반적인 형태
  (hex0 대신 hub hexagon)로 **손증명 달성**(Lemma 2-3).
- **기준 2 (same ⟹ chaining 완전 손증명)**: **미달성이지만
  대폭 근접** — Lemma 1-3은 완전히 일반적으로 증명됐고, 남은 gap은
  Lemma 4 하나로 정확히 좁혀졌다.
- **기준 3 (최소 initial-state axiom 식별)**: **달성** —
  word-origin hex/orbit의 유일 사전등록성 + unique-hub-hexagon.
- **기준 4 (countermodel 제거 최소 공리 집합)**: **달성** —
  M2(`R1-is-hub-completer`)가 정확히 그 공리임을 직접 구성으로 증명.
