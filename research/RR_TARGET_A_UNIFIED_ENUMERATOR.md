# The unified Target A enumerator

Round 36, Part D (sections 11-14). Source `src/search_rr_target_a_unified.py`.

## 1. The minimal decorated key (§11)

`decorated_key(state, r_count) = (state.stable_key(), r_count)`.

**Claim.** No further decoration is needed — not R1 source/target, not
CH1/CH2 status, not a stored component-ancestry relation, not the
first-return class, not the abandonment ell.

**Proof.** Every one of those candidate decorations is *recoverable* from
`(state, r_count)` at the moment it is needed, rather than being
independent information:

* R1 source/target and CH1/CH2 status are properties of the **path taken to
  reach the state**, but Target A's recognizer never asks "how did we get
  here" — it asks a question about the exact R2-edge candidate (child
  `F_def`, child `H`, same-component of the **pre-joint** state). The
  pre-joint state at that moment is fully determined by `state` itself
  (it's whatever the search is standing on when it considers an R edge), so
  no history needs to be carried forward.
* The component-ancestry relation is recomputed **fresh from
  `orbit_masks`** every time `component_forest` is called (both in Round 35
  and here) — it was never stored as a running structure, and doesn't need
  to be, since `orbit_masks` already contains every fact the forest is built
  from.
* The first-return class and abandonment ell are properties of the *root*,
  constant for an entire search run — they never vary state to state within
  one enumeration, so they add no discriminating power to a per-state key.

So two different histories that arrive at the identical `(stable_key,
r_count)` pair have **identical future Target-A reachability**: every
subsequent macro edge is a pure function of `(ExactState, r_count)`, and the
recognizer is a pure function of the same two things at the point it is
evaluated. Merging on this key cannot lose a boundary.

## 2. Deterministic traversal (§12)

* **Root order**: fixed by the driver (`run_rr_target_a_coverage.py`) —
  short-family roots in `ell` order, long roots by `prefix_index`.
* **Edge order**: `sorted_macro_edges` orders every macro edge by
  `(rotation run length, joint label)` — a total order, so branching is
  identical across runs and platforms.
* **Checkpoint / resume**: every `checkpoint_every` expansions and once at
  the end, the frontier (`ExactState` fields serialized directly — `p`,
  `hex_masks`, `orbit_masks`, `F`, `S`, `H` — not re-derived by replay), the
  seen-set as SHA-256 hashes of the decorated key, the hit list, and running
  stats are written to `outputs/rr_target_a_checkpoints/<key>.json`.
  `--resume` reconstructs `ExactState` objects directly via the frozen
  dataclass constructor, so resumption is exact, not approximate.
* **Parent pointer / exact witness replay**: each frontier entry (and each
  hit) carries its own `path` — the literal sequence of macro-edge labels
  from the root — so any boundary found can be replayed edge-by-edge with no
  additional bookkeeping. This is checked directly:
  `tests/test_rr_target_a_unified.py::test_hit_path_replays_to_the_hit_hash`
  literally replays a found hit's `path` from its root and confirms the
  resulting state's hash matches `boundary_raw_hash`.

## 3. Boundary deduplication levels (§13)

A found boundary is recorded at four levels simultaneously in every hit
record:

| level | field |
|---|---|
| words | `path` (the literal macro-edge label sequence) |
| raw boundary state | `boundary_raw_hash` (SHA-256 of `stable_key()`, truncated to 16 hex chars) |
| canonical boundary state | `boundary_canonical_hash` (SHA-256 of `exact.canonicalize(state).stable_key()`) |
| decorated boundary class | implicit in `(boundary_raw_hash, extension_depth)` — no coarser decorated class than the raw state is used, since §11 already showed the decoration adds nothing |

**The existing 18 are counted at the raw-boundary-STATE level**, not at the
word level — this matches `outputs/rr_target_b_survivors.json`'s convention
(18 distinct `canonical_state_hash` values, one per boundary). Stated
explicitly here so a reader never has to infer the unit from context.

A CORRECTION found while building the regression (§14): `P_core =
preparation_length − 2` holds only for the ell=0 branch. For ell=4 the
correct offset is `preparation_length − 1` (the ell=0 branch's R2 edge is a
full ℓ=5 rotation run, the ell=4 branch's is ℓ=0 — see
`RR_TARGET_A_BACKWARD_FILTER.md`, Round 35 — so the two branches' word
lengths carry different amounts of "free" rotation relative to `P_core`).
`verify_rr_target_a_coverage_status.py` does not use either offset formula:
it looks up each replayed boundary's `P_core` directly in
`rr_target_b_survivors.json` by `(root_ell, raw_hash)`, which is exact and
branch-independent.

## 4. Regression against the 18 currently known boundaries (§14)

`src/verify_rr_target_a_coverage_status.py` replays every one of the 18
currently known boundaries from its recorded preparation, and for each one
records: literal replay result, source root (which of the 5 short-family or
6 long-FOUND roots it came from), the literal search path, its raw and
canonical hashes, its CH1/CH2 classification (`CH_none` at the root, as
established in Round 35 — the branch is undetermined until the extension
reaches the hub), its `ell` and `P_core`, and its Round 34 Target B status
(`EXHAUSTED_NO_PATH`, independently verified UNSAT, for all 7 of the 18 that
survived to Round 34; the other 11 were removed earlier by the capacity
theorem, Rounds 30-32). Output: `outputs/rr_target_a_known18_regression.json`.

## 5. What "unified" means and does not mean

One engine, one status vocabulary, one prune classification, used for every
root source. It does **not** mean one search run: each root gets its own
independent budget and checkpoint (§18 of the brief), because a slow root
must never starve or corrupt the accounting of a fast one. It also does not
mean Target B is touched anywhere in this module — `enumerate_target_a`
stops at the R2 edge by construction (an R event is never expanded past),
matching every prior round's discipline.
