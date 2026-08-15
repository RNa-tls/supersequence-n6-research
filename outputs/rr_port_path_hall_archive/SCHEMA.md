# PORT-PATH HALL 감사 아카이브 — 스키마와 재구성 규칙

**라운드:** 93c (감사 아티팩트 수리)
**생성:** `python3 src/export_rr_port_path_hall_archive.py --exclude <closed261.json>`
**검증:** `python3 src/verify_rr_port_path_hall_archive.py` — **표준 라이브러리만** 쓰고 이
저장소의 탐색·frontier·probe 코드를 하나도 import 하지 않는다.

이 아카이브만으로 라운드 93 의 판정을 처음부터 다시 계산할 수 있다. frontier 재구성은
필요 없다.

> **원장 지위.** 감사된 Q2 잔여는 여전히 **6,396** 이다. 여기 담긴 `SAT 5,030 / UNSAT 1,366`
> 은 **Claude 재현 수치이며 독립 감사 대기 중**이다.

---

## 파일

| 파일 | 행 | 내용 |
|---|---|---|
| `geometry.jsonl.gz` | 720 | 단어 번호 고정표 |
| `states.jsonl.gz` | 6,396 | 리터럴 상태 |
| `covers.jsonl.gz` | 90,396 | 상태별 라운드-92 통과 cover 집합 **전부** |
| `hall_results.jsonl.gz` | 90,396 | (상태, cover) 마다 Hall 판정과 결손 인증서 |
| `sat_witnesses.jsonl.gz` | 5,030 | SAT 상태의 통과 cover 와 **완전 매칭** |
| `unsat_certificates.jsonl.gz` | 1,366 | UNSAT 상태의 **모든** cover 에 대한 결손 인증서 |
| `summary.json` | — | 총계와 라벨이 명시된 히스토그램들 |

각 `.jsonl.gz` 의 **첫 줄은 스키마 헤더**이고 나머지가 데이터 행이다.

## `geometry.jsonl.gz`

```
{"id": 0..719, "word": "012345", "orbit": 0..143, "phase": 0..4,
 "hexagon": 0..119, "hex_index": 0..5,
 "joint_targets": {"0": [id,id,id,id], ..., "5": [id,id,id,id]}}
```

`joint_targets[ell]` = 그 단어에서 `σ` 를 `ell` 회 적용한 뒤 4개 joint(`w2:10`, `w3:120`,
`w3:201`, `w3:210`)를 각각 적용한 target 단어의 id. 순서는 그 joint 순서로 고정한다.
`hexagon` 은 `σ` 궤도(6칸), `orbit`/`phase` 는 `E` 궤도(5칸)다. 720 단어 ↔ 144×5 port 는
전단사이므로 **port 하나가 단어 하나**다.

## `states.jsonl.gz`

```
{"sid": <sha256>, "root": "short_ellK", "idx": <checkpoint index>,
 "p": "130452", "p_id": <geometry id>,
 "hex_masks": [120 ints], "orbit_masks": [144 ints],
 "F":1, "S":.., "H":.., "O":.., "P":.., "D":..,
 "c":.., "r":0|1, "K":.., "b":.., "U": "0x…", "open_orbits": "0x…",
 "current_hex":.., "empty_hexes":..,
 "fragment": null | {"hex":.., "c_f":1..5, "ell":5-c_f, "entry_id":.., "port":[q,f]},
 "short_local_fresh_targets": [궤도…]}
```

* `hex_masks[h]` 의 비트 `b` = geometry 의 `(hexagon=h, hex_index=b)` 단어가 **방문됨**.
* `orbit_masks[q]` 의 비트 `f` = `(orbit=q, phase=f)` port 가 **등록됨**(= pass 시작).
* 방문과 등록은 다르다 — 회전 내부로 방문된 단어는 등록되지 않으며 다시 joint target 이 될
  수 없다. **전임자가 이미 소비됐는지 판정하는 데 필요한 정보가 바로 `hex_masks` 다.**
* 검증기가 재계산하는 항등식: `P = Σ popcount(orbit_masks)`, `O = #{q : mask≠0}`,
  `D = 5·O − P`, 현재 육각형의 방문 칸 = 1, `121 − P = (빈 육각형) + (fragment 유무)`.

## `covers.jsonl.gz`

```
{"sid":…, "cover_id": 0.., "orbits": [K개 궤도], "short_used": [궤도?], "round92_model": "local"}
```

