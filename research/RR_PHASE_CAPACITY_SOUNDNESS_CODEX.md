# Round 38 — soundness boundary of `true_phase_walk_capacity`

## Reproduced counterexample

`src/audit_rr_phase_capacity_callsites.py` independently replays
`long_found_142`.  At the stored Target-A boundary

```text
root boundary path:
  rot^5;w2:10, rot^5;w2:10, rot^5;w2:10, rot^0;w3:120
old true_phase_walk_capacity: 2
```

the exact engine accepts the three successive macro joints

```text
rot^0;w3:120
rot^3;w2:10
rot^4;w2:10
```

The final landing is in hexagon 21 with mask `47` (`0b101111`): five of its
six positions have already been visited and one legal landing position
remains.  Thus “2” is not an upper bound on arbitrary legal future macro
edges.  The machine-readable replay, including each exact state, is recorded
in `outputs/rr_round38_claim_provenance.json`.

This does **not** automatically contradict a theorem explicitly restricted
to a full-hexagon segment model.  But the generic wording “true capacity” is
unsafe without that missing precondition.

## Call-site audit

| Historical result | status | audit finding |
|---|---|---|
| Rounds 30–32 Target-B results | `NOT_AFFECTED` | helper did not yet exist; no direct call |
| Round 33 phase-walk refinement theorem | `RETRACTION_REQUIRED` | generic capacity statement is refuted; its own numerical pass removed zero survivors |
| Round 34 static successor capacity profiles | `INCOMPLETE_AUDIT` | code imports the helper-derived table; full-segment preconditions need a proof or rerun |
| Round 34 flow-first Target-B result | `INCOMPLETE_AUDIT` | code reads the same table; audit does not assume it was merely ordering |
| Round 35 Target-A exact search | `NOT_AFFECTED` | literal transition search has no helper call |
| Round 37 1,398 coarse exclusions | `RETAINED_BY_INDEPENDENT_PROOF` | all fail the coarse bound before phase refinement matters |
| Round 37 root envelope | `RETAINED_BY_INDEPENDENT_PROOF` | uses `M`, `Ndef`, and the four-run bound, never the helper |

This is a soundness correction to historical phase-capacity use, not a
refutation of the independently checked Round-37 coarse/envelope result.
