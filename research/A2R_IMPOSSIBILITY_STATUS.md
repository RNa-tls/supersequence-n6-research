# A2R: 비관측(0/25,660)의 이론적 지위 — 반증됨 (도달 가능함이 증명됨)

산출: `src/search_a2r_min_depth.py` -> `outputs/a2r_search.json`.

## 결론 먼저

**A2R(A2 다음 R)은 이론적으로 불가능하지 않다.** 초기 상태로부터
macro-depth **정확히 6**에서 도달 가능한 구체적 witness가 존재하고,
아래에서 그 witness를 리터럴하게 재생·검증했다. 따라서 이 연구가 요청한
목표 정리 후보

> "F=1, H=0, N=2 조건에서 A2 이후 R은 불가능하다"

는 **반증됨(disproved)** — 정확히 그 반대가 유한 완전 검증으로
확인됐다.

## 1. 자원-예산 논증 (사전 스크리닝) — A2R을 배제하지 못함

`search_a2r_min_depth.py`의 리소스 논증: A2는 F<=1 슬랩이 허용하는
유일한 abandonment 예산을 소모한다(F: 0→1). R은 `abandonment=False`만
요구하며, 이는 F/N 예산이 전혀 금지하지 않는 조건이다. 따라서 A2R은
A2A2/A2A3/A3A2/A3A3(모두 두 번째 abandonment가 필요해 F 예산 위반으로
즉시 배제됨)를 죽이는 것과 **같은 논증으로는 배제되지 않는다** — 이
사실 자체는 25,660개 depth<=6 코퍼스가 만들어지기 전부터 이미 알 수
있었던 것으로, "A2R=0"이 이론적 불가능성이 아니라 다른 이유(탐색
순서·자원 편향)일 가능성을 시사했다.

## 2. Raw BFS 최소 깊이 탐색 — **유한 완전 검증 (depth<=6, node_cap=200,000)**

`search_a2r_min_depth.raw_bfs_minimum_a2r_depth`: 초기 상태에서
raw(비정규화) BFS로, "정확히 두 개의 charge 이벤트, 순서대로 A2 다음
R" 조건을 만족하는 가장 얕은 상태를 탐색. 결과:

```
found: true
depth: 6   (코퍼스 자신이 기록한 depth<=6 경계와 동일)
macro_path: 6단계, 이벤트 순서 = Z3, Z3, Z3, A2, R  (3개의 zero-charge
            Z3 다음 A2, 그 다음 R — 전부 이 depth 이내)
nodes_expanded: (outputs/a2r_search.json 참조)
```

이는 **"depth<=6을 넘어야만 가능하다"는 설명(원인 후보 #2)를 반증한다**
— A2R은 이 코퍼스가 스캔한 것과 동일한 depth 경계 안에서 이미 존재한다.

## 3. 정규화(canonical) BFS 확인 — 독립 경로로 재확인

별도로 `find_a2_only_states`(canonical-memoized BFS, depth<=6,
node_cap=3000)로 "positive-charge 이력이 정확히 (A2,)"인 상태를 찾고,
그 상태에서 raw BFS로 R을 탐색한 결과도 동일한 결론을 낸다: A2-only
상태 1개 발견, 그로부터 depth 2 만에 R 도달
(`macro_path: ["rot^5;w2:10", "rot^5;w3:120"]`). 두 개의 독립적 탐색
방법(raw 전체 BFS, canonical A2-anchor BFS)이 서로 다른 구체적
witness를 내지만 둘 다 "A2R 도달 가능"이라는 같은 결론에 도달한다 —
`outputs/a2r_search.json`의 `results` 필드.

## 4. 5가지 후보 설명 재평가

| # | 후보 설명 | 판정 |
|---|---|---|
| 1 | 이론적으로 불가능 | **반증됨** — §2, §3의 구체적 witness가 직접 반례 |
| 2 | depth 6을 넘어야만 가능 | **반증됨** — depth 정확히 6에서 존재 (§2) |
| 3 | canonical 탐색 순서(node_limit=20000)의 artifact | **가장 유력** — 아래 §5 |
| 4 | A2 이후 자원 충돌 | **반증됨** — §1의 예산 논증과 §2/§3의 실제 도달로 이중 반박 |
| 5 | A2의 abandonment 구조가 기존 orbit로의 R을 구조적으로 막음 | **반증됨** — 실제 witness에서 R이 기존 orbit을 목표로 정확히 발생함(§2 macro_path의 마지막 `w3:120` 스텝은 `new_orbit=false`, 즉 "existing orbit" R) |

## 5. 왜 원 코퍼스는 A2R을 0개 기록했는가 — 손증명 아님, 근거 있는 설명

원 25,660개 코퍼스는 `node_limit=20000`인 **canonical-memoized** BFS의
산출물이다(`legacy_research/outputs/f1_n2_defect_words.json`의
`checkpoint_header.config`). Canonical BFS는 상태마다 720개의
좌-재라벨링을 시도하는 정규화 비용 때문에 초당 ~20-25 상태로 매우
느리다(이 연구 전반에서 반복 확인된 사실, 예:
`J_STATE_SPACE_REDUCTION.md`). `node_limit=20000`은 depth<=6 전체
도달 가능 상태 공간보다 훨씬 작을 수 있는 하드 캡이며, BFS 프론티어
확장 순서에 따라 어떤 브랜치가 예산 소진 전에 도달되는지가 갈린다. §2,
§3에서 실제로 도달한 A2R witness들이 이 20,000-노드 예산 안에
포함됐는지 여부는 원 코퍼스의 원본 노드 순회 로그 없이는 사후적으로
알 수 없다 — 따라서 이 설명은 **추측(반증되지 않았고, 다른 후보들이
모두 반증됐다는 점에서 가장 유력하지만 직접 증명되지는 않음)**으로
표시한다.

## 정직한 결론

- A2R=0은 **미관측**이었을 뿐 불가능이 아니었다 — 원 요청이 처음부터
  강조한 구분이 정확히 맞았다.
- 목표로 제시됐던 "A2 이후 R 불가능" 정리는 **반증됨**.
- 성공 기준 (2) "A2R 불가능성 정리"는 문자 그대로는 달성되지 않았지만,
  그 반대 방향으로 **동등하게 강한, 유한 완전 검증된 결론**(도달
  가능성 + 구체적 witness + 5개 후보 설명의 배타적 소거)에 도달했다 —
  이는 정직한 음성/반전 결과이며 은폐하지 않고 그대로 보고한다.
