# 순서·phase 기반 parity 분석 (라운드 25)

산출: `src/analyze_rr_ordered_phase_actions.py` ->
`outputs/rr_ordered_event_words.json`. completion search 없음.

## 4. 순서 있는 군 방정식 (비가법적 정식화)

모든 preparation edge는 `ell=5`로 강제되므로 각각 고정 생성원
\(g_j=\Sigma^5\cdot a_j\)의 우측 곱이다. 따라서 hub 위치 \(j\)에
착지한다는 것은 **군 방정식**

\[
\Sigma^{\ell}\, a_2\, g_{x_1}g_{x_2}\cdots g_{x_k}\,\Sigma^{m} a_c=\Sigma^{j}
\]

이고, 생성원이 비가환이므로 **\(x_i\)의 순서에 의존**한다.
라운드24의 불가능성 정리가 "증명은 비가법적 대상을 써야 한다"고
했는데, 이것이 바로 그 대상이다.

## 2. 순서 의존성의 직접 증거 (exact counterexample)

**가법 계수가 완전히 같은데 착지 클래스가 다른 쌍이 11개** 존재한다
(`outputs/rr_same_count_opposite_order_pairs.json`). 예:

| 계수 (ell,#R,#Z,#F) | word A | 클래스 | word B | 클래스 | 최초 차이 |
|---|---|---|---|---|---:|
| (0,1,4,3) | `FFEFR` | **O\*** | `EFFFR` | far | index 0 |
| (0,0,6,3) | `EFEFEF` | ell+2 | `EFFFEE` | far | index 2 |
| (0,2,4,2) | `ERFERF` | ell+2 | `RFEFER` | far | index 0 |

> **착지 위치는 사건 계수의 함수가 아니다 — 순서의 함수다.**
> 이는 라운드24의 불가능성 정리를 실증적으로 보완한다.

## 3. O\* phase 방문 수열

\(O_*\) 착지 완성에서 \(O_*\)의 phase 방문 순서는 항상
**abandonment의 phase에서 시작해 completer가 착지하는 hub phase로
끝나며, 중간은 증가 수열**이다. 관측된 30개 수열 예:

```
[1, 0]      [1, 2, 3, 0]   [1, 2, 3, 4, 0]   [1, 2, 4, 0]
[0, 4]      [0, 2, 4]      [0, 1, 2, 3, 4]   [0, 1, 3, 4]
```

(1로 시작 = ell=0 분기, 0으로 시작 = ell=4 분기.)

## 핵심 측정 — 착지 클래스별 zero-charge parity

| 착지 클래스 | 완성 수 | \(\#Z\) 짝수 | \(\#Z\) 홀수 |
|---|---:|---:|---:|
| \(j=\ell+1\) (\(O_*\)) | 95 | **95** | **0** |
| \(j=\ell+2\) | 48 | **48** | **0** |
| \(j\ge\ell+3\) | 44 | 31 | **13** |

> **\(\#Z\)의 짝수성은 가장 가까운 두 잔여 위치에서만 성립하고,
> 그보다 먼 착지에서는 깨진다** — root-local exhaustive,
> R-count 상한 없음.

**등급**: root-local exhaustive (95+48+44 완성 전수).
