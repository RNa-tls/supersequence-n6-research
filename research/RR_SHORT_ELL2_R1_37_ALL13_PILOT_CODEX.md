# Round 56 Codex: `short_ell2_r1_37` all-13 pilot

작성자: Codex  
실행일: 2026-08-08 (Asia/Seoul)  
판정: **제한 실험 / `ALL13_PILOT_PARTIAL`**

## 1. 실행 전 게이트

Round 55 계획 교정 산출물을 먼저 별도 원격 branch에 동기화했다.

- remote branch: `codex/round-r1-37-all13-pilot-plan`
- commit: `c394624f046930ec4257228cad4e13aaba70231f`
- parent: `fae8ded9a8fe5e2958e602fafb2ac4e337ef8958`
- `git ls-remote`: `c394624f046930ec4257228cad4e13aaba70231f refs/heads/codex/round-r1-37-all13-pilot-plan`
- 세 계획 파일은 remote tree에 존재하며 Git LFS 대상이 아니다.

원장과 plan JSON을 다시 읽어 다음 불변량을 확인했다.

- unresolved state가 정확히 13개이며 중복이 없다.
- 각 state의 독립 cap은 10,000 additional expansions이다.
- budget transfer는 금지되어 있다.
- 총 최대 budget은 130,000 expansions이다.
- `421,221 - 2 = 421,219`: 두 parent-null root를 뺀 모든 parent-DAG vertex가 정확히 하나의 incoming path에 대응한다.
- frontier incoming edge 22개는 이미 B0에 포함되며 누락 레코드는 없다.
- immutable source checkpoint SHA-256은 `2847a6bd5861476428ec7cd9bd9d1d855229b33378662ebeef4ae4db832b1551`이다.

## 2. 탐색 규격

각 state를 source checkpoint에서 정확히 복원한 뒤 별도 namespace
`outputs/checkpoints/rr_short5/r1_37_all13_v8/state_<id>/checkpoint.json`
에서 탐색했다. branch 간 budget은 공유하지 않았다. 자연소진이면 즉시 멈추고,
10,000 cap에서 frontier가 남으면 `INCOMPLETE`로 기록했다.

계측은 다음을 유지했다.

- exact Target-A-safe macro legality
- literal R2 joint source semantics (`edge.run.state`)
- component merge 및 bridge template
- B0--B6 maximum level ledger
- immediate/later R2 outcome
- literal Target A 및 helper-free Target B

Round-53/v7 checkpoint는 수정하지 않았다.

## 3. Branch별 결과

