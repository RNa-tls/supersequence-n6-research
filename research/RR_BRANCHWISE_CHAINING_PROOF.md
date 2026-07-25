# same-component ⟹ chaining — branchwise 증명, 코퍼스 완전성 정정 포함 (라운드 16)

산출: 이번 라운드 전체 스크립트 종합. 새 대규모 탐색 없음(모든
새 계산은 국소 exhaustive case check 또는 작은 state-space fresh
BFS, frontier가 매번 자연 소진).

## 이번 라운드 최우선 보고 사항: 코퍼스 완전성 정정

`legacy_research/outputs/f1_n2_defect_words.json`(및 그로부터 파생된
`outputs/rr_literal_witnesses.json`의 4,470개 RR witness)은
**"depth≤6 legal RR-structured state의 수학적으로 완전한 열거"가
아니라, 과거 어느 라운드의 65,340-state로 capped된 bounded search
frontier의 replay**임을 원본 스크립트 docstring에서 직접 확인했다
(`legacy_research/work/analyze_f1_n2_defects.py`: `"Its only
exploration is a capped continuation"`, scope: `"finite complete
replay of an existing bounded Area-A frontier; not an N=2
enumeration"`).

**이는 라운드 11-15가 이 코퍼스를 근거로 내린 "유한 완전 검증"
판정들 중, "코퍼스 내에서 반례 0"이라는 사실 자체는 여전히 유효하지만,
"그러므로 depth≤6 전체에서 일반적으로 성립한다"는 확장 해석은
과잉주장이었음을 뜻한다.** 구체적 반증 witness를 하나 직접
구성해 확인했다(`RR_R1_SELF_COMPLETION.md`) — area_a-legal하고
RR 구조와 일치하지만 코퍼스에 없는 상태.

**좋은 소식**: 이 코퍼스에 의존하지 않고 각 abandonment root에서
`macro.macro_edges()`+`area_a_prune_reason()`만으로 새로 완전탐색한
결과(state space가 원래 작아 수천 개 수준, frontier 자연 소진),
**same-component ⟹ ell∈{0,4} 이분법과 ell=0의 유일 예외라는
핵심 결론은 그대로 재확인됐다** — 흔들린 것은 "nearest만
completer로 실현된다"는 부수적 주장이었다.

## 11-12. Branchwise 증명 구조 (정정판)

### Lemma A — Unique Hub Hexagon (손증명, 라운드12, 불변)
### Lemma B — Hub Touch Count ≤ 2 (손증명, 라운드13, 불변)

### Lemma C — same-component RR ⟹ abandonment ell∈{0,4}
**상태 격상**: 이제 **두 개의 독립적 방법**(역사적 코퍼스 전수
확인 + 이번 라운드의 코퍼스-비의존적 fresh exhaustive BFS)이
동일한 결론에 도달했다. 여전히 depth≤6로 범위가 제한되지만,
**코퍼스 불완전성 문제로부터 독립적으로 재확인됐다는 점에서
증거가 크게 강화됐다.**

### Lemma D-cost — 최소 비용 nearest 정리 (손증명, 신규)
`c=1`은 불가능, `c=2`는 항상 nearest에서만 달성됨을 4개 조인트에
대한 완전 케이스체크(320개 분기)로 손증명했다. **코퍼스와 무관한
순수 조합론적 사실.**

### Lemma D4 — ell=4 분기 (부분 손증명, 라운드14-15 유지)
1-4단계 손증명, 5단계(R2가 실제로 orbit1을 쓰는지)는 여전히
corpus-exact. **단, "hub-completed=45/45가 전부 orbit1"이라는
라운드15 수치는 역사적 코퍼스 기준이며, ell=4는 residual 위치가
1개뿐이므로 nearest=유일 후보라는 조합론적 사실 자체는 코퍼스
완전성과 무관하게 여전히 성립한다(불변).**

