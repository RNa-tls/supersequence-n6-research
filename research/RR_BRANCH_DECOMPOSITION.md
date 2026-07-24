# RR의 Chain branch / Separate branch 분리

산출: `outputs/rr_full_relation_table.json`, `outputs/rr_chain_cost_analysis.json`
재사용(새 계산 없음, 기존 4,470개 전체 분류를 재편성).

## 12. Corollary — same-component ⟹ chaining이므로

`RR_ANCESTRY_PROOF.md`가 확립한 사실(non-chaining ⟹ different-component,
corpus-exact 4,470/4,470 + 부분 손증명)을 이용해 RR 전체를 두
branch로 나눈다.

### Chain branch (chaining=True, 75/4,470 = 1.68%)

- same-component 가능(10/75, 나머지 65는 resolved-different).
- hex 0(word-origin hex)이 word 첫 joint에서 abandon되어 hub가 됨
  (10/10 same의 경우) 또는 hub가 아예 존재하지 않거나(대부분의
  chaining-different) 존재해도 R1과 무관.
- ancestry chain이 R1→R2로 고정된 구조(§`RR_ANCESTRY_PROOF.md` §7의
  8-패턴 중 1개가 same, 나머지 7개가 different에 해당).
- **completion obstruction 후보**: `RR_CHAINING_COMPLETION_COST.md`가
  보인 대로, 이 branch의 same 부분집합(10개)은 **Φ=0**(완주 여유
  없음, 절대 경계)에 몰려 있다 — 향후 라운드가 이 10개를 대상으로
  "ell=5만 계속 허용되는 좁은 회랑에서 실제 완주 가능한 경로가
  존재하는가"를 검증할 만하다. chaining-different(65개)는 오히려
  이 코퍼스에서 **가장 여유로운**(Φ 평균 4.91) 그룹이다 — obstruction
  후보로 우선순위가 낮다.

### Separate branch (chaining=False, 4,395/4,470 = 98.3%)

- 반드시 different-component(same은 절대 불가능, 손증명).
- component merge demand가 존재하지 않음(두 R이 서로 무관한 자원을
  씀) — 즉 두 R은 **서로 다른 두 개의 fresh-orbit 자원**을
  소비하며, "재사용 경쟁"이 없다.
- fresh-root demand 가능: 이 branch의 대다수(3,067+1,221=4,288/4,395,
  `RR_ANCESTRY_PROOF.md` §6 표의 "unresolved" 행)는 R2의 source
  orbit 자체가 **아직 등록조차 안 된 상태**(전형적인 "각자 독립적인
  fresh 자원을 쓰는" 패턴)이며, 나머지 107개(§`RR_CHAINING_PROOF_STATUS.md`,
  이전 라운드에서 이미 발견)만 "우연히 다른 이미-등록된 orbit과
  일치"하는 예외적 경우다.
- **completion obstruction 후보**: 이 branch는 κ_chain(Φ) 평균이
  3.68로 중간 정도이며, 분산이 크다(0~6) — 개별 상태별 편차가
  커서 단일 obstruction 후보를 특정하기 어렵다. **fresh-orbit
  자원을 두 배로 쓴다는 점**(비교: chain branch는 자원 하나를
  재사용해 아낀다) 자체가 orbit-budget(TARGET_O=25) 소진 속도에
  영향을 줄 수 있다는 것이 자연스러운 다음 가설이지만, 이번
  라운드는 검증하지 않았다 — **추측**으로 남긴다.

## 정직한 요약

| | Chain branch (75) | Separate branch (4,395) |
|---|---|---|
| component 관계 | same(10) 또는 different(65) | 반드시 different |
| 자원 재사용 | 있음(같은 orbit을 R1,R2가 나눠 씀) | 없음(독립 자원) |
| κ_chain(Φ) 평균 | same: 0, different: 4.91 | 3.68 |
| completion obstruction 우선순위 | same 10개가 유력 후보(Φ=0 경계) | 미결정, 개별 편차 큼 |

이 분리는 §11에서 발견한 Φ 상관관계를 구조적으로 재확인한다:
**chain branch 안에서도 same과 different는 completion 여유가
극단적으로 다르다**(0 대 4.91) — "chaining"이라는 이름 하나로
묶인 75개가 사실은 completion 관점에서 서로 매우 다른 두
하위집단이라는 것이 이번 라운드의 부가적 발견이다.
