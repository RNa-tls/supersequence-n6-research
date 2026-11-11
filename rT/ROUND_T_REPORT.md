# Round T 보고서: 공개 46173 구성의 수입·감사와 고정 선택의 정확 최적

브랜치는 `claude/n6-supersequence-length-rn17wf`, 디렉터리는 `rT/`이다. 용어 구분은 앞 라운드와 같다: **증명**(논증 또는 Lean), **계산 증명서**(전수 계산, 파일 있음), **관측**(표본·탐침).

## 0. 결론

* 공개 46173 단어(Theo H.)를 받아, 선택 파일에서 **독자 코드로 다시 만들고** 바이트 단위로 같음을 확인했다. 검증 경로는 여섯 가지이다(§B).
* 구 가족(6A + 24φ)과 공개 선택은 **같은 Pantone 틀 안의 두 선택**이다. 길이 장부 하나 `L = 46085 + Q + J`가 둘 다에 정확히 맞는다(Lean `ledger`).
  * 구 46183: Q = 48, J = 50. 공개 46173: Q = 64, J = 24. 열 글자는 −16 + 10 + 15 + 1이다(§E).
* **고정 선택의 단일 개방 최적은 정확히 46173이다(계산 증명서, 독립 검사기 둘).** 16개 trail의 모든 순서 × 모든 단일 개방(클래스 안 절단 포함 40,488개, 겹침 7까지)에서 J의 최솟값은 24이다. 46172(J ≤ 23)는 이 범위에 없다(§I).
* **다중 개방**: 감싸기를 쓰지 않는 run 수준 경로는 모두 J ≥ 24이다(정리 S1의 이전 + 괄호 나무 하한 26). 감싸기를 쓰는 경로는 열려 있다(§J).
* ≤ 46172 단어는 찾지 못했다. 하한 46134의 산술은 재현했고 46135는 얻지 못했다(§L).
* 하지 못한 것: 선택을 바꾸는 탐색(§16), 선택 + 연결 결합 하한(§17), 하한 46134의 Lean 재빌드. 외부 C++ 검사기와 외부 탐색 프로그램은 실행하지 않았다(실행 권한이 거부되어 자체 검사기만 썼다).

---

## A. 외부 현황과 신뢰 등급

| n | 범위 | 등급 |
|---|---|---|
| 6 | L(6) = 872 (Halfar, `SmallSuperperm.exact_six`, `grayzel_six`) | 1: Lean 커널만. 공리 propext, Classical.choice, Quot.sound. Comparator 승인, nanoda 통과(2026-10-28). 독립 제3자 재실행은 아직 확인되지 않음 — 출처·재현 문제이지 수학적 공백이 아니다. |
| 6 | 길이 872 최소 단어 45,116개 목록 | 4: 별개의 열거 결과. 형식 증명과 섞지 않는다. |
| 7 | 5900 ≤ L(7) ≤ 5905 | 2: Lean + native_decide |
| 7 | 5901 ≤ L(7) | 3: 컴퓨터 보조. 탐색 방정식 30개 중 7개만 native_decide(K6 포함, K6은 둘째 집계 없음), 23개는 외부 프로그램 |
| 8 | L(8) ≥ 46133 | 1: 커널만 |
| 8 | L(8) ≥ 46134 | 2: Lean + native_decide 방정식 3개 |
| 8 | L(8) ≤ 46173 (Theo H.) | 4: 검증된 구성 |

* 이 표는 사용자가 준 정보와 두 저장소의 README를 정리한 것이다. 이번 라운드에 직접 다시 확인한 것은 n = 8 상한(단어 검증)과 하한 46134의 **산술 단계**뿐이다.
* 이 프로젝트의 구 가족 결과(Round P–S)는 등급 4의 가족 내부 결과이다. 전역 하한을 주지 않는다.

## B. 46173 자료와 독립 검증