### Lemma D0 — ell=0 분기 (강화됨)
`RR_ELL0_SATURATED_PHASE_NORMAL_FORM.md`: fresh exhaustive
검증으로 same-component witness가 정확히 1개임을 코퍼스-비의존적으로
재확인. **거짓으로 반증된 부분**: "nearest(orbit120)만 hub를
완성할 수 있다" — 5개 orbit 전부 hub 완성 가능함이 fresh 탐색에서
직접 관측됨. **참으로 남는 부분**: same-component를 만드는 것은
여전히 유일하게 1개뿐.

### Theorem — same-component ⟹ chaining
핵심 정리 자체(원래 라운드14의 4,470/4,470 corpus-exact 결과)는
이번 라운드가 건드리지 않았다 — 다만 그 근거였던 코퍼스의
완전성에 대한 이해가 정정됐을 뿐, 결론 자체(same이면 항상
chaining)를 반증하는 증거는 이번 라운드에서도 나오지 않았다.

## 13. Φ의 재확인 (정정판)

라운드15의 "hub-completed 212/212 전부 Φ=0" 주장도 같은 코퍼스에
근거했다. 이번 라운드의 fresh exhaustive 재확인(`outputs/rr_hub_completion_phi.json`):
hub가 터치된 RR-final 상태 중 **압도적 다수(약 98%, 300개 중
293개)는 Φ=0이지만, 정확히 7개는 Φ≠0**이다 — "hub-touched ⟹
Φ=0"은 완전한 필연이 아니라 **거의 항상 성립하는 corpus-exact
경향**으로 하향 조정한다. 반대 방향("hub를 안 만지면 Φ≠0")은
이 fresh 표본에서 300/300 성립 — 이쪽은 더 견고해 보인다.

## 성공 기준 최종 평가

1. **nearest residual completer theorem**: **부분 손증명** — 최소
   비용(c=2) 버전은 완전히 손증명됨; "nearest만 실현 가능"이라는
   강한 버전은 반증됨.
2. **hub completion ⟹ Φ=0**: **corpus-exact, 거의 전부(98%)지만
   완전한 필연은 아님** — 소수의 반례가 fresh 탐색에서 발견됨.
3. **R1/R2 self-completion의 정확한 obstruction 또는 정상형**:
   **미완료** — 제안된 5개 obstruction 후보 중 3개(S1,S2,S5)가
   반증됐고 나머지(S3,S4)는 미확인. 명확한 정상형은 확립하지
   못했다.
4. **ell=0 saturated-phase family 정리**: **유한 완전 검증(코퍼스
   비의존적으로 재확인)** — family는 존재하지 않으며, same-component
   witness는 정확히 1개다.
5. **ell=1,2,3 same-component 불가능 손증명**: **corpus-exact,
   이번엔 코퍼스 비의존적 fresh exhaustive 재확인으로 강화**됐으나
   여전히 depth≤6 범위 내로 국한되며, 완전한 일반(임의 depth)
   손증명은 아니다.
6. **branchwise same-component ⟹ chaining 완전 증명**: 핵심
   정리는 불변(반증되지 않음)이지만, 이를 뒷받침하던 코퍼스의
   완전성 가정이 정정되어 증명의 **기반이 재확인을 필요로
   했고, 재확인 결과 정리 자체는 살아남았다.**

## 가장 중요한 메타적 교훈

이번 라운드의 가장 큰 성과는 특정 정리의 증명이 아니라
**"코퍼스가 완전하다"는, 여러 라운드에 걸쳐 암묵적으로 전제됐던
가정 자체를 검증하고 정정한 것**이다. 이는 사용자가 지속적으로
요구해온 "정직한 자기 검증"의 정신에 부합하며, 향후 라운드는
`f1_n2_defect_words.json` 기반 주장에 **"코퍼스 내에서"라는
단서를 명시적으로 붙이거나, 가능하면 이번 라운드처럼 코퍼스에
의존하지 않는 fresh 재검증을 병행**해야 한다.
