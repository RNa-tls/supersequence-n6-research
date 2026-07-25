# Decorated Markov completeness와 decorated predicate (라운드 20)

산출: `src/verify_rr_decorated_markov.py` -> `outputs/rr_decorated_ablation.json`.
새 completion search 없음.

## 4. Markov completeness — 어디까지 확립됐는가

목표 명제:

> 두 history가 동일한 decorated boundary state에 도달하면 이후 가능한
> 모든 decorated continuation tree가 동일하다.

### 4단계 요구사항별 판정

| 단계 | 판정 | 근거 |
|---|---|---|
| 1. child legality가 decorated state만으로 결정 | **부분(손증명)** | `macro_edges()`와 `area_a_prune_reason()`은 **`ExactState`의 순수 함수**다(코드 정의). 따라서 `\widehat S=(S,\mathcal D)`에 `S`가 들어 있는 한 legality는 결정적이다 — decoration은 여기에 관여하지 않는다. |
| 2. R1/R2 ancestry transport가 child에서 결정적으로 갱신 | **손증명** | `enumerate_decorated`의 갱신 규칙은 전부 `(부모 decoration, 이번 edge의 exact transition)`의 함수다 — 과거 경로를 다시 읽지 않는다(코드로 확인 가능). |
| 3. chaining/same relation이 decoration에서 판정 가능 | **exact decorated quotient** | decoration 단독이 세 relation을 전부 결정한다(2,216 key / 2,234 경계, 충돌 0). §`RR_DECORATED_BOUNDARY_STATE.md` §2. |
| 4. 나머지 literal history는 불필요 | **미완료(이 universe에서는 공허)** | 이 universe에는 **동일 decorated state에 도달하는 서로 다른 history가 하나도 없다**(`stabilizer_size`, `tie_variant_count` 모두 전부 1, 그리고 라운드19가 확인한 대로 2,234개 상태가 각각 1개 경계로만 도달). 비교할 쌍이 없으므로 이 단계는 **경험적으로 검증 불가**. |

### 정직한 결론

> **완전한 Markov-completeness는 증명되지 않았다.** 1-3단계는
> 확립됐지만 4단계는 이 universe에서 **공허**하다 — 반례가 없는
> 것이 아니라 **검사할 쌍 자체가 없다**.
>
> 다만 1단계(legality가 `ExactState`의 순수 함수)와 2단계(decoration
> 갱신이 국소적)는 코드 정의에서 나오는 **손증명**이므로, "decorated
> state가 transition에 대해 닫혀 있다"는 **약한 형태**는 성립한다.
> 강한 형태(동일 decorated state ⟹ 동일 continuation tree)는
> **미완료**로 남긴다.

## 5. 비자명한 chaining predicate

정의 자체(`R1_t = R2_s`)는 결과로 제출하지 않는다. decorated
좌표로 표현한 후보들의 결과(event level, 2,234개 경계):

| 판정 | predicate | tp | fp | fn |
|---|---|---:|---:|---:|
| *(정의, 제외)* | `r1_target == r2_source` | 10 | 0 | 0 |
| **충분** | **`r1_target_hub_distance == r2_source_hub_distance == 1`** | 6 | **0** | 4 |
| 충분 | `hub_completer_orbit == r1_target ∧ R2가 완성 지점에서 발동` | 5 | 0 | 5 |
| 충분 | `R2 source가 hub 완성 지점` | 5 | 0 | 5 |
| **반증됨** | `hub_completer_orbit == r1_target_orbit` 단독 | 6 | **187** | 4 |
| (비교) | `same_component` | 6 | 0 | 4 |

**최선의 비자명 결과**: `r1_target_hub_distance == r2_source_hub_distance == 1`
— R1의 target과 R2의 source가 **둘 다 incidence graph에서 hub에
직접 인접**하면 chaining이 강제된다. 이는 `same_component`와 동일한
혼동행렬(6/0/4)을 가지며, hub 기하만으로 기술된다는 점에서 정의의
재진술이 아니다.

**그러나 필요조건은 아니다**(fn=4). 따라서 **§5가 요구한
"R2 실행 전에 chaining을 예측하는 필요충분조건"은 이번에도 찾지
못했다 — 미완료.** 라운드19와 같은 판정이지만, 충분조건 쪽은
`same_component`(관계 자체)에서 `hub 거리 1`(순수 기하)로
개선됐다.

**추가로 반증된 것**: `hub_completer_orbit == r1_target_orbit`
단독은 fp가 187개로 **명확히 반증**된다 — completer가 R1의 target
orbit을 맞추는 것만으로는 chaining이 되지 않는다(라운드14의
코퍼스 관측을 corpus-free 환경에서 재확인).

## 6. Same-component의 decorated predicate — 성공

union-find 결과를 그대로 읽는 대신 ancestry 좌표로 판정한 결과,
**세 후보 모두 정확한 필요충분조건(IFF)** 이다:

| 판정 | predicate | tp | fp | fn |
|---|---|---:|---:|---:|
| **IFF** | **`r2_meet_is_hub` (LCA 형)** | 6 | **0** | **0** |
| **IFF** | `두 endpoint의 hub 거리가 모두 유한` | 6 | 0 | 0 |
| **IFF** | `양쪽 root가 hub component`(라운드19) | 6 | 0 | 0 |

**§6이 제시한 목표 형태 `LCA(R2_s, R2_t) = H`가 정확히 확인됐다.**

### 그래프 논증 (부분 손증명)

세 predicate가 동치인 이유는 **Unique Hub Hexagon lemma**(라운드12,
손증명)에서 나온다: F≤1 예산 하에서 2회 이상 터치되는 hexagon은
최대 1개(=hub)뿐이므로, incidence graph에서 **두 개 이상의 orbit을
잇는 유일한 합류점이 hub 노드**다. 따라서

- 두 orbit이 같은 component에 있다 ⟺ 둘 다 hub에 연결돼 있다
  (hub가 유일한 합류점이므로) ⟺ 둘을 잇는 최단경로가 hub를 지난다.

**이 논증은 "hub가 유일한 합류점"이라는 부분에서 Unique Hub
Hexagon lemma에 의존하며, 그 lemma는 이미 손증명돼 있다.** 다만
"component가 항상 hub를 포함한다"(즉 hub와 무관한 별도 component가
두 R2 endpoint를 동시에 담을 수 없다)는 부분은 이 universe의
관측(fp=0)으로만 확인했고 일반 증명은 하지 않았다 — 따라서
전체 판정은 **root-local exhaustive + 부분 손증명**으로 표기한다.