* 출처: `Tholsh/superpermutation_study`, 커밋 `415ed468d50a9962d6fba51e692cb36901413f80`, 경로 `data/n8/46173/`. 패키지의 `SHA256SUMS` 24개 항목이 모두 맞는다.
* 46174 기반: 같은 패키지의 `reference.txt`·`reference.plan`(Halfar의 단어). Halfar 저장소 `jhalfar/superpermutations`는 커밋 `a93638e798cc380b19f84a01a6c9edacf8dcf114`를 읽었다(패키지가 고정한 개정은 `c9cb9230…`).
* 저장소에 둔 사본: `rT/external/tholsh_46173/`(선택, 표, 두 계획, 두 단어, base, LICENSE·NOTICE·PROVENANCE).

| 파일 | sha256 |
|---|---|
| `solution.txt` (46173, LF 포함) | `9ec23c8c05d60e51786d5fedea27aa3b6b2841c96fe15cf82c6095ecede7b475` |
| `solution.txt` (LF 제외) | `6ad59b18b8cd281fe0052a0e6898d74e533c6c56f68776948fb0f1c912c4a613` |
| `reference.txt` (46174) | `66ec57ba428e0ac1affc5503b86821920f0def27380697317033911a6628cddd` |
| `selection.txt` | `d3ce4d10b47acc831766b710ee04f5d3c87ea82cce0ca98b1c79e68d9e0b201b` |
| `solution.plan` / `reference.plan` | `87ae8338…` / `c9bbb987…` |

* 재구성 명령: `python3 -I rT/src/build_from_selection.py selection.txt base.tsv solution.plan OUT.txt --base base.txt`. 결정적이다(탐색 없음).
* 검증 경로(서로 다른 논리).
  1. **선택에서 다시 만들기**: slice 정의만으로 16개 닫힌 trail을 만들고(문자 그래프의 순환), 계획을 자체 철자기로 적용했다. 두 단어 모두 바이트가 같다. 외부 도구는 불러오지 않았다. `base.txt`는 trail 번호와 회전을 맞추는 데만 썼고, 순환 단어가 내 것과 같음을 확인했다.
  2. 창 문자열 집합: 순열 창 40,376개, 서로 다른 순열 40,320개, 빠진 것 0.
  3. numpy Lehmer 순위 + 개수 세기: 같은 수, 최대 중복도 2, 반복 56.
  4. 클래스 구조: 무게 1 구간 5,040개가 서로 다른 순환 클래스 5,040개를 각각 완전히(8개 순열) 지난다.
  5. C 검사기(8진 부호 표, `rT/csrc/check_word.c`): 같은 수.
  6. run 장부: 길이 = 46085 + 64 + 24를 단어에서 직접 계산(`word_ledger.py`).
* 알파벳은 0–7이고 잘못된 창은 없다. 46174 단어도 같은 경로로 통과했다(순열 창 40,377, 반복 57).
* 패키지에 든 원래 영수증(Pantone의 literal checker 등)은 외부 주장으로만 적는다. 이번에 그 프로그램을 실행하지 않았다.

## C. 용어 사전 (외부 → 이 프로젝트)

