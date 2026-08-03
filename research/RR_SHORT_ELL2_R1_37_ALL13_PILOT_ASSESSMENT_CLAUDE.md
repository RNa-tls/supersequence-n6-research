# Corrected all-13 pilot: conditional assessment

**No new Codex branch was found this round** (`git fetch --all
--prune` and `git remote show origin` show the same seven branches
already known — `codex/round-r1-37-frontier-analysis` is unchanged at
`fae8ded`, the commit independently verified last round). Consistent
with the task's own explicit instruction, every "reported fact" below
is treated as **conditional, not verified**. Sections 1, 2, and 4 do
not depend on the specific unverified figures and are given as direct
methodological/mathematical assessment; section 5 is explicitly scoped
as a logical/schema check only. Grounding throughout uses this
analyst's own **already-independently-verified** data on
`short_ell2_r1_37`'s 22-state frontier from two rounds ago (successor
counts, depths, profile distinctness, hub/Φ/component facts) — that
data is real and confirmed, unlike this round's new claims.

## 1. Is the corrected all-13 pilot a sound next diagnostic step?

**Complete frontier coverage**: yes, and this directly fixes the flaw
this analyst independently found in the previous 8-state proposal — all
13 unresolved states have distinct compound `(successor_signature,
component_geometry)` profiles (independently confirmed two rounds ago),
so any subset smaller than 13 necessarily omits at least one
structurally-unique state's own continuation entirely. Including all 13
is the only design that avoids this.

**Fairness of equal branch-local caps**: fair as a *resource*
allocation, but **not obviously optimal as an *information* allocation**.
The 13 states have verified successor counts ranging 1-3 (five states
at 1, five at 2, three at 3, from this analyst's own reproduced ranking
table two rounds ago). A flat 10,000-expansion cap gives states with
fewer live successors effectively more expansions-per-branching-choice
than states with more successors — meaning the pilot will likely probe
*proportionally deeper* into the narrow states than the wide ones within
the same nominal budget, even though the wider states (more branching
options per step) are, if anything, the more plausible place to find a
rare bridge event, simply by having more distinct edges tried.  Equal
caps are a defensible, simple default for a first diagnostic pass — but
they are not demonstrably the information-maximizing choice, and this
document does not describe them as such.

**Is 10,000 enough to distinguish rapidly-exhausting from long-tail
states?** Plausibly yes for the *rapid* end (states that empty their
frontier within a few hundred to a few thousand expansions will show
it clearly), but the ceiling is genuinely uncertain for the *long-tail*
end. The already-verified whole-branch history reached the current
22-node frontier (depths 47-88) via 305,000 total expansions with a
frontier-local mean legal-successor count of 1.27 and mean 13.18
collisions per 24 raw candidates — heavy collision saturation. A 10,000
cap per state, applied to states that are *already* 47-88 macro-steps
deep, is a meaningfully smaller relative probe than what produced the
existing frontier from the root; it is a reasonable *first* triage step
(cheap enough to run 13 in parallel, informative enough to separate
"empties almost immediately" from "still going"), but should not be
read as calibrated to reliably reach a *second* natural-exhaustion
plateau if one of the 13 turns out to need substantially more depth
than the others did to reach their current point.

**Would any budget allocation be mathematically preferable?** A
successor-count-informed allocation — e.g. weighting the cap inversely
by branching factor, or explicitly reserving more budget for the five
highest-successor-count states (`:3, :6, :305018, :303321, :13` — the
exact five this analyst found excluded from the flawed 8-state batch
two rounds ago) — would be more defensible on information grounds than
a flat cap, since it directly compensates for the asymmetry just
described. This is a genuine methodological improvement worth
considering for a *second* pilot round, not a criticism of using equal
caps for a *first* diagnostic pass, where simplicity and comparability
across all 13 has real value.

**Is the checkpoint cost justified?** 1.86-2.09 GB total (across 13
independent branch-local checkpoints) for a diagnostic, explicitly
non-final pilot is reasonable — well under half the size of the single
4.88 GB checkpoint already used for this branch's prior continuation,
and the stated discipline (no budget transfer, any nonempty capped
frontier stays `INCOMPLETE`) avoids exactly the kind of silent
relabeling this project has consistently guarded against. Justified as
described.

## 2. Pre-registered outcome interpretation

