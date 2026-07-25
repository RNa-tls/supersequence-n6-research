# Branch transport map — 상태 수준에서는 불가능 (라운드 23)

산출: `src/build_rr_branch_transport.py` -> `outputs/rr_branch_transport_map.json`.

## 13. Abandonment root의 정확한 구조

| ell | \(O_*\) | visited | touched hex | O | endpoint (orbit,phase) |
|---:|---:|---:|---:|---:|---|
| 0 | 120 | **2** | 2 | 2 | (120, 1) |
| 1 | 33 | **3** | 2 | 2 | (33, 2) |
| 2 | 9 | **4** | 2 | 2 | (9, 3) |
| 3 | 3 | **5** | 2 | 2 | (3, 4) |
| 4 | 1 | **6** | 2 | 2 | (1, 0) |

두 개의 깔끔한 항등식(손증명):

- \(\mathrm{visited}(\mathrm{root}_\ell) = \ell + 2\)
  (hub 위치 0..\(\ell\) 그리고 abandonment 표적)
- **abandonment 표적은 언제나 \(O_*\) 자신이며 phase는
  \((\ell+1)\bmod 5\)** — 즉 abandonment는 \(O_*\)를 hub 바깥의
  다른 phase에서 먼저 연다.

## 12-16. 불가능성 (손증명)

> **정리**: exact legality를 보존하는 상태 수준 전단사
> \(\tau: Q_4 \to Q_0\)는 **존재하지 않는다**.
>
> **증명**: 이후 모든 joint의 legality는 "표적 permutation이 이미
> 방문됐는가"로 결정되므로, legality를 보존하는 map은 방문 집합의
> 크기를 보존해야 한다. 그러나
> \(\mathrm{visited}(\mathrm{root}_4)=6 \ne 2=\mathrm{visited}(\mathrm{root}_0)\).
> ∎

**따라서 §12-16이 제안한 경로는 닫혔다 — 반증됨.**

## 결과: 역포함은 여전히 미완료

라운드22는 \(\mathcal P_4\cap\{E,F\}^*\subseteq\mathcal P_0\)를
"transport map 부재로 미완료"라 남겼다. 이번 라운드는 **그 경로가
원리적으로 불가능함**을 보였다 — 다른 논증이 필요하다.

살아남는 것은 **symbolic/quotient 수준의 대응**뿐이다: 두 분기가
같은 알파벳, 같은 \(|P|\)-짝수 제약, 같은 "completer가 \(O_*\)를
target" 요구, \(\ell\)-무관한 \(\Phi=0\)을 공유한다. 그러나 이는
언어 동일성을 **시사할 뿐 증명하지 않는다.**

**성공 기준 3 평가: 미달성(불가능성 증명으로 대체).**
**성공 기준 4(언어 동일성) 평가: 미달성** — 관측 등급 유지.
