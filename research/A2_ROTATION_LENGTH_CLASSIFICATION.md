# A2 rotation-length(ell_A2) spectrum — 완전 분류

산출: `src/analyze_a2_rotation_length.py` -> `outputs/ra2_a2_length_spectrum.json`.

## 결론 먼저

**ell_A2의 가능한 값은 정확히 {0,1,2,3,4}다. ell_A2=5는 구조적으로
불가능함이 증명됐다(손증명). ell_A2=2는 24개 RA2 코퍼스(depth<=6)
안에서는 예외 없이 부재하지만, depth<=6 전체를 raw BFS로 완전 탐색해도
등장하지 않는다는 것까지 확인한 뒤(유한 완전 검증, 소진된 탐색),
depth=7에서 구체적 witness를 찾아 반증했다 — A2R 사례와 정확히
같은 패턴으로, "불가능"이 아니라 "depth<=6 코퍼스의 아티팩트"였다.**

## 1.1 ell_A2=5 — 구조적으로 불가능 (손증명)

`f1_normal_form`이 F=0인 동안 current hex를 단일 연속 arc로 강제한다.
ell=5에 도달하면 그 arc 길이가 6(=FULL)이 되고, 그 순간의
rotation-successor는 정의상 그 arc 자신의 시작점(이미 방문됨)이므로
`extend()`의 `abandonment = not visited(successor)` 계산이
`abandonment=False`를 강제한다. A2는 정의상 `abandonment=True`이므로
ell=5에서는 발동될 수 없다. (이 논증은 `RA2_ZERO_CHARGE_HISTORY.md`
§1.2와 동일 — 여기서는 A2에 국한해 재확인.)

## 1.2 ell_A2=2 — 판정: 미관측(depth<=6) → depth=7에서 반증됨(불가능 아님)

`find_ell2_witness`(초기 상태부터 raw BFS, "정확히 R 다음 A2, ell_A2=2"만
찾음):

- **depth<=6, node_cap=300,000**: **frontier가 노드 12,367개만에 완전
  소진**됐다(node cap에 도달하지 않고 스스로 끝남) — 즉 이것은 "제한
  실험"이 아니라 **depth<=6 전체에 대한 유한 완전 검증**이다: ell_A2=2는
  이 경계 안에서 정말로, 예외 없이 존재하지 않는다.
- **depth<=7**: **depth=7에서 즉시 발견**됐다(30,850 노드).
  구체적 witness:
  ```
  macro_path = [rot^5;w3:120, rot^5;w3:201, rot^5;w2:10, rot^5;w3:201,
                rot^5;w3:210, rot^5;w2:10, rot^2;w2:10]
  ```
  (앞의 6단계가 R + zero-charge word, 마지막 `rot^2;w2:10`이
  `ell_A2=2`인 A2 자신.)

**따라서 "ell_A2=2가 구조적으로 불가능한가, 코퍼스에서만
미관측인가?"라는 질문에 대한 완전한 답: 구조적으로 불가능하지
않다 — depth<=6 코퍼스의 경계 아티팩트였다.** 이는 이전 라운드의
A2R(0/25,660 관측, depth-6에서 반증됨) 사례와 완전히 같은 패턴이며,
이 프로젝트에서 "미관측 ≠ 불가능"이라는 원칙이 다시 한번 확인됐다.

## 1.3 각 ell 값이 남기는 arc, endpoint 상대 위치, target 관계

24개 RA2 코퍼스 + 위 depth-7 witness에서 관측된 boundary normal form
(`outputs/ra2_a2_length_spectrum.json`의 `boundary_normal_forms_by_ell`):

| ell_A2 | 코퍼스 관측 수 | 남는 fragment arc 길이 | debt(=6-len) | Φ(=1+ell) |
|---:|---:|---:|---:|---:|
| 0 | 1 | 1 | 5 | 1 |
| 1 | 18 | 2 | 4 | 2 |
| 2 | 0(코퍼스)/depth7에서 확인 | 3 | 3 | 3 |
| 3 | 1 | 4 | 2 | 4 |
| 4 | 4(=U4) | 5 | 1 | 5 |
| 5 | 0(구조적 불가능) | — | — | — |

endpoint(canonical화 이후)는 abandon 순간 항상 hex 안의 특정 위치이며,
arc는 항상 "hex의 시작 slot부터 ell+1칸 연속 방문, 나머지가 단일
missing arc"라는 동일 패턴을 따른다(§`RA2_ZERO_CHARGE_HISTORY.md`
§1.2가 이미 증명한 단일-arc 강제의 직접 결과) — ell 값이 다르면 missing
arc 길이만 다를 뿐, "단일 연속 missing arc"라는 형태 자체는 모든 ell에서
동일하다.

target E-orbit/phase 관계는 §`RA2_ELL4_BOUNDARY_GEOMETRY.md`에서 controlled
counterfactual(같은 R, ell만 바꾼 비교)로 더 정밀하게 다룬다 — 코퍼스
전체 비교는 서로 다른 R을 쓴 상태를 섞어버려 ell만의 순수한 효과를
가린다는 것이 이번 라운드에서 확인된 방법론적 교훈이다.
