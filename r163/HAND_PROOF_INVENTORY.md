# `L6 = 872` 현행 DAG 손증명 목록 — 라운드 163

**브랜치** `round153-equality-coexistence`  **기반 커밋** `7c5d4ca`
**정본 DAG** `r163/certs/dag_163.json`
(`r162/certs/dag_162.json` 를 비파괴 수리하여 승계)
**산출물** `r163/src/*.py`, `r163/certs/*.json`, 그리고 이 문서

이 라운드는 **새 정리를 증명하지 않는다**.  라운드 149–162 이후 최종
`L6 = 872` 증명에 무엇이 감사되지 않은 채 남아 있는지를 확정하는 것이 목적이고,
그 과정에서 실제로 미해결인 적재 의무가 나오면 그때만 증명으로 넘어간다.
실제로 나온 것은 **미기록 적재 가정 세 개**였고, 셋 다 수학은 이미 증명되어
있었으므로 현행 DAG 의 메타데이터 수리로 닫았다.

---

## 0. 현행 상태 (라운드 153 이 아니라)

`supersedes` / `source_sha256` 사슬을 끝에서부터 되짚어 **끊김 0** 으로 검증했다
(`r163/src/inventory163.py`, `r163/certs/inventory_163.json`).

```
r163/certs/dag_163.json   <- r162 <- r161 <- r160 <- r159 <- r158 <- r157 <- r153
```

각 단계의 `source_sha256` 이 선행 파일의 실제 `sha256` 과 일치한다.
`r147`–`r152` 의 DAG 는 `supersedes` 관례 이전이라 사슬 밖이다.

| 항목 | 값 |
|---|---|
| 브랜치 | `round153-equality-coexistence` |
| HEAD (이 문서 기준) | `7c5d4ca` |
| DAG 경로 | `r163/certs/dag_163.json` |
| 승계 원본 | `r162/certs/dag_162.json` (`sha256 = 4c41bebf…0f7e29`) |
| 노드 수 | **31** |
| 정리 경로 노드 수 | **31** (경로 밖 노드 0) |
| 손증명 노드 수 | **12** |

**주의할 사실**: `r150`, `r154`, `r155`, `r156` 은 산출물을 남겼지만 **DAG 개정을
남기지 않았다**.  그래서 라운드 155(H.tight)·156(H.extract)·150(feas) 의
결론이 라운드 163 직전까지 DAG 에 반영되어 있지 않았다.  아래 F 의 결함
대부분이 여기서 나온다.

---

## A. 현행 정리 상태

| 상태 | 수 | 노드 |
|---|---:|---|
| `CERTIFIED_MACHINE` | 15 | `A.orbitfive`, `C.chaincaps`, `C.piececaps`, `C.dag152`, `C.census`, `E.equivariance`, `E.enumeration`, `X.structure`, `X.exclusion`, `X.nolemmaE`, `X.controls`, `X.mutation`, `X.adversarial`, `T.ge872`, `T.eq872` |
| `AUDITED_HAND_PROOF` | 12 | 아래 B |
| `PROVEN_ANALYTIC` | 2 | `A.monotone`, `A.hexcount` |
| `EXPLICIT_WITNESS` | 2 | `W.872`, `T.le872` |

`forbidden_on_path`, `retracted_on_path`, `unresolved_on_path` 는 **전부 비어
있다**.  `UNKNOWN`·`UNKNOWN_CAP` 상태의 노드도 없다.

최종 검증기 `r153/src/theorem153.py` 를 **깨끗한 체크아웃**에서 재실행한
결과 `L6 >= 872`, `L6 <= 872`, `L6 = 872` 전부 참이고 `FAILURES: none` 이며,
`r153/certs/theorem_153.json` 이 바이트 단위로 동일하게 재생성된다 (아래 §14).

---

## B. 현행 손증명 노드 12 개

`down` = 전이적 하위 노드 수.

| 노드 | 분류 | down | 직접 하위 |
|---|---|---:|---|
| `H.wlog` | INDEPENDENTLY_REPROVED | 13 | `C.chaincaps`, `C.piececaps`, `E.equivariance` |
| `H.catalogue` | INDEPENDENTLY_REPROVED | 12 | `C.chaincaps`, `C.piececaps` |
| `H.feas` | MACHINE_ASSISTED_FULLY_AUDITED | 12 | `C.chaincaps`, `C.piececaps`, `E.enumeration` |
| `H.extract` | INDEPENDENTLY_REPROVED | 9 | `C.census` |
| `H.envelope` | INDEPENDENTLY_REPROVED | 9 | `C.census` |
| `H.incidence` | INDEPENDENTLY_REPROVED | 9 | `C.census`, `X.structure` |
| `H.samehex` | INDEPENDENTLY_REPROVED | 9 | `C.census` |
| `H.master` | INDEPENDENTLY_REPROVED | 9 | `C.census`, `T.ge872` |
| `H.models` | PREVIOUSLY_FULLY_AUDITED | 9 | `C.census` |
| `H.tight` | INDEPENDENTLY_REPROVED | 7 | `X.structure` |
| `H.splice` | INDEPENDENTLY_REPROVED | 2 | `T.ge872` |
| `H.fixedrep` | INDEPENDENTLY_REPROVED | 2 | `T.ge872` |

