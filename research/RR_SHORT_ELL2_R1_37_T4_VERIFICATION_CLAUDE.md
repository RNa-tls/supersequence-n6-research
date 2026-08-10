# T4 verification attempt: commit does not exist, but the core lemma does check out

## 0. Fetch result — stronger than "not found"

`git fetch --all --prune`, `git remote show origin`, and a direct
attempt to fetch the specific SHA were all performed. **`git fetch
origin 19d484b2aff4344b619c536459d1a9155209751f` returns `fatal:
remote error: upload-pack: not our ref
19d484b2aff4344b619c536459d1a9155209751f`** — the git server itself
explicitly states this object does not exist in the remote repository.
No new branch appears in `git remote show origin` either. **This is a
stronger and more definitive finding than "unverified": the commit is
confirmed nonexistent, not merely unreachable through an outdated
branch list.**

Consequently, **section 1 (fetch/verify artifacts), section 4's
84-anchor `h40`-fullness check, and every numeric verification claim
(replay nodes, `M1`-`M5` figures, "7/7 regression tests," "no SAT/CSP
used") cannot be performed at all** — there is nothing to fetch, hash,
or replay.

**However, this round's central mathematical claim — the "unique
predecessor lemma" — is stated in terms of specific literal
permutation words (`245130`, `513042`), which are checkable directly
against this repository's own fixed engine tables, independent of any
remote artifact.** Section 3 below performs this check directly, not
as a substitute for the missing verification, but because the task's
own section 3 explicitly asks for it ("do not accept uniqueness from
the report alone") and it does not require the nonexistent commit.
**This is the one genuine, substantive contribution this round can
make.**

## 1-2. Commit/artifact fetch and five-route completeness

**Cannot be performed.** No commit, no files, no hash values exist to
check. The five-route list (`q42:p1, q78:p3, q82:p0, q83:p4, q128:p2`)
matches this analyst's own independently-derived table from three
rounds ago exactly, as already confirmed in the prior round's
document — that part of the *structure* is credible on independent
grounds, but this round's specific claim that it is *complete* (no
sixth route exists) cannot be newly verified without the nonexistent
commit's own completeness argument.

## 3. The unique-predecessor lemma, independently checked

**Word identification, confirmed directly from `ORBIT_PHASE`/
`HEX_POSITION`** (no search, a direct table query):

- `"245130"` = permutation `(2,4,5,1,3,0)` — `HEX_POSITION` gives
  **hexagon 40**, matching the report's own claim exactly.
- `"513042"` = permutation `(5,1,3,0,4,2)` — `ORBIT_PHASE` gives
  **orbit 91, phase 2**, matching the report's "`q91:p2`" exactly, and
  `HEX_POSITION` gives **hexagon 82**.

**Literal transition check**: iterating every move in `ALL_MOVES` and
computing `core.word_after((2,4,5,1,3,0), move.action)` finds exactly
two moves landing on `(5,1,3,0,4,2)`: a weight-2 move (`w2:10`) and a
weight-6 move (`w6:234510`). **The weight-2 transition
`245130 --w2:10--> 513042` is confirmed real.**

**Uniqueness, checked properly** (per the task's explicit instruction
not to accept it from the report alone): `ALL_MOVES` contains **exactly
one weight-2 move in the entire 550-move alphabet** (the weight
distribution across all 550 moves, computed directly, is `{1:1, 2:1,
3:3, 4:13, 5:71, 6:461}`). Since a "move" acts as a fixed relabeling
function (`core.word_after`) and every such function is a bijection
over the 720-permutation space, **every single target permutation in
the entire state space has exactly one weight-2 predecessor** — this
was independently spot-checked against five random other targets, and
all five also showed exactly one weight-2 predecessor.

**This is the most important nuance this document adds**: the
"uniqueness" of `245130 --w2--> 513042` is **not a special property of
this configuration** — it is a **trivial, universal consequence of
this engine having only one weight-2 move total**, true for every
permutation in the state space without exception. The report's framing
("the unique pre-R2 Z2 predecessor is...") is technically correct but
should not be read as evidence of anything distinctive about
`q91:p2` — it holds vacuously for every target. **This does not weaken
the report's overall argument** (the argument does not depend on the
uniqueness being *special*, only on it being *true*, which it is) —
but it clarifies exactly how much logical weight step 3 of the report
actually carries: none beyond "there is exactly one Z2 candidate to
check," which was never in serious doubt given the engine's own
structure.

