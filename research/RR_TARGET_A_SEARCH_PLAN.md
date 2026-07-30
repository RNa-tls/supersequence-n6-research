# Round 35 — exact Target-A coverage plan

## Purpose and non-goal

This document specifies the next implementation only.  It does **not** start
the cap-free search and does not convert prior cap exhaustion into a theorem.
The input roots are the 22 audited singleton roots in
`outputs/rr_target_a_22_root_ledger.json`.

The target is a Target-A **boundary**, not Target B and not a complete NR6
walk.

## A. Deterministic roots and serialization

Roots are replayed with
`build_rr_long_excursion_roots.py::replay_state`; their deterministic order is
increasing `prefix_index` from the ledger (`R27-prefix-<prefix_index>`).
The source serialization remains the literal prefix record in
`rr_long_excursion_prefixes.json`, including `(root_ell, literal_joint_word)`.

For every new result, retain:

* root ID and input-artifact SHA-256;
* literal macro trace, where an edge is `rot^ell;joint-label`;
* exact predecessor stable-key hash and child stable-key hash;
* R1 decoration, `O*`, source/target orbit and phase of R2;
* same-component and chaining values separately.

The literal witness format is already accepted by
`verify_rr_long_extension_certificate.py::replay_witness` and is the required
certificate format for a `FOUND` result.

## B. Target-A recognizer

The Round 35 recognizer evaluates a candidate joint from an exact predecessor
state and accepts it only if all of the following hold:

1. this event is the **second** R event (`r_seen_before==1`, candidate kind
   `R`, and `r_seen_after==2`);
2. the child passes exact Area-A legality;
3. `F_def <= 1`, `Ndef == 2`, and `H == 0` at the child;
4. source and target E-orbits, with phases, are recorded from the exact
   predecessor/transition; and
5. `same_component` is evaluated from the predecessor's orbit/hexagon
   incidence structure and **recorded separately**.

`chaining := (R1_target_orbit == R2_source_orbit)` is likewise recorded but
is not an acceptance condition.  Target B continuation and Target C/full-NR6
completion predicates are explicitly out of scope.

The old Round 27 recognizer required `F_def == 1`, `H == 0`, and same
component, while every old root already had `F_def==1`.  Round 35 must log the
additional `Ndef==2` condition rather than silently assuming it.

## C. CH1 / CH2 split and decorated continuation state

Search is partitioned by the hub-completer record:

* **CH1:** completer \(C\) is R1;
* **CH2:** completer \(C\) is Z2 and a preceding R1 exists.

CH1 has the existing hand theorem in `research/RR_SAME_COMPONENT_CHAINING_LONG.md`;
CH2 is not closed (`research/RR_CH2_STATUS_AFTER_R31.md`).  This is a search
partition, not an inference that CH2 chains.

Bare `ExactState` determines literal child legality because the engine's
`macro_edges()` and `area_a_prune_reason()` are functions of it.  It does not
by itself preserve all boundary labels required here.  The memo/certificate
key therefore transports under the same left-\(S_6\) action at least:

\[
(\text{ExactState},\ O_*,\ r_{\rm seen},\ R1_{\rm source/target},\
 C_{\rm seen},C_{\rm kind},C_{\rm target},C_{\rm macro\ index}).
\]

The current component relation, hub residual mask, and fresh-opening count
may be cached as diagnostics but must either be recomputed from `ExactState`
or included and checked on every child.  This preserves CH1/CH2 and chaining
data.  Minimality beyond this conservative key is **open**; no unproved
history quotient may be used.

## D. Safe-prune register

Only the following are enabled initially.

| prune | status and source | independent check / implementation rule |
|---|---|---|
| visited-permutation collision | exact engine semantics; `exact.extend(...) is None` | use the engine result directly |
| exact Area-A necessary conditions | `superperm_partial_f1_macro.py::area_a_prune_reason` | replay every retained witness; record reason histogram |
| \(\Phi<0\) | proved necessary maximum-cover bound in `research/J_CAPACITY_OBSTRUCTION.md`; it is already `remaining_window_capacity_prune` inside Area A | do not charge it twice as a second prune |
| `F_def`, `H`, `P`, `O`, final-D reachability, remaining starts/orbit credit, F1 normal form | individual monotone/necessary checks inside `area_a_prune_reason` | retain its literal reason in output |
| RR R budget | exact only within the RR reduction: no third R and R2 is terminal for Target A | store `r_seen`; never expand beyond an R2 candidate |
| hub touch count \(\le2\) | existing hand theorem, `research/RR_HUB_TOUCH_COUNT.md` | enable only after the new decorated ledger recomputes touch count exactly |

The following are **not** enabled: a guessed "Target-A terminal predecessor
unreachable" rule; `orbit1 phase4 unreachable` in a relaxed phase graph; any
empirical normal form; and any dominance/history merge.  They may be
diagnostics only until separately proved.

## E. Cap-free exhaustion protocol

Traverse each root deterministically, with no node cap and no timeout used as
proof.  Persist a disk-backed FIFO/DFS frontier (choice fixed in metadata),
the complete decorated canonical visited set, a monotonically numbered trace
parent table, and an atomic checkpoint manifest with SHA-256 of every chunk.
Checkpoint/resume must verify engine, source-input, and key-schema SHA-256
before continuing.

Per root, statuses are exactly:

* `FOUND`: a literal Target-A boundary certificate exists;
* `EXHAUSTED_NO_TARGET_A`: frontier naturally emptied with no recognized
  Target-A boundary; or
* `INCOMPLETE`: stopped externally, malformed checkpoint, or verification
  failure.

Only the second status supports a root-level nonexistence statement.  A
separate traversal or literal replay verifier replays every `FOUND` trace;
for an exhausted root it must recompute state-key/canonical-key uniqueness and
prune reason accounting from the frozen checkpoint/output.

## F. Automatic Target-B handoff

For each new, verified Target-A boundary:

1. canonicalize the decorated boundary and compare its hash with the known
   Target-A corpus (known 18 boundary states);
2. if known eliminated, record that provenance and do not rerun it;
3. otherwise apply the coarse capacity theorem;
4. apply the phase refinement;
5. apply the R-reuse penalty; and
6. only if it survives, invoke the Round-34 flow-first verifier.

The entry points are `src/analyze_rr_target_b_survivors.py`, the Round-34
successor/flow tools (`src/build_rr_segment_successors.py`,
`src/search_rr_target_b_flow.py`, `src/verify_rr_target_b_flow.py`), and their
existing certificate formats.  This pipeline has no authority to re-run or
alter known eliminated boundaries.

## Implementation surface

The planned new driver should consume the ledger rather than regenerate roots.
It may reuse: `search_rr_long_prefix_extensions.py::replay_state`,
`::component_roots`, `::joint_kind`; the exact macro engine in
`legacy_research/work/superperm_partial_f1_macro.py`; and the action transport
used by `build_rr_long_excursion_roots.py::canonical_pair_key`.  A dedicated
decorated-key constructor and checkpoint reader/writer are required before
the cap-free traversal begins.
