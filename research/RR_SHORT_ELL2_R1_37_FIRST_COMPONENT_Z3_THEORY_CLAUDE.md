# First component-changing Z3 (FZ1): a formal attack from the fixed-table side

## 0. Verification status

**No "Round-57" branch, commit, or file exists.** `git fetch --all
--prune`, `git remote show origin`, and a repository-wide search for
"round57"/"FZ1"/"dangerous" all return nothing beyond the branches
already independently verified in prior rounds. **Every specific
figure attributed to Round-57 (196 dangerous transitions, 88
direct-Z3, 108 next-Z2, 176 preceding triples, R3=174, R4=22, R5=0, the
depth-4 region's 1,075 states / 991 edges) is asserted in the prompt
only and is not used as fact anywhere below.**

This does not block most of this document's work. Tasks 1, 3, 4, 5, 7,
8, and 9 are formal/mathematical derivations attackable directly from
this project's own already-verified engine semantics and fixed global
tables (`HEX_POSITION`, `ORBIT_PHASE` in
`legacy_research/work/superperm_partial_f1.py`) — independent of
whether Round-57's specific counts are real. Task 2 (classify 22 named
R4 entries) and the count-dependent parts of task 6 **cannot be
performed** without the actual data naming which 22 states these are;
those sections state precisely what is missing rather than fabricating
an analysis of nonexistent entries.

**A new, load-bearing computed result is produced in section 3**: a
direct, non-search table lookup (identical in method to the one used
successfully last round) that **concretely refutes** the strongest
possible form of a cut theorem, by exhibiting real candidate
component-growth pathways — while leaving the actual reachability of
any of them exactly as open as before.

## 1. Minimal necessary-condition system for FZ1

**Exact definition used throughout**: let `C_R1` denote the incidence-
forest component containing the vertex `(q, R1_target_orbit)` at a
given moment. A Z3 edge (opens fresh orbit `q'`, target hexagon `h`) is
an **FZ1 witness** if, at the moment just before it fires, `h` is
already a member of `C_R1`'s registered hexagon set, and no earlier
event in the same continuation already merged `C_R1` with anything.

Grounded directly in the exact mechanics already established in this
session (`extend()`, `advance_decoration`, `joint_kind`,
`incidence_components` — all previously read from source and
independently re-confirmed by code across three prior rounds):

### A. Orbit/phase conditions
- **A1 — target orbit must be fresh** (`om[q']==0` before the move):
  **already proved necessary** — this is `Z3`'s own defining condition
  in `joint_kind`; without it the move is `R`, not `Z3`, by
  construction.
- **A2 — the specific phase reached must correspond to a target
  hexagon already in `C_R1`**: **already proved necessary** — this is
  the direct consequence of how `orbit_masks` bits are set
  (`om[q] |= 1<<phase`, keyed by *target* orbit/phase only, established
  four rounds ago) and how `incidence_components` unions vertices from
  those bits.
- **A3 — the source orbit is irrelevant to whether the edge is
  component-changing**: **already proved necessary** (in the sense of
  "already proved to hold," i.e. this is a proved fact, not merely an
  assumption) — the incidence bit is keyed by target only, confirmed
  from `extend()`'s source four rounds ago; a common misreading (that
  source-orbit membership matters) is explicitly ruled out.

### B. Incidence-forest conditions
- **B1 — the edge must not already exist**: **redundant given A1** —
  since `q'` is fresh, no `(q', h)` edge has ever been added before,
  so this is automatic.
- **B2 — `h`'s vertex must be *already present* in the forest before
  the move** (i.e. some earlier joint already touched `h`, from
  whichever orbit): **already proved necessary** — if `h` were
  unregistered, the new edge could not connect to any pre-existing
  component at all, `C_R1` or otherwise.

### C. Component-partition conditions
- **C1 — `h`'s pre-existing component must equal `C_R1` specifically**
  (not merely *some* component): **already proved necessary** — this
  is the literal definition of "component-changing for `C_R1`," not a
  separate assumption.