**분류 집계**: 독립 재증명 **10**, 기계보조 완전감사 **1** (`H.feas`),
기존 완전감사 **1** (`H.models`).
`PARTIALLY_AUDITED` 0, `UNAUDITED` 0, `OBSOLETE` 0.

분류는 판정 토큰이 아니라 **산출물의 내용과 정리 소유권**을 보고 붙였다.
두 곳에서 토큰과 분류가 갈린다.

* **`H.extract`** — 라운드 156 의 토큰은 `H_EXTRACT_PARTIAL` 이지만, 그 사유는
  **수학이 아니라 출처**였다: 정리 (0)–(7) 은 증명되고 전수 2,032만 사례에서
  확인되었는데 노드가 가리키던 문서가 **구현하지도 못하는 다른 절단 절차**를
  적고 있었다.  라운드 156 이 직접 "`where` 를 `r156/THEOREM.md` 로 옮기면
  된다" 고 적었고, 라운드 163 이 그 수리를 했다.  라운드 156 산출물은 고치지
  않았고 여전히 `H_EXTRACT_PARTIAL` 로 읽힌다.
* **`H.models`** — 라운드 149 의 토큰은 `OPUS_H_MODELS_PARTIAL` 이었고 사유는
  **오직 feas 교차검증 불가** 하나였다.  라운드 150 이 그 사유를 제거했다
  (§12).

---

## C. 노드별 감사 이력

| 노드 | 라운드 | 커밋 | 산출물 | 증명 유형 | 판정 |
|---|---:|---|---|---|---|
| `H.models` | 149 | `cc70967` | `r149/PROOF.md`, `r149/AUDIT.md` | 지필 + 전수 유한 검사 | `OPUS_H_MODELS_PARTIAL` (사유: feas) |
| `H.feas` | 149 | `cc70967` | `r149/PROOF.md` §9.5 | 지필 (교차검증 **수행 불가**) | — |
| `H.feas` | 150 | `f410148` | `r150/PROOF.md`, `r150/certs/*` | 지필 + 전수 유한 검사 + 독립 재구현 | `ROUND150_FEAS_FULLY_CERTIFIED` |
| `H.catalogue` | 149 | `cc70967` | `r149/certs/catalogue_complete_149.json` | 전수 유한 검사 (518,400 쌍) | — |
| `H.wlog` | 149 | `cc70967` | 위 인증서 `left_S6_equivariance` | 지필 + 전수 유한 검사 | — |
| `H.wlog` | 153 | — | `r153/src/eqwit153.py` | 기계 인증서 (`E.equivariance`) | — |
| `H.tight` | 155 | `2b081f4` | `research/RR_L6_H_TIGHT_AUDIT.md` | 지필 + 전수 유한 검사 | `H_TIGHT_FULLY_CERTIFIED` |
| `H.extract` | 156 | `324b6d6`, `90bdba6` | `r156/THEOREM.md`, `research/RR_L6_H_EXTRACT_AUDIT.md` | 지필 + 독립 재구현 + 전수 | `H_EXTRACT_PARTIAL` (출처 사유) |
| `H.incidence` | 157 | `6404c09` | `research/RR_L6_H_INCIDENCE_AUDIT.md` | 지필 + 전수 유한 검사 | `H_INCIDENCE_FULLY_CERTIFIED` |
| `H.envelope` | 158 | `400524e` | `research/RR_L6_H_ENVELOPE_AUDIT.md` | 지필 + 전수 유한 검사 | `H_ENVELOPE_FULLY_CERTIFIED` |
| `H.samehex` | 159 | `f5ad1ca` | `research/RR_L6_H_SAMEHEX_AUDIT.md` | 지필 + 전수 유한 검사 | `H_SAMEHEX_FULLY_CERTIFIED` |
| `H.master` | 160 | `d0c370b` | `research/RR_L6_H_MASTER_AUDIT.md` | 지필 + 전수 유한 검사 | `H_MASTER_FULLY_CERTIFIED` |
| `H.splice` | 161 | `48afd14` | `research/RR_L6_H_SPLICE_AUDIT.md` | 지필 + 전수 유한 검사 | `H_SPLICE_FULLY_CERTIFIED` |
| `H.fixedrep` | 162 | `c5814bd` | `research/RR_L6_H_FIXEDREP_AUDIT.md` | 지필 + 전수 유한 검사 | `H_FIXEDREP_FULLY_CERTIFIED` |
| `H.catalogue`·`H.wlog`·`H.feas`·`H.models` | 163 | 이 라운드 | `r163/certs/recheck_163.json`, `hidden_163.json` | 독립 재구현 + 전수 유한 검사 | (전용 감사 라운드는 아님) |

