# Preparation parity 정리 (라운드 21)

산출: `src/analyze_rr_preparation_grammar.py` -> `outputs/rr_preparation_words.json`,
`src/verify_rr_preparation_parity.py` -> `outputs/rr_preparation_parity_general.json`.
새 completion search 없음.

## 0. Depth convention 확정 (§5의 지적 반영)

라운드20의 "ell=0은 홀수 depth"는 **abandonment-root 기준**이었다.
두 규약을 모두 고정하고 모든 JSON에 병기한다:

- `depth_from_word_start` = abandonment edge를 1로 세는 총 macro-edge 수
- `depth_from_abandonment_root` = abandonment **이후**의 macro-edge 수
- 관계: `word_start = root + 1`

| 분기 | word_start | root | \|W\| | before_C |
|---|---|---|---|---|
| ell=4 | 5,7,9 (**홀수**) | 4,6,8 (짝수) | 3,5,7 (홀수) | 2,4,6 (**짝수**) |
| ell=0 | 6,8,10 (**짝수**) | 5,7,9 (홀수) | 4,6,8 (짝수) | 2,4,6 (**짝수**) |

**라운드20의 서술은 root 규약에서 옳았다**(충돌 아님). 앞으로는
word_start 규약을 기본으로 쓰고, 그 규약에서 **ell=4는 홀수,
ell=0은 짝수**다.

## 1. 단어 분해

\[
A_\ell\; W\; R_2,\qquad W = P\;C\;T_\ell
\]

- \(A_\ell\): abandonment (hub 내 회전 offset \(\ell\))
- \(P\): completer 이전 준비 부분, 길이 `before_C`
- \(C\): hub completer (W 내부의 edge)
- \(T_\ell\): completer 이후 tail — **ell=4에서 빈 단어, ell≠4에서 `Xh`**

## 2. 손증명된 부분

### Lemma P1 (손증명): \(T_\ell\)의 길이는 \(\ell=4\)에서 0, \(\ell\ne4\)에서 1

hub의 유일한 exit 위치는 위치 5(orbit 1)이다 — **Hub Exit Source
Lemma**(라운드15, 손증명): F=1 소진 후 hub를 떠나는 조인트는 반드시
위치 5를 source로 쓴다. 한편 completer는 nearest residual 위치
\(\ell+1\), 즉 orbit \(O_*=\mathrm{HEX0POS}[\ell+1]\)에 착지한다.

chaining이 성립하려면 \(R_2\)의 source orbit이 \(O_*\)여야 한다.

- \(\ell=4\): \(O_*=\mathrm{HEX0POS}[5]=1\) = **exit 위치의 orbit과 일치**.
  따라서 hub를 떠나는 그 edge 자체가 \(R_2\)가 될 수 있고, 실제로
  그렇다 ⟹ \(|T_4|=0\), completer→R2 거리 = **1**.
- \(\ell\ne4\): \(O_*\ne1\)이므로 exit edge의 source(orbit 1)는
  \(O_*\)가 아니다 ⟹ exit edge는 \(R_2\)가 될 수 **없고**, 별도의
  zero-charge exit edge `Xh`가 하나 필요하다 ⟹ \(|T_\ell|=1\),
  거리 = **2**.

**측정 확인**: ell=4에서 거리 1 (9/9), ell=0에서 거리 2 (5/5).

> **따라서 라운드20의 "hub completer는 준비 구간의 마지막 edge다
> (12/12)"는 정정된다 — ell=4에서만 참(9/9)이고 ell=0에서는
> 거짓(0/5)이다.** 이는 라운드20이 ell=4 패턴을 ell=0에 검증 없이
> 일반화한 오류였다.

### Lemma P2 (손증명): \(\Phi=0\)은 이 normal form에서 \(\ell\)과 무관하게 자동

\(\Phi(S')=\Phi(S)+(\ell'-5)\)이고 \(\Phi(\text{initial})=6\)이므로
\(\Phi_{\text{final}}=0 \iff \sum(5-\ell_i)=6\).

F=1 소진 후에는 회전 후계자가 이미 방문된 위치에서만 \(\ell<5\)
조인트가 legal한데, 그런 위치는 hub 안에만 있다(Hub Touch Count≤2로
hub는 한 번 닫히면 재진입 불가). 따라서 \(\ell<5\)인 edge는 정확히
둘뿐이다:

- \(A_\ell\): 기여 \(5-\ell\)
- hub exit edge: completer가 위치 \(\ell+1\)에 착지한 뒤 위치 5까지
  \(4-\ell\)번 회전하므로 회전길이 \(4-\ell\), 기여
  \(5-(4-\ell)=1+\ell\)

\[
(5-\ell)+(1+\ell)=6\quad\text{— }\ell\text{에 무관}
\]

**측정 확인**: 모든 12개 witness의 `phi_cost_profile`에서 0이 아닌
기여가 정확히 하나씩(ell=4는 5, ell=0은 1)이고 \(A\)의 기여와
합이 6이다. `phi=0` 12/12.

이는 라운드15가 "산술적 우연"으로 남겨 두었던 \(\Phi=0\)을
**normal form의 기하에서 나오는 필연**으로 격상시킨다.

### 정리 P3 (조건부 손증명): parity

\(|W| = |P| + 1 + |T_\ell|\)이므로 P1에 의해

- \(\ell=4\): \(|W| = |P|+1\), `word_start` \(=|W|+2=|P|+3\)
- \(\ell\ne4\): \(|W| = |P|+2\), `word_start` \(=|P|+4\)

**\(|P|\)가 짝수이면** `word_start`는 ell=4에서 홀수, ell≠4에서
짝수가 된다 — 관측과 정확히 일치.

## 3. 남은 gap — \(|P|\)의 짝수성은 손증명되지 않았다

`before_C` 값은 관측된 12+2개 witness 전부에서 짝수(2,4,6)다.
그러나 **이것은 same-component 경계에 특유한 현상이지 일반적인 hub
완성의 성질이 아니다**: 모든 hub 완성(same-component 여부 무관)을
세면 `before_C` 분포가 `{1:1, 2:3, 3:5, 4:10}`(ell=0) 등으로
**홀수 값이 실제로 존재**한다(`outputs/rr_preparation_parity_general.json`).

> **판정**: \(|P|\) 짝수성은 **root-local exhaustive 관측**이며
> **손증명 미완료**. 따라서 parity 정리 전체는 "P1·P2는 손증명,
> P3는 \(|P|\) 짝수성을 전제로 한 조건부 손증명"으로 표기한다.
> 홀수 \(|P|\)를 갖는 same-component 경계가 더 깊은 depth에서
> 나타날 가능성은 배제되지 않았다.

**성공 기준 1 평가**: **부분 달성** — parity의 분기별 차이(왜 ell=4는
홀수이고 ell=0은 짝수인가)는 P1으로 완전히 손증명됐다. 남은 것은
공통 인자 \(|P|\)의 짝수성 하나이며, 그것이 미완료다.