상태마다 **라운드-92 결합 조건(SLACK-COVER + `G5` induced 생성 + 단사 source-port 매칭 +
fragment-local short 기회)을 통과하는 서로 다른 cover 집합 전부**다. 도출 중복은 제거했고,
**첫 성공에서 끊지 않았다** — UNSAT 상태의 완전성이 여기에 달려 있다.

## Hall 그래프 재구성 규칙 (아카이브만으로 결정)

    최종 궤도 = open_orbits ∪ cover.orbits            (|·| = 25)
    빈 육각형 = hex_masks[h] == 0 인 h
    육각형 h 의 진입 후보 = hexagon=h 이고 orbit ∈ 최종 궤도인 단어
    왼쪽  = 빈 육각형 전부 (+ fragment 가 있으면 fragment 진입)
    슬롯  = 현재 pass + 왼쪽                          (각 슬롯은 정확히 1회 발사)
    후속  = 현재 pass: p 의 joint_targets["5"]
            fragment : entry 의 joint_targets[str(ell)]
            빈 육각형: 진입 후보들의 joint_targets["5"] 합집합
    간선  = 슬롯의 후속 ∩ 왼쪽 노드의 진입 후보 ≠ ∅   (자기 자신 제외)

근거: 회전은 port 를 등록하지 않고 joint 는 정확히 1개 등록하므로 **pass 하나가 육각형
하나를 소비하고 진입 칸 하나만 등록**한다. 진입 칸은 등록되는 port 이므로 최종 25궤도의
단어여야 한다. 후보를 합집합으로 쓰는 것은 **관대한 과대근사**이며, 따라서 **Hall 위반만**
폐쇄 근거가 된다.

## `hall_results.jsonl.gz`

```
{"sid":…, "cover_id":…, "left":…, "slots":…, "matched":…, "deficit":…,
 "verdict": "SAT"|"UNSAT",
 "hall_violator": {"X": [왼쪽 노드…], "size":…, "neighbourhood": [슬롯…], "neighbourhood_size":…}}
```

`hall_violator` 는 König 로 뽑은 결손 부분집합이며 `|N(X)| < |X|` 를 만족한다. 검증기는
저장값을 믿지 않고 **인접 관계를 다시 만들어** 이 부등식을 직접 확인한다.

## `sat_witnesses.jsonl.gz` / `unsat_certificates.jsonl.gz`

```
SAT   {"sid":…, "cover_id":…, "orbits":[…], "matching": [[왼쪽 노드, 슬롯], …]}
UNSAT {"sid":…, "covers": n, "certificates": [{"cover_id":…, "deficit":…, "hall_violator":…}, …]}
```

SAT 은 매칭의 **모든 간선**이 위 규칙으로 실재하는지, 슬롯이 중복 사용되지 않는지 검증된다.
UNSAT 은 그 상태의 **모든** cover 에 인증서가 있어야 하며(`covers` 가 `covers.jsonl.gz` 의
개수와 일치해야 한다), 캡·타임아웃은 UNSAT 으로 표기하지 않는다 — 이번 내보내기에서 cover
열거는 전부 완전했다.

## 히스토그램 라벨 (라운드 93 정정)

라운드 93 이 보고한 결손 히스토그램 `{1:812, 2:381, 3:144, 4:28, 5:1}` 은 상태마다
**마지막으로 평가된 cover** 의 결손이었다 — 첫 성공에서 끊는 루프의 부산물이며 완전 통계가
아니다. 아카이브는 라벨을 나눠 셋 다 담는다.

| 필드 | 뜻 | 값 |
|---|---|---|
| `all_failing_cover_deficits` | 모든 상태의 **실패한 모든 cover** | `{1:35412, 2:20523, 3:6304, 4:1014, 5:47, 6:1}` |
| `unsat_state_cover_deficits` | **UNSAT 상태**의 cover 들 | `{1:5756, 2:6577, 3:2732, 4:482, 5:29, 6:1}` |
| `unsat_state_min_deficit` | UNSAT 상태별 **최소** 결손 (의미 있는 상태별 통계) | `{1:1206, 2:156, 3:4}` |
| `hall_passing_cover_histogram` | 상태별 Hall **통과** cover 수 (완전 열거) | `0:1366, 1:746, 2–5:2791, 6–20:1340, >20:153` |

마지막 줄이 라운드 93 의 "1,760 개 상태가 통과 cover 1개" 주장을 정정한다 — 완전 열거에서는
**746** 이다.
