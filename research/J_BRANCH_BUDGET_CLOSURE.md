# J-branch budget 분석 최종 판정

## 최종 탐색 결과 — **제한 실험 (완전 탐색 아님)**

`src/search_j_budget_families.py`로 74개 생존 seed 전체에 depth<=15,
seed당 edge budget ~67,567(전체 500만, 체크포인트 없음, 단발 실행,
241초 소요)를 적용했다.

| 단계 | 실패(같은 Φ 메커니즘) | 미해결 | 전체 |
|---|---:|---:|---:|
| depth<=6, edge cap 3,000(raw 프로파일링) | 45 | 185 | 230 |
| + depth<=6, edge cap 20,000(최소 실패 경로 탐색) | 156 | 74 | 230 |
| + depth<=15, seed당 edge cap ~67,567 | **221** | **9** | 230 |

**221/230(96%)이 정확히 같은 메커니즘**(`SHORTFALL_BUDGET_THEOREM.md`의
Φ 붕괴, 짧은 rotation run)**으로 capacity 실패에 도달함을 실제로
확인했다.** 남은 9개는 depth 8·seed당 67,568 edge에서 cap에 걸려
미해결로 남았다(완주도, 실패도 발견 못함) — 그중 3개는 Φ=0(가장
좁은, 산술적으로 유일한 charge-word를 가진) 상태다.

## 후보 정리 T1–T5 판정

**T1. "모든 J 상태에서 필요한 최소 future shortfall은 현재 Φ보다
크다."** → **반증됨(일반적으로).** `SHORTFALL_BUDGET_THEOREM.md` §3이
보이듯, 순수 counting 하에서는 `m_LB=0`이 타이트하다 — 즉 이 명제는
산술만으로는 성립할 수 없다(그랬다면 애초에 어떤 J 상태도 §2의 최소
1개 charge-word조차 갖지 못했을 것이다, 모순). T1은 기하적 형태로
다시 쓰이지 않는 한 **거짓**이다.

**T2. "Φ budget을 만족하는 모든 future word는 특정 zero-charge
skeleton family에 속한다."** → **유한 완전 검증(약한 의미로).**
`SHORTFALL_BUDGET_THEOREM.md` §5가 정확히 이를 보인다 — 모든 budget
값(0,1,2,4,5)에서 family 수는 유한(1,2,4,12,19)하다. 다만 "특정
하나의" family가 아니라 "유한 개의" family들이다 — 여러 개 중 하나에
속한다는 뜻이면 참, 유일하다는 뜻이면 거짓(Φ=4,5인 상태는 12개/19개
family 중 하나).

**T3. "해당 zero-charge skeleton family는 incidence/orbit 재사용으로
불가능하다."** → **미결정.** `ZERO_CHARGE_SKELETON.md` §3,§5에서 이미
밝혔듯, orbit/incidence 재사용 여부는 이번에 계산하지 않았다 — Φ의
정의에 아예 등장하지 않는 정보이기 때문이다.

**T4. "J-branch는 유한 개의 charge-word subcase로 완전히 환원된다."**
→ **유한 완전 검증(산술 차원에서).** budget별 charge-word family
카탈로그(1~19개)로 완전히 환원됐다 — 이것이 이번 작업의 핵심
성과다. 다만 이 환원은 **산술 차원**에서만 완전하다; 각 charge-word가
실제로 기하적으로(충돌 없이) 실현 가능한지는 별개 질문으로 남는다
(§ZERO_CHARGE_SKELETON.md §5).

**T5. "살아남은 74개 exact state가 family-local exhaustive search로
전부 닫힌다."** → **미결정, 그러나 221/230(96%)까지 강한 bounded
증거.** 74개 중 65개가 이번 확장 탐색에서 추가로 실패를 보였다 — 9개만
남았다. 이는 **완전 탐색이 아니라 제한 실험**이므로 "전부 닫혔다"고는
쓰지 않는다.

## 종합 결론

이번 작업의 성공 기준(무한한 미래를 유한 charge-word family로 환원)은
**달성됐다** — `SHORTFALL_BUDGET_THEOREM.md`의 유한 카탈로그가 그
증명이다. "살아남은 74개를 실제로 닫을 수 있는 subcase로 환원"하는
목표는 **부분적으로** 달성됐다: 234개 중 221개(96%)가 실제로 같은
메커니즘으로 실패함을 실측했고, 남은 9개(그중 3개는 산술적으로 가장
좁은 Φ=0 상태)만이 이 bounded 실험의 지평 안에서 미해결이다.

**J-branch 전체가 닫혔다고는 쓰지 않는다.** 남은 9개, 그리고 221개의
"실패"가 진짜 완전한 walk의 불가능성을 증명하는지(부분 branch 실패가
전체 seed의 불가능성을 함의하려면 그 seed의 **모든** branch가 실패해야
하는데, 이번 탐색은 그것까지 보이지 못했다 — 각 seed에서 하나의
실패 경로를 찾은 것이지, 그 seed의 모든 경로가 실패한다는 것을 보인
게 아니다)는 여전히 열려 있다. 이 구분은 중요하다: **"이 seed에서
어떤 branch가 capacity 실패에 도달한다"와 "이 seed의 모든 branch가
결국 실패한다(=이 seed 자체가 완주 불가능하다)"는 다른 명제다.** 이번
작업은 전자만 확인했다.
