# Strengthened bounds and the segment-defect theorem for the five short roots

Round 38, Parts E, F, G, H. Source
`src/analyze_rr_short_root_envelope.py` →
`outputs/rr_short_root_defect_bounds.json`.

Every bound below is **occupancy-independent**: none consults hexagon
freshness, so all remain valid for partial hexagons, single landings, full
segments, and existing-orbit re-entries alike — exactly as Part A's
firewall requires.

## 1. Entry-sensitive preserving bound (§E)

The universal bound is "no legal preserving run exceeds 4 steps", from the
no-repeat phase condition (a preserving word's partial sums mod 5 must be
distinct). Part E asks for an **entry-sensitive** strengthening using only:

* the exact no-repeat phase condition — group-theoretic;
* ports already used as pass-starts in the same E-orbit (`orbit_masks`),
  which the engine forbids re-using;
* the remaining R budget, since every `E²` step costs one `N`.

Implemented as `entry_sensitive_preserving_bound(orbit_mask, entry_phase,
r_budget, entry_already_occupied)`. It consults **no hexagon occupancy**.

**Measured result at all five roots: capacity 5, defect 0.** The initial
segment's orbit has exactly one port used (the one the walk stands on), and
with `R_cap = 3` the pure-E word `EEEE` reaches all five phases. So the
entry-sensitive bound **does not improve on the universal bound here** —
reported as a measured non-improvement rather than quietly dropped.

> A bug worth recording: the first implementation treated the entry phase's
> own bit in `orbit_masks` as a blocker, yielding `init_cap = 0` and a
> nonsensical `init_defect = 5` at every root. The walk already stands on
> its entry port, so that bit must be masked out while still counting the
> port. Fixed via the `entry_already_occupied` flag; the corrected value is
> 5.

## 2. Re-entry tax (§F)

Round 32 proved an R-entry into an existing orbit has capacity ≤ 4 (the
orbit already holds a pass-start), i.e. a tax of 1 relative to a fresh
`EEEE` segment. Part F asks for a root-specific tax **greater than 1**.

`worst_case_reentry_tax` computes the *best* capacity the walk could
achieve over every legal (orbit, phase) re-entry choice — which is what a
safe lower bound on lost capacity must use.

**Measured: best re-entry capacity 4, minimum tax 1, at all five roots.**
Witness: orbit 0, entry phase 1, 1 port already used, capacity 4.

**No improvement over Round 32.** The reason is structural: an orbit with a
single used port leaves four free phases, and a pure-E word reaches all
four. Since the walk may open many orbits before its R events, and any of
them will have just one used port at that moment, the minimum tax cannot be
pushed above 1 by any occupancy-independent argument. Reported as a
measured non-improvement.

## 3. Usable fresh openings (§G)

The envelope counts fresh openings by quantity (`O_cap = 23`). Part G asks
for a bound on *usable* openings.

**Measured: an unopened orbit has all five ports free, so a fresh segment
attains the full 5 ports.** Fresh-opening capacity is therefore not reduced
below 5 by any occupancy-independent argument available here. No
improvement.

## 4. The segment-defect theorem (§H)

Define `d(S) = 5 − capacity(S)`, capacity in **ports stood on**. A walk from
a short root to a Target A boundary consists of the initial segment, some
fresh-opening segments, and exactly `k = 2` R re-entry segments. A safe
lower bound on total defect uses each type's smallest possible defect:

```
D_min(root) = d_initial_min + k · (minimum re-entry tax)
            =      0        + 2 ·          1
            =      2
```

Test: `D_min(root) > margin` ⟹ root is Q2-impossible.

| root | `init_cap` | `init_defect` | min re-entry tax | `D_min` | margin | verdict |
|---|---|---|---|---|---|---|
| `short_ell0` | 5 | 0 | 1 | **2** | 14 | UNRESOLVED |
| `short_ell1` | 5 | 0 | 1 | **2** | 14 | UNRESOLVED |
| `short_ell2` | 5 | 0 | 1 | **2** | 14 | UNRESOLVED |
| `short_ell3` | 5 | 0 | 1 | **2** | 14 | UNRESOLVED |
| `short_ell4` | 5 | 0 | 1 | **2** | 14 | UNRESOLVED |

**`2 > 14` is false at every root. Roots closed by the defect theorem: 0 of 5.**

## 5. Honest summary

Parts E, F, and G were each attempted and each produced **no improvement**
over the bounds already in hand. The defect theorem is therefore far from
the margin — `D_min = 2` against a margin of `14`, a gap of 12.

This is a negative result and is recorded as one. The five short roots are
**not** closed, and no bound was stretched, no precondition relaxed, and no
heuristic substituted to make them appear closed. The specific obstacle is
identified precisely: with `Ndef = 0` these roots have the **full** `R_cap`
of 3 and the **full** `O_cap` of 23, so every resource term in the envelope
is at its maximum, and the only structurally exploitable term (preserving
slack, +8) is already tight under any occupancy-independent argument.

Closing them will require either an occupancy-**dependent** argument with a
proved precondition (the firewall permits this — it forbids only *unstated*
preconditions), or a genuinely different invariant.
