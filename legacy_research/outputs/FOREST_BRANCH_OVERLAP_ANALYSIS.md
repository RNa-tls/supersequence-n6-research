# Forest branch overlap and port-lift failure analysis

## Scope and reproducibility

This is a read-only analysis of the two already completed, independently verified branch files. It does not touch the supervisor, running branches, enumerator, generator, or existing branch JSON.

- Analysis code SHA-256: `60db6cac5c4a0c46437acc3327d083cc538da188482318dde5995df691eac420`
- Core transition code SHA-256: `18f75735b08fc061765e33cc661a084c8735e433e80ee8035a163b113ee39d60`
- Input `0,2` SHA-256: `3fd842db73dd8e56e8335a2bde57ef3ba23bb55b91a4a37f475b32e1e6f0c7d3`
- Input `0,3` SHA-256: `36d4d4b75d20b75560b151b06e56db287930c21b6001943d9b4fc7b74fa7f194`

## Branch overlap

| branch seed | raw certificates | unique cover SHA-256 |
| --- | --- | --- |
| 0,2 | 326 | 326 |
| 0,3 | 326 | 326 |

The SHA sets are exactly equal: intersection = 326, union = 326. Every shared SHA has byte-for-byte identical serialized certificate content after parsed JSON comparison: 0 differences.

This is not reported as an enumerator error. Canonical-child augmentation plus memoization removes repetitions within a branch, but the completed depth-2 branches maintain separate memo tables. Hence different seeds can re-enter the same canonical descendants. The matching count 326 is therefore explained by cross-seed duplication of the same canonical set, not treated as evidence for 652 classes or as coincidence.

## Exact DP facts from certificates

| H=3 maximum f-cycles reached | covers |
| --- | --- |
| 9 | 8 |
| 10 | 6 |
| 11 | 20 |
| 12 | 64 |
| 13 | 164 |
| 14 | 64 |

All 326 canonical covers have `complete_lift_exists=false` for each recorded budget H=0,1,2,3. These are certificate facts, not extrapolations to unfinished branches or to other (F,D,N) slabs.

## Structural tests

- A. Forest component-size partition determines H=3 `max_cycles_reached`: **False**.
- B. f-cycle length multiset determines H=3 failure profile: **False**.
- C. The implemented unlabeled forest-topology + cycle-length + collision-edge-incidence fingerprint determines H=3 profile in this data: **False**.

For A--C, `false` means the report JSON contains a lexicographically selected counterexample pair; `true` would mean only no counterexample in this 326-cover union, not a theorem.

The C counterexample fixes the full implemented unlabeled fingerprint, yet has a different H=3 layer-state-count profile. Thus the fingerprint is insufficient for exact DP-profile prediction in this finite data. The missing information is port-level phase/deep-tail transport; this is a computed counterexample to sufficiency of the stated fingerprint, not a general theorem about every possible structural invariant.

## Phase-aware lifted diagnostic graph

For each cover, the analysis reused the main program's `w2_permutation` and `deep_edges` APIs to construct states `(f-cycle, forced exit port, heavy spent)`. Its reconstructed H=3 collapsed cycle-arc count, SCC sizes, and weak-component sizes were asserted equal to the certificate diagnostics for all covers. The graph deliberately omits the exact DP visited-cycle mask. It is therefore useful for local transport/SCC diagnostics but cannot itself prove the no-revisit obstruction; no mask-free cut or common terminal entry phase is claimed.

## Bounded potential search

The JSON records a deliberately limited coefficient search on five static diagnostic-state features. It is exploratory only, excludes the tautological budget-only potential, and is not a proof because the graph has forgotten the visited-cycle mask.

## Candidate lemmas (explicitly not yet theorems)

> For every C in the completed canonical SHA union B_02 union B_03, an H<=3 exact port-lift does not visit all 20 f-cycles.

Tested covers: 326; counterexamples: 0; observed H=3 maximum: 14.  
Status: Finite computation for this duplicated two-branch union only; not a theorem about all forest covers.

> For every C in the current union with collision component partition [6, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], an H<=3 exact port-lift reaches at most 14 f-cycles.

Tested covers: 248; counterexamples: 0; observed H=3 maximum: 14.  
Status: No counterexample in this finite input union; partition alone is not sufficient to determine the full H=3 profile.

> For every C in the current union with collision component partition [3, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], an H<=3 exact port-lift reaches at most 13 f-cycles.

Tested covers: 76; counterexamples: 0; observed H=3 maximum: 13.  
Status: No counterexample in this finite input union; partition alone is not sufficient to determine the full H=3 profile.

## Failure archetypes

Using the requested strict H=3 layer-state-count profile together with the other minimum fields gives 326 groups over 326 covers. If this equals 326, the strict profile is too fine to compress the data: it should not be represented as a falsely small number of identical archetypes. A coarser grouping by H=3 maximum, first empty layer, forest partition, and f-cycle multiset gives 11 diagnostic groups; its representatives and the strict groups are in `forest_failure_archetypes.json`.

## Epistemic status

- **Computed exactly for this input union:** branch overlap; all stored DP profiles; all reconstructed local-transition/SCC consistency assertions; all stated fingerprints and counterexample pairs.
- **No-counterexample claims:** only where explicitly labelled as such in the JSON, and only for these 326 canonical covers (not 652 independent covers).
- **Not established here:** a proof for all five branches, a full port-lift obstruction beyond the certificate's stated relaxation, the other F<5 slabs, removal of NR6, or `L_6 >= 872`.
