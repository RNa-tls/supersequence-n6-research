# 층 A 폐쇄 정정 — 204 철회, 196 확정, 잔여 4,834

**작성:** Claude (독립 검증 트랙)
**라운드:** 94d (정정 라운드, 새 정리 없음)
**재현:** `src/probe_rr_path_connectivity.py` + `outputs/rr_layer_a_archive_v2/`
**감사된 Q2 잔여:** **5,030 → 4,834**

---

## 1. Codex 정정 수용 (§1)

| 항목 | 결과 |
|---|---|
| 층 A 필요조건 자체 | **CONFIRMED** (반박 아님) |
| 제출한 `Layer-A closures = 204` | **철회** |
| 정정값 `Layer-A-only state closures` | **196** |
| 감사된 잔여 | **5,030 − 196 = 4,834** |

이전 주장은 지우지 않고 정정 항목으로 남긴다.

## 2. 버그의 정확한 위치 (§2)

`ma_layerA2.py` 의 상태 집계에서:

```python
if any(v[0] == "SAT" for v in verd):  continue          # 상태 생존
if any(v[0] == "A"   for v in verd):  A_sids.add(sid)   # ← 여기가 틀렸다
if any(v[0] == "B2"  for v in verd):  B2_sids.add(sid)
```

`A_sids` 는 "**어떤** cover 가 A 를 실패" 로 계산됐다. 상태 수준 층-A 폐쇄는
"**모든** Hall 통과 cover 가 A 를 실패" 여야 한다. 그 결과 *다른* cover 가 B2 로 죽어서
상태가 생존하지 못한 경우까지 `A_sids` 에 섞였다 — 즉 **집계 술어가 B2 로 오염**됐다.
`mb_export.py` 는 그 `A_sids` 를 그대로 아카이브로 내보냈다.

정확히 말하면: 잘못된 술어는 `∃cover: A_fail` 이고, 올바른 술어는 `∀cover: A_fail` 이다.

## 3. 로컬 재계산 — Codex 수치 전부 일치 (§3)

`LayerA_UNSAT(s) ⟺ 모든 Hall 통과 cover 가 뿌리 도달성을 실패` 로만 계산했다(B2 불참).

| | Codex | Claude 재계산 |
|---|---|---|
| 상태 | 5,030 | **5,030** |
| Hall 통과 (상태, cover) 쌍 | 27,095 | **27,095** |
| 층 A PASS 쌍 | 21,751 | **21,751** |
| 층 A FAIL 쌍 | 5,344 | **5,344** |
| 상태 수준 층 A UNSAT | 196 | **196** |

SID 단위로 일치한다.

## 4. 여덟 개의 잘못된 제출 (§4)

| SID 접두 | Hall 통과 cover | **층 A 통과 cover** |
|---|---|---|
| `19fb8d24` | 6 | 4, 6 |
| `5c461c58` | 2 | **7** |
| `7ebde4e2` | 4 | 4, 6 |
| `83c00d63` | 9 | 0, 2, 4, 8 |
| `bc2f9d02` | 2 | 13 |
| `c202bf3b` | 4 | 6, 9 |
| `d78d1384` | 7 | 15, 16, 19 |
| `e2d93a51` | 4 | 18, 19 |

Codex 가 지목한 예시를 직접 확인했다:

```
5c461c58  cover 7 : A=PASS  의무 107  뿌리 도달 107
5c461c58  cover 10: A=FAIL  의무 107  뿌리 도달  92
```

여덟 개 전부 `outputs/rr_layer_a_archive_v2/false_submissions_8.jsonl.gz` 에 옛/새 분류와
A-통과 witness cover 를 담아 보존했다.

## 5. 정정 아카이브 (§5)

`outputs/rr_layer_a_archive_v2/layer_a_closures_v2.jsonl.gz` — **정확히 196 상태**.
각 상태에 **모든** Hall 통과 cover 를 싣고 `every_cover_fails_A = true` 를 검증했으며,
cover 마다 의무 수·뿌리 도달 수·**불도달 집합 인증서**를 담았다. B2 정보는 들어 있지 않고
검증에 필요하지도 않다. 그래프는 라운드-93c 아카이브에서 결정적으로 재구성된다.

## 6. 보존되는 건전성 결과 (§6)

층 A 정리 자체는 **반박되지 않았다.** Codex 가 독립 확인한 것: `121−P = 빈 육각형 + 살아있는
fragment` (5,030/5,030) · 일반 `ℓ=5` 범위 · fragment `ℓ=5−c_f` 범위 · `r=1` 수리 port 재사용
불가 · 188,208 전임자 분류 재현 · `LEGAL_BUT_OMITTED = 0` · **2,692,056 건으로 확장한
검사에서도 누락 0** · `G_MAX` 227/228 재현.

> **LAYER-A NECESSITY: CONFIRMED / 204-STATE SUBMISSION: REFUTED /
> 196-STATE CLOSURE SET: INDEPENDENTLY FOUND BY CODEX**

## 7. 집합 산술 정정 (§7)

쌍 수준 실패가 아니라 **상태 수준 술어**로 다시 유도했다.

| 집합 | 정의 | 크기 |
|---|---|---|
| `A_closed` | 모든 cover 가 A 실패 | **196** |
| `B2_closed` | 모든 cover 가 B2 실패 | **186** |
| `A_closed ∩ B2_closed` | | **154** |
| 라운드 94 합집합(모든 cover 가 A 또는 B2 실패) | | 228 |

이전의 "A 관여 204 / B2 관여 32 / 교집합 8" 은 집계 버그가 섞인 값이므로 폐기한다.
**B2 폐쇄는 승격하지 않는다** — 여전히 잠정이고 감사 원장 밖이다(§9).

## 8. 원장 (§8)

| | |
|---|---|
| 정정 전 감사 잔여 | 5,030 |
| Claude 최초 주장 | ~~204~~ **철회** |
| Codex 독립 정정값 | **196** |
| Claude 재계산 | **196** (SID 일치) |
| **감사된 잔여** | **4,834** |

## 9. 생존자 census (§10, 다음 표적 결정용)

4,834 생존자에 대해:

| Hall 통과 cover 수 | 1 | 2–5 | 6–20 | >20 |
|---|---|---|---|---|
| 상태 수 | 735 | 2,722 | 1,246 | 131 |

| **층 A 통과** cover 수 | 1 | 2–5 | 6–20 | >20 |
|---|---|---|---|---|
| 상태 수 | **921** | 2,724 | 1,119 | 70 |

`r` 분포: `r=0` 4,500 · `r=1` 334.
**층 A 를 통과하는 cover 가 정확히 하나인 상태가 921개** — 다음 라운드의 자연스러운 표적이다.
이번 라운드에서는 더 강한 경로 정리를 개발하지 않았다.

**This project has not proved `L₆ ≥ 872`. The results here are conditional progress toward
that goal within the stated Q2/Area-A framework.**
