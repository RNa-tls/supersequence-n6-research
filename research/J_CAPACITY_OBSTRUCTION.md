# J-branch capacity 장애물: Φ 단조 potential

산출: `src/analyze_j_capacity_failures.py` -> `outputs/j_capacity_45_seeds.json`,
독립 검증 `src/verify_j_capacity_cores.py` -> `outputs/j_capacity_core_certificates.json`.

## 1. Φ의 독립 재유도 — **증명됨**

기존 엔진의 `remaining_window_capacity_prune`을 그대로 인용하지 않고,
다음 스칼라를 처음부터 재정의했다.

\[
\Phi(S) = 5 + 6\underbrace{(TARGET_P - P(S))}_{n(S),\ \text{남은 pass-start 수}}
- \underbrace{(720 - \text{visited}(S))}_{\text{deficit}(S),\ \text{남은 미방문 순열 수}}
\]

**유도.** joint-boundary 상태 \(S\)에서, 이후 완주까지 정확히 \(n(S)\)개의
future joint가 남아 있다(각 joint는 `P`를 정확히 1씩 올리고
\(P\)는 정확히 `TARGET_P`에서 끝나야 하므로). 각 future joint는 자기
자신의 창(1개) + 그 다음 rotation run(0~5개)으로 최대 6개의 새 창을
만든다. 현재(가장 최근) pass는 이미 joint가 발생한 직후이므로 그 자신의
추가 rotation만 0~5개 남아 있다(자신의 joint 창은 이미 `visited`에
반영됨). 따라서 남은 전체 새 창의 최댓값은 정확히 \(5+6n(S)\)이고,
완주를 위해 필요한 새 창의 수는 정확히 \(\text{deficit}(S)\)이다.
\(\Phi(S)\ge0\)은 완주의 **필요조건**이다(collision을 전혀 고려하지 않은
가장 느슨한 상한이므로 sufficient는 아니다).

## 2. Φ 단조성 항등식 — **증명됨 + 실제 엔진에서 예외 없이 검증됨**

