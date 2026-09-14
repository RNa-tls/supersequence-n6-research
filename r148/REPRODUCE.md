# `L6 = 872` — 재현 안내

브랜치 `claude/n6-supersequence-length-rn17wf`.  모든 경로는 **깨끗한 체크아웃**
에서 시작하며 작업 디렉터리의 커밋되지 않은 파일에 의존하지 않는다.

```
git clone <repo> l6 && cd l6
git checkout claude/n6-supersequence-length-rn17wf
```

## FAST — 커밋된 정확 용량 증명서를 신뢰

커밋된 셀 원장(사슬 825 + 무거운 276 = 1,101 셀, 전부 EXACT_UNCAPPED)을
**재계산하지 않고** 그 위의 모든 결론을 다시 검사한다.

```
bash r148/src/cleanroom148.sh
```

이 스크립트가 하는 일:

1. 상속된 실행파일을 전부 지우고 커밋된 소스에서 다시 빌드
   (`gcc -O2 -Wall -Wextra`; 빌드는 비트 재현 가능하다)
2. `r147/src/catalogue147.py` — 탐색기 기하를 문자열 대수로 재구성해 대조
3. `genheader147.py` 로 C 헤더를 다시 만들어 커밋된 것과 diff
4. `r147/src/failclosed147.py` — 표 로더가 16 가지 고장 입력을 전부 거부
5. `r147/src/monotone147.py` — 1,101 셀 표의 단조성과 해석적 상한
6. `r147/src/rows147.py` — 정의에서 좌표행 재생성, 라운드 144 열거와 집합 비교
7. `r148/src/synthetic_control148.py` — 공존 solver 세 개의 구성된 양성 대조
8. `r148/src/rows148.py` — 세 번째 독립 열거로 L=870, L=871 인구조사
9. `r148/src/witness148.py` — 등호 증인을 두 경로로 재열거(한 경로는 **가지치기
   표 없이**)하고 정본 집합 SHA-256 비교, 증인마다 공존 시험 세 개
10. `r148/src/verifier148.py` — fail-closed 마스터 검증기
11. `r148/src/dag148.py` — 최종 증명 DAG
12. `tests/test_l6_endgame_144.py` — 회귀 스위트

예상 실행 시간: **약 6–8 분** (4 코어).  대부분은 9 번의 표 없는 증인 열거
(9.0e8 + 1.5e8 노드) 가 차지한다.

## FULL — 모든 load-bearing 정확 용량을 소스에서 재생성

```
bash r148/src/cleanroom148.sh                      # 먼저 FAST 경로
rm -f r147/tables/chain_cells_147.json r147/tables/heavy_cells_147.json
python3 r147/src/recompute147.py outputs/rr_l6_chain_dependency_146.json
R147_OUT=heavy_cells_147.json R147_SEEDS=chain_cells_147.json \
  python3 r147/src/recompute147.py r147/tables/heavy_dependency_147.json
python3 r147/src/verify2_147.py                    # 2 차 구현 교차검증
python3 r148/src/strict148.py                      # 엄격 노드 수 교차검증
bash r148/src/cleanroom148.sh                      # 재생성된 원장으로 다시
```

예상 실행 시간 (4 코어, 3 워커):

| 단계 | 노드 | 시간 |
|---|---:|---:|
| 사슬 825 셀 | 6.60e10 | 약 2 시간 25 분 |
| 무거운 276 셀 | 약 1e10 | 약 40 분 |
| 2 차 구현 905 셀 | 약 4e11 | 약 6 시간 |
| 엄격 노드 수 교차검증 | 가변 | 셀당 240 초 예산 |

하드웨어 가정: x86-64, 4 코어 이상, 16 GB 메모리.  가지치기 표는 셀마다
메모리에 약 108 MB 를 잡는다 (`UB[6][41][25][25][25][7]`).

## 무엇이 어디에 있나

| 산출물 | 내용 |
|---|---|
| `r147/tables/chain_cells_147.json` | 사슬 용량 825 셀, 전부 EXACT_UNCAPPED |
| `r147/tables/heavy_cells_147.json` | 무거운 용량 276 셀, 전부 EXACT_UNCAPPED |
| `r147/certs/second_impl_147.json` | 2 차 구현이 905 개 load-bearing 셀에서 일치 |
| `r147/certs/monotonicity_147.json` | 단조성·해석적 상한 위반 0 |
| `r147/certs/failclosed_147.json` | 로더 fail-closed 16/16 |
| `r147/certs/catalogue_agreement_147.json` | 기하 재구성 열 개 필드 일치 |
| `r148/certs/regen_148.json` | 스크래치 전삭제 후 재생성, 용량 차이 0 |
| `r148/rows/census_148.json` | L=870, L=871 인구조사 |
| `r148/certs/witnesses_148.json` | 등호 증인 두 경로 열거와 공존 배제 |
| `r148/certs/synthetic_controls_148.json` | 공존 solver 양성 대조 |
| `r148/certs/mutation_148.json` | 변이 18/18 검출 |
| `r148/certs/dag_148.json` | 최종 증명 DAG |
| `r148/certs/master_verifier_148.json` | 마스터 검증기 결과 |
| `research/RR_L6_R147_SOUND_UB.md` | 건전한 가지치기 상한의 정의와 증명 |
| `research/ERRATA_146_CHAIN_UB.md` | 라운드 146 이 찾은 결함의 전말 |

## 쓰이지 **않는** 것

* 라운드 144/145 의 사슬 가지치기 상한 파일 (`outputs/rr_l6_chain_ub_144.txt`).
  새 로더는 이 파일을 매직 불일치로 거부하며, 그 거부가 fail-closed 시험 항목이다.
* 라운드 144/145 의 사슬·무거운 용량표.  라운드 146 에서 철회되었고
  `r147/INVALIDATED_BY_UB146.md` 에 목록이 있다.
* NR6 (n=6 특수 가정) — 어디에서도 가정하지 않는다.
