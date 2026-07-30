# Round 35 exhaustion certificates

## What constitutes a certificate

An `EXHAUSTED_NO_TARGET_A` record is valid only when its final serialized
frontier is empty and it has neither a positive-node-limit stop nor a
depth-limit stop.  Its root certificate contains:

* root identifier and literal replay hash;
* engine, search, recognizer, and prune-registry SHA-256 values;
* deterministic traversal order;
* total expanded/decorated/exact states, memo hits, depth, terminal and prune
  counts;
* final empty frontier and checkpoint lineage;
* result digest and every found-boundary replay, if applicable.

`src/verify_rr_target_a_exhaustive.py` reconstructs the root literally and
replays each serialized found trace through an independently loaded exact
engine.  It re-evaluates the R2 conditions and validates root/config/manifest
hashes.  The optional `--replay-exhausted` mode independently reruns the
deterministic direct traversal of an exhausted root; it is intended for a
completed proof run, not for the bounded pilot.

## Current artifact

The current pilot certificate is an **incomplete checkpoint manifest**, not an
exhaustion certificate.  It records the nonempty frontier and the intentional
8,000-node cap.  The verifier accepting it means the bounded computation is
well-formed; it does not change its status to exhaustive.

## Required proof-run workflow

1. Run a root with `--node-limit 0` and no `--max-depth`.
2. Preserve its checkpoint lineage and source hashes.
3. Require `EXHAUSTED_NO_TARGET_A`, an empty frontier, and no truncation.
4. Run the independent verifier, then `--replay-exhausted`.
5. Only then aggregate independently verified root certificates.  A missing,
   capped, interrupted, or hash-mismatched root remains `INCOMPLETE`.
