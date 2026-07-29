# orbit 1 first-opener ledger (라운드 30 §16–17)

산출: `src/analyze_rr_ch2_chaining.py` ->
`outputs/rr_orbit1_opener_ledger.json`.

## 1. 질문

과제 §16이 제안한 정리:

> \(C\)가 Z2라면 orbit 1을 처음 연 사건이 \(R_1\)이어야 한다.

이것이 참이면 chaining이 즉시 따라온다.

## 2. 답 — **반증됨**

\(\ell=4\)에서 abandonment 직전/직후의 orbit 1 mask:

| 항목 | 값 |
|---|---|
| abandonment 직전 orbit 1 mask | **0** (닫힘) |
| abandonment 직후 orbit 1 mask | **1** (phase 0 열림) |
| abandonment target | **(orbit 1, phase 0)** |
| abandonment의 `new_orbit` 플래그 | **True** |

> **orbit 1의 최초 opener는 abandonment joint 자신이다.**
> \(R_1\)이 아니다.

이것은 우연이 아니라 구조다: \(\ell=4\) rotation run은 hex0 위치
1,2,3,4(orbit 120, 33, 9, 3)를 열고, 그 다음 유일한 abandonment 조인트
`w2:10`이 **orbit 1의 phase 0**에 착지한다. orbit 1은 그때 처음 열린다.

## 3. 따름 — §19 architecture는 교체돼야 한다

| Lemma | 판정 |
|---|---|
| CH2-A (\(C\)가 Z2면 orbit 1은 이미 열려 있다) | **손증명** — 그러나 자명하고 무력하다. abandonment가 항상 열어 두기 때문에 \(C\)의 종류와 무관하게 참이다 |
| CH2-B (최초 opener \(=R_1\)) | **반증됨** |
| CH2-C, 정리 | CH2-B에 의존 — **무효** |

**\(R_1\)보다 앞선 Z3 opener가 가능한가?** 질문 자체가 성립하지 않는다 —
opener는 Z3도 \(R_1\)도 아닌 **abandonment**다.

## 4. 그렇다면 무엇을 세어야 하는가

orbit 1은 abandonment가 열지만, 걸음이 \((1,0)\)에서 \((1,4)\)까지
가려면 \(O_*\) phase walk를 걸어야 한다(라운드29 §10의 정정된 항등식이
다루는 대상). CH2의 진짜 질문은 **opener**가 아니라

> \(P_{\mathrm{core}}\) 안의 \(O_*\) 걸음 중 **적어도 하나가 R인가**

이다. 15개 사례에서는 항상 그랬지만, 라운드30의 탐색이
**\(\#R_{\le C}=0\)인 legal completion**을 하나 찾았으므로
"항상"은 증명되지 않는다. `RR_CH2_CHAINING.md` §4 참고.

**등급**: opener 판정 **손증명**, CH2-B **반증됨**,
남은 질문 **미완료**.
