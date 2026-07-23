# supersequence-n6-research

Research into the minimal-length superpermutation on 6 symbols. See
[STATUS.md](STATUS.md) for what is actually proven, what is cited from the
literature, and what remains open.

## Quick start

```
python -m unittest discover -s tests -v   # run the test suite
python -m src.lower_bound                 # proven lower bound table
python -m src.construct                   # self-verified constructive witnesses
python -m src.exact_solve                 # from-scratch exhaustive proof for small n
python -m experiments.n6_search_baseline  # honest n=6 attempt (inconclusive)
```

## Layout

- `src/perms.py`, `src/verify.py` — permutation utilities and the
  ground-truth superpermutation checker.
- `src/lower_bound.py` — the published Houston/Pantone/Vatter lower bound.
- `src/construct.py` — a simple, correct, self-verified greedy constructor.
- `src/exact_solve.py` — exhaustive IDA* solver (proves L(n) for n <= 4).
- `experiments/` — bounded, honestly-reported attempts at the open n=6
  question.
- `data/known_witnesses.py` — literature-sourced example strings, each
  independently re-verified by this repo's own checker before being
  trusted (see `tests/test_literature_witnesses.py`).
- `tests/` — the test suite.
- `legacy_research/` — the actual local research corpus (write-ups, data,
  Python implementation) behind this project's deeper NR6-conditional
  lower-bound attempt. Much further along than `src/`, but its own headline
  claims (conditional `L_6 >= 872`, unconditional `L_6 = 872`) are marked
  **open** by the material itself. See `legacy_research/README.md`.