| state | expansions | frontier | max depth | natural exhaustion | R2 records | merge | Target A | checkpoint SHA-256 |
|---|---:|---:|---:|:---:|---:|---:|---:|---|
| `304973` | 6 | 0 | 81 | yes | 3 | 0 | 0 | `7dc5876d53e1c1515af4e3043e9736095e1619fd7ffee460f8bfa7dd36e38f74` |
| `304860` | 4 | 0 | 70 | yes | 0 | 0 | 0 | `5b509029327711bfb41727cc6b60dd595dd5188b2e2e9cbc1628bbbe144f193d` |
| `304858` | 1,480 | 0 | 94 | yes | 664 | 0 | 0 | `f4bed786ff6f00d6bbda77951b30d17b1d42f0750d2d2a576b4cb3b1274166bf` |
| `303323` | 4 | 0 | 62 | yes | 1 | 0 | 0 | `4f12744b8af99fe1a1ef4b279824050fb924c8c4b30f8a346536f84cb28c189c` |
| `236166` | 10,000 | 9 | 98 | no | 4,757 | 0 | 0 | `e75da6bdf90c794e83c3ab3c4618f0fbefdefd78e6e9b85bfe106f85e2507c89` |
| `304872` | 92 | 0 | 98 | yes | 45 | 0 | 0 | `6c3170f99504240f41153483e193c14b762bcd5bac20150a486eb6fdcd0a3e56` |
| `303324` | 4,503 | 0 | 101 | yes | 2,279 | 0 | 0 | `3d110f662e57dbce82ba90b970c18629fe0ca7b986dada03b1c229d12333571a` |
| `12` | 10,000 | 8 | 98 | no | 4,511 | 0 | 0 | `c3b2dbde91c6bc5c3ef5fd138d7f173dc5f74c454257d712a4607cf6d9dc9f92` |
| `6` | 10,000 | 20 | 99 | no | 4,968 | 0 | 0 | `4f0d45d9949071fb3c94263e3cf41855d3277e47b3e4cba571ce476ade75239f` |
| `3` | 10,000 | 21 | 99 | no | 4,786 | 0 | 0 | `4944c792b4cc7e20352cff2def1a3694697205beb1f6e68f6ab7263338e443f2` |
| `305018` | 7 | 0 | 92 | yes | 3 | 0 | 0 | `b3f48f75d4b378fee0c0b446b9a35aac5dcb4a61dbfc12abd074c690ff5091cd` |
| `303321` | 10,000 | 12 | 102 | no | 4,748 | 0 | 0 | `6df21ecb28630e1e078f972be12bb3162d3b0c9546a9f2056a0a330478e69ac5` |
| `13` | 10,000 | 14 | 98 | no | 4,700 | 0 | 0 | `86a459b38c0ebc28eb13bc290ea9e5cbb673656ceb4a2f1dff8c594c1bb2bc16` |

합계:

- expansions: **66,096**
- natural exhaustion: **7/13**
- capped with nonempty frontier: **6/13**
- final frontier: **84**
- exact R2 records: **31,465** (immediate 7, later 31,458)
- B0 accepted paths: **66,167**
- B1--B6: **0**
- component merge / bridge: **0 / 0**
- literal Target A / Target B: **0 / 0**

R2 failure는 immediate `recognizer_geometry_failure` 7건, later
`recognizer_geometry_failure` 28,758건, later `not_same_component` 2,700건이었다.

## 4. 독립 검증

`src/verify_rr_short_ell2_r1_37_all13_pilot.py`가 다음을 독립 재검증했다.

1. 13개 root state와 decoration의 exact replay
2. 모든 저장 child의 parent-edge replay와 path hash
3. 모든 **66,096 expanded node**에서 outgoing macro candidate 전수 재열거
4. 저장 child set과 exact accepted child set의 동일성
5. 31,465개 R2 record의 literal-source recognizer 재실행
6. component merge / B0--B6 / Target A / Target B count conservation
7. 자연소진 7개에서 empty frontier, cap 6개에서 nonempty frontier

검증 결과는 `verified=true`, `overall_status=ALL13_PILOT_PARTIAL`이다.

코드 및 결과 SHA-256:

- runner: `ee35b44920eaec3c57c29282f1e986d6bde758494924f09dc12e14ae887fe195`
- verifier: `78dafd1e4752df740cdc000787bc8fd6b5a2532b2a1f08665fe0c0582fe6ae68`
- results: `66eec734e60707268825b2641f9f51ff0622a36b9b1e70c048cad9be3ceb4b78`
- bridge ledger: `66e96078bf5ce09cda1f8914e4f4936f270348115dcde4c80b797ea2c1c11f16`
- verified ledger: `958b7346f700704ea8a83d024cd2ec64153ab53ec59a2275266d47de36c449e0`

## 5. 정확한 해석

자연소진한 7개 state의 subproblem은 exact closure다. 그러나 나머지 6개는
각각 10,000 cap에서 nonempty frontier를 보존한다. 따라서 all-13 subproblem이나
`short_ell2_r1_37` 전체가 닫혔다고 말할 수 없다.

또한 6개 capped branch에서 merge/bridge/Target A/Target B가 0회였다는 것은
현재 prefix의 관측일 뿐 불가능성 정리가 아니다.

**최종 상태: `ALL13_PILOT_PARTIAL`.**
