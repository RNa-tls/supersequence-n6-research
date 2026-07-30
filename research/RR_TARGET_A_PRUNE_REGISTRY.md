# Round 35 Target-A prune registry

Every active prune is exact or a previously proved necessary condition.  The
registry is serialized and SHA-256 hashed into every checkpoint and root
result.

| Name | Mathematical condition | Implementation | Evidence |
| --- | --- | --- | --- |
| `exact_permutation_collision` | the candidate's new window was already visited | `iter_raw_macro_candidates` / exact `extend` | exact engine semantics |
| `area_a_necessary_conditions` | inherited Area-A necessary condition fails | `macro.area_a_prune_reason` | existing macro-engine tests |
| `phi_negative` | inherited capacity potential is negative | a named subcase of Area-A, never double-counted | `research/J_CAPACITY_OBSTRUCTION.md` |
| `rr_R_budget` | scoped word has more than two R's, or attempts to continue after R2 | `evaluate_edge` | Round-27 RR model |
| `hub_touch_count` | a joint target touches the distinguished hub more than twice under `F <= 1` | `advance_decoration`/`evaluate_edge` | `research/RR_HUB_TOUCH_COUNT.md` |

The following are intentionally **not** active: heuristic depth scoring,
beam width, state dominance, terminal-predecessor normal forms, relaxed
phase-4 reachability, and any unproved T3/CH2 simplification.  They may be
measured externally, but never delete a state in this traversal.

The test module `tests/test_rr_target_a_exhaustive.py` checks that collision
is counted, Area-A reasons are preserved, R2 is a boundary rather than a
child, and the registry contains no heuristic class.
