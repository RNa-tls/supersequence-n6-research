# The 7 incomplete-Q1 roots: full audit and continuation strategy

Round 37, Goal D, sections 8 (known-18 separation), 11-15. Source
`src/audit_rr_incomplete_roots.py` → `outputs/rr_incomplete_root_audit.json`.

## 1. The 7, fixed

Round 36 left 7 of 33 roots at `INCOMPLETE_TIMEOUT` with zero hits: 5
short-family roots (`short_ell0..4`, `r_count=0`, needing **two** more R
events) and 2 long-prefix roots (`long_q1_140`, `long_q1_178`, `r_count=1`,
needing **one** more).

## 2. The envelope theorem already resolves 2 of the 7 (§10 cross-reference)

`RR_ROOT_LEVEL_CAPACITY_ENVELOPES.md`'s root-level certificate, computed
with **no further search**, gives:

| root | `k` | envelope | certified Q2-impossible |
|---|---|---|---|
| `long_q1_140` | 1 | **-13** | **YES** |
| `long_q1_178` | 1 | **-13** | **YES** |
| `short_ell0..4` | 2 | **+14** | no (inconclusive) |

**So only 5 of the original 7 remain genuinely open**, and only for Q2;
Q1 (any Target A boundary at all) remains open for all 7, since the
envelope theorem is Q2-only machinery and says nothing about Q1 by
construction.

## 3. Full audit (§12) — never interpreted as absence

| root | `P₀` | `O₀` | `Ndef₀` | expanded | queued | checkpoint |
|---|---|---|---|---|---|---|
| `short_ell0` | 2 | 2 | 0 | 70,999 | 120,103 | 147MB |
| `short_ell1` | 2 | 2 | 0 | 80,000 | 134,378 | 165MB |
| `short_ell2` | 2 | 2 | 0 | 80,000 | 134,275 | 165MB |
| `short_ell3` | 2 | 2 | 0 | 80,000 | 133,889 | 164MB |
| `short_ell4` | 2 | 2 | 0 | 80,000 | 133,668 | 164MB |
| `long_q1_140` | 10 | 8 | 1 | 64,401 | 92,671 | 116MB |
| `long_q1_178` | 10 | 8 | 1 | 67,663 | 97,220 | 122MB |

Every row's `interpreted_as_absence` field is explicitly `false`. A
timeout with zero hits is a **budget** fact, not an existence claim — this
is the exact discipline Round 36's status vocabulary was built to enforce,
and this audit re-affirms it rather than assuming it.

## 4. Symmetry/quotient attempt on the 5 short-family roots (§13)

Three levels checked, on the 5 roots' literal states:

| level | classes |
|---|---|
| raw state hash | **5** (no collision) |
| left-S6 canonical hash | **5** (no collision) |
| resource signature `(P,F,S,H,O,D,Ndef)` | **1** (collapses completely) |

**The resource signature collapses all 5 to one class** — expected, since
every abandonment root shares identical counters (`P=2, O=2, Ndef=0, ...`)
regardless of which orbit/hexagon it literally sits in. This is useful for
the capacity-envelope computation (already reflected in the identical
`envelope=+14` for all 5) but is **not a state-level quotient**: the raw
and canonical hashes stay fully distinct, meaning finding (or failing to
find) a Target A boundary from one abandonment root says nothing directly
about another — their *geometric* reachability differs even though their
*resource* accounting is identical.

**No quotient with proved completeness was found.** Per the brief's own
instruction ("완전성을 증명하지 못하면 사용하지 마라"), none is used to
merge roots or to prune the search. This is reported as the honest outcome
of the attempt, not a gap silently left unaddressed.

## 5. Distance bounds, proved vs. heuristic (§14)

| root | proved lower bound (macro edges) | heuristic estimate |
|---|---|---|
| `short_ell0..4` | **2** (needs 2 more R events, each ≥1 edge) | not computed, not used |
| `long_q1_140`, `long_q1_178` | **1** | not computed, not used |

The proved lower bound is **손증명**: an RR word needs exactly `k` more R
events, and each is itself one macro edge, so the extension is at least `k`
edges long — nothing more is claimed. Sibling roots' *observed* Target A
depths (9-12 macro edges at several `long_q1_*` roots, from Round 36) are
explicitly **not** used here: they are search results specific to those
roots' own geometry, and generalizing them to a different root's minimum
distance would be exactly the unvalidated-heuristic-as-prune error Part C
forbids.

## 6. Continuation decisions (§15)

| root | decision | reason |
|---|---|---|
| `long_q1_140` | **STRUCTURAL_ANALYSIS_FIRST** | Q2 already certified impossible by the envelope theorem; further search only ever refines Q1, and structural analysis already answered the question this root was being searched for |
| `long_q1_178` | **STRUCTURAL_ANALYSIS_FIRST** | same |
| `short_ell0..4` (all 5) | **FRONTIER_TOO_LARGE** | queued frontier (120,000-134,000) exceeds expanded nodes (71,000-80,000) by >30% at the budget cutoff; naive resumption at the same rate would not converge within a comparable additional budget |

**No root is classified `RESUME_WORTHWHILE`.** Simple timeout extension is
not recommended for any of the 7: the 2 that matter for Q2 are already
answered without more search, and the 5 that remain open need either a
proved quotient (not found) or a fundamentally different pruning strategy
before resumption is worth the compute — exactly the priority the brief
sets ("단순 timeout 연장보다 구조 분석을 우선하라").

## 7. Separation from the known-18 corpus (§8/§11)

* The known-18 corpus **has** capacity survivors historically at the
  boundary level in the sense that Rounds 30-32 removed 11 of 18 by
  capacity and Round 34 exhaustively searched the remaining 7 for Target
  B — those 7 are a **different, disjoint** object from this round's 1,398
  or the 5-root audit here.
* The 22-root corpus (source of the 1,398) has **0** capacity-theorem
  survivors, established in Round 36 and re-confirmed here.
* Overlap check: none of the 1,398 boundaries' raw or canonical hashes
  matches any of the 18 known ones (Round 36's `is_new_vs_known18_raw`:
  1,392 of 1,398 new, the other 6 being the known long-FOUND roots'
  re-discovered witnesses — themselves already part of the 18, not new
  members of either corpus).

**Known-18 Target B status is unchanged by this round.** Nothing here
re-opens or re-searches it.
