# Round 48 — R2 literal-source correction

## Scope and status

**Finite replay verification completed.** This correction concerns only the
already-fixed fair `short_ell0` prefix: four independent R1 subroots, each
with exactly 25,000 expansions. It does not resume or deepen any continuation
search.

The historical repair hierarchy interpreted an R2 macro edge at macro entry.
For an edge `rot^ell ; joint`, that word can differ from the literal joint
source after the rotation run. Target A's source-orbit, incidence membership,
and same-component conditions must instead be evaluated at
`edge.run.state`.

\[
  \operatorname{R2Source}(\operatorname{rot}^\ell;J)
  = \texttt{edge.run.state},
  \qquad\text{not macro-entry state.}
\]

## Call-site correction

| Location | Historical state | Correct state | Role |
|---|---|---|---|
| `target_a_recognizer` | ambiguously named `pre_state` | `joint_source_state` | source orbit, forest endpoints, same-component, chaining |
| `geometry_failure_record` | `pre_state` | literal joint source | R2 endpoint evidence |
| `same_component_failure_record` | `pre_state` | `edge.run.state` | component-mismatch evidence |
| `hierarchy_for_r2` | macro entry | `edge.run.state` | repair hierarchy R2 classification |
| `predicate_before_r2` | ambiguous `pre_state` | literal joint source | focused pre-Target-A predicate |
| `repair_predicate` | ambiguous `pre_state` | literal joint source | repair predicate |
| `verify_rr_short_ell0_repair_search.py` | macro entry | literal joint source | independent replay |

The machine-readable table, historical SHA-256 values, and a concrete
counterexample fixture are in
`outputs/rr_r2_source_callsite_audit.json`.

## Schema firewall

New outputs use:

```text
rr-short-ell0-fair-repair-v2-literal-r2-source
rr-short-ell0-fair-repair-checkpoint-v2-literal-r2-source
```

Every corrected R2 record serializes both the macro-entry provenance and the
post-rotation/literal joint source, together with a role map specifying that
Target A, incidence membership, and same-component consume the literal joint
source. Historical v1 hierarchy artifacts are preserved, but explicitly
classified `INVALID_R2_SOURCE_SEMANTICS`; they are not overwritten or used as
corrected boundary evidence.

## Regression fixture

The fixture
`tests/fixtures/rr_r2_literal_source_counterexample.json` is a literal macro
trace for which the final R2 has `rot^4;w3:120`:

* macro-entry hash: `631d91e53c…e9495f`, same-component = true;
* literal joint-source hash: `348e1dd64f…f7b93e`, same-component = false.

The test reconstructs every macro edge and asserts that
`hierarchy_for_r2` agrees with the literal-joint-source recognizer. This is a
regression against silently passing macro entry to the recognizer.

## Corrected replay ledger

The traversal was unchanged: the old and v2 node-parent transcript hashes
agree branch-by-branch. Only boundary interpretation changed.

| Quantity | Count |
|---|---:|
| Fair branches | 4 |
| Expansions per branch | 25,000 |
| Repaired R2 paths | 46,128 |
| Historical macro-entry Target-A claims | 38,406 |
| Corrected literal same-component failures | 38,405 |
| Corrected literal Target-A hits | 1 |
| Canonical boundary classes | 1 |
| New canonical classes | 0 |

The one remaining class is proved-left-`S_6` equivalent to known-18 class
`short_ell0_33d70b4249b7`. The independent verifier replays every R2 path
from its parent DAG, then repeats the helper-free Target-B continuation DFS.

## Limits

This is a correction of a capped prefix, not an absence theorem for the five
short roots or for all Target A. It establishes neither `L_6 >= 872` nor a
general repair-hierarchy theorem.
