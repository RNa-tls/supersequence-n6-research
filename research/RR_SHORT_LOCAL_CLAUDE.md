# fragment-local short 기회로 일반 예외를 교체 — 186개 폐쇄, 그리고 short 계열은 소진됐다

**작성:** Claude (독립 검증 트랙)
**라운드:** 92
**재현:** `src/probe_rr_short_local.py` (`build`, `control`, `sweep`)
**JSON:** `outputs/rr_short_local_claude.json`, `outputs/rr_short_local_ledger.jsonl.gz`
**기준선:** 6,582 → **6,396**
**범위:** Q2 / Area-A. 보존된 아카이브와 리터럴 체크포인트만 사용. frontier 재구성 없음,
무제한 continuation 탐색 없음, M2 전수 스윕 재개 없음.

---

## 결과 요약

> **새 폐쇄 186, UNKNOWN 0, 33초. 잔여 6,582 → 6,396.**
>
> 라운드 88/90 의 결합 모델은 short 예외를 `Gshort ∖ G5` 의 **아무 edge** 로 허용했다.
> 라운드 91 의 SHORT-PASS LOCALITY(독립 확인)에 따르면 그 자리는 fragment 하나뿐이다.
> 상태별로 실제 가능한 opening 집합 `SHORT_LOCAL(s)` 를 만들어 보니 **source port 는 정확히
> 1개, fresh target 궤도는 1~2개**뿐이다 — 일반 모델이 허용하던 궤도 수십 개와 비교된다.
>
> 폐쇄 186개는 **전부** "일반 모델의 short target 이 `SHORT_LOCAL` 밖" 이라는 한 가지
> 이유(§7 분류 E)에서 나왔다.
>
> 그리고 생존자 진단이 이 계열의 끝을 알려준다: **6,396 생존자 중 short 기회를 쓰는 통과
> cover 를 가진 상태는 0개**다. 남은 상태는 short edge 없이 전부 `G5` 로 생성 가능한 cover 를
> 갖는다. **short-edge 계열은 폐쇄 지렛대로 소진됐다.**

---

## 1. `SHORT_LOCAL(s)` 구성 (§1)

예산 0 이면 공집합. 예산 1 이면 fragment 의 **유일한 미방문 run** 시작 칸에서
`ℓ = 5 − c_f` 회전 후 4개 joint 로 갈 수 있는 target 을 전부 담는다. 과대근사를 유지하기
위해 (a) blocked-w2 보조정리로 배제 가능한 `w2` joint 도 남기고, (b) 착지 위상이 정해져도
후보를 좁히지 않으며, (c) 미방문 run 이 여러 개면 전부 진입점으로 넣는다.

**Codex 의 경고를 반영했다.** `c_f = 5` 면 `ℓ = 0` 이다(1,487개 상태). "매크로 진입 마스크는
항상 부분적" 으로 강화하지 않았고, 시간 상대적 locality 진술만 썼다.

기록 항목: fragment 육각형 · source 궤도 · source port · `ℓ` · joint 종류 · target 궤도 ·
착지 위상.

## 2. census (§2)

| | |
|---|---|
| 예산 | `1` 이 5,947 · `0` 이 710 |
| fragment 방문 칸 `c_f` | 1:445 · 2:985 · 3:1,410 · 4:1,620 · **5:1,487** |
| 상태당 source port 수 | **모두 1** |
| 상태당 서로 다른 target 궤도 | **모두 3** (4 joint 중 하나가 중복) |
| 그중 **fresh** target | 2개가 5,699 · 1개가 248 |
| 예산 1 인데 fresh target 0 | **0** |

collision 밴드별 fresh target 수도 고르다(`c=1..5` 전 구간에서 대부분 2개).

**라운드 91 경계 witness 4개 교차 확인 (실측).** 넷을 새 표현으로 다시 판정했다:
`SHORT_LOCAL` 의 fresh target 은 넷 다 `{32, 138}` 이고, **local 모델에서 4/4 UNSAT**,
같은 파이프라인의 **일반 모델에서는 4/4 SAT** 이다. 라운드 91 의 독립 판정(일반 추상에서는
살아남고 locality 에서 닫힌다)과 정확히 일치한다. 이 라운드의 기준선 6,582 는 그 4개를
이미 닫힌 것으로 제외한 값이다.

## 3. 결합 모델 (§3, §4)

기존의 다항식 결합 필요조건 — 유효 SLACK-COVER `S`, `G5` induced 생성, 단사 source-port
매칭 — 은 그대로 두고 short 예외만 바꿨다.

> `S` 는 `SHORT_LOCAL(s)` 의 원소 **최대 1개**(예산 0 이면 0개)로만 short opening 을 쓸 수
> 있고, **모델 전체가 그 하나의 기회를 공유**한다.

추가로, fragment 수리 edge 는 **모든** 완성에서 그 port 에서 발사되므로(라운드 87: port 당
매크로 edge 1회) 그 port 는 `G5` opening 의 source 가 될 수 없다. short 를 쓰든 안 쓰든
매칭 풀에서 배제했다.

판정은 상태의 **모든** valid cover 를 흘려보내며 하고, 첫 완전 SAT witness 에서 멈춘다.
UNSAT 은 완전 유한 판정일 때만 인정하고 캡 도달은 UNKNOWN 이다 — 이번 스윕에서 **UNKNOWN 0**.

