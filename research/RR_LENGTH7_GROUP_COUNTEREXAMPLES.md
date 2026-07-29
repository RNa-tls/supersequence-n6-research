# 길이 7·8 홀수 지수 반례 해부 (라운드 26)

산출: `src/analyze_rr_length7_obstructions.py` ->
`outputs/rr_length7_counterexamples.json`. **탐색 없음** — 리터럴
단어 전수 열거 + 엔진 replay.

## 1. 열거 범위

네 \(\ell=5\) 생성원 위의 길이 7·8 **리터럴 단어 전부**
(\(4^7+4^8=81{,}920\))를 열거하고, first-return이면서 지수가 **홀수**인
것만 남겼다.

| 길이 | 홀수 지수 first-return word 수 | 지수 분포 |
|---:|---:|---|
| 7 | **3** | {3: 3} |
| 8 | **36** | {1: 12, 3: 24} |

## 2. Replay 결과 — 기대와 정반대

각 단어를 다섯 abandonment root에서 \(\ell=5\) macro-edge로 **실제
엔진에 replay**하고 최초 실패 step과 사유를 기록했다.

```
홀수 지수 단어 총계                    : 39
어느 root에서든 LEGAL하게 실현됨       : 38
legality로 제거됨                      : 1
```

**최초 실패 사유는 단 하나**: `area_a prune: N_exceeded_monotone`
(word×root 쌍 9건, 실패 step 6 또는 7).

> 과제 §3의 목표는 "모든 길이 7 반례를 하나의 공통 legality
> obstruction으로 제거하는 것"이었다. **정반대 결과다: 39개 중 38개가
> legality를 통과한다.** 제거되는 것은 단 1개이며, 그것도 길이 8이다.

## 3. 최소 반례 — 정확한 형태

> **길이 7, return exponent 3 (홀수), 다섯 root 전부에서 legal:**
>
> ```
> joints   = w3:201, w3:201, w2:10, w3:210, w2:10, w3:210, w3:201
> symbolic = F F E F E F R          (#R=1, #F=4, #E=2)
> ```
>
> 두 번째 반례:
> ```
> joints   = w3:201, w3:210, w2:10, w3:210, w2:10, w3:201, w3:201
> symbolic = F F E F E F R          (#R=1, #F=4, #E=2)
> ```

두 단어 모두 **abandonment \(\ell=0,1,2,3,4\) 전부에서** legal하게
replay된다. 이것이 목표 명제의 **exact counterexample**이다.

## 4. 후보 obstruction 전수 판정 (과제 §3 목록)

| 후보 obstruction | 최소 반례를 제거하는가 |
|---|---|
| visited permutation collision | **아니오** (replay 통과) |
| visited phase collision | **아니오** |
| repeated hex target | **아니오** |
| F budget | **아니오** — 아래 §5 |
| N budget | **아니오** — 39개 중 1개만 제거 |
| Hub Touch Count | **아니오** (excursion은 hub에 닿지 않는다) |
| component ancestry | **아니오** |
| endpoint mismatch | **아니오** (first-return 정의상 착지) |
| intermediate illegal abandonment | **아니오** (\(\ell=5\)는 abandonment 아님) |
| \(O_*\)를 더 일찍 재방문 | **아니오** (first-return 조건으로 이미 배제) |

**공통 obstruction은 존재하지 않는다. 반증됨.**

## 5. 분리 좌표 탐색 (과제 §7)

과제가 제안한 budget 좌표를 전부 검사했다.

| 좌표 | 홀수 excursion의 값 | 허용 excursion의 값 | 분리되는가 |
|---|---|---|---|
| 길이 \(L\) | 7, 8 | 1, 4, 5, 7, 8 | **아니오** (\(L=7,8\)에 양쪽 공존) |
| \(\#R\) | 최소 **1** | 0~3 | **아니오** (RR 예산 2 이내) |
| \(\#F\) | 최소 **3** | \(L=5\)에서 이미 3 | **아니오** |

- \(\#R\le2\)로 잘라도 최소 반례(\(\#R=1\))가 살아남는다.
- \(\#F\le2\)로 자르면 홀수는 전부 제거되지만, 그 bound는 **거짓**이다 —
  legal한 \(L=5\) 허용 excursion `FFEFR`이 이미 \(\#F=3\)이고, 관측된
  same-component word에도 \(\#F=3\)이 5개 있다.

> **판정: {길이, R 예산, F 예산} 중 어떤 것도 홀수 excursion을
> 분리하지 못한다. 세 좌표 모두 반증됨.**

## 6. 길이 8 (과제 §4)

길이 8 홀수 반례 36개도 동일하게 거의 전부 legal하다(제거 1개). 길이 7
obstruction에서 자동으로 제거되지 **않는다** — 애초에 길이 7
obstruction이 존재하지 않기 때문이다. 지수 1과 3이 모두 나타나므로
"홀수 지수는 3뿐"이라는 약한 형태도 성립하지 않는다.

## 7. 증명 등급

- 길이 7·8 홀수 first-return 단어 열거: **exact group theorem**
  (리터럴 전수).
- 38/39가 legal: **exact counterexample** (엔진 replay).
- 공통 obstruction 부재, 세 분리 좌표 실패: **반증됨**.
- \(N\_\text{exceeded\_monotone}\)로 제거되는 1개: **exact legality
  obstruction** (단, 일반화 불가).
