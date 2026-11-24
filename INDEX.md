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

## 브랜치와 보관 태그

2026-11-24에 GitHub 브랜치를 정리했다. 기록은 하나도 지우지 않았다: 지운 브랜치의 끝 커밋은 모두 남은 브랜치의 역사에
들어 있고, 브랜치 이름과 끝 커밋의 대응은 `archive/<브랜치 이름>` 태그로 남겼다(`git checkout archive/<이름>`으로 그대로
볼 수 있고, `git branch <이름> archive/<이름>`으로 되살릴 수 있다). `main`은 이때 개발 브랜치의 끝으로 fast-forward했다
(역사 재작성 없음).

남은 브랜치:

| 브랜치 | 역할 |
|---|---|
| `main` | 기본 브랜치, 최종 상태 |
| `claude/n6-supersequence-length-rn17wf` | 개발 브랜치(Round T–Ω와 그 앞의 모든 claude 라운드를 포함) |
| `codex/round-r1-37-hex82-t4` | codex 라운드 40–61 계열의 끝(개발 브랜치에 없는 고유 커밋 30개) |
| `codex/round143-dirty-threshold` | codex 라운드 136–143 계열의 끝(고유 커밋 92개) |
| `codex/round171-joint-audit` | codex 라운드 171(고유 커밋 6개; 손대지 않음) |
| `ccr-beb17f74-5zemcj` | 작업 환경이 만든 세션 브랜치(초기 커밋) |

보관 태그(지운 브랜치 40개; 끝 커밋, 그 커밋을 품은 남은 브랜치):

| 태그 | 끝 커밋 | 마지막 날짜 | 포함하는 브랜치 |
|---|---|---|---|
| `archive/claude/final-attack` | `f3047baa26` | 2026-10-06 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/final-universal` | `c0ecce1311` | 2026-10-01 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/n6-master-status-index` | `2730c99432` | 2026-08-10 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/round-i-r0-score` | `7d65fd8a4b` | 2026-10-11 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/round-j-l8` | `e8de8ca3f7` | 2026-10-13 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/round-k-global` | `ccaee70192` | 2026-10-13 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/round-l-antibundle` | `9766a70c3c` | 2026-10-13 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/round-m-joint` | `ae35c720e5` | 2026-10-15 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/round-n-linking` | `750aa03737` | 2026-10-16 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/round174-universal-structure` | `2df2f6fcbd` | 2026-09-26 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/round175-row-run-lemma` | `f1d0781aaa` | 2026-09-26 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/round176-charge2-capacity` | `e426c0b453` | 2026-09-26 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/round177-separator-e2` | `b3ce04f69b` | 2026-09-26 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/round178-coarsening-bridge` | `eb0f649e61` | 2026-09-26 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/round179-audit-payload` | `968ea02429` | 2026-09-26 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/round180-large-charge` | `dc9e423928` | 2026-09-26 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/round181-global-packing` | `c38544c54f` | 2026-09-26 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/round182-nonfull-control` | `e44d2a96cf` | 2026-09-26 | `claude/n6-supersequence-length-rn17wf` |
| `archive/claude/structured-hypergraph` | `5038269ee7` | 2026-10-07 | `claude/n6-supersequence-length-rn17wf` |
| `archive/codex/round-r1-37-all13-pilot-plan` | `c394624f04` | 2026-08-08 | `codex/round-r1-37-hex82-t4` |
| `archive/codex/round-r1-37-all13-pilot-results` | `e280d325f5` | 2026-08-08 | `codex/round-r1-37-hex82-t4` |
| `archive/codex/round-r1-37-dangerous-entry-results` | `681113270a` | 2026-08-09 | `codex/round-r1-37-hex82-t4` |
| `archive/codex/round-r1-37-first-component-z3-stage-d` | `9342018cd3` | 2026-08-09 | `codex/round-r1-37-hex82-t4` |
| `archive/codex/round-r1-37-frontier-analysis` | `fae8ded9a8` | 2026-08-04 | `codex/round-r1-37-hex82-t4` |
| `archive/codex/round-r2-literal-source-correction` | `b09f1d55cc` | 2026-08-02 | `codex/round-r1-37-hex82-t4` |
| `archive/codex/round-v6-endpoint-v7-plan` | `4792891075` | 2026-08-03 | `codex/round-r1-37-hex82-t4` |
| `archive/codex/round136-g2-k3-delta1` | `7d7cedf454` | 2026-09-08 | `codex/round143-dirty-threshold` |
| `archive/codex/round137-mr-hard-core` | `ec8a5f1aaa` | 2026-09-08 | `codex/round143-dirty-threshold` |
| `archive/codex/round138-universal-privacy` | `703538c0c1` | 2026-09-09 | `codex/round143-dirty-threshold` |
| `archive/codex/round139-g2-k2-multidefect` | `ab16be1533` | 2026-09-09 | `codex/round143-dirty-threshold` |
| `archive/codex/round140-g3-general-splicing` | `92b62a9e3a` | 2026-09-09 | `codex/round143-dirty-threshold` |
| `archive/codex/round141-outer-slack-and-nr6` | `fb792c2bf2` | 2026-09-10 | `codex/round143-dirty-threshold` |
| `archive/codex/round142-dirty-first-occurrence` | `6f39f6cb4f` | 2026-09-11 | `codex/round143-dirty-threshold` |
| `archive/codex/round150-feas-audit` | `30f72ed007` | 2026-09-15 | `claude/n6-supersequence-length-rn17wf` |
| `archive/codex/round40-short5-r1-complete` | `abfcdca4b6` | 2026-07-31 | `codex/round-r1-37-hex82-t4` |
| `archive/codex/round43-short-ell0-taxonomy` | `24002fdd73` | 2026-08-01 | `codex/round-r1-37-hex82-t4` |
| `archive/codex/round51-short5-child-outcomes` | `dfc314fa0a` | 2026-08-03 | `codex/round-r1-37-hex82-t4` |
| `archive/round149-opus-hmodels-audit` | `195d11bdbf` | 2026-09-14 | `claude/n6-supersequence-length-rn17wf` |
| `archive/round152-capacity-certificates` | `64e851e104` | 2026-09-15 | `claude/n6-supersequence-length-rn17wf` |
| `archive/round153-equality-coexistence` | `0029fe2905` | 2026-09-20 | `claude/n6-supersequence-length-rn17wf` |

## 정리 기록

* 2026-11-24: 빈 파일 `=`(Round 140에서 셸 재지정 실수로 생김)과 `b1b.log`(Round 88의 "파일 없음" 오류 한 줄)를 지웠다.
  둘 다 연구 내용이 없고 git 역사에 남아 있다.
