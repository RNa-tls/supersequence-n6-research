# 홀수 preparation 배제 (라운드 24)

산출: `src/verify_rr_preparation_parity_theorem.py` ->
`outputs/rr_odd_preparation_classes.json`.

## 8. 홀수 \(\vert P\vert\) 분류 (상한 제거 후)

\(O_*\) 위치에 착지하면서 \(\vert P\vert\)가 홀수인 완성을 전부
분류하면, **모든 분기에서 동일하게** completer까지의 R 개수가
**짝수**다:

| 분기 | 홀수 \(\vert P\vert\)에서의 \(\#R\) 분포 |
|---|---|
| ell=0..4 (전부) | `{0: 1, 2: 9}` |

## Branch exclusion 정리

> **\(\#R=0\)** — \(O_*\)를 target하는 R이 없으므로 R1이 존재하지
> 않고, chaining(\(R_1\) target \(=R_2\) source \(=O_*\))이
> **불가능**하다.
>
> **\(\#R=2\)** — completer까지 이미 R이 둘이므로 \(R_2\)는 세 번째
> R이 되어 **RR word가 아니다**.
>
> 두 경우 모두 same-component RR과 양립하지 않는다. 따라서 **홀수
> \(\vert P\vert\)의 same-component RR witness는 존재할 수 없다.**

**단, 이 논증은 "홀수 \(\vert P\vert\) ⟹ \(\#R\) 짝수"에 의존하며,
그것이 바로 미증명 parity 관계다** — 따라서 이 배제 정리는
**root-local exhaustive** 등급이지 손증명이 아니다.
세 번째 종류(\(\#R\) 홀수이면서 \(\vert P\vert\) 홀수)가 구조적으로
불가능하다는 것도 **미완료**다.

## 9. 최종 증명 구조의 현재 상태

| 구성요소 | 등급 |
|---|---|
| **Lemma 1**: \(O_*\) 경계에서 \(\vert P\vert+\#R\equiv1\) | **미완료** (root-local exhaustive, 5/5 분기, 상한 없이 재확인, sharp) |
| **Lemma 2**: same-component RR ⟹ completer까지 R이 정확히 하나 | **손증명** (라운드23) |
| **Theorem**: \(\vert P\vert\equiv0\) | Lemma 1에 의존 — **미완료** |
| **Corollary**: ell=4/ell=0의 word-depth parity 차이는 tail 길이 차이 | **손증명** (라운드21 Lemma P1) |
