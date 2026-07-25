# Near/far 착지의 parity 차이 (라운드 25)

산출: `src/search_rr_far_landing_loops.py` ->
`outputs/rr_far_landing_odd_loops.json`.

## 10-11. Far 착지의 홀수 witness (exact counterexample)

\(j\ge\ell+3\) 착지에서 zero-charge 개수가 **홀수**인 완성이
**13개** 존재한다. 최소 예:

| ell | j | \(\vert P\vert\) | word | #Z | #R |
|---:|---:|---:|---|---:|---:|
| 0 | 4 | 5 | `EFRRFR` | **3** | 3 |
| 1 | 5 | 5 | `EFRRFR` | **3** | 3 |
| 0 | 5 | 5 | `FFRFFE` | **5** | 1 |

이들이 §11이 요구한 "parity를 뒤집으면서 착지를 유지하는 최소
구조"의 exact witness다.

## 12. 근접 착지에서 왜 불가능한가 — 미완료

\(O_*\)와 \(\ell+2\) 착지에서는 이런 홀수 witness가 **하나도 없다**
(95+48 = 143개 전수). 그러나 **왜 불가능한지는 규명하지 못했다.**

§12가 제시한 후보(phase overshoot, 방문 충돌, hub touch count,
endpoint mismatch, nearest residual 이중 통과, R target ancestry
파괴) 중 어느 것도 exact transition 수준의 최소 모순으로 확정하지
못했다 — **미완료.**

## 관측된 구조적 차이

- \(O_*\) 착지: zero-charge가 "\(O_*\) target 여부"로 **짝수 이분**
  된다(`RR_ZERO_CHARGE_MATCHING.md`).
- \(\ell+2\) 착지: 그 이분이 **깨지지만** \(\#Z\) 총합은 여전히 짝수.
- far 착지: 총합조차 홀수가 될 수 있다.

즉 짝수성은 근접도에 따라 **단계적으로 약해진다**. 이 단계 구조가
증명의 실마리로 보이나, 정식화하지 못했다.

**등급**: 홀수 far witness는 **exact counterexample**,
근접 착지의 불가능성은 **root-local exhaustive**(143/143), 이유는
**미완료**.
