# EEEE full-segment 정리와 exit 분류 (라운드 32 §3–4, §6)

## 1. 정리 (§3)

> **EEEE full-segment theorem (손증명)**: \(R_{\mathrm{cap}}=1\)일 때
> capacity-5 segment의 보존 word는 **`EEEE` 하나뿐**이다.

**증명**:

1. capacity 5 ⟹ 자기 orbit의 다섯 port를 전부 사용 ⟹ 보존 edge가
   정확히 **4개**(길이 5 run은 존재하지 않는다 — 전수표에서 0개).
2. 길이 4 saturating block은 정확히 **세 개**:
   `EEEE`(\(E^2\) 0개), `E2EEE2`(2개), `E2E2E2E2`(4개).
3. **\(E^2\) 개수는 항상 짝수**다(관측 {0,2,4} — 세 block 전부).
   따라서 \(E^2\)를 **정확히 1개** 쓰는 saturating block은 **존재하지
   않는다**.
4. `w3:120`\(=E^2\)는 orbit을 보존하므로 절대 `new_orbit`이 될 수 없고
   weight 3이므로 **항상 R**이다(라운드30). 즉 \(E^2\) 하나가 R 슬롯
   하나를 먹는다.
5. \(R_{\mathrm{cap}}=1\)이므로 \(E^2\)를 2개 이상 쓰는 두 block은
   **사용 불가**. ∎

## 2. 역 (§3 converse)

> **역도 성립한다 — 단, hexagon 가용성 조건 아래에서.**

entry phase \(\phi\)에서 `EEEE`는 \(\phi,\phi{+}1,\dots,\phi{+}4\),
즉 **다섯 phase 전부**를 방문하므로 항상 capacity 5다 — **다섯 port가
모두 미방문이고 그 hexagon이 모두 비어 있다면**. 이 단서가 정확히
§10의 distinct-hexagon 조건이다.

**등급: 손증명** (조건부 부분 명시).

## 3. Exit 분류 (§4)

| 조인트 | orbit 보존 | 가능한 역할 |
|---|:---:|---|
| `w3:201` | 아니오 | fresh opening (O 슬롯) **또는** R (R 슬롯) |
| `w3:210` | 아니오 | fresh opening (O 슬롯) **또는** R (R 슬롯) |

**중요**: 착지 orbit과 phase는 **출발 port에 의존**하며 조인트만으로는
정해지지 않는다. 그래서 segment graph가 entry phase를 노드에 실어야
한다(§5).

## 4. Full-block transition graph (§6)

노드 \((\text{orbit},\text{entry phase})\), edge = "`EEEE` 실행 후
orbit-변경 exit".

| 항목 | 값 |
|---|---:|
| 노드 | **720** (= 144 orbit × 5 phase) |
| EEEE-then-exit 전이 | **1,440** (시도 1,440개 전부 성공) |
| out-degree | **모든 노드가 정확히 2** |
| dead end (out-degree 0) | **0** |
| target orbit이 source와 hexagon을 **공유하지 않는** 전이 | **720 (정확히 절반)** |

> **degree/dead-end 장애물은 존재하지 않는다.** graph가 완전히 규칙적
> (2-regular out)이다.
>
> 다만 **전이의 정확히 절반만 hexagon-disjoint**하다는 것은 기록해 둘
> 구조다 — full block 뒤 두 exit 중 하나만 완전히 새 orbit으로 간다.

이 graph는 **sound over-approximation**이다: 생성원 대수만으로 만들었고
방문된 hexagon·permutation을 무시하므로 실제 graph는 부분graph다.

**등급**: 정리 **손증명**, exit 분류 **exact segment graph**,
graph 수치 **sound over-approximation**.
