# Depth-cap artifact 정확한 영향 정리 (라운드 27 §15)

## 1. 문제의 형태

라운드19~25의 root-local universe는 **abandonment 이후 depth ≤ 6**
(비교 실행 ≤7, 일부 ≤8)이었다. 라운드26이 찾은 알파벳 반례는
\(L=7\) excursion, 즉 **\(O_*\) 재방문 사이에만 7개의 macro-edge**를
요구한다.

## 2. 최소 등장 depth — 정확한 산술

| 구성요소 | 최소 macro-edge 수 |
|---|---:|
| abandonment (word 시작) | 1 |
| \(L=7\) 홀수 excursion | 7 |
| **여기까지 소계** | **8** |
| 이후 Target A(\(R_2\) 경계)까지 최소 추가 | ≥1 |
| **완성된 word 최소 길이** | **≥9** |

따라서:

> **\(L=7\) 홀수 excursion을 포함한 word는 최소 9 macro-edge다.**
> abandonment 이후 depth로는 **≥8**.

## 3. 과거 run들의 scope 판정

| run | abandonment 이후 depth ceiling | \(L=7\) excursion 포함 가능? |
|---|---:|:---:|
| 라운드17~19 uncapped local (depth 6) | 6 | **불가능** |
| 라운드19 비교 실행 (depth 7) | 7 | **불가능** (excursion 자체는 7이나 abandonment 뒤 8 필요) |
| 라운드20 depth 8 실행 | 8 | **excursion만 가능, \(R_2\)까지는 불가능** |
| 라운드25 alphabet 검증 (depth 6) | 6 | **불가능** |
| 라운드26 excursion 열거 (\(L\le8\)) | — | **가능** (그래서 발견됨) |

## 4. 자동으로 scope-limited였던 관측들 — 목록

다음 관측들은 **구조적 사실이 아니라 depth ceiling의 결과**일 수
있으며, 그렇게 표시해야 한다:

1. **라운드25 "알파벳 위반 0/18,778"** — depth 6 scope. 반례가 들어갈
   자리가 없었다. 이미 라운드26에 정정됨.
2. **라운드25 "\(O_*\) 착지 95개 완성 전부 \(\#Z_{\to O_*}\) 짝수"** —
   같은 depth 6 scope. 홀수 excursion을 포함한 word는 ≥9 edge이므로
   이 95개 안에 있을 수 없다. **따라서 95/95 짝수성은 홀수 excursion에
   대해 아무것도 말하지 않는다.**
3. **라운드25 "\(O_*\) 재방문 간격 0, 3, 4"** — 같은 이유로
   \(L\le5\)만 관측 가능했다.
4. **라운드19 "ell=4의 L5는 완전히 안정적"** — 이미 라운드20에
   **반증**됨(원인은 parity). 같은 종류의 artifact다.
5. **non-\(O_*\) zero-charge 총계 95/95 짝수** — 동일 scope.
   `RR_OTHER_ORBIT_ZERO_PARITY_STATUS.md`에 이미 scope가 명시돼 있다.

## 5. 정정의 성격

이것들은 **틀린 측정이 아니다**. 전부 정확한 measurement이며, 각자의
scope 안에서 옳다. 잘못된 것은 그것을 **scope 없는 일반 명제로 읽는
것**이었고, 라운드26·27이 그 읽기를 제거했다.

> **규칙**: depth ceiling \(d\)의 universe에서 얻은 관측은
> "완성된 word 길이 \(\le d+1\)"에 대한 진술이다. 그보다 긴 구조에
> 대해서는 **어느 방향으로도** 증거가 되지 않는다.

## 6. 반대 방향 주의 — 과잉 정정 금지

\(L=7\) excursion이 legal prefix로 존재한다는 사실이 곧 "긴 word가
존재한다"를 뜻하지 **않는다**. prefix legality와 terminal
compatibility는 다른 문제이며, 그 판정이 이번 라운드
(`RR_LONG_EXCURSION_EXTENSION.md`)의 내용이다.

**등급**: §2의 산술은 **손증명**, §3의 표는 **scope correction**,
§4의 목록은 **scope correction**.