**전용 감사 라운드가 없는 노드**: `H.wlog`, `H.catalogue`, `H.feas`,
`H.models` — 라운드 153 목록이 매긴 우선순위에서 각각 12·11·2·6 위였고,
155–162 이 1·3·4·5·7·8·9·10 위를 처리했다.  라운드 163 이 이 넷을
**전용 라운드 대신 독립 재도출**로 다뤘다 (§10, §11, §12).

### 라운드 163 이 직접 재도출한 것

`r163/src/recheck163.py` 는 `src/`, `r149/`, `r150/` 에서 아무것도 import 하지
않고 정의만으로 다시 계산한다.

| 대상 | 규모 | 결과 |
|---|---|---|
| 카탈로그 완전성 | 순서쌍 **518,400** 전수 | 간격 분포 720/1,440/4,320/17,280/86,400/408,240, 출발지별 프로필 (free 1, A 1, B 1, paid 5, heavy 710) × 720, C1 720/720, C2 720/720 ×2, C3 720/720 ×2, C4 = **0**, 미분류 **0**, 실패 **0** — 라운드 149 인증서와 **전부 일치** |
| 좌 `S6` 추이성 | 720 군원 | 궤도 720, 안정자 **1** |
| 카탈로그 동변성 | 생성원 5 개 × (v,t) 전수 = **2,592,000** 쌍 | 위반 **0**; 동변성은 합성에 닫히고 인접 호환 5 개가 `S6` 를 생성하므로 **군 전체에 대해 전수** |
| feas 쌍대 보조정리 | 다중집합 **7,722** 전수 | 쌍대 최대 = 부분집합 최적, per-`T` 하한 위반 **0** |
| feas **운용 정의역** | 상태 **220,255** 전수 | **생산 히스토그램 탐욕 = 쌍대 = 부분집합 최적** (불일치 0) |

운용 정의역이 220,255 로 끝나는 이유: 가지치기 값은 비현재 개방 궤도의
미사용 위상 수 히스토그램 `(n1,n2,n3,n4)` 와 토큰 예산에만 의존하고,
`t <= 4` 에서 사슬이 여는 궤도는 `O = 24 + k <= 28` 개이므로 비현재는 **27 개
이하**다.  `n1+n2+n3+n4 <= 27`, 토큰 `<= 6` 이 정의역 **전부**다.

---

## D. 소유권 정정

23 개 적재 주장 각각에 **단일 주 소유자**를 지정하고, 그 소유자의 현행 DAG
텍스트에 해당 진술이 실제로 있는지 정규식으로 확인했다 — **실패 0**
(`r163/src/summary163.py`, `r163/certs/hand_proof_inventory_163.json`).

### `H.tight`

| 주장 | 주 소유자 | 비고 |
|---|---|---|
| 등호 행 ⟹ `mu(B) = R_int = 0` ⟹ `B` 는 나무 | **`H.incidence`** | 항등식 `2g = mu(B) + R_int` 가 H.incidence 것이고 H.tight 는 `g = 0` 을 대입할 뿐 |
| **120 개 육각형이 전부 pass 를 갖는다** | **`H.splice` 보조정리 A** | 라운드 155 가 §9 의 괄호 근거는 유도가 아님을 보였다; 올바른 근거는 `m_h >= 1` |
| 사슬이 육각 단순 | `H.tight` | `R_int = 0` 에서 즉시 |
| `\|F\| = 4c` | `H.tight` | `G = 2g + c + d` 에 `g = d = 0` ⟹ `c = G` 필요 |
| `c` 개 순수 순환(완전 `tau`-궤도)이 `F` 를 덮는다 | `H.tight` | "순수 순환 = 완전 궤도" 는 `H.splice` 보조정리 E, "궤도는 서로 다른 다섯 육각형" 은 `A.orbitfive` |

### `H.samehex`

| 주장 | 주 소유자 |
|---|---|
| **하한** `D2 + Qs <= R_int` | **`H.samehex`** (추출 정리의 따름정리가 **아니다**) |
| **상한** `R_int <= 2g` | **`H.incidence`** — 수입일 뿐 이 노드가 증명하지 않는다 |

### `H.master`

| 주장 | 주 소유자 |
|---|---|
| 항등식 `L = 867 + k + Z + H + B*` | `H.master` |
| `k >= 0` | `H.splice` 보조정리 A (`G >= 0`) + `H.models` 보조정리 1.1 (`G <= 5k`) |
| `Z >= 0` | `H.samehex` + `H.incidence` |
| `B* >= 0` | `H.extract` Claim 3·4 |
| `H >= 0` | `H.master` (정의) |

