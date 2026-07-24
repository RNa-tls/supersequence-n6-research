# Combined classifier: critical-restart signature + ell_A2=4

산출: `src/verify_critical_restart_classifier.py` -> `outputs/ra2_combined_classifier.json`.

## 결론 먼저

> **classifier: predicted_U4 = (critical restart의 target orbit이
> R의 target orbit과 다름) AND (ell_A2 == 4)**
>
> **RA2 24개 전체에서: TP=4, FP=0, TN=20, FN=0 — 완전히 정확하다.**

이는 **RA2 24개 코퍼스에 대한 정확한 classifier(corpus exact
classifier)**다 — 아직 일반 정리(모든 depth, 모든 가능한 RA2
상태에 대해 성립한다는 증명)라고 부르지 않는다. 정의는
`RA2_FIVE_STATE_COMPARISON.md`에서 수정한 모호함 없는 버전을
사용한다(component_relation이 아니라 리터럴 orbit 인덱스 직접
비교).

## 2. 24개 전체 confusion matrix

| 결과 | 개수 |
|---|---:|
| True Positive(U4로 정확히 예측) | 4 |
| False Positive | 0 |
| True Negative | 20 |
| False Negative | 0 |

`signature_unrelated`(critical restart가 R의 orbit과 다름)만
단독으로는 5개 상태(U4 4개 + outlier 1개)에서 참이다 — **이
성분 하나로는 U4를 완전히 가르지 못한다**(outlier가 반례). 하지만
`ell_A2==4`와 결합하면 정확히 U4 4개만 남는다.

**중요한 자기비판**: `ell_A2==4`는 이미 이전 라운드들에서
단독으로도 U4를 완전히(24/24, 0 오류로) 식별하는 것으로 확립됐다
(`RA2_ZERO_CHARGE_HISTORY.md`). 즉 이번 결합 classifier의 완벽한
정확도는 **`ell_A2==4`라는 이미 알려진 완전한 판별자에 의해 이미
보장돼 있다** — `signature_unrelated` 성분은 이 24개 코퍼스
안에서는 **추가 판별력을 제공하지 않는다**(정직하게 기록: 이는
새로운 독립 classifier가 아니라, 이미 알려진 classifier에 부수적
성분을 덧붙인 것). signature_unrelated의 진짜 가치는 다른
곳에 있다: **U4를 특징짓는 구조적 서명(critical restart 유형)을
제공한다는 것**이지, ell_A2를 대체하거나 능가하는 새 판별력을
제공한다는 것이 아니다.

## 성공 기준 (1) 평가

"critical restart signature + ell_A2=4가 RA2 24개에서 U4의 정확한
필요충분 classifier"는 **corpus exact classifier로서 달성됐다**
(24/24, 0 오류) — 다만 정직하게, 그 정확도의 원천은 `ell_A2=4`
단독 항이며, signature 성분은 판별력을 추가하지 않는다는 것을
함께 기록한다. 이를 "새로운 독립 정리"라고 과장하지 않는다.
