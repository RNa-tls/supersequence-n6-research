# Round L record words (n = 8)

All four words are r = 0 superpermutations of `12345678` (every one of the 40320 permutations
occurs as a window of length 8).

| file | length | sha256 (prefix) | q | τ | λ | E + (τ−1) + λ |
|---|---|---|---|---|---|---|
| `superperm8_46185.txt` | 46185 | 66782d744376 | 774 | 29 | 18 | 100 |
| `superperm8_46185_b.txt` | 46185 | 7382643c2c1f | 774 | 29 | 18 | 100 |
| `superperm8_46186.txt` | 46186 | 9c6688ca3946 | 772 | 30 | 20 | 101 |
| `superperm8_46186_b.txt` | 46186 | b9ed04bc25e1 | 774 | 29 | 19 | 101 |

Previous best: 46187 (`rI/records/superperm8_46187.txt`).

**How to verify** (each check is independent of the search code):

    python3 rI/src/minicheck.py rL/records/superperm8_46185.txt      # plain window check
    python3 rI/src/r0verifyA.py rL/records/superperm8_46185.txt      # route, r = 0, length identities
    python3 rI/src/r0verifyB.py rL/records/superperm8_46185.txt      # second implementation
    sha256sum -c rL/records/superperm8_46185.sha256

The stored outputs are `*.minicheck.txt`, `*.verifyA.json` and `*.verifyB.json`.

**Construction.**

* Run `rL/src/hybrid_beam.py`: a beam search over the order of the 30 closed trails (6 A-bundles and 24 φ-cycles) of a 46187/46188 chain set.
* Each closed trail is opened at any of its edges.
* φ-cycles may be traversed in either world.
* `rL/ROUND_L_REPORT.md` §13.4–13.5 describes the model and the length identity it uses.
