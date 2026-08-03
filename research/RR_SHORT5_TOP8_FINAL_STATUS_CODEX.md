# Round 52 — official v6 top-8 endpoint ledger

## Certified fixed-cap endpoint

The v6 top-8 run is closed only at its stated fixed-cap endpoints:

| measure | value |
| --- | ---: |
| selected children | 8 |
| natural empty-frontier certificates | 6 |
| cap-reached nonempty frontiers | 2 |
| exact additional expansions | 167,820 |
| repair literal replays | 207,842 |
| R2 literal replays | 99,438 |
| incidence component merges | 0 |
| bridge-template occurrences | 0 |
| literal Target A hits | 0 |
| Target B survivors | 0 |

The independent ledger verifier passed. This does not prove that the top-8
continuation space is empty: two branches remain capped.

## Capped endpoints

| child | total expansions | frontier | max depth | checkpoint SHA-256 |
| --- | ---: | ---: | ---: | --- |
| `short_ell2_r1_70` | 55,000 | 11 | 100 | `d42a446eb125364a7cd2786504f9ca790ded10b556e861137b788f3b2ff43587` |
| `short_ell2_r1_37` | 55,000 | 19 | 100 | `36404b918ffe335bbfa5607cb1a187ab85e16b416e123028be31eaddcee2f671` |

Their canonical frontier-engine-state digests are respectively
`0de5382a5d102db6cff1f54b02526cbdc04674c5aecf5a3d6153555b11bb2850`
and `9465498b993a042bfb0c9604e6b3a7a5f02fa31b0b2f6b139992e9738729dbd5`.
Each digest covers every frontier node id, exact state hash, decoration,
lineage, and literal parent-DAG trace hash. The nearest recorded profile for
both has zero bridge events and zero literal Target A hits; this is an
observation at the 50,000 cap only.

## Frozen empty-frontier certificates

`short_ell4_r1_12`, `short_ell1_r1_98`, `short_ell2_r1_40`,
`short_ell3_r1_64`, `short_ell2_r1_107`, and `short_ell3_r1_56` each have a
complete atomic checkpoint with `frontier=[]`. Their ledger records exact
checkpoint SHA, config hash, total expansions, terminal prune histogram,
maximum depth, repair/R2 candidate counts, and component-merge count. These
six certificates remain valid independently of later v7 schema work.

The complete machine-readable record is
`outputs/rr_short5_top8_official_ledger.json`.
