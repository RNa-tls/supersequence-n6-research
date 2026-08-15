# 라운드 93 감사 아티팩트 수리 — 새 정리 없음, 재현 가능한 인증서만

**작성:** Claude (독립 검증 트랙)
**라운드:** 93c
**생성:** `src/export_rr_port_path_hall_archive.py`
**검증:** `src/verify_rr_port_path_hall_archive.py` (표준 라이브러리만, 이 저장소 코드 미사용)
**아카이브:** `outputs/rr_port_path_hall_archive/` (+ `SCHEMA.md`)
**감사된 Q2 잔여:** **6,396 — 변동 없음**
**라운드 93 지위:** `HALL NECESSITY SOUND / STATE COUNTS CLAUDE-REPRODUCED /
INDEPENDENT COUNT AUDIT PENDING`

---

## 1. Codex 해석 정정 수용 (§1)

라운드 93 은 생존자의 "통과 cover 수" 히스토그램을 `{1: 1,760, 2–5: 1,876, 6–20: 1,316,
>20: 78}` 로 보고했다. 구현이 **첫 Hall 통과 cover 에서 멈추므로** 그것은 통과 cover 의 완전
계수가 아니다.

> **철회.** "1,760개 상태가 Hall 통과 cover 를 정확히 하나 가진다" 는 **틀렸다.**
> 라운드 94 의 표적으로도 쓰지 않는다.

이번 라운드는 §3 이 요구한 **완전 열거**를 실제로 수행했으므로 정정값을 함께 남긴다.

| Hall 통과 cover 수 | 0 | **1** | 2–5 | 6–20 | >20 |
|---|---|---|---|---|---|
| 상태 수 | 1,366 | **746** | 2,791 | 1,340 | 153 |

같은 종류의 정정이 하나 더 있다. 라운드 93 의 결손 히스토그램 `{1:812, 2:381, 3:144, 4:28,
5:1}` 은 상태마다 **마지막으로 평가된 cover** 의 결손이었다 — 역시 첫 성공에서 끊는 루프의
부산물이다. 아카이브는 라벨을 나눠 셋을 모두 담는다.

| 필드 | 값 |
|---|---|
| 모든 상태의 실패한 모든 cover | `{1:35,412, 2:20,523, 3:6,304, 4:1,014, 5:47, 6:1}` |
| UNSAT 상태의 cover 들 | `{1:5,756, 2:6,577, 3:2,732, 4:482, 5:29, 6:1}` |
| **UNSAT 상태별 최소 결손** (의미 있는 상태별 통계) | **`{1:1,206, 2:156, 3:4}`** |

이전 서술은 지우지 않고 정정 항목으로 남긴다.

## 2. 아카이브 (§2–§6, §9)

`outputs/rr_port_path_hall_archive/` — 전부 스키마 헤더가 붙은 압축 JSONL.

| 파일 | 행 | 내용 |
|---|---|---|
| `geometry.jsonl.gz` | 720 | 단어 고정 번호: 순열 문자열, 궤도·위상, 육각형·위치, `ℓ=0..5` 각각의 4개 joint target |
| `states.jsonl.gz` | **6,396** | `p`, `hex_masks`(120), `orbit_masks`(144), `F/S/H`, `O/P/D`, `c/r/K/b`, `U`, 열린 궤도, 현재 육각형, fragment 육각형·`c_f`·`ℓ`·수리 진입 단어·port |
| `covers.jsonl.gz` | **90,396** | 상태별 라운드-92 통과 cover 집합 **전부**(도출 중복 제거, 첫 성공 절단 없음) |
| `hall_results.jsonl.gz` | 90,396 | (상태, cover) 마다 왼쪽/슬롯 크기, 매칭 크기, 결손, König 결손 부분집합 `X` 와 `N(X)` |
| `sat_witnesses.jsonl.gz` | **5,030** | 통과 cover 와 **완전 매칭**(왼쪽 의무 → 전임 슬롯) |
| `unsat_certificates.jsonl.gz` | **1,366** | 그 상태의 **모든** cover 에 대한 결손 인증서 |
| `SCHEMA.md` | — | 스키마 + Hall 그래프 **재구성 규칙** |

