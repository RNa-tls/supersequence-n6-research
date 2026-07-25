# Local chaining predicate — 필요성/충분성 분리 (라운드 19)

산출: `src/verify_rr_l5_states.py` -> `outputs/rr_l5_state_ledger.json`
(§`section7_chaining_predicate_ablation`),
`outputs/rr_local_implication_lattice.json`. 새 completion search 없음.

## 6. same-component ⟹ chaining 재검증 (L5 범위)

| 단위 | depth ceiling | 전제 개수 | 위반 | 판정 |
|---|---:|---:|---:|---|
| event-level | 6 | 6 | **0** | 성립 |
| post-R2-state-level | 6 | 6 | **0** | 성립 |
| event-level | 7 | 8 | **0** | 성립 |
| post-R2-state-level | 7 | 8 | **0** | 성립 |

**증명 등급: root-local exhaustive.** 명시적으로 **전역 RR
정리가 아니며 손증명도 아니다** — `RR_L5_LOCAL_UNIVERSE.md` §9의
coverage statement 안에서만 성립한다.

## 7. Chaining predicate ablation (event level, depth 6, 2,234개 R2 경계)

| 판정 | predicate | tp | fp | fn |
|---|---|---:|---:|---:|
| **IFF** | `r1_target == r2_source` | 10 | 0 | 0 |
| 충분(필요X) | `same_component` | 6 | **0** | 23 |
| 충분(필요X) | `source_root == hub ∧ target_root == hub` | 6 | **0** | 23 |
| 충분(필요X) | `same_component ∧ r2_source_orbit == 1` | 5 | 0 | 26 |
| 둘 다 아님 | `r2_source_orbit == 1` | 6 | **31** | 23 |
| 둘 다 아님 | `source_root == hub` | 6 | **8** | 23 |
| 둘 다 아님 | `target_root == hub` | 6 | **85** | 23 |
| 배타적 | `r1_target == r2_target` | **0** | 449 | 10 |

(depth 7에서도 같은 순위 구조가 유지된다 — 7,724개 경계, `same_component`
tp=8/fp=0/fn=23.)

### 정직한 판정 — 비자명한 필요충분 predicate는 찾지 못했다

유일하게 IFF인 `r1_target == r2_source`는 **이 코드베이스에서
chaining의 정의 그 자체**다. 따라서 이는 발견이 아니라 항진명제이며,
**과제 §7이 요구한 "최소 boundary predicate"를 비자명한 형태로
찾는 데는 실패했다 — 미완료로 표시한다.**

### 그럼에도 확립된 세 가지 실질적 결과

1. **`same_component`는 chaining의 충분조건이지만 필요조건이 아니다**
   (fp=0, fn=23). 즉 §6의 함의는 이 ablation에서 독립적으로
   재확인되며, 역방향(`chaining ⟹ same-component`)은 **반증됨**
   (23개 chaining 경계가 same-component가 아니다).
2. **`same_component`와 `(source_root == hub ∧ target_root == hub)`는
   이 universe에서 정확히 동치**다 — 혼동행렬(tp/fp/fn)이 완전히
   일치한다(6/0/23, depth7에서 8/0/23). 이는 우연이 아니라 hub가
   유일한 다중터치 hexagon(Unique Hub Hexagon lemma)이라는 사실의
   국소적 반영으로 보이나, **일반 증명은 하지 않았다(미완료).**
3. **`r2_source_orbit == 1` 단독은 predicate로 반증됨**(fp=31).
   Hub Exit Source Lemma가 "hex0를 떠나는 joint의 source는 orbit 1"
   임을 보장하지만, 그 역(orbit 1을 source로 쓰면 chaining)은
   거짓이다 — orbit 1을 source로 쓰면서 R1의 target이 orbit 1이
   아닌 경계가 31개 있다.
4. **`r1_target == r2_target`(same_target)과 chaining은 완전히
   배타적**이다(tp=0, 449개 반례). 이는 라운드14의 코퍼스 관측을
   이 corpus-independent universe에서 **독립적으로 재확인**한
   것이다.

## 각 좌표의 필요성 (ablation 요약)

- `same_component`에서 `r2_source_orbit == 1` 조건을 **추가**하면
  tp가 6→5로 줄고 fn이 23→26으로 늘어난다 ⟹ 이 좌표는
  **충분성을 유지하지만 적용범위를 좁힐 뿐 개선이 아니다**.
- `source_root == hub`와 `target_root == hub`를 **각각 단독**으로
  쓰면 fp가 8, 85로 발생 ⟹ **두 조건의 결합(AND)이 필수**이며
  한쪽만으로는 충분조건이 되지 못한다. 이것이 §7이 요구한
  "좌표 제거 ablation 반례"의 구체적 사례다.

## 12. Implication lattice — 계수 단위 부착

`outputs/rr_local_implication_lattice.json`에 9개 implication을
`scope` / `count_unit` / `proof_status` / `counterexample` 네 필드와
함께 기록했다. 요약:

| implication | 단위 | scope | 판정 |
|---|---|---|---|
| same-component ⟹ chaining | event / state | root-local, depth 6·7 | root-local exhaustive |
| chaining ⟹ same-component | event | root-local, depth 6 | **반증됨**(23 반례) |
| r2_source_orbit==1 ⟹ chaining | event | root-local, depth 6 | **반증됨**(31 반례) |
| r1_target==r2_target ⟹ chaining | event | root-local, depth 6 | **반증됨**(449 반례) |
| same-component ⟺ 양쪽 root가 hub component | event | root-local, depth 6 | root-local exhaustive |
| same-component ⟹ ell∈{0,4} | state | root-local, depth 6·7 | root-local exhaustive |
| #words = Σ #trailing completions | word+state | 역사적 ell=4 집합 | **exact counting identity** |