| 외부 용어 | 이 프로젝트 | 관계 |
|---|---|---|
| loop (K = 6 글자의 순환 순서, 120개) | 두 특수 글자를 지운 클래스 묶음; 클래스 42개씩 | **정확**. 모든 클래스는 loop 하나에 속한다. 구 가족의 특수 글자는 {0, 7}, 공개 선택은 {6, 7}. |
| row (x, v) | loop에서 선택이 취한 조각; v = 12 − (그 loop의 slice 수) | **정확**(v ≥ 1). 구 용어에는 직접 대응이 없었고 이번에 읽어 냈다. |
| slice (b, d, c) | 무게 2로 이어진 run의 최대 사슬(c개), 사슬 = c = 7일 때 "완전 사슬" | **정확** |
| closed walk (행의 닫힌 보행) | A 묶음(행 16개) / W27(행 27개) | **정확**: A = 행 낱말 (4666)⁴의 보행 |
| closed trail | trail | **정확**. 행 없는 loop의 trail = φ trail(완전 사슬 6개, run 42개) |
| selection | 가족(trail 집합); φ-집합 = 행 없는 loop의 집합 | **정확** |
| Q = Σ(6 − v) | (무게 3 자연 결합 수) − 720 | **정확**(양쪽 가족에서 확인: 48, 64) |
| opening, g ∈ {2, 3} | 절단(자연 결합 c ∈ {2, 3}을 끊음); opening cost = 3 − c | **정확** |
| g = 1 개방(클래스 안) | 없음(run은 원자) | 대응 없음. 이번 정확 해법에는 넣었다. |
| join, cost = 5 − overlap₅ | 이음, 무게 w = 8 − overlap₈; cost = w − 3 | **아핀**(겹침 ≤ 5일 때 같음; 이 선택에서 trail 사이 겹침은 5 이하) |
| J (Halfar) = opening + join | Σ절단(3 − c) + Σ이음(w − 3) | **정확** |
| — | G(구) = L − 46162 = Q + J − 77 | **아핀**. 공개 46173은 이 눈금으로 11 |
| — | e(o → o′) = w − c(o′) − 1 | **정확**; J = (P − 1) + (3 − c₁) + Σe (Lean `ledger_e`) |
| — | 전하 χ(v), Σχ = J | **정확**(단일 조각 방문: χ(v₁) = 3 − c₁, χ(v) = e + 1) |
| plan (O t start g) | 조각 목록 = 경로(route) | **정확** |
| transport / port | 보행을 도는 trail의 통과 번호(5개 port의 순열) | **부분**: port 순열의 순환 수 = 보행당 trail 수 |
| piece, visit, bracket, 덮개 τ | 계획의 사건, 같은 trail 안 연속 조각, 닻에 매단 순환 | 외부에 대응 용어 없음(외부 계획은 조각 S 사건까지만 있음) |
| endpoint state | 조각의 첫 7글자·끝 7글자 | **정확**(이음 비용은 이것만으로 정해진다) |

## D. 46173의 정확한 분해

* trail 16개: 행 없는 loop의 trail 12개(D, R = 384, run 42개, 무게 3 결합 6개)와 W27의 trail 4개(R = 10,384, run 1,134개, slice 178개; 무게 2 결합 956, 무게 3 결합 178 가운데 14개는 아홉째 창을 지나는 "1 + 2"형).
* ΣR = 46,144 = 46,080 + 64. 자연 결합 무게 합 10,864.
* 경로: P = 16, V = 16, 덮개는 경로 하나(순환 0, 괄호 0, 회전 0, 감싸기 0).
* 절단: c = 3이 13개, c = 2가 3개. 이음 15개의 무게: 3이 1개, 4가 9개, 5가 3개, 6이 2개.
* **J = 3 + 21 = 24**, L = 46149 + 24. Σe = 9, c₁ = 3. 방문별 전하(순서대로): 0, 1, 1, 3, 1, 1, 2, 3, 1, 3, 1, 1, 1, 3, 1, 1 (합 24).
* D trail 12개는 세 개씩 네 덩이 [3,4,5], [10,0,2], [1,11,7], [6,8,9]를 이룬다(덩이 안 이음은 비용 1; 두 단어에서 같다).

| 양 | 값 | 분류 |
|---|---|---|
| trail 수, Q, P, V, 절단·이음 무게, J, Σe, χ | 위 | 직접 정의 |
| 클래스 재방문(이 프로젝트의 r) | 0 (클래스 5,040개를 한 번씩 완전히 지남) | 직접 정의 |
| 순열 반복 창 | 56 (구 46183은 48) | 직접 정의. 무게 3 결합이 아홉째 창을 지나는 수이다 |
| G | 11 = Q + J − 77 | 정확한 공식으로 번역 |
| E (Round R의 "J" = L − 46085) | 88 | 정확한 공식으로 번역 |
| τ(덮개), 괄호·회전 구조 | 경로 하나, 없음 | 직접 정의 |
| 판본(trail당 2개) | 해당 없음 | 가족 고유. 구 가족의 두 판본은 특수 글자 0과 7의 역할 교환이다 |
| 예산 "Σχ ≤ 49", κ·slack 표, H/HT 표 | 해당 없음 | 가족 고유(trail 30개 전제) |
| λ | 옮기지 않음 | 정의를 이번에 다시 확인하지 못했다 |

