# Branch transport map (라운드 22)

산출: `outputs/rr_branch_transport.json`. completion search 없음.

## 10. 보존/변화 좌표

\(\tau: Q_4 \to Q_0\)가 보존해야 할 것과 바뀌는 것:

| 보존 | 변화 |
|---|---|
| `E`/`F` symbolic action | \(O_*\): 1 → 120 |
| preparation parity(\(\vert P\vert\) 짝수, 양 분기 공통) | tail \(T_\ell\): 빈 단어 → `Xh` |
| completer가 \(O_*\)를 target한다는 요구 | completer 착지 phase: 4 → 0 |
| \(\Phi(R_2)=0\) (라운드21에서 \(\ell\)-무관하게 손증명) | completer→R2 거리: 1 → 2 |
| automaton 상태 수(양쪽 26) | `Rh` 가용성: 있음 → 없음 |

## 판정

> **명시적인 state-to-state 전단사는 구성하지 못했다 — 미완료.**

현재 확립된 것은 **불변량 수준의 대응**뿐이다: 두 분기의 automaton이
같은 상태 수(26)를 갖고, `E`/`F` 전이가 같은 방식으로 작용하며,
Rh-free 언어가 일치한다. 그러나 이는 **transport map의 존재를
시사할 뿐 구성하지 않는다.**

특히 `RR_RH_FREE_SUBLANGUAGE.md`의 **Inclusion 2**(ell=4의 Rh-free
단어가 ell=0 boundary에서도 실현 가능)를 일반적으로 증명하려면
바로 이 map이 필요한데, 그것이 없으므로 Inclusion 2는 관측 등급에
머문다.

**성공 기준 4 평가: 미달성.** 좌표별 대응표는 얻었으나 map 자체는
구성하지 못했다.
