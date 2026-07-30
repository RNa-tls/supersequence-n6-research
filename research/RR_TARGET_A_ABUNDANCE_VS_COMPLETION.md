# Why Target A abundance does not give completion viability

Round 37, Goal B, sections 3, 4, 8, 9. Sources
`src/build_rr_1398_boundary_ledger.py` →
`outputs/rr_1398_boundary_capacity_ledger.json`.

## 1. The corpus, fixed exactly (§3)

Every one of the 1,398 boundaries Round 36 found is ledgered with: root id,
canonical and raw boundary hashes, literal word hash (computed over the
**full** literal path from the true initial state, not just the extension —
an early draft hashed only the extension and found spurious word collisions
across different roots that happened to share a label sequence; fixed by
prepending each root's own literal prefix), `ell`, `P_core`
(root/extension-relative, not re-derived by formula — see the caveat
below), `B`, `O_cap`, `R_cap`, `c(q0)` (both the port-availability and
true-phase-walk versions), the coarse/refined bound values, failure
margins, first-failing theorem, terminal signature, and a replay
certificate (independently re-confirmed for all 1,398).

**Word count vs. boundary-state count.** 1,398 rows, **1,398 distinct raw
boundary states**, **1,398 distinct full literal words** — the corpus has
no internal duplication at any of these levels (verified, not assumed).

## 2. Three capacity theorems, and where each corpus member fails (§4)

| theorem | formula | grade |
|---|---|---|
| 1. coarse segment bound | `5·(O_cap+R_cap)+4 ≥ B+1` (Round 30) | exact theorem |
| 2. initial-phase port refinement | `(1+(5-used_ports(q0))) + 5·O_cap + 4·R_cap ≥ B+1` (Round 31/34) | exact theorem |
| 3. true phase-walk refinement | `true_phase_walk_capacity(q0,ph0) + 5·O_cap + 4·R_cap ≥ B+1` (Round 33/35) | exact theorem, **scope-limited** (see `RR_ROOT_LEVEL_CAPACITY_ENVELOPES.md` §5) |

`bound_1 ≥ bound_2 ≥ bound_3` always (checked by assertion on every row).

**Result: all 1,398 boundaries fail at Theorem 1, the coarsest.**

```
first_failing_theorem_histogram: {"coarse_segment_bound": 1398}
```

Not one boundary needed Theorem 2 or 3 to be excluded. This answers Goal 4
directly: there is **one** structural deficit, not several competing
failure mechanisms. The refinements Rounds 31-35 built to squeeze extra
survivors out of a *small* corpus (18 boundaries) add nothing here, because
the deficit at these 22 roots is large enough that the loosest bound
already suffices.

## 3. Why abundance and infeasibility coexist (§8, resource accounting)

The reason is the conservation law
(`RR_ROOT_LEVEL_CAPACITY_ENVELOPES.md` §7): every macro edge either
advances `P` at unit cost with no `O` cost (`Z2`, `R` — worth `+1` toward
the bound) or advances `P` at the cost of opening a fresh orbit (`Z3` —
worth `-4`, since one unit of `O_cap` is worth `5` in the bound formula but
costs a whole orbit). Reaching a Target A boundary is *cheap* — it needs
only `k` (1 or 2) R events, each just one macro edge, with no requirement on
the surrounding `Z2`/`Z3` mix at all. Reaching *completion* needs `O_cap`
and `R_cap` to still cover the full remaining distance to `TARGET_P=121`
divided by up to 5 — a MUCH larger requirement, entirely independent of how
"close" the Target A boundary itself sits.

So the 22 roots are not "close to Target A but far from completion" by
coincidence — they are architecturally set up so that satisfying Target
A's cheap local condition (one more R event, minimal extension) is trivial
long before the resources needed for eventual completion could possibly be
assembled. **Abundance of local boundaries and scarcity of completable ones
are not in tension: the first question is cheap, the second is expensive,
and this corpus sits in exactly the regime where the gap between them is
large.**

## 4. Long/short preparation comparison (§8, historical continuity)

The known long-preparation boundaries (Rounds 27-32, the 6 `P_core ∈
{7,10}` known boundaries) were already shown to fail via fresh-opening
capacity exhaustion — the same "`Z3` is expensive" mechanism. The 1,398 new
boundaries fail for the identical reason: `first_failing_theorem` is
`coarse_segment_bound` for every one of them, and the coarse bound is
*exactly* the fresh-opening/re-entry accounting Round 30 established. No
new invariant beyond preparation length was needed; the deficit is the same
kind found before, just now proved to be universal across this root class
rather than checked on 6 examples.

## 5. Boundary quotient (§9)

| quotient level | classes among 1,398 |
|---|---|
| raw state hash | **1,398** (no collisions) |
| canonical (left-S6) hash | **1,398** (no collisions — no two boundaries are related even by a global relabeling) |
| literal word hash | **1,398** |
| terminal signature `(orbit, phase, O, Ndef)` | **16** |
| capacity signature `(O_cap, R_cap, c(q0)_port)` | **15** |
| root ancestry (`root_id`) | **26** |
| `(root_id, terminal_signature)` | **157** |

**The smallest capacity-relevant quotient is 15 classes** — the
`(O_cap, R_cap, c(q0))` triple, which is exactly the information Theorem 1
consumes. This matches the histogram in §2: 15 distinct capacity profiles,
1 shared failure mode. No coarser *state-level* quotient exists (raw,
canonical, and word-level counts are all 1,398 — this corpus has no
redundancy to exploit at the state level, only at the capacity-signature
level).

## 6. What this does not say

This is Q2 machinery, applied to an already-fixed corpus, as pure
post-processing. No new search was run to produce these numbers. Nothing
here revisits the known 18's Target B status, and nothing here claims
anything about the 5 short-family roots (not part of this corpus — see
`RR_INCOMPLETE_ROOT_AUDIT.md`).
