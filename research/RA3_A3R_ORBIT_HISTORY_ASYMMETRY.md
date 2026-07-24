# RA3/A3R orbit-history 비대칭 — 전체 저장 corpus의 exact count

산출: 저장된 witness ledger 전체(RA3 300개 전량 재확인, A3R 298개
전량 재확인 — sample이 아니라 이 세션이 이미 복구해 놓은 전체
ledger. 새 continuation search는 수행하지 않았다).

## 결론 먼저

> **A3R(A3가 먼저, R이 나중)에서, R 직전 critical restart가 A3
> 자신의 target orbit을 재사용하는 사례는 저장된 298개 전체 중
> 정확히 0개다. RA3(R이 먼저, A3가 나중)에서는 300개 중 75개가
> 재사용, 143개가 무관, 82개가 critical restart 자체가 없다(인접).**

## 11. 판정

| 질문 | 답 |
|---|---|
| (1) A3가 fresh target을 여는 사건이라 A3R에서는 R 이전 reuse가 구조적으로 불가능한가? | **미결정** — 정성적으로 그럴듯한 메커니즘(아래)은 있지만, 연역적 증명은 얻지 못했다 |
| (2) RA3에서는 R이 먼저 기존 orbit을 재사용한 뒤 A3가 fresh orbit을 열 수 있는가? | **그렇다, corpus로 확인** — RA3의 reuse=75/300은 정확히 이 패턴(R이 먼저 무언가를 열고, critical restart가 그것을 재사용)이다 |
| (3) 이 비대칭이 event order 정의에서 손증명되는가? | **아니오, 미완료** |
| (4) 전체 corpus에서 exact count는? | **RA3: reuse 75, unrelated 143, no_critical 82(총 300, 이 세션이 복구한 전체). A3R: reuse 0, unrelated 200, no_critical 98(총 298, 전체).** |

## 정성적 메커니즘(추측, 미증명)

A3가 먼저 발동하면 F=1이 즉시 성립하고, 그 뒤 critical restart는
`RA3_A3R_ASYMMETRY.md`(더 이전 라운드)의 F-budget/fragment
order-lock 정리에 의해 **fresh hex 착지가 강제된다**(fragment가
아니라면). A3 자신의 target orbit은 방금 막 1개 phase만 touched된
상태이므로, 뒤이은 critical restart가 **같은 orbit의 다른
phase**를 우연히 겨냥할 가능성이 이론적으로는 있다 — 하지만 관측상
0/298이다. **이것이 구조적으로 불가능한지, 아니면 이 프로젝트가
반복 확인해 온 패턴("미관측은 불가능이 아니다" — A2R, ell_A2=2와
동일 패턴)처럼 depth<=6 경계의 아티팩트인지는 판정하지 못했다.**
이 프로젝트의 반복된 교훈에 따라, **"불가능"이라고 단정하지 않고
"corpus exact observation(298/298, 아직 반증되지 않음)"으로만
표시한다.**

## 목표 정리 후보 판정

> "A3R에서 A3와 R 사이의 pre-R orbit reuse는 불가능하다."

**증명 상태: corpus exact observation(298/298 재확인) — 정리로
격상하지 않는다.** 거짓임을 보이는 최소 witness도 찾지 못했다(이번
라운드는 저장된 ledger만 사용했고, A2R/ell_A2=2 사례처럼 더 깊은
탐색이 반례를 낼 가능성을 배제할 수 없다). **양쪽 다 확정하지
못한 채 정직하게 열어 둔다.**

## 성공 기준 (5) 평가

"RA3/A3R orbit-history 비대칭의 손증명"은 **미달성**이다 — 정확한
(표본이 아닌 전체) corpus 관측(298/298 대 75/300)은 확보했으나,
연역적 증명에는 이르지 못했다.
