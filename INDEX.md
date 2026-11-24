# 저장소 색인

이 저장소에는 최소 초순열(superpermutation) 길이에 관한 세 갈래의 연구 기록이 함께 있다: **n = 6**, **일반 n**,
**n = 8**. 라운드마다 디렉터리 하나에 보고서·코드·증명서(`certs/`)가 있고, 보고서가 경로를 그대로 인용하므로 디렉터리는
옮기지 않았다. 이 문서는 무엇이 어디에 있는지만 적는다. 무엇이 증명되었는지는 각 갈래의 상태 문서가 정한다.

## 최상위 문서

| 파일 | 내용 |
|---|---|
| [README.md](README.md) | n = 6 코드베이스 안내와 n = 8 안내 |
| [STATUS.md](STATUS.md) | n = 6: 증명된 것, 인용한 것, 열린 것 (생산 문서) |
| [ROUNDS.md](ROUNDS.md) | n = 6: 라운드별 연대기 (생산 문서) |
| [research/SUPERPERMUTATION_N6_MASTER_STATUS.md](research/SUPERPERMUTATION_N6_MASTER_STATUS.md) | n = 6: 논리적 현황, 증거 등급, 철회 기록 |
| [rOmega/N8_STATUS.md](rOmega/N8_STATUS.md) | n = 8: 현재 상태 (46134 ≤ L(8) ≤ 46173) |
| [rOmega/FINAL_REPORT.md](rOmega/FINAL_REPORT.md) | n = 8: 종결 보고서 (Round Ω, A–Q절) |

## n = 6

| 디렉터리 | 내용 |
|---|---|
| `src/`, `tests/`, `data/`, `experiments/` | 검사기·하한 표·구성기·소규모 정확 해법과 시험 (README의 Quick start) |
| `research/` | n = 6 연구 문서 전체(현황, 감사, 반증 기록) |
| `legacy_research/` | 앞선 NR6 조건부 하한 연구의 원자료와 구현 (그 자체의 README가 상태를 적음) |
| `outputs/` | 탐색·감사 산출물 (예: `outputs/rr_port_path_hall_archive/SCHEMA.md`) |
| `r147` | 라운드 146에서 발견된 무효 가지치기 상한에 의존한 산출물의 목록 (`INVALIDATED_BY_UB146.md`; 역사적 증거로 보존) |
| `r148` | `L6 = 872` 재현 안내 (`REPRODUCE.md`) |
| `r149`, `r150`, `r152` | `H.models` 독립 감사, 실행 가능성 가지치기 감사, 용량 인증서 |
| `r153`–`r162`, `r169` | 라운드별 인증서 (`certs/`; 설명은 ROUNDS.md) |
| `r156`, `r163`–`r168`, `r170` | 추출 정리(156), 손증명 목록(163), Route B 인증서 재생(164), 최소 기계 증명 기저(165), EXTREE 기저 인증(166), 다리 고려 기저 재최적화(167), 190셀 기저의 점진 인증(168), 두 인자 사다리(170) |
| `r171`, `r172` | Round 171 대량 생산 체크포인트, Round 172 R1 실험 |

## 일반 n

| 디렉터리 | 내용 |
|---|---|
| `r173`–`r182` | 일반 n 공식 감사(173), 보편 구조(174), row-run 보조정리(175), charge-2 용량(176), 분리자 E2(177), coarsening bridge(178), 감사·payload(179), 큰 charge(180), 전역 packing(181), non-full 행(182) |
| `rF` | 일반 n 최종 라운드: 정리, 보존 법칙 (`FINAL_REPORT.md`) |
| `rG` | 완성(completion) 문제 집중 공격 (`COMPLETION_REPORT.md`) |
| `rH` | 구조화-하이퍼그래프 공격 (`STRUCTURED_REPORT.md`) |

## n = 8

라운드 I–R은 이 프로젝트의 옛 가족(6A + 24φ)에서, T–Ω는 공개 46173 선택과 하한 경계(46135)에서 일했다.

| 디렉터리 | 주 보고서 | 내용 |
|---|---|---|
| `rI` | `ROUND_I_PART2_REPORT.md` | {a,b}-시스템, 번들 packing, 당시 기록 46187 |
| `rJ` | `ROUND_J_REPORT.md` | 46187의 증명·반증 시도 |
| `rK` | `ROUND_K_REPORT.md` | 전역 소진 시도 |
| `rL` | `ROUND_L_REPORT.md` | 반-번들 전역 패킹 |
| `rM` | `ROUND_M_REPORT.md` | 단편화와 연결의 결합 최적화 |
| `rN` | `ROUND_N_REPORT.md` | J = 100 간극 (6A + 24φ 가족) |
| `rO` | `ROUND_O_REPORT.md` | 순서 정수성 공격 |
| `rP` | `ROUND_P_REPORT.md` | 6A + 24φ 단일 개방 가족의 정확 최적 |
| `rQ` | `ROUND_Q_REPORT.md` | 다중 개방: 46183 |
| `rR` | `ROUND_R_REPORT.md`, `ROUND_S_REPORT.md` | 영전하 정규화와 46182 장벽 (R), 괄호 나무 환원 S1 (S) |
| `rT` | `ROUND_T_REPORT.md` | 공개 46173 단어의 수입·검증, 고정 선택의 단일 개방 최적 |
| `rU` | `ROUND_U_REPORT.md` | 두 조각·감싸기 하나 |
| `rV` | `ROUND_V_REPORT.md` | 감싸기 둘, 선택 탐색, 46134 탐색의 독립 재현 |
| `rW` | `ROUND_W_REPORT.md` | 글자 수준 감싸기 둘, 46135 경계 115 → 69칸 |
| `rX` | `ROUND_X_REPORT.md` | 두 방향·예외 사슬·묶음 보조정리, 69 → 40칸 |
| `rY` | `ROUND_Y_REPORT.md` | 전역 밀도 진단, 기호 일관성 |
| `rZ` | `ROUND_Z_REPORT.md` | 긴 사슬의 공존, 40 → 34칸, 769행 장벽 |
| `rOmega` | `FINAL_REPORT.md` | 두 문턱 공존표, 34 → 27칸, 종결 보고서 |

## 증거 표기

* `*/certs/`의 파일은 증명서(정확 계산 또는 증명 보조)이다. 이름이 `HYPOTHETICAL_`로 시작하는 파일은 증명되지 않은
  명제를 넣은 강도 측정이다.
* 외부 저장소의 코드는 읽기만 하고 실행하지 않았다. 외부 자료는 `rT/external/`에 출처와 함께 있다.

## 정리 기록

* 2026-11-24: 빈 파일 `=`(Round 140에서 셸 재지정 실수로 생김)과 `b1b.log`(Round 88의 "파일 없음" 오류 한 줄)를 지웠다.
  둘 다 연구 내용이 없고 git 역사에 남아 있다.
