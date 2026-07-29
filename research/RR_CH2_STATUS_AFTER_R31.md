# CH2 현재 상태 고정 (라운드 32 §18–19)

이번 라운드는 **CH2 탐색을 확대하지 않았다**(과제 지시). 상태만
고정한다. segment 문제와 섞지 않는다.

## 1. CH2 현황

| 항목 | 상태 |
|---|---|
| CH1 (\(C\)가 R ⟹ chaining) | **손증명** — 15개 사례 중 5개 |
| CH2-B (orbit 1 최초 opener \(=R_1\)) | **반증됨** — abandonment가 연다 |
| local legality counter-scenario | **존재** — `rot^5;w2:10`×4의 순수 \(E\)-walk, \(C\) 이전 R \(=0\) |
| Target A 확장 (depth \(\le9\)) | **미발견** (64,500 노드, cap 미도달) |
| 탐색 상태 | **INCOMPLETE** — depth ceiling에서 잘림 |
| chaining 정리 | **미완료** |

## 2. 왜 depth만 올리지 않았는가

과제가 명시적으로 금지했고, 근거도 있다: depth 9까지 Target A 경계가
**하나도** 나타나지 않았으므로 10, 11로 올려도 같은 종류의 INCOMPLETE를
더 비싸게 반복할 가능성이 높다. 필요한 것은 **구조적 판정**이다:

> \(C\) 이전 \(R=0\)인 prefix에서 두 R을 모두 \(C\) 이후에 배치할 수
> 있는가?

\(C\) 직후는 \(\ell=0\) 강제이고 그 뒤는 \(\Phi=0\)이라 \(\ell=5\)만
가능하다(라운드29). 그 구조에서 **두 R의 배치 가능성**을 손분류하는
것이 다음 시도의 올바른 형태다.

## 3. segment 문제와의 분리

CH2는 **Target A 도달** 문제이고, 이번 라운드의 segment 분석은
**Target A 이후 Target B** 문제다. 두 문제는 자원 회계를 공유하지
않는다:

- CH2의 R-free prefix는 post-\(C\)에서 \(N=0\), \(O=2\)이므로
  \(R_{\mathrm{cap}}=3\), \(O_{\mathrm{cap}}=23\)로 **capacity가 매우
  넉넉**하다. capacity 장애물이 적용되지 않는다.
- 반대로 segment 분석의 7개 survivor는 전부 chaining이 이미 성립하는
  경계다.

**섞지 않는다.**

## 4. T3 (§19)

T3은 **exact observation 15/15**로 유지한다. 이번 라운드의 segment
구조에서 T3이 자동으로 필요해지는 새 손증명 연결은 **나오지 않았다** —
Target B capacity는 Target A 이후를 다루므로 \(C\) 직후 edge의 정체를
강제하지 않는다(라운드31 §23에서 이미 확인).

**재공략하지 않았다.**