## E. 열 글자 (46183 → 46173)

공통 장부(증명, Lean `ledger`): P개 조각의 경로에서 `L = 35288 + N − Σc(절단) + Σw(이음) = 46085 + Q + J`. 상수 차이는 없다.

| 항 | 구 46183 | 공개 46173 | 차 |
|---|---|---|---|
| 선택 비용 Q | 48 (보행 (4666)⁴ 6개 × 8) | 64 (W27 4개 × 16) | **−16** |
| trail 수 / 행 없는 loop | 30 / 24 | 16 / 12 | |
| 개방 비용 Σ(3 − c) | 13 (조각 31개 중 13개가 c = 2) | 3 | **+10** |
| 이음 수 | 30 | 15 | **+15** (이음마다 1) |
| 이음의 초과 Σ(w − 3) − (이음 수) | 37 − 30 = 7 | 21 − 15 = 6 | **+1** |
| J | 50 | 24 | +26 |
| 길이 | 46,183 | 46,173 | **10** |

* 두 줄 모두 단어에서 직접 계산했다(`certs/ledger_*.json`). 구 단어는 P = 31(trail 22가 두 조각)이다.
* 뜻: 공개 선택은 행에 16글자를 더 쓰고 trail을 14개 줄인다. 구 가족에서는 이음 하나가 평균 1.23, 개방이 0.42글자였다.

## F. 27-loop 보행

`certs/walk_algebra.json`, `certs/walk_rows_*.json`. 상태 x는 6글자 배열, 행 v는 자리 치환 π_v이다.

| | W27 (공개) | A (구) |
|---|---|---|
| 행 낱말 | 266646664666466466646664666 | 4666466646664666 |
| 행 수, Q, loop당 비용 | 27, 16, 0.593 | 16, 8, 0.5 |
| 생성원 | π₂(순환형 4·2, 위수 4), π₄·π₆(5-순환) | π₄, π₆ |
| 곱 치환 | 항등(27행 뒤에 처음 닫힘, 상태 27개 모두 다름) | 항등; 구획 4666의 곱은 4·2형, 위수 4 |
| port 순열(한 바퀴) | 5-순환 → trail 하나, 주기 5바퀴 | 5-순환 → trail 하나 |
| 낱말의 회전 대칭 | 없음(뒤집으면 회전과 같음) | 4, 8, 12칸 이동 |
| 글자 재표기 고정군 | 자명 | 위수 4 (Round R의 "168 이동"과 같다) |
| run 수, R | 1,134, 10,384 | 672, 6,152 |

* π₂, π₄, π₆이 생성하는 군은 A₆(위수 360)이다. π₄, π₆만으로도 같다.
* 공개 선택의 고정군은 Klein 4군 {012345, 015432, 102435, 105342}이고 네 W27 사본 위에서 단순 추이적이다.
* **판정(증명)**: W27은 A와 동치가 아니다. 행 수와 trail 길이가 다르고 대칭군의 위수가 다르다. 27은 16의 배수가 아니므로 W27의 loop 집합을 A 보행들로 다시 나눌 수도 없다. 같은 틀(같은 생성원, 같은 완성 규칙)의 **다른 보행 유형**이다. D trail은 φ trail과 같은 유형이다.

## G. 무게 2 개방 세 개 (46174 → 46173)

README를 옮기지 않고 두 계획에서 다시 계산했다(`certs/plan_ledgers.json`). 바뀐 것은 네 W trail의 개방과 덩이의 순서이다. 무게 2 개방은 셋(14, 15, 13)이고 trail 12는 다른 무게 3 자리로 옮겼다.

