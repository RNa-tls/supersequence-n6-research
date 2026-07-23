# F=1, H=0, N=2 defect-charge lemma

Status:

- **Proved:** the local truth table, nonnegativity after the blocked-w2 lemma,
  the F=1 word filter, and zero-charge factorisation between positive-charge
  events.
- **Not proved:** that every N=2 completion has exactly two unit defects.

## Correction to the requested normal form

The local row J = abandonment w3 -> existing E-orbit has Delta N=2.
It is not removed by the blocked-w2 lemma.  Therefore the ledger gives

    N=2 = 1+1  or  N=2,

where the second alternative is one charge-two J event.  A two-unit-defect
theorem requires an additional geometric proof that J is impossible.

## Truth table

~~~json
{
  "identity": "Delta N = 1_{w>=3} + 1_{abandonment} - 1_{new E-orbit}",
  "not_proved": {
    "exactly_two_unit_defects": "The J row, abandonment w3 -> existing orbit, has DeltaN=2. It is not excluded by the current ledger or blocked-w2 lemma.",
    "single_charge_two_alternative": [
      "J_abandon_w3_existing_charge2"
    ]
  },
  "proved": {
    "F1_impossible_words": [
      "A2A2",
      "A2A3",
      "A3A2",
      "A3A3"
    ],
    "negative_row_excluded": "Only blocked w2 -> new orbit has negative charge, and the blocked-w2 lemma excludes it.",
    "reason_for_impossible_words": "Each A2/A3 is an abandonment; F=1 permits exactly one abandonment.",
    "unit_charge_words": [
      "RR",
      "RA2",
      "A2R",
      "RA3",
      "A3R"
    ]
  },
  "rows": [
    {
      "abandonment": false,
      "delta_N": 0,
      "geometry": "not excluded by current flow bookkeeping",
      "kind": "Z2_blocked_w2_existing",
      "new_E_orbit": false,
      "weight": 2
    },
    {
      "abandonment": false,
      "delta_N": -1,
      "geometry": "excluded by proved blocked-w2 lemma",
      "kind": "forbidden_blocked_w2_new",
      "new_E_orbit": true,
      "weight": 2
    },
    {
      "abandonment": true,
      "delta_N": 1,
      "geometry": "not excluded by current flow bookkeeping",
      "kind": "A2_abandon_w2_existing",
      "new_E_orbit": false,
      "weight": 2
    },
    {
      "abandonment": true,
      "delta_N": 0,
      "geometry": "not excluded by current flow bookkeeping",
      "kind": "Z2_abandon_w2_new",
      "new_E_orbit": true,
      "weight": 2
    },
    {
      "abandonment": false,
      "delta_N": 1,
      "geometry": "not excluded by current flow bookkeeping",
      "kind": "R_blocked_w3_existing",
      "new_E_orbit": false,
      "weight": 3
    },
    {
      "abandonment": false,
      "delta_N": 0,
      "geometry": "not excluded by current flow bookkeeping",
      "kind": "Z3_blocked_w3_new",
      "new_E_orbit": true,
      "weight": 3
    },
    {
      "abandonment": true,
      "delta_N": 2,
      "geometry": "not excluded by current flow bookkeeping",
      "kind": "J_abandon_w3_existing_charge2",
      "new_E_orbit": false,
      "weight": 3
    },
    {
      "abandonment": true,
      "delta_N": 1,
      "geometry": "not excluded by current flow bookkeeping",
      "kind": "A3_abandon_w3_new",
      "new_E_orbit": true,
      "weight": 3
    }
  ],
  "schema": "f1-n2-local-defect-truth-table-v1"
}
~~~

If the charge is split into two unit events, every other joint has zero
charge, so the path has form Z0; d1; Z1; d2; Z2.  The current bookkeeping
does not force a positive length for Z1; adjacent unit defects are not
algebraically excluded.  Component and fragment relations require exact
mask information and are not promoted from observations to theorems.
