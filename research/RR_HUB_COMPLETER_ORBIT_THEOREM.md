# Hub completer orbit 정리 — 원래 목표의 반증과 abandon-ell별 재구성

산출: `src/analyze_rr_hub_completer_orbits.py` -> `outputs/rr_hub_completer_candidates.json`.

## 정직한 선언: 원래 목표 정리(§4)는 반증됐다

> **원래 목표: "O≠O_R인 candidate는 적어도 하나의 exact legality
> condition을 반드시 위반한다."**
>
> **판정: 반증됨(exact witness).**

`989d2261b458`의 abandon 직후 상태에서 depth≤6 **완전탐색**
(exhaustive, frontier 완전 소진, 1,174개 노드)을 실행한 결과, hub
(hex0)의 **5개 남은 위치 전부가 legal한 completing candidate**로
확인됐다 — orbit `{1, 3, 9, 33, 120}` 모두 도달 가능하며, 각각
R(existing), Z2(existing), 심지어 Z3(**fresh**, `new_orbit=True`)
타입으로도 도달 가능한 경우가 있다:

```
orbit 1:   count 11, kinds {Z3, R, Z2}, min_depth 3
orbit 3:   count 3,  kinds {R},         min_depth 5
orbit 9:   count 9,  kinds {Z3, R, Z2}, min_depth 4
orbit 33:  count 12, kinds {Z3},        min_depth 3
orbit 120: count 19, kinds {R, Z2},     min_depth 1  (실제 R1이 사용한 candidate)
```

이는 원래 §1(hub completer 정의)의 전제("hub completer 후보가
개념적으로 좁게 제한된다")와 §4의 목표(단일 candidate만 legal)를
**정면으로 반증**한다 — hub가 "누구에 의해" 완성되는지는 결코
유일하게 강제되지 않는다, **적어도 남은 위치가 2개 이상인 경우에는.**

## 결정적 재구성: abandon ell이 completer 후보의 개수를 결정한다

hex0의 6개 위치는 `[orbit0(anchor), orbit120, orbit33, orbit9,
orbit3, orbit1]` 순서로 고정돼 있다(§`RR_HEX0_NECESSITY_THEOREM.md`
계산 재확인). word의 첫 joint(hidden abandonment)가 `ell=k`에서
발동하면, 위치 `0..k`가 방문되고 **`5-k`개**의 위치가 미방문으로
남는다 — 이것이 곧 hub completer의 candidate 개수다.

**전체 10개 same-component witness의 abandon ell 분포**:

```
python3 src/analyze_rr_hub_completer_orbits.py
9/10: abandon_ell=4  → candidate 정확히 1개(orbit 1)
1/10: abandon_ell=0  → candidate 5개(orbit 1,3,9,33,120)
```

**전체 4,470개 코퍼스에서 abandon ell 분포(전수 재확인)**:

| abandon ell | 전체 개수 | same-component 개수 |
|---:|---:|---:|
| 0 (5개 후보) | 200 | 1 |
| 1 (4개 후보) | 204 | 0 |
| 2 (3개 후보) | 205 | 0 |
| 3 (2개 후보) | 208 | 0 |
| 4 (**1개 후보**) | 206 | **9** |

**corpus-exact 관측(새로 발견)**: same-component는 abandon
ell=1,2,3(후보 2-4개)에서는 **단 한 건도 나타나지 않는다**(0/617) —
압도적으로 ell=4(후보 정확히 1개)에서 발생한다.

## Lemma C의 재구성 — ell=4 하위 케이스에서는 완전 손증명 성립

### Lemma C′ (ell=4 하위 정리) — **완전 손증명**

> abandon이 `ell=4`에서 발동하면, hub(hex0)의 미방문 위치는
> **정확히 1개**이고, 그 위치가 속한 orbit(순열 위치표에 의해
> 고정적으로 결정됨, `orbit 1`)이 hub completer의 **유일하게
> 가능한** candidate다 — `O≠1`인 candidate는 개념적으로 존재하지
> **않는다**(legality 위반이 아니라,애초에 그런 candidate 자체가
> 없다 — 훨씬 강한 형태).

**증명**: `HEX_POSITION`과 `ORBIT_PHASE`의 코드 정의로부터 순수
조합론적으로 확인된다 — hex0의 6개 위치는 6개의 서로 다른 orbit에
1:1 대응(라운드 11 §1.2에서 이미 손증명)되므로, `ell=4`에서
abandon(위치 0-4 방문)하면 남는 위치는 정확히 1개(위치 5, orbit
1)뿐이다. □

**따름정리(즉각적, 손증명)**: `ell=4` 케이스에서 hub가 실제로
완성된다면(2번째 touch가 발생한다면), 그 completer의 orbit은
**반드시 orbit 1**이다 — 선택의 여지가 없다. **그러므로 이
하위집단에서 "same이 나오려면 completer orbit = R1 target orbit"은
"R1의 target이 orbit 1이어야 한다"는 단일하고 검증 가능한 조건으로
완전히 환원된다.**

### ell≠4 케이스(ell=0,1,2,3) — **미완료**

`ell=0`(989d2261b4가 속한 유일한 관측 사례)은 5개의 candidate가
legal하게 공존하므로, "completer orbit이 유일하게 결정된다"는
강한 형태의 정리는 **성립하지 않는다**. 대신 §9(별도 문서)의 심층
bounded search(depth≤12, node_cap=150,000, 부분탐색 — frontier
287,322개 잔존, exhaustive 아님)가 same+non-chaining 반례를 찾지
못했다는 **국소 증거**만 있다 — 완전 손증명은 아니다.

`ell=1,2,3`은 이 코퍼스에서 same-component 자체가 **한 건도
관측되지 않았으므로**(0/617), 이 하위집단에 대한 Lemma C의 참/거짓
여부는 **판정할 데이터 자체가 없다** — 미완료.

## 성공 기준 (1) 평가

**부분 달성**: "hub completer target orbit = R1 target orbit"의
**일반(모든 abandon ell) 손증명은 달성하지 못했다.** 그러나
**abandon ell=4라는 corpus에서 압도적으로 지배적인(9/10)
하위경우에 대해서는 완전한 손증명을 얻었다** — 이는 순수한
조합론(hex0의 위치-orbit 1:1 대응 + ell=4가 남기는 유일한 빈
자리)에서 직접 도출되며, corpus나 탐색에 의존하지 않는다.