- **C2 — `C_R1` and `h`'s component must have been distinct
  immediately before the move**: **redundant given C1** as stated (if
  `h`'s component already *is* `C_R1`, "changing `C_R1`" would need a
  different reading — this document uses C1 to mean `h ∈
  Hexagons(C_R1)` directly, making C2 automatically satisfied by
  construction of "first").

### D. Registration conditions
- **D1 — the literal permutation window at `h` reached by this move
  must not already be visited** (`hex_masks` collision check in
  `extend()`, distinct from the coarser `orbit_masks`/hexagon-level
  incidence bookkeeping): **already proved necessary** — this is the
  ordinary `NR6` legality check every move must pass regardless of any
  component question; confirmed from `extend()`'s source.
- **D2 — the move must be *forced* (non-abandoning)**, since `F` is
  already at its `TARGET_F=1` cap for these roots (established four
  rounds ago): **already proved necessary** — any abandoning `Z3`
  candidate is pruned by `F_exceeded` before the component question is
  ever reached, confirmed from `evaluate_edge`'s source.

### E. Resource-counter conditions
- **E1 — `hub_touch_count` must remain `<=2` after the move**:
  **already proved necessary** as a *general* legality gate (applies to
  every move, not specific to FZ1) — but note precisely: `hub_touch_
  count` only increments when the target *hexagon equals `hub_id`
  exactly* (established two rounds ago), so this condition is *usually
  irrelevant* to an FZ1 witness specifically unless `h == hub_id`.
  **Plausible but unproved** whether it can ever bind for an actual
  FZ1 witness — depends on which specific `h` is involved.
