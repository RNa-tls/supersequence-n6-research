# Component 모델 — necessary-condition 전용 (라운드 33 §6–7)

## 1. 왜 exact model이라고 부르지 않는가

> **이 프로젝트는 Target B의 최종 component 요구 구조를 아직 정의하지
> 못했다.** 이 문장 자체를 기록하는 것이 §6의 지시다.

Target B는 "pure-rotation suffix를 허용하는 상태에서 끝난다"로 정의됐다
(라운드28). 그 조건이 orbit/hexagon 접합 forest의 **최종 component
구성**에 무엇을 요구하는지는 특성화되지 않았다. 따라서:

- component 조건을 제약으로 넣은 모델은 **exact model이 아니다.**
- 이번 라운드는 R5를 **necessary-condition model**로만 취급했고,
  실제로는 **제약으로 강제하지 않았다**(§17).

## 2. Segment의 component 효과 라벨 (§6) — 기록만

| 라벨 | 의미 |
|---|---|
`attach` | fresh orbit이 이미 방문된 hexagon을 통해 기존 component에 붙는다 |
`extend` | 같은 component 안에서 port를 추가한다 |
`merge` | 서로 다른 두 component를 잇는다 |
`revisit` | 같은 component를 다시 건드린다 |
`isolate` | 어떤 기존 component와도 연결되지 않는 새 조각을 만든다 |

**이 라벨을 제약으로 쓰지 않은 이유**: 최종 요구가 없으면
"isolate가 나쁘다"조차 증명할 수 없다. heuristic으로 금지하면
안전한 하한이 아니게 된다(라운드32의 greedy 오용과 같은 종류의 실수).

## 3. 이번 라운드가 답한 §17의 질문

> R0~R4가 전부 feasible로 나오는 survivor가 있다면, 그때 처음으로
> "component가 진짜 병목인가"라는 질문이 의미를 가진다.

**답: 그런 survivor가 없다.** 4개는 R1을 통과했으나 R3에서 미판정이고,
3개는 R1 자체가 미판정이다. 따라서

> **component 조건은 아직 병목 후보가 아니다.** 그보다 앞선 층(R3,
> segment flow/order)이 먼저 결판나야 한다.

이는 라운드29–32에서 component 조건을 반복적으로 "다음 병목"으로
지목했던 것에 대한 정정이다 — 실제 병목은 **순서**다.

## 4. 다음에 필요한 것

component 모델을 완성하기 전에:

1. **flow-first 모델**로 R3을 먼저 결판낸다(§5 아래).
2. R3이 feasible한 cover가 나오면 R4(engine replay)로 검증한다.
3. **그 다음에야** component 조건의 정의가 의미를 갖는다.

**등급**: 라벨 정의 **exact allocation model**의 일부,
component 제약 **미완료**, "병목이 아니다"라는 판정 **exact replay**
(층 상태에서 직접 읽음).
