# 공통 terminal normal form과 trailing-edge 정리 (라운드 20)

산출: `src/analyze_rr_ell0_family.py`, `src/enumerate_rr_decorated_local.py`.
새 completion search 없음(모든 실행은 root-local, frontier 자연소진).

## 9. 공통 terminal normal form theorem

> **정리 (root-local exhaustive; `ell=4` root, depth ceiling 8까지
> frontier 자연소진; `ell=0` root, depth ceiling 7까지 자연소진)**
>
> 지정된 root-local universe에서 same-component인 모든 post-R2
> boundary는 다음 terminal normal form을 갖는다. \(O_*\)를
> abandonment 직후 hub에 남는 **가장 가까운 잔여 위치의 orbit**
> (`HEX0_POSITION_ORBIT[ell+1]`; `ell=4`에서 \(O_*=1\), `ell=0`에서
> \(O_*=120\))이라 하자.
>
> 1. **R1이 \(O_*\)를 target한다.**
> 2. **hub 완성 사건이 \(O_*\)의 어떤 phase에 착지해 hub를 닫는다**
>    (`ell=4`: phase 4 = 위치 5; `ell=0`: phase 0 = 위치 1).
> 3. **hub 완성 사건은 준비 구간의 마지막 macro-edge**이다
>    (`hub_completer_macro_index == preparation_length`, 12/12).
> 4. **R2의 source는 \(O_*\)의 phase 4**이고 **target은 초기 orbit
>    0**이다(두 분기 공통).
> 5. **Φ = 0.**
> 6. 따라서 `R1_t = O_* = R2_s`이므로 **chaining이 강제된다**
>    (12/12, 반례 0).

**검증 범위**: `ell=4`의 9개 state(depth 4/6/8) + `ell=0`의 3개
state(depth 5/7) = **12개 전부**에서 위 6개 항목이 예외 없이
성립한다.

### 다섯 state에서만 exact인가, universe 전체에서 유도되는가

**둘 다 아니다 — 정확히는 "검사된 12개 전부에서 exact"이다.**
라운드19는 `ell=4`의 5개만 보고 "terminal signature 공유"를
서술했으나, depth 8에서 4개가 더 나타나 총 9개가 됐고 **그 4개도
같은 terminal form을 만족**한다. 그러나 이것이 universe 전체에서
**유도**된다는 증명은 없다 — 각 항목은 관측이다. 등급:
**root-local exhaustive**, 손증명 아님.

### 두 분기의 차이 (정리에 포함되지 않는 부분)

| | `ell=4` | `ell=0` |
|---|---|---|
| \(O_*\) | 1 | 120 |
| completer 착지 phase | 4 | 0 |
| completer → R2 macro 거리 | **1** | **2** |
| R2 target phase | 2 | 3 |
| boundary depth parity | **짝수**(4,6,8) | **홀수**(5,7) |

`ell=0`에서 거리가 2인 것은 completer(phase 0)와 R2 source(phase 4)가
**다른 phase**여서 중간에 Z2 하나가 더 필요하기 때문이다 — 라운드15가
"phase saturation"이라 부른 메커니즘이 여기서 정확히 이 한 칸의
차이로 나타난다.

## 10. Trailing edge 정리 — 정제된 형태

라운드19는 "정확히 3개"라고 했다. depth 8 확장 결과 **이는 정제가
필요하다**.

> **Lemma (손증명, 상한)**: terminal normal form 상태에서 legal
> trailing macro-edge는 **최대 3개**다.
>
> 1. R2 시점에 `F=1`이 이미 소진돼 있다(word당 abandonment 1회).
> 2. 따라서 이후 어떤 조인트도 abandonment일 수 없다 —
>    `area_a_prune_reason`이 `F_exceeded`로 제거한다.
> 3. `ell<5` macro-edge는 현재 hex를 다 훑지 않고 떠나므로 전부
>    abandonment가 되어 제거된다 ⟹ **`ell=5`만 남는다.**
> 4. 이 모델의 조인트는 정확히 4개다(`UNIQUE_WEIGHT2_MOVE_THEOREM.md`).
> 5. 그중 `w3:120`은 이 상태들에서 여전히 abandoning이라 제거된다.
> 6. **남는 것은 최대 3개**: `rot^5;w2:10`, `rot^5;w3:201`, `rot^5;w3:210`.

