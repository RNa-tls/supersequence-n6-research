# n = 8 상태 (Round T–Ω, 최종)

이 문서는 n = 8 연구(디렉터리 `rT/` … `rZ/`, `rOmega/`)의 현재 상태만 적는다. n = 6 문서(`STATUS.md`, `ROUNDS.md`)와는
별개이다. 자세한 내용과 근거는 `rOmega/FINAL_REPORT.md`(종결 보고서, A–Q절)와 각 라운드 보고서에 있다.

## 구간

**46134 ≤ L(8) ≤ 46173** (미해결, 표지 L8_UNSOLVED_FINAL).

| 끝 | 값 | 근거 | 이 프로젝트의 확인 |
|---|---|---|---|
| 하한 | 46134 | Halfar: Theorem D(k = 8) + 탐색 방정식 3개 (Lean + native_decide); 커널만으로는 46133 | 세 방정식의 유지 사슬 수를 독립 구현으로 재현(Round V, 이후 4회) |
| 상한 | 46173 | Theo H.의 공개 단어 | 여섯 경로로 검증(Round T); 동치가 아닌 46173 단어 둘 추가(Round V) |

## 46135 경계

* 길이 46134의 칸 (R, p, F)는 처음 170개(Round V)였고, 증명된 제약으로 115(V) → 69(W) → 40(X) → 34(Z) → **27(Ω)**칸이
  되었다. 남은 칸의 목록과 최적 분해는 `rOmega/FINAL_REPORT.md` §F, 증명서 `rOmega/certs/frontier/`.
* 가장 단단한 칸 (769, 0, 0)은 "769행, 이음매가 모두 무게 3인 해밀턴 사슬"의 존재와 같다(Round Z, §H).

## 증거 표기 규칙 (저장소 전체)

* `*/certs/`의 파일은 증명서(정확 계산 또는 증명 보조)이다. 이름이 `HYPOTHETICAL_`로 시작하는 파일은 증명되지 않은 명제를 넣은
  강도 측정이며 어떤 칸도 지우지 않는다.
* 탐색·휴리스틱 출력(빔 탐색, 담금질, 대리 목적 포장)은 보고서에서 "관측" 또는 "실험적 증거"로만 쓴다.
* 외부 저장소(Halfar, Theo H., Hunter)의 코드는 읽기만 하고 실행하지 않았다. 외부 데이터는 `rT/external/`에 출처와 함께 있다.

## 라운드별 보고서

`rT/ROUND_T_REPORT.md`, `rU/ROUND_U_REPORT.md`, `rV/ROUND_V_REPORT.md`, `rW/ROUND_W_REPORT.md`, `rX/ROUND_X_REPORT.md`,
`rY/ROUND_Y_REPORT.md`, `rZ/ROUND_Z_REPORT.md`, `rOmega/FINAL_REPORT.md`. 앞 라운드 보고서는 고치지 않았다. 앞 라운드
결과의 정정은 최종 보고서에만 적었다(Round Z 계수 완화의 HiGHS 행 누락: 결론 불변).
