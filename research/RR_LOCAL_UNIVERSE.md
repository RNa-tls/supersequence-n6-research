# RR local root space 정의 (라운드 17)

산출: `src/enumerate_rr_uncapped_local.py` -> `outputs/rr_uncapped_local_universe.json`.
새 대규모 탐색 없음.

## 3. Root class 후보와 측정

| root class | 정의 | 이번 라운드 구현 여부 | 상태 수(depth ceiling 6) | 자연소진 가능? |
|---|---|:---:|---:|:---:|
| 1. abandonment 직후 state | hex0의 유일한 abandonment 사건(`w2:10`) 직후, ell=0..4 각각 | **구현됨** | 3,657~3,858(ell별) | 예(ceiling 있을 때만; ceiling 없이는 590초 내 미종료) |
| 2. hub first-touch 직후 state | hex0가 처음 터치되는 시점 — 이는 사실상 `t=0`(초기 상태) 자체이므로 별도 root로서 의미가 약함 | 미구현(개념적으로만 root class 1과 동일시됨) | — | — |
| 3. hub completion 직전 state | hex0가 두 번째로 터치되기 바로 전 상태 — root class 1의 하위 노드 집합(고정된 단일 root가 아니라, class 1 탐색 도중 발견되는 다수의 상태) | 미구현(별도 enumerator 없음, class 1 결과에서 파생 가능) | — | — |
| 4. R1 직전 state | R1이 발동하기 바로 전 — word마다 다른 위치이므로 "하나의 root"가 아니라 root class 1의 탐색 트리 안 여러 지점 | 미구현 | — | — |
| 5. R2 직전 state | 위와 동일한 이유로 다중 지점 | 미구현 | — | — |

**정직한 평가**: 원래 과제가 요청한 5개 root class 중, **명확히
독립적인 "root"로서 의미가 있는 것은 class 1(abandonment 직후)
뿐이다.** class 2는 class 1의 시작점과 사실상 동일(hex0의 첫
터치는 항상 `t=0`), class 3-5는 "root"가 아니라 class 1의 탐색
트리 내부에서 발견되는 **다수의 중간 노드 집합**이다 — 이들을
별도 root로 잡으려면 "어떤 특정 R1/R2 배치를 고정할 것인가"라는
추가 선택이 필요한데, 이는 사실상 class 1의 부분집합을 다시
나열하는 것과 같다. **이번 라운드는 class 1만 구현했고, 2-5는
개념적으로만 논의하고 별도 enumerator를 만들지 않았다 — 미완료로
정직하게 남긴다.**

## 측정치 (root class 1)

| ell | expanded | unique **raw** states | duplicate | frontier_empty | max_depth | RR-final | same-component |
|---:|---:|---:|---:|:---:|---:|---:|---:|
| 0 | 3,814 | 3,814 | (아래 참고) | True | 6 | 455 | 1 |
| 1 | 3,657 | 3,657 | | True | 6 | 415 | 0 |
| 2 | 3,858 | 3,858 | | True | 6 | 464 | 0 |
| 3 | 3,840 | 3,840 | | True | 6 | 450 | 0 |
| 4 | 3,834 | 3,834 | | True | 6 | 450 | 5 |

(정확한 `duplicate_count`, `terminal_reasons`는
`outputs/rr_uncapped_local_universe.json`에 전체 기록됨.)

## Outside-corpus state 포함 여부

**예** — 이 local universe는 역사적 capped corpus에 전혀
의존하지 않고 `exact.extend()`/`macro.area_a_prune_reason()`만으로
새로 계산됐으므로, capped corpus 밖에 있던 legal state(라운드16이
발견한 non-nearest completer 등)를 자동으로 포함한다. 실제로
`hub_completer_orbit_distribution`이 capped corpus의 "nearest만"과
다르게 5개 orbit 전부를 보여주는 것이 그 직접 증거다.

## Canonical quotient

이번 구현은 `state.stable_key()`(리터럴 상태, `canonicalize()`
없음)만 사용한다 — S6 relabeling 대칭을 quotient하지 않았으므로,
표에 나온 상태 수는 **canonical(대칭 축소) 개수가 아니라 리터럴
개수**다. Canonical quotient를 적용하면 이 수치들은 더 작아질
것이나, 이번 라운드는 그 축소를 시도하지 않았다 — 미완료.

## Exhaustive certificate 크기

`outputs/rr_uncapped_local_universe.json` 파일 크기와 내용은
root당 약 3,600~3,900개 상태의 parent-implicit(터미널 사유 집계
방식) 기록이다 — 개별 parent pointer 전체를 파일에 저장하지는
않았다(용량 문제로 집계 통계만 저장, 개별 상태는 재생 가능하도록
알고리즘은 결정적이나 파일 자체에 전체 트리를 덤프하지는 않음 —
필요시 스크립트 재실행으로 정확히 재현 가능, 이는 "deterministic
replay" 조건을 만족하지만 "저장된 트리"는 아니다).

## 목표 평가

> "capped global corpus 대신 작지만 완전한 local universe를
> 얻는다"는 목표는 **root class 1에 대해서만 달성됐다.** state
> space 크기(~3,600-3,900, depth ceiling 6)는 실제로 작고
> tractable했다 — 다만 "작다"는 것은 ceiling을 선언했을 때만
> 참이라는 것을 `RR_EXHAUSTIVENESS_STANDARD.md`가 별도로 명시한다.
