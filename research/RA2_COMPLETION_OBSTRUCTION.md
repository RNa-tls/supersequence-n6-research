# RA2 U4: completion demand, macro compression, family-local re-search, generalization

산출: `outputs/ra2_reduction_benchmark.json` (via `src/search_ra2_reduced.py`).

## 5. Completion demand — U4 4개 상태의 정확한 요구량

24개 RA2 witness 전부에서 `f1_normal_form`/`ExactState` 프로퍼티로 직접
계산한, U4 4개 상태 각각이 완주까지 필요로 하는 정확한 양(전부
`outputs/ra2_24_comparison.json`의 `after_A2_final` 필드에서 이미
확보됨):

| 상태 | 남은 P (pass-start) | 남은 O(new orbit) | 남은 D | 남은 방문(720-visited) | fragment debt |
|---|---:|---:|---:|---:|---:|
| 17a42b24ccfb | 121-6=115 | 25-3=22 | 4-9=(음수, 이미 초과분 없음 — D는 orbit deficit 합, 목표보다 큰 것이 정상) | 720-30=690 | 1 |
| 1d8b48ab7d56 | 121-7=114 | 22 | — | 720-36=684 | 1 |
| 29f6af1e8aee | 114 | 22 | — | 684 | 1 |
| 86ec22eaaba4 | 115 | 22 | — | 690 | 1 |

(D의 부호에 대한 주의: `D = sum((N-1)-popcount) over touched orbits`이며
touched orbit이 적을 때 자연히 TARGET_D=4보다 크다 — 이는 정상이며,
`arithmetic_D_reachable`이 이미 별도로 검증하는 값이다. 이 표에서
"남은 D"로 표기한 것은 오해의 소지가 있어 위 표는 원 필드 값만
정직하게 옮긴다.)

**relaxation 조합**: Φ(=5 for all 4)는 이미 이 모든 개별 요구량을
하나의 산술 부등식(remaining P need vs remaining window budget)으로
합친 것이다. orbit reuse cost, fragment repair cost, phase cost,
endpoint compatibility cost를 개별적으로 추가 조합해 Φ보다 강한
`minimum required future cost > available future budget` 부등식을
시도했으나, §3/§4(FRAGMENT_DEBT_LEMMA.md, RA2_THETA_POTENTIAL.md)에서
이미 정직하게 기록했듯 **fragment/phase 관련 성분의 안전성 자체를
증명하지 못했으므로, 그것들을 Φ에 추가한 결합 부등식도 증명할 수
없다.** 이 절은 새 결과 없이 §3/§4의 결론을 그대로 상속한다.

## 6. Zero-charge run macro 압축 — 실험, 결정적 압축 발견 못함

두 decisive event 사이의 zero-charge run(Z2/Z3, abandonment=False,
new_orbit 무관)을 하나의 요약된 macro transition으로 안전하게 압축할
수 있으려면, "시작 boundary data가 같을 때 가능한 종료 boundary set이
완전히 동일"해야 한다. 이미 존재하는 `macro_edges()`가 정확히
"rotation-run + 단일 joint"라는 1단계 압축을 제공하지만(이 프로젝트의
표준 macro 단위), 이를 넘어 **여러 개의 zero-charge macro-edge를 하나로
더 압축**하는 것은 시도했으나 결론에 이르지 못했다: RA2 U4 4개 상태에서,
같은 (P,F,S,H,O,D,Ndef) 좌표를 가진 서로 다른 두 zero-charge-run
결과가 **다른 legal-move 집합**을 갖는 사례를 발견했다(orbit/hex
방문 마스크가 좌표만으로는 결정되지 않기 때문 — 이는 예상된 결과다,
좌표는 원래 손실이 있는 요약이다). 즉 **좌표만으로는 압축이 안전하지
않다.** 더 세밀한 요약(예: fragment/current hex mask까지 포함)을
시도할 시간이 이번 라운드에는 없었다 — **미완료**로 남긴다.

## 7. U4 family-local exact 재탐색 — 실행했으나, 결정에 따라 baseline과 동일

`src/search_ra2_reduced.py` 실행 결과(`outputs/ra2_reduction_benchmark.json`):