### `H.envelope`

| 주장 | 주 소유자 |
|---|---|
| 상한 네 개 `a <= D2`, `bb <= Qs`, `e <= Z - Qs`, `a+bb+e = rep <= R_int <= 2g` | `H.envelope` — `r156/THEOREM.md` (5)(7) 의 따름정리이며 라운드 158 이 독립 재증명 |
| 조각 모형 **하한** `a >= D2 - d`, `a + bb >= D2 + Qs - d` | **`H.envelope`** — 라운드 158 이 처음 적었다 |

### `H.splice`

| 주장 | 주 소유자 |
|---|---|
| 보조정리 A–F | `H.splice` (라운드 161 이 23 개 절로 분해) |
| G1 — `tau`-궤도는 서로 다른 `n-1` 개 육각형을 만난다 | **`A.orbitfive`** (별도 `CERTIFIED_MACHINE` 노드; 라운드 161 이 한 줄 증명 제공) |

### `H.fixedrep`

| 주장 | 주 소유자 |
|---|---|
| 정규화의 **존재성** (L1–L4 + 따름정리) | `H.fixedrep`.  유일성은 **거짓**이고 필요하지도 않다 |
| C3 로 가는 **정확한 다리** — L5(b) 모든 선택 간격 `= omega` | `H.fixedrep`.  C3 는 이것을 **검사 가능한 가설**로 받으므로 의존은 한 방향, 순환 없음 |

### 라운드 163 이 새로 지정한 소유권 (아래 E 의 발견)

| 주장 | 주 소유자 |
|---|---|
| `G <= 5k` | **`H.models`** (r149 보조정리 1.1) |
| `2g := (G+1) - K >= 0` 이고 짝수, `R_int <= 2g` | **`H.incidence`** |
| `d := K - c - 1 >= 0` (더미를 품은 `beta`-순환은 절대 순수하지 않다) | **`H.extract`** |
| `required = 120 + G - 5c` (Claim 1) | **`H.extract`** |

---

## E. 숨은 적재 주장 — 이번 라운드의 실제 발견

라운드 158 이 조각 모형 하한 두 개를 찾아낸 방식을 **행 생성기 전체에**
적용했다.  `r163/src/hidden163.py` 는 인구조사를 독립 재구현하고
(같은 인증 용량표, 새로 쓴 열거·상한), 후보 가정을 하나씩 끄는 삭마를 돌린다.
**기준선이 저장 인증서를 재현하지 못하면 삭마는 무의미**하므로 먼저 확인했다:
행 1,609, `STRICTLY_CLOSED` **1,607**, `EQUALITY` **2** — `r152/certs/census_152.json`
과 일치.

| 끄는 가정 | 행 수 | 살아남음 | 판정 | 수리 전 DAG 표현 |
|---|---:|---:|---|---|
| `G = 2g + c + d` (`g,c,d >= 0`) | 50,335 | **7,848** | 적재 | **없음** |
| `G <= 5k` | 3,748 | **332** | 적재 | `H.master` 의 `derived_from` 에 `(n-1)O >= P` 로만, 소유자 없음 |
| `required = 120 + G - 5c` | 1,609 | **8** | 적재 | **없음** (`H.extract.what` 은 "the extraction bookkeeping") |
| 묶음: `D2<=2g` + `Qs<=Z` + `Qs<=2g-D2` | 100,424 | **16,375** | 적재 | `H.samehex`, `H.incidence` |
| `t = k + Z + H + B*` | 1,609 | 504 | 적재 | `H.master` |
| `1 <= h <= H` | 5,034 | 664 | 적재 | `H.master` |
| `bb <= Qs` / `e <= Z - Qs` | 1,609 | 435 / 435 | 적재 | `H.envelope` |
| `a + bb + e <= 2g` | 1,609 | 18 | 적재 | `H.envelope`·`H.incidence`·`H.samehex` |
| `a >= D2 - d` | 1,609 | 32 | 적재 | `H.envelope` (라운드 158 발견 재확인) |
| `a + bb >= D2 + Qs - d` | 1,609 | 2 | 적재 | `H.envelope` |
| 모형 split / piece / merged | 1,609 | 439 / 53 / 3 | **셋 다 적재** | `H.models` |
| `Qs <= 2g - D2` 단독 | 1,964 | 0 | **단독 비적재** | — |
| `a <= D2` 단독 | 1,609 | 0 | **단독 비적재** | — |
| `D2 <= 2g` / `Qs <= Z` / `sigma <= B*` 단독 | 1,609 | 0 | **이웃 제약에 가려짐** | — |
| `sigma >= 0` / `D2 >= 0` | 1,609 / 1,806 | 0 | **판정 불가** — 완화가 예산을 오히려 줄인다 | — |

