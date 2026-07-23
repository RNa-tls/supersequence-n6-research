# F=1, H=0, N=0 live exact-search status

**Status: `N=0 exhaustive search resumed from committed checkpoint`.**

The earlier PID 4448 run ended without a final output.  Its committed
checkpoint, not the newer uncommitted `.tmp` payload, was copied into immutable
evidence backups and is the sole `--resume` input for the current run.

| field | value |
|---|---:|
| committed resume source | `f1_small_n0.checkpoint.json` |
| source expansions | 25,000 |
| source canonical states | 79,683 |
| source frontier | 54,683 |
| node limit / memory limit | 0 / 0 MiB |
| current supervisor PID | 27752 |
| current Python PID | 9696 |

The supervisor writes only new artifacts named
`f1_small_n0_committed_resume*`.  It polls the child process and new atomic
checkpoint, performs no automatic restart, and runs structural and full
literal-replay verification only if a completed final result is produced.

The `.tmp` payload remains comparison evidence only and is never an input to
this resumed search.  The two immutable backups, their SHA-256 values, sizes,
and timestamps are in
[`f1_n0_committed_resume_preflight.json`](f1_n0_committed_resume_preflight.json).
Live machine-readable state is in
[`f1_small_n0_committed_resume_status.json`](f1_small_n0_committed_resume_status.json).

No nonexistence conclusion is permitted until this new run reports
`completed=true` and both verifiers pass.
