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
