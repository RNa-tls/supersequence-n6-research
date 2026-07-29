# NR6 주정리 영향 평가 (라운드 28 §16)

## 0. 먼저 명확히 — 무엇이 반증되지 **않았는가**

> **이번 반증은 \(L_6\ge872\)를 거짓으로 만들지 않는다.**
> Target A witness의 존재는 **same-component \(R_2\) 경계**의 존재일
> 뿐이며, NR6 completion(720개 permutation 전부를 덮는 walk)의 존재와는
> **아무 논리적 연결이 없다.** 이 문장을 그렇게 읽으면 안 된다.

반증된 것은 전부 **RR branch 내부의 보조 명제**이며, 그 대부분은
**최근 4개 라운드에서 이 세션이 스스로 제안한 것들**이다.

## 1. 무너진 보조정리

| 보조정리 | 도입 | 상태 |
|---|---|---|
| \(O_*\)-걸음 알파벳 \(\{E{:}{+}1, R{:}\text{짝수}\}\) | 라운드25 | **반증됨** (라운드26) |
| \(O_*\) revisit gap \(\le6\) | 라운드26 목표 | **반증됨** (라운드26) |
| 환원 \(\#Z_{\to O_*}\equiv k\) | 라운드25 | **반증됨** (라운드28) |
| \(\#Z_{\to O_*}\) 짝수 (Conjecture B) | 라운드24~25 | **반증됨** (라운드27~28) |
| \(P_{\mathrm{core}}+\#R_{\le C}\equiv1\) (Conjecture A) | 라운드24 | **반증됨** (라운드27~28) |
| \(\ell=4\) preparation length 홀수 고정 | 라운드20~21 관측 | **반증됨** |
| non-\(O_*\) zero-charge 총계 짝수 | 라운드25 관측 | **반증됨** (witness 2–5에서 7) |

**공통점**: 전부 **parity 계열**이며, 전부 **depth \(\le6\) 관측에서
귀납된 것**이다. 그 관측들은 각자 scope 안에서 여전히 정확하다.

## 2. 영향받지 않는 보조정리

| 보조정리 | 등급 | 왜 무사한가 |
|---|---|---|
| Unique Weight-2 Move Theorem (조인트 4개) | 손증명 | parity와 무관 |
| \(\ell=5\) 합성 생성원 \(g_j=\Sigma^5\circ a_j\) 네 값 | exact group computation | 순수 군 계산 |
| `w2:10`\(\to E\), `w3:120`\(\to E^2\) | exact group computation | 〃 |
| \(F_{\mathrm{sym}}\)은 `w3:201`/`w3:210`만 | 손증명 | orbit 보존 논증 |
| \(O_*\) port에서 `w2:10`은 phase +1 | 손증명 | 군 항등식 |
| F는 \(O_*\)를 target하지 않는다 | 손증명 | orbit이 이미 열림 |
| 총 전진 4 (mod 5), phase injectivity | 손증명 | 조합/방문기록 |
| **정정된 항등식 \(\#Z\equiv k+\#R_{\text{odd-}\delta}\)** | **손증명 (신규)** | 알파벳 전제를 쓰지 않음 |
| Unique Hub Hexagon (R12), Hub Touch \(\le2\) (R13) | 손증명 | parity와 무관 |
| Hub Exit Source Lemma (R15) | 손증명 | 〃 |
| Lemma P1 (tail 길이), Lemma P2 (\(\Phi=0\)) | 손증명 | 여섯 witness에서도 성립 |
| **same-component ⟹ chaining** | 미완료(정리로는) | **반증되지 않음 — 확인 사례 6개 추가** |
| terminal normal form 관측 | root-local exhaustive + witness exact | **오히려 강화됨** |

## 3. RR branch closure 상태

| 목표 | 상태 |
|---|---|
| RR branch를 parity 논증으로 닫기 | **닫히지 않음. 이 경로는 폐쇄됨** |
| same-component \(\Rightarrow\) chaining | **여전히 유효한 열린 목표** (반례 0, 확인 사례 15개) |
| terminal normal form 유일성 | **가장 강해진 후보** — preparation 길이 2~10 전 범위 예외 0 |
| Target A 도달 가능성 | **exact witness 6개** |
| Target B | **미완료**, 정의와 안전 prune만 준비됨 |

> **RR branch는 이번 라운드로 "닫힘"에서 멀어졌다.** parity 경로가
> 사라졌고, 대신 chaining과 terminal normal form이 유일하게 살아남은
> 구조적 경로다.

## 4. U/J branch 상태

**변동 없음.** 이번 라운드의 어떤 작업도 U-branch나 J-branch를 건드리지
않았다. `research/N2_CLOSURE_STRATEGY.md`의 상태가 그대로이며,
"F=1,H=0,N=2 slab의 J-branch가 완전한 walk로 확장되는가"는 여전히
**미완료**다. N=0 search/checkpoint도 건드리지 않았다.

## 5. 최종 하한에 미치는 실제 영향

| 항목 | 영향 |
|---|---|
| \(L_6\ge872\) 조건부 하한 | **영향 없음** — 이 저장소는 애초에 그것을 증명한 적이 없다 |
| \(L_6\ge867\) (문헌) | **영향 없음** |
| 이 저장소의 RR parity 프로그램 | **폐쇄** |
| NR6 가정의 지위 | **영향 없음** — 별개 문제 |

정직하게 말하면: **이번 반증이 제거한 것은 이 세션이 라운드24~26에
스스로 세운 증명 전략 하나이며, 문헌의 하한이나 이 저장소의 다른
결과에는 영향이 없다.** 그 전략이 거짓 전제 위에 있었다는 것을
4개 라운드 만에 exact counterexample로 확정한 것이 이번 성과다.

## 6. 다음에 실제로 유망한 것

우선순위 순:

1. **terminal normal form 유일성의 손증명** — 15개 사례에서 예외 0이고,
   preparation 길이에 무관함이 확인됐다. 가장 승격 가능성이 높다.
2. **same-component ⟹ chaining** — 반례가 없고 사례가 늘었다. 다만
   길이에 의존하는 논증은 이제 witness 2–5(\(P_{\mathrm{core}}=10\))로
   반증될 위험이 있으므로 그 family를 반드시 포함해야 한다.
3. **\(\Phi=0\) slab에서 남은 비용의 하한** — Target B를 안전하게
   판정하려면 필요하고, 계산 가능해 보인다.

**하지 말아야 할 것**: 반증된 parity 명제를 조건을 덧붙여 되살리는 것.
`RR_PARITY_CONJECTURE_REFUTATION.md` §5가 그런 시도 두 개를 이미
"자명한 재서술"로 분류해 버렸다.