| outcome | exact conclusion permitted | conclusion **not** permitted | required replay/certificate | best next step |
|---|---|---|---|---|
| **A. all 13 naturally exhaust** | the *entire* 22-state `short_ell2_r1_37` frontier is exactly exhausted — an `EXACT_EXHAUSTIVE_CERTIFICATE` for the whole branch, joining the other 7 top-8 children | anything about the other 431 children in the 439-child corpus, or about a family-wide/universal bridge conjecture | independent hash-verified replay of each of the 13 new certificates, exactly as done for the prior 7 | attempt the structural hand-proof route (section 4) now that a complete, comparable 8-of-8 dataset exists |
| **B. some exhaust, some cap** | each exhausted state individually gets its own exact certificate; capped states remain individually `INCOMPLETE`, unchanged in kind from before | any aggregate claim about all 13 together; any assumed correlation between successor-count and outcome without checking it explicitly | per-state replay verification for the exhausted subset; an explicit (not assumed) comparison of exhausted-vs-capped by successor count and other profile fields | raise the cap only for the still-capped subset (efficient triage), or begin hand-analysis of the newly-exhausted subset immediately |
| **C. all 13 hit cap** | 10,000 expansions is not sufficient to resolve any of these 13 at this depth/complexity — a negative result about *cap size*, not about mathematical content | any change to bridge-conjecture status; zero net information about existence/non-existence beyond a slightly larger bounded observation | none required, but a breakdown of *why* (near-empty remaining frontier vs. still-growing frontier at the cap) is genuinely informative | diagnose the growth pattern first (plateaued vs. still-expanding), then either raise the cap substantially or switch to an adaptive/unequal allocation |
| **D. a component merge appears** | a hand-verifiable exact fact about *that specific continuation* — constructively refutes the "no continuation ever merges these two components" local conjecture for this one branch; the exact precondition this analyst's own component-bridge template (established four rounds ago) identified as missing has now occurred | that Target A is found — a merge is necessary but not sufficient; the subsequent `R2` attempt must still separately satisfy `F_def=1`, `H=0`, `hub_touch_count<=2` | full replay verification of the specific merge edge against the section-6 template's exact definition; then explicit tracking of the very next `R2` candidate's `same_component` outcome | halt the equal-cap pilot for that one state immediately and deep-dive it specifically — this becomes the single highest-priority item in the whole research thread |
| **E. a bridge-template occurrence appears** | treated as **the same event as D**, described in this project's own established vocabulary (a forced, non-abandoning `Z2`/`Z3` edge landing on a non-`hub_id` hub-component hexagon) — flagged here as a terminology note pending confirmation that Codex's classification is using the same definition | (same as D) | (same as D) | (same as D) |
| **F. literal Target A appears** | a new Target-A boundary is found in `short_ell2_r1_37` — the single most significant possible outcome of this entire multi-round thread | anything about `L_6 >= 872` or the unconditional bound directly — a Target-A discovery is a structural data point, not direct progress on the main conjecture | mandatory independent literal replay plus left-`S6` canonicalization, checked against the known-18 corpus, exactly as this project's established methodology requires before any claim of novelty | this becomes the top priority of the whole project: characterize the boundary's exact structure and test it directly against the "known-18 collapse" conjecture (every short-root Target-A boundary observed so far has been left-`S6` equivalent to known-18) — a genuinely new class here would refute that conjecture with an exact witness |
| **G. Target B survivor appears** | a new data point for the separate Target-B/Area-A research thread (a different completion envelope than Target A, established in earlier rounds) | should not be conflated with Target-A/bridge-conjecture progress — the two are governed by different recognizers | cross-check against this project's established Target-B verification apparatus (not engaged with this round) | hand off to whatever thread tracks Target-B specifically; do not let it substitute for this round's Target-A-focused question |

## 3. Bridge-conjecture significance, by scope

| outcome | `short_ell2_r1_37` scope | top-8 scope | 439-child corpus scope |
|---|---|---|---|
| **13/13 exhaustion, no bridge** | fully closed — joins the other 7, matching their exact-certificate status | **8/8 exact, complete-space certificates** — the strongest possible finite result for this specific family; still not a theorem | unchanged — 431 children remain entirely uninvestigated at this level of rigor; the family-wide conjecture is exactly as open as before, with one more (already-small, n=8) confirmed instance |
| **partial exhaustion, no bridge** | remains `INCOMPLETE` as a branch (any nonempty frontier keeps it open) — deeper, more granular sub-certificates recorded, but branch-level closure not achieved | remains at 7/8 (or a fraction thereof) in terms of whole-branch closure | negligible additional evidence beyond the row above |
| **130,000 additional bounded observations, no bridge (i.e. outcome C)** | remains `INCOMPLETE` — the weakest positive-direction outcome; adds roughly 43% more volume to an already-large (≈305,000-node) bounded observation without changing its category | remains at 7/8; zero new exact certificates | negligible; still just a larger finite negative count, graded exactly as every other zero-occurrence finding in this session — evidence, not proof |