| trail | 옛 개방(run, c) | 새 개방(run, c) | 옛 앞 / 뒤 | 옛 이음 비용 (앞, 뒤) | 새 앞 / 뒤 | 새 이음 비용 (앞, 뒤) |
|---|---|---|---|---|---|---|
| 12 | 8946 (977, 3) | 9422 (1029, 3) | 13 / 끝 | 2, — | 2 / 14 | 2, 2 |
| 14 | 4157 (454, 3) | **6538 (714, 2)** | 15 / 6 | 3, 2 | 12 / 15 | 2, 0 |
| 15 | 128 (14, 3) | **8616 (941, 2)** | 5 / 14 | 2, 3 | 14 / 13 | 0, 2 |
| 13 | 3204 (350, 3) | **3415 (373, 2)** | 7 / 12 | 2, 2 | 15 / 1 | 2, 1 |

* 순서: 옛 `[10,0,2][3,4,5] 15 14 [6,8,9][1,11,7] 13 12`, 새 `[3,4,5][10,0,2] 12 14 15 13 [1,11,7][6,8,9]`.
* 덩이 밖 이음 7개의 비용: 옛 3, 2, 3, 2, 3, 2, 2 = 17, 새 3, 2, 2, 0, 2, 1, 3 = 13. 덩이 안 8개는 둘 다 8이다.
* **개방 +3, 이음 25 → 21 (−4), 합 −1** (Lean `rephasing`). 공개 설명과 일치한다.

## H. Round R/S 정리의 이전

`certs/transfer_public.json`, `certs/ladders_public.json`(같은 프로그램을 구 가족에도 돌려 비교: `transfer_old.json`).

| 항목 | 공개 선택에서 | 근거 |
|---|---|---|
| Monge 4점 부등식 (S0) | **그대로 성립** | 임의 문자열의 Lean 정리. 표본 696만 개에서 위반 0 |
| 무게 1 결합 없음 | 성립 | 전수(계산 증명서) |
| 자연이 아닌 무게 2 결합 = 감싸기뿐 | 성립: 588개 = 완전 사슬 588개 | 전수 |
| trail 사이 e ≥ 0 | 성립(최소 0, 0인 쌍 2,336개) | 전수 |
| trail 안 도약 E′ ≥ −1, −1은 감싸기뿐 | 성립(−1이 588개) | 전수 |
| trail 사이 무게 3 결합은 모두 내부 run → mid run | 성립(1,512개) | 전수 |
| 건너뛰기 무게 3 + k (k ≤ 4) | 성립(588 / 420 / 276 / 144, 위반 0); k = 5는 D trail에서만 생기고 감싸기가 된다 | 전수 |
| 사다리 보조정리 (m = 2, 4, 6) | 성립(최대 −5, −13, −21) | 전수 |
| **정리 S1 (감싸기 없는 경로 → 괄호 나무)** | **번역 후 성립** | 증명이 쓰는 사실이 위의 것뿐이다. 환원기 종단 시험은 새 선택에서 돌리지 않았다 |
| 정리 S2 (건너뛰기 순환), S3 (틈 우회) | 번역 후 성립 | 건너뛰기 법칙과 Monge만 쓴다 |
| χ ≥ 0, Σχ = J | 단일 조각 방문에서는 e ≥ 0에서 바로 나온다. 다조각 방문의 χ ≥ 0(중점 퍼텐셜 보조정리 Q3)은 **다시 증명하지 않았다** | 국소 조건 하나만 확인: trail 안 무게 3으로 mid run에 드는 결합 5,768개(구 5,568개) |
| χ = 0 회전 분류 (R4) | 확인하지 않음 | |
| 단일 방문 지배, κ·slack 표 (R9, R10) | **뜻이 없음**(표가 trail 30개 가족의 것). 새 선택에서 V = P = 16은 정확 DP가 직접 답한다 | §I |
| 괄호 수 상한 c′ ≤ 8, 틈 닻 괄호 (S4) | 가족 고유. 대신 새 선택의 괄호 나무 하한을 직접 계산했다 | §J |

## I. 고정 선택의 단일 개방 최적 (정확)

