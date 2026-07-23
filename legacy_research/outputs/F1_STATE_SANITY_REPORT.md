# F=1 exact-state sanity report

Status: **pass**.  This report validates the transition engine,
the left-`S_6` quotient, and bounded-search prerequisites.  It does **not**
claim an enumeration of `(F,D,N)=(1,4,*)`.

## Fixed finite data

- hexagons: 120
- `E`-orbits: 144
- indecomposable tails by weight: `{'1': 1, '2': 1, '3': 3, '4': 13, '5': 71, '6': 461}`
- every literal tail has no intervening permutation window: `True`

## Positive control: standard length 873

```json
{
  "windows": 720,
  "visited": 720,
  "P": 120,
  "F": 0,
  "S": 24,
  "H": 6,
  "O": 24,
  "D": 0,
  "N": 0,
  "matches_expected": true
}
```

## Exact-state controls

```json
{
  "synthetic_F1_prefix": {
    "move": "w2:10",
    "F": 1,
    "P": 2,
    "D": 8,
    "abandonment": true
  },
  "rotation_repeat_collision_rejected": true,
  "D_identity": true,
  "normal_form_round_trip": true,
  "left_S6_legal_tail_equivariance_720": true,
  "sparse_canonical_transport_matches_dense_720": true,
  "mask_layer_counterexample": true,
  "mask_counterexample_scope": "exact-state countermodel; not claimed as a pair of complete walk prefixes"
}
```

`mask_layer_counterexample` is intentionally only a state-level countermodel:
it proves that pass-start masks cannot replace the hexagon membership oracle.
It is not presented as two complete no-repeat walk prefixes.


## Bounded canonical census (diagnostic only)

The recorded depth-limited run had configuration `{"canonical_children": true, "max_depth": 2, "node_limit": 250}`.
It completed its stated depth bound: `True`; it
hit a node limit: `False`.

```json
{
  "depth_counts": {
    "0": 1,
    "1": 89,
    "2": 177
  },
  "accepted": 267,
  "generated": 49365,
  "prunes": {
    "F_exceeded": 48178,
    "N_plus_H_exceeded": 921
  },
  "N_plus_H_accepted": {
    "0": 6,
    "1": 9,
    "2": 39,
    "3": 213
  },
  "fragment_shape_accepted": {
    "fragment=0;current=1": 3,
    "fragment=1;current=1": 264
  },
  "tracemalloc_peak_bytes": 1523424
}
```

This is a depth-two finite validation of the state engine, not an enumeration
of the `F=1,D=4` slab.


Code SHA-256: `9196dcc17b3081aeb777001a1c5366e787fe15c1dad0614ec760953b785801a8`  
Core SHA-256: `18f75735b08fc061765e33cc661a084c8735e433e80ee8035a163b113ee39d60`