## 4. Candidate hand-proof route

**No invariant is asserted as proved here** — the task explicitly asks
for a proposal, not a claim.

Given the established common facts (hub complete; `Phi=0`; `R1`-target
and hub components separated; immediate `R2` fails only by
`same_component`; no exact recurrence; collision saturation
non-monotone), the weaker, already-largely-understood candidate — a
pigeonhole/well-foundedness argument from the finite state space
(`720 - visited` strictly decreasing, per the `Phi` formula and the
already-confirmed monotone quantities `P,O,S,Ndef,Phi,hub_popcount,
visited`) — only proves that any branch must eventually terminate
*somehow*. It does not explain why it terminates *without* a bridge,
so it is not the promising direction.

**The genuinely promising, not-yet-attempted route** is a **direct
combinatorial enumeration over the fixed `HEX_POSITION`/`ORBIT_PHASE`
tables** (not a search): since the entire hexagon/orbit incidence
structure is a fixed, finite, fully-known object independent of any
particular branch, it should be possible in principle to enumerate,
for the specific family of orbits reachable via this family's
branching-spine parametrization (the shared spine plus `root_ell`
parametrization established several rounds ago), exactly which
hexagons each such orbit's phase-cycle *could ever* touch — and check
by direct table lookup, not by search, whether any of those hexagons
coincide with the fixed, already-known hub-component hexagon set. If
such a coincidence can be shown structurally impossible for this
family's specific orbit-reachability pattern, that would be an actual
hand-proof of the local conjecture; if a coincidence can be
constructively exhibited, that would refute it directly. This is a
restatement, specifically scoped as the next concrete step, of a
direction already named (but not attempted) in this analyst's own
documents four and two rounds ago — proposed again here because nothing
in the newly-reported facts changes the assessment that it remains the
correct next move once the pilot's empirical results are in hand.

## 5. Logical audit of the count-reconciliation relation

**Assessing the form only** — "parent-DAG vertices minus 2 parent-null
roots equals 421,219 B0-classified incoming paths" — since no ledger is
available to check actual values.

The arithmetic form "vertices − roots = (non-root) incoming-edge count"
is the **standard, sound identity for a rooted tree or forest**, where
every non-root vertex has *exactly one* parent: the number of edges in
such a structure always equals the number of non-root vertices, so
subtracting the root count from the vertex count gives exactly the
edge (equivalently, "incoming path") count. This project's own
already-verified data is consistent with a single-parent structure —
every frontier record checked two rounds ago carried exactly one
`parent_node_id`, not a list of parents — so **the form is sound in
principle for this project's actual data shape**, contingent on two
conditions this document cannot verify without the ledger:

1. **Genuine single-parent structure holds for the *entire* scanned
   graph**, not just the 65-node ancestry union previously checked —
   if any vertex anywhere in the full 421,221-vertex structure has more
   than one incoming edge (a true DAG diamond, not a tree), the simple
   subtraction would undercount the edge total.
2. **"B0-classified" must be coextensive with "every non-root incoming
   edge," not a proper subset of it** — if `B0` denotes a specific
   status (e.g. "no `R` event yet observed on this path") that could in
   principle exclude some non-root edges for reasons unrelated to
   root-ness (e.g. edges downstream of an `R1` admission), then
   `vertices − roots` would only be an *upper bound* on the `B0` count,
   not an exact equality, and the reconciliation as stated would need a
   further subtraction this document cannot confirm is absent.

**Conclusion**: the relation's *form* is a correct and unsurprising
identity for a rooted-forest structure, and is plausible given this
project's own established data conventions — but its exactness for the
*specific* B0/root-count figures cited depends on two assumptions
neither confirmable nor refutable without the underlying ledger. This
is reported as a conditional structural assessment, not a verification.

## What this document does not do

- Does not verify any of this round's reported figures — no branch or
  file exists to check them against, exactly as the task specifies.
- Does not assert any hand-proof invariant as established — section 4
  is a proposal for future investigation only.
- Does not resolve the count-reconciliation question numerically —
  only its logical form is assessed, per the task's own scoping.
- No search run, no Codex file touched.

CLAUDE_ALL13_PILOT_ASSESSMENT_READY
