# Insertion / deletion 판정 — 목표 정리 반증 (라운드 21)

산출: `outputs/rr_preparation_words.json`, `outputs/rr_insertion_blocks.json`.
completion search 없음.

## 6-7. 목표 정리와 그 반증

> **검사한 정리(§7)**: 모든 non-minimal same-component RR preparation
> history는 제거 가능한 2-edge block을 포함한다 — 즉 어떤 연속 2개
> edge를 지우면 더 짧은 valid history가 된다.

**판정: 반증됨(symbolic 수준에서 이미 실패).**

관측된 `before_C` 단어 \(P\)를 길이별로:

- \|P\|=2: `EE`, `RhE`, `ERh`
- \|P\|=4: `FEFE`, `FFEF`
- \|P\|=6: `EEFEEE`, `FFFEFF`, `FEEERhE`, `EFEEERh`

### 반례 1 — `FEFE`에서 어떤 2-block을 지워도 valid 길이-2 단어가 안 된다

`FEFE`의 연속 2-block 제거 결과: 위치(0,1)→`FE`, (1,2)→`FE`,
(2,3)→`FE`. 세 경우 모두 **`FE`**인데, 길이-2 집합은
`{EE, RhE, ERh}`이고 **`FE`는 그 안에 없다**.

### 반례 2 — `EEFEEE`도 마찬가지

제거 결과는 `FEEE`, `EEEE`, `EFEE`, `EEFE` 등인데 길이-4 집합은
`{FEFE, FFEF}`뿐이라 **어느 것도 일치하지 않는다**.

### 역방향(삽입)도 실패

`EE`에 임의의 연속 2-block \(B\)를 삽입해 얻을 수 있는 길이-4
단어는 `B EE`, `E B E`, `EE B` 꼴이다. `FEFE`를 얻으려면 `F`와 `F`가
위치 0과 2에 각각 있어야 하는데 이는 **연속 블록 하나의 삽입으로
불가능**하다(두 개의 분리된 삽입이 필요).

## 결론

> **preparation history는 "짧은 base + 반복 삽입 block" 구조가
> 아니다.** 길이 2, 4, 6의 \(P\) 집합은 서로 삽입/삭제로 연결되지
> 않는, **길이마다 독립적으로 나타나는 단어 집합**이다.

이는 §8이 요구한 "irreducible base normal forms + insertion blocks"
분해가 **이 데이터에서는 성립하지 않음**을 뜻한다. 따라서:

- **모든 관측된 \(P\)가 irreducible**이다(어느 것도 더 짧은 valid
  \(P\)로 환원되지 않는다).
- base normal form 개수 = 관측된 \(P\) 개수 자체이며, 길이가 늘수록
  계속 증가한다(2개→... 실제로는 길이 2에서 3개, 4에서 2개, 6에서
  4개).

**성공 기준 2(insertion/deletion lemma), 3(finite base + insertion
grammar) 평가: 둘 다 미달성 — 정리가 참이 아니기 때문이다.**
목표 형태를 데이터에 맞추려 강제하지 않고 반증으로 보고한다.

## 그럼에도 확립된 구조

삽입 문법은 없지만, **모든 \(P\)에 공통인 두 제약**은 확인됐다:

1. \(|P|\)는 짝수(2, 4, 6) — root-local exhaustive, 손증명 미완료
2. \(P\)의 알파벳은 \(\{E, F, Rh\}\)뿐이며 `Xh`와 `C`는 절대
   \(P\) 안에 나타나지 않는다 — `Xh`는 정의상 hub 내부에서만
   발동하는데 \(P\) 구간에서 hub는 아직 닫히지 않았고 walk는 hub
   밖에 있으므로. **손증명.**
3. \(P\)에 포함된 `Rh`는 최대 1개(=R1)이며, 0개이면 \(C\)가 R1이다.
   **RR word의 정의(R 사건 정확히 2개)에서 직접 따름 — 손증명.**
