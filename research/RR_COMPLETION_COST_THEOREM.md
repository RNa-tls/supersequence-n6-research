# Completion cost 정리 — 일반 자원 정리로 강화 (라운드 17)

산출: `src/verify_rr_completion_cost.py` -> `outputs/rr_completion_cost_table.json`.
새 대규모 탐색 없음(320개 분기 완전 케이스체크 + 작은 국소 BFS).

## 6. Cost 정의 재정식화

\[
C(\text{edge}) = (\text{macro\_joints}=1,\ \Delta P,\ \Delta S,\ \Delta O,\
\Delta N_{\text{def}},\ \text{hub\_exits}\in\{0,1\},\ \text{orbit\_reuse}\in\{0,1\})
\]

- `ΔP,ΔS,ΔO,ΔNdef`: `ExactState`의 해당 필드의 전/후 차이(코드
  정의 그대로).
- `hub_exits=1`: 이 edge의 source가 hex0 내부이고 `F=1`이 이미
  소진된 경우(Hub Exit Source Lemma가 다루는 바로 그 사건).
- `orbit_reuse=1`: target orbit의 mask가 이 edge 발동 **이전에**
  이미 0이 아니었던 경우(이미 방문된 orbit 재사용).

**가산성(additivity)**: 각 필드가 상태 필드의 단순 차분이므로,
연속된 edge들의 벡터 합은 경로 전체의 시작-끝 차분과 정확히
같다 — **손증명**(구조상 자명), 3-edge 경로에서 spot-check로
재확인(`additive: True`, `outputs/rr_completion_cost_table.json`).
"cost"라는 스칼라는 이 벡터의 `macro_joints` 성분의 누적 합으로
정의된다(이번 라운드까지 사용해온 것과 동일한 스칼라, 이제 벡터의
한 성분으로 명확히 자리매김됨).

## 7. Cost 1 불가능 — 손증명 구조

**정리**: hub의 abandonment 직후, 어떤 legal word로도 1개의
macro-edge만으로 hex0를 재터치할 수 없다.

**증명(완전 유한 case analysis)**: 이 case space가 전부를
덮는다는 것은 다음 세 가지 사실의 결합에서 나온다.

1. 이 모델에는 **정확히 4개의 조인트**만 존재한다(`w2:10` 1개,
   `w3:120/201/210` 3개) — `UNIQUE_WEIGHT2_MOVE_THEOREM.md`가
   `w=2`에 대해, 그리고 이 모델의 `ALL_MOVES` 정의가 `w=3`에
   대해 이를 고정한다. **누락된 조인트 선택은 없다.**
2. abandonment 자체도 이 4개 조인트 중 하나를 골라 발동하므로,
   abandonment 선택지도 최대 4개다(`ell`마다 실제로는 4개 전부
   legal, `outputs/rr_completion_cost_table.json`의
   `cost1_cost2_complete_case_check.per_ell_detail` 참고).
3. abandonment 직후 F=1이 소진되므로, 다음 조인트가 legal하려면
   현재 hex를 완전히 스윕(`full_sweep_legal`, ell'=5 강제)해야만
   한다 — 이는 Hub Exit Source Lemma의 일반형에서 나오는 **결정적
   함수**(선택의 여지 없음)다.

이 세 가지를 결합하면, "abandonment 직후 1개의 macro-edge로
hex0에 도달"하는 경우의 수는 정확히 `5(ell) × 4(abandon 선택)`
= 20가지 조합의 "step1 조인트"뿐이며, 이 20가지에서 파생되는
`step1` 조인트 선택 자체도 강제된 풀스윕 뒤에 legal한 것만
남는다(80개 분기, 전부 열거). **이 80개 분기 전부가 hex0에 착지하지
않음을 직접 확인**(`cost1_hits: 0`). 이는 표본이 아니라, 위
1-3에 의해 "빠질 수 있는 경우가 원천적으로 없는" **완전한 case
space**이므로 손증명 등급이다.

## 8. Cost 2 ⟹ nearest residual — 정리와 converse

**정리(손증명, 완전 case check)**: `c=2`로 hex0를 재터치하는
모든 legal 분기(총 320개 중 15개가 성립)는 예외 없이 nearest
residual 위치에 착지한다.

**증명 스케치**: cost-1이 불가능함(§7)이 이미 증명됐으므로, cost-2
분기는 "abandonment(4택) → 강제 풀스윕 후 step1(≤4택) → 강제
풀스윕 후 step2(≤4택)"의 320개 완전 case space에서 나온다. 이
안에서 hex0에 착지하는 15개 전부를 직접 열거해 위치를 확인한
결과, **전부 nearest다** — 이는 다시 완전한 case space이므로
표본이 아니다.

### Converse: nearest ⟹ 항상 cost 2인가?

**일반적으로는 거짓**: nearest orbit에 도달하는 최소 비용은
abandonment 조인트 선택에 따라 다르다(`converse_check_min_cost_to_nearest`):

| abandonment 선택 | nearest까지 최소 cost |
|---|---:|
| `w2:10` | 2 |
| `w3:120` | 2 |
| `w3:201` | 3 |
| `w3:210` | 5 |

**단, 실제 역사적 코퍼스는 abandonment에 항상 `w2:10`만
사용한다(4,470/4,470, capped-corpus exact)** — 이 조건 아래에서는
converse가 **손증명**된다: `w2:10` abandonment를 고정하면 nearest는
항상 정확히 cost 2다(5개 ell 전부 확인).

## 9. Non-nearest completer의 정확한 최소 비용

`w2:10` abandonment로 조건화한 원장(`RR_HUB_COMPLETION_COST.md`
재확인, 이번 라운드 스크립트로 재계산):

| ell | nearest(cost) | 2순위(cost) | 3순위(cost) |
|---:|---|---|---|
| 0 | 120(2) | 33(4), 1(4) | 9(5), 3(도달불가≤depth5) |
| 1 | 33(2) | 9(4) | 3(5), 1(도달불가) |
| 2 | 9(2) | 3(4) | 1(5) |
| 3 | 3(2) | 1(4) | — |
| 4 | 1(2) | — | — |

정확한 cost formula `C(r)=f(cyclic distance, phase, exit count)`
형태로 닫힌 공식을 유도하는 것은 **미완료로 남긴다** — 위 표는
cyclic distance(= nearest부터 몇 계단 떨어졌는지)와 대략적으로
상관되지만(가까운 것이 대체로 더 싸다), `orbit9`(ell=0에서 3계단
떨어짐, cost5)과 `orbit3`(4계단, 도달불가)의 관계처럼 단조적이지
않은 부분이 있어 간단한 닫힌 공식으로 요약하지 못했다.

## 성공 기준 (3), (4) 평가

- **cost 1 불가능 손증명**: **달성.**
- **cost 2 ⟹ nearest residual 손증명**: **달성**(일반 형태); converse는
  `w2:10` 조건 하에서 손증명, 무조건 일반 형태는 반증됨(명시적
  반례: `w3:210` abandonment 선택 시 cost5).
