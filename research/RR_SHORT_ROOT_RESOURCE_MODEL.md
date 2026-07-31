# Symbolic resource model and the search-worthiness decision

Round 38, Parts I and J. Source
`src/verify_rr_short_root_resource_model.py` →
`outputs/rr_short_root_resource_results.json`.

## 1. The model (§I)

A tiny symbolic **resource relaxation** — not a path model. Variables, all
non-negative integers:

| variable | meaning |
|---|---|
| `c_init` | ports of the segment already in progress |
| `f_j`, j∈1..5 | number of fresh-opening segments of capacity `j` |
| `r_j`, j∈1..4 | number of re-entry segments of capacity `j` (≤4, Round 32) |
| `n_E2` | total `E²` preserving steps used anywhere |

Constraints:

```
(1) c_init + Σ j·f_j + Σ j·r_j == TARGET_P − P0 + 1
(2) Σ f_j <= O_cap                              (= TARGET_O − O0)
(3) Σ r_j + n_E2 <= R_cap                       (= n_limit − Ndef0)
(4) 1 <= c_init <= init_cap_max                 (entry-sensitive, occupancy-independent)
```

**Solver.** No certified ILP solver exists in this environment, so the model
is decided by **exhaustive enumeration over an explicitly bounded integer
lattice** — independently checkable, with the number of lattice points
examined reported per root. No truncation occurs: every quantity has a small
explicit range.

## 2. Interpretation, fixed before the result

| outcome | meaning |
|---|---|
| **infeasible** | the root is Q2-impossible — a real certificate |
| **feasible** | **UNRESOLVED**, and *never* a continuation witness |

Feasibility here carries no path, no geometry, no hexagon disjointness, and
no ordering. It says only that the resource *counts* can be balanced. This
is recorded in the output JSON on every row
(`feasibility_is_not_a_witness`).

## 3. Result

| root | ports required | `O_cap` | `R_cap` | `init_cap_max` | feasible | lattice points | classification |
|---|---|---|---|---|---|---|---|
| `short_ell0` | 120 | 23 | 3 | 5 | **yes** | 120 | STRUCTURAL_SURVIVOR |
| `short_ell1` | 120 | 23 | 3 | 5 | **yes** | 120 | STRUCTURAL_SURVIVOR |
| `short_ell2` | 120 | 23 | 3 | 5 | **yes** | 120 | STRUCTURAL_SURVIVOR |
| `short_ell3` | 120 | 23 | 3 | 5 | **yes** | 120 | STRUCTURAL_SURVIVOR |
| `short_ell4` | 120 | 23 | 3 | 5 | **yes** | 120 | STRUCTURAL_SURVIVOR |

The model is comfortably feasible — 120 required ports against a ceiling of
`5 + 5·23 + 4·3 = 132`. **No root is closed by the resource relaxation.**

## 4. Part J: search-worthiness classification

| classification | count | roots |
|---|---|---|
| `ROOT_ENVELOPE_IMPOSSIBLE` | 0 | — |
| `SYMBOLIC_RESOURCE_IMPOSSIBLE` | 0 | — |
| **`STRUCTURAL_SURVIVOR`** | **5** | `short_ell0..4` |
| `MODEL_INCOMPLETE` | 0 | — |

**All five short roots are genuine STRUCTURAL_SURVIVORs**: they have no
impossibility certificate of any kind. By the round's own rule, they are
therefore the roots — and the only roots — eligible for resumed
continuation search.

This *reverses the recommendation wording* of Round 37, which said "no root
is resume-worthy." That phrasing was not supported: it rested on a
frontier-growth observation, which is a cost argument, not a mathematical
certificate. Round 38 separates the two:

* **Mathematically**: all five are search-worthy. Nothing rules them out.
* **Heuristically** (explicitly labelled, never used as a proof or a prune):
  at the Round 36 budget each expanded 71k–80k nodes in 90 s with the queue
  still growing to 120k–134k. Extrapolating, exhausting even one is far
  outside a single session's budget, so a naive resumption is not the
  *efficient* next step — a new occupancy-independent bound, or a proved
  quotient, would be. This is a statement about cost, and it is **not**
  claimed to close the roots or to make search pointless.

The distinction matters because the earlier phrasing risked reading as
"these roots are done." They are not.

## 5. What would actually close them

The margin decomposition (`RR_SHORT_ROOT_ENVELOPE.md` §2) shows the +14 is
`−8 + 8 + 2 + 7 + 5`. Parts E/F/G established that the preserving (+8),
re-entry (+2), and fresh-opening terms are all **already tight** under
occupancy-independent reasoning. The terminal slack (+7) is a constant of
the target values. So no further occupancy-independent tightening is
available, and closing these roots requires either:

1. an occupancy-**dependent** argument carrying a proved, explicitly stated
   precondition (Part A's firewall permits this — it forbids only *unstated*
   preconditions); or
2. a genuinely new invariant, independent of the `M = P − 5·O` accounting; or
3. exhaustive Q1 search with substantially more compute than a session
   affords.
