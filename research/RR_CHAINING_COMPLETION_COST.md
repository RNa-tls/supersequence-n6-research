# Chaining의 completion cost — κ_chain = Φ

산출: `outputs/rr_chain_cost_analysis.json` (전체 4,470개 RR witness,
R2 발동 직후 상태에서 Φ와 orbit slack 계산 — 새 continuation search
없음, 이미 복구된 리터럴 witness의 R2 직후 상태만 평가).

## κ_chain의 유도 — 임의 통계가 아니라 terminal 필요조건에서

이전 라운드들이 이미 증명한 사실: **Φ(S) = 5 + 6·(TARGET_P - S.P) -
(720 - S.visited_count)**는 완주(P=121 달성)를 위한 **필요조건**
`Φ≥0`이 손증명된 potential이며, `Φ(S') = Φ(S) + (ell-5)`라는
monotonicity를 갖는다(매 macro-edge마다 ell<5면 Φ가 감소,
ell=5면 불변). 이는 "**남은 완주 요구량 대비 사용 가능한
chain-호환 capacity**"를 정확히 측정하는 양이다 — `ell=5`(완전
스윕, "낭비 없음")를 계속 쓸 수 있는 한 Φ는 유지되고, 단 한 번이라도
`ell<5`(부분 사용, "낭비")를 쓰면 그만큼 Φ가 소진된다.

> **정의: κ_chain(S) := Φ(S).** 이는 "S 이후로 허용되는 총
> ell-미달 낭비의 합"과 정확히 같다(Φ가 0 밑으로 내려가면 완주
> 불가능, 이미 증명됨).

## R2 직후 κ_chain — 전체 코퍼스, 정확

| 그룹 | n | κ_chain(Φ) 평균 | 범위 | orbit slack 평균 |
|---|---:|---:|---|---:|
| non-chaining | 4,395 | 3.68 | 0–6 | 22.00 |
| chaining, different | 65 | 4.91 | 2–5 | 22.42 |
| **chaining, same** | **10** | **0** | **0–0** | **23.00** |

## 핵심 발견

> **same-component RR 경로(10개 전부)는 R2 직후 정확히 κ_chain=0
> (Φ=0)이다 — 예외 없이.** 이는 Φ≥0이 증명된 하한이므로, 이
> 10개 상태는 **완주 가능성의 절대적 경계선 위**에 있다: 이 시점
> 이후로는 **단 한 번의 ell<5(낭비) 이동도 허용되지 않는다** —
> 즉시 Φ<0이 되어 완주가 **영구적으로 불가능**해진다.

비교하자면 non-chaining(κ_chain 평균 3.68)과 chaining-but-different
(평균 4.91, 오히려 가장 여유롭다)는 same-component보다 훨씬 큰
여유를 갖는다. **"same-component(=hex-0/hub을 통한 orbit0 소비)"
자체가 completion 자원을 크게 갉아먹는다는 뜻은 아니다** —
오히려 이 10개는 **우연히 다른 이유로**(그 특정 word가 택한
회전 길이 이력) Φ=0에 도달했을 뿐, chaining/same 메커니즘 자체가
Φ를 깎는 것은 아니다(Φ는 오직 `ell` 시퀀스에만 의존, 라운드 9의
`J4_COMPONENT_ANALYSIS.md`에서 이미 증명된 "R/Z2 orthogonality"와
정확히 같은 이유). **그러나 결과적으로, same-component 경로는
전부 이 위험한 경계에 몰려 있다는 것은 정확한 사실이다.**

## 정직한 결론

목표로 제시된 형태
`κ_chain = 남은 완주 요구량 - 사용 가능한 chain-호환 capacity`는
**정확히 이미 증명된 Φ와 동일한 양**으로 환원된다 — 이는 새로운
발견이 아니라, chaining/same-component 현상을 **기존에 증명된
capacity 정리에 연결**한 것이다. **새로운 사실은 "same-component
경로가 항상 이 경계에서 발견된다"는 corpus-exact 상관관계
(10/10)이며, 이것이 인과관계(same-component가 Φ=0을 유발한다)인지
단순 상관관계(둘 다 같은 word-길이 예산 제약의 산물)인지는
판정하지 못했다 — **추측 수준으로 표시**.
