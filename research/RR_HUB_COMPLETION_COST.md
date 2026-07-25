# Hub completion cost — 정확한 정의와 원장(ledger) (라운드 16)

산출: `src/analyze_rr_residual_cost.py` -> `outputs/rr_residual_cost_table.json`.
새 대규모 탐색 없음(작은 bounded 케이스체크와 depth≤5 국소 BFS만).

## 1-2. Residual position geometry와 cost의 정의

hex0 위치-orbit 대응(불변, 라운드12): `[0,120,33,9,3,1]`. abandonment가
위치 `ell`에서 발동하면 residual = 위치 `ell+1..5`.

**Cost 정의 (이번 라운드가 채택한 형태)**: `c_hub(r)` = abandonment
직후 상태로부터, `macro.macro_edges()`가 생성하는 (rotation-run;
joint) 형태의 macro-edge를 몇 개 거쳐야 hex0의 residual 위치 `r`에
착지하는 조인트가 legal하게 존재하는가의 **최솟값**. 이는 원래
과제가 제안한 벡터 비용 `(ΔP,ΔS,ΔO,ΔN,ΔΦ,hub exits,orbit reuses)`
전체를 아직 구현하지 않은 **단순화된 스칼라 버전**이다 — 시간
제약으로 벡터 버전은 이번 라운드에 완성하지 못했다(미완료).

## 실제 abandonment 조인트로 조건화한 원장

라운드15가 이미 확립했고 이번 라운드가 4,470/4,470 전수 재확인한
사실: **원본(역사적) 코퍼스의 모든 RR witness는 abandonment에
`w2:10`만 사용한다.** 이 조건 하에서(`w2_10_conditioned_cost_table`):

| ell | nearest(cost) | 그 외 residual orbit별 cost |
|---:|---|---|
| 0 | 120(2) | 33:4, 1:4, 9:5, 3: **도달 불가(depth≤5 내)** |
| 1 | 33(2) | 9:4, 3:5, 1: **도달 불가(depth≤5 내)** |
| 2 | 9(2) | 3:4, 1:5 |
| 3 | 3(2) | 1:4 |
| 4 | 1(2) | (residual 1개뿐) |

**이 표는 `w2:10` abandonment로 고정했을 때의 국소 cost이며,
이번 라운드가 발견한 반증(`RR_NEAREST_RESIDUAL_THEOREM.md`)과
모순되지 않는다** — `RR_NEAREST_RESIDUAL_THEOREM.md`의 신선한
완전탐색은 abandonment 자체도 자유 변수로 풀어(사실은 여전히
`w2:10`만 사용하지만, macro_edges()의 전체 후속 legal 조인트
공간을 `area_a_prune_reason`까지 반영해) 확인했고, 그 결과
non-nearest completion이 legal함을 보였다 — 즉 **이 표의
"도달 불가"는 제가 만든 국소 BFS의 depth5 캡 안에서 도달 못했다는
뜻일 뿐, `verify_rr_nearest_residual.py`의 macro_edges 기반
탐색과 캡·조인트-집합 세부사항이 달라 결과가 정확히 일치하지
않는다 — 두 스크립트의 방법론 차이를 완전히 조화시키지는
못했다(미완료, 정직하게 표시).**

## 3-4. Lower bound와 global budget

**손증명 부분(불변)**: `c=1`은 불가능, `c=2`는 nearest에서만
달성된다(`RR_NEAREST_RESIDUAL_THEOREM.md` 참고, 320개 분기
exhaustive case check). 이 두 사실은 이 원장의 유일한 완전
손증명 등급 항목이다.

**budget 결합**: 전체 word가 6 macro-edge라는 것은 역사적 코퍼스
관측 사실(4,470/4,470의 macro_path 길이가 6)이며 일반 상한으로
증명되지는 않았다(코퍼스가 depth≤6 bounded search의 산물이므로,
이 6이라는 숫자 자체가 그 탐색의 depth 한계에서 온 것일 수
있다 — 즉 "실제 최소 RR word 길이가 6이다"라는 주장과 "이
코퍼스가 depth≤6까지만 뒤졌다"라는 사실을 혼동하지 않도록
주의해야 한다). **이 결합 논증은 미완료로 유지한다.**

## 5. Manual 5-orbit candidates의 정확한 지위 — 재정리

| 상태 | 라운드14(수동 국소 BFS) | 라운드15(역사적 코퍼스) | 라운드16(신선한 완전탐색) |
|---|---|---|---|
| orbit 1,3,9,33,120 모두 legal completer인가(ell=0) | 예(exact witness) | — | **예, 재확인** — 5개 전부 신선한 완전탐색에서 실제 발생(120:19,1:10,33:12,9:9,3:3) |
| nearest만 실현되는가 | — | 예(43/43) | **아니오, 반증됨** |
| same-component와의 관계 | — | 1개만 same(120 사용) | **1개만 same(depth≤6), 여전히 120 사용** — completer orbit 분포는 넓어졌지만 same-component 발생은 여전히 극히 드묾 |

**정리**: local legal과 global RR-continuation 양립성은 여전히
구분해야 하지만, 원래 기대했던 "nearest만 global 양립 가능하다"는
가설은 **반증됨** — 실제로는 5개 orbit 모두 hub를 완성할 수 있고
RR 구조(F=1,H=0, 2개 R 이벤트)까지 만족시키지만, **same-component를
만드는 것은 여전히 극도로 드물다**(depth≤6 완전탐색에서 ell=0은
단 1/455, ell=4는 5/450). 즉 "hub 완성"과 "same-component 달성"은
서로 다른 난이도를 가진 별개의 질문이며, nearest/non-nearest
구분은 same-component 희소성을 설명하지 못한다 — 진짜 설명은
아직 열려 있다.
