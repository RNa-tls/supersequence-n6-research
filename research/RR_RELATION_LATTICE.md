# RR relation implication lattice — 완전판

산출: `src/verify_rr_chaining_proof.py` -> `outputs/rr_relation_lattice.json`
(전체 4,470개 코퍼스, 새 탐색 없음, 기존 리터럴 witness 재사용).

## 11. Implication 표 — 전체 코퍼스 정확 검증

| Implication | 전제 개수 | 성립 개수 | 판정 |
|---|---:|---:|---|
| same-component ⟹ chaining | 10 | 10 | **HOLDS(유한 완전 검증, 반례 0)** |
| chaining ⟹ same-component | 75 | 10 | **반증됨**(65개 반례 — chaining인데 different) |
| chaining ⟹ relation ≠ unresolved | 75 | 75 | **HOLDS(유한 완전 검증)** — 라운드 9의 "chaining ⟹ resolved" 정리 재확인 |
| hub touched(존재) ⟹ chaining | 526 | 15 | **반증됨**(511개 반례) — hub 존재만으로는 chaining을 전혀 함의하지 않음 |
| same target orbit(R1,R2 동일 target) ⟹ chaining | 1,200 | 0 | **반증됨**(1,200개 전부 반례) — `same_target`은 오히려 chaining과 **배타적**(§ 아래) |
| (hub 존재 ∧ chaining) ⟹ completer orbit = R1 target orbit | 15 | 10 | **반증됨**(5개 반례, 모두 relation='different') — hub가 R1/R2와 **무관하게** word 다른 곳에 존재할 수 있고, 그 경우 chaining은 hub와 독립적으로 성립할 수 있다 |
| (hub 존재 ∧ completer orbit=R1 target orbit) ⟹ same | 426 | 10 | **반증됨**(416개 반례) — `RR_HUB_SECOND_TOUCH_THEOREM.md`에서 이미 확인: orbit 일치가 충분조건은 아니다(R2가 실제로 그 위치를 source로 삼아야 함) |

## 최소 반례 — same_target과 chaining의 배타성

`same_target ⟹ chaining`은 1,200/1,200 전부 반례다 — 사실
**`same_target`과 `chaining`은 이 코퍼스에서 완전히 배타적**(교집합
0개, 라운드 14 §10 데이터 재확인)이다. 최소 반례:
`same_target=True`인 첫 번째 정렬 witness는 `chaining=False`이며,
이는 구조적으로 자명하다 — `same_target`은 "R1과 R2가 같은
orbit을 target한다"는 것이고 `chaining`은 "R1의 target이 R2의
**source**"라는 것이므로, 만약 두 orbit이 애초에 다르다면(대부분의
경우) 이 둘은 서로 다른 조건을 말한다. 왜 **교집합이 정확히
0**인지(단순히 드문 것이 아니라 전무함)는 이번 라운드에서 완전히
규명하지 못했다 — **추측**: R2가 R1의 target을 source로도 target으로도
동시에 재사용하려면 그 orbit의 서로 다른 두 phase를 R2 자신의
source/target 양쪽에 써야 하는데, 이는 R2 한 사건의 (source,target)
쌍이 서로 다른 hex를 거쳐야 하는 제약과 충돌할 수 있다 — 일반
증명은 미완료.

## 목표 정리의 정확한 형태 재확인

**"hub 존재 + chaining이 항상 completer=R1 target을 강제한다"는
것은 거짓**이지만, 이는 원래 §9(H0-Necessity류) 정리를 반증하지
않는다 — 그 정리가 요구하는 조건은 훨씬 좁다:
**`same-component`(hub가 R2 자신과 직접 연결된 경우) 자체는 여전히
10/10 완전 검증으로 성립**한다. 위 표의 "반증됨" 항목들은 전부
**더 넓은(그리고 원래 요구되지 않았던) 일반화**를 테스트한
것이며, 정확한 핵심 정리(`same-component ⟹ chaining`)는 이
테스트들에 의해 전혀 흔들리지 않는다 — 오히려 정확히 어디까지가
참이고 어디부터 거짓인지 이번 라운드에서 훨씬 명확해졌다.

## Lattice 요약 다이어그램(텍스트)

```
same-component  ──(HOLDS, 10/10)──▶  chaining
     ▲                                   │
     │ (반증, 65개 반례)                  │ (HOLDS, 75/75)
     └───────────────────────────  relation ≠ unresolved

hub 존재            (반증, 511개 반례)      chaining
same target orbit   (반증, 1200개 반례)     chaining
(hub∧chaining)      (반증, 5개 반례)        completer=R1 target
(hub∧completer=R1target) (반증, 416개 반례)  same
```

**유일하게 무결한 두 화살표**: `same-component ⟹ chaining`(핵심
목표 정리, 유한 완전 검증)과 `chaining ⟹ relation≠unresolved`(라운드
9의 기존 정리). 나머지 모든 "더 강한" 또는 "더 넓은" 변형은 전부
반증됐다 — 이는 원래 정리가 **최대한 타이트한(더 이상 일반화할 수
없는) 형태**임을 보여주는 결과로 해석할 수 있다.
