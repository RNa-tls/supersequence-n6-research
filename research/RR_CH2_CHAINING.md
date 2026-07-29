# CH2 chaining — 제안된 architecture는 **반증됨**, 문제는 열린 채 (라운드 30 Part B)

산출: `src/analyze_rr_ch2_chaining.py` -> `outputs/rr_ch2_witnesses.json`,
`outputs/rr_orbit1_opener_ledger.json`.

## 1. CH2 corpus (§12) — 10개

\(\ell=4\) same-component 경계 중 completer \(C\)가 zero-charge인 것:

| 출처 | \(P_{\mathrm{core}}\) | \(C\) | \(C\) target | \(R_1\) | \(R_1\) target | \(R_1\!\to\!C\) 거리 |
|---|---:|---|---|---|---|---:|
| 긴 witness | 7 | `rot^5;w2:10` | (1,4) | `rot^5;w3:201` | **(1,3)** | 1 |
| 긴 witness | 7 | `rot^5;w2:10` | (1,4) | `rot^5;w3:201` | **(1,3)** | 1 |
| 긴 witness | 10 | `rot^5;w2:10` | (1,4) | `rot^5;w3:210` | **(1,1)** | 3 |
| 긴 witness | 10 | `rot^5;w2:10` | (1,4) | `rot^5;w3:210` | **(1,1)** | 3 |
| 긴 witness | 10 | `rot^5;w2:10` | (1,4) | `rot^5;w3:201` | **(1,1)** | 3 |
| 긴 witness | 10 | `rot^5;w2:10` | (1,4) | `rot^5;w3:201` | **(1,1)** | 3 |
| 역사적 | 2 | `rot^5;w2:10` | (1,4) | `rot^5;w3:120` | **(1,2)** | 2 |
| 역사적 | 2 | `rot^5;w2:10` | (1,4) | `rot^5;w3:120` | **(1,3)** | 1 |
| 역사적 | 6 | `rot^5;w2:10` | (1,4) | `rot^5;w3:210` | **(1,2)** | 2 |
| 역사적 | 6 | `rot^5;w2:10` | (1,4) | `rot^5;w3:210` | **(1,3)** | 1 |

**10/10에서 \(R_1\) target orbit \(=1\)**, phase는 1·2·3으로 다양하다.
\(C\)는 **10/10 전부 `rot^5;w2:10`** 이다.

## 2. §19 architecture 판정

| Lemma | 내용 | 판정 |
|---|---|---|
| **CH2-A** | \(C\)가 Z2면 orbit 1은 \(C\) 이전에 이미 열려 있다 | **손증명** (자명) |
| **CH2-B** | terminal-compatible preparation에서 orbit 1의 최초 opener는 \(R_1\)이다 | **반증됨** |
| CH2-C | 따라서 \(R_1\) target \(=\) orbit 1 | CH2-B에 의존 — **무효** |
| 정리 | \(C\)가 Z2여도 chaining | **미완료** |

**CH2-B가 반증되는 이유** (`RR_ORBIT1_FIRST_OPENER.md` 참고):
\(\ell=4\) abandonment joint 자신이 \((1,0)\)에 착지하며
`new_orbit = True`다. 즉 **orbit 1의 최초 opener는 abandonment**이지
\(R_1\)이 아니다. 따라서 first-opener 논증으로는 chaining이 나올 수
없고, §19의 구조는 **교체돼야 한다**.

## 3. \(R_1\) target 후보 전수분류 (§13) — 그리고 진짜 장애

\(C\)가 zero-charge(`w2:10`)이면 \(\ell=5\) 합성이 정확히 \(E\)이므로

\[
C_{\text{target}}=(1,4)=(\text{직전 joint target})\circ E
\;\Longrightarrow\;
\text{직전 joint target}=(1,3).
\]

\((1,3)\)에 도달하는 방법은 둘뿐이다:

1. orbit 1 **안에서의 \(E\) 걸음** (\((1,2)\)로부터), 또는
2. **orbit을 바꾸는 joint** — 이 경우 F는 불가능(orbit 1은 이미 열림)
   이므로 **R**이다. 그 R이 \(R_1\)이면 chaining 성립.

경우 1이면 한 칸 물러나 반복한다. 재귀는 orbit 1로의 **첫 진입**에서
멈추는데, 그것이 abandonment의 \((1,0)\)이면 \(P_{\mathrm{core}}\) 안에
orbit 1을 target하는 R이 **하나도 없다**.

> **이 시나리오가 실제로 legal하다.** §4의 탐색이 그것을 찾았다.

## 4. 반례 탐색 (§18)

\(\ell=4\) root에서 \(\ell=5\) preparation edge만으로, \(C\)에 도달하는
모든 경로를 depth \(\le8\)까지 열거했다(노드 24,474).

| \((C\) 기호, \(R_1\) target\()\) | 완성 수 |
|---|---:|
| \(C=E\), \(R_1\) target \(=1\) | 6 |
| \(C=E\), **\(R_1\) 없음** | **1** |
| \(C=R\), \(R_1\) target \(=1\) | 13 |

- **\(C\)가 zero-charge이면서 \(R_1\) target \(\ne\) orbit 1인 경우: 0개.**
- 그러나 **\(R_1\)이 아예 없는 경우가 1개 존재한다** — 즉
  \(\#R_{\le C}=0\)인 completion이 legal하다. 이는 §3의 "순수 \(E\)
  경로" 시나리오가 실현됨을 뜻한다.

그런 word가 RR이 되려면 R 두 개가 모두 \(C\) 이후에 있어야 하는데,
\(C\) 직후는 \(\ell=0\)이 강제되고(T4a) 그 이후는 \(\Phi=0\)이라
\(\ell=5\)만 가능하다. 그 조합이 RR word를 이루는지는 **판정하지
않았다** — 판정하려면 completion 탐색이 필요하다.

**탐색 상태**: frontier가 depth 8에서 잘렸으므로 **bounded incomplete**.
\(P_{\mathrm{core}}\le8\) 범위에서 반례 0이라는 것 이상은 주장하지
않는다(실제 witness에는 \(P_{\mathrm{core}}=10\)도 있다).

## 5. 현재 상태

| 명제 | 등급 |
|---|---|
| CH1 (\(C\)가 R ⟹ chaining) | **손증명** — 15개 중 5개 |
| CH2-B (first-opener) | **반증됨** |
| CH2 전체 | **미완료** |
| CH2 corpus 10/10에서 \(R_1\) target \(=1\) | **exact observation** |
| \(P_{\mathrm{core}}\le8\)에서 반례 부재 | **bounded incomplete** |
| \(\#R_{\le C}=0\)인 legal completion 존재 | **exact observation** — CH2의 실제 장애 |

**다음에 필요한 것**: "\(\#R_{\le C}=0\)인 preparation은 RR word로
확장되지 않는다"를 판정하는 것. 그것이 참이면 CH2가 닫힌다.
