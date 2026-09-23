# Round 171 production checkpoint: 11 / 35

The 20,000,000-node pass finished normally. The logged supervisor recorded
exit code 0. This is an intermediate production checkpoint, not completion
of the 35-bound program or an unconditional census closure.

## New genuine bounds since the initial six

| Cell | Upper bound | Proof nodes | A / B | Histogram mismatches |
|---|---:|---:|---|---:|
| 1\|6\|3\|1\|0\|0 | 111 | 7,037,801 | ACCEPT / ACCEPT | 0 |
| 1\|4\|5\|0\|1\|0 | 106 | 7,270,523 | ACCEPT / ACCEPT | 0 |
| 2\|1\|3\|0\|1\|0 | 104 | 14,731,120 | ACCEPT / ACCEPT | 0 |
| 2\|1\|3\|1\|0\|0 | 119 | 13,741,690 | ACCEPT / ACCEPT | 0 |
| 2\|2\|8\|0\|0\|0 | 123 | 16,717,435 | ACCEPT / ACCEPT | 0 |

Fresh own-tree dual replay was performed before each admission. The subsequent
progress audit checks the artifact hashes, predecessor DAG, source identities,
and exact accepted report rows; it does not claim another fresh tree replay.
The authoritative artifact is `certs/bulk_j171/manifest.json`.

## Independence-restricted census

`certs/bulk_j171/progress_11_codex.json` grants only genuine accepted bounds,
not the 24 unbacked J values. Historical basis fallback is disabled.

- All arithmetic rows: 1,487 STRICTLY_CLOSED, 44 EQUALITY, 78 SURVIVING.
- The 180 exposed rows: 60 STRICTLY_CLOSED, 42 EQUALITY, 78 SURVIVING.
- Required load-bearing bounds: 11 backed, 24 outstanding.

The older full-J census is conditional on proving every remaining J value.
The original six-bound base file is intentionally retained as the immutable
bootstrap input; the bulk manifest, not that base file, tracks current progress.

## Cost and interruptions

- New production proof nodes: 59,498,569.
- Completed cap-hit attempt nodes: 1,044,000,121.
- Separate bounded diagnostics: 623,159 nodes (422,572 earlier; 200,587 E probe).
- Known measured research total: 1,044,623,280 nodes.
- Three interrupted generation attempts have unknown additional node cost.
- A later worker-start failure occurred before any proof generation began.

Both interruption records and original job bytes are preserved under
`certs/bulk_j171/interruptions/`. No capped or interrupted result was promoted.
No new helper was admitted in this bulk run.

## E-family diagnostic

The unchanged 100k observation run and its no-observer control agree. The
candidate `1|2|0|0|0|0 <= 45` reached a feasible threshold in 195 nodes.
Explicit replay confirmed a 48-port witness (10 orbits, deficit 2, one token,
zero A/B/E/H use). This disproves that proposed helper, not any J target.

Of 23,253 recorded failed-prune calls, 20,185 demand an upper bound below 48
for a resource cell that contains this feasible witness. No sound scalar
capacity upper bound for those cells can satisfy those demanded thresholds.
This observation does not rule out state-sensitive reasoning or longer
production trees. No such new rule is introduced here.

## Next bounded pass

Use 50,000,000 nodes per outstanding cell and at most two workers. Existing
generation, J targets, proof format, and A/B verifiers remain unchanged.
The new scheduler only gates admission: stop new dispatch below 6 GiB free
RAM, or below 35% battery while off AC, then drain and checkpoint active jobs.
Unstarted jobs receive no cap-hit claim and no fabricated node count.

Four scheduling-only tests pass: threshold handling, hold before dispatch,
draining an active job without charging an unstarted job, and independent
per-cell caps. Older proof regressions were not rerun unnecessarily.

Final clean-checkout reproduction remains outstanding; this is not the final
report and does not claim 35/35.