* 문제: 16개 trail을 각각 한 조각(순환 단어의 연속 호)으로 쓰고 임의 순서로 최대 겹침으로 잇는다. 호는 그 trail의 모든 순열 창을 담아야 한다(같은 trail에 한 번 더 나오는 창은 뺄 수 있다).
  * 호는 **40,488개**: 비용 0(무게 3 절단) 840, 비용 1(무게 2 절단) 4,312, 비용 2(클래스 안 절단) 35,336. 앞의 둘은 외부 도구의 수와 같다.
  * 길이 = 46149 + J, J = Σ호 비용 + Σ(5 − 겹침), 겹침은 7까지 허용.
  * 범위 밖: 한 trail이 버린 순열을 다른 두 조각의 이음매가 만들어 주는 경우.
* 문턱: 46172 ⇔ **J ≤ 23** (Lean `record_threshold`). e 꼴로는 Σe + (3 − c₁) + (P − 16) ≤ 8.
* 검사기 A `rT/csrc/hk_exact.c`: (trail 집합, 마지막 호)의 전진 Held–Karp, 겹침은 접두 부호 표로 처리.
* 검사기 B `rT/src/hk_check_b.py`: 호를 따로 열거하고(호의 끝에서 전진), **역방향** DP를 numpy로 한다. A와 코드·열거·방향을 공유하지 않는다.

| 모형 | 호 | A | B |
|---|---|---|---|
| 외부 도구 모형(비용 ≤ 1, 겹침 ≤ 5) | 5,152 | **24** | **24** |
| 비용 ≤ 1, 겹침 ≤ 7 | 5,152 | 24 | — |
| **전체(비용 ≤ 2, 겹침 ≤ 7)** | 40,488 | **24** (211초) | **24** (124초, 상태 1.33×10⁹) |
| 변이: 무게 3 개방만 | 840 | 25 | 25 |
| 심은 증인: 한 이음을 1 / 0 / −1로 강제 | 5,152 | 23 / 22 / 21 | 23 / 22 / 21 |

* B는 두 공개 계획을 같은 표에서 25와 24로 평가한다.
* **결과(계산 증명서).** 이 선택의 단일 개방 최적은 J = 24, 길이 46173이다. ≤ 46172는 없다. 무게 3 개방만 쓰면 46174가 최적이다(Halfar의 단어).
* 최적 끝 호는 4개이다. A의 역추적 증인은 공개 단어와 다른 46173 단어이고(sha256 `a16c9483…`), 검사기를 통과했다(`dp_witness_46173.txt`). 새 기록은 아니다.

## J. 다중 개방 (공개 선택)

* **괄호 나무 하한(계산 증명서)**: `rT/csrc/cyc_tree.c`, `rT/src/tree_bound.py`. PATH[M] = M의 trail을 지나는 경로의 최소, CYC[U] = U의 trail을 도는 닫힌 순환의 최소(run 수준 호 5,152개). trail t가 구성원 B의 괄호를 달면 정확히 CYC[B ∪ {t}]가 더해진다(둘째 절단과 이음 |B| + 1개).
  * `J(나무) ≥ PATH[M] + Σ CYC[B_i ∪ {t_i}]`. 숙주는 괄호 밖의 아무 trail로 완화하고 16개 trail의 분할 위에서 최소를 구했다.
  * 닫힌 순환의 최소 비용: 크기 2, 3은 5, 크기 4는 6, 크기 5는 9, …, 크기 16은 28.
  * **괄호가 하나라도 있으면 J ≥ 26 (길이 ≥ 46175).** 괄호가 없으면 24(§I).
  * 확인: PATH[전체] = 24. 크기 2, 3인 집합 680개 전부에서 PATH와 CYC를 최소-합 행렬 곱으로 따로 계산해 불일치 0. 크기 4 이상의 CYC는 구현이 하나이다.
