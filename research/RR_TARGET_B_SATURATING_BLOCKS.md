# Capacity-saturating block 분류 (라운드 31 Part C)

산출: `src/build_rr_refined_capacity_bound.py` ->
`outputs/rr_saturating_blocks.json`.

## 1. 보존 run의 전수 분류 (§13)

보존 generator는 둘뿐이다: `w2:10`\(=E\)(Z2), `w3:120`\(=E^2\)(**항상 R**).
run 안의 entry port는 \(p, pE^{s_1}, pE^{s_2},\dots\)이고 부분합이
mod 5로 서로 달라야 한다.

| run 길이 | legal word 수 |
|---:|---:|
| 1 | 2 |
| 2 | 4 |
| 3 | 5 |
| **4** | **3** |
| 5 | **0** |

## 2. 길이 4 saturating block — 정확히 세 개

| block | phase 열 | 다섯 phase 전부 | \(E^2\) 개수 = 필요한 R 슬롯 |
|---|---|:---:|---:|
| `EEEE` | 0,1,2,3,4 | 예 | **0** |
| `E2EEE2` | 0,2,3,4,1 | 예 | **2** |
| `E2E2E2E2` | 0,2,4,1,3 | 예 | **4** |

**세 block 모두 자기 orbit의 다섯 phase를 전부 사용**한다 — 그래서
capacity를 포화시킨다.

## 3. 결정적 따름 — \(R_{\mathrm{cap}}=1\)이면 block은 `EEEE`뿐

`w3:120`은 \(\ell=5\)에서 orbit을 보존하므로 절대 new_orbit이 될 수
없고, weight 3이므로 **항상 R**이다(라운드30 손증명). 따라서 block 안의
\(E^2\) 하나가 R 슬롯 하나를 먹는다.

모든 Target A 경계에서 \(R_{\mathrm{cap}}=1\)이므로:

> **`E2EEE2`(2 슬롯)와 `E2E2E2E2`(4 슬롯)는 사용 불가.**
> capacity를 포화시키는 block은 **`EEEE` 하나뿐**이다.

이는 §4 equality case를 **완전히 강제된 형태**로 만든다:
\(M=0\)인 continuation은 반드시

\[
\texttt{EEEE}\;\to\;\text{opening}\;\to\;\texttt{EEEE}\;\to\;\text{opening}\;\to\cdots
\]

이어야 한다. 다른 형태는 존재하지 않는다.

## 4. Block-transition graph (§14) — 만들지 않은 이유

현재 corpus에 \(M=0\) survivor가 **하나도 없으므로**(최소 \(M=1\)),
"완전 포화 block 열"을 요구하는 대상이 없다. \(M=1\)인 survivor는
비효율 1개를 허용하므로 block 열이 강제되지 않는다.

따라서 block-transition graph는 **이번 라운드에 구축하지 않았다** —
회피가 아니라 **적용 대상 부재**다. \(M=0\) survivor가 나타나면 §14와
§15(no outgoing block, forced short block, repeated target, incompatible
entry phase, component conflict, terminal suffix incompatibility)가
곧바로 적용 가능하다.

**등급**: run 분류와 세 block **exact symbolic reduction**,
"`EEEE`만 사용 가능" **손증명**, block graph **미완료 (적용 대상 없음)**.
