# Round S 증명서 색인

보고서는 `rR/ROUND_S_REPORT.md`이다. 아래 파일은 모두 이번 라운드(Round S)에 만든 것이다. 재현 명령은 보고서 부록 A에 있다.

## monge/ — Monge 부등식과 환원 정리 S1–S3

| 파일 | 내용 | 만든 프로그램 |
|---|---|---|
| `lean_axioms_Monge.txt` | `rR/lean/Monge.lean`의 컴파일 출력(Lean 4.22.0), 공리 목록, sorry 검사 | `lean` |
| `monge_natural_links.json` | 자연 결합 10,080개 전부에서 Monge 4점 부등식 전수(868,193,230,512 세 쌍, 초과 최대 0); 가설이 깨지는 곳은 감싸기 옆뿐 | `rR/csrc/monge_nat.c` |
| `ladder_lemma.json` | 사다리 보조정리 S1.4, m = 2, 4, 6 전수(최대 −5, −13, −21) | `rR/csrc/ladders.c` |
| `ladder_lemma_numpy.json` | 같은 것의 둘째 구현(m = 2, 4) | `rR/src/ladders_check.py` |
| `skip_weight_law.json` | 연속 완전 사슬 k ≤ 4개의 건너뛰기 무게 = 3 + k (60 판본), trail 사이 w3 결합의 위치, 섞인 건너뛰기 | `rR/src/skip_weights.py` |
| `skip_weight_law_check.json` | 건너뛰기 무게 법칙의 둘째 구현(가족 JSON에서 직접) | `rR/src/skip_weights_check.py` |
| `reduction_selftest_seed2026.json` | 환원 알고리즘 종단 시험: 감싸기 없는 경로, 심은 사다리, 건너뛰기형 회전, 열린 틈 | `rR/src/monge_reduce_test.py` |
| `one_wrap_classes_P33.json` | 감싸인 사슬이 하나인 P ≤ 33 경로의 부류별 환원 여부(부류당 500개) | `rR/src/p33_classes_test.py` |

## gap/ — 틈 닻 괄호와 단일 분할 재확인

| 파일 | 내용 | 만든 프로그램 |
|---|---|---|
| `single_split_recheck.json` | Round Q 이음매 탐색(THR 20) 재실행의 수치와 `gap_eval.c` STD = 1의 결과; 증인 192개가 Round Q와 집합으로 같음 | `rQ/csrc/ckT_search.c`, `rR/csrc/gap_eval.c` |
| `single_split_std_witnesses.jsonl` | 위 증인 192개 | `rR/csrc/gap_eval.c` (STD = 1) |
| `gap_anchor_thr20.json` | 틈 닻 괄호(k = 1) 정확 평가: 심사값 pa + cz ≤ 20인 배치 0개 (정리 S4) | `rR/csrc/gap_eval.c` |
| `gap_anchor_crosscheck_thr25_subset.json` | 느슨한 문턱의 생존 760개를 경로로 조립해 무게를 직접 잰 교차 확인(불일치 0) | `rR/src/gap_witness.py` |
| `hybrid_main_own_bracket_partial_thr20.json` | G1″ 부류의 부분 심사(THR 20 패턴 위에서만; 심사값 ≤ 20은 0개, 최솟값 21) | `rR/csrc/gap_eval.c` (GAP2 = 1) |

## brackets/ — 괄호 나무 c′ ≥ 3의 부분 결과

| 파일 | 내용 | 만든 프로그램 |
|---|---|---|
| `cheap_cycles.json` | 덮개 순환의 비용 목록: 비용 1은 960개(꼭짓점 5), 비용 2는 7,188개(꼭짓점 3, 4); 서로 다른 trail의 영 경로는 선택지 5개까지 | `rR/src/cheap_cycles.py` |
| `partial_path_bounds.json` | H 표에서 읽은 부분 경로 완화 하한 F[n_φ][n_A], F0 | `rR/csrc/pathlb.c` |
| `bracket_count_bound.json` | 순환 수별 셈 하한 LB(c′); c′ ≥ 9이면 G ≥ 21 | `rR/src/bracket_count_bound.py` |

## kappa45_rev/ — A 단일 방문 κ 탐색의 둘째 구현

| 파일 | 내용 | 만든 프로그램 |
|---|---|---|
| `rev_B3_slackadd0.json`, `rev_B3_slackadd1_planted.json`, `rev_B3_slackadd2_planted.json` | 심은 slack 시험(B = 3): 쌍 0 / 4,144 / 4,260개, `rR/certs/kappa45/`의 목록과 같음 | `rR/csrc/kappa_rev.c` |
| `rev_B4_x0_336.json`, `nodes_B4_x0_336.txt` | κ ≤ 4 표적 탐색, 진출 run 0..335: 지배 안 됨 0 | `rR/csrc/kappa_rev.c` |
| `rev_B5_*.json`, `SUMMARY.json` | κ = 5 표적 탐색과 전체 요약(있는 범위는 SUMMARY에 적혀 있다) | `rR/csrc/kappa_rev.c`, `rR/src/kappa_rev_summary.py` |

## 저장소에 넣지 않은 것

* Round P의 H 층(9.5 GB), Round Q의 HT 층(9.6 GB), THR 20 패턴 파일(20 MB, sha256 `247e3cddec3e5a45c85977e52eae9ad2819fecee31af46eb3117f38f72458095`): 부록 A의 명령으로 다시 만든다.
* A 판본 trail 1 v0의 유효 slack 표(451,584바이트, sha256 `b1d335c4840125def42c68cc5a3f0b6e351a549b4702e97b17a5f1d5db8bd4b4`): `rR/csrc/dominance_slack.c`로 다시 만든다.