joint-boundary 상태 \(S\)에서 rotation run 길이 \(\ell\in\{0,\dots,5\}\)를
거쳐 다음 joint-boundary 상태 \(S'\)로 가면:

\[
n(S')=n(S)-1,\qquad \text{deficit}(S')=\text{deficit}(S)-(\ell+1)
\]
\[
\Rightarrow\quad \boxed{\Phi(S')=\Phi(S)+(\ell-5)}
\]

\(\ell\le5\)이므로 \(\Phi\)는 **모든 합법적 이행에서 결코 증가하지
않는다**. 이는 종이 위의 항등식일 뿐 아니라, 실제 엔진(`exact.extend`,
`macro.macro_edges`)으로 230개 J-witness 각각에서 depth 4, 상태당 최대
300 edge까지 전개해 **11,920건의 실제 transition 전부에서 예외 없이
확인**했다 (`phi_identity_verification.transitions_checked=11920,
monotonicity_formula_mismatches=0, prune_iff_phi_negative_mismatches=0`).
기존 엔진의 `remaining_window_capacity_prune(S)`는 정확히 `Φ(S)<0`과
동치임도 같은 실행에서 확인했다.

**함의.** \(\Phi(S)\)는 "이 지점부터 완주까지 허용되는 총
shortfall(=\(\sum(5-\ell_i)\), 모든 남은 joint에 대해)의 상한"이다. 한 번
쓰면 되돌릴 수 없다 — 어떤 미래 joint도 \(\Phi\)를 되돌리지 못한다.

## 3. 전체 F=1,H=0 slab 차원의 사실 — **증명됨 (J 특유의 사실이 아님)**

`Φ(초기 상태)=6`이다(`P=1,visited=1,n=120,deficit=719` ⇒ `5+720-719=6`).
즉 **F=1,H=0인 어떤 완전한 872-길이 근처 walk에서도, 121개 전체 joint에
걸쳐 누적 shortfall이 6을 넘으면 안 된다** — 이는 J-branch만의 사실이
아니라 전체 slab의 사실이다. J는 그저 이 이미 극도로 빠듯한 예산의
초반(6번째 macro-joint 부근)에서 발생할 뿐이다.

## 4. 230개 J-witness에서의 Φ 분포 — **완전 계산**

```
Φ 값:     0    1    2    4    5
개수:     3    2    8  216    1
```

**230개 전부가 \(\Phi\in\{0,\dots,5\}\)다** — 초기 예산 6 중 이미 거의
전부가 이 지점(depth 6 근처)까지 오는 동안 소진됐다는 뜻이다. 216개
(94%)가 정확히 4에 몰려 있다.

## 5. 45개 관측된 capacity failure의 완전한 기계적 설명 — **유한 완전
검증**

45개 seed 전부에서 "가장 얕은(depth 최소) Φ<0 도달 경로"를 실제로 찾아
`src/verify_j_capacity_cores.py`로 독립 재생·검증했다: **45/45 PASS**.
결과는 예외 없이 하나의 패턴이다.

| 실패 직전 Φ | 필요한 최소 ell (실패를 만드는) | 관측된 개수 |
|---:|---:|---:|
| 4 | 0 | 37 |
| 2 | 0,1,2 중 하나 | 6 |
| 1 | 0,1 중 하나 | 2 |

**45개 전부가, `Φ(S) + (ell-5) < 0`을 만드는 단 하나의 "짧은 rotation
run"(주로 `ell=0`, 즉 joint 직후 첫 rotation이 이미 방문된 창과
충돌)으로 완전히 설명된다.** 신비한 별도 메커니즘은 없다 — §2의 항등식
그 자체가 원인의 전부다.

## 6. Φ는 45와 나머지 185를 깔끔히 분리하지 못한다 — **정직한 음성 결과**

```
45개(관측된 실패)의 Φ 분포:    {1: 2, 2: 6, 4: 37}
185개(미관측)의 Φ 분포:        {0: 3, 2: 2, 4: 179, 5: 1}
phi_cleanly_separates_45_from_185: false
```

185개 중 3개는 **Φ=0**(45개의 최솟값 1보다도 작다!)인데도 이 bounded
실험(depth≤6, edge cap 3,000)에서는 capacity 실패가 **관측되지 않았다**.
이는 §2 항등식이 틀렸다는 뜻이 아니라, **Φ는 필요조건일 뿐 "이 얕은
raw 탐색이 어떤 branch를 우연히 만났는가"를 예측하지 않는다**는 뜻이다
— 실패는 실제로 `ell` 작은 rotation run(=충돌)을 만나야 촉발되는데,
그런 run을 만나는지는 그 seed의 구체적 permutation 충돌 기하에 달려
있고, 얕은 edge cap 안에서는 운이 좋으면 아직 안 만날 수 있다.

## 7. 확장: 더 깊이/넓게 보면 나머지도 대부분 같은 방식으로 실패한다 —
**제한 실험 (증명 아님)**

동일한 "최소 실패 경로 탐색"을 depth≤6, seed당 edge cap 20,000(사용자
지정 상한 200,000 이하)으로 **230개 전부**에 적용했다
(`outputs/j_capacity_extension_profile.json`):

```
found_within_bound: 156 / 230   (원래 45개 대비 111개 추가로 발견)
not_found_within_bound: 74 / 230
```

**156/230(68%)이 같은 Φ 메커니즘으로 capacity 실패에 도달함을 확인했다**
— 원래 관측된 45개는 얕은 edge cap(3,000)의 인공물이었을 뿐, 조금만 더
찾아보면 3배 이상 많은 seed에서 같은 현상이 나타난다. 나머지 74개는 이
bounded 조건 안에서는 실패 경로를 찾지 못했다 — **이것이 그 74개가
안전하다는 뜻은 아니다**, 단지 이 bound 안에서 못 찾았을 뿐이다.

> **정리로 승격하지 않은 이유.** 230개(또는 J-branch 전체) 모두가
> 결국 capacity 실패에 도달한다는 것은 강하게 뒷받침되는 **추측**이지
> 증명이 아니다 — 이를 증명하려면 "이 slab의 어떤 완전한 walk도 121개
> 전체 joint에서 6단위를 넘는 shortfall 없이는 불가능하다"(§3)는 사실과,
> "그런 무결점에 가까운 walk가 실제로 충돌 없이 존재하는지"를 결합해야
> 하는데, 후자는 순수 기하학적 질문이라 이 Φ 논증만으로는 답할 수 없다.
