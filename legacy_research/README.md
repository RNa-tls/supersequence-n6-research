# legacy_research/

This directory is the actual local research corpus behind the long n=6
superpermutation progress summary referenced earlier in this repo's
history. It was uploaded as a ~30MB zip on 2026-07-23 and integrated here
verbatim (not rewritten, not re-derived) except for the exclusions below.
It is kept separate from `src/`, `tests/`, and `experiments/` (this repo's
own from-scratch, independently-verified infrastructure) so the two bodies
of work are never confused with each other.

## Provenance and what was excluded

Source: a local Windows working directory (`Codex\2026-07-20\a-n-ge-4-s-n`),
containing `outputs/` (markdown write-ups, JSON data/certificates, logs)
and `work/` (Python scripts + a few PowerShell launchers).

Per explicit instruction, the following were **not** committed:

| Pattern | What / why |
|---|---|
| `*checkpoint*.json` | `f1_small_n0.retry2.checkpoint.json` (696MB) — a live, still-in-progress search checkpoint, not a result artifact, and far too large besides |
| `*.tmp` | none present in this upload |
| `*backup*.json` | none present in this upload |
| `__pycache__/`, `*.pyc` | 19 compiled bytecode files under `work/__pycache__/` |
| files > 100MB | only the checkpoint above qualified |

279 of 280 files were copied (139MB total); only the one checkpoint file
was excluded. Nothing already in this repository (`src/`, `tests/`,
`experiments/`, `STATUS.md`, `README.md`) was touched, moved, or deleted.

## What this actually is

A substantial, careful, self-auditing exploration of the NR6-conditional
lower bound approach described in `outputs/SUPERPERMUTATION_RESEARCH_RECORD_KO.md`
(the main write-up, in Korean) — permutation-transition/E-orbit/hexagon-cover
structure, a genus-zero + multiplicity-2 finite theorem about saturated
25-orbit covers, a canonical-augmentation enumeration of "forest" covers,
and an in-progress exact-state search for the `F=1, H=0, N=0` subcase.

The material is internally disciplined about proof status — it
consistently distinguishes **증명됨** (proved), **유한 계산 인증** (closed
by a finite computation), **실험** (sampled/experimental, not exhaustive),
and **반증됨** (disproved by explicit counterexample), and its own final
status table (`outputs/SUPERPERMUTATION_RESEARCH_RECORD_KO.md`, section 16)
already marks the things that matter most here as **open**:

| layer | status (as recorded by the original work) |
|---|---|
| Theorem A: `(n-1)S + (n-2)F >= (n-1)!` | proved |
| n=6 coordinate system `L = 867 + k + N + H` | derived by definition |
| `F=0` full-cassette `L >= 873` | proved in that range |
| saturated-cover genus-zero | proved by finite computational certificate |
| saturated-cover multiplicity `115x1 + 5x2` | proved by finite computational certificate |
| `c=20 <=> collision graph is a forest` | proved |
| exact-partition-plus-one `H<=3` port-lift failure | fully computed/certified |
| general forest-cover `H<=3` port-lift failure | every sample so far fails; **not** exhaustive |
| `F<5` branch | **open** |
| removing the NR6 assumption | **open** |
| conditional `L_6 >= 872` | **open** |

**No stronger claim is made here than what is in that table.** In
particular:

- The `F=1, H=0, N=0` exact-state search (the thing that was running when
  this upload was made) is **incomplete**. See
  `outputs/RESEARCH_EXECUTION_STATUS.md`,
  `outputs/F1_N0_LIVE_STATUS.md`, and
  `outputs/F1_N0_COMMITTED_RESUME_FINAL_STATUS.md`: as of the last
  recorded checkpoint, 36,250 nodes expanded, 114,182 accepted, 77,932
  frontier, 142 terminal certificates, **0 success certificates**, and the
  run had been interrupted twice. `RESEARCH_EXECUTION_STATUS.md` says this
  explicitly: *"No global lower-bound conclusion is licensed until the
  active search has completed and the passive finalizer has recorded both
  replays."*
- **Neither `L_6 >= 872` nor `L_6 = 872` is proved here**, conditionally or
  unconditionally. Nothing in this repository should be read or cited as
  claiming otherwise.
- The 872-length upper-bound construction (Egan/Houston) is discussed but
  its literal string is **not** included in this corpus — only an
  independently generated/verified classical 873-length construction is
  present.

For this repo's own (separately built, deliberately simpler) verification
tooling and its account of the published literature, see the top-level
[`STATUS.md`](../STATUS.md).

## Layout

- `SUPERPERMUTATION_RESEARCH_RECORD_KO.md`, `RESEARCH_EXECUTION_STATUS.md`,
  `EXECUTION_LOG.md` (in `outputs/`) — start here for the overall
  narrative and the most current status.
- `outputs/*.md` — individual theorem/analysis write-ups (genus-zero
  certificate, multiplicity-two theorem, forest enumeration, F=1 defect
  analyses, etc.).
- `outputs/*.json`, `outputs/*.log`, `outputs/*.jsonl` — the data,
  certificates, and run logs those write-ups cite.
- `work/*.py` — the Python implementation (enumeration, canonical
  augmentation, port-lift verifiers, etc.); `work/*.ps1` — the Windows
  launch scripts used to run long searches with checkpoint/resume.
- `PARTIAL_F1_*.md`, `SEMI_SATURATED_F2_TO_F4_ARCHITECTURE.md` (top level
  of this directory) — the F<5 exact-state-model design docs.

## Continuing this work

The excluded checkpoint (`f1_small_n0.retry2.checkpoint.json`, 696MB) is
the resumable state for the still-incomplete `F=1, H=0, N=0` search. It
was deliberately not committed (too large, and a live checkpoint isn't a
result). Anyone resuming that search needs the original local copy; the
scripts expecting it are in `work/` (see `run_f1_small_n0_retry2.ps1` /
`run_f1_small_n0_committed_resume.ps1`).