* **따름(증명 + 계산 증명서)**: 정리 S1이 이 선택에서 성립하므로(§H), 감싸기를 쓰지 않는 run 수준 경로는 조각·방문 수와 상관없이 J ≥ 24이다. 등호는 단일 개방에서만 나온다.
* **구간 재배치 전수(계산 증명서)**: 46173 경로의 모든 3-교환 재배치 21,337,343,160개를 검사했다(`or3opt.c`). 개선 0, 중립 2. A의 증인 단어에서도 같다. 이 이웃에는 감싸기를 쓰는 경로도 들어 있다.
* **열린 것**: 감싸기 588개를 쓰는 경로 가운데 S2·S3으로 지워지지 않는 것(틈 절단, 가벼운 이웃, D trail의 사슬 5개 이상 회전), 그리고 다중 개방에서 클래스 안 절단.
* 새 전하 체계: 이 선택에서는 J 자체를 쓴다. `J = (P − 1) + (3 − c₁) + Σe`, e ≥ 0(전수). 구 G·χ의 예산 수치(49, 29)는 가져오지 않았다.

## K. 새 구성

≤ 46172 단어는 없다. 얻은 것은 길이 46173인 다른 단어 하나뿐이다(§I).

## L. 하한

* `proofs/lean/n8_46134/`의 구조를 읽었다: 정리 D(커널) + 탐색 방정식 3개(native_decide). Lean 4.31·Mathlib 빌드는 하지 않았다.
* 산술 단계를 두 가지로 재현했다.
  * Lean(4.22 core): `d8_arith`를 omega로 다시 증명했다(가설 `Tri`가 세 방정식의 내용이다).
  * 열거(`d8_cells.py`, `certs/lower_bound/d8_cells.json`): 덮개·구멍·두 직선만으로는 46132까지 칸이 없고 **46133에 칸 3개**가 남는다(R = 766, 구멍 322, X + J = 2, F = 0). 구역 명제 (H3)이 이 셋을 지운다. **46133 → 46134를 주는 유한 장애물은 (H3), 곧 `zoneSearch`이다**(Lean `d8_lines_only_cell`).
* **46135는 얻지 못했다.** 같은 산술에서 46134에는 칸 1,435개가 남는다. 직선 하나나 구역 명제 하나로 지울 수 있는 모양이 아니다. Round R/S의 도구(Monge, 환원)는 trail 가족 안의 경로를 다루므로 이 사슬 모형에 바로 쓰이지 않는다. 다리를 증명하지 못했다.

## M. 증명서와 검사기

| 주장 | 종류 | 검사기 A | 검사기 B / 변이 |
|---|---|---|---|
| 46173·46174 단어 | 검증된 구성 | 선택에서 재구성(바이트 일치) | 창 집합, Lehmer 순위, 클래스 구조, C 표 |
| 공통 장부, Q = 48 / 64 | 증명(Lean) + 계산 | `word_ledger.py` (단어 7개) | `plan_ledger.py` (계획에서) |
| 단일 개방 최적 24 | 계산 증명서 | `hk_exact.c` | `hk_check_b.py`; 심은 이음 3종, 변이 1종 일치 |
| 괄호 나무 ≥ 26 | 계산 증명서 | `cyc_tree.c` + `tree_bound.py` | 크기 2·3 전수 대조; 그 밖은 구현 하나 |
| run 수준 사실, 사다리 | 계산 증명서 | `transfer_tests.py`, `ladders_public.py` | 구 가족에서 Round S의 수치와 같은 꼴(감싸기 600, 위반 0) |
| 보행 대수 | 계산 | `walk_algebra.py` | trail에서 읽은 행 낱말(`walk_rows.py`)과 선택 파일이 일치 |
| 3-교환 전수 | 계산 증명서 | `or3opt.c` | 없음 |
| 하한 산술 | 증명(Lean) | `RoundT.lean` | `d8_cells.py` |

* 파일: `rT/certs/`(검증·장부·이전), `rT/certs/fixed_selection/`(호 목록 `options.txt.gz` sha256 `3f0114bf…`, 표 `path_cyc_tables.bin.gz` sha256 `90c0d94b…`(풀었을 때), 검사기 출력), `rT/certs/lower_bound/`.

## N. Lean

`rT/lean/RoundT.lean`, Lean 4.22.0 core. 종료 코드 0, sorry·admit·사용자 공리 없음(`certs/lean_axioms_RoundT.txt`).

