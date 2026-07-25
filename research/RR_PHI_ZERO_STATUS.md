# Φ=0 — 독립 산술 보조정리로서의 지위

산출: 직접 계산 재검증(`outputs/rr_full_relation_table.json`,
`outputs/rr_literal_witnesses.json` 재사용, 새 탐색 없음).

## 12. Chaining 구조와 Φ의 분리

**Φ(S) = 5 + 6·(TARGET_P − S.P) − (720 − S.visited_count)**는 오직
`P`(pass-start 개수)와 `visited_count`(방문한 permutation 개수)에만
의존한다 — orbit_masks, hex_masks의 세부 구조(어떤 orbit/hex가
언제 방문됐는지)는 전혀 참조하지 않는다. 반면 chaining/hub/same-component는
**전적으로** orbit_masks의 incidence 구조(union-find)에만 의존하며
`P`나 `visited_count`의 절대값과는 무관하다. **이 둘은 코드 정의상
완전히 독립적인 두 축이다.**

### 질문별 답

1. **chaining 구조를 증명하는 데 Φ가 필요한가?** — **아니오.**
   `RR_SAME_COMPONENT_CHAINING_PROOF.md` §10의 1-4단계 논증 전체가
   Φ를 단 한 번도 사용하지 않는다(union-find, `f1_normal_form`,
   `current_hex`, orbit-phase 대응만 사용).
2. **Φ=0은 chaining의 결과인가?** — **아니오, 논리적 함의가 아니다.**
   Φ는 orbit 구조를 전혀 모르므로 chaining/same이 Φ를 "결정"할
   메커니즘 자체가 없다.
3. **same-component의 별도 산술 결과인가?** — **부분적으로,
   그러나 인과관계가 아니라 공통 원인에 의한 상관관계다**(아래
   §확인).
4. **corpus 우연인가?** — **아니오, 정확한 산술적 필연이지만
   그 필연은 "same-component" 자체가 아니라 "이 10개 witness가
   공유하는 특정 macro-edge 개수·ell 시퀀스 패턴"에서 나온다.**

## 계산 재확인 — Φ=0의 정확한 산술적 원천

`Φ(initial_state()) = 6`(고정 상수, `TARGET_P=121, P=1,
visited_count=1`에서 직접 계산). `Φ(S') = Φ(S) + (ell−5)`이므로
`Φ_final = 6 − Σ(5−ell_i)`. 10개 witness 전부의 R2까지 macro-edge
ell 시퀀스를 직접 재생한 결과:

```
9/10(abandon_ell=4): ells = [4, 5, 5, 5, 0]  →  Σ(5-ell) = 1+0+0+0+5 = 6
1/10(abandon_ell=0): ells = [0, 5, 5, 5, 4, 5]  →  Σ(5-ell) = 5+0+0+0+1+0 = 6
```

**두 경우 모두 정확히 `Σ(5-ell)=6=Φ_initial`이므로 `Φ_final=0`이다
— 이는 우연이 아니라 정확한 산술이지만, 그 산술 자체가
"same-component"의 논리적 정의로부터 도출되는 것은 아니다.** 오히려
**공통 메커니즘**(라운드 12-13에서 확립: same-component가 되려면
R2가 hub completer 직후 즉시(`ell=0`) 발동해야 함, `RR_HUB_SECOND_TOUCH_THEOREM.md`)이
**두 가지 서로 다른 결과**를 동시에 만든다: (a) chaining/same
component 구조(orbit 일치를 통해), (b) 특정 ell 시퀀스 패턴(`ell=0`
발동이 반드시 포함되므로 `5-ell=5`라는 큰 기여를 만듦) — 이 (b)가
누적되어 정확히 `Φ_initial`(=6)과 상쇄되는 것은, **이 project의
전체 예산(`TARGET_P=121` 등)과 RR word 자체의 짧은 길이(depth≤6)가
만나는 지점에서 나오는 부가적 산술 우연**으로 보인다 — 완전히
일반적인 이유(왜 항상 정확히 상쇄되는지)는 규명하지 못했다.

## same-component RR ⟹ Φ(R2)=0 — 독립 손증명 후보 판정

**미완료.** 이 명제를 독립적으로(chaining 논증과 섞지 않고)
증명하려면 "same-component가 되는 모든 word는 정확히 5개 또는
6개의 macro-edge를 쓰고, 그 ell 시퀀스가 항상 `Σ(5-ell)=6`을
만족한다"는 것을 일반적으로 보여야 하는데, 이는 다시
"same-component가 되려면 word 구조가 이런 특정 형태여야 한다"는
것을 증명하는 문제로 귀결되며, 이는 §10의 미완료 gap(4단계)과
본질적으로 같은 난이도다. **corpus-exact(10/10)로만 표시하고,
"산술적 우연이 아니다"와 "완전히 일반적으로 증명됐다"를 명확히
구분한다.**

## 13. Terminal demand 정적 분석 (completion search 확대 없음)

`RR_PHI_ZERO_CONTINUATION.md`(라운드 13)의 결과를 재사용, 새 탐색
없이 요약만 갱신한다:

- **남은 ell=5 transition 수**: 미정(정확한 개수는 최종 완주 경로에
  의존하며 계산하지 않음).
- **hub 재사용 필요성**: `RR_HUB_TOUCH_COUNT.md`(라운드 13, 손증명)에
  의해 **불가능** — hub는 이미 2회로 닫혔다.
  이는 여전히 유효하며, 이번 라운드에서 재확인 필요 없음.
- **remaining orbit openings**: `TARGET_O − O = 25 − 2 = 23`개, 라운드
  12/13에서 이미 계산, 변경 없음.
- **final pure-rotation suffix**: `area_a_final` 판정에 이미 포함되는
  개념, 별도 분석 불필요(라운드 13 확인 사항 재확인).
- **endpoint compatibility**: 미결정(§`RR_PHI_ZERO_CONTINUATION.md` P1/P3
  참고, 라운드 13에서 이미 미결정으로 표시, 변경 없음).

**이번 라운드는 지시대로 completion search를 확대하지 않았다** —
새로운 안전 prune이 증명되지 않았으므로, 라운드 13의 INCOMPLETE
판정을 그대로 유지한다.
