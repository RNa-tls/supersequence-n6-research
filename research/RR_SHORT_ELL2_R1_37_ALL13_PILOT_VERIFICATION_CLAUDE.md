# All-13 pilot results: independent verification and structural analysis

Branch `codex/round-r1-37-all13-pilot-results` fetched directly. Every
count below was independently recomputed from the raw JSON, not read
from the markdown summary. Section 5 includes a genuine hand-computed
result (a fixed-table lookup over the already-existing
`HEX_POSITION`/`ORBIT_PHASE` tables, no search, no branching) that goes
beyond verification into new, load-bearing content.

## 1. Remote verification

- `git fetch origin codex/round-r1-37-all13-pilot-results` succeeded.
- `git rev-parse` = `e280d325f59de8aebdcb0b149403ad770cf6ad18` — **exact
  match**.
- Parent = `c394624f046930ec4257228cad4e13aaba70231f` — **exact match**
  to the claimed parent (the plan commit independently noted, but not
  fetched, in the prior round).
- `git log --oneline`: `e280d32 → c394624 → fae8ded → 4792891 → ...` —
  full chain intact back to every previously-verified commit.
- All 5 required files exist as ordinary Git blobs (`git cat-file -t`
  returns `blob` for every one; none is an LFS pointer — checked by
  reading the first 100 bytes of each file for a `git-lfs` marker,
  none found).