읽는 법.

* `Qs <= Z` 는 `Qs <= 2g - D2` 와 `D2 = 2g + d - Z`, `d >= 0` 에서 **따라 나온다**
  (`2g - D2 = Z - d <= Z`).  단독으로 껐을 때 행 수가 안 변하는 이유다.
* `sigma >= 0`, `D2 >= 0` 의 삭마는 새로 생기는 행에 **더 작은** 예산을 주므로
  구조상 행을 다시 열 수 없다.  "비적재" 가 아니라 **이 방법으로는 판정
  불가**다.  정직하게 그렇게 적는다.
* 인구조사는 조각 모형에서 `m_max = z + 1 + h` 를 쓰는데 `r156/THEOREM.md` (6)
  이 주는 사슬 수는 `d + 1 + h - s <= d + 1 + h <= z + 1 + h` 다 (`z = 2g + d`).
  즉 **정리보다 느슨한 쪽**을 쓰고 있고, 조각을 더 허용하면 용량 상한이 커져서
  행이 덜 닫히므로 상한 논증에 **안전한 방향**이다.

**결론 — 미기록 적재 가정 세 개**: `G = 2g + c + d`, `G <= 5k`,
`required = 120 + G - 5c`.  셋 다 수학은 이미 증명되어 있다 (각각
`H.incidence`+`H.extract`, r149 보조정리 1.1, r156/THEOREM.md (1)).
누락은 **기록의 누락**이었고, §17 이 허용하는 비파괴 메타데이터 수리로 닫았다.
수리 후 재확인: 셋 다 소유 노드를 가지며 `still_unrepresented = []`.

---

## F. 출처 결함

### 수리한 것 (라운드 163, `r163/src/dag163.py`)

| 노드 | 필드 | 수리 전 | 수리 후 |
|---|---|---|---|
| `H.extract` | `what` | `"the extraction bookkeeping"` (자리표시자) | `r156/THEOREM.md` (0)–(7) 전문 + `d = K - c - 1 >= 0` |
| `H.extract` | `where` | 구현 파일 하나 | `r156/THEOREM.md` + 감사 문서 + 구현 (구현은 옳고 **도입부 산문이 틀렸다**는 사실 명기) |
| `H.extract` | `derived_from` | 없음 | 라운드 156 의 `PARTIAL` 은 출처 사유였음, 수치 근거, 원본은 hash-pin 이라 수정하지 않음 |
| `H.incidence` | `derived_from` | 없음 | `2g = mu(B) + R_int`, 좌표 `2g := (G+1) - K`, 연결성 가설, 105,077 반례 |
| `H.models` | `what`, `where` | `r149/PROOF.md` (절 없음) | 절 지정 + 보조정리 1.1·1.2 명시 + 세 모형의 적재 수치 |
| `H.models` | `derived_from` | 없음 | 라운드 149 `PARTIAL` 의 유일 사유와 라운드 150 의 해소 |
| `H.feas` | `where` | **산문** `"round 150 feasibility audit"` | `r150/PROOF.md` + `r149/PROOF.md` §9.5 + `r150/src`, `r150/certs`, `r149/certs` |
| `H.feas` | `what`, `derived_from` | 한 줄 | 정리 전문 + 쌍대형 + 라운드 163 운용 정의역 전수 + **알려진 한계 명시** |
| `H.tight` | `where` | §9 만 | `research/RR_L6_H_TIGHT_AUDIT.md` (라운드 155) 추가 |
| `H.tight` | `derived_from` | 없음 | 120-육각형 근거는 `H.splice` 보조정리 A 라는 정정 |
| `H.wlog` | `what`, `where`, `derived_from` | 한 줄 | 구조적 증명 + 인증서 + 라운드 163 생성원 전수 재도출 + `H.fixedrep` 와 독립임 |
| `H.catalogue` | `what`, `where`, `derived_from` | 한 줄 | 완전성 정리 전문 + 인증서 + 라운드 163 재도출 |

수리 검증: `diff_is_exactly_the_repairs = true`,
`every_derived_field_unchanged = true`, `statuses_unchanged = true`,
`deps_unchanged = true`, **불변 산출물 34 개 `sha256` 전부 불변**,
`theorem_path_clean = true`.  수리 후 손증명 12 노드의 출처 결함
(산문 전용 `where`, 없는 경로, 자리표시자 `what`, 빈 `derived_from`) = **0**.

### 수리하지 않고 이월한 것

* `src/l6_extraction_145.py` 18–22 행과 `r149/PROOF.md` §3 3–5 단계의 **틀린
  절단 절차**.  여러 라운드의 provenance 가 `sha256` 로 인용하므로 고치면
  그 인용이 전부 깨진다.  **DAG 가 더 이상 그것을 정본으로 가리키지 않는다.**
