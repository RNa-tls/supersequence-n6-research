# Target B capacity survivor 감사 (라운드 31 Part A)

산출: `src/analyze_rr_target_b_survivors.py` ->
`outputs/rr_target_b_survivors.json`. **long six에는 DFS를 돌리지
않았다** — 이미 손증명으로 닫혔고 corpus에 기록용으로만 실었다.
N=0 checkpoint 미접촉, 전역 NR6 search 없음.

## 1. Capacity 정리의 더 깨끗한 유도

continuation의 entry port \(p_0,\dots,p_B\)를 **orbit segment**로
쪼갠다(orbit-보존 edge의 극대 run 하나가 segment 하나).

- segment 수 \(\le m+1\) (\(m=\) orbit-**변경** edge 수)
- 한 segment는 자기 orbit의 port를 **최대 5개** 쓴다(orbit의 port가 5개)

\[
B+1 \;\le\; 5(m+1)
\quad\Longleftrightarrow\quad
B \le 5m+4,
\qquad m \le O_{\mathrm{cap}}+R_{\mathrm{cap}} .
\]

> 이 유도는 \(\Phi=0\)과 생성원 구조만 쓴다 — **\(\ell=4\)를 쓰지
> 않으므로 \(\ell=0\) 경계에도 적용된다.**

## 2. 전체 corpus와 정확한 survivor 집합

**단위 주의**: 아래 행은 **boundary state**이지 word가 아니다.

| class | \(\ell\) | \(P_{\mathrm{core}}\) | \(B\) | \(O_{\mathrm{cap}}\) | bound | margin \(M\) | \(O\) | \(D\) | 판정 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| long | 4 | 7 | 110 | 19 | 104 | **−6** | 6 | 19 | **CAPACITY_IMPOSSIBLE** |
| long | 4 | 7 | 110 | 19 | 104 | **−6** | 6 | 19 | **CAPACITY_IMPOSSIBLE** |
| long | 4 | 10 | 107 | 17 | 94 | **−13** | 8 | 26 | **CAPACITY_IMPOSSIBLE** (×4) |
| short | 0 | 2 | 114 | 23 | 124 | **+10** | 2 | 3 | CAPACITY_SURVIVOR |
| short | 0 | 4 | 112 | 21 | 114 | **+2** | 4 | 11 | CAPACITY_SURVIVOR |
| short | 0 | 4 | 112 | 20 | 109 | **−3** | 5 | 16 | **CAPACITY_IMPOSSIBLE** |
| short | 4 | 2 | 115 | 23 | 124 | **+9** | 2 | 4 | CAPACITY_SURVIVOR (×3) |
| short | 4 | 4 | 113 | 21 | 114 | **+1** | 4 | 12 | CAPACITY_SURVIVOR |
| short | 4 | 4 | 113 | 20 | 109 | **−4** | 5 | 17 | **CAPACITY_IMPOSSIBLE** |
| short | 4 | 6 | 111 | 22 | 119 | **+8** | 3 | 5 | CAPACITY_SURVIVOR (×3) |
| short | 4 | 6 | 111 | 18 | 99 | **−12** | 7 | 25 | **CAPACITY_IMPOSSIBLE** |

**boundary state 18개 = survivor 9 + impossible 9.**
survivor는 **전부 short**이며, canonical state hash가 **9개 전부 다르다**
(축약 불가). legal outgoing signature는 **2종류**뿐이다.

## 3. Margin 분포

| \(M\) | 0 | 1–4 | ≥5 |
|---|---:|---:|---:|
| survivor 수 | **0** | **2** (\(M=1,2\)) | **7** |

전체 히스토그램 `{1:1, 2:1, 8:3, 9:3, 10:1}`.

**equality case(\(M=0\))는 존재하지 않는다.** 가장 빠듯한 것이
\(M=1\)이다.

## 4. Equality-case 정리 (§4)

\(M=0\)이면 부등식 \(B+1\le5(m+1)\)이 등식이므로 **모든 segment가
정확히 5 port를 써야** 한다. 즉:

1. 갱신 사건이 \(O_{\mathrm{cap}}+R_{\mathrm{cap}}\)개 **전부** 사용되고,
2. 각 segment의 보존 run 길이가 **정확히 4**이며,
3. collision·낭비 전이가 **0**이고,
4. 각 orbit의 **다섯 port 전부**가 실제로 쓰인다.

> **따름**: \(M=0\)이면 continuation의 symbolic pattern이 완전히
> 강제된다 — 길이 4 보존 block과 갱신 edge가 번갈아 나오는 형태
> 하나뿐이다. 그런데 길이 4 block은 **3종류뿐**이고 그중 \(R\) 예산
> 안에서 쓸 수 있는 것은 **`EEEE` 하나**다
> (`RR_TARGET_B_SATURATING_BLOCKS.md`).

현재 corpus에 \(M=0\)이 없으므로 이 정리는 **적용 대상이 없다**.
그러나 \(M\)이 작은 두 survivor(\(M=1,2\))는 **비효율을 각각 1개, 2개
까지만** 허용한다.

## 5. Near-equality defect ledger (§5)

각 future edge의 비효율은 capacity를 **최소 1** 줄인다:

| 비효율 | capacity 손실 |
|---|---:|
| 보존 run 길이 \(<4\) | \(4-\text{길이}\) |
| opening이 unusable port에 착지 | ≥1 |
| 이미 방문된 phase | ≥1 |
| component-incompatible opening | ≥1 |
| terminal suffix mismatch | ≥1 |
| R 낭비 | ≥1 |

**증명**: 각 항목은 segment가 쓸 수 있는 port 수를 5보다 작게 만들고,
\(B+1\le\sum(\text{segment당 port})\)의 우변을 그만큼 줄인다. ∎

> survivor가 허용할 수 있는 **총 비효율 \(\le M\)**.
> \(M=1\)인 survivor는 continuation 전체에서 비효율을 **한 번**만
> 허용한다 — 극히 빠듯하다.

**등급**: capacity 정리 **손증명**, survivor 집합 **safe capacity bound
+ exact replay**, equality 정리 **손증명**(적용 대상 없음),
defect ledger **손증명**.
