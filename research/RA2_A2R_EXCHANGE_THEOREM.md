# RA2 ↔ A2R defect-order exchange

산출: `src/analyze_defect_exchange.py` -> `outputs/ra2_a2r_exchange_table.json`;
`src/search_a2r_minimum_depth.py` -> `outputs/a2r_minimum_witnesses.json`
(corpus 재사용 — 24개 RA2 witness 전체 + 기존 A2R witness + 이번 라운드
bounded 재탐색으로 확보한 추가 A2R 사실들, 새 대규모 탐색 없음).

## 결론 먼저

**R과 A2의 순서를 교환하는 것은 인접(adjacent) 경우 전부에서
반증됐다 — 원인은 정확히 "R 자신의 pre-boundary hex가 이미 FULL로
강제된다"는, 이전 라운드에서 이미 증명된 F=0 full-sweep 정리의
직접 귀결이다.** 이는 새로운 정리라기보다, 기존에 증명된 정리의
**교환 문맥에서의 재확인 및 응용**이다.

## 2. Exchange 정의 — 4단계

1. **literal commutation**: 교환된 순서가 정확히 같은 리터럴
   endpoint permutation에 도달.
2. **canonical-state commutation**: 교환된 순서가 같은 canonical
   state(hash)에 도달.
3. **continuation-equivalence commutation**: 교환된 순서가 이후
   legal-continuation tree와 isomorphic한(depth-2 추상 서명이 일치하는)
   상태에 도달.
4. **defect-ledger-only commutation**: 자원 델타(P/F/S/H/O/D/N) 총합만
   일치.

## 1+3. Adjacent exchange truth table (R과 A2가 macro-adjacent인 경우)

24개 RA2 중 R과 A2가 **바로 인접**한(사이에 zero-charge joint가
없는) 경우는 10개다. 이 10개 전부에서, "A2의 실제 move를 R의
pre-boundary에서 그대로 발동한 뒤 R의 move를 잇는" 교환을
시도했다:

**10/10 전부 실패, 이유는 정확히 동일: "R 자신의 pre-boundary hex가
이미 FULL이므로, A2 자신의 rotation-run(ell_A2≥1)을 그 지점에서
재생하려는 순간 첫 rotation부터 collision이 발생한다."**

### 증명 (일반, 10개 사례에 국한되지 않음)

`RA2_ZERO_CHARGE_HISTORY.md` §1.2에서 이미 증명된 정리: F=0인 동안
모든 blocked(비-abandoning) joint는 자신이 발동하는 순간 current
hex가 FULL이어야 한다. R은 blocked joint이므로, **R이 발동하기
직전의 hex는 반드시 FULL이다.** FULL hex의 rotation-successor는
정의상 이미 방문됨 — 따라서 그 지점에서 **어떤 추가 rotation도
불가능**하다(`exact.extend`가 즉시 `None`을 반환). A2 자신의
`ell_A2`가 1 이상이면, "A2를 R의 자리에서 그 rotation 길이만큼
재생"하는 시도는 **첫 rotation에서부터 구조적으로 불가능**하다. □

**이 논증은 ell_A2=0인 경우(코퍼스에 1개 존재하나, 그 상태는
비인접 사례)는 배제하지 않는다** — 이론상 ell_A2=0이면서 R과
A2가 인접한 사례가 있다면 이 특정 장벽은 적용되지 않을 수
있으나, 그런 사례는 24개 코퍼스에 존재하지 않아 **미완료(검증
대상 없음)**로 남긴다.

## 5. Obstruction 분류 — 인접 사례는 정확히 "literal collision(full-hex)"

요청된 후보 중 인접 사례 10개 전부의 최소 obstruction은 **"literal
collision"**(구체적으로: target hex가 이미 FULL이라 rotation
자체가 불가능) 하나로 완전히 설명된다 — 다른 후보(target orbit
미개방, phase incompatibility, fragment/split role 변경, incidence
component dependency)는 이 인접 사례들에서 **원인이 아니다**(문제가
드러나기도 전에 rotation 자체가 막힌다).

## 4. 비인접(zero-charge word 포함) 사례 — 부분 탐색, 일반화 실패를 정직하게 기록

비인접 사례(R과 A2 사이에 zero-charge joint가 있는 경우, U4 포함
14개)에서 "A2를 마지막 zero-charge joint 자리로 옮기는" 국소
치환을 U4 witness 하나(`17a42b24ccfb`)로 시도했다 — **이번에는
성공했다**(4번의 rotation과 A2 move 발동이 모두 legal). 이는
인접 사례의 장벽(full-hex)이 **R 자신에게 고유한 것이지, zero-charge
word 안의 모든 joint에 보편적으로 적용되지 않는다**는 것을
보여준다: canonicalize 관례상 각 macro-edge 이후 상태가 "새로
시작하는" 신선한 hex(mask=1)로 재정규화되는 경우가 많아, 그
지점에서는 A2의 rotation을 재생하는 것 자체는 막히지 않는다.

**정직한 결론**: 인접 사례(§3)에서 발견한 깔끔한 일반 정리는 R
자신의 위치에 국한되며, zero-charge word 전체에 대한 "bubble
sort"로 일반화하려던 §4의 시도는 **1개 사례에서 반례를 만나
반증됐다** — 전체 word에 대한 완전한 bubble-sort 가능성/불가능성
분류는 이번 라운드에서 완료하지 못했다(**미완료**).

## 전역: R과 A2가 "첫 사건"으로 등장 가능한 최소 깊이의 비대칭

24개 코퍼스 전체에서 R이 등장하는 macro-index(r_idx) 분포:
`{0:1, 1:4, 2:9, 3:8, 4:2}` — **R은 walk의 첫 joint로 등장할 수
있다(r_idx=0, 실제 witness 1개 존재).** 반면 A2가 walk의 첫
counted 이벤트로 등장하려면 **최소 depth 5**(index 4)가 필요함이
이전 라운드에서 이미 확립됐고, 이번 라운드의 `global_a2_first`
재탐색(depth<=5, node_cap=50,000, exact)도 **정확히 depth 5**를
재확인했다. **이 비대칭(0 대 4)이 R-먼저 순서가 A2-먼저 순서보다
구조적으로 더 이른 시점에 시작 가능한 근본 이유다** — 다음
문서(`A2R_MINIMUM_DEPTH.md`)에서 이를 A2R 전체의 최소 depth와
연결한다.