* `r152/src/rows152.py` 16–19 행의 `"the piece model is not used at all"`.
  실제로는 `bounds()` 가 204 행에서 `res["piece"]` 를 무조건 기록하고, 조각
  모형을 빼면 **53 행이 다시 열린다**.  자기 기술만 낡았고 건전성 문제는 아니다
  (조각 용량도 인증값이다).
* 손증명 12 노드의 `deps: []` — 아래 §7 의 관례.

### 후속 라운드 발견과의 대조 (§8)

10 건 전부가 현행 DAG 텍스트에 **기록되어 있음**을 정규식으로 확인했다
(`unrecorded_corrections = []`).  더 강한 **거짓** 역사 진술이 인증된 채
남아 있는 경우는 없다.

| 발견 | 무엇을 무효화했나 | 현재 |
|---|---|---|
| R156 추출 산문 오류 | 노드가 가리키던 **문서**.  구현은 옳고 라운드 156 은 `PARTIAL` 을 냈으므로 거짓이 인증된 적은 없다 | 라운드 163 이 `where` 이전 |
| R158 조각 모형 하한 두 개 | `H.envelope.what` 이 상한 네 개만 적고 있었다 | 라운드 158 수리 완료 |
| R159 `R_int <= 2g` 소유권 | `D2+Qs <= R_int <= 2g` 를 한 덩어리로 소유한다는 진술 | `derived_from` 이 상한은 수입임을 명시 |
| R160 비음수성 소유권 | MASTER-142 가 비음수성까지 준다는 진술 | `what` 이 "imported, not proved here" 명시 |
| R161 보조정리 E 역이 거짓 | 역의 사용 (324/646 덮개에서 실패) | `derived_from` 이 "false and is not used" 명시; `X.nolemmaE` 가 E 없이도 배제됨을 기계로 확인 |
| R162 고정 대표원 유일성이 거짓 | 유일성에의 호소 | `what` 이 존재성만 주장 |
| R155 §9 의 120-육각형 근거 | **근거**만 (주장은 참) | `derived_from` 이 보조정리 A 로 정정 |
| R163 `G = 2g + c + d` 미기록 | 인증된 거짓은 없음; 미기록이었을 뿐 | `H.incidence` + `H.extract` + `H.tight` |
| R163 `G <= 5k` 소유자 없음 | 동 | `H.models` |
| R163 Claim 1 미기록 | 동 | `H.extract` |

---

## G. 남은 의무와 다음 권고

### `REMAINING_HAND_PROOF_OBLIGATIONS` — **비어 있다**

12 개 손증명 노드 전부가 (i) 전용 감사 라운드에서 독립 재증명되었거나
(155–162, 8 개), (ii) 라운드 163 이 정의에서 독립 재도출했거나
(`H.wlog`, `H.catalogue`), (iii) 전용 라운드의 유일한 미결 사유가 이후
라운드에서 제거되었다 (`H.models` ← 라운드 150, `H.feas` ← 라운드 150 + 163).
**새 손증명 감사 대상을 만들어 내지 않는다.**

### 남은 것은 손증명이 아니다 — feas 상태 유지 충실성

| 항목 | 내용 |
|---|---|
| 무엇 | 탐색기의 마스크·카운트·토큰이 정말 보조정리가 말하는 `(u_q, k)` 인가 |
| 왜 부족한가 | 보조정리는 증명되었고 (r150 §2), 알고리즘 동일성은 운용 정의역 220,255 상태에서 **전수** 확인되었으며 (r163), C 구현 5 개의 대응은 179,850 사례에서 불일치 0 이다.  그러나 그 179,850 은 비현재 궤도 **8 개 이하**에서만 전수이고 운용값은 27 이며, 역사적 가지치기의 per-prune 기록은 **존재하지 않는다** (`no_per_prune_trace_available: true`) |
| 하위 영향 | `C.chaincaps`, `C.piececaps` → `C.census`, `E.enumeration` → 사실상 경로 전체 |
| 성격 | **기계 충실성** 의무이지 손증명 의무가 아니다.  라운드 150 자신이 이것을 `cheapest_remaining_risk` 로 적어 두었다 |

### 라운드 164 권고 — **독립 클린룸 종단 검증기**

미해결 손증명이 없으므로 §16 에 따라 **질적으로 다른 공격**을 권고한다.
저장소가 실제로 지탱하는 것은 다음 하나다.

> **탐색기를 다시 쓰지 말고, 탐색기가 남긴 상태를 믿지도 말고,
> `r152/certs/verify_all_c152.json`·`verify_piece_c152.json` 의
> 용량 인증서를 처음부터 다시 검사하는 독립 검사기를 쓴다 —
> 그리고 그 검사기가 각 인증 셀에 대해 `feas` 를 **호출하지 않고**
> 도달 가능성을 재구성하게 한다.**

