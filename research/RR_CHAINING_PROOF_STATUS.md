# RR same-component ⟹ chaining — 구조적 증명 시도

목표 명제(정확히): RR 상태에서 두 R defect 중 **둘째 R 자신의**
`component_relation`(즉 `partial_component_relation`, `component_map(pre_joint)`에서
둘째 R의 source orbit root와 target orbit root가 같은지)가 `"same"`이면,
`first_target_second_source`(첫 R의 target orbit == 둘째 R의 source
orbit, chaining)가 성립한다.

## 1. 메커니즘 추적 — 정의로부터

`component_map(state)`는 그 시점까지 **오직 joint(weight>=2)만이**
`orbit_masks`의 비트를 설정한다는 사실(`extend()`, weight-1 rotation은
`om`을 건드리지 않음)에 의해, union-find 그래프의 노드 `("q", q)`가
"등록"(즉 `roots.get(("q",q))`이 `None`이 아님)되려면 **그 orbit q가
과거 어느 joint의 target orbit이었어야 한다**(또는 초기 상태 자신의
orbit). 둘째 R의 `pre_joint` 상태에서 이 그래프에 이미 등록된 joint는:
첫 R 자신, 그리고 첫 R과 둘째 R 사이의 zero-charge joint들, 그리고
초기 상태뿐이다.

**둘째 R의 source orbit(`ssrc`)** = `ORBIT_PHASE[pre_joint.p]`의 q값이며,
`pre_joint.p`는 (첫 R 착지 후 몇 번의 rotation을 거친) 현재 위치다.
`ssrc`가 그래프에 등록되려면 **`ssrc`가 앞선 어떤 joint의 target
orbit과 정확히 같아야 한다**(rotation 자체는 orbit_masks를 갱신하지
않으므로, rotation만으로 도달한 새 위치의 orbit은 자동으로 등록되지
않는다).

## 2. 증명된 부분 정리 (**손증명, 전체 코퍼스로 계산 검증됨**)

> **Chaining(`first_target_second_source=True`, 즉 `ftgt==ssrc`)이면,
> 둘째 R 자신의 `component_relation`은 절대 `"unresolved"`가 아니다
> (`"same"` 또는 `"different"` 중 하나로 반드시 resolve된다).**

증명: chaining이면 `ssrc == ftgt`이고, `ftgt`는 첫 R 자신이 이미
그래프에 등록한 노드(첫 R 자신의 joint가 `ftgt` orbit을 target으로
했으므로)다. 따라서 `("q", ssrc) = ("q", ftgt)`는 이미 등록된 노드이고
`roots.get(("q",ssrc))`은 `None`일 수 없다 — `partial_component_relation`의
정의상 `source_root is not None`이 참이므로 `"unresolved"`(두 root 중
하나라도 `None`)가 나올 수 없고, `"same"` 또는 `"different"`로 확정된다. □

전체 4,470개 RR 코퍼스로 검증: **chaining 75개 전부에서 둘째 R의
`component_relation`은 `different`(65) 또는 `same`(10)뿐이며,
`unresolved`는 0개다** — 이론과 정확히 일치.

## 3. 요청된 명제(same ⟹ chaining) 자체 — **증명하지 못함, 정직하게 미완료로 표시**

§2의 정리는 "chaining이면 반드시 resolve된다"(resolve ⊇ chaining이
안기는 필요조건)를 보여줄 뿐, "resolve된 것 중 `same`인 것은 반드시
chaining에서 왔다"는 반대 방향은 별도로 증명해야 한다. 코퍼스 전체를
교차검증한 결과:

| | component_relation[2번째]="unresolved" | ="different" | ="same" |
|---|---:|---:|---:|
| chaining(75개) | 0 | 65 | 10 |
| non-chaining(4,395개) | 4,288 | **107** | **0** |

**non-chaining인데도 둘째 R의 source가 resolve되는 경우가 107건
존재한다**(`ssrc`가 `ftgt`와 다른데도 그래프에 등록됨 — 즉 초기
orbit이나 중간 zero-charge joint의 target orbit과 우연히 일치한
경우로 추정된다) — 하지만 이 107건 전부 `"different"`이지 `"same"`은
단 한 건도 없다. 이는 "`ssrc`가 `ftgt`가 아닌 다른 경로로 등록되면
`target_root`가 그 root에 절대 도달하지 못한다"는 **더 강한 사실**을
시사하지만, 이것을 일반적으로 왜 그런지 정의로부터 연역적으로
끝까지 추적하지 못했다 — 남은 depth<=6, 최대 5개의 zero-charge joint
경로에 대한 경우의 수 분석이 필요하며, 이번 라운드에서 완료하지
못했다.

## 4. 반례 모델 시도 — 구성하지 못함, 정직하게 보고

요청은 "실제 exact state가 아니라도 transition axiom을 만족하는 반례
모델"을 허용한다. 그러나 이 명제의 반례가 되려면 실제 S6의 144개
E-orbit(각 크기 5)과 120개 hexagon(각 크기 6) 사이의 구체적인 교차
구조(`ports_of_e_orbit`, `hexagon_id`)를 반영해야 하며, 이를 무시한
일반적 "토이 모델"은 이 명제의 진위와 무관해질 위험이 크다(예:
`FRAGMENT_DEBT_LEMMA.md`의 fragment debt 반례는 순수 집합/순환
성질만으로 충분했지만, 이 명제는 두 서로 다른 유한군의 서로 다른
작용이 만드는 교차 구조에 의존한다). 이번 라운드에서 이 정밀도로
반례 모델을 구성할 시간이 없었다 — **반례도 만들지 못했다.**

## 5. 정직한 최종 상태

- **손증명 + 전체 코퍼스 검증**: chaining ⟹ resolved(§2) — 새로운
  진짜 정리.
- **미완료**: resolved 중 same ⟹ chaining이라는, 사용자가 원래
  요청한 정확한 방향의 명제 — 증명도 반증도 하지 못했다. 4,470개
  전체(표본 아님)에서 반례가 없다는 사실(`RR_INTERACTION_INVARIANT.md`)은
  여전히 유효하지만, 이것만으로는 정리라고 부를 수 없다는 원 지침을
  그대로 따른다.

## 성공 기준 (4) 평가

"RR same-component ⟹ chaining의 손증명"은 문자 그대로는 **미달성**이다.
그러나 그 증명을 시도하는 과정에서 §2의 새로운, 진짜로 증명된 부분
정리(chaining ⟹ resolved)를 얻었다 — 목표로 했던 정확한 명제는
아니지만, 같은 구조(원인: R1이 등록한 노드의 재사용)를 정직하게
한 단계까지 파고든 실질적 진전이다.