**Whether any `Z3` or other legal macro can register the same state**:
`q91:p2` (`513042`) sits in orbit 91, which is *already registered*
(orbit 91 opened at `R1`) — `Z3` requires a *fresh* target orbit
(`om[q]==0`), so **no `Z3` can ever target `q91:p2`**, by definition,
confirmed directly from `joint_kind`'s already-established semantics.
An `R`-kind arrival at `513042` remains structurally possible in
principle, but would itself be the terminal `R2` event (per the
established fact that any `R`-kind edge fired after `R1` is
immediately evaluated as `R2`, never an intermediate registration
step) — so it is not a "prior registration" mechanism at all, and is
outside the scope of what "pre-`R2` predecessor" means here. **The
weight-2 route is indeed the only *non-terminal* route to `q91:p2`.**

## 4. `h40` fullness and no-reentry — logically sound, empirically unconfirmed

**The logical argument, checked step by step, is valid**: `extend()`'s
own collision check (`if state.visited(target): return None`) means
any permutation, once visited, can never again be the *target* of a
later move — and since every state the walk occupies was necessarily
reached as some earlier move's target, **a permutation that has already
been visited can never again be the walk's *current position* either**
(returning to it would require re-targeting it, which is forbidden).
**Given the premise that hexagon 40 is genuinely *full* (all 6 literal
permutation-windows visited, not merely "registered" in the coarser
`orbit_masks` sense) by the relevant point, `245130` specifically must
already have been visited, and the walk can therefore never again be
positioned at `245130` — so the unique weight-2 move to `513042` can
never fire again. This chain (steps 6-9 of the report) is sound,
conditional entirely on that premise.**

**The premise itself cannot be confirmed or refuted this round.**
This is the single most important open item: "`h40` is full" in the
strong sense (`hex_masks[40] == FULL_HEX`, all 6 windows) is a
*stronger* claim than what this analyst has *actually* verified in
prior rounds. Re-checking the already-hash-verified 22-state frontier
data directly: at all 22 states (depths 47-88), the `component_
partition` shows hexagon 40 as a member of `C_R1`'s *registered
incidence set* — a fact about `orbit_masks` (some orbit has touched
some window of hex 40), not a fact about `hex_masks` (whether *every*
window of hex 40 has been visited). **These are genuinely different
claims, and only the weaker one has been independently confirmed.**
**Whether this is "genuinely a hand proof or still relies on finite
anchor enumeration" — it is neither, as things stand**: it is a valid
*conditional* hand proof whose premise itself would need to be
established either by a further hand argument (not attempted here) or
by finite enumeration over the real 84 anchors (data this analyst
cannot reach this round, since the commit does not exist).

## 5. Theorem implication chain, checked conditionally

- **`T2b`** (all five hex-82 routes obstructed): **not established**,
  pending the `h40`-fullness premise. **A genuinely new and sharper
  reduction is worth crediting here, though**: the report's own framing
  (steps 1-2) argues that *none* of the five hex-82 routes matters
  unless hexagon 82 itself first becomes part of `C_R1` — and the
  *only* direct way for that to happen is via orbit 91's own phase 2
  (`513042`), since the five candidate orbits (`42,78,82,83,128`)
  are not yet part of `C_R1` themselves, so their independently
  touching hexagon 82 would only create an *isolated* sub-component,
  not a `C_R1` merge, unless hexagon 82 is *also* independently linked
  to `C_R1` via orbit 91. **This is a real, valid structural point this
  analyst's own prior two-round framing (treating the five routes as
  five independent, symmetric candidates) did not make explicit** —
  if `q91:p2` is blocked, it plausibly renders the other four orbits'
  hex-82 touches moot for the `C_R1`-merge question specifically, not
  merely blocked by their own independent mechanism. This sharpens,
  but does not on its own complete, `T2b`.
- **`T2+`** (complete `C4` prerequisite space collides): **not
  established** — as this analyst's own prior document already noted,
  `T2b` (even if fully proved) does not imply `T2+` without a separate
  completeness argument that the five-route list, plus the
  `{40,90,91,92}`-eliminated routes, exhausts the entire `C4`
  prerequisite space. Nothing this round adds such an argument.
