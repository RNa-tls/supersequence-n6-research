# `short_ell0`: corrected official status

## Scope

This document integrates the correction history for the **capped**, equal-work
`short_ell0` experiment.  It does not start, resume, or extend a search.  Its
purpose is to prevent a historical telemetry count from being reused as a
literal Target-A count.

The current result is deliberately two-level:

```text
corrected 4 x 25,000 fair prefix: ALL_OBSERVED_TARGET_A_TARGET_B_CLOSED
global short_ell0 continuation:  OPEN / INCOMPLETE
```

In particular, no bounded run in this document is an exhaustion certificate.

## Historical-status separation

| Label | Status | Precise scope | Consequence |
|---|---|---|---|
| v1 | `R1_TRAVERSAL_COMPLETENESS_GAP` | Bare short roots started at `r_count=0`, but every R edge was terminally discarded. | The search covered only the pre-R subspace.  Its frontier/prune statistics are not short-root continuation evidence. |
| v2 | `Q2_ONLY_PRUNE_CONTAMINATION` | A Target-A prefix used completion-only Area-A/Q2 pruning, including `O>25`. | The bounded result is retained only as an Area-A/Q2 experiment, never as Target-A coverage. |
| old repair hierarchy | `INVALID_R2_SOURCE_SEMANTICS` | `hierarchy_for_r2` evaluated source-sensitive predicates at macro entry rather than the state after the rotation run. | Its R6/Target-A labels are historical false-positive telemetry, not boundary witnesses. |
| corrected fair prefix | `VALID_CAPPED_OBSERVATION` | Four exact R1 provenance roots, each given 25,000 expansions; Target-A-safe prune registry; literal R2 source. | Positive witnesses and their helper-free Target-B closure are valid in this observed prefix only. |

The v1 and v2 defects concern short-root search **scope**.  The last defect is
different: it was a hierarchy-classification defect in
`search_rr_short_ell0_repair_fair.py`.  The live
`evaluate_edge`/`target_a_recognizer` logic already used `edge.run.state` for
the literal joint source; the fair hierarchy did not.

## Official count ledger

All arrows below preserve their unit.  The first two quantities count repaired
R2 paths; the next quantities count literal/canonical boundary objects.

```text
38,406 historical macro-entry Target-A claims
  -> 38,405 literal-source same-component false positives
  ->      1 literal Target-A hit
  ->      1 left-S6 canonical class
  ->      1 known-18 class: short_ell0_33d70b4249b7
  ->      1 helper-free Target-B DFS, 3,214 nodes, empty frontier
  ->      0 unresolved classes in the corrected prefix
```

The sole literal hit is left-`S_6` equivalent to an already known class.  Its
independent helper-free continuation search returned `EXHAUSTED_NO_PATH` with
`truncated=false` after 3,214 nodes.  This closes Target B for the one class
**observed in this prefix**; it does not close unvisited `short_ell0` states.

## Correct literal-source contract

For a macro edge `rot^ell ; J`, the source of the literal joint is

\[
  \operatorname{R2Source}(\operatorname{rot}^\ell;J)
  = \texttt{edge.run.state},
\]

not the macro-entry state.  The repository now models the distinction with
`R2SemanticState` and two tags:

```text
R2_LITERAL_JOINT_SOURCE_V1
R2_MACRO_ENTRY_PROVENANCE_ONLY_V1
```

New source-sensitive production call sites pass the literal wrapper.  A
macro-entry wrapper is rejected by the Target-A recognizer.  Untagged raw
states remain accepted only as explicitly labelled historical/regression
controls, so old artifacts can be replayed without silently gaining the
status of a new schema.

## v4 checkpoint disposition and safe next namespace

The four historical `r1_split_v4` checkpoints preserve exact state,
decoration, trace, and R1-origin data.  They do **not** serialize the
source-semantics contract as a configuration field, and their engine SHA is
not the current engine SHA.  Moreover their allocation is not fair:
`short_ell0_r1_2` received 100,245 expansions while the other three recorded
root frontiers were not comparably expanded.

Therefore direct v4 resume is forbidden.  A future continuation uses the new
namespace:

```text
outputs/checkpoints/rr_short5/r1_split_v5_literal_source/
```

It may use **replay-validated migration** only if every imported frontier
state passes all of the following before it is enqueued:

1. replay the literal parent trace from the frozen R1 child;
2. compare exact-state hash and decoration with the checkpoint record;
3. recompute the decorated key and the R1-origin hash;
4. assign a fresh v5 config hash containing the engine hashes,
   `R2_LITERAL_JOINT_SOURCE_V1`, the Target-A-safe prune registry hash, and
   the scheduler specification.

Otherwise the v5 fair roots must be regenerated from their frozen literal R1
traces.  Hierarchy labels are never migrated: they are recomputed at the
literal joint source.

## Regression controls

The current controls enforce:

* `hierarchy_for_r2` calls the recognizer with a literal-joint-source wrapper;
* source-sensitive hierarchy fields serialize their semantic-state tag;
* a macro-entry wrapper is rejected by the literal recognizer;
* the historical hierarchy schema is rejected as
  `INVALID_R2_SOURCE_SEMANTICS` for current use; and
* the official machine-readable ledger fixes 38,406 as a **historical
  macro-entry** count, while `literal_target_a_hits` is exactly 1.

The state-key grade remains **exhaustive tested-universe equivalence**, not a
general theorem.

## Evidence and attribution

* Exact traversal and R2 literal-source correction: **CODEX**.
* Envelope and root-reduction facts: **CLAUDE, CODEX_VERIFIED**.
* The literal-source counterexample fixture and independent isolated-worktree
  reproduction: **CLAUDE, independently reproduced by CODEX**.
* The observed short-root target boundary is not a new class; its known-18
  mapping and helper-free Target-B closure are **CODEX_VERIFIED**.

Machine-readable integration is in
`outputs/rr_short_ell0_official_ledger.json`.
