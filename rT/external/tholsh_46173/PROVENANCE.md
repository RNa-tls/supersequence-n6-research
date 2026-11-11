# Provenance and scope

Packaged 2026-10-20. Upstream source files are copied without modification.
The README and Makefile are packaging additions; they add no search logic.

## Jakub Halfar

Repository: https://github.com/jhalfar/superpermutations

Pinned source revision: `c9cb923057f757efa7c0f0e4c4cc1677ef3e6d3b`.

- `src/trailsearch.c` <- upstream `tools/trailsearch.c`.
- `src/applyplan.py`, `src/geng.py`, `src/gen12.py` <- upstream `reproduce/tools/`.
- `LICENSE` and `NOTICE` are the upstream originals and must be retained.

The original n=8 probe used the existing local `trailsearch.exe` with SHA-256
`f833cdcbfb47543fc21067eb916fcc42cef2cd13397f9c0ba94d3adf46991a25`.
The included C source is byte-identical to the pinned upstream source and
the local source retained with that tool family. Rebuilding is tested for
byte-exact plan replay, not claimed to reproduce a compiler-identical EXE.

Halfar supplied the input selection: four 27-loop, charge-16 walks and
twelve remaining source loops, completed as sixteen closed trails. His
46,174 word and its plan are the reference. The selection and the existing
randomized assembler are his, not new code authored for this probe.

The actual 60-second probe is retained in `evidence/discovery.log`.
The final solution plan is the exact reproducible result. Its three
weight-2 openings have IDs 14,15,13 and offsets 6538,8616,3415, respectively.
All sixteen final events are complete-trail `O` events, with g1=0.

## Jay Pantone

Repository: https://github.com/jaypantone/superperm-upper-43-80

Literal checker source revision: `c8fb7ffdd69be1375580710ae11b47a295b1f0f6`.

- `src/literal_check.cpp` <- upstream `tools/literal_check.cpp`.
- Upstream license: Apache License 2.0, as retained in `LICENSE`.

The construction's loops, slices, completion, transport, and closed trails
are Pantone's. The checker is independent of the search/replay program.
Original run receipts also record a second, independently implemented
inversion-rank scanner; that separate implementation is not needed for
this small source package and is not included.

## This experiment

The new assembly preserves Halfar's selected sixteen complete trails.
It changes order and opening positions, paying three extra opening
symbols while reducing joins from 25 to 21. The word is one shorter than
the inspected 46,174 reference. This is not an all-n construction,
proof of minimum length, or survey of concurrent unpublished results.

Original experiment directory:
`research/halfar-n8-46174-20261020/` in the source workspace.
No original third-party code is relicensed by this package.
