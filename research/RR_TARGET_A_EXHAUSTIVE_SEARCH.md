# Round 35: root-local Target-A traversal

## Scope and status

This program searches **only** the 22 raw incomplete long-prefix roots in
`outputs/rr_target_a_22_root_ledger.json`.  It is not an NR6 completion, an
`N=0` search, or a Target-B/Target-C traversal.  A positive `--node-limit`
or `--max-depth` produces `INCOMPLETE`; neither condition is evidence of
impossibility.

The checked-in Round-35 run is a bounded pilot only:

```text
root: R27-prefix-6
node limit: 8,000
result: INCOMPLETE
frontier at stop: nonempty
Target-A boundaries: 0
```

Consequently no root has the status `EXHAUSTED_NO_TARGET_A` in this artifact
set, and no conclusion about all 22 roots is licensed.

## Exact objects reused

| Source | Role in the new traversal |
| --- | --- |
| `legacy_research/work/superperm_partial_f1.py` | literal `ExactState`, `extend`, visited-window collision semantics, and accounting |
| `legacy_research/work/superperm_partial_f1_macro.py` | legal rotation runs, H=0 macro candidates, and exact Area-A necessary prune |
| `src/build_rr_long_excursion_roots.py` | deterministic audited-root reconstruction context |
| `src/search_rr_long_prefix_extensions.py` | inherited literal root/replay and RR-boundary conventions |
| `src/analyze_rr_target_b_survivors.py` | canonical comparison for an actually new Target-A boundary |

No historical cap or timeout is used as a prune.  The new search regenerates
every literal macro candidate; an attempted joint with a repeated permutation
window is counted and is not silently omitted.

## Traversal

`src/search_rr_target_a_exhaustive.py` performs deterministic root-local LIFO
DFS.  Successors are sorted by literal macro label before stack insertion.
The raw memo key is the exact state plus the conservative RR decoration
specified in `RR_TARGET_A_STATE_KEY.md`.  A prospective second `R` is a
boundary: it is recognized and serialized, never expanded through.  This is
the scoped meaning of a Target-A traversal.

The only result labels are:

* `FOUND_TARGET_A` — a literal R2 boundary passed the recognizer;
* `EXHAUSTED_NO_TARGET_A` — only after the frontier is empty and no limit or
  interruption occurred;
* `INCOMPLETE` — a cap, depth bound, or externally interrupted run with a
  persisted frontier.

## Checkpoint protocol

Each root checkpoint stores the configuration, code hashes, serialized exact
frontier, decoration, witnesses, memo keys, counters, and the checkpoint
lineage digest.  It is written `*.tmp` then atomically replaced.  Resume
asserts the root literal hash, registry hash, and every engine/source SHA-256;
therefore a checkpoint from a different search implementation cannot be
silently resumed.

Proof run form (no cap):

```powershell
$py = (Get-Command python).Source
& $py src\search_rr_target_a_exhaustive.py `
  --root-id R27-prefix-6 --node-limit 0 `
  --checkpoint-dir outputs\checkpoints\rr_target_a `
  --checkpoint-every 10000 --resume
```

The 22 roots must be invoked independently or by an external supervisor; a
completed root does not authorize a conclusion for another root.

## Target-A recognition and downstream handling

At an R2 boundary the recognizer independently records: exactly two R events,
immediate R2 timing, `F <= 1`, `Ndef = 2`, `H = 0`, Area-A legality, the
same-component relation, chaining relation, and CH1/CH2 classification.
Same-component is an acceptance condition here; chaining is reported rather
than silently assumed.  Target B/C are not declared by this recognizer.

Each found boundary is canonically compared with the reconstructed true
canonical hashes of the 18 historical Target-A boundaries.  A known boundary
is not sent through Target B again.  A genuinely new boundary gets the coarse
capacity check.  Any later phase/R/flow analysis is deliberately marked
`PENDING_GENERIC_VALIDATION` unless the existing verifier's hypotheses have
been independently checked for that boundary.

## Reproduction commands

Bounded pilot and independent replay:

```powershell
$py = (Get-Command python).Source
& $py src\search_rr_target_a_exhaustive.py `
  --root-id R27-prefix-6 --node-limit 8000 --checkpoint-every 1000 `
  --checkpoint-dir outputs\checkpoints\rr_target_a_pilot `
  --audit-state-key `
  --output outputs\rr_target_a_exhaustive_results.json `
  --certificates outputs\rr_target_a_exhaustion_certificates.json `
  --new-boundaries outputs\rr_target_a_new_boundaries.json
& $py src\verify_rr_target_a_exhaustive.py `
  --results outputs\rr_target_a_exhaustive_results.json `
  --certificates outputs\rr_target_a_exhaustion_certificates.json `
  --output outputs\rr_target_a_exhaustive_verified.json
```