- **E2 — the `R`-budget is not directly implicated**: **already proved
  necessary** as a non-condition — `Z3` never touches `r_count`
  (confirmed from `evaluate_edge`'s source, four rounds ago); FZ1 has
  no resource interaction with the `R`-budget at all.

### F. Provenance/history conditions
- **F1 — no earlier move in the same continuation already merged
  `C_R1` with anything**: **already proved necessary** by the
  definition of "first."
- **F2 — the specific continuation reaching this point must itself be
  legal** (every prior move passed `F`/`H`/collision/`hub_touch`
  checks): **already proved necessary**, tautologically — an illegal
  prefix cannot produce a real witness.

**Minimal prerequisite system for FZ1** (removing the redundant items
B1, C2): **A1, A2, B2, C1, D1, D2, F1** — seven genuinely independent,
already-proved-necessary conditions; E1 is conditionally relevant only
when `h == hub_id`; E2 and A3 are proved *non*-conditions worth stating
explicitly since they rule out two plausible-sounding but false
complications.

## 2. The 22 R4 entries — cannot be analyzed, exact reason stated

**This task cannot be completed.** No file anywhere in this session's
reach names which 22 states constitute "R4," what their individual
records contain, or what "R3"/"R4"/"R5" mean operationally beyond the
prompt's own gloss ("R5 exact bridge = 0"). Fabricating a
classification of 22 specific, named mathematical objects that cannot
be inspected would be indistinguishable from making them up.

**What would be needed to do this properly**, stated precisely rather
than left vague: for each of the 22 claimed R4 states, (a) its exact
decorated state (or a state hash resolvable against an already-
verified checkpoint), (b) the specific incidence-forest snapshot at
that state, (c) which of the section 1 conditions (A1-F2) it satisfies
and which it fails, and (d) its literal continuation history back to
`R1`. Given that, the requested partition ("do the 22 collapse into
fewer obstruction types") would be a direct, mechanical classification
by which condition(s) from section 1 each entry fails — exactly the
kind of task this analyst's role is suited to, once real data exists.
**No such partition is offered here**, and none should be inferred from
this document's silence on the specific 22.

## 3. Cut / separator theorem — a concrete counter-computation, not a proof of impossibility

**Modeling** `C_R1` and `C_H` as requested: vertices `(q,orbit)` /
`(h,hexagon)`, edges = registered `orbit_masks` bits, exactly as
`incidence_components` already computes.

**Direct table computation** (not a search — a deterministic query
over `ORBIT_PHASE`/`HEX_POSITION`, the same fixed global tables used
successfully two rounds ago):

`C_R1` at `R1` admission contains exactly orbit 91's own hexagon set,
already established two rounds ago: `{40, 82, 90, 91, 92}`. Querying
which of the *other* 143 orbits has a phase-hexagon set intersecting
this set — i.e., exactly the set of orbits a legal `Z3` could open to
produce an FZ1 witness, per section 1's A2/C1 — gives **20 orbits**:

```
36, 40, 41, 42, 72, 74, 78, 82, 83, 90, 92, 93, 95, 96, 98, 102, 120, 126, 128, 129
```

**This alone already answers the "must all admissible Z3 attachment
sites be saturated" question in the negative, combinatorially**: these
20 orbits are, by table lookup, legal FZ1 *candidates* in principle —
`C_R1`'s boundary in the fixed orbit-adjacency structure is not empty.
Whether any of them is *actually reachable* (fresh, and reached via a
forced, collision-free move) from any real continuation is a
state-history question this table cannot answer alone — but the
`no legal Z3 edge incident to C_R1` lemma shape the task asks for
**cannot be stated for `C_R1` in general**, because a counterexample to
"the boundary is empty" already exists at the table level.

**A further, more striking finding**: of these 20 candidate orbits,
**5** independently also touch hub's hexagon set `{0,1,4,6,8,9,18,24,
96}` directly:

| candidate orbit | shares with orbit 91 (FZ1 entry hexagon) | its full hexagon set | overlaps hub at |
|---|---|---|---|
| 96 | `{90}` | `{90, 96, 97, 100, 114}` | `{96}` |
| 120 | `{90}` | `{0, 33, 64, 90, 96}` | `{0, 96}` |
| 126 | `{40, 91}` | `{6, 40, 57, 91, 98}` | `{6}` |
| 128 | `{82}` | `{8, 42, 63, 82, 99}` | `{8}` |
| 129 | `{92}` | `{9, 24, 65, 92, 102}` | `{9, 24}` |

**This exhibits, at the fixed-table level, five concrete two-step
candidate pathways** (FZ1 into one of these five orbits, followed by a
*second*, later event from within that same now-`C_R1`-attached orbit
touching its own hub-overlapping hexagon) that — *if* both steps prove
legally reachable from an actual continuation, which this table cannot
determine — would constitute exactly the pre-`R2` bridge this entire
multi-round investigation has been testing for. **This is reported as
an existence result about the fixed combinatorial structure, not a
claim that either step is reachable in practice.**

**On the requested lemma shape**: "Before R2, every legal Z3 edge
incident to `C_R1` has endpoint in ___, therefore `C_R1` cannot grow"
**cannot be asserted** — the premise is false at the table level (20
nonempty candidate endpoints exist). The correctly-scoped, still-open
question is not "can `C_R1` grow at all" (table-level: yes, in
principle) but "does any continuation from the actual root state reach
one of these 20 orbits while it is still fresh, under the forced-move/
collision/hub-touch constraints" — a genuinely dynamic question,
unresolved here.

**Context check, not requested but directly relevant**: orbit 91's
hexagon-adjacency degree (number of other orbits sharing a hexagon) is
exactly **20**, and — computed directly — **every one of the 144
orbits in the system has exactly degree 20**, including hub's own
orbits `{0, 9}`. The orbit-adjacency structure (in this specific,
hexagon-sharing sense) is uniformly 20-regular. Orbit 91 is not
unusually isolated or unusually well-connected; the 20-candidate count
is the *generic* value for any orbit in this system, not a special
weakness or strength of this particular branch.

## 4. Component-boundary invariant candidates

| candidate | value at R1 admission | effect of Z2 | effect of non-component-changing Z3 | required for FZ1 | monotone? | counterexample |
|---|---|---|---|---|---|---|
| unregistered attachment hexagons adjacent to `C_R1` (of the fixed 20-orbit boundary, how many target hexagons remain unregistered) | 20 orbits' worth of shared hexagons, all initially unregistered (only orbit 91 itself is registered) | may register a *new* hexagon within orbit 91 itself (if that phase is touched), shrinking this count by at most the overlap with the 20 boundary orbits | opens an unrelated fresh orbit, registering its own hexagons — could *incidentally* register one of the 20 boundary hexagons without itself being an FZ1 witness (if the specific hexagon touched isn't the shared one) or *could* itself be the FZ1 witness | must reach exactly 0 available options for `C_R1` to be permanently blocked, or must be nonzero and reached for FZ1 to fire | **not established either way** — not checked against real data this round | none available (no per-step trace exists this round) |
| incidence-boundary size of `C_R1` (count of distinct components adjacent via a single missing edge) | at least 20 (one component per candidate orbit not yet opened, though several already-opened *other* orbits along the shared spine could also be adjacent — not recomputed here for the full 22-state frontier) | unaffected unless it registers a boundary hexagon | can only ever *decrease* this quantity or leave it unchanged (registering fresh territory can only close off options, never open new fixed-table candidates, since the table itself is fixed) | — | **plausibly non-increasing**, but not proved — flagged as the most promising monotone candidate, not asserted | not checked |
| accessible-orbit boundary (orbits reachable via a single legal Z3 from the current state, restricted to the 20-orbit candidate list) | depends on the live legal-successor set at each frontier state (state-dependent, not a fixed-table quantity) | irrelevant (Z2 doesn't open new orbits) | shrinks the "fresh" subset of the 20 by exactly one per non-boundary-hexagon-touching event, if it happens to *use up* a boundary orbit for an unrelated hexagon | must be nonzero | **not established** | not checked |
| distance of `C_R1` to `C_H` in the component adjacency graph | at admission: undefined/infinite in the strict graph-distance sense until the first crossing edge exists; in the *orbit*-adjacency sense (ignoring registration), the two 5-hexagon component-orbits are computed above to require at least 2 hops via specific orbits (e.g. orbit 96) | no effect (doesn't touch new orbits) | can reduce this distance by 1 (if it happens to open one of the 5 two-step orbits, even without landing on the FZ1-triggering hexagon specifically) | reaching orbit-adjacency-distance 0 (a direct edge) or the confirmed minimum distance 2 (via one of the 5 orbits in the table above) | **not monotone in general** — opening an *irrelevant* fresh orbit (one of the 124 orbits outside the 20-candidate set) leaves this distance unchanged, so it does not strictly decrease on every step | **counterexample exists at the table level**: any Z3 targeting one of the 124 non-candidate orbits changes nothing about this distance, so a sequence of such moves is a direct counterexample to strict monotonicity |

**A single counterexample is sufficient to reject monotonicity, per the
task's own instruction — applied above to the orbit-adjacency-distance
candidate.** The "incidence-boundary size" candidate is the most
promising surviving proposal (plausibly non-increasing, since the
table of possible crossing points is fixed and only shrinks as options
are used up or the branch progresses), but this document does **not**
assert it as proved monotone — no actual per-step trace from the
Round-57 (or any other) exploration was available to test it against.

## 5. Bounded witness length for FZ1

**Distinguishing the three bounds precisely, per the task's own
caution.**

**Eventual termination bound**: already established (four rounds ago)
— `(720 - visited)` strictly decreases by exactly 6 on every literal
move (a proved fact, re-confirmed from `RotationRun`/`extend`
semantics), giving an absolute, walk-independent finite bound on any
branch's total length. This bounds *everything*, including FZ1, but
gives no information about *when* (or whether) FZ1 specifically occurs
within that bound.

**Bound on first component change specifically**: a genuine, tighter
argument is available and is stated here (not previously derived in
this session): since only `Z3` and `Z2abandon`-excluded `Z2` moves can
add incidence edges, and a `Z3` opens one *fresh* orbit per firing,
**an FZ1 witness — if the branch produces one at all — must occur
within the first `144` `Z3` events of the continuation** (a firm upper
bound, since there are only 144 orbits total and each fresh-orbit
opening is a distinct, non-repeatable event by definition of `Z3`).
This is a real, if extremely loose, bound — tightenable in principle
using the already-established `F<=1` forced-move constraint (which
limits how many `Z3`s can even fire before collision saturation
closes off further weight-3 options), but not tightened further here.

**Bound on first bridge (not just first component change)**: strictly
weaker information is available — a bridge additionally requires the
*second* leg (from `C_R1`'s newly-merged orbit onward to `C_H`, per
section 3's two-step table), which is not bounded by the same
144-orbit argument alone, since it requires a *specific* one of the 5
identified orbits (or some other, unidentified multi-hop path) to be
opened *and then revisited* at the right phase. **No bound on first
bridge specifically is derived here** beyond the (very loose) global
termination bound.

**The task's own caution is directly applicable**: the finite-state
pigeonhole argument above is a genuine bound on FZ1's *timing if it
occurs*, but says nothing about *whether* it occurs — repeated states
(none exist on any replayed path, per two rounds ago's `exact_
decorated_recurrences: []` finding) would need to imply safe
continuation equivalence to strengthen this into an existence/non-
existence result, and no such equivalence has been established.

## 6. The R3/R4 gap

**What could separate R3 from R4 in principle** (methodology only,
since the specific 174/22 partition cannot be inspected): given
section 1's seven-condition system (A1, A2, B2, C1, D1, D2, F1), a
natural, principled reading is that "R3" denotes states failing at
least one of the *structural* conditions (A1/A2/B2/C1 — the state
genuinely cannot reach a shared hexagon at all from its current
position) while "R4" denotes states satisfying the structural
conditions but failing a *dynamic/legality* one (D1 collision, D2
force-timing, or F1 already-merged-elsewhere) — i.e., R4 would be
"structurally adjacent to a crossing, blocked only by a move-legality
detail," which matches the task's own framing ("currently the
structurally closest known cases"). **This is a plausible reading, not
a confirmed one**, offered because it is the natural fit to this
document's own condition system, not because it was checked against
real R4 records.

**Ranking candidate additional coordinates by expected proof value**
(not compression, per the task's instruction):

1. **Exact incidence edge set** — highest expected proof value: this
   is the literal, complete state of the forest at that node; it
   directly and completely determines every one of conditions A1-F1
   without approximation. Nothing else on the list adds information
   this doesn't already contain.
2. **Registered orbit history** — very high value, largely redundant
   with (1) but computationally cheaper to compare across many states
   (a set of orbit IDs vs. a full edge list); would immediately reveal
   whether any R4 case has already opened one of the 20 boundary
   orbits (this document's section 3 table) without yet landing on the
   shared hexagon.
3. **Local degree vector around `C_R1`** — high value specifically for
   testing the section 4 "incidence-boundary size" candidate; directly
   operationalizes the one invariant this document flags as most
   promising.
4. **Source hex predecessor** — moderate value: relevant to whether a
   *forced* (D2) move is even available toward one of the 20 candidate
   orbits from the current position, but does not by itself resolve
   any of A1-F1.
5. **Last 2-4 macro kinds** — moderate value: useful for a quick
   "was the F budget just consumed by an abandonment elsewhere"
   sanity check, but strictly less informative than (1) or (2) for
   this specific question.
6. **Component canonical labeling** — lower value for *this* question
   specifically (it aids cross-state comparison/deduplication, which
   was useful for the frontier-classification work two-three rounds
   ago, but does not itself reveal which of A1-F1 is failing).
7. **Exact R1 provenance** — lowest value for distinguishing R3 from
   R4 specifically, since (per section 3) the R1-target orbit and its
   boundary structure is *fixed* for the whole branch (orbit 91,
   always) — this coordinate is constant across all candidates within
   one branch and therefore carries zero within-branch discriminating
   power, though it would matter for cross-branch comparison.

## 7. Theorem ladder, graded honestly

- **L0 — direct Z2 obstruction only.** **Proved, this session, two
  rounds ago**: orbit 91's complete phase-hexagon set `{40,82,90,91,
  92}` is disjoint from hub's `{0,1,4,6,8,9,18,24,96}`; therefore no
  `Z2` fired from within `C_R1` at admission can ever directly touch a
  hub hexagon. **Status: proved.**
- **L1 — no component-changing Z3 in the verified depth-4 region.**
  **Cannot be asserted** — no depth-4 region data exists in this
  session's reach. If Round-57's claimed figures are real, this would
  be an empirical, bounded observation only (not a proof), exactly as
  every zero-occurrence finding is graded throughout this project.
- **L2 — no first component-changing Z3 satisfying obstruction family
  X.** **Cannot be asserted** — no obstruction-family classification
  exists (task 2 is blocked, section 2). What *can* be said: section 3
  shows the naive "zero candidate orbits" obstruction is **false** (20
  candidates exist at the table level), so any L2-level claim would
  need to identify a *different*, non-vacuous obstruction family — not
  attempted here.
- **L3 — every possible first component-changing Z3 would require an
  impossible incidence/registration configuration.** **Refuted at the
  level this document can check**: section 3 exhibits 20 *possible*
  (table-level, not yet shown unreachable) configurations. L3 would
  require showing each of the 20 is dynamically unreachable from the
  actual root — not attempted, and not obviously true given no
  contradiction was found in the fixed tables.
- **L4 — `short_ell2_r1_37` cannot change `C_R1` before `R2`.**
  **Not provable from anything in this document** — indeed section 3's
  table evidence points the other way (nonempty candidate set),
  though this is not itself proof that a change *does* occur, only
  that the strongest form of "cannot" is not available from table
  data alone.
- **L5 — `short_ell2_r1_37` cannot produce a pre-`R2` bridge.**
  **Not provable**, and section 3's 5-orbit two-step table is a
  standing candidate counterexample-in-waiting to exactly this claim,
  pending a dynamic reachability check neither this document nor any
  data available this round can perform.

**What is missing at each level, summarized**: L0 is closed. L1-L2
need real depth-region/obstruction-family data (task 2/6's missing
inputs). L3-L5 need a dynamic reachability argument over the 20 (and
especially the 5 two-step) candidate orbits identified in section 3 —
this is now a **precisely bounded**, not open-ended, further question.

## 8. Route to a theorem if Codex's search finds nothing

Ranked by plausibility, assuming Codex reports millions of exact
states, zero FZ1, with some branches exhausted and some still capped:

1. **Complete exact closure** (most plausible route to an actual
   theorem, least likely to be achieved in practice): if every branch
   reaches genuine empty-frontier exhaustion (not merely a raised cap)
   with zero FZ1 anywhere, that is an exact certificate — but, per
   this session's own repeated caution, only for the *specific*
   branches that actually close, not for `short_ell2_r1_37` as a whole
   unless *all* of them close, and not for the family beyond it.
2. **Backward closure of all FZ1 prerequisite states** (second most
   plausible, and arguably higher intrinsic value than raw forward
   closure): using this document's section 1 seven-condition system,
   enumerate every state satisfying A1/A2/B2/C1 (i.e., every state from
   which an FZ1 witness is *structurally* available, per section 3's
   20-orbit table) and show, for the finite set of such states
   reachable at all, that D1/D2/F1 always fails. This is smaller and
   more targeted than complete forward closure, since section 3 has
   already reduced the target set to a bounded 20 (or 5, for the
   two-step case) orbit list.
3. **Exact cut-state enumeration**: a formalization of section 4's
   "incidence-boundary size" candidate — if it can be shown genuinely
   monotone non-increasing (not yet established here), enumerating its
   possible values would give a finite state-count bound tighter than
   raw exhaustion.
4. **Finite transition-system quotient with proved continuation
   equivalence**: the most powerful in principle, least plausible to
   achieve soon — this session has repeatedly found that the
   *available* quotients (resource profile, component geometry,
   successor signature) are explicitly *not* proved continuation
   equivalences (two rounds ago), so this route requires new
   theoretical work, not just more computation.
5. **SAT/UNSAT certificate**: lowest plausibility of the five as a
   near-term route — would require translating the exact engine
   semantics into a satisfiability instance, a substantial undertaking
   with no precedent in this project's own methodology so far.

## 9. Route to interpret an FZ1 witness, if Codex finds one

**Strict replay checklist**, to be applied the moment any FZ1 witness
is reported, before any broader claim is made:

1. **Independently replay the exact literal path** from the immutable
   `v5`/root anchor through the witness, exactly as done for every
   prior claimed result this session — confirm the state hash,
   decoration, and incidence-forest snapshot match at every step.
2. **Confirm the witness genuinely satisfies section 1's A1-F1**
   directly against the replayed state (not against a summary) —
   verify the target orbit was fresh, the target hexagon was already
   in `C_R1`, and no earlier merge occurred.
3. **Test whether the newly-merged orbit can reach `C_H`** — check
   directly (table lookup, as in section 3) whether the witness's
   specific target orbit is one of the 5 two-step candidates
   identified here, or requires a further, unidentified hop.
4. **Test whether a later `Z2` becomes possible from within the new
   orbit that lands on a `C_H` hexagon** — this is the second leg of
   the two-step pathway; must be checked for actual legality (D1
   collision, D2 force-timing, E1 hub-touch budget) from the specific
   post-witness state, not assumed from the fixed table alone.
5. **Test whether the eventual `R2` source remains admissible** — even
   a successful merge does not guarantee the walk's position at the
   moment `R2` fires is still inside the merged component; this must
   be checked against the literal continuation, not inferred.
6. **Test whether Target A becomes possible** — `same_component`
   passing is necessary but not sufficient for
   `target_a_recognizer`'s `is_target_a`; `F_def==1`, `H==0`, and
   `hub_touch_count<=2` must all still hold at the `R2` moment,
   checked directly.
7. **Determine scope of refutation precisely**: a witness refutes, at
   minimum, this document's "no component-changing Z3" observation for
   this one state — it does *not* automatically refute the broader
   top-8 or 439-child bridge conjecture unless the same mechanism is
   shown to generalize, and does not by itself establish Target A
   unless step 6 also passes. State exactly which of L1-L5 (section 7)
   the witness resolves and which remain open, rather than a blanket
   "the conjecture is refuted."

## What this document does not do

- Does not verify any Round-57 figure — no branch or file exists to
  check them against.
- Does not classify the 22 claimed R4 entries — the data does not
  exist in this session's reach; task 2 is explicitly left undone
  with the exact missing inputs stated.
- Does not claim branch-wide impossibility at any level beyond L0,
  which was already proved two rounds ago, not newly established here.
- Does claim, as new content: the 20-orbit FZ1-candidate table and the
  5-orbit two-step bridge-candidate table (section 3) are genuine,
  verifiable, non-search computations over already-existing global
  constants — offered as the concrete, bounded target for whatever
  dynamic reachability work comes next.
- No search run, no Codex artifact modified.

CLAUDE_FIRST_COMPONENT_Z3_THEORY_READY
