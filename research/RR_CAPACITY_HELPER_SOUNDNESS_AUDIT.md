# Capacity-helper soundness audit and firewall

Round 38, Part A. Source `src/audit_rr_capacity_helpers.py` →
`outputs/rr_capacity_callsite_audit.json`.

## 1. The root cause, stated once

Every capacity refinement in this codebase counts a port as "usable" only
if its **hexagon** is entirely unvisited:

```
c(q)                      ports of q whose hexagon has mask 0
true_phase_walk_capacity  the same, restricted to a legal {+1,+2} phase walk
```

That precondition is exactly right for one question and exactly wrong for
another:

| question | what a port needs | helper correct? |
|---|---|---|
| **full-segment** — "how many hexagons can this segment COMPLETE?" | the whole hexagon free, because at Φ=0 the engine forces ℓ=5 and an ℓ=5 run visits all six permutations of the hexagon | **yes** |
| **single-landing** — "how many ports can this segment STAND ON?" (how many times `P` increments) | only the one target permutation free | **no — undercounts** |

## 2. The exact counterexample (§A.3) — and a correction to Round 37

Root `long_found_142` (prefix index 142, abandonment ℓ=4), at
`P=10, O=8, Ndef=1`, **Φ=5** — so ℓ=5 is *not* forced and the helper's
precondition does not hold.

Port occupancy of orbit `q0=1` from entry phase `ph0=1`:

| offset | phase | hexagon | hexagon popcount | already a pass-start |
|---|---|---|---|---|
| 0 | 1 | 72 | 1 | yes (we stand here) |
| 1 | 2 | 12 | 0 | no |
| 2 | 3 | 2 | 0 | no |
| 3 | 4 | **0** | **5** | no |
| 4 | 0 | 1 | 6 | yes |

**Helper predicts 3 ports. The engine achieves 4.** The engine literally
walks `rot^5;w2:10` three times, landing on phases 2, 3, and 4 — the last
of these into hexagon 0, which already has 5 of its 6 slots visited. The
landing succeeds because the single remaining free slot *is* the target
permutation. (The next `rot^5` run from there is then illegal, exactly as
expected — the hexagon cannot be completed, only landed in.)

The helper rejects offset 3 because hexagon 0 is not entirely unvisited.
That rejection is **correct for the full-segment question** and **wrong for
the port-count question**.

### Correction to Round 37

Round 37 recorded this counterexample as *"predicts 2, engine achieves 3."*
The correct figures are **predicts 3, engine achieves 4**. The *direction*
of the Round 37 finding — that the helper undercounts and is therefore
unsound as a port-count bound — is confirmed. Only the two numbers were
wrong, and no Round 37 result depends on them: the Round 37 envelope
rejected the helper outright and never used it. Grade: **corrected claim**.

## 3. Helper taxonomy (§A.4)

| helper | class | freshness required | precondition |
|---|---|---|---|
| `c(q)` port capacity | **SOUND_FOR_FULL_SEGMENT** | yes | Φ = 0 (ℓ=5 forced) |
| `true_phase_walk_capacity` | **SOUND_FOR_FULL_SEGMENT** | yes | Φ = 0 (ℓ=5 forced) |
| coarse segment bound | **SOUND_FOR_SINGLE_LANDING** | no | none — segment *count* and ≤5 ports/segment only |
| `capacity_slack` / `orbit_capacity_bound` | **SOUND_FOR_SINGLE_LANDING** | no | none — uses `popcount(orbit_masks[q0])`, i.e. **port** occupancy, not hexagon occupancy |
| root envelope (Round 37) | **SOUND_FOR_SINGLE_LANDING** | no | none — conservation law + exact `Ndef` cost + group-theoretic max preserving run |

No helper is classified `UNSOUND` or `UNKNOWN`: each of the five has an
explicit precondition under which it is an exact theorem. The two
freshness-dependent ones are unsound only *outside* their stated
precondition, which is what the firewall now enforces.

20 call sites were enumerated by AST parse across `src/*.py`.

## 4. The runtime firewall (§A.5)

`assert_full_segment_context(state, helper_name)` raises
`CapacityPreconditionError` when a `SOUND_FOR_FULL_SEGMENT` helper is
invoked at a state with Φ ≠ 0. `guarded_true_phase_walk_capacity` wraps the
historical computation behind it.

Verified live, both directions:

* called at `long_found_142` (Φ=5) → **correctly raised**;
* called at a known Φ=0 Target B boundary → **correctly allowed**, value 2.

A full-segment-only helper therefore cannot be reached from a root-envelope
or single-landing context without an explicit, loud failure.

## 5. Historical elimination re-verification (§A.6)

All **18** currently known Target A boundaries were replayed (12 short-family
via `rr_preparation_words.json`, 6 long via the Round 27 long-prefix
witnesses). For each, Φ was recomputed and both a freshness-**dependent**
and a freshness-**independent** bound were evaluated.

**Precondition check: Φ = 0 at all 18 of 18.** Every historical use of a
freshness-dependent refinement was therefore inside its valid domain.

Of the 18, **9 carry the recorded verdict `CAPACITY_IMPOSSIBLE`**. Each was
re-proved from scratch:

| provenance | ℓ | `P_core` | Φ | status |
|---|---|---|---|---|
| short_family | 0 | 4 | 0 | **RETAINED** — independent replacement proof succeeds |
| short_family | 4 | 4 | 0 | **RETAINED** — independent replacement proof succeeds |
| short_family | 4 | 6 | 0 | **RETAINED** — independent replacement proof succeeds |
| long_found_4 | 4 | 7 | 0 | **RETAINED** — independent replacement proof succeeds |
| long_found_9 | 4 | 7 | 0 | **RETAINED** — independent replacement proof succeeds |
| long_found_44 | 4 | 10 | 0 | **RETAINED** — independent replacement proof succeeds |
| long_found_74 | 4 | 10 | 0 | **RETAINED** — independent replacement proof succeeds |
| long_found_142 | 4 | 10 | 0 | **RETAINED** — independent replacement proof succeeds |
| long_found_180 | 4 | 10 | 0 | **RETAINED** — independent replacement proof succeeds |

**Retained: 9. Retracted: 0.**

Critically, every one of the 9 is retained by the **freshness-INDEPENDENT
coarse segment bound** — `5·(O_cap+R_cap)+4 < B+1` — which consults no
hexagon occupancy at all. So none is retained merely because "the final
answer happened to match": each has a replacement proof that does not touch
the questioned helper. The freshness-dependent bound is recorded alongside
for comparison but is not load-bearing for any retained result.

## 6. Where the questioned helper actually mattered

* **Round 33's independent re-derivation** of two Round 32 removals — at
  Φ=0 boundaries, precondition holds, sound.
* **Round 37's `bound_3`** in the 1,398-boundary ledger — applied at
  boundaries with Φ ∈ {0, −3, −4, −8}, i.e. **mostly outside** the
  precondition. This is a genuine scope violation, but it is **not
  load-bearing**: all 1,398 boundaries fail at `bound_1` (the coarse,
  freshness-independent bound), so `bound_3` never decided anything. It is
  now flagged in the ledger's own documentation rather than silently left.

## 7. Verdict

No soundness retraction is required. The questioned helper was never used
outside its precondition in any way that decided a result, every historical
elimination has an independent freshness-free replacement proof, and the
firewall now makes future misuse impossible without an exception.
