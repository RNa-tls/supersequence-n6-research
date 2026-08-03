# Round 52 — v6 auxiliary provenance-loss audit

## Finding

**AUXILIARY_PROVENANCE_NOT_CLOSED_UNDER_V5_CHECKPOINT_SERIALIZER**

At bootstrap, `search_rr_short5_top8_continuation.py` writes an auxiliary
top-level `top8_continuation` object containing the v6 schema, source
checkpoint path/SHA, base expansion count, and additional budget. It then
calls the shared v5 `run_branch` writer. The shared
`checkpoint_payload` is a whitelist serializer and emits only v5-native
fields, so its first atomic replacement silently drops that auxiliary object.

| call site | role | result |
| --- | --- | --- |
| `search_rr_short5_top8_continuation.py:45` | add v6 wrapper provenance | present only in bootstrap payload |
| `search_rr_short1_4_corrected_fair.py:311-318` | v5 checkpoint payload whitelist | omits wrapper provenance |
| `search_rr_short1_4_corrected_fair.py:454-465` | atomic rewrite | commits omission |
| `search_rr_short5_top8_continuation.py:46-48` | future v6 resume guard | requires omitted `source_sha256` |

The first affected version is the v6 wrapper introduced in `06dae7c`; the
shared serializer predates it in `4785cc6`. The first defective persisted
write is the first `run_branch` atomic checkpoint rewrite after bootstrap.

## Scope of impact

The following engine-critical data remain present and validated: v5 checkpoint
schema/config including engine and recognizer hashes, root and R1 child,
frontier, seen keys, parent DAG, repair records, R2 paths, statistics, and the
complete-frontier flag. All completed analysis and independent ledger results
remain valid because their v5 source SHA is separately anchored in the
immutable Round-50 aggregate and literal replay passed.

v5 is not retrospectively affected: it never claimed the v6 wrapper fields.
Only a wrapper that adds unrecognised top-level data to the shared serializer
would lose it. The existing v6 driver itself must not be used to resume these
payloads, because its guard later requires `top8_continuation.source_sha256`.

No v6 checkpoint was modified during this audit. Full call-site and schema
data are in `outputs/rr_v6_provenance_loss_audit.json`.
