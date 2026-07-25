# "완전 탐색(exhaustive)"의 정확한 정의 (라운드 17)

산출: `src/enumerate_rr_uncapped_local.py`,
`src/verify_rr_exhaustive_certificate.py`의 설계와 실행 결과. 새
대규모 탐색 없음.

## 2. 용어 정식화

### 필수 조건 (앞으로 "exhaustive"를 쓰려면 전부 만족해야 함)

1. **root set 완전성**: root class가 정확히 정의되고, 그 class에
   속하는 모든 root가 실제로 탐색됐음을 명시.
2. **transition generator 완전성**: 매 상태에서 시도하는 move
   집합이 이 모델의 전체 move 집합(`exact.ALL_MOVES`)과 일치함을
   증명(또는 `macro.macro_edges()` 같은 기존에 검증된 generator를
   그대로 재사용).
3. **no node/edge/time cap**: 탐색 종료 조건이 "frontier가
   비었다" 하나뿐이어야 한다 — node cap, edge cap, timeout이
   종료 조건이면 그 결과는 exhaustive가 아니다.
4. **frontier empty**: 실행 로그에 `frontier_empty: true`가
   명시적으로 기록되어야 한다.
5. **canonicalization soundness**: 중복 제거에 쓰는 key(이번
   라운드는 `state.stable_key()`, canonicalize() 없이 리터럴)가
   실제로 서로 다른 상태를 같다고 잘못 합치지 않음을 별도로
   확인(간단한 해시 충돌 부재 확인 또는 구조적 논증).
6. **prune soundness**: legality 판정 함수(`area_a_prune_reason`)가
   실제 legal 여부와 정확히 일치함을(과거에 이미 증명된 necessary
   condition 함수임을) 명시.
7. **deterministic replay**: 저장된 parent pointer로부터 root부터
   해당 상태까지 재생 가능해야 한다.
8. **certificate 생성**: root count, expanded count, generated
   edges, unique canonical states, duplicate count, frontier empty,
   max depth, engine SHA-256를 전부 출력.
9. **independent verifier 통과**: 구조적으로 다른 순회 방법(이번
   라운드는 역순 DFS)으로 같은 수치가 재현되는지 확인.

### 이번 라운드가 실제로 만족시킨 것

`src/enumerate_rr_uncapped_local.py` + `src/verify_rr_exhaustive_certificate.py`:
1-9 전부 만족(`outputs/rr_uncapped_local_universe.json`,
`outputs/rr_exhaustive_certificate_verification.json` — DFS 재검증
5/5 ell 전부 일치).

## 결정적으로 중요한 발견: depth ceiling 없이는 실제로 tractable하지 않다

**정직하게 보고한다**: `--depth-ceiling` 없이(순수 frontier-empty
종료만으로) 이 로컬 universe를 확장하려 시도했으나, 590초 타임아웃
안에 종료하지 않았다(kill함). 원인은 `max_r_events=2` 제약만으로는
자연 종료가 보장되지 않는다는 것 — R 이벤트를 전혀 안 쓰는
Z2/Z3/J/A2/A3만의 사슬은 `TARGET_P=121`, `TARGET_O=25` 같은 이
프로젝트 전체의 훨씬 큰 예산 한도에 도달할 때까지 계속 자랄 수
있다. 즉 **"depth ceiling 없는 완전 탐색"은 이 근방에서 사실상
원래 전체 문제(N=6 슈퍼퍼뮤테이션 완성 문제)와 비슷한 규모가 되어
tractable하지 않다.**

이는 라운드16이 "state space가 원래 작다"고 서술한 것이
**depth ceiling을 암묵적으로 적용했을 때만 참**이라는 것을
분명히 한다 — 이번 라운드는 이를 명시적으로 선언한
`depth_ceiling` 파라미터로 바꾸고, 매 결과에 `depth_ceiling_applied`
필드로 정직하게 기록한다.

## 용어 분리

| 용어 | 정의 | 이 프로젝트에서의 예 |
|---|---|---|
| corpus replay | 과거에 저장된 탐색 결과를 그대로 재생만 함 | `f1_n2_defect_words.json` 기반 모든 라운드11-16 분석 |
| capped BFS | node/edge cap이 실제로 걸려 종료됨 | Round14의 150,000-node targeted search |
| depth-bounded exhaustive | 명시적 depth ceiling까지는 frontier가 완전히 빈다 | 이번 라운드의 `--depth-ceiling 6` 실행 |
| root-local exhaustive | 하나의 잘 정의된 root(들)로부터, 선언된 depth ceiling까지, cap 없이 frontier가 자연 소진 | `rr_uncapped_local_universe.json` |
| globally exhaustive | depth ceiling 없이 전체 도달 가능 상태공간이 frontier-empty로 끝남 | **이번 라운드에 달성하지 못함**(intractable로 확인) |
| naturally exhausted search | globally exhaustive의 동의어, "자연히 끝났다"는 것을 강조 | 위와 동일, 미달성 |

**결론**: 이 프로젝트가 realistically 주장할 수 있는 최고 등급은
**"root-local exhaustive, 명시적 depth ceiling, 독립 재검증
통과"**다. "globally exhaustive"는 이번 라운드에 시도했고
tractable하지 않음을 확인했다 — 이는 실패가 아니라 정직한 경계
설정이다.
