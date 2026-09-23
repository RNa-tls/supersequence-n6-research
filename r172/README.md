# r172: EXPERIMENTAL R1 (token-split) architecture — NOT PRODUCTION

This directory is a bounded experiment approved for OLD-vs-R1 comparison only.

- Nothing here is a production certificate.
- No file here is referenced by any trust table.
- Nothing outside `r172/` was modified.

| file | contents |
|---|---|
| `THEOREM_R1.md` | theorem, proof, format, and verifier obligations |
| `R1_EXPERIMENT_REPORT.md` | results and verdict (`R1_SOUND_BUT_INSUFFICIENT`) |

Source files in `src/`:

| file | role |
|---|---|
| `gen172.py` | OLD/R1 generator; old mode is byte-identical to gen168 |
| `verifyA172.py`, `verifyB172.py` | the two independent EXTREE-4 verifiers |
| `casetable172.py` | finite case proof of the accounting identities |
| `mut172.py` | mutation suite |
| `regress172.py` | old-format regression |
| `dual172.py` | dual gate |
| `exp172.py`, `runq172.py` | bounded runs |
| `probe172.py` | complete failed-call probe |
| `summary172.py` | side-by-side table |
| `timing172.py` | clean overhead timing |
| `env172.py`, `trust172.py` | environment and trust set up exactly as Round 171 |
| `fixtures172.py` | test trees |

Results are in `certs/`.