```
'ledger' depends on axioms: [propext, Quot.sound]
'ledger_e' depends on axioms: [propext, Quot.sound]
'record_threshold' depends on axioms: [propext, Quot.sound]
'record_threshold_e' depends on axioms: [propext, Quot.sound]
'ten_letters' does not depend on any axioms
'rephasing' does not depend on any axioms
'tree_bound' depends on axioms: [propext, Quot.sound]
'd8_arith' depends on axioms: [propext, Quot.sound]
'd8_lines_only_cell' depends on axioms: [propext, Quot.sound]
```

* 형식화한 것: 장부 항등식(목록 꼴), e 꼴, 문턱 J ≤ 23, 열 글자와 +3/−4의 산술, 나무 하한의 덧셈, 정리 D의 n = 8 산술.
* 형식화하지 않은 것: 단어 검증, DP의 건전성, S1의 조합 논증, 탐색.

## 하지 못한 것 (지시 항목별)

* §16 선택 바꾸기, §17 결합 하한: 손대지 못했다. §E의 장부(Q와 J의 교환 비율)만 있다.
* §18: Lean 재빌드 없음. §19: +1 없음.
* §10: 다조각 방문의 χ ≥ 0과 회전 분류는 새 선택에서 다시 증명하지 않았다.
* §14: 감싸기를 쓰는 다중 개방은 열려 있다.

## 부록. 재현

    X=rT/external/tholsh_46173
    python3 -I rT/src/build_from_selection.py $X/selection.txt $X/base.tsv $X/solution.plan out.txt --base $X/base.txt
    python3 -I rT/src/check_word.py out.txt;  gcc -O2 -o check_word rT/csrc/check_word.c && ./check_word out.txt
    python3 -I rT/src/plan_ledger.py $X/selection.txt $X/base.tsv $X/base.txt $X/reference.plan $X/solution.plan ledgers.json
    python3 -I rT/src/word_ledger.py $X/solution.txt new $X/selection.txt $X/base.tsv $X/base.txt a.json
    python3 -I rT/src/word_ledger.py rQ/records/superperm8_46183.txt old rM/certs/family_46187.json b.json
    python3 -I rT/src/options.py $X/selection.txt $X/base.tsv $X/base.txt options.txt options.json
    gcc -O3 -march=native -fopenmp -o hk_exact rT/csrc/hk_exact.c;  MAXCOST=2 OVCAP=7 ./hk_exact options.txt A.json     # ~3.5 min, 2.7 GB
    python3 -I rT/src/hk_check_b.py $X/selection.txt $X/base.tsv $X/base.txt B.json --plans $X/reference.plan $X/solution.plan   # ~2 min
    gcc -O3 -march=native -fopenmp -o cyc_tree rT/csrc/cyc_tree.c;  MAXCOST=1 ./cyc_tree options.txt cyc.bin              # ~30 s
    python3 -I rT/src/tree_bound.py cyc.bin tree.json;  python3 -I rT/src/cyc_spotcheck.py options.txt cyc.bin spot.json
    python3 -I rT/src/transfer_tests.py new $X/selection.txt $X/base.tsv $X/base.txt t.json
    python3 -I rT/src/ladders_public.py new $X/selection.txt $X/base.tsv $X/base.txt l.json
    python3 -I rT/src/word_to_runs.py $X/solution.txt runs.txt;  gcc -O3 -march=native -fopenmp -o or3opt rT/csrc/or3opt.c && ./or3opt runs.txt o.json
    python3 -I rT/src/walk_rows.py new $X/selection.txt $X/base.tsv $X/base.txt w.json;  python3 -I rT/src/walk_algebra.py $X/selection.txt rT/certs/walk_rows_old_family.json alg.json
    python3 -I rT/src/d8_cells.py cells.json;  lean rT/lean/RoundT.lean

판정: 고정 선택은 **단일 개방의 뜻에서** 정확하다(§12–13의 물음). 다중 개방은 감싸기 없는 경로까지만 닫혔고, 전역 L(8)은 열려 있다.

**N8_46173_SELECTION_EXACT**