- **`T3`** (first component-changing `Z3` impossible): **far short**,
  same reasoning as two rounds ago.
- **`T4`** (pre-`R2` bridge impossible): **far short of `T3`**, hence
  far short of this.

**Direct-`Z2` exclusion, re-verified**: this analyst's own hand-proof
from four rounds ago (orbit 91's phase-hexagon set `{40,82,90,91,92}`
disjoint from hub's `{0,1,4,6,8,9,18,24,96}`) remains independently
correct and unaffected by anything this round — direct `Z2` from an
*unexpanded* `C_R1` cannot reach hub, exactly as before. Whether *this
specific* argument (about `q91:p2` and hexagon 82) changes that
conclusion: no — `513042` itself is hexagon 82, still disjoint from
hub's set; the report's chain is about whether hex 82 *enters* `C_R1`
at all, a prerequisite *before* any hub-reaching question, not a
revision of the disjointness fact itself.

## 6. Scope-leakage audit

Every fact used in section 3-4's conditional argument is explicitly
scoped to: **this specific branch** (`short_ell2_r1_37`, via orbit 91
being the fixed `R1`-target orbit), **the `Phi=0`/full-pass, `F<=1`
forced-move regime** (needed for the "no-repeat forbids reentry"
argument's premises about which moves are even attempted), and **the
unverified 84-anchor set specifically** (the `h40`-full premise, if
ever established, would need to be shown for *that* specific state
set, not assumed to generalize). **No fact in this document's own
independent verification (section 3) implicitly smuggles in anything
broader than these scopes** — the weight-2-uniqueness fact is a
genuinely global, engine-wide fact (true for every permutation, not
just this branch), correctly and explicitly flagged as such rather
than presented as branch-specific evidence.

## 7. Proof compression

**Conditional on the unverified premise, the shortest valid lemma
chain is**:

- **Lemma A (hand proof, already established four rounds ago)**:
  direct `Z2` from an unexpanded `C_R1` cannot reach hub — orbit 91's
  5-hexagon set is disjoint from hub's 9-hexagon set.
- **Lemma B (hand proof, conditional on premise)**: if hexagon 40 is
  fully visited by the relevant point, the unique weight-2 route to
  `q91:p2` (hexagon 82) can never fire again, since its sole
  predecessor permutation (`245130`) can never be revisited — this is
  a genuine hand proof of a conditional statement, sound as verified
  in section 3-4, **not** a finite certificate (it does not enumerate
  states; it is a direct algebraic/no-repeat argument).
- **Lemma C (unverified, would need to be a finite certificate over
  the real 84 anchors)**: hexagon 40 is genuinely fully visited at all
  84 real Stage-D anchors. **This is the only piece of the whole chain
  that is not, and cannot from this round's data be, a hand proof** —
  it is an empirical claim about specific search states that would
  need direct inspection of real anchor records to confirm.
- **Theorem (would follow, conditional on Lemma C)**: no `q91:p2`
  registration is possible in the 84-anchor descendant region via
  the direct route — **but this closes only the direct-orbit-91 path
  to hexagon 82, not automatically all five hex-82 routes** (section
  5's `T2b` gap) **nor the full `C4` space** (`T2+`'s gap), both of
  which remain open regardless of Lemma C's status.

**Lemma A**: hand proof, fully established.
**Lemma B**: hand proof, sound, but conditional.
**Lemma C**: not a hand proof candidate at all — an empirical,
finite-certificate claim, unconfirmed.

## What this document does not do

- Does not verify any artifact, hash, or numeric figure from the
  claimed commit — it does not exist.
- Does not confirm or refute the `h40`-fullness premise — flagged
  precisely as the one remaining empirical gap in an otherwise sound
  conditional argument.
- Does not claim `T2b`, `T2+`, `T3`, or `T4` are established — all
  remain open, with `T2b` newly and precisely reduced to a single
  empirical question (Lemma C) rather than five independent ones,
  a genuine simplification credited to this round's framing.
- No search run; section 3's verification is a direct, deterministic
  query of already-existing engine tables, not an exploration of any
  kind.

REMOTE_DATA_INSUFFICIENT