근거: (i) 남은 유일한 잔여가 feas 상태 유지 충실성이고, 이를 없애는 유일한
방법은 feas 를 쓰지 않는 독립 경로로 같은 용량을 재확인하는 것이다;
(ii) 저장소에 이미 `r152/src/checker152.py` 와 그 C 쌍둥이,
`r149/src/certcheck149.py` 라는 독립 인증서 검사기가 있어 출발점이 있다;
(iii) 라운드 150 이 "route A: 보편 증명 + 구현 대응" 이라고 명시했으므로
route B(인증서 재생) 는 **아직 아무도 하지 않은 일**이다.

형식화·외부 재현·논문화는 그 다음이다.  지금은 증명의 **가장 싼 실패
가능성**이 한 군데로 좁혀져 있고, 그 한 군데를 겨냥하는 것이 옳다.

---

## §7. DAG 의미론 — `deps` 관례

손증명 12 노드 전부가 `deps: []` 다 (12/12).  이것은 누락이 아니라 **관례**이며,
이 프로젝트는 세 관계를 구분한다.

| 관계 | 어디에 | 무엇 |
|---|---|---|
| 논리 DAG `deps` | `deps` 배열 | **기계 파이프라인** 간선: 어느 인증서가 어느 인증서를 소비하는가.  손증명은 파이프라인의 잎이므로 `[]` 가 옳다 |
| provenance `derived_from` | `derived_from` 산문 | 손증명 사이의 **수학적** 의존과 그 근거 |
| 감사 의존 | 감사 문서 | 어느 라운드가 어느 노드를 이미 인증된 의존으로 인용했는가 |

`derived_from` 산문이 이름을 부르는 의존 관계는 `H.fixedrep`→`{H.samehex,
H.wlog}`, `H.splice`→`{A.orbitfive, H.fixedrep}`, `H.master`→`{H.extract,
H.incidence, H.samehex, H.splice}`, `H.samehex`→`{H.incidence}`,
`H.envelope`→`{H.incidence, H.samehex}` 이며 **순환이 없다**
(`H.incidence` 가 싱크).  다만 이 목록은 정규식이 뽑은 것이라 방향이 반대인
언급도 섞인다 (예: `H.fixedrep` 가 `H.samehex` 를 부르는 것은 5(c) 의
**소비자**를 적은 것이다).  실제 방향은 D 의 소유권 표가 정본이다.

`deps` 를 기계적으로 채우지 **않았다**.  채우면 두 관계가 섞여 인증 의미가
흐려진다.

---

## §13. 최종 정리 경로 걷기

출발 (모두 `deps: []`):

| 출발 노드 | 표지 |
|---|---|
| `W.872` | `EXPLICIT_WITNESS` |
| `A.monotone`, `A.hexcount` | `PROVEN_ANALYTIC` |
| `A.orbitfive`, `X.mutation` | `MACHINE_CERTIFIED` |
| `H.wlog`, `H.catalogue`, `H.feas`, `H.models`, `H.extract`, `H.envelope`, `H.incidence`, `H.samehex`, `H.master`, `H.tight`, `H.splice`, `H.fixedrep` | `INDEPENDENTLY_AUDITED_HAND_PROOF` |

`UNKNOWN`·`RETRACTED`·`FORBIDDEN`·`UNRESOLVED` 표지의 출발 노드는 **없다**
(48 개 간선, 위상 순서 전체 확인).

간선의 수학적 함의:

1. `{A.monotone, A.hexcount, H.catalogue, H.wlog, H.feas} -> C.chaincaps`
   — 이동 카탈로그가 완전하고(누락 조인트 없음), 시작 포트를 고정해도 좋고,
   가지치기가 실현 가능한 연장을 지우지 않으므로, 탐색기가 각 예산 벡터에서
   계산한 최댓값은 **참 용량의 상한으로 인증**된다.  `C.piececaps` 는 같은
   전제 위의 표시 조각 판본.
2. `{C.chaincaps, C.piececaps} -> C.dag152` — 용량표가 라운드-147 폐기표를
   읽지 않고 구성되었음을 고정.
3. `{C.chaincaps, C.piececaps, C.dag152, H.master, H.incidence, H.samehex,
   H.extract, H.envelope, H.models} -> C.census`
   — 좌표 `(k,Z,H,B*,G,g,c,d,D2,Qs,h)` 의 행 공간이 `t = k+Z+H+B*`
   (master), `G = 2g+c+d`·`2g >= 0` 짝수 (incidence), `G <= 5k` (models),
   `D2+Qs <= 2g` (samehex+incidence) 로 **유한하게** 잘리고, 각 행이 요구하는
   포트 수 `120 + G - 5c` (extract Claim 1) 를 세 모형의 인증 용량이
   `a<=D2, bb<=Qs, e<=Z-Qs, a+bb+e<=2g` (envelope) 와 조각 하한
   `a>=D2-d, a+bb>=D2+Qs-d` (envelope) 아래에서 **넘지 못함**을 보여
   `L <= 871` 인 행 1,609 개 중 **1,607 개가 엄격히 닫힌다**.