**정확히 3개인가?** 12개 중 **11개는 정확히 3개**이지만,
`cbfdf11e4a79`(depth 8, `ell=4`)는 **2개**다 — `rot^5;w3:210`이
추가로 사라진다. 이는 `F_exceeded`가 아니라 **방문 충돌(visited
collision)** 때문으로, 준비 구간이 길어져 더 많은 permutation이
이미 방문된 결과다.

> **정정된 명제**: trailing edge는 **항상 위 3개의 부분집합**이고
> (손증명, 상한), **보통 정확히 3개이지만 준비 구간이 길어지면
> 방문 충돌로 2개로 줄 수 있다**(exact counterexample:
> `cbfdf11e4a79`). 라운드19의 "정확히 3개"는 **반증됨**.

각 edge의 성질: 셋 다 `ell=5`(full sweep), `F` 변화 0,
`Φ` 변화 `ell−5 = 0`. `w2:10`은 Z2(기존 orbit), `w3:201`/`w3:210`은
Z3(새 orbit) — `outputs/rr_word_state_multiplicity.json` 참고.

## 11. Word-state multiplicity 일반식

\[
\#W_d=\sum_{S\in B_{d-1}} m(S)
\]

- \(W_d\): 총 macro-edge 수가 \(d\)인 word 집합
- \(B_{d-1}\): 마지막 edge를 떼어낸 boundary state 집합
- \(m(S)\): \(S\)에서 허용되는 마지막 macro-edge 수

**성립 조건 (§11이 요구한 항목)**:

1. **각 word가 유일한 predecessor boundary를 갖는다** — 마지막
   macro-edge를 떼는 연산이 word마다 well-defined하므로 자명.
   **손증명.**
2. **마지막 edge 제거가 surjective onto \(B_{d-1}\)** — 정의상
   \(B_{d-1}\)을 "길이 \(d\) word의 접두사로 실제 등장하는 boundary"로
   잡으면 성립. **손증명(정의에 의해).**
3. **injective가 아니다** — 서로 다른 word가 같은 boundary를 공유할
   수 있고, 바로 그 다중도가 \(m(S)\)다. **이것이 항등식의 내용
   전부다.**
4. **canonical word 계수와 state 계수를 구분해야 한다** —
   `RR_COUNTING_UNIT_STANDARD.md`의 4단위 규약을 따른다.
5. **decoration transport** — \(m(S)\)는 `ExactState`의 함수이므로
   decoration과 무관하지만, \(B_{d-1}\)을 decorated로 잡으면
   같은 `ExactState`가 여러 decorated boundary로 갈라질 수 있다.
   이 universe에서는 갈라지지 않는다(라운드19).

**Corollary (H9)**: 역사적 `ell=4` same-component word 집합에서
\(d=6\), \(|B_5|=3\), \(m(S)=3\) (세 상태 전부) 이므로
\(\#W_6 = 3+3+3 = 9\). **exact counting identity**(라운드19에서
확립, 여기서 일반식의 따름정리로 재배치).

## 12. `ell=4` depth 안정성 — 라운드19 주장 반증

라운드19는 depth 6과 7에서 `ell=4` same-component state가 둘 다
5개인 것을 보고 **"완전히 안정적"**이라고 서술했다. depth 8
coverage run(root-local, cap 없음, frontier 자연소진, 43,459 노드)
결과 **5개 → 9개**로 증가한다. **그 주장은 반증됨.**

### §12의 네 질문에 대한 답

1. **더 깊이서 새 state가 나타날 수 없는가** → **나타난다.**
   preparation length 7인 4개가 depth 8에서 새로 등장.
2. **단지 depth 7까지 미관측이었나** → **정확히 그렇다.** 원인은
   **parity**: `ell=4`의 same-component boundary는 abandonment
   root로부터 **짝수 depth**(4, 6, 8)에서만 발생하고, `ell=0`은
   **홀수 depth**(5, 7)에서만 발생한다. 그래서 ceiling을 6→7로
   올리면 `ell=4`에는 아무것도 추가되지 않고(홀수 depth 없음)
   `ell=0`에만 2개가 추가된 것이다. **라운드19가 본 "안정성"은
   parity 산물이었다.**
3. **preparation depth 상한이 있는가** → **확립되지 않았다.**
   관측된 길이는 3, 5, 7(전부 홀수)이며 상한을 시사하는 증거는 없다.
4. **fresh-opening block을 더 삽입할 수 없는 이유가 있는가** →
   **없다.** depth 8의 `d408ede44825`는 Z3를 5개 사용한다(O=7).

**등급**: root-local exhaustive (depth ceiling 8, frontier 자연소진,
node cap 미사용). depth 9 이상은 시도하지 않았다.
