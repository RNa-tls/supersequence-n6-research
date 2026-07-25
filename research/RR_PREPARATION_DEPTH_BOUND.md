# Preparation depth 상한 — 비자명한 자원 상한 미발견 (라운드 21)

산출: `src/verify_rr_preparation_parity.py` ->
`outputs/rr_preparation_depth_resources.json`. completion search 없음.

## 12. "무한 성장"의 정확한 재정의 (§12의 요구)

n=6 상태공간은 유한하므로 literal history family는 당연히 유한하다.
따라서 여기서 문제 삼는 것은:

> **현재 bounded depth에서 안정화하는가, 아니면 depth를 올릴 때마다
> 새로운 same-component preparation family가 계속 나타나는가?**

관측:

| depth 상한 | ell=4 same states | ell=0 same states |
|---:|---:|---:|
| 6 (word_start) | 3 (\|P\|=2) | 1 (\|P\|=2) |
| 7 | 5 (\|P\|=2,4) | 1 |
| 8 | 5 | 3 (\|P\|=2,4) |
| 9 | 9 (\|P\|=2,4,6) | 3 |
| 10 | — | 5 (\|P\|=2,4,6) |

**depth를 2 올릴 때마다 각 분기에서 새 \(|P|\) 길이가 하나씩
추가된다.** 안정화의 징후가 전혀 없다.

## 13. 단조 자원 후보 검사 — 전부 실패

각 preparation edge가 소비하는 유한 단조 자원을 찾으면
\(d_{\text{prep}}\le B\) 형태의 상한이 나온다. 후보별 판정:

| 자원 후보 | 판정 |
|---|---|
| fresh E-orbit (`F` edge가 소비) | **실패.** `E` edge는 새 orbit을 전혀 쓰지 않는다. \|P\|=6인 `EEFEEE`는 fresh를 **1개만** 쓰고 O=3에 머문다 — 길이가 늘어도 orbit 소비가 비례하지 않는다. |
| 미방문 phase | **실패(부분적).** phase는 소비되지만 orbit당 5개씩 144 orbit이 있어 상한이 720 규모로 자명하다. |
| 미터치 hexagon | **실패(자명).** 120개 hexagon — 자명한 상한만 준다. |
| component root 수 | **실패.** `E` edge는 component 수를 바꾸지 않는다. |
| permutation 수 | **자명한 상한**(720). |
| \(\Phi\) 예산 | **실패.** 모든 준비 edge가 `ell=5`라 \(\Phi\) 기여가 0이다 — \(\Phi\)는 준비 길이를 전혀 제약하지 않는다(`RR_PREPARATION_PARITY_THEOREM.md` §2 P2). |

**핵심 장애물**: 관측된 준비 단어의 대부분이 `E`(기존 orbit
zero-charge 전이)인데, **`E` edge는 어떤 단조 자원도 소비하지
않는다** — O 불변, fresh 불변, \(\Phi\) 기여 0. 실제로
\|P\|=6인 `EEFEEE`는 `E`를 5개 쓰면서 O를 2에서 3으로만 올린다.

## 판정

> **비자명한 자원 상한을 찾지 못했다 — 미완료.**
> 유일하게 유효한 상한은 자명한 것(유한 상태공간, 720
> permutation)뿐이며, 이는 §13이 명시적으로 배제한 형태다.
>
> 나아가 관측 추세(depth +2마다 새 \(|P|\) 길이)는 **작은 상한이
> 존재하지 않는 쪽을 시사**한다. `E` edge가 자원을 소비하지 않는
> 한, 준비 구간이 짧게 묶일 구조적 이유가 보이지 않는다.

**성공 기준 4(preparation depth의 비자명한 자원 상한) 평가:
미달성.** 억지 상한을 만들지 않고 실패로 보고한다.


## 라운드22 정정 — "E는 어떤 단조 자원도 소비하지 않는다"는 틀렸다

위 §13은 "`E` edge는 어떤 단조 자원도 소비하지 않는다(O 불변, fresh
불변, Φ 기여 0)"고 썼다. 라운드22가 48개 preparation edge 전부의
증분을 직접 측정한 결과:

- **touched hexagon 수: 모든 edge에서 정확히 +1** (48/48)
- **visited permutation 수: 모든 edge에서 정확히 +6** (48/48)

즉 `E`도 **hexagon과 permutation이라는 단조 자원을 확실히 소비한다.**
정확한 서술은 "**`E`는 orbit 수준 자원(O, fresh count)을 소비하지
않는다**"이며, 그 결과 나오는 상한은

\[
|P| \le 118 \quad(\text{미터치 hexagon}), \qquad |P| \le 119 \quad(\text{미방문 permutation})
\]

로 **여전히 자명한 상태공간 상한 수준**이다. 따라서 §13의 결론
("비자명한 상한 미발견, 미완료")은 그대로 유지되지만, 그 이유는
"자원을 안 쓴다"가 아니라 "**쓰는 자원이 너무 커서 유용한 상한을
주지 못한다**"로 정정된다.