- §3, §4에서 **새로 검증된 안전한 prune이나 압축을 얻지 못했으므로**,
  이번 요청의 명시적 지침("새 obstruction 또는 압축 표현을 적용한
  뒤에만 U4를 다시 탐색하라", "상태 감소 효과가 30% 미만이면 cap을
  키우지 말고 이론 단계로 돌아가라")에 따라 **이번 탐색은 요청된
  초기 제한(state당 node cap 200,000, 전체 edge cap 2,000,000)만
  사용했고, 그 이상으로 cap을 확장하지 않았다.**
- 실행 결과: 전체 edge cap 2,000,000이 **첫 번째 상태(17a42b24ccfb)
  만으로 소진**됐다(96,691 node 확장 시점에 도달) — 4개 상태를 골고루
  탐색할 예산조차 부족했다. 이는 이 예산이 이전에 이미 시도한
  `depth<=18, edge_cap=1,500,000/state`(총 6,000,000/4개)보다
  훨씬 작기 때문이다 — 의도적으로, 새 prune 없이 cap만 키우는 것을
  피하기 위해 요청된 값 그대로 사용했다.
- **success_found: False** — 예상대로, 이 예산 안에서는 Φ 위반을
  찾지 못했다. **0% 개선**이며, 정직하게 그렇게 기록한다(억지로 더
  탐색하지 않음).

## 9. RA3/A3R/RR로의 일반화 조건

이번 라운드의 RA2 전용 결과(§1-7)가 다른 U-branch 계열로 옮겨지는지
분리해 판정한다. **9,000개 이상인 RA3/A3R corpus 전체에 대한 새
continuation search는 수행하지 않았다** — 아래는 이론적 판정만이다.

| 결과 | RA3 | A3R | RR |
|---|---|---|---|
| U4의 "R, A2 이벤트 자체가 리터럴로 동일" 패턴 (`RA2_FOUR_SURVIVORS.md`) | **부적용 불가 판정 불가** — RA3는 abandonment(A3)가 항상 마지막이므로 같은 분석 틀을 적용할 별도의 "미해결 subset" 자체가 아직 식별되지 않았다(RA3에는 이번 라운드 Φ capacity 재현을 하지 않음) | 상동 | 상동 |
| F=1 이후 blocked-only 하위 정리(`FRAGMENT_DEBT_LEMMA.md` §1) | **그대로 적용됨** — F<=1은 전체 슬랩의 공통 제약이므로 word와 무관하게 항상 성립한다. RA3/A3R 양쪽 다 A3 발동 이후에는 §1이 그대로 적용된다 | **그대로 적용됨**(A3가 첫 이벤트든 둘째든 이후에는 동일) | **그대로 적용됨**(부호 반전 없음, 추가 가정 없음 — Z2_abandon이 발동한 이후부터 적용) |
| 스칼라 fragment debt 반증(§2) | **그대로 적용됨** — 같은 동어반복 논증이 word에 무관하다 | 그대로 적용됨 | 그대로 적용됨 |
| d_frag=1 ⟺ 미해결이라는 24/24 관측(`FRAGMENT_DEBT_LEMMA.md` §3) | **적용 불가 판정 불가** — RA3에는 이번 라운드에서 별도의 "미해결 vs 해결" 분류 자체를 만들지 않았다(9,952개 전체 재탐색은 범위 밖) | 상동 | 상동(단, RR은 fragment_hex가 두 이벤트 모두에서 강제로 None이 아니므로 — `RA3_A3R_ASYMMETRY.md` — 애초에 "post-A2/A3 fragment debt"라는 개념 자체가 RR에는 그대로 옮겨지지 않는다. **추가 가정 필요**) |

**결론: F=1 이후 blocked-only 정리와 스칼라 debt의 실패 논증만 세
계열 전부로 안전하게 일반화된다(부호 반전 없이 그대로). 나머지 이번
라운드의 RA2 전용 실험적 관측들은 RA3/A3R/RR로 옮기기 전에 각 계열
자체의 별도 재현이 필요하며, 이번 범위에서는 그 재현을 수행하지
않았다.**
