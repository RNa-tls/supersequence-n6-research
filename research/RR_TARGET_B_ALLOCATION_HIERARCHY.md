# Capacity bound 계층 최종본 (라운드 33 §22)

## 1. 네 단계

### (A) Coarse — 손증명
\[
B+1\le5(m+1),\qquad m\le O_{\mathrm{cap}}+R_{\mathrm{cap}}
\]
**가정**: \(\Phi=0\)(⟹ 모든 macro-edge가 \(\ell=5\)), 생성원 대수,
orbit의 port가 5개.

### (B) Phase-refined — safe capacity bound
\[
B+1\le c(q_0)+\sum_{\text{top }O_{\mathrm{cap}}}c(q)+5R_{\mathrm{cap}}
\]
\(c(q)=\) hexagon이 미방문인 \(q\)의 port 수. **추가 가정**: port는
그 hexagon이 비어 있어야 쓸 수 있다.

### (B+R) Orbit-reuse penalty — 손증명 (라운드32)
\[
B+1\le c(q_0)+\sum_{\text{top }O_{\mathrm{cap}}}c(q)+\mathbf{4}R_{\mathrm{cap}}
\]
orbit-변경 \(R\)로 진입한 segment는 **이미 열린** orbit에 있으므로
capacity \(\le4\).

### (C) Phase-walk initial refinement — 손증명 **(라운드33 신규)**

> \(c(q_0)+1\)은 **과대평가**다. initial segment는 legal **phase walk**
> 여야 한다 — 그 covered phase는 현재 phase에서 시작하는
> \(\{+1,+2\}\) 위 word의 부분합이다. 따라서 **가용하지만 walk로
> 도달할 수 없는 port는 세면 안 된다.**

\[
B+1\le \operatorname{cap}^{\mathrm{walk}}_{\mathrm{init}}
+\sum_{\text{top }O_{\mathrm{cap}}}c(q)+4R_{\mathrm{cap}}
\]

**실측**: 9개 CAPACITY_SURVIVOR 전부에서 port-가용 bound는 \(c_0=3\)
이지만 **실제 phase-walk capacity는 2**이고 최적 initial word는
`E`(길이 1)다. bound가 정확히 **1 강해진다**.

## 2. 계층별 제거 실적

| bound | 제거된 survivor |
|---|---:|
| (A) coarse | 9 (18 → 9) |
| (B) phase-refined | +1 (→ 8) |
| (B+R) orbit-reuse | +1 (→ **7**) |
| **(C) phase-walk initial** | **+0 among the 7** |

**중요 — (C)의 독립적 가치**: (C)는 라운드32가 (B)와 (B+R)로 제거한
**같은 두 상태를 완전히 다른 경로로 재확인**한다
(`ell0 P_core=4`: bound 111 < 113; `ell4 P_core=4`: 111 < 114).
즉 두 제거는 **두 개의 독립 증명**을 갖는다.

남은 7개에서는 margin이 5–7 → 4–6으로 줄었을 뿐 부호가 바뀌지 않는다.

## 3. 왜 더 강해지지 않는가

(C)의 이득은 initial segment 하나에만 적용된다(1단위). 남은 7개의
margin은 4 이상이므로 부족하다. 더 강한 bound가 나오려면
**fresh segment들의 capacity**를 깎아야 하는데, 그 orbit들은 거의 전부
port 5개를 온전히 갖고 있다(라운드32 §4).

**등급**: (A) **손증명**, (B) **safe capacity bound**,
(B+R) **손증명**, (C) **손증명**.

## Round 39 correction

The generic phase-walk capacity claim is retracted. The retained `18 -> 9
-> 8 -> 7` reduction uses only coarse capacity, the `c(q)` port-count bound,
and B+R. No phase-walk capacity table is used in the corrected proof; see
`RR_ROUND33_PHASE_CAPACITY_CORRECTION_CODEX.md`.
