# Target B transition universe와 \(\Phi=0\) continuation 정리 (라운드 29 §11–12)

산출: `src/analyze_rr_target_b_remaining_cost.py` ->
`outputs/rr_target_b_transition_universe.json`. **탐색 없음.**

## 1. \(\Phi=0\) continuation 정리 — 손증명

> **정리**: \(\Phi=0\)인 상태에서는 이후 **모든** admissible macro-edge가
> rotation run \(\ell=5\)를 갖는다.
>
> **증명**: (H2) \(\Delta\Phi=\ell-5\). (H3) `remaining_window_capacity_prune`가
> 참인 것은 정확히 \(\Phi<0\)일 때이므로 \(\Phi\ge0\)은 Area A 자신의
> prune이다. \(\ell<5\)이면 \(\Delta\Phi<0\)이 되어 \(\Phi<0\), 즉
> 즉시 prune된다. ∎

**적용 범위 확인**: \(\Delta\Phi=\ell-5\)는 **모든** macro-edge에 대해
성립한다(abandonment 여부, joint weight, new_orbit 여부와 무관) — 왜냐하면
\(\Delta P=1\)과 \(\Delta\text{visited}=\ell+1\)이 joint 종류에 의존하지
않기 때문이다. 순수 rotation suffix는 joint이 없으므로
\(\Delta\Phi=+1\)/rotation이다.

**따름**: \(\Phi\)는 단조 비증가가 아니다(rotation은 \(+1\)). 그러나
**macro-edge 단위로는** \(\ell\le5\)이므로 \(\Delta\Phi\le0\)이고,
따라서 **\(\Phi=0\)에 도달하면 macro-edge 단위로 영원히 \(\Phi=0\)**이다.

## 2. 여섯 post-\(R_2\) 상태의 transition universe

| # | 나가는 macro-edge | legal | legal 목록 |
|---:|---:|---:|---|
| 0 | 22 | **3** | `rot^5;w2:10`/Z2, `rot^5;w3:201`/Z3, `rot^5;w3:210`/Z3 |
| 1 | 22 | **3** | 동일 |
| 2 | 19 | **3** | 동일 |
| 3 | 21 | **3** | 동일 |
| 4 | 20 | **3** | 동일 |
| 5 | 22 | **3** | 동일 |

> **여섯 상태의 legal transition signature가 완전히 동일하다**
> (distinct signature 수 = 1).

각 edge의 전체 정보(target permutation/orbit/phase/hexagon,
\(\Delta\Phi\), \(\Delta F_{\mathrm{def}}/\Delta N/\Delta H/\Delta O\),
component 병합 여부, collision 상태)는 JSON에 있다.

**핵심 관찰**:

1. **legal한 것은 전부 \(\ell=5\)** — §1 정리의 실측 확인.
2. **`w3:120`은 legal하지 않다** — 여섯 전부에서. 즉 \(R_2\) 이후
   즉시 세 번째 R을 놓을 수 없다(Target B 정의의 "추가 R 없음"과
   무관하게 legality가 이미 막는다).
3. 세 legal edge는 **Z2 하나 + Z3 둘**이다. Z3 두 개는 새 orbit을
   여므로 \(O\)를 증가시킨다.
4. 나머지 16~19개는 전부 `F_exceeded` — \(\ell<5\)라서 abandonment가
   되기 때문이다.

## 3. Hexagon 판독 — Target B의 정확한 정규형

\(\ell=5\) macro-edge는 5회 rotation으로 **현재 hexagon을 완성**하고
joint으로 **다음 hexagon에 진입**한다. 따라서 새로 방문하는
permutation은 정확히 6개이고, **macro-edge 하나가 hexagon 하나를
완성**한다.

여섯 상태의 hexagon 인구조사:

| # | 완성 | 부분 | 미방문 | \(B=\)남은 pass start |
|---:|---:|---:|---:|---:|
| 0,1 | 9 | **1** | **110** | **110** |
| 2–5 | 12 | **1** | **107** | **107** |

> **미방문 hexagon 수 \(=B\)가 정확히 일치한다.** 부분 방문 hexagon은
> 항상 **정확히 1개**(걸음이 현재 서 있는 것)다.

따라서:

> **Target B ≡ 남은 미방문 hexagon 전부를 각각 한 번의 macro-edge로
> 완성하며 지나가는 walk** — 즉 hexagon 그래프 위의 **Hamiltonian
> 경로 문제**다. 마지막 hexagon은 순수 rotation suffix 5회로 완성된다.

이것은 Target B를 **탐색 문제에서 조합 구조 문제로 재서술**한 것이며,
이번 라운드에서 얻은 가장 유용한 재정식화다.

**증명 등급**: \(\Phi=0\) continuation 정리 **손증명**,
transition universe **exact replay**, hexagon 재서술 **손증명**
((H2)와 rotation run의 정의만 사용).
