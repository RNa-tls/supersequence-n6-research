# Zero-charge 짝수성 — 동치는 손증명, 명제는 미완료 (라운드 24)

산출: `outputs/rr_zero_charge_parity.json`.

## 2. 동치 정리 (손증명)

completer까지의 사건은 charged(R, Rx)와 zero-charge(E, F)로 정확히
이분된다. 사건 수가 \(\vert P\vert+1\)이므로

\[
\vert P\vert+\#R_{\le C}\equiv1 \pmod 2
\quad\Longleftrightarrow\quad
\#\{\text{zero-charge}\}\equiv0 \pmod 2 .
\]

**순수 산술이며 손증명.**

## Symbol ↔ charge 대응

| symbol | 정의 | charge |
|---|---|---|
| `R` | weight-3, 비-abandoning, 기존 orbit, target \(=O_*\) | **charged** |
| `Rx` | 위와 같으나 target \(\ne O_*\) | **charged** |
| `E` | 유일 weight-2 move, 기존 orbit | zero-charge |
| `F` | weight-3, 새 orbit(Z3) | zero-charge |
| `C` | hub completer — 위 중 어느 것이든 될 수 있다 | 경우에 따라 다름 |

## 지위

- **동치**: 손증명 ✔
- **\(\#\text{zero}\) 짝수성 자체**: **미완료**
- **가법적 증명의 불가능성**: 손증명
  (`RR_PREPARATION_R_PARITY_THEOREM.md`)