- **Blob SHA-256 consistency**: recomputed the SHA-256 of the three
  JSON outputs and the verifier script directly against the values
  recorded inside `rr_short_ell2_r1_37_all13_verified.json`
  (`result_sha256`, `bridge_ledger_sha256`, `verifier_sha256`) —
  **all three matched on raw bytes**, with no CRLF round-trip needed
  this time (unlike several prior rounds' artifacts).
- Every hex string matching a SHA-256-shaped pattern across the three
  JSON files was checked programmatically for exactly 64 hex
  characters — no anomalies (the only 40-character hex strings found
  were ordinary Git commit SHAs, correctly 40 characters for SHA-1).

## 2. Count verification, independently recomputed

All figures below were recomputed by summing the raw per-branch
records in `rr_short_ell2_r1_37_all13_pilot_results.json`, not read
from the markdown table (though the recomputed values are then cross-
checked against it as an independent consistency test):

| quantity | recomputed | claimed | match |
|---|---:|---:|---|
| unresolved input states | 13 | 13 | yes |
| total expansions | 66,096 | 66,096 | yes |
| naturally exhausted | 7 | 7 | yes |
| capped, nonempty frontier | 6 | 6 | yes |
| total remaining frontier | 84 | 84 | yes |
| R2 records | 31,465 | 31,465 | yes |
| B0 | 66,167 | 66,167 | yes |
| B1-B6 | 0 (all six) | 0 | yes |
| component merges | 0 | 0 | yes |
| bridge-template occurrences | 0 | 0 | yes |
| literal Target A | 0 | 0 | yes |
| Target B survivors | 0 | 0 | yes |
| independent verification | `verified: true`, `overall_status: "ALL13_PILOT_PARTIAL"` | true | yes |

**A finer-grained check beyond what was asked**: the markdown's R2
failure breakdown ("immediate `recognizer_geometry_failure` 7건, later
`recognizer_geometry_failure` 28,758건, later `not_same_component`
2,700건") was independently recomputed by summing the nested
`R2_outcomes.immediate`/`R2_outcomes.later` dictionaries across all 13
branches: **7 / 28,758 / 2,700 exactly**, summing to 31,465 — matching
the R2-record total exactly and confirming the markdown's more granular
narrative claim, not just its headline numbers.

## 3. Certificate-scope verdict

**For the 7 exhausted subproblems**: each has `frontier_size == 0` and
`naturally_exhausted == true` in the raw records — genuine empty-
frontier termination, independently confirmed by direct field
inspection, not inferred from the `status` label alone. The verifier's
own per-branch `exact_successor_replay: "PASS"` field (checked for all
13, not just the 7) confirms every stored child was reproduced by an
independent outgoing-edge re-enumeration, per the verifier script's own
logic (`rr.iter_raw_macro_candidates` + `rr.evaluate_edge` — the same
already-established engine machinery used throughout this project).
**Exact certificate unit: subgraph**, exactly as established two rounds
ago for the original 9 locally-exhausted roots — each of these 7 is a
complete-reachable-subgraph exhaustion certificate for its own starting
state, not a state-level fact and not a branch-level (whole
`short_ell2_r1_37`) fact. **No bridge/Target-A path is omitted**: the
verifier's stated scope is "all stored incoming edges plus exact
outgoing-edge replay of every expanded node" — i.e. every one of the
66,096 expanded nodes' complete outgoing candidate set was
independently re-enumerated and compared against the stored accepted-
child set, not merely spot-checked.

**For the 6 capped subproblems**: each has `frontier_size > 0`
(9, 8, 20, 21, 12, 14 for `:236166, :12, :6, :3, :303321, :13`
respectively) and `expanded == 10,000` exactly — confirmed nonempty,
confirmed capped at the declared budget. **These remain `INCOMPLETE`**,
exactly as the pilot's own status vocabulary requires (`status_counts:
{"INCOMPLETE": 6}`). **Explicitly, zero bridge/merge/Target-A
observations in these six branches are bounded evidence only**: each
of the six explored exactly 10,000 further expansions from an already-
deep starting point and found nothing, but their frontiers remain open,
so nothing beyond "not found in this much exploration" can be
concluded for any of them individually — consistent with every
zero-occurrence finding graded this way throughout this session.

## 4. The 7-vs-6 split: structural comparison

Combining this round's outcome data with the already-independently-
verified frontier data (two rounds ago) for the same 13 starting states:

| id | status | orig. successors | orig. depth | P | O | D | M |
|---|---|---:|---:|---:|---:|---:|---:|
| `:303323` | exhausted | 1 | 59 | 61 | 23 | 54 | -54 |
| `:303324` | exhausted | 2 | 59 | 61 | 23 | 54 | -54 |
| `:304858` | exhausted | 1 | 66 | 68 | 28 | 72 | -72 |
| `:304860` | exhausted | 1 | 67 | 69 | 28 | 71 | -71 |
| `:304872` | exhausted | 2 | 74 | 76 | 30 | 74 | -74 |
| `:304973` | exhausted | 1 | 77 | 79 | 32 | 81 | -81 |
| `:305018` | exhausted | 3 | 88 | 90 | 36 | 90 | -90 |
| `:3` | capped | 2 | 47 | 49 | 17 | 36 | -36 |
| `:6` | capped | 2 | 48 | 50 | 17 | 35 | -35 |
| `:12` | capped | 2 | 52 | 54 | 19 | 41 | -41 |
| `:13` | capped | 3 | 52 | 54 | 19 | 41 | -41 |
| `:236166` | capped | 1 | 56 | 58 | 22 | 52 | -52 |
| `:303321` | capped | 3 | 58 | 60 | 23 | 55 | -55 |

**Initial successor count does *not* separate the two groups**:
exhausted states have successor counts `{1,1,1,1,2,2,3}`, capped states
have `{1,2,2,2,3,3}` — both sets span the full 1-3 range, with a
successor-count-1 state landing in *each* group (`:304973` exhausted,
`:236166` capped) and a successor-count-3 state in each group
(`:305018` exhausted, `:303321` capped). Any correlation suggested by
this feature alone in earlier rounds does not hold up under the actual
outcome data.

**Original starting depth *does* separate the two groups cleanly, with
no overlap in this sample**: every exhausted state's original depth is
`>= 59` (range 59-88); every capped state's original depth is `<= 58`
(range 47-58). Since `P`, `O`, `D`, `M` are already established
(two rounds ago) to move monotonically with depth on these replayed
paths, they track the same separation and are not independent
evidence — they are restatements of the same "how far along the shared
spine" signal, not four separate confirmations.

**This is reported as a correlation observed in `n=13`, not promoted
to an invariant**, per the task's explicit instruction. A plausible
(not proved) mechanistic reading: states starting deeper into the
shared spine have less remaining room before the fixed `F<=1`/`NR6`
collision constraints force termination, making faster natural
exhaustion more likely — but this is offered as a candidate
explanation for the observed pattern, not a demonstrated cause.
`resource_profile`/`component_geometry` class hashes were not checked
as independent features beyond `P,O,D,M` themselves, since two rounds
ago's work already established these hashes are computed from exactly
those (plus the already-uniform `F,H,Ndef,Phi`) — no additional
information beyond what the table above already shows.

`R2_record_count` also separates cleanly (exhausted: 0-2,279; capped:
4,511-4,968) but this is very likely a downstream *consequence* of
whether a branch was allowed to run long enough to attempt many `R2`
candidates (i.e., of hitting vs. not hitting the cap), not an
independent structural signal — flagged as such rather than added as a
fifth "separating feature."

## 5. `HEX_POSITION` / `ORBIT_PHASE` assessment — includes a new hand-computed result

**The three pilot output files do not export per-node or per-edge
orbit/hexagon identity** — only aggregate counts (`B0`-`B6` level
tallies, `R2_outcomes` reason tallies). This is genuinely insufficient
to tabulate `HEX_POSITION x ORBIT_PHASE` cell purity across the 66,096
expanded nodes explored during the pilot itself.

**What *is* available, and was computed directly** (a fixed-table
lookup over the already-existing `HEX_POSITION`/`ORBIT_PHASE` tables in
`legacy_research/work/superperm_partial_f1.py` — no search, no
branching, a deterministic query over global constants shared by every
branch in this family):

All 13 starting states share the identical `R1`-target orbit, **91**
(confirmed directly from the already-verified frontier data — this
orbit is fixed for the whole `short_ell2_r1_37` branch, not a
per-state variable). Querying `ORBIT_PHASE` and `HEX_POSITION`
directly for orbit 91's own five phases:

| orbit 91 phase | hexagon touched |
|---:|---:|
| 0 | 91 |
| 1 | 40 |
| 2 | 82 |
| 3 | 92 |
| 4 | 90 |

**Orbit 91's complete phase-linked hexagon set is `{40, 82, 90, 91,
92}`.** The hub component's hexagon set for this branch (independently
confirmed identical across all 13 states from the already-verified
`component_partition` records) is `{0, 1, 4, 6, 8, 9, 18, 24, 96}`.
**These two sets are disjoint.**

**This is a genuine, hand-verified structural fact, not an
observation**: since `Z2` is orbit-preserving (established four rounds
ago) and the only way `Z2` could merge `R1`-target's isolated component
with hub's is by landing on a hexagon already in hub's component while
remaining in the `R1`-target orbit — and orbit 91 *never* touches any
of hub's 9 hexagons at *any* of its 5 phases — **a `Z2`-mediated bridge
is structurally impossible for the entire `short_ell2_r1_37` branch,
for all 13 (and, by the same orbit-91 fact, all original 22) states**.
This closes the `Z2` sub-case of the local bridge conjecture completely
for this branch, by direct computation rather than by search volume.

**The `Z3` case remains open, and is now precisely characterized rather
than left vague.** Extending the same table lookup to *all 144 orbits*
in the system (`ORBIT_COUNT`, the complete global table): **36 orbits**
have a phase-linked hexagon set intersecting hub's 9-hexagon set — 2 of
these are hub's own already-registered orbits (`0`, `9`, expected and
uninteresting since `Z3` can never target an already-open orbit by
definition), leaving **34 other orbits** that *could*, if ever opened
fresh via a legal `Z3` move and landing on the right phase, touch a hub
hexagon:

```
1, 3, 4, 5, 6, 7, 8, 10, 11, 13, 16, 18, 19, 21, 24, 25, 27, 33, 35,
45, 57, 63, 65, 96, 97, 99, 105, 120, 121, 124, 126, 128, 129, 138
```

**This is the smallest finite table that could plausibly support a
full hand-proof**: not a single-orbit check (already done, and
resolved), but a bounded, closed, 34-orbit "watch list" — whether *any*
of these 34 orbits is ever legally opened fresh via `Z3` from within
this branch's actual reachable state space is a state-history-dependent
question the fixed tables alone cannot answer (unlike orbit 91's own
check, which needed no state history at all).

**Exactly what Codex should export next**: for every `Z3` edge
encountered during any future continuation of the 6 capped branches (or
re-derivable from the already-completed 66,096-node exploration if the
raw edge log still exists), record the target orbit ID. If none of the
34 listed orbits ever appears as a `Z3` target across the full
explored space, that is a substantially stronger empirical result than
the current aggregate "bridge_count: 0" (since it would confirm the
*specific* mechanism gap, not just the outcome), and if the 6 capped
branches are fully exhausted without any of the 34 ever appearing, that
would constitute strong (though — per the 13/439 corpus caveat
established throughout this session — still branch-scoped, not
family-wide) evidence toward a genuine hand-proof for this branch as a
whole.

## 6. Recommended next step

Given the verified 7/6 split, the clean (if unexplained) depth
separator, and — most importantly — the new hand-computed result that
half the bridge mechanism (`Z2`) is now *provably* closed for this
entire branch while the other half (`Z3`) has been reduced to a
precise, bounded 34-orbit watch list:

**Recommend D, refined by the new section-5 result, ahead of a plain
equal-effort continuation (A).** The most valuable immediate action is
not "run more expansions" in the abstract but the specific, bounded,
non-search step this document has already substantially advanced: (i)
confirm (by re-deriving from already-computed data if possible, or by
requesting Codex export raw `Z3` target-orbit identities on any future
run) whether any of the 34 orbits ever appears as a legal `Z3` target
anywhere in the already-completed 66,096-node exploration — this is a
data-query against existing computation, not a new search — and (ii)
only if that check is inconclusive from existing data, continue the 6
capped branches specifically instrumented to flag a `Z3` target among
the 34, which is a far more targeted diagnostic than an undirected
deepening pass. Option B (classify the 84 frontier states first) is a
reasonable complement but lower-value than checking the 34-orbit
question directly, since the components/successors of those 84 states
are already governed by the same orbit-91-versus-hub-hexagon
disjointness fact established here. Option C (successor-weighted
continuation) is not supported by section 4's finding that successor
count does not separate the two groups — depth does, and depth is not
a resource knob that can be "weighted." Option E (hybrid) is
effectively what is being recommended: a targeted data check (D) that,
if it doesn't fully resolve the branch, feeds directly into which of
the 6 capped states to prioritize for further bounded search.

## Final response summary

1. **Remote verification**: branch, commit, and parent all confirmed
   exactly; all 5 files present as ordinary blobs, no LFS; all three
   cited SHA-256 values matched on raw bytes with no CRLF conversion
   needed.
2. **Count verification**: every one of the twelve requested figures
   (13/66,096/7/6/84/31,465/66,167/0×6/true) independently recomputed
   and confirmed exact, plus a finer R2-failure-reason breakdown
   (7/28,758/2,700) also confirmed exact.
3. **Certificate-scope verdict**: exhausted subgraphs confirmed
   genuinely empty-frontier (subgraph-level certificate unit, as
   established two rounds ago), verifier scope confirmed exhaustive
   (every expanded node's outgoing edges re-enumerated); capped
   branches confirmed nonempty and `INCOMPLETE`, with zero-occurrence
   findings explicitly graded as bounded evidence only.
4. **7-vs-6 structural comparison**: successor count does not separate
   the groups (counterexamples in both directions); original starting
   depth (and its monotone correlates `P,O,D,M`) separates them
   cleanly in this `n=13` sample — reported as a correlation, not
   promoted to an invariant.
5. **`HEX_POSITION`/`ORBIT_PHASE` assessment**: the pilot's own exports
   are insufficient for a full cell-purity table, but a direct,
   non-search table lookup over the already-existing global tables
   proves the `Z2`-mediated bridge mechanism is structurally
   impossible for this entire branch (orbit 91's phase-hexagon set is
   disjoint from hub's), and reduces the remaining `Z3` question to an
   exact, bounded 34-orbit watch list — the smallest finite table that
   could plausibly support a full hand-proof, with a precise
   specification of what Codex should export next to test it.
6. **Recommended next step**: a targeted, non-search data check against
   the 34-orbit watch list (refining option D), ahead of undirected
   further expansion.

## What this document does not do

- Does not claim the `short_ell2_r1_37` branch, the top-8 family, or
  the 439-child corpus is closed — 6 of 13 (and the branch as a whole)
  remain `INCOMPLETE`.
- Does not claim the `Z3` bridge mechanism is impossible — only that it
  has been reduced to a precise, bounded, 34-orbit question, itself
  still open.
- Does not promote the depth correlation (section 4) to a proved
  invariant — reported as an `n=13` observation with a plausible,
  unproved mechanistic reading offered alongside it.
- No search run: section 5's computation is a deterministic query over
  fixed, pre-existing global tables (`HEX_POSITION`, `ORBIT_PHASE`),
  identical in kind to the non-search table lookups used successfully
  in this analyst's own prior rounds.
- Does not modify any Codex artifact.

CLAUDE_ALL13_PILOT_VERIFIED
