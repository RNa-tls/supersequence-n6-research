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

A second, inequivalent word (not an image of the first under the order-12 symmetry group of the family):

| file | length | sha256 (prefix) | q | τ | λ | J |
|---|---|---|---|---|---|---|
| `superperm8_46184_b.txt` | 46184 | 3068bfd880f0 | 777 | 25 | 18 | 99 |

Trail order: `7 6 4 24 1 3 25 23 8 9 18 17 15 27 26 5 28 0 29 14 22 19 20 21 11 12 13 10 16 2`.

Two further inequivalent words (checker B's complete enumeration at THR = 22 found exactly **24** single-opening
trail orders with F = 22, forming **4 classes** under the 6 trail actions of the family group; words a and b
represent two classes, words c and d the other two; `rP/certs/optimal_orders_F22.json` lists all 24 orders):

| file | length | sha256 (prefix) | q | τ | λ | J |
|---|---|---|---|---|---|---|
| `superperm8_46184_c.txt` | 46184 | 2e2a254efc6f | 776 | 27 | 17 | 99 |
| `superperm8_46184_d.txt` | 46184 | ad3cd43b50ba | 776 | 27 | 17 | 99 |

Trail order c: `4 24 23 6 2 16 9 10 11 12 22 17 19 13 29 7 5 3 28 21 20 18 15 14 8 0 1 25 26 27`.
Trail order d: `4 24 23 6 2 16 12 9 10 11 22 17 19 13 29 7 5 3 28 21 20 18 15 14 8 0 1 25 26 27`.

Each of `_b`, `_c`, `_d` is verified with the same five commands as above (file name substituted); the outputs
are stored next to the word (`.minicheck.txt`, `.verifyA.json`, `.verifyB.json`, `.sha256`).