4. `{C.chaincaps, C.census, E.equivariance, A.hexcount, H.feas} ->
   E.enumeration` — 남은 등호 행 2 개의 **모든** 실현을 열거한다.
5. `{E.enumeration, H.tight, H.incidence} -> X.structure`
   — 등호 행에서는 `g = d = 0` 이므로 `mu(B) = R_int = 0`, 사슬은 육각 단순,
   120 육각형 전부 사용, 미사용 `|F| = 4c` 를 `c` 개 완전 `tau`-궤도가 덮어야
   한다는 **구조**가 강제된다.
6. `{X.structure, A.orbitfive} -> X.exclusion`
   — 각 `tau`-궤도가 정확히 다섯 육각형을 만나므로 그 덮개 조건이 **모순**임을
   유한 트리로 보인다 (E1 두 개 295·619 노드, E2 하나 385 노드, 전부
   `EXCLUDED`).
7. `X.exclusion -> {X.nolemmaE, X.controls, X.adversarial}`
   — 보조정리 E 없이도 배제되고, 대조군과 적대적 변형이 통과하지 않는다.
8. `{C.census, E.enumeration, X.*, H.fixedrep, H.splice, H.master} -> T.ge872`
   — 임의의 덮개를 `H.fixedrep` 로 고정 대표원으로 바꾸고(길이 불증가),
   `H.splice` 로 pass·`beta` 구조를 세우고, `H.master` 로 길이를 좌표행으로
   바꾸면, 위에서 모든 행이 닫혔으므로 **`L <= 871` 인 덮개는 없다**.
9. `W.872 -> T.le872` — 길이 872 의 명시적 덮개가 720 순열을 전부 담는다.
10. `{T.ge872, T.le872} -> T.eq872` — **`L6 = 872`**.

---

## §14. 깨끗한 재현

현행 커밋에서 **새 클론**을 만들어 실행했다 (`git clone --no-hardlinks`,
`git checkout 7805115`).

| 명령 | 결과 |
|---|---|
| `python3 r153/src/theorem153.py` | `FAILURES: none`; `L6 >= 872 True`, `L6 <= 872 True`, `L6 = 872 True`; `r153/certs/theorem_153.json` **바이트 동일** |
| `python3 r152/src/rows152.py --verify r152/certs/verify_all_c152.json --verify-piece r152/certs/verify_piece_c152.json --layers 0 1 2 3 4` | L867 1 / L868 14 / L869 85 / L870 353 / L871 1,154+2 — `r152/certs/census_152.json` 의 `layers` 와 **완전 일치** |
| `python3 r163/src/recheck163.py` | 시간 필드를 빼면 로컬 인증서와 **완전 일치** |
| `python3 r163/src/dag163.py` | `dag_163.json`·`hash_invariance_163.json` **바이트 동일** |
| `python3 r163/src/inventory163.py` | `branch`·`head` 를 빼면 일치 (클론은 detached HEAD) |

전수 탐색은 재실행하지 않았다.  프로젝트가 의도적으로 인증서를 저장하므로
(`verify_all_c152.json` 1,101 셀, `verify_piece_c152.json` 220 셀)
**인증서를 검사**했고, 인구조사가 그 1,101 셀을 전부 읽고 미사용 셀이 0 임을
확인했다.  해시 고정 불변 산출물 **34 개**는 이번 라운드 전후로 하나도 바뀌지
않았다 (`hash_invariance_163.json`, `all_unchanged = true`).

---

## 최종 수치

| 항목 | 값 |
|---|---:|
| 정리 경로 노드 수 | **31** |
| 손증명 노드 수 | **12** |
| 독립 감사(재증명·재도출) 완료 | **12** |
| 미해결 손증명 의무 | **0** |
| 발견한 출처 결함 | **18 필드 / 7 노드** (전부 이번 라운드에서 수리) |
| 미기록 적재 가정 | **3** (전부 이번 라운드에서 기록) |
| 소유권 표 검증 실패 | **0 / 23** |
| 불변 산출물 해시 변화 | **0 / 34** |

**라운드 164 권고**: 독립 클린룸 종단 검증기 — `feas` 를 호출하지 않는 경로로
라운드 152 용량 인증서를 재확인하여 남은 유일한 잔여(feas 상태 유지 충실성)를
제거한다.
