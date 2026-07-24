# 초기 hexagon/orbit의 invariant 정식화와 pre-registration axiom 추출

산출: `src/analyze_rr_hex0_ancestry.py`, `src/enumerate_rr_initial_axioms.py`
-> `outputs/rr_ancestry_patterns.json`, `outputs/rr_initial_axiom_ablation.json`.

## 1. "hex 0"의 invariant 정식화

이전 라운드까지 "hex 0"은 구현 인덱스(hexagon_id의 특정 정수값)로만
지칭됐다. 이번 라운드는 이를 좌표 불변적으로 재정의한다.

> **정의(word-origin hexagon)**: 어떤 word가 시작하는 순열 `p_0`가
> 속한 hexagon. `hex_id(p_0)`. **정의(word-origin orbit)**: `p_0`가
> 속한 E-orbit, `E-orbit(p_0)`.

이 project의 raw(비-canonicalize) 재생 관례에서는 `p_0 = IDENTITY`가
고정이므로 word-origin hexagon = `hexagon_id(IDENTITY)` (구현
번호로는 0), word-origin orbit = `E-orbit(IDENTITY)`(구현 번호로도
0)로 **수치상 우연히** 일치하지만, **정의 자체는 `p_0`의 구체적
값과 무관하다** — 어떤 `p_0`에서 시작하든 "그 word가 시작하는
순열이 속한 hexagon/orbit"이라는 관계는 그대로 성립한다.

### 1.1 초기 metadata — 다른 hexagon과 다른 유일한 표식

- **초기 방문 arc**: `initial_state()`가 직접 설정하는 것은 정확히
  1개의 (orbit,phase) 쌍뿐이다 — `hm[hex(p_0)] |= 1<<bit(p_0)`,
  `om[orbit(p_0)] |= 1<<phase(p_0)`. 다른 모든 hexagon/orbit은
  0(완전 미방문)에서 시작한다.
- **초기 endpoint**: `state.p = p_0`.
- **초기 E-orbit relation**: `ORBIT_PHASE[p_0] = (q_0, phase_0)`.
- **초기 component root**: `component_map(initial_state())`은 정확히
  1개의 union을 담고 있다 — `{("q",q_0): ("q",q_0), ("h",hex_0):
  ("q",q_0)}`(또는 그 반대 방향, union 구현에 따라) — **다른 모든
  orbit/hexagon 노드는 이 시점에 union-find 구조에 아예 존재하지
  않는다(등록 자체가 없음).**
- **다른 hexagon과 다른 초기 metadata**: `hex_0`는 이미 1/6 bit가
  set된 채로 시작하는 **유일한** hexagon이다(나머지 119개는 전부
  0/6). `orbit_0`도 이미 1/5 phase가 set된 채로 시작하는 **유일한**
  orbit이다(나머지 143개는 전부 0/5).
- **canonicalization 이후에도 보존되는 invariant 표현**: `left_relabel`이
  right-action(SIGMA, E) 궤도 구조에 자기동형사상을 유도한다는 사실
  (라운드 11 §1.1에서 손증명, 코드 주석 "commutes with every right
  action"에 근거)에 의해, **"어떤 hexagon/orbit이 t=0부터
  사전등록되어 있는가"라는 관계 자체**(구체적 번호가 아니라)는
  canonicalize 여부와 무관하게 보존된다 — canonicalize는 그 번호를
  재라벨링할 뿐, "유일하게 사전등록된 노드가 존재한다"는 사실
  자체를 없애거나 만들지 않는다.

## 2. Pre-registration axiom 추출 — ablation

`initial_state()`가 "일반 fresh state"(예: word 중간의 아무 상태)와
다른 조건을 열거하고, 하나씩 제거했을 때 목표 정리가 유지되는지
검사했다(`enumerate_rr_initial_axioms.py`).

| 조건 | 이 조건만으로 충분한가(단독 axiom) | 판정 |
|---|---|---|
| 이미 touched로 등록됨(orbit_masks 비트 1개 set) | 아니오 | M0(라운드 11 countermodel)가 이미 "어떤 orbit이 hexX를 통해 등록됨"이라는 조건을 만족하면서도 same+non-chaining을 만든다 — **단독으로는 불충분** |
| component root가 존재함 | 아니오 | 위와 동일한 이유로 불충분 |
| parent pointer가 없음(자기 자신이 root) | 아니오 | 그래프 수준 성질일 뿐, ordering 정보가 없음 |
| 특정 phase가 이미 점유됨 | 아니오 | 위와 동일 |
| union-find node가 미리 생성됨 | 아니오 | 위와 동일 |
| **"hub hexagon은 최대 1개"**(F<=1에서 연역적으로 증명됨, §3 `RR_ANCESTRY_PROOF.md`) | **아니오, 여전히 불충분** | `enumerate_rr_initial_axioms.py`의 M1 — 이 axiom을 추가해도 countermodel이 **생존**한다(M0가 이미 hub 1개만 사용하므로) |
| **"R1이 hub의 두 번째 접촉 사건이어야 한다"**(순서/ancestry 공리) | **예, 충분** | M2 — 이 axiom을 추가하면 countermodel이 **제거**된다(`countermodel_survives: false`) |

### 최소 axiom (달성됨)

> **Distinguished initial hexagon은 component ancestry에서 유일한
> pre-existing root를 제공한다** — 이것만으로는 부족하다. 완전한
> 최소 axiom은: **"hub hexagon(존재한다면 word 전체에서 유일하게
> 2회 이상 접촉되는 hexagon)의 두 번째 접촉 사건은 반드시 R1(첫
> 번째 charged R event) 자신이어야 한다"**(제3의 무관한 사건이
> hub를 완성해서는 안 된다). 이 axiom을 그래프 모델에 추가하면
> abstract countermodel이 제거된다(`M2_plus_R1_is_hub_completer`,
> `countermodel_survives: false`, exact 검증됨).

**정직한 한계**: 이 axiom 자체가 exact permutation model에서
**일반적으로**(임의 길이의 word에 대해) 증명됐는가? **아니오** —
`RR_ANCESTRY_PROOF.md` §6이 보이듯, 4,470개 전체(depth<=6로 제한된
코퍼스)에서는 **예외 없이** 성립하지만(10/10 same-component
witness에서 hub의 두 번째 접촉이 정확히 R1), 이것이 depth<=6이라는
코퍼스 경계의 artifact인지, 일반적으로 항상 성립하는지는 이번
라운드에서 결정하지 못했다 — **necessary axiom(이 코퍼스에서
확인됨), 그러나 일반 손증명은 미완료**로 표시한다.
