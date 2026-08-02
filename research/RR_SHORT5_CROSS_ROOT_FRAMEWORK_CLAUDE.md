# Cross-root proof-analysis framework for the five short roots

Planning document, prepared ahead of Codex's fair-admission pilots on
`short_ell1`–`short_ell4`. No new commit exists beyond
`codex/round-r2-literal-source-correction` (`b09f1d5`, unchanged —
checked via `git ls-remote` before writing this); nothing below is
analysis of new data. No search run.

## 1. Root-invariant versus root-specific classification

**`CLAUDE_OBSERVATION`**, four categories, defined precisely before use:

- **universally semantic** — true by definition/construction of the
  engine code; verifying it requires only reading the code, no
  combinatorial argument.
- **proved RR-wide** — a nontrivial theorem (a real proof step, even if
  short) already established to hold for *every* root, not just one.
- **short-root-wide conjectural** — a pattern observed at ≥1 short root,
  hypothesized but not proven to hold for the 5-root bare-abandonment
  family generally.
- **short_ell0-specific** — a literal/numeric/structural fact tied to
  `short_ell0`'s own concrete starting permutation; not expected to
  generalize without independent re-derivation per root.

Several of the ten named features split across categories — the
methodology and the specific instance are not the same claim, and
conflating them is exactly the kind of overclaim this framework exists
to prevent.

