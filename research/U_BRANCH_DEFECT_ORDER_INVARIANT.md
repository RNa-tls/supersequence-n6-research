# Defect-order invariant, 그리고 RR/RA3/A3R로의 일반화

## 9. Defect-order invariant — "최초 등장 가능 최소 index"

요청된 후보(component roots, orbit ancestry, phase displacement,
fragment position, endpoint class)를 개별적으로 시도했으나, 이번
라운드의 실제 계산이 뒷받침하는 깔끔한 invariant는 다른 것이었다:

> **Ξ(이벤트 종류) := 그 이벤트가 walk의 첫 번째 counted 결함으로
> 등장할 수 있는 최소 macro-index.**

진짜 초기 상태(identity, 회전 0회)에서 각 이벤트 종류의 legal한
move 개수를 직접 계산했다:

| 이벤트 종류 | 정의 | 진짜 초기 상태(ell=0)에서 legal 개수 | 첫 등장 가능 최소 index |
|---|---|---:|---:|
| **A3** | weight=3, abandon, new_orbit | **3개(즉시 legal)** | **0** |
| **R** | weight=3, blocked, existing | 0개(ell=0에서 불가) | **0**(단, 자신의 hex를 ell=5까지 다 채운 뒤에만 — 여전히 macro-index로는 0) |
| **A2** | weight=2, abandon, existing | 0개 | **4**(depth 5, `A2R_MINIMUM_DEPTH.md`) |

**A3 < R < A2 순으로 "빨리 등장 가능"하다.** A3는 리터럴하게
즉시(ell=0) legal한 반면, R은 자신이 시작하는 hex를 완전히
채워야만(ell=5) legal해지고(그래도 macro-index 자체는 여전히
0이다 — 회전은 별도 스텝이 아니라 같은 macro-edge에 포함되므로),
A2는 최소 4개의 선행 joint(다른 orbit들을 touch해야 함)가 필요하다.

**이 Ξ가 정확히 RA2/A2R 순서를 구별하는 invariant다**: RA2(R
먼저)는 Ξ(R)=0이 Ξ(A2)=4보다 작으므로 자연스럽게 더 이른
depth에서 시작 가능하고, A2R(A2 먼저)은 Ξ(A2)=4라는 병목을 먼저
통과해야 하므로 전체 walk가 최소 depth 6까지 밀린다
(`A2R_MINIMUM_DEPTH.md`). **부호가 바뀌거나 일정 offset을 갖는
좌표를 찾으라는 원 요청에 대한 답은: 부호가 아니라, 이 비대칭
자체(0 대 4)가 순서를 구별하는 척도(scalar, 아니라 truly a single
integer per event kind)라는 것이다.**

## 10. RR, RA3/A3R로의 일반화

### RR — 대칭 예측, 검증하지 않음(구조적으로 자명)

RR의 두 이벤트는 **둘 다 R**(같은 종류)이므로, Ξ(R)=Ξ(R)로 항상
같다 — **이 invariant는 RR 안에서 순서를 구별할 정보를 주지
않는다**(둘 다 같은 시작 조건을 공유하므로 자명하게 대칭). 이는
`RR_INTERACTION_INVARIANT.md`(이전 라운드)가 이미 관측한, RR이
가장 이질적이고 자유로운 구조를 보이는 이유와 정성적으로
일치한다 — 새 계산 없이 이 자명한 함의만 기록한다.

### RA3/A3R — Ξ 비대칭이 코퍼스 크기 비대칭을 설명한다

`RA3_A3R_ASYMMETRY.md`(더 이전 라운드)는 RA3(9,952개)와
A3R(10,984개)가 RA2(24개)보다 압도적으로 큰 코퍼스를 갖는다는
사실을 fragment-relation 각도에서 설명했다. 이번 라운드가 찾은
Ξ(A3)=0(즉시 legal)은 그 근본 이유를 하나 더 제공한다:

> **A3가 walk의 첫 이벤트로 즉시(ell=0) legal하다는 사실은, A2가
> 최소 depth 5를 요구하는 것과 극명히 대조되며, 이것이 RA3/A3R가
> 이 depth<=6 코퍼스 안에서 RA2보다 압도적으로 더 많이(24개 대
> 9,952+10,984개) 관측된 근본 이유 중 하나로 보인다** — A3로
> 시작하는 walk는 RA2가 A2를 만들기 위해 소모해야 하는 "준비
> depth 4"라는 병목이 아예 없다.

**이는 추측이다** — 정성적으로 강하게 뒷받침되지만(Ξ(A3)=0 대
Ξ(A2)=4라는 극명한 차이), 코퍼스 크기 차이(24 대 ~10,000)를
정량적으로 완전히 설명하는 모델(다른 요인, 예를 들어 R 자체의
빈도나 zero-charge word의 branching factor 등)까지 검증하지는
않았다.

## 성공 기준 (5) 평가

"RA3/A3R에도 적용되는 일반 defect-exchange theorem"은 문자
그대로는(exchange lemma 자체의 일반화) **시도하지 않았다**(범위:
경량 검토만). 대신 Ξ invariant가 RA3/A3R의 이미 알려진 코퍼스
크기 비대칭에 대한 **새로운, 근본적인 설명 후보**를 제공한다는
점에서 부분적으로 기여한다 — 이는 요청된 정확한 형태의 성공
기준은 아니지만, 관련된 정직한 진전으로 기록한다.
