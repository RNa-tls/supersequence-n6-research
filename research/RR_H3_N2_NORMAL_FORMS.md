# H3 / N2 normal form 분류 (라운드 19)

산출: `src/verify_rr_l5_states.py` -> `outputs/rr_l5_state_ledger.json`,
`outputs/rr_h3_n2_comparison.json`. 새 completion search 없음.

## 3. 두 집합의 정의

- **H3**: 역사적 depth≤6 word scope 안에 나타나는 post-R2 state 3개
  (`5d3f8cb9fdd4`, `6f1ed828b231`, `fe82b0cdb512`) — abandonment 이후
  depth 4, word 총 5 macro-edge.
- **N2**: depth≤6 scope 밖에서 처음 나타나는 2개
  (`86195429f1c6`, `b2898cc223e9`) — abandonment 이후 depth 6, word
  총 7 macro-edge.

## 공유 불변량 — 다섯 상태 전부 동일 (예외 0)

| 좌표 | 값 |
|---|---|
| R1 target orbit | **1** |
| R2 source (orbit, phase) | **(1, 4)** |
| R2 target orbit | **0** |
| hub completer 착지점 | **(orbit 1, phase 4)** = hex0 위치 5 |
| 마지막 macro-edge | **`rot^0;w3:120`** |
| Φ | **0** |
| legal trailing edge 수 | **3** |
| 도달 경로 수 | **1** |

**즉 다섯 상태는 완전히 동일한 종결 메커니즘(terminal mechanism)을
갖는다**: `ell=4` abandonment가 hex0에 유일한 잔여 위치(위치 5 =
orbit 1)를 남기고 → hub completer가 정확히 그 (orbit 1, phase 4)에
착지해 hub를 닫고 → R2가 즉시 `ell=0`으로 발동해 orbit 1을 source로
삼는다. R1의 target이 orbit 1이므로 **chaining이 자동으로
성립**한다.

## 차이나는 좌표 — 준비(preparation) 구간뿐

| 좌표 | H3 | N2 |
|---|---|---|
| 준비 macro-edge 수 | **3** | **5** |
| Z3(fresh orbit opening) 수 | **0** | **2 또는 3** |
| 최종 O | **2** | **4 또는 5** |
| hub completer가 R1 자신인가 | **False 2개 / True 1개** | **True 2개** |
| hub completer의 kind | **R 또는 Z2** | **R만** |

kind signature (마지막 R2 edge 포함):

```
H3  5d3f8cb9fdd4: [R,  Z2, Z2, R]
H3  6f1ed828b231: [Z2, R,  Z2, R]
H3  fe82b0cdb512: [Z2, Z2, R,  R]
N2  86195429f1c6: [Z3, Z2, Z3, Z2, R, R]
N2  b2898cc223e9: [Z3, Z3, Z2, Z3, R, R]
```

## 8. 목표 정리 판정 — 반증됨

> **검사한 명제**: "N2 state는 H3 family에 **하나의** zero-charge
> preparation block을 삽입한 정확한 delayed form이다."

**판정: 반증됨(falsified as literally stated).** 세 가지 이유:

1. **개수가 안 맞는다.** N2는 H3보다 준비 edge가 **2개** 많다(5 vs
   3), 하나가 아니다.
2. **삽입된 블록의 종류가 다르다.** N2의 추가 edge는 **Z3(fresh
   orbit opening)** 인데, **H3는 Z3를 단 한 번도 쓰지 않는다** —
   H3는 O=2로 고정, N2는 O=4~5로 증가. 즉 "같은 종류의 블록을
   지연 삽입"한 것이 아니라 **다른 종류의 준비**를 한다.
3. **hub completer 역할이 다르다.** N2는 둘 다 **R1 자신이
   completer**인 반면, H3는 두 변종을 모두 포함한다(2개는 zero-charge
   Z2가 hub를 닫고, 1개는 R1이 닫는다).

## 정정된 정규형 — 하나의 종결형, 두 개의 준비 family

> **종결 normal form(1개, 다섯 상태 공유)**: 마지막 2개 edge —
> hub completer가 (orbit 1, phase 4)에 착지 → R2가 `rot^0;w3:120`로
> 즉시 발동. Φ=0, trailing edge 3개.
>
> **준비 family(2개, 구조적으로 독립)**:
> - **H3형 — orbit-1 phase walking**: R1이 orbit 1을 (마지막이 아닌)
>   어떤 phase에서 target하고, zero-charge Z2들이 orbit 1의 남은
>   phase를 걸어 hex0의 phase 4에 도달한다. 새 orbit을 열지 않아
>   O=2로 고정. 준비 3 edge.
> - **N2형 — fresh-orbit opening**: Z3 이벤트들이 새 orbit을 열어
>   더 긴 사슬을 만들고, R1 자신이 직접 hex0의 (1,4)에 착지한다.
>   O가 4~5로 증가. 준비 5 edge.

**두 family는 "지연된 같은 것"이 아니라 같은 종결형에 도달하는 서로
다른 경로**다. 과제 §8이 요구한 대로, 거짓이므로 **구조적으로
독립된 normal form으로 분리**해 기술한다.

## N2가 왜 depth 7에서만 나타나는가

N2형은 준비 구간에서 **fresh orbit을 2~3개 열어야** 한다. 각
orbit opening은 그 자체로 하나의 macro-edge를 소비하고, 열린 orbit을
가로지르는 Z2 연결도 추가 edge를 요구한다. 그 결과 준비에 최소
5 edge가 필요해지고, R2까지 총 6 edge(abandonment 제외) = word 7
macro-edge가 되어 역사적 depth≤6 scope를 넘어선다.

**H3형은 새 orbit을 전혀 열지 않고 이미 등록된 orbit 1의 phase만
걸어서** 준비를 3 edge로 끝낸다 — 이것이 H3형만 depth≤6 안에
들어오는 이유다.

**증명 등급**: 위 서술은 다섯 상태의 exact trace에서 직접 읽은
**root-local exhaustive** 관찰이다. "N2형이 반드시 5 edge를
요구한다"는 하한(lower bound)은 **증명하지 않았다** — depth 6
universe에서 N2형이 하나도 나타나지 않았다는 사실이 강한 증거이나,
일반 하한 논증은 **미완료**.


## 라운드20 정정 — fresh-opening 이분법은 depth 8에서 무너진다

위 분류는 "H3는 Z3를 전혀 안 쓴다(fresh=0) / N2는 쓴다(fresh=2~3)"를
축으로 삼았다. depth ceiling 8까지 확장하면 preparation length 7인
state가 4개 더 나타나는데, 그중 **3개가 fresh=1**이라 이 이분법에
깔끔히 들어맞지 않는다.

**더 안정적인 분류 축은 preparation length**(관측값 3, 5, 7 — 전부
홀수)이며, 각 길이 안에서 Z3 개수가 다양하게 나타난다. 자세한 내용은
`RR_N2_PREPARATION_NORMAL_FORM.md`와
`RR_TERMINAL_NORMAL_FORM_THEOREM.md` §12 참고.
