# Round 42: `short_ell0` medium Target-A-safe v3 run

Status: **INCOMPLETE**.  The positive node cap makes this diagnostic only unless the frontier is empty.

## Scope

- Resumed only the immutable semantic v3 250-node pilot.
- No v1/v2 checkpoint and no other root was used.
- `target_a_semantic_v1` is the only enabled profile; Area-A/Q2 completion gates are disabled.

## Telemetry

| quantity | value |
|---|---:|
| expansions | 100250 |
| frontier | 85 |
| pre-R / post-R1 nodes | 5 / 100245 |
| R1 transitions / exported events | 4 / 4 |
| R2 candidates / Target-A hits | 49440 / 0 |
| max depth / max post-R1 depth | 103 / 103 |
| frontier r-counts | {0: 10, 1: 75} |

## Exact enabled-prune counts

`{'exact_permutation_collision': 1541360, 'F_exceeded': 172882, 'H_positive': 0, 'F1_fragment_normal_form_impossible': 0, 'rr_R_budget': 0, 'hub_touch_count': 0}`

Additional exact/model exits: `{'decorated_memo_duplicate': 107, 'exact_permutation_collision': 1541360, 'outside_RR_joint_model': 541873, 'r2_not_target': 49440, 'target_a_semantic_v1:F_exceeded': 172882}`

Completion-only gates are asserted absent: {'P_exceeded': 0, 'O_exceeded': 0, 'Ndef_cap': 0, 'D4_reachability': 0, 'Phi_window_capacity': 0, 'future_orbit_credit': 0}

## R2 outcome ledger

`{'TARGET_A_HIT': 0, 'wrong_R_count': 0, 'wrong_Ndef': 0, 'wrong_Fdef': 0, 'wrong_boundary_timing': 0, 'not_same_component': 5419, 'recognizer_geometry_failure': 44021, 'hub_touch_failure': 0, 'exact_collision': 0, 'other_explicit_reason': 0}`

`wrong_Ndef` is intentionally zero: Ndef is not a Target-A condition.  It remains in the fixed vocabulary to make this distinction auditable.

## Differential

The v2/v3 comparison is descriptive only because the two profiles traverse different samples.  The first O-only divergent literal state and seen-state P/O distributions are in the JSON ledger.
