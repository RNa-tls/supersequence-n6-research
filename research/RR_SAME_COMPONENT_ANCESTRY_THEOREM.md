# Same-component ancestry 정리 (라운드 21)

산출: 라운드20 `outputs/rr_decorated_ablation.json` 재사용 +
그래프 논증. 새 계산 없음.

## 17. 정리

> **정리 (부분 손증명 + root-local exhaustive)**: F≤1 예산의 RR
> word에서, R2 boundary의 두 endpoint orbit \(q_s, q_t\)에 대해
> 다음 셋은 동치다.
>
> 1. `same-component`: incidence graph에서 \(q_s\)와 \(q_t\)가 같은
>    연결 성분에 속한다.
> 2. \(q_s\)와 \(q_t\)가 **둘 다 hub 노드에 연결**되어 있다(= 두
>    hub 거리가 모두 유한).
> 3. \(q_s\)에서 \(q_t\)로 가는 **모든 최단경로가 hub 노드를
>    지난다**(LCA 형).
>
> 측정: 세 predicate 모두 tp=6, fp=0, fn=0 (라운드20, 2,234개 경계).

## 방향별 논증

### (2) ⟹ (1) — 손증명, 자명

둘 다 hub에 연결되어 있으면 hub를 경유해 서로 연결되므로 같은
성분이다. 그래프 가정: 없음(연결성의 정의만 사용).

### (1) ⟹ (2) — Unique Hub Hexagon lemma 사용

**Unique Hub Hexagon lemma**(라운드12, 손증명): F≤1 예산 하에서
**2회 이상 터치되는 hexagon은 최대 1개**(= hub)뿐이다.

incidence graph는 이분 그래프이며, orbit 노드 \(q\)와 hexagon 노드
\(h\) 사이에 간선이 있다는 것은 "\(q\)의 어떤 phase가 \(h\) 안에서
방문됐다"는 뜻이다. hexagon 노드의 **차수(degree)** 는 그 hexagon
안에서 방문된 서로 다른 orbit의 개수와 같다.

한 번만 터치된 hexagon은 그 안에서 방문된 위치가 **하나의 연속
회전 구간**뿐이고, 그 구간이 hexagon 전체를 덮지 않는 한 여러 orbit을
담을 수 있다 — 따라서 차수가 2 이상일 수 있다. **여기가 논증의
빈틈이다**: "hub만이 두 orbit을 잇는 합류점"이라는 주장은
Unique Hub Hexagon lemma에서 **직접 따르지 않는다**.

> **정직한 판정**: (1) ⟹ (2)는 **일반적으로 손증명되지 않았다.**
> 관측(fp=0, 2,234/2,234)으로만 뒷받침된다 — **root-local
> exhaustive**.

### (2) ⟺ (3) — 조건부 손증명

(3) ⟹ (2)는 자명하다(경로가 존재하므로 둘 다 연결).

(2) ⟹ (3)에는 추가 가정이 필요하다: \(q_s\)-\(q_t\) 사이에 **hub를
지나지 않는 경로가 없어야** 한다. 이는 다시 "hub가 유일한 합류점"
이라는 위와 같은 가정이며, 같은 이유로 **일반 손증명 미완료**다.

## 종합 판정

| 방향 | 등급 | 필요한 그래프 가정 |
|---|---|---|
| (2) ⟹ (1) | **손증명** | 없음 |
| (1) ⟹ (2) | **root-local exhaustive** | "hub가 유일한 orbit 합류점" — 미증명 |
| (2) ⟹ (3) | **root-local exhaustive** | 동일 |
| (3) ⟹ (2) | **손증명** | 없음 |

> **라운드20이 "그래프적 이유는 이미 손증명된 Unique Hub Hexagon
> lemma"라고 쓴 것은 과잉주장이었다.** 그 lemma는 "2회 이상 터치된
> hexagon이 유일"함을 주지만, 1회 터치 hexagon도 여러 orbit을 담을
> 수 있으므로 "유일한 합류점"까지는 주지 않는다. 이번 라운드에서
> 그 간극을 명시하고 등급을 낮춘다.

**성공 기준(§17) 평가**: **부분 달성** — 두 방향은 손증명, 나머지
두 방향은 명시된 미증명 가정에 의존하는 root-local exhaustive.

## 18. Chaining과 terminal block

> **후보**: "final completer가 \(O_*\)를 만들고 즉시 다음 R2의
> source가 \(O_*\)이면 chaining이다."

**이는 정의의 재진술이다.** chaining ≡ (R1 target = R2 source)이고,
terminal normal form에서 R1 target = \(O_*\) 이므로 위 조건은
"R2 source = \(O_*\) = R1 target"과 같은 말이다. 새로운 내용이 없다.

**그러나 라운드21이 확립한 P1(손증명)은 실질적 내용을 준다**:
\(\ell=4\)에서는 hub exit 위치의 orbit이 \(O_*\)와 **일치**하므로,
hub를 떠나는 첫 조인트가 R2이면 **chaining이 자동**이다. 즉

> **\(\ell=4\)에서 "R2가 hub exit edge 자신이다" ⟹ chaining.**
> (`RR_PREPARATION_PARITY_THEOREM.md` §2 P1, 손증명)

이것은 R2 실행 **이전의** boundary 조건(어느 edge가 hub exit인가)
으로 chaining을 강제하므로, §18이 요구한 "더 이른 predicate"에
해당한다. 다만 \(\ell\ne4\)에는 적용되지 않으므로 **필요충분조건은
여전히 미완료**다.
