# Hub touch ledger 정식화와 hub touch count ≤ 2의 완전 손증명

산출: `src/analyze_rr_hub_touches.py` -> `outputs/rr_hub_touch_truth_table.json`
(`hub_ledger_analysis` 필드).

## 1. Hub touch ledger의 정확한 정의

각 hexagon `H`에 대해 touch sequence `τ(H) = (e_1, e_2, ...)`을
정의한다. 각 `e_i`는 다음 metadata를 갖는다: `event_type`
(Z2/Z2abandon/R/Z3/A2/A3/J/`initial_registration`), `source_hex`,
`target_hex`, `target_orbit`, `phase`, `abandonment` 여부, `delta_F`,
`full_sweep`(ell=5 여부), `endpoint_before/after`.

구현 번호와 무관한 정식화:

- **first touch**: `H`가 처음 어떤 joint(또는 `initial_state()`
  자신)의 target이 된 사건. `H`가 word-origin hex라면 first touch는
  `initial_state()`의 등록(사건이 아님, event_index=-1)이고, 다른
  hex라면 그 hex로 처음 "착지"한 joint다.
- **second touch**: `τ(H)`의 두 번째 원소(존재한다면).
- **hub**: `|τ(H)| ≥ 2`인 hexagon. (§2에서 `|τ(H)| ≤ 2`가 항상
  성립함을 증명하므로, 실질적으로 "hub"는 `|τ(H)| = 2`인 유일한
  hexagon을 가리킨다.)
- **hub creator**: first touch를 만든 사건(또는 초기 등록).
- **hub completer**: second touch를 만든 사건 — `H`의 마지막 남은
  자리를 채워 `H`를 그 순간 "current"로 만드는 사건.
- **hub re-entry**: hub completer가 `H`를 새로운 current로 만드는
  전이 자체(정의상 hub completer와 동일 사건).
- **hub source/target orientation**: hub completer 사건의
  `source`(그 사건이 발동하기 직전 위치, `H`가 아닌 다른 곳)와
  `target`(H 내부의 남은 위치) — orientation은 항상 "외부 →
  H내부"다(H를 "떠나는" 방향이 아니라 "채우는" 방향).

## 2. Hub touch count ≤ 2 — 완전 손증명 (일반적, depth 무관)

### 정리

> F≤1 예산의 임의의 word에서, 임의의 hexagon `H`가 joint의 target이
> 되는 횟수는 **최대 2회**다.

### 증명

1. `current_hex(S) := hexagon_id(S.p)`(코드 정의,
   `superperm_partial_f1.py:174-175`, 직접 확인). `H`가 처음 target이
   되는 순간(first touch), 그 사건의 target이 새로운 `S.p`가 되므로
   `current_hex(S) = H`가 된다 — **first touch 직후 H는 반드시
   current다.**
2. `H`가 current인 동안, 다음 조인트는 두 갈래뿐이다:
   - **(a) ell=5에서 발동(완전 스윕, non-abandoning)**: `H`는
     `FULL_HEX`가 되어 6/6 방문 완료. `extend()`의
     `state.visited(target)` 체크(코드 확인)에 의해, `H`의 어떤
     permutation도 다시는 joint의 target이 될 수 없다 — **H는
     영구히 닫힌다.**
   - **(b) ell<5에서 발동(abandon)**: `H`는 일부만 방문된 채
     "fragment"로 남고, `F`가 1 증가한다.
3. F≤1이므로, (b)는 word 전체에서 **최대 1번**만 일어날 수 있다.
4. (b)가 일어나 `H`가 fragment가 됐다고 하자. 이 시점 이후로는
   **추가 abandon이 절대 불가능**하다 — 코드 확인:
   `area_a_prune_reason`의 `state.F > TARGET_F` 체크(`TARGET_F=1`)가
   `F_exceeded`로 즉시 pruning한다.
5. `H`(fragment)의 남은 미방문 위치 하나를 target으로 삼는 조인트가
   발동한다고 하자(이것이 second touch, hub completer). 이 조인트의
   target은 `H` 내부이므로, 1번과 같은 논증에 의해 **그 즉시
   `current_hex = H`가 다시 된다.**
6. `H`가 다시 current가 됐지만, `F`는 이미 소진되어(4번) 추가
   abandon이 불가능하다. 그러므로 `H`를 떠나려면 반드시 **완전히
   스윕(ell=5)**해야 하며, 그 남은 위치들은 순수 rotation(orbit_masks
   갱신 없음, `extend()`가 weight≥2 joint에서만 orbit_masks를
   갱신함을 코드로 확인)으로만 방문된다 — **어떤 joint도 다시는
   H를 target으로 삼지 않는다.**
7. `H`가 완전히 스윕된 후, 2번의 (a)와 동일하게 **영구히 닫힌다.**

**QED.** □

### 전체 코퍼스 재확인 — 유한 완전 검증

```
python3 src/analyze_rr_hub_touches.py
unique-hub violations: 0 / 4470
hub-touch-count>2 violations: 0 / 4470
```

**이 정리는 라운드 12에서 "경험적으로만"(corpus-exact, 4,470/4,470,
증명 없음) 표시됐던 것을, 이번 라운드에서 `current_hex`의 코드
정의와 F≤1 예산만으로 완전히 연역적으로 승격시킨 것이다.**
depth와 무관하게 임의의 F≤1 word에 대해 일반적으로 성립한다 — 이는
`RR_HEX0_NECESSITY_THEOREM.md`의 "Lemma 4"가 명시했던 gap(§2 후보
1,2,4,5) 중 **1, 2, 4번을 완전히 해소**한다: hub는 3번째 touch될
수 없고(1,2번 해소), 이는 depth와 무관한 일반 법칙이다(5번 해소,
"depth≤6에서만 미관측"이 아니라 **일반적으로 불가능**함을
증명). 3번(추가 abandonment 강제 여부)은 그 자체로 답이 됐다 —
추가 abandonment는 **애초에 불가능**하므로 강제할 필요조차 없다.
