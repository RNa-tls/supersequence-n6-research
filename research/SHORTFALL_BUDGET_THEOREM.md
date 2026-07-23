# Shortfall-charge budget: 완전한 정식화 (그리고 스스로 잡아낸 오류 하나)

산출: `src/verify_shortfall_potential.py` -> `outputs/shortfall_potential_verification.json`,
`src/analyze_shortfall_budget.py` -> `outputs/shortfall_charge_words.json`.

## 1. \(\ell\)의 정확한 정의와 경계 — **증명됨**

`superperm_partial_f1_macro.py::rotation_runs`에서: \(\ell\)은 joint 하나가
발사된 직후, 다음 joint가 발사되기 전까지 연속으로 성공한 literal
`w=1` rotation의 개수다. 가능한 값은 \(\ell\in\{0,1,2,3,4,5\}\) — 6개
헥사곤 크기(\(N=6\))에서 joint 자신의 창을 빼면 최대 5번 더 돌 수
있다. **\(\ell\)은 joint의 종류(Z2/Z3/R/A2/A3/J)와 무관하다** — 어떤
joint 종류든, 그 앞의 rotation run 길이는 0부터(그 상태의) 충돌 지점까지
자유롭게 선택 가능하다(§2). "Z2의 \(\ell\)", "R의 \(\ell\)" 같은 고정값은
없다.

## 2. Charge 정의와 macro/literal 일관성 — **증명됨 + 실제 엔진 검증**

\[
c(t)=5-\ell(t),\qquad \Phi(S')=\Phi(S)-c(t)=\Phi(S)+(\ell-5).
\]

**주의(§요청 4의 정확한 답): 이 항등식은 joint-boundary 대 joint-boundary
에서만 성립하고, literal 단위에서는 성립하지 않는다 — 오히려
반대다.** 실제 엔진으로 rotation run 내부의 매 literal step마다 Φ를
재계산하면, rotation 한 번마다 Φ는 정확히 **+1씩 증가**한다(`n`은
고정, `visited`가 줄어드므로 deficit이 줄어 Φ가 는다). 그리고 joint가
발사되는 순간 Φ는 한 번에 \((\ell-5)\)만큼 떨어진다. 즉 Φ는 매
rotation마다 올라갔다가 매 joint에서 내려가는 **톱니 모양**이며, "결코
증가하지 않는다"는 단조성은 **joint-boundary 시퀀스에만** 적용된다.
실제 엔진에서 확인(`macro_literal_consistency_check`,
`literal_increase_by_exactly_1_mismatches: 0`): 예시로 \(\ell=5\)인 한
macro edge에서 Φ가 joint 직전 2→3→4→5→6→7로 다섯 번 오르고, joint에서
7→2로 떨어져(변화량 \(\ell-5=0\)) 정확히 원래 값으로 돌아온다.

| transition kind | \(\ell\) | 비고 |
|---|---|---|
| `Z2_blocked_w2_existing`,`R_blocked_w3_existing`,`Z3_blocked_w3_new` 등 모든 non-abandoning joint | 0–5, 자유 선택(충돌까지) | charge는 joint 종류가 아니라 \(\ell\)에만 의존 |

## 3. 완주 경계 조건 — **스스로 잡아낸 오류와 정정**

이번 분석 도중 처음에는 다음과 같이 (잘못) 결론 내렸다: "Φ가 결코
증가하지 않고 완주 시점에 정확히 \(\Phi=5\)(\(n=0,\text{deficit}=0\))로
끝나야 하므로, 모든 joint-boundary에서 \(\Phi\ge5\)여야 한다." 이 결론은
**틀렸고, 확인 즉시 폐기했다.**

**틀린 이유.** 완주가 반드시 "\(n=0\)이면서 동시에 \(\text{deficit}=0\)인
joint-boundary"에서 일어난다고 가정했다. 하지만 실제로는 **마지막
joint 이후 rotation-only suffix로 완주할 수 있다**(`run_macro_search`의
`rotation_only_success` 처리 참고). 마지막 joint-boundary 상태
\(S_k\)에서는 이미 \(n(S_k)=0\)(P가 이미 TARGET_P)이지만
\(\text{deficit}(S_k)\)는 0이 아닐 수 있고, 그 나머지를 최대 5번의
순수 rotation으로 닫으면 된다 — 즉 필요조건은
\(\text{deficit}(S_k)\le5\), 즉 \(\Phi(S_k)\ge0\)이다. **이것이 정확히
기존 엔진의 문턱값이다.**

> **정정된 결론(증명됨): \(\Phi\ge0\)은 (P, visited_count)만을 쓰는
> counting 논증에서 이미 얻을 수 있는 가장 타이트한 필요조건이다.**
> 이 문턱을 이 relaxation 안에서 더 강화할 방법은 없다 — 강화하려면
> 어떤 구체적 순열이 충돌하는지 아는, 순수 기하적 정보가 필요하다.

이 오류-발견-정정 과정을 그대로 기록하는 이유는, 만약 정정하지 않고
"229/230 J 상태가 이미 산술적으로 죽었다"는 (틀린) 주장을 냈다면 이번
전체 작업 노선을 그릇된 방향으로 이끌었을 것이기 때문이다.

## 4. Zero-charge run이 무한히 계속되지 않는 이유 — **증명됨 (새 군론
불필요)**

\(c=0\)(\(\ell=5\)) transition은 Φ를 소비하지 않지만, **모든** joint(
charge 0이든 아니든)는 `P`를 정확히 1 늘리고, `P`는 `TARGET_P`로
상한이 있다. 따라서:

> **남은 전체 joint 수는 charge와 완전히 무관하게 정확히
> \(n=TARGET_P-P\)로 고정돼 있다.** zero-charge run이 "무한히 이어지는"
> 일은 없다 — charge를 안 쓰든 쓰든, 매 joint가 이 유한한 예산 \(n\)을
> 1씩 깎는다.

이는 C3/C4류의 추가 군론 없이, `P`의 상한이라는 훨씬 더 기본적인 사실
하나로 완전히 해결된다. `n`은 나아가 정확히 \(n_{\text{new}}=TARGET_O-O\)개의
`Z3`(신규 orbit)와 \(n_{\text{existing}}=n-n_{\text{new}}\)개의
기존-orbit joint(최대 1개만 `R`, 나머지 `Z2`)로 강제 분해된다
(`J_COMPLETION_OBSTRUCTION.md` §3에서 이미 증명).

## 5. Budget ≤ Φ의 전체 charge-word family 열거 — **완전 계산**

임의의 budget \(B\)에 대해, 가능한 "charge multiset"은 \(0\)부터
\(B\)까지의 모든 정수를 5 이하의 양의 정수로 분할하는 것 전부다
(순서, 어떤 joint가 R/Z2/Z3인지는 아직 반영 안 한 순수 산술 단계).
230개 전체에서 관측된 budget 값과 그 family 수:

| \(\Phi\) | family 수 |
|---:|---:|
| 0 | 1 |
| 1 | 2 |
| 2 | 4 |
| 4 | 12 |
| 5 | 19 |

**어떤 budget도 무한하지 않다** — 전부 20개 이하의 유한 family로
끝난다. 이것이 "무한한 미래를 유한 family로 바꾼다"는 목표의 정확한
달성이다(`outputs/shortfall_charge_words.json`).
