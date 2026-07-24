# ell_A2=4 post-A2 boundary geometry — controlled counterfactual 비교

산출: `src/search_ra2_ell4.py` -> `outputs/ra2_ell_counterfactuals.json`;
`src/analyze_ra2_ell4_geometry.py` -> `outputs/ra2_ell4_transition_table.json`.

## 2+4. Controlled ell-sweep — U4가 다른 이유는 Φ만이 아니다

방법론 수정: 코퍼스 24개를 그대로 비교하면 서로 다른 R 이벤트가
섞여 ell만의 순수 효과를 가린다(`A2_ROTATION_LENGTH_CLASSIFICATION.md`
§1.3 참고). 대신 **U4 witness 하나의 R-부터-A2-직전까지 prefix를
고정**하고, **그 지점에서 실제로 쓰인 A2 move(`w2:10`) 자체를 ell=0,1,2,4에서
반복 발동**했다(ell=3,5는 각각 illegal/구조적 불가능, §1). 4개 U4
상태 전부에서 **완전히 동일한 패턴**이 나왔다:

| ell | legal | Φ | orbit slack | new_orbit | capacity-failure 탐색(depth<=8, edge_cap 20,000) |
|---:|---|---:|---:|---|---|
| 0 | 예 | 1 | 21 | **True** | **찾음, depth 5** |
| 1 | 예 | 2 | 21 | **True** | **찾음, depth 5** |
| 2 | 예 | 3 | 21 | **True** | **찾음, depth 5** |
| 3 | illegal | — | — | — | — |
| 4(U4 실제값) | 예 | 5 | **22** | **False** | **못 찾음** |
| 5 | illegal(구조적) | — | — | — | — |

### 핵심 발견: U4는 Φ뿐 아니라 new_orbit(orbit 소비 여부)에서도 다르다

ell=0,1,2는 전부 **새 orbit을 연다**(new_orbit=True, orbit
slack 21). ell=4(U4)는 **기존 orbit을 재사용**한다(new_orbit=False,
orbit slack 22). 이는 같은 move(`w2:10`)라도 rotation을 몇 번
거쳤는지에 따라 **그 move가 도달하는 target permutation 자체가
바뀌고**, 그 target이 우연히 이미 방문된 orbit에 속하는지(ell=4) 아니면
새 orbit인지(ell=0,1,2)가 달라지기 때문이다 — orbit 구조(E-orbit)와
hexagon 구조가 서로 다른 두 분할이라는 사실의 직접 결과다
(`superperm_partial_f1.py`의 `ORBIT_PHASE` vs `HEX_POSITION`).

**질문에 대한 답**: "ell_A2=4 상태가 다른 ell 값과 구별되는 이유가
단순히 Φ=5이기 때문인지, 아니면 endpoint/phase/orbit geometry가
별도로 다른지" → **둘 다다.** Φ가 다르다는 것은 이미 알려진
사실(`RA2_ZERO_CHARGE_HISTORY.md`)이고, 이번에 **추가로** orbit
소비 여부(new_orbit)가 독립적으로 다르다는 것을 확인했다(**손증명 +
4개 상태 전부 재현, 유한 완전 검증**). endpoint 자체(canonical화 후
permutation 값)는 ell에 무관하게 항상 identity 근처로 재정규화되므로
구별에 쓸 수 없다(canonicalization 관례의 artifact).

### capacity-failure 탐색과의 상관 — 재확인, 새로운 원인 규명은 아님

ell=0,1,2(모두 새 orbit 소비, Φ 낮음)는 depth<=8 이내에 전부
capacity-failure를 찾았다. ell=4(기존 orbit 재사용, Φ=5)만 못 찾았다.
이것이 **orbit 재사용 자체가 원인**인지, 아니면 **Φ가 높아서 탐색이
더 깊이 가야 하기 때문**인지는 이 실험만으로 분리되지 않는다 — 둘
다 ell=4에서 동시에 일어나므로 상관관계이지 인과 분리는 아니다.
**정직하게 미완료로 남긴다.**

## 3. ell=4 전용 transition truth table

U4 4개 상태의 A2 직후(depth 1) 전체 legal continuation을 열거했다
(`outputs/ra2_ell4_transition_table.json`). 4개 상태 모두 **legal
child가 3~4개뿐**이고(`FRAGMENT_REPAIR_OBLIGATION.md`에서 이미 확인한
"depth 1에는 fragment repair edge가 없다"는 사실과 일치), 전부
`kind ∈ {Z2, Z3}`(blocked, N budget 안에서), `is_fragment_repair=False`다
(hole target이 아직 도달 불가). ell=4에서만 가능하거나 ell=4에서만
불가능한 transition 종류 자체는 이 depth-1 데이터만으로는 발견되지
않았다 — child 수 자체가 적어(3~4개) ell=4가 유난히 제한적인
분기라는 인상은 주지만, "ell=4에서만" 나타나는 transition TYPE은
없었다(제한 실험, 반증 아님).
