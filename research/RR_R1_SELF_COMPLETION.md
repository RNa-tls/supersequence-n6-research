# R1/R2 self-completion 분류와 obstruction 후보 검증 (라운드 16)

산출: `src/analyze_rr_self_completion.py` -> `outputs/rr_self_completion_cases.json`.
새 대규모 탐색 없음(단일 exact witness를 직접 구성해 검증).

## 6. Self-completion 정확한 정의와 분류

"self-completion" = R1 또는 R2 자신이 hub(hex0)의 두 번째 터치를
제공하는 경우. 라운드14/15 데이터에서 이미 이런 사례가 존재함이
알려져 있었다(예: `989d2261b458`에서 R1 자신이 completer).

이번 라운드는 **R2가 completer인 self-completion**의 새 exact
witness를 직접 구성했다(`analyze_rr_self_completion.py`):

```
idx0 ell=0 w2:10  kind=Z2abandon
idx1      w3:120  kind=R          (R1, hex90, orbit120 phase3)
idx2      w3:201  kind=Z3         (hex72, orbit1 phase1)
idx3      w2:10   kind=Z2         (hex12, orbit1 phase2)
idx4      w3:120  kind=R          (R2 = hub completer, hex0, orbit1 phase4 -- hex0의 가장 먼 residual 위치!)
```

최종 상태: `F=1,S=4,H=0,O=3,D=9,P=6`, `area_a_prune_reason` =
**`None`(완전히 legal)**. `macro.stable_hash`로 원본 코퍼스
전체(25,660개 레코드)를 대조한 결과 **이 상태는 코퍼스에 없다** —
`RR_NEAREST_RESIDUAL_THEOREM.md`가 발견한 코퍼스 불완전성의 구체적
증거 사례다.

## 7. Obstruction 후보 S1-S5 판정

| 후보 | 판정 | 근거 |
|---|---|---|
| S1(기존 target slot 소실) | **반증됨** | 이 witness는 R1, R2 둘 다 정상 발동하며 슬롯 손실이 없다 |
| S2(Hub Exit Source Lemma로 인한 endpoint 불일치) | **반증됨** | `area_a_prune_reason=None`, F=1,H=0으로 완전히 legal — endpoint 불일치 없음 |
| S3(Φ budget 조기 소진) | **미완료** | Φ 값 자체는 계산했으나 음수이거나 명백히 장애가 되는지는 이 단일 witness만으로 판단 불가 |
| S4(ancestry가 non-chaining 구조로 고정) | **미완료(적용 불가)** | 이 witness는 R2가 completer이지 R1이 아니므로 S4를 직접 검증할 수 없음 — 별도의 R1-completer witness 구성이 필요하나 이번 라운드에 완료하지 못함 |
| S5(ell=0 예외만 phase saturation으로 우회) | **반증됨** | 이 witness는 phase saturation 패턴이 아닌, 4-step 직접 연쇄로 non-nearest에 도달한다 — saturation이 유일한 우회 경로가 아님을 보여줌 |

## 정직한 결론

**S1, S2, S5는 이 구체적 witness에 대해 명확히 반증됐다.** 즉
"R2가 self-completer가 되어 non-nearest 위치를 완성하는 것"은
구조적으로 legal하고 실제로 구성 가능하며, 제안된 5개 obstruction
후보 중 3개가 이 사례에서 성립하지 않는다. 코퍼스에 이 witness가
없는 이유는 **가장 단순한 설명(원본 코퍼스가 65,340-state
capped frontier라는, 이번 라운드가 발견한 사실)으로 충분히
설명되며, 별도의 깊은 수학적 장애물을 가정할 필요가 없어
보인다** — 그러나 이것이 "장애물이 전혀 없다"는 것을 증명하지는
않는다(S3, S4는 미완료로 남는다).

**성공 기준 (3) 평가**: "R1(및 R2) self-completion의 정확한
obstruction 또는 정상형" 요구에 대해 — obstruction 후보 대부분이
반증되어 명확한 정상형(normal form)이나 완전한 obstruction 이론
어느 쪽도 확립하지 못했다. 대신 **self-completion이 nearest뿐
아니라 non-nearest 위치에서도 legal하게 가능하다는 새로운 사실**과
**그것이 코퍼스에 없는 이유가 수학적 장애물이 아니라 코퍼스
자체의 불완전성일 가능성이 높다는 증거**를 확립했다 — 이는
원래 질문("왜 self-completion이 거의 안 나타나는가")에 대한
답의 방향을 바꾼다: "안 나타나는" 것이 아니라 "기록되지 않았을
뿐"일 가능성이 크다.
