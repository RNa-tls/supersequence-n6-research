# 두 탐색의 scope 화해 — canonicalization / generator / prune (라운드 18)

산출: `src/compare_rr_generators.py` -> `outputs/rr_generator_diff.json`.
새 탐색 없음(H9 witness의 exact replay만).

## 6. Canonicalization 차이 감사 — 차이는 실재하나 무해하다

| | 역사적 generator | 라운드17 enumerator |
|---|---|---|
| 해시 대상 | `exact.canonicalize(state)` (`analyze_f1_n2_defects.py` L484, L501) | **raw** `state.stable_key()` |
| dedup 대상 | canonical | **raw** |
| relabeling group | left-S6 value relabeling | (미적용) |

**결정적 확인**: H9 9개의 raw replay 최종 상태를
`exact.canonicalize()`한 뒤 해시하면 **역사적 코퍼스 해시와 9/9
정확히 일치**한다(raw 해시는 0/9 일치). 즉 **역사적 해시는 내
raw replay가 만든 바로 그 상태의 canonical 형태**이며, 두 파이프라인은
동일한 상태를 서로 다른 대표원으로 부르고 있었을 뿐이다.

역사적 스크립트 자신이 raw replay의 정당성을 문서화하고 있다
(`replay_path_raw_equivariant`의 docstring): *"Canonicalization is
only a left value-relabeling. Every literal tail is a right position
action, so left relabeling commutes with every transition."* — 그래서
legality, resource 좌표, component 관계가 전부 보존되고, 내 raw
replay가 same-component와 ell을 정확히 재현한 것이다.

**H9의 post-R2 상태는 raw 기준 3개, canonical 기준으로도 3개** —
canonicalization이 더 축약하지 않는다.

### 발견된 라벨 오류 (정정 완료)

`rr_uncapped_local_universe.json`의 `unique_canonical_states`는
실제로 raw 상태 수였다. **raw dedup은 완전성에 안전**(left-relabeled
복제본을 중복 확장할 뿐 건너뛰지 않음)하므로 결과는 무효화되지
않으나, 필드명을 **`unique_raw_states`**로 정정하고 `dedup_key`
필드를 추가했다. 독립 DFS 검증기도 함께 갱신해 재실행했고, 5/5
ell 여전히 일치한다.

## 7. Transition generator 차이 감사

| 항목 | 역사적 | 라운드17 |
|---|---|---|
| child generator | `macro.macro_edges()` | **동일** |
| canonicalize 시점 | generate + prune **이후** | 호출 안 함 |
| rotation length / R candidate / abandonment candidate 생성 | `macro_edges()`가 전담 | **동일** |

H9 witness들의 모든 중간 상태에서 raw child-label 집합과
canonicalized child-label 집합을 exact diff한 결과 **불일치 0건** —
left relabeling이 어떤 `(rot^ell; joint)` 라벨의 legality도 바꾸지
않는다(§6의 commute 논증과 정확히 부합).

**판정: `GENERATOR_OMISSION` 해당 없음.**

## 8. Prune 차이 감사

| prune | 적용 함수 | 역사적 | 라운드17 | H9를 제거하는가 |
|---|---|:---:|:---:|:---:|
| 전체 Area-A 조건 | `macro.area_a_prune_reason(state, macro.AREA_A)` | ✓ | ✓ | **아니오(0/9)** |

두 경로가 **동일한 함수, 동일한 config(`macro.AREA_A`)**를 쓴다.
H9 9개를 현재 prune으로 전 단계 재검사한 결과 **탈락 0건**.

**판정: `PRUNE_MISMATCH` 해당 없음.**

## 종합 판정

> 세 축(canonicalization, generator, prune) **어디에도 버그나
> 누락이 없다.** 유일한 실질적 차이는 "역사적 쪽은
> canonicalize하고 라운드17 쪽은 안 한다"는 것이며, 이는 해시
> 동일성과 dedup 입도(raw는 과다확장, 과소확장 아님)에만 영향을
> 주고 도달가능성이나 legality에는 영향을 주지 않는다.
>
> 따라서 **ell=4의 9-vs-5 격차는 §6-8 중 어느 것으로도 설명되지
> 않으며**, 그 원인은 `RR_ELL4_DISCREPANCY_AUDIT.md`가 확정한
> **계수 단위(word vs post-R2 state) + depth scope** 차이다.

**증명 등급: exact replay** (H9 9개를 세 축 전부에서 현재 엔진으로
재유도).