핵심은 `hex_masks` 다 — Codex 가 갖지 못했던 것, 즉 **후보 전임자가 이미 방문/소비됐는지**를
판정하는 자료가 여기 있다. 방문(window)과 등록(port)의 구분도 스키마에 명시했다.

Hall 그래프는 저장값에 의존하지 않는다. `SCHEMA.md` 의 규칙만으로 상태·cover·기하에서
**결정적으로 재구성**된다.

## 3. 독립 재생 (§7)

`src/verify_rr_port_path_hall_archive.py` 는 **표준 라이브러리만** 쓰고 이 저장소의 탐색·
frontier·probe 코드를 **하나도 import 하지 않는다.** 아카이브만 읽어 다음을 수행한다.

1. 6,396 상태 행 검증 — 마스크 형태, `P = Σ popcount(orbit_masks)`, `O`, `D = 5O − P`,
   endpoint 가 방문·등록됨, 현재 육각형 방문 칸 = 1, fragment 점유와 `ℓ = 5 − c_f`,
   그리고 `121 − P = (빈 육각형) + (fragment)`.
2. (상태, cover) 90,396 쌍의 Hall 그래프를 처음부터 재구성.
3. 저장된 SAT 매칭의 **모든 간선**을 기하에 대조하고 슬롯 중복 사용을 검사.
4. 모든 cover 에 대해 최대 매칭 재계산.
5. cover 하나라도 통과하면 SAT, 전부 실패해야 UNSAT.
6. 저장된 결손 인증서의 `|N(X)| < |X|` 직접 확인.

**결과.**

| | |
|---|---|
| 상태 행 문제 | **없음** |
| 재생된 총계 | **SAT 5,030 / UNSAT 1,366** |
| 저장값 대 재계산 Hall 결과 불일치 | **없음** |
| 잘못된 SAT witness | **0** |
| 잘못된 UNSAT 인증서 | **0** |
| 결손 히스토그램 일치 | **True** |

즉 라운드 93 의 상태 계수는 **아카이브만으로 재현된다.** (여전히 Claude 재현이며 Codex
독립 감사 대기다.)

## 4. 구체 사례 수리 (§8)

`14fda65d…` 를 아카이브만으로 펼치면 Codex 가 확인하지 못했던 사실이 그대로 나온다.

```
=== 14fda65d covers=1 p=130452 ===
cover 0 deficit=1 unmatched=[('hex', 101)]
  hexagon 101: final-orbit candidate words [101]
   entry word 051432 (orbit 101, phase 0) — all predecessors:
     240513 orbit 97  hex 98  ell=5 visited=False in_final_orbits=False
     305142 orbit 101 hex 100 ell=5 visited=True  in_final_orbits=True
     340512 orbit 99  hex 96  ell=5 visited=False in_final_orbits=False
     430512 orbit 101 hex 97  ell=5 visited=True  in_final_orbits=True
```

육각형 101 은 최종 궤도 단어를 **하나만**(`051432`) 포함하고, 그 단어의 **모든** 전임자
4개는 둘이 비선택 궤도(97, 99), 둘이 **이미 방문된** 단어다. 그래서 진입이 불가능하고
결손 1 이 나온다. 이 상태의 라운드-92 통과 cover 는 1개뿐이므로 상태 판정이 UNSAT 이다.
재현: `python3 src/verify_rr_port_path_hall_archive.py --example 14fda65d`.

## 5. 원장 (§10, §11)

새 정리 없음. 매칭을 단일 경로로 강화하지 않았고, 잠정 5,030 생존자를 연구하지 않았으며,
철회된 1,760 집합을 표적으로 삼지 않았고, continuation 탐색도 하지 않았다.

| | |
|---|---|
| **감사된 Q2 잔여** | **6,396** |
| 잠정 Claude Hall 잔여 | 5,030 |
| 잠정 폐쇄 | 1,366 |
| UNKNOWN | 0 |
| 라운드 93 지위 | HALL NECESSITY SOUND / STATE COUNTS CLAUDE-REPRODUCED / **INDEPENDENT COUNT AUDIT PENDING** |

**This project has not proved `L₆ ≥ 872`. The results here are conditional progress toward
that goal within the stated Q2/Area-A framework.**
