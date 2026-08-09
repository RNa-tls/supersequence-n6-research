# Round 59 — `short_ell2_r1_37` FZ1 candidate reachability audit

작성자: Codex
상태: Stage-D corpus read-only 감사 및 Stage E bounded continuation 완료·독립 검증.

## 1. 범위와 증명 등급

이 라운드는 다음 질문을 분리한다.

1. 고정된 `HEX_POSITION / ORBIT_PHASE` incidence 표에서 orbit 91의 성분을
   확장할 수 있는 orbit은 무엇인가?
2. 그 국소 후보가 Stage-D의 exact reachable history 안에서 실제
   component-changing Z3(FZ1)으로 실현되는가?
3. 남은 `seed_6`, `seed_3` frontier를 후보 거리 우선순위만 바꾸어 더
   탐색하면 witness 또는 자연소진을 얻는가?

첫 질문은 144 orbit 유한표의 완전 검사이다. 두 번째는 보존된 여섯
Stage-D parent DAG의 literal replay에 대한 완전 검사이다. 세 번째가 cap에서
끝나면 그 결과는 제한 계산이며, 부재 정리가 아니다.

## 2. 원격 동기화

Round 57 dangerous-entry 산출물은
`codex/round-r1-37-dangerous-entry-results`의
`681113270ac8811af3392ac1c3efd412a52be5b3`에 동기화했다. 부모는
`e280d325f59de8aebdcb0b149403ad770cf6ad18`이다.

Stage D 산출물은 `codex/round-r1-37-first-component-z3-stage-d`의
`9342018cd3499de187a534d403aa2d7b85a81ed5`에 동기화했다. 부모는
`681113270ac8811af3392ac1c3efd412a52be5b3`이다. 두 branch 모두
`git ls-remote`로 remote ref를 재확인했고, 검사한 산출물은 일반 Git blob이며
LFS pointer가 아니다. 개별 SHA-256은 실행 원장의 final handoff에 보존한다.

## 3. 20개 국소 후보 — 유한 완전 검증

orbit 91의 다섯 phase가 만나는 hexagon은

```text
{40, 82, 90, 91, 92}
```

이다. 이 집합과 하나 이상의 hexagon을 공유하는 다른 E-orbit은 정확히

```text
36, 40, 41, 42, 72, 74, 78, 82, 83, 90,
92, 93, 95, 96, 98, 102, 120, 126, 128, 129
```

의 20개이다. 144개 모든 orbit의 이 adjacency degree는 정확히 20이다.
따라서 단순한 local cut-saturation 명제는 성립하지 않는다.

hub component의 hexagon

```text
{0, 1, 4, 6, 8, 9, 18, 24, 96}
```

도 만나는 후보는 다음 다섯 개뿐이다.

| orbit | orbit-91 접촉 hex | hub 접촉 hex | 두 incidence의 phase displacement |
|---:|---|---|---|
| 96 | 90 | 96 | 4 |
| 120 | 90 | 0, 96 | 2, 1 |
| 126 | 40, 91 | 6 | 3, 2 |
| 128 | 82 | 8 | 3 |
| 129 | 92 | 9, 24 | 3, 2 |

이 표는 두 edge가 같은 legal history에서 동시에 존재함을 말하지 않는다.
그것은 오직 필요한 local two-edge bridge template이다. 실제 legality에는
fresh target orbit, exact collision 회피, `F=1,H=0`, fragment normal form,
future-R2 source 보존, terminal geometry가 함께 필요하다.

## 4. Stage-D exact corpus의 first-failed-condition 원장

여섯 immutable checkpoint의 모든 확장 노드 1,256,023개에서 weight-3
candidate attempt 2,698,241개를 재생했다. exact/decorated state의 전역
중복을 제거한 별도 census와 전체 frontier를 합치면 1,318,577개이다.

요청된 단계는 다음처럼 구현했다.

- `C0`: 해당 candidate orbit이 legal target으로 노출되지 않음
- `C1`: orbit은 맞지만 orbit-91 접촉 phase가 아님
- `C2`: orbit/phase는 맞지만 target hex가 현재 `C_R1`에 없음
- `C3`: attachment hex는 가능하지만 fresh-orbit registration 조건 실패
- `C4`: registration까지 가능하지만 resource/legality 실패
- `C5`: 모든 local 조건은 만족하지만 exact component change가 아님
- `C6`: exact FZ1 이상 witness

literal attempt의 nonzero 분포는 다음이다.

```text
C1  2,045,959
C2    359,314
C3     39,431
C4    253,537
C5          0
C6          0
```

20개 orbit 모두 target exposure가 있어 orbit별 `C0` 제거 대상은 없다.
`C4` 253,537건은 전부 `F/H/Ndef/P/O` 자원 초과가 아니라 exact literal
collision이었다. 따라서 관측된 병목은 local incidence의 부재가 아니라
visited-history/provenance가 만든 충돌이다.

가장 높은 단계가 `C4`인 orbit은

```text
36, 40, 41, 42, 78, 93, 102, 126, 129
```

