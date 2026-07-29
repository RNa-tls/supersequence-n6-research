# R-free-to-C prefix와 CH2 확장 판정 (라운드 31 Part D)

산출: `src/analyze_rr_ch2_r_free_extension.py` ->
`outputs/rr_ch2_r_free_prefix.json`, `outputs/rr_ch2_extension_results.json`.

## 1. Prefix 고정 (§16) — 놀랄 만큼 단순하다

\(\ell=4\) root에서 \(\ell=5\) preparation edge만으로 \(C\)에 도달하면서
R이 **하나도 없는** 경로는 depth \(\le8\) scope에서 **정확히 하나**다:

```
A_4 : rot^4;w2:10        -> (orbit 1, phase 0)
  0 : rot^5;w2:10   E    -> (1,1)
  1 : rot^5;w2:10   E    -> (1,2)
  2 : rot^5;w2:10   E    -> (1,3)
  C : rot^5;w2:10   E    -> (1,4)   hex 0   <- hub completer
```

즉 **abandonment가 연 \((1,0)\)에서 순수 \(E\) 걸음 네 번으로
\((1,4)\)에 도달**한다. \(\ell=5\) `w2:10`이 정확히 \(E\)의 우측 곱이라는
사실(라운드26)의 가장 단순한 귀결이다.

| 항목 | 값 |
|---|---|
| \(P_{\mathrm{core}}\) | **3** (C 포함 4 edge) |
| \(O_*\) phase 열 | \(0\to1\to2\to3\to4\) |
| \(C\) 이전 R | **0** |
| post-\(C\): \(\Phi\) | **5** |
| post-\(C\): \(F_{\mathrm{def}}\)/\(N\)/\(H\) | 1 / **0** / 0 |
| post-\(C\): \(O\)/\(P\)/visited | 2 / 6 / 25 |

> 이것이 CH2를 막는 정확한 구조다. **legality만으로는
> "\(C\) 이전에 \(R_1\) target이 orbit 1"이 강제되지 않는다** —
> \(C\) 이전에 R이 아예 없을 수 있기 때문이다.

## 2. \(C\) 직후의 손분류 (§18)

post-\(C\) endpoint는 hex0 위치 5이고 rotation이 불가능하므로
**\(\ell=0\) 강제**(T4a). \(\Phi=5\)이고 어느 joint을 골라도
\(\Delta\Phi=-5\)이므로 그 다음부터 \(\Phi=0\), 즉 이후 모든
macro-edge는 \(\ell=5\)다.

| joint | legal | kind | R? | target orbit | \(\Phi\) 이후 |
|---|:---:|---|:---:|---:|---:|
| `w2:10` | 예 | Z2 | 아니오 | 0 | 0 |
| **`w3:120`** | 예 | **R** | **예** | **0** | 0 |
| `w3:201` | 예 | Z3 | 아니오 | 138 | 0 |
| `w3:210` | 예 | Z3 | 아니오 | 32 | 0 |

**네 개 전부 legal**하다. 따라서 §18이 기대한

> "\(C\) 이전 R=0이면 \(C\) 직후 forced R이 \(R_1\)이고, \(R_2\)를
> 만들 여지가 없다"

는 **강제되지 않는다** — R이 아닌 세 선택지가 살아 있고, `w3:120`을
고르면 그것이 \(R_1\)(target orbit **0**)이 된다.

**중요**: 만약 그 경로로 Target A에 도달한다면 \(R_1\) target은
orbit 0이고 \(R_2\) source가 orbit 1이면 **non-chaining** — 즉
`same-component ⟹ chaining`의 반례가 된다.

## 3. 확장 탐색 (§19–20)

post-\(C\) 상태에서 Target A 경계(두 번째 R, \(F_{\mathrm{def}}=1\),
\(H=0\), same-component)까지 root-local exact search.

| 항목 | 값 |
|---|---|
| coverage scope | \(\ell=4\) abandonment root, prefix depth ≤8, **extension depth ≤9** |
| node cap | 400,000 |
| 확장 노드 | **64,500** |
| 도달한 Target A 경계 | **0** |
| non-chaining 반례 | **0** |
| frontier 자연소진 | **아니오** |
| **판정** | **INCOMPLETE** |

> node cap에 닿지 않았고 **depth ceiling 9에서 잘렸다.**
> 이것을 absence로 읽지 않는다. 반례가 없다고 주장하지 **않는다**.

관측 하나는 기록해 둘 만하다: extension depth 9까지 **Target A 경계가
하나도 나타나지 않았다**. 짧은 witness에서는 \(C\) 이후 2 edge 만에
경계가 나왔던 것과 대조적이다. 그러나 이는 **bounded observation**이며,
\(R\) 두 개를 \(C\) 이후에 배치하려면 더 깊은 확장이 필요하다는 것을
시사할 뿐이다.

## 4. CH2 최종 상태 (§21)

| 결과 유형 | 해당 |
|---|---|
| counterexample 발견 | **아니오** |
| exhaustive absence + coverage proof | **아니오** (frontier 미소진) |
| structural proof | **아니오** |
| **incomplete** | **예 — CH2는 열린 채로 둔다** |

`same-component`가 \(\ell=4\)에서 자동이라는 사실은 이 절에서 **모순으로
사용하지 않았다**(라운드30의 경고 준수).

**CH2 현황 요약**:

- CH1(\(C\)가 R): **손증명**, 15개 중 5개.
- CH2(\(C\)가 Z2): **미완료**. 장애물이 정확히 특정됨 —
  \(C\) 이전 R이 0개인 legal prefix가 존재하며, 그 prefix가 Target A로
  확장되는지가 미판정.
- 확장 판정: **bounded incomplete** (depth ≤9).

**등급**: prefix **exact observation**, \(\ell=0\) 강제 **손증명**,
네 joint 전부 legal **exact replay**, 확장 탐색 **bounded incomplete**,
CH2 **미완료**.
