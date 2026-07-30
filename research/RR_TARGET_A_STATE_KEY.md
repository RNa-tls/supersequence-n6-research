# Round 35 Target-A state key

## Key

The memoization key is deliberately conservative:

```text
(ExactState.stable_key(), Decoration.key())
```

`ExactState` retains the current permutation, every visited permutation
window, hexagon masks, E-orbit phase masks, and all exact resource counters.
It therefore decides literal legality, collision, Area-A pruning, the current
hub mask, and the current incidence components.  Those quantities are not
duplicated in the decoration.

| Decoration field | Updated by | Why it remains in the key | Effect |
| --- | --- | --- | --- |
| `root_ell`, `o_star`, `hub_id` | root construction | distinguish the audited root's terminal convention and hub | recognition/reporting |
| `macro_index` | every macro joint | preserves order of R/completer events | recognition/reporting |
| ordered `r_events` with source/target orbit and phase | every R joint | R1 endpoint and R-event order are not recoverable from masks | Target-A and chaining |
| `hub_touch_count` | a joint targeting the hub | enforces the proved hub-touch budget | pruning |
| `completer` with kind/source/target/phase | first hub-targeting joint | distinguishes CH1 and CH2 | recognition/reporting |

`root_id` is serialized for provenance but is not a semantic key coordinate:
each raw audited root is searched independently.  Current component ancestry,
hub residual mask, and opened-orbit information are recomputed from the exact
state.  No field is included merely because it appeared in a historical log.

## State-key audit

`--audit-state-key` reconstructs all 22 audited roots and their immediate
accepted children.  It deliberately repeats each sampled key and compares the
complete deterministic successor signature:

* literal legal macro-edge set, including collision outcomes;
* Area-A and other prune outcomes;
* Target-A recognizer result;
* child decorated keys.

The checked-in pilot audit has 88 deliberate duplicate groups and zero
signature mismatches.  It additionally mutates an R1 target in a known
witness and observes that chaining reporting changes; this guards against
dropping the R1 endpoint.

**Grade:** exhaustive tested-universe equivalence for this audit universe,
not an exact theorem about every possible future RR history.  The key is used
because it is a raw exact state plus all currently identified history on which
the scoped recognizer depends, not because an unproved canonical quotient has
been taken.

## Update consistency

`advance_decoration` is pure: it reads source coordinates after the literal
rotation run and target coordinates from the exact joint.  It creates an R
event only for the inherited RR `w3` R label, and freezes the first hub
completer.  Unit tests cover root replay, deliberate same-key signatures,
R-count/boundary negatives, and interruption/resume equivalence.
