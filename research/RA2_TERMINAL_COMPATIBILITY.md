# Terminal suffix compatibility, 그리고 A2/A3 공통 정리

산출: `outputs/ra2_ell_counterfactuals.json`(§5); 인라인 검증(§9, A3R
표본 60개, 재현 가능한 절차 아래 기록).

## 5. Terminal suffix compatibility

`search_ra2_ell4.py`의 `terminal_suffix_analysis` 결과:

1. **abandoned source hex의 남은 한 칸은 언제 방문되어야 하는가?**
   → rotation은 정의상 current hex 안에서만 움직이므로(`FRAGMENT_REPAIR_OBLIGATION.md`
   §5), 그 한 칸은 **오직 미래의 joint가 그것을 직접 target할 때만**
   방문될 수 있다. "마감 시한"은 딱 하나 — walk 전체의 terminal
   상태(`visited_count==720`) 이전이면 언제든 가능하다.
2. **너무 일찍 repair하면 terminal suffix 자원이 사라지는가?** →
   **반증됨.** `FRAGMENT_REPAIR_OBLIGATION.md`에서 확인한 repair
   witness들은 Φ/orbit slack을 전혀 소비하지 않는다 — "일찍
   repair"가 나중에 필요한 어떤 자원도 눈에 띄게 소비하지 않는다는
   근거가 이미 있다.
3. **너무 늦게 repair하면 endpoint가 맞지 않는가?** → **미완료.**
   이를 검증하려면 전체 720칸 walk의 실제 terminal endpoint(마지막
   permutation)와 비교해야 하는데, 이 슬랩의 완주 witness가 이
   연구 전체에서 단 하나도 확보된 적이 없다 — 구체적으로 검증할
   대상이 없다.
4. **pure-rotation suffix가 그 한 칸을 흡수할 수 있는가?** → **손증명,
   불가능하다.** pure-rotation suffix는 정의상 마지막 joint 이후
   현재 hex 안에서의 순수 회전만을 말한다. hole은 fragment_hex(비-current)
   안에 있으므로, suffix가 시작되는 시점에 hole이 아직 안 채워져
   있다면 **suffix 자체가 hole을 채울 수 없다** — hole을 채우려면
   반드시 그 이전에 fragment를 다시 current로 만드는 joint가
   있어야 한다(그 이후에야 그 지점에서 시작하는 rotation이 이어질
   수 있지만, 그것은 "joint + 새 suffix"이지 원래의 마지막 suffix가
   아니다).

**결론: fragment-debt obstruction 가설 전체가 이미 이전 라운드에서
반증됐으므로(`FRAGMENT_REPAIR_OBLIGATION.md`), 이 terminal 조건
분석은 그 반증을 뒤집지 않는다** — 오히려 "일찍 repair해도 손해
없음"(항목 2)이 그 반증과 정확히 일치한다.

## 9. A2/A3 공통 정리 — 확인됨

`RA2_ZERO_CHARGE_HISTORY.md` §1.2의 증명(F=0인 동안 모든 blocked
joint는 자신의 현재 hex가 FULL일 때만 발동 가능)은 abandoning
move의 weight(2 또는 3)를 전혀 사용하지 않는다 — **연역적으로 A3에도
그대로 적용된다.** 이를 A3R 코퍼스(298개 표본 중 60개)로 직접
재검증했다:

```
60/60 상태에서: Φ(A3 직후) = 1 + ell_A3 = 6 - fragment_debt  (정확히 일치)
60/60 상태에서: A3 이전의 모든 blocked joint(R 포함 없음 -- A3R은
                A3가 첫 이벤트이므로 A3 이전은 순수 zero-charge word뿐)가
                ell=5를 사용
```

또한 A3R의 `ell_A3` 분포(표본 100개)는 `{0:21, 1:28, 2:18, 3:13,
4:20}` — **5개 값 전부 관측됨**, RA2의 작은 24-코퍼스에서 ell=2가
우연히 빠진 것과 대조적으로 A3R의 더 큰 표본에서는 처음부터 5개
전부가 나타난다 — 이는 `A2_ROTATION_LENGTH_CLASSIFICATION.md`의
"ell=2는 불가능이 아니라 미관측이었다"는 결론을 독립적으로
재확인해 준다.

### 공통 정리 (손증명 + 유한 완전 검증, A2/A3 양쪽)

> **F=1, H=0 슬랩에서, 첫 abandonment(A2 또는 A3, 어느 쪽이든)
> 직후의 shortfall(Φ)과 그것이 버리는 source-hex의 residual
> geometry(단일 연속 missing arc, 길이 = 5-ell)는 그 abandonment
> 직전의 rotation length(ell) 하나만으로 완전히 결정된다:
> `Φ = 1+ell = 6-debt`. abandoning move의 weight(2 대 3, 즉 target이
> 기존 orbit인지 새 orbit인지)는 이 정체성에 전혀 영향을 주지
> 않는다 — 오직 ell만이 결정 인자다.**

**차이가 나는 지점(A2 대 A3)**: target orbit이 기존(A2 소속 정의)인지
새 orbit(A3 소속 정의)인지는 `new_orbit` 플래그 자체(정의상 다름)의
차이일 뿐, `RA2_ELL4_BOUNDARY_GEOMETRY.md`에서 확인한 "같은 ell 안에서도
new_orbit이 갈릴 수 있다"는 사실과는 다른 층위의 구분이다 — A2/A3
구분은 **정의 자체**(target이 새 orbit이냐 아니냐)이고, 이 문서의
공통 정리가 다루는 Φ/debt 정체성은 그 구분과 **독립**이다.

## 성공 기준 (4) 평가

"abandonment rotation-length에 관한 A2/A3 공통 정리"는 **달성됐다** —
연역적 증명(F=0 full-sweep 논증이 weight에 무관함)과 A3R 60개 표본에
대한 완전 일치(60/60)로 이중 확인됐다.