이다. 다섯 hub-touch 후보 중 126과 129는 `C4`에 도달했고, 나머지
96, 120, 128은 `C2`까지만 도달했다. `C5/C6=0`은 Stage-D의 보존된
bounded corpus에 대한 정확한 관측이지 미래 frontier에 대한 정리가 아니다.

## 5. `seed_6` / `seed_3`

두 seed 모두 같은 종류의 최상위 병목, 즉 fresh attachment 직전의 exact
collision(`C4`)을 보인다. 그러나 단계별 histogram은 같지 않으므로 두
continuation이 동치라고 주장하지 않는다.

Stage-D 종료 frontier에 candidate-near state가 다수 남았다.

| seed | frontier | best `C3` | best `C4` | legal-successor-positive `C3` | legal-successor-positive `C4` |
|---|---:|---:|---:|---:|---:|
| 6 | 34,712 | 183 | 9,012 | 71 | 5,162 |
| 3 | 34,657 | 446 | 8,982 | 353 | 4,930 |

각 seed의 가장 가까운 상태와 exact ancestry replay는
`rr_short_ell2_r1_37_seed3_seed6_candidate_census.json`에 보존했다.

## 6. Round-57 R4 교차검사

보존된 Round-57 R4 22개 중 20-candidate orbit과 일치하는 entry는 0개,
candidate phase까지 일치하는 entry도 0개이다. 따라서 그 22개는 현재의
exact FZ1 attempt와 같은 객체가 아니라 backward abstraction의 entry다.

## 7. “144 Z3 events” 주장

단순 orbit pigeonhole로는 이 bound가 증명되지 않는다.

- 같은 ancestry에서 orbit 재방문이 실제로 존재한다.
- 같은 orbit도 phase, component partition, visited history가 다를 수 있다.
- orbit ID의 일치는 exact continuation equivalence를 주지 않는다.

Stage-D에서 실제 관측된 ancestry별 최대 Z3 수는 36이며, exact revisit
반례 여섯 개를 certificate에 저장했다. 이것은 “144 이내”라는 수치 명제를
반증한 것이 아니라, 제안된 pigeonhole 증명을 무효화한 것이다. 따라서
현재 판정은 `NOT_PROVED_BY_ORBIT_PIGEONHOLE`이다.

## 8. Stage E 결정과 결과

Stage E 실행 조건 가운데 “`seed_3/6` frontier에 candidate-near state가
다수 존재”가 충족됐다. 이에 두 seed만 fresh namespace에서 각각 독립
500,000 expansion cap으로 실행한다. 후보 거리는 heap ordering에만 쓰며
prune에는 쓰지 않는다. source Stage-D checkpoint는 SHA로 고정하고 수정하지
않는다.

<!-- STAGE_E_RESULT_START -->
두 seed 모두 독립 500,000 expansion cap에 도달했다.

| seed | expansions | frontier | accepted transitions | R2 | FZ1+ | Target A/B |
|---|---:|---:|---:|---:|---:|---:|
| 6 | 500,000 | 560 | 465,848 | 239,200 | 0 | 0 / 0 |
| 3 | 500,000 | 9,483 | 474,826 | 248,646 | 0 | 0 / 0 |
| 합계 | 1,000,000 | 10,043 | 940,674 | 487,846 | 0 | 0 / 0 |

두 frontier가 모두 비어 있지 않다. 따라서 정확한 실행 판정은
`STAGE_E_INCOMPLETE`이며, 0회 관측은 branch-wide 불가능성 증명이 아니다.

독립 verifier는 Stage-D source SHA, Stage-E manifest/provenance, 두 parent
DAG의 1,010,043 node, 1,000,000 expanded node의 모든 raw macro candidate,
940,674 accepted transition, 487,846 R2 record를 literal replay했다. 두
checkpoint SHA와 prune/R2 ledger가 모두 일치했고 `verified=true`다.

실행 도중 이전에 시작된 장기 analyzer가 candidate JSON의 provenance 한
줄을 뒤늦게 덮어쓰는 시간차가 발견됐다. 의미상의 20-orbit 표는 변하지
않았고, Stage-E 시작 manifest와 독립 candidate verifier가 고정한 원본
SHA `6f5bb3dc...`를 현재 analyzer SHA와 일치하는 exact bytes로 복원한 뒤
Stage-E verifier가 그 SHA를 재확인했다. checkpoint 의미에는 영향이 없다.
<!-- STAGE_E_RESULT_END -->

## 9. 결론의 정확한 범위

고정 incidence 표는 20/5 후보를 완전히 결정한다. Stage-D exact corpus에서는
국소 후보가 풍부하지만 component-changing Z3는 없었고, 가장 가까운 시도는
모두 literal collision에서 막혔다. Stage E가 이 관측을 1,000,000회 더
확장했지만 FZ1은 없었고 10,043 frontier가 남았다. 따라서 병목은
provenance-dependent exact collision으로 식별되지만, branch-wide obstruction
정리나 T3/T4 closure로 승격하지 않는다.