| feature | classification | note |
|---|---|---|
| literal R2 source = `edge.run.state` | **universally semantic** | a property of `extend()`/`ORBIT_PHASE`/rotation mechanics, independent of which root produced the state |
| incidence forest construction | **universally semantic** | `incidence_components` is a pure function of `orbit_masks`, no root-dependence in its definition |
| component monotonicity | **proved RR-wide** | requires the `orbit_masks` OR-only argument — a real (short) proof step, but one that holds for any root once made |
| R1 preparation spine — **literal instance** (orbit sequence `33→64→90→96`, phase sequence `2→3→4→0`) | **short_ell0-specific** | tied to this root's own starting permutation arithmetic |
| R1 preparation spine — **qualitative pattern** (one shared `Z2` spine, R1 firing as alternative stopping points) | **short-root-wide conjectural** | untested beyond `short_ell0`; a natural hypothesis from the RR alphabet's move-table design, not yet checked against the other four |
| `CH1`/pre-R-completer relation — **definitions** (`Decoration.branch`, `event_order_class`) | **universally semantic** | engine-level, root-independent by construction |
| `CH1`/pre-R-completer relation — **which events land where** | **short_ell0-specific data point** | depends on each root's own hub/orbit geometry; not yet observed for the other four |
| completer orbit/phase (the specific values, e.g. orbit 120 phase 0 = hex 0) | **short_ell0-specific** | a literal coincidence of this root's own permutation structure |
| repair types — **classification logic** (`joint_kind`, "`Z3` re-entry" is definitionally `R`) | **universally semantic** | follows from `joint_kind`'s fixed definition, no root term anywhere in it |
| repair types — **only `Z2`/`Z3`-fresh are viable repair candidates** | **proved RR-wide** | deduced from the universally-semantic classification logic, so the deduction itself carries over to any root |
| known-18 equivalence — **methodology** (literal replay + left-`S6` canonicalization + comparison) | **proved RR-wide** | the machinery (`exact.canonicalize`, the decorated-pair comparison procedure) is root-agnostic by construction |
| known-18 equivalence — **this specific result** (`short_ell0`'s hit = `short_ell0_33d70b4249b7`) | **short_ell0-specific** | a fact about one boundary, not a pattern yet |
| Target-B full-segment closure — **the theorem** (Round 32 `EEEE` theorem, conditional on `R_cap=1`) | **proved RR-wide** | stated and proved generally, applies to any state satisfying its precondition regardless of which root produced it |
| Target-B full-segment closure — **whether a given boundary satisfies the precondition** | **must-check-per-boundary, not assumed** | genuinely root/boundary-specific and cannot be inherited |
| Phi/M behavior (conservation law, sawtooth identity) | **proved RR-wide** | both follow purely from `joint_kind`/`extend()` definitions, independent of root |

## 2. Cross-root canonical profile

**`CLAUDE_PROPOSAL`** — the minimal proof-safe comparison profile,
built directly on the already-proven 27-field decoration schema
(`RR_DECORATED_BOUNDARY_STATE.md`) rather than inventing a new one.
Every field is marked with its transformation behavior under the one
proven symmetry (left-`S6` relabeling):

| field group | fields | left-`S6` behavior |
|---|---|---|
| **root identity** (provenance only, never quotiented) | `root_id`, `root_ell`, `o_star` | **not quotiented** — these identify *which* root, and comparing them across roots is the whole point; quotienting would erase the very thing being compared |
| **R1 child geometry** (orbit/hexagon-transported) | `r1_source_orbit`, `r1_source_phase`, `r1_target_orbit`, `r1_target_phase`, `r1_macro_index` | orbit/phase pair **quotiented** (orbit id transports under `LEFT_ORBIT_ACTION`; phase is left-`S6`-**invariant**, per `RR_DECORATED_BOUNDARY_STATE.md`'s own field list); `macro_index` invariant |
| **hub/completer timing** | `hub_id`, `hub_completer_orbit`, `hub_completer_hexagon`, `hub_completer_macro_index`, `hub_completer_kind`, `hub_completer_is_r1`, `hub_touch_count` | `hub_id`/`hub_completer_hexagon` **quotiented** (hexagon-transported); `hub_completer_orbit` **quotiented** (orbit-transported); the rest **invariant** |
| **incidence forest / component partition** | component vertex/edge counts, `component_count`, `r1_target_hub_distance`, `r2_source_hub_distance`, `r2_target_hub_distance`, `r2_meet_is_hub` | raw vertex/edge identities **quotiented** (they name specific orbits/hexagons); BFS-distance and LCA-type coordinates are **graph invariants**, hence left-`S6`-**invariant** |
| **resource coordinates** | `P`, `O`, `F`, `H`, `Ndef`, `D` | **invariant** — pure counts (how many orbits opened, how many passes, etc.), unaffected by relabeling which symbol is which |
| **`Phi`/`M`** | `Phi`, `M` | **invariant** — both are arithmetic functions of `P`/`O`/`visited_count` alone |
| **literal R2 geometry** | `r2_source_orbit`, `r2_source_phase`, `r2_target_orbit`, `r2_target_phase`, `ell` (rotation length) | orbit **quotiented**, phase and `ell` **invariant** |
| **canonical known-18 mapping** | `canonical_state_hash`, `canonical_boundary_class`, `known18_matches[].known_id`, `mapping_type` | **already-canonicalized outputs** — comparable directly across roots with no further transform, that being the entire purpose of canonicalizing first |

**Explicit warning, carried forward from `RR_DECORATED_BOUNDARY_STATE.md`
and directly load-bearing here:** a profile that *separates* roots'
boundaries into distinct-looking groups is not thereby a *minimal*
profile, and matching profiles across two states does **not** license
treating them as continuation-equivalent. The profile above is for
**comparison and classification only** — any claim that two states with
identical profiles share future reachability requires the full
canonicalized `(state, decoration)` pair to match exactly, per the
existing decorated-key sufficiency argument (itself graded *exhaustive
tested-universe equivalence*, not a universal proof, per this session's
own standing correction).

## 3. Generalization tests

**`CLAUDE_PROPOSAL`** — five exact outcomes, each with significance,
next task, and an explicit boundary on what a *bounded* pilot cannot
establish even if the outcome is observed:

### A. All roots reproduce only known-18 classes

- **Significance**: moderate — consistent with (not proof of) the
  RR-branch's recurring "Target A abundant, Target B empty" pattern
  extending to the short-root family.
- **Next proof task**: attempt a structural (not merely empirical)
  argument for *why* — a theorem connecting short-root R2 geometry to
  the known-18 corpus's own defining structure, not yet attempted.
- **Cannot be concluded**: search-space exhaustion (a bounded pilot is
  not full coverage); that no short-root-specific class exists beyond
  the tested budget; anything about the long-excursion roots that timed
  out in Round 36.

### B. Roots produce new Target A classes but all Target-B close

- **Significance**: moderate-to-high — demonstrates genuinely new
  geometric structure exists (relevant to later Target C/NR6 questions)
  while reinforcing, with fresh witnesses, that Target B stays empty.
- **Next proof task**: characterize what makes the new classes distinct
  from known-18; determine whether the *same* closure theorem
  (full-segment/`R_cap=1`) closes them or a genuinely different
  obstruction is needed each time.
- **Cannot be concluded**: that *all* new classes anywhere would close;
  a general "Target A abundant, Target B always empty" theorem from
  finitely many closed instances.

### C. One root produces a Target-B survivor

- **Significance**: **major** — the first actual candidate contribution
  toward `L_6≥872` from this entire RR-branch investigation.
- **Next proof task**: exhaustively (not just once) re-verify the
  survivor; attempt extension to a full Target-C/NR6 completion; re-audit
  every capacity theorem/helper used along the way — this project's own
  history (Round 38's firewall, this session's R2-source correction)
  shows exactly this kind of claim is where subtle unsoundness hides.
- **Cannot be concluded**: that the survivor extends to a full
  construction *without* that extension being separately, exhaustively
  verified — a Target-B survivor is necessary, not sufficient, for a
  full witness.

### D. R1 preparation-spine geometry differs across roots

- **Significance**: informative either direction — would refute (or fail
  to support) the §1 "qualitative pattern generalizes" hypothesis,
  narrowing which findings are truly RR-wide.
- **Next proof task**: distinguish *superficial* relabeling differences
  (expected — literal orbit labels are not left-`S6`-invariant, §2) from
  a genuine *structural* divergence (different spine length, different
  number of R1 alternatives, a fundamentally different branching shape).
- **Cannot be concluded**: that the roots are "fundamentally different"
  from surface-level label differences alone — those are expected and
  uninteresting on their own.

### E. One root has no R1 admission in the tested normal form

- **Significance**: potentially important — all 5 short roots have,
  since Round 36, shared an *identical* resource signature
  (`P=2,O=2,Ndef=0`) and an identical `legal_first_macro_edges` set; a
  genuine admission asymmetry among roots differing only in `ell` (the
  pure-rotation prefix depth) would be a real surprise worth flagging
  prominently, not quietly noting.
- **Next proof task**: determine whether this is a genuine geometric
  asymmetry or an artifact of the specific tested search design/normal
  form — a different prefix construction might restore admission.
- **Cannot be concluded**: that R1 is impossible for that root in *every*
  possible search design — only that it did not appear in the one
  design actually tested.

## 4. Candidate RR-wide lemmas — none asserted true

**`CLAUDE_PROPOSAL`** for each statement; **no lemma below is claimed
true**, per instruction. Each states exactly what would be needed to
decide it, in either direction.

### Lemma 1 — short-root boundaries reduce to known-18

**Statement**: for every short root `r` and every Target A boundary `b`
reachable from `r`, `canonicalize(b)` (raw state) is left-`S6`-equal to
`canonicalize(b')` for some `b'` in the original known-18 corpus.

- **Necessary evidence**: exhaustive (not bounded) Target-A search from
  all 5 roots, or a structural argument independent of search.
- **Likely counterexample pattern**: a boundary reached via a longer
  repair chain that opens enough fresh orbits/hexagons to reach a
  canonical form outside the (small) known-18 corpus.
- **Hand-proof route**: would need a bijection/quotient argument showing
  short-root R2-recognition geometry is structurally forced into the
  same finite canonical-form set as known-18 — no such argument exists
  yet.
- **Finite-certificate route**: exhaustively enumerate all Target-A
  boundaries from all 5 roots and check each against known-18 — the
  bounded pilots are a *sample* of this, not the certificate itself.

### Lemma 2 — short-root boundaries satisfy `Phi=0` and `R_cap=1`

**Statement, split by epistemic status because the two halves are not
equally supported:**

- **`Ndef(boundary) = 2` exactly**, for every short-root Target-A
  boundary — **this half is already provable**, not merely conjectural:
  it is the same "`+k` exactly" identity Round 37's envelope theorem
  already uses (`Ndef(boundary) = Ndef(root) + k`, `k=2` for a bare
  short root, `Ndef(root)=0`), independent of any search.
- **`Phi(boundary) = 0`** — genuinely open. Unlike `Ndef`, `Phi` depends
  on the rotation-run lengths along the specific path taken, not on
  `Ndef`/R-event accounting, so nothing forces it a priori.
- Whether "`Ndef=2`" should be read as "`R_cap=1`" additionally depends
  on treating `n_limit=3` as the reference constant — itself now
  understood (Round 41) as a Target-B/Area-A-scope convention, not an
  intrinsic Target-A property. **The lemma is more precisely two
  separate claims wearing one name**, and should not be evaluated as a
  single unit.
- **Necessary evidence** (for the `Phi=0` half): check `Phi(b)=0` for
  every boundary found across all 5 roots, not just the one instance
  confirmed so far.
- **Likely counterexample pattern**: a boundary reached via a rotation
  run of length exactly `ell=5` at every step *except* one short step
  elsewhere in the path (not at the R2 edge itself) that leaves `Phi>0`
  at the boundary.
- **Hand-proof route** (for `Ndef=2`, already essentially proven): direct
  citation of Round 37's exact identity — no new proof needed, only
  restatement.
- **Finite-certificate route** (for `Phi=0`): cheap, deterministic — read
  directly off already-exported per-boundary telemetry.

### Lemma 3 — every short-root R1 preparation is a phase truncation of one orbit spine

**Statement**: for every short root `r`, there is a single E-orbit `q*`
(or a small, canonically-defined family) such that `r`'s R1 alternatives
are exactly the "fire R now instead of continuing" choices at successive
`Z2`-preparation depths along one spine through `q*`'s phases.

- **Necessary evidence**: `short_ell0` exhibits this; needs the same
  check for `short_ell1`–`short_ell4`.
- **Likely counterexample pattern**: a root where more than one
  independent preparation spine exists (branching earlier than a single
  shared prefix) — would falsify the "one spine" claim.
- **Hand-proof route**: would require showing, from the fixed move table
  (`w2:10`/`w3:120`/`w3:201`/`w3:210`) and `new_orbit`/`ORBIT_PHASE`
  structure, that exactly one `Z2`-continuation is legal at each
  preparation depth from any bare short root — not yet attempted.
- **Finite-certificate route**: direct inspection of the legal successor
  set at each preparation depth for all 5 roots — cheap; partially
  already done (all 5 roots share an identical
  `legal_first_macro_edges` list from the Round 36-era ledger).

### Lemma 4 — every genuinely new boundary violates a common component condition

**Statement** (deliberately provisional — the condition `X` is
unidentified): for every Target A boundary *not* equivalent to known-18,
its R2 source/target components at the moment of recognition fail some
specific structural condition `X` that every known-18-equivalent
boundary satisfies.

- **Necessary evidence**: at least one genuinely-new boundary must exist
  to even begin characterizing `X` — none does yet (outcome B or C from
  §3 would be a prerequisite).
- **Likely counterexample pattern**: untestable until such a boundary is
  observed.
- **Hand-proof / finite-certificate routes**: **neither available yet** —
  `X` itself has not been identified. This lemma is recorded as a
  placeholder for future work, not a claim with any current support.

## 5. Evidence-grading ledger format

**`CLAUDE_PROPOSAL`** — a reusable ledger schema, populated here with a
worked example drawn from already-established facts (not new claims):

| grade | meaning |
|---|---|
| `HAND_THEOREM` | a proved, general statement with a complete argument, root-independent unless explicitly scoped |
| `EXACT_EXHAUSTIVE_CERTIFICATE` | a specific, bounded question (one boundary, one root's Q2 status, etc.) decided by a search verified to be non-truncated |
| `CORRECTED_BOUNDED_OBSERVATION` | a real, reproducible fact about a specific capped run — informative, not exhaustive |
| `CORPUS_SPECIFIC_SYMMETRY_MEASUREMENT` | an empirical measurement (e.g. stabilizer size, tie-variant count) taken over one specific, finite corpus — not a general symmetry theorem |
| `REFUTED_CONJECTURE` | a specific claim shown false, with the exact counterexample recorded |
| `OPEN` | genuinely undecided; no evidence yet in either direction |

**Worked example** (a sample of claims from this thread, not an
exhaustive catalog):

| claim | grade |
|---|---|
| Component partition is monotone non-increasing under any macro edge | `HAND_THEOREM` |
| R2 source is `edge.run.state`, never macro entry | `HAND_THEOREM` (engine-level, verified by running the regression test independently) |
| 28 of 33 roots are Q2-impossible | `EXACT_EXHAUSTIVE_CERTIFICATE` (envelope theorem, no enumeration) |
| `short_ell0`'s one corrected Target-A hit is Target-B closed | `EXACT_EXHAUSTIVE_CERTIFICATE` (helper-free DFS, `EXHAUSTED_NO_PATH`, not truncated) |
| The old 100,250-node `short_ell0` LIFO run's 44,021/5,419/0 split | `CORRECTED_BOUNDED_OBSERVATION` (real, reproducible for that run; not exhaustive of `short_ell0`) |
| `stabilizer_size=1` for all 2,234 old-corpus boundaries | `CORPUS_SPECIFIC_SYMMETRY_MEASUREMENT` (explicitly not generalized in its own source document) |
| The original "38,406 exact Target A hits" claim | `REFUTED_CONJECTURE` (38,405 of 38,406 were same-component failures, independently verified this session) |
| `short_ell1`–`short_ell4`'s R1 preparation spine shape | `OPEN` |
| Lemmas 1-4 above | `OPEN` (explicitly, per §4) |

## What this document does not do

- Does not analyze any `short_ell1`–`short_ell4` data — none exists yet;
  `git ls-remote` was checked before writing this and shows no new
  commit beyond `b09f1d5`.
- Does not assert any of §4's candidate lemmas as true.
- Does not claim the §2 profile is minimal in the strong (structural)
  sense — only that it is proof-safe and built from already-proven
  machinery, with the separating-vs-structural-minimality distinction
  stated explicitly.
- Runs no search, edits no Codex file.

CLAUDE_CROSS_ROOT_FRAMEWORK_READY
