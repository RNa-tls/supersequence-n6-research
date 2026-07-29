# non-\(O_*\) zero-charge parity — 분리 상태 (라운드 26)

과제 §15의 지시대로 이 문제는 \(O_*\) 정리와 **섞지 않는다**.
여기 있는 것은 데이터와 scope뿐이다.

산출: `src/verify_rr_o_star_gap.py` ->
`outputs/rr_o_star_excursions.json`의 `non_o_star_zero_charge` 필드.

## 1. Scope (정확히)

`outputs/rr_ordered_event_words.json`의 **\(O_*\) 착지 완성 95개**.
abandonment 이후 depth ceiling 6의 root-local exhaustive 열거이며,
**일반 RR 주장이 아니다.**

## 2. 관측

| 항목 | 값 |
|---|---|
| \(\#Z_{\to\text{other}}\) 총계가 짝수인 완성 | **95 / 95** |
| 개별 orbit 중 홀수 count를 갖는 orbit이 하나라도 있는 완성 | **5 / 95** |

## 3. 판정 — 과제 §16의 목표 정리는 반증됨

> **검사한 명제**: "모든 non-\(O_*\) orbit은 짝을 이루는 excursion으로
> 진입·이탈한다."

**반증됨.** 그것이 참이면 **모든 개별 orbit**의 zero-charge count가
짝수여야 하는데, 95개 중 **5개 완성에서 어떤 개별 orbit이 홀수 count를
갖는다.** 총계가 짝수인 것은 홀수 orbit들이 **짝수 개** 나타나 서로
상쇄되기 때문이며, orbit별 짝짓기 때문이 아니다.

따라서 \(O_*\)에 대해 얻은 excursion 구조는 다른 orbit으로 **그대로
이전되지 않는다.** 차이의 원인은 과제가 나열한 그대로다:

- non-\(O_*\) orbit에는 distinguished nearest phase가 없다
- completer의 target이 아니다
- 초기 visited mask가 다르다(abandonment가 등록하지 않았다)
- R ancestry에서 맡는 역할이 없다

## 4. 남는 것

\(\#Z_{\to\text{other}}\) 총계 짝수성(95/95)에 대해서는 **어떤 논증도
없다** — \(O_*\) 논증의 유사물이 성립하지 않음이 위에서 확인됐으므로,
새로운 메커니즘이 필요하다.

**등급**: 95/95 관측은 **root-local exhaustive**(명시된 scope 안에서),
orbit별 짝짓기 명제는 **반증됨**, 총계 짝수성의 설명은 **미완료**.

## 5. 전체 parity와의 관계

\(|P|+\#R_{\le C}\equiv1 \pmod 2\)를 닫으려면 \(O_*\) 부분과
non-\(O_*\) 부분이 **모두** 필요하다. 현재 둘 다 미완료이며,
\(O_*\) 부분은 이번 라운드에 주요 경로가 닫혔다
(`RR_O_STAR_ZERO_PARITY.md`). 두 문제를 합치려는 시도는 하지 않는다.
