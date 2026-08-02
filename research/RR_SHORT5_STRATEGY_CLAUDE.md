# Strategy assessment: where the RR/short-root branch actually stands

Planning/assessment document — no search run, no new data generated.
Synthesizes everything already established and independently verified in
this session (the R2-literal-source correction, `b09f1d5`) with this
repository's own longer-standing record (`STATUS.md`, the 33-root
envelope theorem, the known-18 corpus).

## 1. Current proof-state reassessment

### Proved hand theorems (stand independent of any specific search)

- **Conservation law** `M = P − 5O`: `dM = +1` for `Z2`/`R`, `−4` for
  `Z3` (Round 37, re-verified against a BFS sample, unaffected by this
  round's correction — it never used R2-source semantics).
- **Root-level envelope theorem**: closes 28 of 33 roots for the Q2
  question with no enumeration (Round 37).
- **Incidence-forest monotonicity**: `orbit_masks` bits are OR-only, so
  the forest's vertex/edge sets only grow and its component partition
  only coarsens — proven directly from `extend()`, root-independent.
- **`CH2` requires R1-strictly-before-completer by construction**; a
  pre-R1 completer is therefore not `CH2` (two rounds ago, from
  `Decoration.branch`'s own source).
- **Repair-theory lemmas A, C, D, E** (one round ago): `Z2` can merge
  components; any legal repair changes the future R2 source orbit; a
  geometry-preserving repair need not precede the completer; a
  post-completer repair does not necessarily cause `F_exceeded`.
- **`Z3`-re-entry nonexistence**: a weight-3 edge into an already-open
  orbit is definitionally `R`, never `Z3`.
- **The `Phi` sawtooth identity** (pre-dates this thread,
  `SHORTFALL_BUDGET_THEOREM.md`): flat across `rot^5` runs, drops by
  `(ell−5)` at a joint.
- **Full-segment `EEEE` theorem** (Round 32), conditional on `R_cap=1`;
  **existing-orbit entry capacity `≤4`** (Round 32).
- **Left-`S6` canonicalization** (`exact.canonicalize`) is the one
  proven symmetry on boundary states.
- **R2 source is `edge.run.state`, not macro-entry state** — now
  independently verified this session (not merely stated): confirmed by
  reading the diff, and by *running* the regression fixture test myself
  in an isolated worktree.

### Exact exhaustive certificates

- **28 of 33 roots, Q2-impossible** (envelope theorem, no enumeration).
- **22 long-excursion roots, Q2-exhausted** at their respective slack
  levels (Round 35 exact search).
- **The known-18 corpus's Target-B status**: closed via a combination of
  capacity-theorem arguments (9 of 18 confirmed capacity-impossible,
  Round 38's rerun) and earlier rounds' direct Target-B search — the
  *exact* split across all 18 is not re-verified this round and should
  be treated as an open bookkeeping question, not re-derived here.
- **The single corrected `short_ell0` Target-A hit → Target-B**: an exact
  exhaustive certificate *for that one boundary specifically* —
  `EXHAUSTED_NO_PATH` at 3,214 nodes, explicitly `truncated: false`,
  `Phi=0`/`R_cap=1` preconditions satisfied and checked, no unsound
  helper used. This is genuinely exact, not bounded — for this one
  boundary.

### Corrected bounded observations

- **Two distinct `short_ell0` corpora exist and must not be conflated**:
  (a) the **old single-LIFO 100,250-expansion run** (three rounds ago),
  which used `evaluate_edge`/`target_a_recognizer` — *never buggy*, per
  this round's diff — and reported 44,021 `r2_wrong_source_orbit` +
  5,419 `not_same_component` + 0 hits out of 49,440 R2 candidates,
  entirely from one R1 event's subtree (a LIFO-scheduling artifact,
  already diagnosed); and (b) the **new four-branch fair-repair search**
  (this round), equal 25,000-node budget per R1 child, using the
  *now-corrected* `hierarchy_for_r2`, reporting 46,128 repaired R2 paths
  → 38,405 same-component failures → 1 literal hit. These are different
  searches over overlapping but not identical state spaces — the fair
  search's equal-budget design directly addresses the LIFO-bias finding
  from two rounds ago, which is itself a real methodological improvement
  worth crediting.
- All four fair-repair branches remain `INCOMPLETE` as searches (capped,
  nonempty frontiers) — including branch `short_ell0_r1_1`, whose
  `FOUND_TARGET_A` classification records a real hit but does not imply
  its own frontier is exhausted.

### Invalidated historical observations

- The **pre-correction `hierarchy_for_r2` output**
  (`outputs/rr_short_ell0_repair_hierarchy.json` v1, and the "38,406
  exact hits" figure it implied) — now explicitly marked
  `INVALID_R2_SOURCE_SEMANTICS`. 38,405 of those 38,406 were false
  positives.
- Nothing else — this session's own prior three structural documents
  (R2-source-orbit, productive-R1, repair-theory) remain unaffected, per
  last round's audit, now reconfirmed rather than merely asserted.

### Open branches

- **`short_ell1`–`short_ell4`: entirely untouched by the corrected
  recognizer.** The correction's own scope statement is explicit —
  *"this correction concerns only the already-fixed fair `short_ell0`
  prefix."* This is the largest, most immediate open branch.
- `short_ell0` beyond the capped 4×25,000 prefix.
- The 5 long-excursion-family roots that timed out during Round 36's
  original Q1 coverage pass (unrelated to this correction, still open
  from much earlier in this thread).
- Whether the RR/NR6 framework this entire branch operates inside is
  even the right lens for `L_6 ≥ 872` — `STATUS.md`'s own standing
  caveat, untouched by anything in this session: *"whether the specific
  `NR6` assumption... is even true is... a separate open question — not
  addressed here."*

### `short_ell0`'s exact current position, stated precisely

`short_ell0` has exactly **one** verified, closed Target-A→Target-B
chain, discovered inside a specific, capped, fair, corrected-recognizer
4×25,000-node prefix. That chain collapses under left-`S6` equivalence
into an **already-known, already-closed** class from the pre-existing
known-18 corpus. **This resolves zero new Target-B survivors.** It does
**not** close `short_ell0` as a root — three of its four R1-branch
subtrees remain `INCOMPLETE` with nonempty frontiers, and the one
`FOUND_TARGET_A` branch is not shown to be exhausted either. What it
*does* establish, solidly: the corrected engine and methodology (literal
R2 source, fair per-branch budget, helper-free Target-B DFS,
known-18 comparison via literal replay) all work correctly end-to-end,
on real data, independently reproduced this session.

## 2. Progress re-estimation — ranges, not points

**`CLAUDE_OBSERVATION` — the governing caveat, stated first because it
bounds every number below:** this entire RR/Target-A/Target-B
investigation operates inside the NR6-assumed framework `STATUS.md`
itself flags as unverified. Every percentage below is progress *within
that conditional framework*, not progress toward a rigorous, unconditional
`L_6 ≥ 872` proof — which remains, honestly, close to **0%** advanced by
any RR-branch result to date, because no result in this framework has
yet been connected back to the unconditional claim, and the framework's
own foundational assumption is unverified.

| scope | rough completion range | basis |
|---|---:|---|
| Unconditional `L_6 ≥ 872` proof | **~0%** | no RR-branch result has been connected to the unconditional claim; `NR6` itself is unverified |
| RR-branch, Q2 question, all 33 roots | **~85%** (28/33 roots) | envelope theorem, exact, no enumeration needed — the solid part of this whole thread |
| RR-branch, Q1 question (any Target-A boundary, all roots) | **~20-40%** | most long-excursion roots covered; short-root family (5 of 33 roots) essentially just starting under the corrected recognizer |
| known-18 corpus, Target-B closure | **~50-100%** | 9/18 confirmed via capacity theorem; the remainder's exact closure basis was not re-verified this session — reported as a range, not re-derived |
| `short_ell0` specifically (state-space fraction actually explored) | **~1-10%**, likely toward the low end | four branches, 25,000 expansions each, against a state space whose branching factor and depth (confirmed depth >100, generated-edge counts in the hundreds of thousands per 25k-expansion branch) suggest a much larger reachable set; no principled total-size estimate exists to sharpen this further |
| `short_ell1`–`short_ell4` | **0%** | corrected recognizer never run on them |

## 3. Next-strategy evaluation: deepen `short_ell0` (A) vs. shallow-pass the other four (B)

| criterion | A (deepen `short_ell0`) | B (shallow-pass `short_ell1`–`4`) |
|---|---|---|
| novel-structure discovery potential | **lower** — the same literal-orbit mechanics (rotation-offset non-registration, hub-phase coincidences) are likely to keep recurring, not reveal qualitatively new phenomena | **higher** — four fresh literal permutation configurations are the only way to tell whether `short_ell0`'s observed patterns (preparation spine, hub-phase-0 coincidence) are general RR-alphabet facts or root-specific coincidences |
| duplicate-computation risk | moderate — not literally duplicate (new territory beyond the cap), but conceptually "more of an already-well-characterized root" | **near zero** — genuinely unexplored roots |
| global-generalization potential | low on its own — one data point cannot confirm a pattern is general | **high** — the only way to test generalization is to look at more than one root |
| exhaustion-certificate potential | **low near-term** — `short_ell0`'s branching already produced hundreds of thousands of generated edges per 25k-expansion branch; full exhaustion looks distant | **unknown but nonzero** — one of the four untried roots could, in principle, have a smaller reachable space; this is unverified but at least *possible*, whereas A forecloses that possibility for the other four roots entirely |
| hand-theorem-candidate generation | **diminishing returns expected** — the repair-theory lemma set (A-E) already extracted the load-bearing mechanics from `short_ell0`'s own structure | **higher** — cross-root confirmation is precisely what would upgrade an observed `short_ell0` pattern into a genuine, provable, root-independent theorem |

**`CLAUDE_PROPOSAL`: B is the stronger choice on four of five criteria.**
The one place A has an edge (continuing to push a single, already-
characterized root) is not where this thread's actual leverage is —
`short_ell0`'s state space already looks too large for near-term full
exhaustion regardless of which option is chosen, so the marginal value
of "more of the same root" is lower than "does this generalize at all."
Recommendation: **B first, A conditionally afterward** — informed by
what B's shallow pass reveals about which root (if any) looks most
tractable to deepen.

## 4. Which structures generalize, and which are `short_ell0`-specific

| structure | generalizes? | reasoning |
|---|---|---|
| R1 preparation spine (literal orbit sequence `33→64→90→96→hub`, phase sequence `2→3→4→0`) | **root-specific in its literal details** | tied to `short_ell0`'s own starting permutation arithmetic |
| ...but the *qualitative pattern* (a shared `Z2`-preparation spine, R1 firing as alternative stopping points at increasing depth) | **plausibly general, untested** | a natural consequence of the RR alphabet's move-table design, not obviously tied to `ell=0` specifically — worth checking directly against the other four roots |
| Literal R2 source semantics (`edge.run.state`, never macro-entry) | **fully general** | a property of the transition engine itself (`extend()`, `ORBIT_PHASE`), applies identically to every root, every search, past and future |
| Known-18 collapse (this *specific* boundary equals `short_ell0_33d70b4249b7`) | **root-specific fact** | a coincidence of this one boundary's own canonical form |
| ...but the *methodology* (literal replay + left-`S6` canonicalization + known-18 comparison) | **fully general** | already built to be root-agnostic; should be applied unchanged to whatever boundaries the other four roots produce |
| Target-B helper-free closure methodology (avoid `true_phase_walk_capacity`, use `Phi=0`/`R_cap=1`-conditioned theorems, exact DFS) | **methodology general; applicability root/boundary-specific** | must re-check `Phi=0` and `R_cap=1` per boundary every time, exactly as this session's own prior framework document required |
| `CH1`/`PRE_R_COMPLETER_EVENT_ORDER` distinction | **definitions general (engine-level); which events land in which category is root-specific** | depends on each root's own hub/orbit geometry |
| Incidence-forest/component conditions (monotonicity, vertex/edge rules) | **fully general** | proven directly from `extend()`'s `orbit_masks` OR-only update, independent of root |

## 5. Recommended research sequence — next 3-5 rounds

**Round N+1 — fair-recognizer shallow pilot on the four untouched roots.**
- *Goal*: run the corrected engine (post-`b09f1d5`) on `short_ell1`
  through `short_ell4`, same fair-branch design (equal budget per R1
  child, matching `short_ell0`'s 25,000-expansion cap per branch for
  direct comparability).
- *Evidence level required*: exact/deterministic, same rigor as
  `short_ell0`'s corrected run — hash-verified, replay-equivalence
  checked, no unsound helper.
- *Stop condition*: equal budget exhausted per branch, or an early hit
  found and independently verified.
- *On success* (any hits found): immediately apply the already-built
  known-18-comparison and helper-free Target-B DFS methodology (cheap,
  since both are already implemented and this round's work proved them
  correct).
- *On failure* (no hits, as `short_ell0`'s three non-productive branches
  showed): still valuable — records each root's own R2-candidate and
  component structure, the necessary input to Round N+2.

**Round N+2 — cross-root generalization pass (analysis only, no search).**
- *Goal*: compare all five short roots' preparation spines, hub
  coincidences, R1 event distributions, and same-component failure
  patterns from Round N+1's data; attempt to state and hand-prove a
  genuinely root-independent theorem about the RR alphabet's short-root
  structure (a natural next candidate given the repair-theory lemma work
  already completed).
- *Evidence level required*: hand proof, or explicit refutation with a
  counterpattern — the same discipline this thread has held throughout.
- *Stop condition*: either a theorem is proved, or the attempt is
  reported as a negative result (as several already have been) — not
  left ambiguous.
- *On success*: the theorem becomes a reusable structural result for any
  future short-root search, independent of this specific corpus.
- *On failure*: still narrows the search space for later rounds by
  documenting exactly which patterns are root-specific.

**Round N+3 — classify any new hits from Round N+1.**
- *Goal*: for every Target-A boundary Round N+1 found beyond the
  already-known one, run the classification checklist already prepared
  (`RR_SHORT_ELL0_TARGET_B_FRAMEWORK_CLAUDE.md` §6): exact duplicate /
  proved symmetry-equivalent / resource-profile collision only /
  genuinely new class.
- *Evidence level required*: canonical-hash comparison plus, for any
  `GENUINELY_NEW_CLASS`, the three precondition checks (`O_cap≥0`,
  `R_cap≥0`, correct `k`) before any capacity theorem is applied.
- *Stop condition*: every found boundary classified, no boundary left
  "probably fine."
- *On success* (a genuinely new class found): this becomes the priority
  — actual new information, unlike the collapsed `short_ell0` case.
- *On failure* (everything collapses to known-18 again): a real,
  reportable negative result — evidence (not proof) that this
  RR-alphabet region is thin on new Target-A boundaries near the roots.

**Round N+4 (conditional on N+1-3) — deepen whichever root looks most
tractable.**
- *Goal*: only now consider "Option A"-style depth, informed by which
  root's Round N+1 structure suggests the best chance of either
  exhaustion or new discovery — not chosen a priori.
- *Evidence level required*: same exact/deterministic standard, larger
  budget.
- *Stop condition*: a resource budget agreed in advance (this thread has
  already seen single-branch budgets reach 100k+ expansions without
  exhausting a root — set expectations accordingly).
- *On success* (exhaustion or new class): a genuine milestone for the RR
  branch.
- *On failure*: still bounds the state-space-size estimate in §2 more
  precisely for future planning.

**Round N+5 (conditional) — consolidate and re-state scope honestly.**
- *Goal*: whatever N+1-4 produce, update `STATUS.md`-level framing of
  what the RR branch has and has not achieved toward `L_6 ≥ 872`, with
  explicit reiteration that even full closure of all five short roots'
  Target-A/B questions would not by itself prove `L_6 ≥ 872` without
  addressing the `NR6` assumption and the remaining long-excursion Q1
  coverage gaps from earlier in this thread.
- *Evidence level required*: an accurate summary, not a new claim.
- *Stop condition*: n/a — this is a reporting round.
- *On success/failure*: either way, the field is left honestly scoped
  for whoever continues it next.

CLAUDE_SHORT5_STRATEGY_READY
