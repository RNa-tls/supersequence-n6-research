# F=1 rotation macro-transition controls

Status: finite transition controls only.  This document does not state an
Area-A nonexistence result.

## Exact compression

A macro edge retains every legal rotation-run length `ell=0,...,ell_max` and
then records one literal nonrotation joint.  It therefore does **not** assume
that a pass must rotate until a collision before taking a deep joint.  Each
literal prefix factors uniquely into these runs and joints; a rotation-only
suffix is tested separately at termination.  Every run is replayed with the
exact `extend` routine, so an intermediate repeated permutation window ends
the run and cannot be skipped.

The rotation component has `(Delta F, Delta S, Delta H)=(0,0,0)` and changes
only its own hexagon mask.  Left value relabelling commutes with the right
rotation, hence canonical child quotienting is applied only after the literal
joint and preserves the legal macro-tail set.

## Finite controls

```json
{
  "schema": "partial-f1-macro-sanity-v1",
  "macro_sha256": "b02d3985d3672c24efdc197777cc25080fc9cb3846545db240ceacd649485049",
  "engine_sha256": "9196dcc17b3081aeb777001a1c5366e787fe15c1dad0614ec760953b785801a8",
  "core_sha256": "18f75735b08fc061765e33cc661a084c8735e433e80ee8035a163b113ee39d60",
  "scope": "finite transition controls only; no Area-A existence conclusion",
  "initial_run_lengths": [
    0,
    1,
    2,
    3,
    4,
    5
  ],
  "initial_maximal_run_ends_by_collision": true,
  "intermediate_rotation_collision_rejected": true,
  "rotation_resource_deltas_are_zero": true,
  "left_S6_macro_legal_tail_equivariance_720": true,
  "canonicalization_preserves_legal_macro_tail_set_720": true,
  "first_joint_control": {
    "literal_macro_first_joint_frontier_equal": true,
    "coordinates_fingerprints_and_representative_literals_equal": true,
    "literal_prunes": {},
    "macro_prunes": {},
    "frontier_size": 24,
    "max_rotation_run_from_initial": 5
  }
}
```

Classification: the facts in this file are literal finite checks or direct
consequences of the exact transition definition.  They are not a whole-slab
enumeration.
