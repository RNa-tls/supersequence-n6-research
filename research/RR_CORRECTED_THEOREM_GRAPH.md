# RR 정리 의존성 그래프 — 정정판 (라운드 17)

산출: 이번 라운드 전체 종합. 새 대규모 탐색 없음.

## 15. 살아남은 손증명 기반 dependency graph

```
F<=1 budget (코드 정의, exact.TARGET_F=1)
 │
 ├─ Unique Hub Hexagon (손증명, Round12)
 │   └─ Hub Touch Count<=2 (손증명, Round13)
 │       └─ Hub Exit Source Lemma [연역 핵심] (손증명, Round15)
 │           ├─ Cost 1 불가능 (손증명, Round17, 완전 320-case 중 80-분기 부분)
 │           │   └─ Cost 2 ⟹ nearest residual (손증명, Round17, 나머지 240-분기)
 │           │       └─ Converse(nearest⟹cost2 | w2:10 abandonment) (손증명, Round17)
 │           └─ (구 주장: "hub-completed⟹Φ=0 전체" — 반증됨, Round17, 이 사슬에서 제외)
 │
 └─ Unique weight-2 move (손증명, Round10, tail_permutations(2) 조합론)
     └─ abandon_ell=4 ⟹ completer 유일(orbit1) (손증명, Round14, 위치-orbit 1:1 대응)
         └─ (ell=4 branch의 1-4단계, RR_ELL4_CHAINING_PROOF.md, 부분 손증명)

── 별도 층: root-local exhaustive(코퍼스 독립, 이번 라운드 신규 확립) ──

Uncapped-local enumerator(root class 1, depth ceiling 6, frontier
empty, 독립 DFS 교차검증 통과)
 ├─ same-component ⟹ ell∈{0,4} (uncapped local exhaustive, Round17)
 └─ ell=0 witness 유일 (uncapped local exhaustive, Round17)

┈┈┈┈┈┈ 점선 층: capped-corpus exact(완전성 미보장, 재확인 필요) ┈┈┈┈┈┈
┊ same-component ⟹ chaining (10/10)                              ┊
┊ chaining ⟹ not unresolved (75/75)                               ┊
┊ forest acyclicity (0/53,054, 0/85,238)                          ┊
┊ delayed completer family (6개 분류)                              ┊
┊ relation lattice (7개 implication)                              ┊
┊ abandonment always w2:10 (4,470/4,470)                          ┊
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

██████ 반증됨(더 이상 참으로 취급하지 말 것) ██████
██ nearest-only completer(전체 ell, 무조건)                    ██
██ hub-completed ⟹ Φ=0(전체, 100%)                             ██
████████████████████████████████████████████████████████████
```

## 그래프를 읽는 법

- **실선(위 두 트리)**: 순수 코드 정의 또는 이번 라운드의 독립
  재검증(cross-checked uncapped local search)에서 나온, corpus
  완전성과 무관하게 성립하는 결과. 다음 라운드가 새 정리를
  쌓는다면 **이 위에 쌓아야 안전하다.**
- **점선 층**: capped corpus에서 반례 없이 관측됐지만, 이번
  라운드가 발견한 corpus 불완전성 때문에 "일반적으로 참"이라고
  아직 말할 수 없는 것들. 반증되지는 않았으나(아직 반례를 못
  찾음), **신뢰도가 실선보다 낮다.**
- **반증된 층**: 명시적으로 거짓임이 확인된 것 — 향후 어떤
  추론의 전제로도 사용하면 안 된다.

## 다음 라운드를 위한 실용적 권고

1. 새 정리를 쌓으려면 실선 층(F≤1 → Unique Hub → Touch Count≤2 →
   Hub Exit Source → Cost 1/2 정리) 또는 uncapped-local-enumerator
   층에서 시작하라.
2. 점선 층의 주장을 인용할 때는 반드시 "capped-corpus 내에서"라는
   단서를 붙이거나, 가능하면 `src/enumerate_rr_uncapped_local.py`
   패턴으로 독립 재검증을 먼저 수행하라.
3. root class 2-5(hub completion 직전, R1/R2 직전 state)는 이번
   라운드에 정의만 하고 구현하지 못했다 — 이들을 실제로 enumerate
   하는 것이 다음 라운드의 가장 직접적인 미완료 과제다.
4. forest lemma의 code-definition 손증명 시도, Φ 7개 반례의 개별
   구조 분석도 미완료로 남아 있다.
