# Round 50 - corrected cross-root comparison

## Scope

This compares only the v5 admission and equal-cap pilot prefixes for
`short_ell1`–`short_ell4`.  It does not deepen `short_ell0`, and a capped
branch is not an exclusion.

## Dominant observed R2-failure mechanisms

- `short_ell1`: recognizer_geometry_failure=59504, not_same_component=5256
- `short_ell2`: recognizer_geometry_failure=60074, not_same_component=5238
- `short_ell3`: recognizer_geometry_failure=59769, not_same_component=4335
- `short_ell4`: recognizer_geometry_failure=69674, not_same_component=6718, TARGET_A_HIT=3

## Cross-root descriptors

```json
{
  "R1_child_counts": {
    "short_ell1": 99,
    "short_ell2": 111,
    "short_ell3": 107,
    "short_ell4": 122
  },
  "known18_absorption_rate": {
    "short_ell1": 0,
    "short_ell2": 0,
    "short_ell3": 0,
    "short_ell4": 3
  },
  "literal_Target_A_frequency": {
    "short_ell1": 0,
    "short_ell2": 0,
    "short_ell3": 0,
    "short_ell4": 3
  },
  "new_boundary_classes": 0,
  "preparation_spine_presence": {
    "short_ell1": false,
    "short_ell2": false,
    "short_ell3": false,
    "short_ell4": false
  }
}
```

The displayed frequencies are descriptive, not a theorem.  All R2
source-sensitive checks use the tagged literal joint source; canonical known-18
comparison uses only proved left-`S_6` symmetry.  Any future continuation must
resume the saved v5 branch-local checkpoint, not infer closure from this
pilot.
