# CH1 / CH2 at the 22 roots: the split does not apply, and the search covers both

Round 35, sections 8, 13, 14. Source `src/search_rr_target_a_exhaustive.py`
→ `outputs/rr_target_a_search_results.json`.

## 1. The classification (§8)

* **CH1** — the hub completer edge C is itself the first R event.
* **CH2** — C is a `Z2` and R1 happened earlier.

Classifying all 22 roots from their prefixes:

    {'CH_none': 22}    hub completer kind: None ×22

**Neither branch applies at the root.** The hub hexagon is incomplete at all
22 (popcount 1–5, never 6), so no edge in any prefix lands as a hub
completer. C must occur inside the extension, which makes the CH1/CH2 label a
property of the extension, not of the root.

This is a real answer, not a classifier failure, and it changes what §8 asks
for. Two searches keyed on a branch that is undetermined at the root would
have to guess the branch and would then be unsound if the guess were wrong.
Instead the Q2 search explores **every** extension of every root, so both
branches are inside its scope by construction. Grade: **scope correction**.

## 2. The searches (§13)

Statuses are `FOUND_TARGET_A` / `EXHAUSTED_NO_TARGET_A` / `INCOMPLETE`, with
`EXHAUSTED_NO_TARGET_A` conditional on `frontier_emptied_naturally`. A node
cap is never a proof condition and a timeout is never exhaustion; both flags
are recorded per root.

**Q2 (capacity-pruned, sound for completability) — no cap, no ceiling:**

| root class | roots | decided by | nodes |
|---|---|---|---|
| slack < 0 at root | 14 | the bound alone, no search | 0 |
| slack = 1 (ell=3, L=8) | 2 | exhaustive search | 25 |
| slack = 2 (ell=1, L=7) | 2 | exhaustive search | 2 |
| slack = 6 (ell=2, L=7) | 2 | exhaustive search | 242, 248 |
| slack = 10 (ell=3, L=7) | 2 | exhaustive search | 10,335, 10,389 |

**22/22 `EXHAUSTED_NO_TARGET_A`; all frontiers natural; 0 boundaries.** The
searches are finite because slack is non-increasing (it falls by `5 − used`
whenever an orbit is abandoned unsaturated), so a root with slack 10 can
waste at most 10 units before the bound closes.

**Q1 (no capacity bound) — 22/22 `INCOMPLETE`**, 13,602–18,766 nodes each
before the budget. Branching ≈ 2.5 with no safe prune strong enough to
terminate. Grade: **bounded incomplete**.

## 3. Section 14: the new-boundary pipeline, implemented and untriggered

`pipeline_for_new_boundary` is wired in and would, for any hit: store the
deterministic witness with its raw and left-S6-canonical hashes, compare
against the 18 known canonical hashes, then apply the capacity theorem and
the phase/R-reuse refinement, and hand the state to the Round 34 flow solver
**only** if it survived both. The Target B search is never restarted from
scratch.

`new_completable_target_a_boundaries: 0`, so the pipeline did not fire. It is
recorded as present-and-untriggered rather than omitted, since the whole point
of §14 is that it exist before it is needed.

## 4. What the Q2 exhaustion does and does not mean

**Does:** for these 22 roots, there is no Target A boundary from which an
Area-A NR6 completion is still arithmetically possible. Combined with Round
34, nothing reachable from these roots can contribute to `L_6 ≥ 872`.

**Does not:** it is not Target A coverage. Q1 is incomplete at all 22, so
Target A boundaries that are themselves capacity-dead may well exist beyond
these roots — Round 30 already exhibited six such boundaries elsewhere. The
distinction is enforced mechanically: the bound that makes Q2 finite is
verified to delete a genuine known Target A boundary, so it can never be used
for Q1.
