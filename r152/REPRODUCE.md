# 라운드 152 재현 안내

모든 명령은 저장소 최상위에서 실행한다.

## 0. 빌드

```
cc -O2 -o r152/src/checker152.exe  r152/src/checker152.c
cc -O2 -o r152/src/producer152.exe r152/src/producer152.c
```

실행 파일은 커밋하지 않는다 (`.gitignore`).  두 `.c` 파일과
`r152/src/checker152.py` 만이 검증 경로에 들어간다.

## 1. 빠른 경로 — 파일럿 (약 1 분)

L = 871 등호 행 두 개가 의존하는 셀과 그 사다리 24 개.

```
./r152/src/checker152.exe r152/certs/cap_cert_pilot_152.txt 200000000 | tail -1
python3 r152/src/checker152.py --cert r152/certs/cap_cert_pilot_152.txt \
        --report /tmp/v.json --node-cap 200000000
python3 r152/src/agree152.py --cert r152/certs/cap_cert_pilot_152.txt
python3 r152/src/mutate152.py --cert r152/certs/cap_cert_pilot_152.txt
```

기대값: 24/24 `EXACT_CERTIFIED`, 총 노드 247,274, 두 검사기 완전 일치,
돌연변이 11 종 전부 `CAUGHT`.

## 2. 전체 경로 — 1,101 셀

인증서 생산 (신뢰되지 않음, 재현할 필요는 없다):

```
./r152/src/producer152.exe r152/certs/claims_152.txt \
        r152/certs/cap_cert_all_152.txt 150000000
```

검증 (이것이 본체다):

```
./r152/src/checker152.exe r152/certs/cap_cert_all_152.txt 30000000000 \
        > r152/certs/verify_all_c152.json
```

인증된 값만 써서 행 인구조사를 다시 한다:

```
python3 r152/src/rows152.py --verify r152/certs/verify_all_152.json --layers 3 4
```

## 3. 청정 재현

```
bash r152/src/cleanroom152.sh r152/certs/cap_cert_pilot_152.txt 200000000
```

실행 파일을 전부 지우고 커밋된 소스에서 다시 빌드한 뒤 전 과정을
재실행한다.

## 4. 소요 시간

파이썬 검사기는 초당 약 3 만 노드, C 검사기는 초당 약 1,200 만 노드다.
파일럿은 어느 쪽으로도 순식간이지만, 1,101 셀 전체는 C 로만 현실적이다.
파이썬 검사기는 적재 셀 부분집합에 대한 독립 교차검증으로 쓴다.
