# Round P record word (n = 8)

`superperm8_46184.txt` is an r = 0 superpermutation of `12345678` of length **46184**: every one of
the 40320 permutations occurs as a window of length 8.  It is a single-opening word of the 6A + 24φ
family (each of the 30 closed trails is opened once), with F = 22, J = 77 + F = 99.

| file | length | sha256 (prefix) | q | τ | λ | J |
|---|---|---|---|---|---|---|
| `superperm8_46184.txt` | 46184 | 4be0e96e64c6 | 780 | 24 | 16 | 99 |

Previous best: 46185 (`rL/records/superperm8_46185.txt`).

**How to verify** (each check is independent of the search code):

    python3 rI/src/minicheck.py rP/records/superperm8_46184.txt
    python3 rI/src/r0verifyA.py rP/records/superperm8_46184.txt
    python3 rI/src/r0verifyB.py rP/records/superperm8_46184.txt
    python3 rM/src/verify_r0_independent.py rP/records/superperm8_46184.txt
    sha256sum -c rP/records/superperm8_46184.sha256

`superperm8_46184.description.json` lists, in word order, each trail with its version, opening run and
number of runs; `rP/src/build_word.py` rebuilds the word from it (order + exact fixed-order DP options).

**Trail order** (30 closed trails, A trails = 1, 8, 15, 22, 28, 29):
`8 3 5 27 28 21 19 17 29 7 6 4 1 0 22 14 15 11 12 13 18 10 9 20 16 2 26 23 24 25`.
