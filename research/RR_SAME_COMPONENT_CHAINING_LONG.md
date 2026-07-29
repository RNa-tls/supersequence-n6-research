# same-component ⟹ chaining — 부분 손증명 (라운드 29 §9)

## 1. 먼저 정정: \(\ell=4\)에서 same-component는 제약이 아니다

`RR_TERMINAL_NORMAL_FORM_PROOF.md`의 **T8(손증명)**:
orbit 0은 hex0 위치 0에 port를 갖고 초기 상태에서 방문됐으며,
completer는 hex0 위치 5(orbit 1의 port)를 방문한다. 따라서 두 orbit은
hexagon 0을 통해 **자동으로 한 component**에 있다.

> 그러므로 \(\ell=4\)에서 "same-component ⟹ chaining"의 **전제는
> \(C\) 발동 이후 공허하게 참**이다. chaining이 참이라면 그 이유는
> same-component가 **아니다**. 이 구분은 정의 재진술과 구조적 증명을
> 가르는 지점이며, 과제 §9가 요구한 그대로 명시한다.

따라서 실제로 증명해야 할 것은:

> **(CH)** \(\ell=4\) RR word의 \(R_2\) 경계에서
> \(R_1\)의 target orbit은 1이다.

(\(R_2\) source orbit \(=1\)은 T5로 이미 손증명이다.)

## 2. 손증명되는 경우 — \(C\)가 R일 때

> **Lemma CH1 (손증명)**: hub completer \(C\) 자신이 R 사건이면
> chaining이 성립한다.
>
> **증명**: \(R_2\)는 \(C\)보다 **뒤에** 있다(\(R_2\)는 word의 마지막
> 사건이고 \(C\)는 그 앞의 hub 착지 edge다). RR word의 R은 정확히 2개이므로
> \(C\)가 R이면 \(C=R_1\)이다. T2에 의해 \(C\)의 target은 \((1,4)\)이므로
> \(R_1\)의 target orbit은 1이다. T5의 \(R_2\) source orbit \(=1\)과
> 일치하므로 chaining. ∎

**적용 범위 (exact replay)**: \(\ell=4\)의 15개 사례 중 \(C\)가 R인 것:

| \(C\)의 조인트 | kind | 사례 수 |
|---|---|---:|
| `w3:120` | R | 1 |
| `w3:201` | R | 2 |
| `w3:210` | R | 2 |
| **소계 — CH1 적용** | | **5** |
| `w2:10` | Z2 | 4 (역사적) + 6 (긴 witness) = **10** |

> **15개 중 5개가 CH1으로 손증명된다.** 나머지 10개는 미완료.

## 3. \(C\)가 zero-charge일 때 — 어디까지 가는가

\(C=\)`w2:10`이면 \(\ell=5\) 합성이 정확히 \(E\)이므로(라운드26 정리)
\(C\)의 target \((1,4)\)는 **직전 joint target \(\circ\,E\)** 이다.
즉 **직전 joint의 target은 \((1,3)\)** — orbit 1 안이다.

그 \((1,3)\)에 어떻게 도달했는가:

1. **\(E\) 걸음** (orbit 1 안에서 \((1,2)\)로부터), 또는
2. **orbit을 바꾸는 joint** — `w3:201`/`w3:210`. 이때 그것은
   **R 아니면 F**인데, **F일 수 없다**: F는 새 orbit을 여는데 orbit 1은
   abandonment가 이미 열었다(손증명). 따라서 **R**이다.

경우 2이면 그 R은 orbit 1을 target하므로, 그것이 \(R_1\)이면 chaining이
성립한다. 경우 1이면 한 칸 뒤로 물러나 같은 분석을 반복한다.

**재귀가 멈추는 곳**: \(E\) 걸음의 사슬을 거슬러 올라가면 orbit 1로의
**첫 진입**에 도달한다. 그것은 abandonment의 target \((1,0)\)일 수도 있다.

> **막히는 지점 (정확히)**: 걸음이 \((1,0)\)에서 순수하게 \(E\) 걸음만으로
> \((1,4)\)까지 갈 수 있다면, \(P_{\mathrm{core}}\cup\{C\}\) 안에
> orbit 1을 target하는 R이 **하나도 없고**, 그러면 \(R_1\)의 target이
> orbit 1이라는 근거가 사라진다.

이 시나리오를 배제하려면 "\(\#R_{\le C}=1\)"(15/15 관측)이나 그에 준하는
사실이 필요한데, 그것 자체가 관측이다. **따라서 CH는 미완료.**

## 4. 긴 preparation family에서의 확인

과제가 요구한 대로 새 long family를 포함해 검사했다.

| family | \(P_{\mathrm{core}}\) | 사례 | \(R_1\) target | \(R_2\) source | chaining |
|---|---:|---:|---:|---:|:---:|
| 역사적 \(\ell=4\) | 2, 4, 6 | 9 | 1 | 1 | **9/9** |
| 긴 witness (Class I) | 7 | 2 | 1 | 1 | **2/2** |
| 긴 witness (Class II) | 10 | 4 | 1 | 1 | **4/4** |

> **preparation 길이 2~10에서 예외 0.** 그리고 긴 family는
> parity 구조를 깨뜨리면서도(\(\#Z_{\to O_*}\) 홀수, \(\#R_{\text{odd-}\delta}=1\))
> **chaining은 유지한다.**

이것이 과제가 지적한 핵심이다: **chaining 증명은 preparation parity에
의존해서는 안 된다.** CH1은 실제로 parity를 전혀 쓰지 않는다 — R 개수와
T2만 쓴다.

## 5. 남은 형태

증명해야 할 것이 정확히 하나로 좁혀졌다:

> **(CH2, 미완료)**: \(\ell=4\) RR word에서 \(C\)가 zero-charge일 때,
> \(P_{\mathrm{core}}\) 안에 orbit 1을 target하는 R이 존재한다.

동치 형태: \(P_{\mathrm{core}}\cup\{C\}\) 안의 \(O_*\) 걸음이
**전부 \(E\)일 수는 없다.** 15개 사례에서는 항상 R 걸음이 최소 하나
있었다(\(\#R\) 걸음 \(\ge1\)). 그러나 그것을 강제하는 논증은 없다.

**증명 등급**: CH1 **손증명** (15개 중 5개 적용),
CH2 **미완료**, 전체 chaining **bounded observation (15/15)**,
same-component 전제의 공허성 **손증명**.
