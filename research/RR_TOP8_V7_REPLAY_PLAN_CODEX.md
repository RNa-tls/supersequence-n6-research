# Round 52 — replay-validated v7 plan

## No search in this round

v7 is a design and manifest only. It must not deserialize missing v6 wrapper
provenance as if it existed, and it must not overwrite or resume a v6
checkpoint.

## Required v7 initialization

For each capped branch, v7 will start from the immutable Round-50 v5 source
checkpoint and its frozen R1 literal trace. It will reconstruct every v6
frontier node through its serialized parent-DAG macro trace, then require:

1. recomputed v7 provenance from the immutable source;
2. exact state hash, decoration, decorated-key, and frontier digest equality;
3. identical legal successor signatures at every frontier state;
4. identical literal-joint-source R2 recognizer outputs for every legal R2
   candidate; and
5. a separate read-only verifier before any v7 continuation is scheduled.

The v7 schema must carry its own immutable provenance block: v5 source path
and SHA, v6 endpoint path and SHA, frontier digest, root/R1 hashes, R1 trace
hash, engine/driver/recognizer hashes, and initialization-verifier hash.

## Next-step comparison

| option | estimated scope | proof value | assessment |
| --- | --- | --- | --- |
| A: deepen the two capped top-8 branches | 100,000 first additional expansions under equal 50,000 caps | may add exact empty-frontier certificates | **recommended after v7 validation** |
| B: pilot all other 105 capped children | up to 5,250,000 expansions at the same cap | broader discovery coverage, weak near-term closure | defer |
| C: hand theorem from current data | little computation, open-ended theory | maximal if true | no current theorem: capped zero-bridge observations are insufficient |

Option A is smallest and most rigorously scoped: the two endpoints already
have only 11 and 19 frontier states. This is not a prediction of exhaustion or
of a new Target A class.

`outputs/rr_top8_v7_replay_manifest.json` lists the exact trusted anchors and
all validation requirements.
