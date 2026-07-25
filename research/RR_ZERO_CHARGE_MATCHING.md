# Zero-charge perfect matching (라운드 25)

산출: `src/find_rr_zero_charge_matching.py` ->
`outputs/rr_zero_charge_matchings.json`.

## 14. 다섯 pairing 규칙 검사

각 규칙이 zero-charge 사건을 **모든 블록이 짝수 크기**가 되도록
분할하는지 전수 검사했다(블록이 전부 짝수여야 그 규칙에 따른
perfect matching이 존재한다).

| 규칙 | \(O_*\) 착지 (95) | \(\ell+2\) (48) | far (44) |
|---|---|---|---|
| 같은 target orbit | 반증됨 (`FFEFR`) | 반증됨 (`FFFF`) | 반증됨 |
| 같은 target hexagon | 반증됨 (`EER`) | 반증됨 | 반증됨 |
| 같은 target phase | 반증됨 (`EER`) | 반증됨 | 반증됨 |
| **\(O_*\)를 target하는가** | **완전 분할 (95/95)** | 반증됨 (`ERFERF`) | 반증됨 |
| 같은 symbol (E vs F) | 반증됨 (`RFERR`) | 반증됨 | 반증됨 |

## 유일하게 살아남은 분할 — 새 결과

> **\(O_*\) 착지에서 zero-charge 사건을 "\(O_*\)를 target하는가"로
> 이분하면 두 블록이 **모두 짝수 크기**다 (95/95).**

즉 \(\#Z_{\to O_*}\)와 \(\#Z_{\to \text{other}}\)가 각각 짝수이며,
이는 \(\#Z\) 짝수성을 **두 개의 더 가는 짝수성으로 정련**한다.
이 분할은 \(\ell+2\)와 far 착지에서는 **성립하지 않는다**(반례
`ERFERF`) — 따라서 \(O_*\) 착지에 특유한 구조다.

## 정직한 판정

**§14의 목표(perfect matching으로 짝수성을 즉시 도출)는 미완료다.**
살아남은 것은 **분할이 짝수 블록을 준다**는 사실이지, 각 블록 안의
명시적 짝짓기 규칙이 아니다. 개수가 짝수라는 것만으로 matching을
주장하지 않는다(§18의 지시).

**등급**: 네 규칙은 **반증됨**(exact counterexample),
\(O_*\)-이분은 **root-local exhaustive**.

## 살아남은 분할의 구조적 원인 (라운드25 추가)

\(O_*\)-이분이 왜 짝수 블록을 주는지는
`RR_ORDERED_PHASE_PARITY.md`의 \(O_*\) phase walk가 설명한다:

- F는 절대 \(O_*\)를 target하지 않으므로 \(\#Z_{\to O_*} =
  \#E_{\to O_*}\) (손증명, 실측 0/95 예외).
- E는 \(O_*\) phase를 +1, R은 짝수만큼 전진시키고, 총 전진량은
  모든 \(\ell\)에서 4 (mod 5)이므로
  \(\#Z_{\to O_*}\equiv k \pmod 2\) (winding number \(k\)).
- phase injectivity와 "R 걸음 \(\le2\)"로 \(k=0\)이 강제된다.

즉 \(O_*\) 블록의 짝수성은 **matching이 아니라 phase 회전수**에서
온다 — §14가 찾던 짝짓기 규칙은 존재하지 않아도 된다. 다만 알파벳
전제가 아직 측정값이므로 전체는 **미완료**이고, 나머지 블록
\(\#Z_{\to\text{other}}\)의 짝수성에는 아직 대응하는 논증이 없다.