## 4. 통제 (§5)

같은 파이프라인으로 두 통제를 먼저 돌렸다.

| 통제 | 모델 | 결과 | SID 일치 |
|---|---|---|---|
| **A** | 일반 예산 2 | UNSAT **13** | 라운드 85 의 13개와 **완전 일치** |
| **B** | 상태별 예산 0/1 + 일반 `Gshort` | UNSAT **71** | 라운드 90 의 71개와 **완전 일치** |

둘 다 SID 단위로 맞은 뒤에만 `SHORT_LOCAL` 을 새 폐쇄에 썼다.

## 5. 본 스윕 (§6)

| | |
|---|---|
| 입력(감사된 기준선) | **6,582** |
| SAT | 6,396 |
| **UNSAT (새 폐쇄)** | **186** |
| UNKNOWN | **0** |
| 소요 | 33초 |

새 폐쇄 분해:

| 축 | 분포 |
|---|---|
| collision `c` | `c=2` 105 · `c=3` 78 · `c=4` 3 |
| root | `short_ell2` 78 · `short_ell1` 61 · `short_ell3` 47 |
| 예산 | **전부 예산 1** (예산 0 상태에서는 0개) |

예산 0 인 710개에서 폐쇄가 0인 것은 일관적이다 — 그 상태들은 라운드 90 의 일반 모델에서
이미 예산 0 으로 판정됐고 `SHORT_LOCAL` 은 그것을 더 좁히지 못한다.

## 6. 일반 예외 대 local 예외 (§7)

새로 닫힌 186개마다 일반 모델(통제 B)의 SAT witness 를 꺼내 비교했다.

| 이유 | 수 |
|---|---|
| **E — short target 이 `SHORT_LOCAL(s)` 밖** | **186 / 186** |
| A/B/C/D (육각형·source 궤도·port·`ℓ`) 단독 | 0 |

일반 witness 의 short target 이 `SHORT_LOCAL` 안에 있었던 경우는 **0건**이고, short 를 아예
쓰지 않은 witness 도 **0건**이다. 즉 **payoff 는 전적으로 target 제한에서 나온다.** 공유 port
규칙(수리 port 를 매칭 풀에서 배제)은 건전하지만 이번에 추가 폐쇄를 만들지 않았다.

일반 모델은 short 로 열 궤도를 사실상 자유롭게 골랐고, locality 는 그 선택지를 **1~2개로**
줄인다. 그 차이가 186개를 만들었다.

## 7. 생존자 진단 — 이 계열의 끝 (§8, §9)

생존자 6,396 전부에 대해 결합 조건을 통과하는 cover 수를 완전히 셌다(캡 도달 0).

| 통과 cover 수 | 1 | 2–5 | 6–20 | >20 |
|---|---|---|---|---|
| 상태 수 | **64** | 1,335 | 3,782 | 1,215 |

| 생존자의 short 사용 | 수 |
|---|---|
| short 기회를 쓰는 통과 cover 가 하나라도 있음 | **0** |
| short 없이 전부 `G5` 로 통과 | **6,396** |

> **short-edge 계열은 소진됐다.** 남은 상태는 short 기회를 아예 필요로 하지 않으므로,
> `SHORT_LOCAL` 을 더 조여도(예: `w2` joint 제거, 착지 위상 고정) 폐쇄는 0이다.
> §9 의 지침대로, 값비싼 M2 전수 스윕을 돌리기 전에 이 사실을 먼저 보고한다.

**다음 경계 집합: 통과 cover 가 정확히 1개인 64개 상태.** 라운드 89 의 19개와 성격이 같지만
이번에는 **감사된 locality 모델 아래에서** 유일하고, 전부 short 를 쓰지 않는다. 즉 그
상태들의 최종 궤도 집합과 생성 구조는 순수 `G5` 로 결정된다 — 다음 라운드의 자연스러운
표적이며, `outputs/rr_short_local_claude.json` 의 `next_boundary_set` 에 cover 까지 보존했다.

## 8. 아티팩트 (§11)

`outputs/rr_short_local_ledger.jsonl.gz` — 상태 1행씩, 스키마 헤더 포함:
안정 `sid` · root · `c` · `K` · 예산 · **판정** · cover 도출 수 ·
`SHORT_LOCAL`(fragment 육각형, `c_f`, `ℓ`, source port, fresh target 궤도, joint별 target 과
착지 위상) · SAT witness cover · 사용한 short · §7 이유 · 유일-통과-cover 여부.
Codex 가 frontier 재구성 없이 그대로 재생할 수 있다.

## 9. 장부

| | |
|---|---|
| 입력 잔여 | 6,582 |
| **새 폐쇄** | **186** |
| UNKNOWN | 0 |
| **잔여** | **6,396** |
| 누적 폐쇄(아카이브 6,657 대비) | 261 = 13 + 58 + 4 + 186 |
| 다음 표적 | 통과 cover 가 유일한 **64** 개 상태 |

**This project has not proved `L₆ ≥ 872`. The results here are conditional progress toward
that goal within the stated Q2/Area-A framework.**
