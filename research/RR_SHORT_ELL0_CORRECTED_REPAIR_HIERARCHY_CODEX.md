# Round 48 — corrected `short_ell0` repair hierarchy

## Result

**Finite replay verification completed for the fixed fair prefix.** The
corrected hierarchy uses the literal source of R2 (`edge.run.state`) rather
than macro entry. The four R1 branches were replayed in the same deterministic
order with equal 25,000-expansion caps and no completion-only prune.

The cap means the four branches remain incomplete as searches. The following
is only a classification of the exact 100,000-expansion prefix.

## Conservation ledger

```text
46,128 repaired R2 paths
  -> 38,405 literal same-component failures
  -> 1 literal Target-A hit
  -> 1 exact decorated boundary state
  -> 1 canonical boundary class
  -> 1 known-18-equivalent class
  -> 0 genuinely new classes
  -> helper-free Target-B DFS: EXHAUSTED_NO_PATH
  -> 0 unresolved classes in this corrected prefix
```

The surviving witness comes from `short_ell0_r1_1`. Its canonical class is
`0df3f68a0cc9a15d70ab0efd79b57bb5f970098457bf4821f400e113593f1d25` and
matches known-18 state `short_ell0_33d70b4249b7` under the proved global
left-`S_6` alphabet action. The comparison is literal state normalisation,
not a match of resource coordinates.

## Helper-free Target B check

The exact Target-B macro DFS for the known class is independent of
`true_phase_walk_capacity`. It reached an empty frontier after 3,214 nodes:

| Field | Value |
|---|---:|
| Verdict | `EXHAUSTED_NO_PATH` |
| Truncated | false |
| Maximum macro depth | 40 |
| Maximum visited permutations | 271 |
| Leaf states | 585 |
| Surviving rotation lengths | `{5}` |
| `F_exceeded` prunes | 48,331 |
| `N_exceeded_monotone` prunes | 91 |
| `round32_B_plus_R` prunes | 5,869 |

The independent verifier reproduces these values from the canonical state and
checks that neither the analysis nor the verifier calls the suspect general
phase-capacity helper.

## Outputs

* `outputs/rr_short_ell0_corrected_repair_hierarchy.json`
* `outputs/rr_short_ell0_corrected_target_a_classes.json`
* `outputs/rr_short_ell0_corrected_known18_comparison.json`
* `outputs/rr_short_ell0_corrected_target_b_ledger.json`
* `outputs/rr_short_ell0_corrected_r2_source_verified.json`

## What is and is not closed

The sole literal Target-A class in this bounded prefix maps to an already
known Target-B-closed boundary. No *new* Target-A or Target-B class appears
in the prefix. Since each R1 branch stopped at a positive cap with a nonempty
frontier, this is not a complete short-root search result.
