# n=6 Minimal Superpermutation: Master Research Status

## Source-of-truth policy

This document (`SUPERPERMUTATION_N6_MASTER_STATUS.md`) is the current
human-readable research index for this project. It is **not** itself the
source of truth for exact counts: individual machine certificates
(`outputs/*.json`) and their verifier scripts (`src/*.py`) remain the
source of truth whenever a number is at stake. Where this document and a
cited JSON disagree, the JSON is authoritative and this document is stale
and should be corrected. Whenever a new result invalidates an old one
recorded here, **this master document must be updated** (see §5 for the
project's own history of exactly that happening, more than once).

This project spans two branch families that share one root commit
(`7dce52e`, "Initial commit") and then diverge: a long chain of `codex/*`
round branches (round 1 through round 61, culminating in
`codex/round-r1-37-hex82-t4` at commit `1f9efff0809c47e7ca1857ed6c7734c20e78f081`)
and this repository's own `claude/n6-supersequence-length-rn17wf` branch,
which independently verifies Codex's work and adds its own hand proofs and
theory documents. Facts cited from the Codex side below are cited against
that specific commit; facts from the Claude side are cited against this
project's own branch. No merge between the two has occurred; this document
is the first artifact that reads both trees together.

**Freshness.** This document was last synchronized against
`codex/round-r1-37-hex82-t4` at commit `1f9efff0809c47e7ca1857ed6c7734c20e78f081`
(no commits beyond this were reachable at last check). Before trusting
this document as current, or before adding a new round's results to it,
run:

```
git fetch --all --prune
git log --oneline origin/codex/round-r1-37-hex82-t4 -3
```

and compare the HEAD against the commit above. If it has moved, this
document is stale until the new round's results are reviewed and folded
in (§5's invalidated-results discipline applies to keeping this document
itself honest, not just to the underlying research). This is a manual
check, not an automated one — no trigger currently re-runs it on a
schedule; that would be a separate, explicit setup if wanted.

---

## Executive summary

- **What are we trying to prove?** The length `L(6)` of the shortest
  string containing all 720 permutations of 6 symbols as contiguous
  substrings ("minimal superpermutation," n=6). Specifically, this project
  is trying to raise the proven lower bound past the literature value of
  867, ideally to 872 (matching the best known explicit construction),
  using a specific combinatorial engine (`ExactState`, no-repeat literal
  permutation walks, "RR/short-root" search program).
- **What have we actually proved?**
  - `L(6) >= 867` — literature result (Houston/Pantone/Vatter, 2014),
    cited and formula-checked in this repo, not re-derived.
  - `L(6) <= 872` — an explicit length-872 witness is checked directly in
    this repo (`data/verified_872_witness.txt`,
    `tests/test_872_witness.py`): all 720 length-6 windows present and
    distinct.
  - A large body of foundational combinatorial facts about the n=6
    permutation/E-orbit/hexagon structure (§4), several of them full hand
    proofs, several finite-computation certificates.
  - **The strongest current result**: for one specific, fully-frozen
    finite family of states (`short_ell2_r1_37`'s 84 Stage-D anchors and
    their exact descendants), a **pre-R2 bridge from the R1-target
    component to the hub component is impossible** ("T4"), independently
    verified (§7). A companion general lemma (VNTS, §8) explains *why*
    that proof works and what a future branch would need to reuse it.
  - This project has also produced a genuinely large catalog of
    **invalidated / corrected** intermediate results (§5) — this is
    normal, disciplined research hygiene, not a project failure, but it
    means old reports must not be cited without checking this document
    first.
- **What is the strongest current result?** T4 for `short_ell2_r1_37`
  (§7): `[T4][HP+EC+ER+IV]`.
- **What remains open?** Everything about `L(6)` itself. **This project
  has not proved `L(6) >= 872` unconditionally, and has not proved it even
  conditionally beyond the single branch above.** See §11 for the full
  "what is proved / what is not proved" split and §12 for ranked open
  problems.
- **What would constitute the next major breakthrough?** Either (a)
  successfully generalizing the T4/VNTS template (§8) to the other seven
  top-8 short children and then to all 439 short children, closing the
  entire RR-short program, or (b) an entirely different argument
  (combinatorial, not search-based) extending the literature's 867 bound.
  Neither is close; see §12.

**Prominently, per this project's own convention:**

> **THIS PROJECT HAS NOT PROVED `L(6) >= 872` UNCONDITIONALLY.**

Three kinds of statements must be kept separate throughout this document
(and are labeled inline via the evidence tags of §9):

- **Unconditional mathematics** — true regardless of any assumption this
  project makes (e.g. the 867 literature bound, the 872 witness, pure
  group-theoretic facts about S6/E-orbits/hexagons).
- **NR6-conditional mathematics** — true only if the "NR6" assumption
  holds (defined in §2); this includes essentially the entire RR-short
  program, T4 included.
- **Bounded computational observations** — true only within an explicitly
  bounded search (a node cap, a depth cap, a fixed finite anchor family);
  never proof of a general statement, however suggestive.

---

## 2. The global problem

A *superpermutation* on n symbols is a string containing every one of the
n! permutations of those symbols as a contiguous substring. `L(n)` is the
length of the shortest one.

- **n=6 known bounds.** `867 <= L(6) <= 872`.
  - **Lower bound 867**, proved in the literature: R. Houston, "Tackling
    the Minimal Superpermutation Problem,"
    [arXiv:1408.5108](https://arxiv.org/abs/1408.5108) (2014), building on
    an anonymous 2011 4chan `/sci/` argument formalized with Jay Pantone
    and Vince Vatter. Formula `L(n) >= n! + (n-1)! + (n-2)! + n - 3`,
    implemented and checked in this repo at `src/lower_bound.py::houston_lower_bound`.
    This bound is **not** re-derived by this project; it is cited and its
    arithmetic is checked.
  - **Upper bound 872**, an explicit witness verified directly in this
    repository: `data/verified_872_witness.txt`, checked window-by-window
    by `src/verify.py::verify_superpermutation` via
    `tests/test_872_witness.py`. (First found by Robin Houston in 2014;
    archived publicly at
    [github.com/superpermutators/superperm](https://github.com/superpermutators/superperm).)
  - This project's own from-scratch greedy constructor
    (`src/construct.py::greedy_construct`) reaches 873, not 872 — an
    honest, non-optimal baseline, not a competing result.
- **What this project is trying to establish.** Whether `L(6) = 872`, i.e.
  whether the 867 lower bound can be raised all the way to 872. The
  concrete research vehicle is the "RR" program: model a hypothetical
  minimal-length string as an exact, non-repeating walk through
  permutation-space (see `ExactState`, §3), and try to show that certain
  walk continuations are combinatorially forced to be impossible, thereby
  raising the achievable lower bound within this project's own coordinate
  system `L = 867 + (k + N + H)` (§3).
- **What NR6 means in this project.** "NR6" is the assumption, stated in
  this project's own original task framing and never proved or disproved
  here, that a minimal n=6 superpermutation can be represented as a
  **non-repeating walk visiting all 720 permutations exactly once** — i.e.
  that the `ExactState` engine's whole state space (`hex_masks`,
  `orbit_masks`, no-repeat semantics) is actually the right model of a
  length-minimizing string, not merely a convenient combinatorial
  abstraction. Source:
  `research/RR_NR6_IMPACT_ASSESSMENT.md` and `STATUS.md`'s own "Open
  problems" list, item 2: *"Whether the specific `NR6` assumption... is
  even true is, per that same prompt, a separate open question — not
  addressed here."*
- **Why the present work is conditional unless NR6 itself is established.**
  Every RR-branch result in this project — including the headline T4
  theorem of §7 — is a statement about walks in the `ExactState` engine's
  model. If NR6 is false (i.e. no minimal n=6 superpermutation actually
  corresponds to such an exact non-repeating walk), then none of these
  results say anything about `L(6)` at all; they would still be true
  combinatorial facts about the model, but the model would not bind the
  quantity this project cares about. **This project does not know whether
  NR6 is true**, and has not attempted to prove it.

**Separation to keep throughout this document:**

| category | examples |
|---|---|
| unconditional mathematics | 867 lower bound (cited); 872 upper bound (verified witness); E-orbit/hexagon group theory (§4); Cover theorem |
| NR6-conditional mathematics | everything in the RR/short-root program, incl. T4 (§7) and VNTS (§8) |
| bounded computational observations | any node-capped/depth-capped search result not backed by a finite-completeness argument (flagged `[BO]` throughout, see §9) |

---

## 3. Project notation

Sources: `legacy_research/work/superperm_partial_f1.py` (engine),
`legacy_research/outputs/SUPERPERMUTATION_RESEARCH_RECORD_KO.md`
("KO-RECORD," the foundational write-up), and this project's own
`research/RR_TARGET_A_DEFINITION.md` / `RR_TARGET_B_DEFINITION.md`.

| symbol | meaning | source |
|---|---|---|
| `S` | strand/rotation-run counter (stored `ExactState` field) | `legacy_research/work/superperm_partial_f1.py` (`ExactState` class) |
| `F` | abandonment counter (`F_def`, stored field; `TARGET_F=1` for the whole RR program) | same |
| `P` | sum of used orbit phases (computed property) | same |
| `O` | number of open E-orbits (computed property) | same |
| `D` | sum of unused phases per open orbit (computed property) | same |
| `N` (`Ndef`) | `Ndef = S + F - O` (computed property) | same |
| `H` | hub-defect counter (stored field) | same |
| `k` | `k = O - 24` (n=6 coordinate) | KO-RECORD §5 |
| **`L = 867 + (k + N + H)`** | the project's length coordinate; 867 is the Houston lower bound | KO-RECORD §5 boxed identity; restated `STATUS.md` line ~69 |

Definitions:

- **E orbit** — orbit of a permutation word under right-multiplication by
  `E = sigma^(n-1) * tau`; size `n-1` (5 for n=6); 144 such orbits in S6
  (`ORBIT_COUNT=144`, enforced by a runtime assertion in
  `superperm_partial_f1.py` that `len(HEX_POSITION)==720` and
  `len(ORBIT_PHASE)==720`). Source: KO-RECORD §2;
  `superperm_partial_f1.py`.
- **Hexagon** — orbit of a word under rotation `sigma` alone; size 6 (120
  hexagons in S6, `HEX_COUNT=120`). Source: KO-RECORD §2; `HEX_POSITION`
  map in the engine.
- **Phase** — a word's position (0-4) within its own E-orbit. Source:
  `ORBIT_PHASE` map in the engine.
- **Hub** — in an F<=1 word, the unique (if any) hexagon that is the
  target of two or more distinct joints over the whole word; proved to
  exist under the F<=1 fragment invariant (Unique Hub Hexagon Lemma).
  Source: `research/RR_ANCESTRY_PROOF.md` §3-4, hand proof plus
  4,470/4,470 finite verification.
- **R event** — a weight-3, non-abandoning joint with `new_orbit=False`:
  re-entry into an already-open E-orbit. Classified via `joint_kind`.
  Source: `legacy_research/work/analyze_f1_n2_defects.py::joint_kind`.
- **Z2** — the engine's unique weight-2, non-abandoning move, classified
  `Z2_blocked_w2_existing` when its target orbit is already open. Same
  source.
- **Z3** — a weight-3, non-abandoning joint with `new_orbit=True`: opens a
  fresh E-orbit. Same source.
- **A2, A3, J (the abandoning joint kinds)** — the `joint_kind` classifier
  (`legacy_research/work/analyze_f1_n2_defects.py::joint_kind`) covers
  eight `(weight, abandonment, new_orbit)` combinations in total; §3's Z2/
  Z3/R entries above are only the three non-abandoning ones. The complete
  table, added here because an earlier draft of this document omitted the
  abandoning half:
  | weight | abandoning | new_orbit | `joint_kind` label |
  |---|---|---|---|
  | 2 | no | no | `Z2_blocked_w2_existing` |
  | 2 | yes | yes | `Z2_abandon_w2_new` |
  | 2 | yes | no | **`A2_abandon_w2_existing`** |
  | 2 | no | yes | `forbidden_blocked_w2_new` (this combination cannot occur) |
  | 3 | no | yes | `Z3_blocked_w3_new` |
  | 3 | no | no | `R_blocked_w3_existing` |
  | 3 | yes | yes | **`A3_abandon_w3_new`** |
  | 3 | yes | no | **`J_abandon_w3_existing_charge2`** — this is the
    §4/§5's "J-branch" charge-2 joint (F=1,H=0,N=2 program) named
    elsewhere in this document only informally as "J"; this row is its
    precise engine-level definition. |
- **R1 / R2** — the first and second R events in an "RR word" (an RR word
  is constructed to have exactly two R events). Source: `STATUS.md`.
- **Target A** — an R2 macro-edge whose resulting child has `F_def=1,
  H=0`, and whose R2 source/target orbits lie in the **same** component of
  the incidence forest at the moment R2 fires. Source:
  `research/RR_TARGET_A_DEFINITION.md` §2.
- **Target B** — an admissible R-free, F/H-preserving terminal
  continuation from a Target-A boundary state. Source:
  `research/RR_TARGET_B_DEFINITION.md` §2.
- **Bridge** — the mechanism by which R2's "same component" condition
  (Target A) can arise: some joint before R2 merges the R1-orbit's
  incidence component with another component (in this project's later
  round-40+ work, specifically with the hub's component) via a shared
  `(hexagon)` vertex in the union-find incidence graph. Source:
  `research/RR_SAME_COMPONENT_CHAINING_THEOREM.md` §5 (hand-proved
  sufficiency, 75/75 empirical necessity at the time).
- **Component-changing Z3** — a Z3 edge whose target hexagon is already a
  member of an existing incidence-forest component, thereby merging two
  components rather than opening an isolated new one. Source:
  `research/RR_SHORT_ELL2_R1_37_FIRST_COMPONENT_Z3_THEORY_CLAUDE.md`.
- **`C_R1`** — the incidence-forest component containing the vertex
  `(q, R1_target_orbit)` at a given moment. Same source.
- **`C_H`** — **notation introduced only within this project's own Claude
  branch** (`research/RR_SHORT_ELL2_R1_37_FIRST_COMPONENT_Z3_THEORY_CLAUDE.md`),
  meaning the hub's incidence-forest component. Not found anywhere in the
  Codex-side research corpus under this name; treat as Claude-branch
  shorthand, not an established project-wide symbol.
- **`Phi` (capacity potential)** — **name collision, flagged rather than
  silently resolved.** The symbol `Phi` (Φ) is used in this project for
  *two different things* that must not be conflated:
  1. The original, project-wide meaning:
     `Phi(S) = 5 + 6*(TARGET_P - S.P) - (720 - S.visited_count)`, a proved
     monotone capacity potential from the J-branch program, verified
     against 11,920 transitions (`STATUS.md`, "Capacity obstruction"
     section).
  2. An informal notation `Phi(q)` introduced in this project's own
     `research/RR_SHORT_T4_GENERIC_THEORY_CLAUDE.md` (§3) meaning "the
     fixed phase-to-hexagon incidence set of orbit `q`" — a completely
     different object (a finite set of hexagon indices, not a numeric
     potential). This document uses `Phi(q)` **only** in that
     local, Claude-branch-introduced sense when discussing VNTS (§8); the
     capacity potential of meaning 1 is not used anywhere in §7-8.
- **VNTS** — Visited Non-Terminal Source, a lemma introduced this project
  round (§8) generalizing the h82 obstruction inside T4. Source:
  `research/RR_SHORT_T4_GENERIC_THEORY_CLAUDE.md`.

---

## 4. Foundational proved results

Primary source for this section:
`legacy_research/outputs/SUPERPERMUTATION_RESEARCH_RECORD_KO.md`
("KO-RECORD"), the write-up for this project's earliest layer
(permutation-transition / E-orbit / hexagon-cover theory), plus the engine
source `legacy_research/work/superperm_partial_f1.py`.

### 4.1 Cover theorem

- **CLAIM.** `(n-1)*S + (n-2)*F >= (n-1)!` for any non-repeating covering
  permutation walk, n>=4. For n=6: `5S + 4F >= 120`.
- **SCOPE.** All non-repeating permutation covering walks in S_n, n>=4,
  under the NR6-type assumption that the walk visits each of the n!
  permutations exactly once as a window.
- **EVIDENCE.** [HP] hand proof + [EC] exhaustive finite verification
  (396/396 on archived walks).
- **SOURCE.** KO-RECORD §4.
- **STATUS.** Currently valid; gives `cost >= 24`, leaving `k+N+H >= 5` as
  the (still open) target.

### 4.2 `flip . r^-1 = E`

- **CLAIM.** In the right-action convention, `flip . r^-1 = E`, i.e.
  `sigma^-1 . tau = E`, where `E = sigma^(n-1) . tau`.
- **SCOPE.** All of S_n, specialized here to n=6.
- **EVIDENCE.** [HP] + [EC] (720/720).
- **SOURCE.** KO-RECORD §2, §4.5.
- **STATUS.** Currently valid, foundational.

### 4.3 E order and E-orbit count

- **CLAIM.** `E` has order `n-1`; every E-orbit has size `n-1`; for n=6,
  `|E|=5` and there are 144 E-orbits.
- **SCOPE.** S6 specifically (the count 144 is n=6-specific).
- **EVIDENCE.** [HP] (cycle structure) + [EC].
- **SOURCE.** KO-RECORD §2; `superperm_partial_f1.py` line ~48
  (`ORBIT_COUNT = len(core.E_REPS)`) with a runtime completeness
  assertion.
- **STATUS.** Currently valid, load-bearing throughout the entire
  corpus.

### 4.4 Overlap-edge (move) weight distribution

- **CLAIM.** The engine's full move table has exactly 550 entries, weight
  distribution `{1:1, 2:1, 3:3, 4:13, 5:71, 6:461}`.
- **SCOPE.** The n=6 engine's move alphabet, independent of any specific
  search branch.
- **EVIDENCE.** [EC], enforced by a hard runtime assertion
  (`if len(ALL_MOVES) != 550: raise AssertionError`).
- **SOURCE (first established).** `superperm_partial_f1.py` lines
  ~108-122. Independently re-derived and re-confirmed twice more in this
  project's own rounds (`research/RR_SHORT_T4_GENERIC_THEORY_CLAUDE.md`,
  `RR_SHORT_ELL2_R1_37_T4_VERIFICATION_CLAUDE.md`) — those are
  re-confirmations, not the original source.
- **STATUS.** Currently valid, unchanged.

### 4.5 Indecomposable-tail counts

Two distinct results, not to be conflated:

- **(a)** Symbol-preservation lemma: an indecomposable tail `pi` of
  weight `w` preserves the E-orbit's last symbol iff `pi(w-1)=0`; count of
  such tails is `(w-1)!` (`1,1,2,6,24,120` for w=1..6). [HP]. KO-RECORD
  §3.3.
- **(b)** All indecomposable tails of weight `w` (no restriction):
  `1,1,3,13,71,461` for w=1..6 — this is the per-weight breakdown behind
  §4.4. [EC], `core.tail_permutations(w)`; the w=1,2,3 cases are
  additionally hand-proved in `research/UNIQUE_WEIGHT2_MOVE_THEOREM.md`.
- **STATUS.** Both currently valid, unretracted.

### 4.6 "Direct R-flip" / weight >= 4 result

**Not found.** No occurrence of "direct R-flip," "R-flip," or an isolated
general "weight >= 4" theorem under that name was located in either
branch tree (searched `STATUS.md`, `research/*.md`, `legacy_research/*`,
and code). The closest adjacent material is the F=0 full-cassette result
(§4.7), where within that specific branch the only valid weight-4
chain-end tails are two specific permutations, not a general theorem. This
document does not invent a citation for this item.

### 4.7 F=0 / "full-cassette" result — canonical name **G2**

- **CLAIM.** `F=0 => H>=6 => L>=873`, via a finite group-theoretic
  argument restricted to the 24 complete cassettes and their weight-3
  chains.
- **SCOPE.** Explicitly **not** a claim about all F=0 walks in general —
  restricted to "the specified full-cassette range." KO-RECORD's own
  words: "this is not an automatic theorem for all of F=0, but a
  group-theory theorem for the specified full-cassette range, and this
  distinction must be kept."
- **EVIDENCE.** [HP] + [EC] (finite group computation over 24 cassettes).
- **SOURCE.** KO-RECORD §6, whose own section title is literally
  *"`F=0` full-cassette 가지: G2"* — this document's earlier draft
  described this result's content but never used its source-canonical
  short name; corrected here. There is no "G1" or "G3" section anywhere
  in KO-RECORD or elsewhere in either branch tree (checked directly via
  `git grep` across every branch's full history) — G2 is the only member
  of a "G-series" that exists in this repository. Do not assume a "G1" or
  "G3" result exists without checking first; this document will not cite
  either until one is actually found.
- **STATUS.** "Proved in that range" per KO-RECORD's own final status
  table; currently valid, unretracted, still explicitly scope-limited.

### 4.8 F<=1 regime

- **Origin.** KO-RECORD itself only closes F=0 (§4.7) and explicitly
  leaves the "F<5" branch open. The legacy corpus's next step was an
  incomplete exact-state search for `F=1, H=0, N=0`
  (`legacy_research/README.md`; never completed).
- **This project's adoption.** This repository's RR/J-branch program picks
  up exactly this corner, generalized to `F_def=1, H=0, N_def=2`
  ("J-branch") and to `F_def<=1` generally for the entire RR-short
  program (`TARGET_F=1` is hardcoded in the engine and inherited
  unchanged by every `src/*rr*` script).
- **A terminology correction, not a narrowing.** Round 27 fixed a
  confusion between `F_def` (the abandonment counter, `TARGET_F=1`) and
  `F_sym` (fresh-orbit-opening event count, effectively unbounded except
  via `O<=TARGET_O=25`) — a clarification, not a scope reduction.
- **STATUS.** Still valid/relevant; it is the active regime for the entire
  RR-short program including T4 (§7).

### 4.9 Saturated-cover / port / collision-graph results

Restricted to the saturated k=1 corner `(F,D,N)=(5,0,0), H<=3`
(`P=125, O=25, S=20`; "port" = a used pass-start phase, 125 ports total):

- **Genus-zero**: every saturated 25-E-orbit cover has ribbon-surface
  genus 0. [EC] (bounded exhaustive classification + exhaustive extension
  search on all positive-genus seed classes, all failed). KO-RECORD §8,
  `legacy_research/outputs/GENUS_ZERO_CERTIFICATE.md`.
- **Multiplicity-2**: every such cover's hexagon multiplicity is exactly
  `115x1 + 5x2` (no triple+). [EC] (exhaustive classification of the 4
  possible triple-seed types, all extension searches failed). KO-RECORD
  §9, `legacy_research/outputs/MULTIPLICITY_TWO_THEOREM.md`.
- **`c(f)=20 <=> the collision (multi)graph is a forest`**: combines the
  two above. KO-RECORD §9.
- **Port-lift / forest port-lift**: the remaining open problem in this
  sub-line. The exact-partition-plus-one subclass is fully computed
  (248/248 fail, [EC]); the general forest-cover case is only **sampled**
  (313/313 sampled failures, **[BO]**, not exhaustive).
- **STATUS.** Genus-zero and multiplicity-2 currently valid ([EC]). The
  general forest port-lift result is explicitly **[OPEN]**, not proved.

### 4.10 The "known-18" Target-A / Target-B ledger

- **Definitions.** See Target A / Target B in §3. The "known 18" is the
  set of Target-A boundary *states* known as of Round 27's enumeration (6
  `FOUND` + 22 `INCOMPLETE` at a node cap of 8,000) — **never claimed
  exhaustive**.
- **Ledger (Rounds 30-34, hand proofs + capacity accounting).**
  `18 -> 9` (Round 30, counting obstruction `B <= 5m+4`) `-> 8` (Round 31,
  refined port capacity) `-> 7` (Round 32, orbit-reuse penalty) `-> 0`
  (Round 34, flow-first model, cross-checked two independent ways,
  `EXHAUSTED_NO_PATH` 7/7).
- **Explicit scope disclaimer (Round 34, in the original text).** "This is
  not 'Target B is impossible'... What is closed is Target B from these
  18. It moves neither bound on L_6." Does not touch `L_6>=872`, CH2,
  Target C, N=0, or the U/J branches.
- **STATUS.** Currently valid and unretracted. Note: Rounds 35-37
  subsequently found **1,398 new** Target-A boundaries via a separately
  rebuilt search; these were **not** re-run through the Target-B ledger —
  the `18 -> 0` result applies only to the original 18, not to the 1,398.
  **Round 70 update (Claude branch).** The 1,398 have now been reclassified
  (`research/RR_TARGET_A_1398_RECLASSIFICATION_CLAUDE.md`): all 1,398 are
  replay-confirmed Q1 boundaries, only **6** are Q2/Area-A admissible and
  those 6 are already among the 18, and Target B is closed for all 1,398 by
  the margin identity `margin = 12 - D` (the occupancy-independent coarse
  segment bound; `D >= 19` throughout). **0 Target-B survivors, 0 new
  Target-A classes at Q2 scope.** The 1,392 remain genuine Q1 boundaries and
  are not deleted.
- **EVIDENCE.** [HP] + [EC] (capacity accounting is exact/finite, not
  sampled).
- **SOURCE.** `STATUS.md` rounds 29-38 narrative
  ("Twenty-ninth" through "Thirty-eighth follow-up round" / numbered
  Round sections).

---

## 5. Invalidated / corrected results

This section exists so that an older report cannot accidentally be cited
as current truth. Every item below was at some point stated as a project
result and was later shown wrong or over-scoped. **Do not cite the
"original claim" lines below as current facts.**

### 5.1 Preparation-parity conjecture family ("k >= 1" / parity claims) — [RF]

- **Original claim.** Rounds 21-26 stated several parity propositions on
  evidence capped at search depth <=6-8: "ell=4 preparation length `|P|` is
  always odd," "`#Z_{->O*}` is always even," "`|P| + #R_{<=C}` is a fixed
  invariant," and a winding-number reduction `#Z_{->O*} == k (mod 2)`.
- **Why it failed.** All underlying observations were correct but
  depth-capped; a genuine odd-length counterexample needs depth >=8, which
  no depth-capped search could reach. Round 27 built long-root extensions
  at that depth and found 6 exact witnesses refuting the parity claims.
- **Exact counterexample.** `abandonment ell=4, rot^4;w2:10 -> prep
  FFEFEFR (L=7, odd) -> rot^5;w2:10 (hub completer) -> R2 rot^0;w3:120`.
  `outputs/rr_long_prefix_extension_results.json`,
  `outputs/rr_counterexample_certificates.json`.
- **Corrected statement.** The preparation-parity conjecture is false.
  Importantly, **Round 27's own stated consequence was itself wrong and
  was corrected in Round 28**: the six witnesses were first read as
  showing `k >= 1`, but all six actually have `k = 0` — what broke was the
  reduction `#Z == k (mod 2)` (which secretly assumed an even-phase-
  displacement alphabet premise Round 26 had already refuted), not the
  `k=0` claim itself.
- **Downstream impact.** Isolated to the RR parity program (rounds
  21-28). `research/RR_NR6_IMPACT_ASSESSMENT.md` §1-2 traces exactly
  which lemmas fell and which survived; the literature 867 bound and the
  verified 872 upper bound are unaffected; NR6's status is explicitly
  unaffected (a separate question).
- **Source.** `research/RR_PARITY_CONJECTURE_REFUTATION.md`;
  `research/RR_NR6_IMPACT_ASSESSMENT.md`; `STATUS.md` rounds 21-28.
  Commits: `a61e85d` (Round 27), `4d9bdc7` (Round 28 correction).

### 5.2 "v1" short-root R1-completeness bug — [RF]

- **Original claim.** The Round-35/37 exhaustive Target-A driver
  (`src/search_rr_target_a_exhaustive.py::evaluate_edge`) treated every
  `R`-kind macro edge as terminal (never enqueue the child).
- **Why it failed.** That rule is only correct once already past R1
  (`r_count=1`). For a bare short root (`r_count=0`) the first legal `R`
  edge must instead be enqueued as an R1 child; the old code discarded it,
  so every pre-fix short-root statistic covers only the pre-R1 subspace.
- **Bug location.** `src/search_rr_target_a_exhaustive.py::evaluate_edge`;
  audited historical commit `abfcdca` (100,250-node `short_ell0` medium
  run).
- **Corrected statement.** Asymmetric rule: `r_count=0` -> create+enqueue
  R1 child; `r_count=1` -> test R2 boundary, don't enqueue; `r_count>=2`
  -> reject.
- **Downstream impact.** No pre-fix short-root frontier/terminal count may
  be cited as an exact-search result for any of the five short roots.
  Does not affect the 28-root long-root Q2 closure or the 18 known
  Target-B closures.
- **Source.** `research/RR_SHORT5_R1_COMPLETENESS_CORRECTION_CODEX.md`
  (Round 40). Commits: `d8600b9`, `e9ff19c`.

### 5.3 "v2" Target-A bug: `O > 25` prune wrongly applied — [RF]

- **Original claim.** The corrected (v2) short-root traversal pruned on
  `state.O > 25` before testing for a Target-A boundary.
- **Why it failed.** `O <= 25` is a Target-B completion coordinate, not
  part of the Target-A boundary definition; pruning on it silently
  discards legal Target-A-reachable states.
- **Exact counterexample.** Bare `short_ell0` root, macro depth 69, legal
  child `(P,O,D,Ndef,F,H)=(71,26,59,1,1,0)`: the legacy profile prunes it
  as `O_exceeded`; the correct Target-A-semantic profile accepts it.
- **Corrected statement.** Two hash-separated profiles: `target_a_semantic_v1`
  (correct) vs. `legacy_area_a_q2_comparison_v1` (audit-only). Checkpoint
  namespace bumped to `v3`.
- **Downstream impact.** The 100,250-node v2 medium run is marked
  `PREMATURELY_PRUNED_INVALID_FOR_TARGET_A_COVERAGE`.
- **Source.** `research/RR_TARGET_A_PRUNE_SCOPE_AUDIT_CODEX.md` (Round
  41); `outputs/rr_target_a_prune_registry.json`. Commits: `d90b69a`,
  `785ddab`.

### 5.4 "Hierarchy" macro-entry source-semantics bug, and 38,405 false Target-A positives — [RF]

- **Original claim.** The repair hierarchy evaluated Target-A's
  same-component/source-orbit predicates for an R2 macro edge `rot^ell;J`
  at the **macro-entry state**, reporting "38,406" macro-entry Target-A
  claims.
- **Why it failed.** For a rotation edge, the literal joint source after
  the rotation run can differ from the macro-entry state. A concrete
  fixture shows macro-entry state gives same-component=true while the
  correct literal joint-source state gives same-component=false, for the
  same trace.
- **Bug location.** `target_a_recognizer` (`pre_state` call sites),
  `geometry_failure_record`, `same_component_failure_record`,
  `hierarchy_for_r2`, `predicate_before_r2`, `repair_predicate`. Fixture:
  `tests/fixtures/rr_r2_literal_source_counterexample.json`.
- **Corrected statement.** `R2Source(rot^ell;J) = edge.run.state`, not the
  macro-entry state. Corrected replay of the fair `short_ell0` prefix (4
  subroots x 25,000 expansions): historical macro-entry Target-A claims =
  **38,406**; corrected literal same-component **failures** = **38,405**;
  corrected literal Target-A **hits** = **1** (proved left-S6-equivalent
  to known-18 class `short_ell0_33d70b4249b7`).
- **Downstream impact.** A correction of a capped prefix result only —
  does not itself establish or refute `L_6>=872`. Old v1 hierarchy
  artifacts are kept but explicitly labeled `INVALID_R2_SOURCE_SEMANTICS`.
- **Source.** `research/RR_R2_LITERAL_SOURCE_CORRECTION_CODEX.md` (Round
  48, commit `b09f1d5`); independent audit
  `research/RR_R2_SOURCE_SEMANTICS_CLAUDE.md` (commit `0266a55`, this
  project's own branch).

### 5.5 Over-scoped `true_phase_walk_capacity` — [RF]

- **Original claim.** Round 33 introduced `true_phase_walk_capacity` as a
  tighter bound on Target-B port availability; Rounds 33-35 used it more
  broadly for single-landing port-availability questions.
- **Why it failed.** The helper is sound only under a full-segment
  precondition (`Phi=0` in the capacity-potential sense of §3, an ell=5
  run visiting all six hexagon permutations); it is unsound for the
  single-landing question, where a joint only needs its own target
  permutation free, not the whole hexagon. Independent counterexamples on
  both sides of the project (root `long_found_142`: predicted capacity
  undercounted the real legal-edge count).
- **Bug location.** `true_phase_walk_capacity` helper; classified
  `SOUND_FOR_FULL_SEGMENT` only by the Round 38 firewall
  (`assert_full_segment_context` raises `CapacityPreconditionError`
  outside the full-segment precondition).
- **Corrected statement.** The generic (single-landing) interpretation is
  retracted; the original full-segment use stands. Replacement for
  single-landing bounding: an occupancy-independent universal port bound
  of 4, verified against all 1,398 known boundaries with zero violations,
  plus a helper-free re-audit of the 18 known Target-A boundaries.
- **Downstream impact.** Does not reopen the 18 historical Target-B
  boundary states; the helper-free re-audit reconfirms 0 remain open.
- **Source.** `research/RR_TARGET_B_18_BOUNDARY_REAUDIT_CODEX.md` (Round
  39, commit `9b345c4`, codex tree); `research/RR_CAPACITY_HELPER_SOUNDNESS_AUDIT.md`
  (Round 38, this project's own Claude branch — the firewall itself was
  authored there; the Codex tree has the related but distinct
  `research/RR_PHASE_CAPACITY_SOUNDNESS_CODEX.md`).

### 5.6 Stale v5/v6 checkpoint provenance loss — [RF] (bookkeeping bug, not a proved-result error)

- **Original claim (implicit).** v6 checkpoints written by the top-8
  continuation driver were assumed to carry their v6 wrapper (source
  checkpoint path/SHA, base expansion count, additional budget) through
  every subsequent atomic checkpoint rewrite.
- **Why it failed.** The bootstrap write includes the wrapper, but every
  subsequent write goes through the shared v5 writer, whose payload
  serializer is a whitelist emitting only v5-native fields — the first
  atomic rewrite silently drops the v6 wrapper, including a field the v6
  resume guard itself later requires.
- **Bug location.** `search_rr_short5_top8_continuation.py` (wrapper
  added at bootstrap only); `search_rr_short1_4_corrected_fair.py`
  (whitelist payload, atomic rewrite commits the omission).
- **Corrected statement.** Classified
  `AUXILIARY_PROVENANCE_NOT_CLOSED_UNDER_V5_CHECKPOINT_SERIALIZER`. All
  v5-native fields remain intact; only the v6-specific wrapper is lost
  after the first rewrite. The v6 driver must not be used to resume
  affected payloads.
- **Downstream impact.** No completed analysis/ledger result is
  affected — each is separately anchored to its v5 source SHA, and
  literal replay of the underlying data passed.
- **Source.** `research/RR_V6_PROVENANCE_LOSS_AUDIT_CODEX.md` (Round 52,
  commit `4792891`); `outputs/rr_v6_provenance_loss_audit.json`.

### 5.7 "144-Z3-events" bound — proof method retracted, numeric bound not disproven — [RF] (method) / [OPEN] (value)

- **Original claim.** A claimed law "`(720-visited)` decreases by exactly
  6 per move" was used to help ground a "<=144 Z3 events" pigeonhole-style
  bound.
- **Why it failed.** `extend()` actually advances `visited_count` by
  exactly **1** window per call; a macro edge of rotation length `ell`
  plus a terminal joint visits `ell+1` windows — state-dependent, with no
  general reason to equal 6. Separately (Round 59), the naive
  orbit-pigeonhole proof of "<=144 Z3 events" itself was found not proved:
  real orbit **revisits** occur (max observed Z3 count per ancestry = 36,
  with 6 exact revisit counterexamples).
- **Exact location.**
  `research/RR_SHORT_ELL2_R1_37_LOCAL_GLOBAL_FZ1_GAP_CLAUDE.md` §4;
  `research/RR_SHORT_ELL2_R1_37_FZ1_CANDIDATE_REACHABILITY_CODEX.md` §7
  (Round 59), verdict `NOT_PROVED_BY_ORBIT_PIGEONHOLE`.
- **Corrected statement.** Two separate, non-conflated bounds stand
  instead: (1) at most 144 Z3 events per branch — still asserted as an
  orbit-count fact (`ORBIT_COUNT=144`), though the naive pigeonhole proof
  route is downgraded to **[OPEN]**; (2) at most `HEX_COUNT x N = 720`
  genuine window-advancing moves of any kind per branch — this one is
  **[HP]**, a direct consequence of the finite 720-window no-repeat
  budget.
- **Downstream impact.** Confined to the `short_ell2_r1_37` FZ1 line. Both
  Stage-E 500,000-expansion continuations (seeds 3 and 6) hit their cap
  without resolving FZ1 reachability by search — bounded/incomplete, not
  an absence theorem. FZ1 was later closed for the 84-anchor family by the
  T4 argument in §7, which does **not** rely on the 144-Z3 bound at all.
- **Source.** `research/RR_SHORT_ELL2_R1_37_LOCAL_GLOBAL_FZ1_GAP_CLAUDE.md`
  (commit `2797e61`);
  `research/RR_SHORT_ELL2_R1_37_FZ1_CANDIDATE_REACHABILITY_CODEX.md`
  (Round 59, commit `bb3e9e1`).

---

## 6. The RR-short program: logical reduction, not a round log

The path from the early Target-A/B work to the current `short_ell2_r1_37`
T4 theorem is a chain of successive reductions, each closing off part of
the search space, not merely "more search." Round numbers/files are given
per step; the full chronological list is in the appendix (§15).

```
known Target-A boundaries (18, from rounds 29-34)
        |
        v
Target-B closure attempt on those 18
   -> 9 lose Target-B (R30) -> 8 (R31) -> 7 (R32) -> 0 open (R34, flow-first)
        |  [all 18 known Target-A boundaries closed w.r.t. Target B]
        v
five short roots identified as the open frontier (short_ell0..short_ell4)
   [R35-R38: envelope/resource-model/defect-theorem groundwork;
    v1 R-child completeness bug found+fixed (R40, see S5.2);
    v2 O>25 prune bug found+fixed (R41, see S5.3)]
        v
short-root searches (v3-v5, rounds 40-51)
   [v3 taxonomy + hierarchy macro-entry bug found+fixed (R43-48,
    38,405 false positives corrected to 1 real hit, see S5.4);
    v5 fair pilot across all 5 roots -> 439-child ledger]
        v
top-8 selection (round 51, from the 439-child ledger)
   [8 children selected as the highest-signal capped-incomplete branches]
        v
v6/v7 replay validation (round 52)
   [v6: fixed 167,820-expansion continuation of the top 8;
    v7: a replay PLAN only -- never executed as its own search, see S10]
        v
7/8 branch exhaustion
   [6 of 8 NATURALLY_EXHAUSTED, 2 CAP_REACHED_NONEMPTY_FRONTIER at v6;
    subsequent frontier analysis (R54) narrows the still-open branch(es)
    down to a single residual short root]
        v
short_ell2_r1_37 residual branch identified as the sole open branch
        v
22 frontier states (depths 47-88, R54 frontier analysis)
        v
9 exact subgraph closures + 13 unresolved (initial closure pass)
        v
all-13 pilot (rounds 55-56)
   [66,096 expansions across the 13 unresolved states;
    result: 7 EXHAUSTED_NO_BRIDGE, 6 remain INCOMPLETE;
    total remaining frontier after this pass: 84 states]
        v
7 additional closures + 6 survivors
   [the 6 surviving seeds: {236166, 12, 6, 3, 303321, 13} --
    these become the six immutable Stage-D checkpoints]
        v
Z2/Z3 bridge analysis (component-bridge derivation)
   [direct-Z2 lemma: R1-target orbit 91's phase-hexagon set
    {40,82,90,91,92} disjoint from hub's {0,1,4,6,8,9,18,24,96}]
        v
phase/watch-list analysis + dangerous-entry reduction (round 57)
   [196 abstract "dangerous" transition mechanisms enumerated over the
    complete depth-4 bounded graph; all require a prior component-changing
    Z3 -- T1-level result at this point, branch_wide_T4_proved=false]
        v
first component-changing Z3 search (Stage D, round 58)
   [full search of the 6-checkpoint corpus: 1,256,023 expansions,
    69,369-state frontier, 1,325,392 total nodes;
    first_component_change_witnesses = 0 across the whole corpus]
        v
C4 collision obstruction (rounds 59-60)
   [T2: all 253,537 observed first-component-Z3 attempts collide;
    T2a: the four hexagons {40,90,91,92} obstructed by root-fullness +
    monotonicity; C4 predecessor closure stabilizes inside the observed
    DAG (712,083 nodes) but is not yet a COMPLETE finite closure at this
    stage]
        v
hex-82 five-route reduction (round 61, first commit)
   [the only remaining gap: hexagon 82's five non-q91 routes
    (q42:p1, q78:p3, q82:p0, q83:p4, q128:p2); each shown to require
    q91:p2 registration, whose unique weight-2 predecessor is 245130,
    a window of hexagon 40]
        v
final T4 closure (round 61, h40-fullness follow-up + independent
Claude-side verification)
   [h40 full & non-terminal at 84/84 anchors -> q91:p2 unreachable ->
    T2b -> T2+ -> T3 -> T4, independently verified over the full
    1,325,392-node replay; see full statement in S7]
```

Each arrow is a **reduction of the open search space**, not a fresh
independent search: the all-13 pilot only searches the 13 states left open
by the prior closure pass; Stage D only searches the 6 seeds left open by
the all-13 pilot; the C4/hex82/T4 line only reasons about the 84-anchor
frontier produced by Stage D. This is why the final T4 theorem (§7) is
scoped exactly to "the 84 frozen Stage-D anchors and their exact
descendants" — that scope is the literal endpoint of this reduction chain,
not an arbitrary restriction.

---

## 7. The final verified r1_37 T4 theorem — the strongest current result

**`[T4][HP+EC+ER+IV]`**

**Exact scope.** `short_ell2_r1_37`; the 84 frozen Stage-D anchors and all
of their exact (literal-permutation, exact no-repeat) descendants; strictly
after R1 and strictly before any R2 event; exact no-repeat semantics only.
Nothing here generalizes past this scope (see §11).

### Direct Z2 obstruction

Orbit 91 (the fixed R1-target orbit for this branch) touches exactly the
hexagon set `{40,82,90,91,92}` across its five phases (from the fixed
`ORBIT_PHASE`/`HEX_POSITION` tables). The hub component's touched hexagon
set is `{0,1,4,6,8,9,18,24,96}`. These two sets are disjoint. A
non-abandoning weight-2 (`Z2`) transition's target orbit must already be
open (`new_orbit=False`); while `C_R1` consists of orbit 91 alone, the
only already-open orbit reachable from it is orbit 91 itself, so every
legal `Z2` fired from within `C_R1` can only touch hexagons in
`{40,82,90,91,92}`. Since that set is disjoint from the hub's hexagon set,
no single `Z2` move can union `C_R1` with the hub component. `[HP]`,
established four rounds before the final T4 round and unaffected since.

### Non-h82 C4 obstruction (T2a)

The other four hexagons `{40,90,91,92}` were shown obstructed by
root-fullness plus monotone occupancy: each is full
(`hex_masks[h]=0b111111`) at the relevant anchors, and occupancy bits are
monotone non-decreasing, so any route requiring a fresh visit into one of
these four hexagons collides with an already-visited window. `[EC+HP]`,
round 60.

### The h82 obstruction (T2b) — the closing case

Hexagon 82 is **not** full at most anchors (occupancy histogram
`{0:81, 2:1, 4:1, 63:1}` across the 84 anchors) — the naive "h82 is full"
framing is false, and this was explicitly recognized and rejected in
Codex's own occupancy-audit text. The real mechanism is cross-hexagon:

```
245130 --w2--> 513042 = q91:p2   (hexagon 40, window 1 --> hexagon 82, window 3)
```

`513042` is orbit 91's own phase-2 window, sitting in hexagon 82. Its
unique weight-2 predecessor (the engine has exactly one weight-2 move
among 550 total, and the move's action is a bijection on the
720-permutation space, so every target has exactly one weight-2
predecessor) is `245130`, a window of hexagon 40 — a *different* hexagon
from the target's own.

Verified anchor facts, recomputed directly from the 84 raw anchor records
(not summary flags):

| metric | value |
|---|---|
| h40 registered in incidence graph | 84/84 |
| h40 FULL (`hex_masks[40]=63`) | 84/84 |
| literal `245130` already visited | 84/84 |
| current endpoint = `245130` | 0/84 |

Monotonic occupancy (bits only ever OR-set, never cleared) plus exact
no-repeat (`extend()` rejects any transition targeting an already-visited
window) together give: once `245130` is visited and no anchor is currently
positioned there, no descendant can ever again be positioned there, so the
unique weight-2 move into `513042` (`q91:p2`) can never fire in any
descendant. This is a specific instance of the general VNTS lemma, §8.

**The five routes this closes:** `q42:p1, q78:p3, q82:p0, q83:p4, q128:p2`
— the five hexagon-82 rotation words other than `q91:p2` itself. Each was
independently confirmed to require hexagon 82 to already be part of
`C_R1` (i.e. to require `q91:p2` registration) before its own Z3 could
count as extending `C_R1` — verified directly from the analyzer's source
(`required_C_R1_relation` field, `outputs/rr_short_ell2_r1_37_hex82_routes.json`
on the Codex tip), not merely asserted in prose.

**Independent replay** (`verify_rr_short_ell2_r1_37_hex82_closure.py`,
read in full and its logic traced by hand):

- **1,325,392 nodes** replayed across the six immutable Stage-D
  checkpoints (1,325,308 non-root parent-to-child macro edges).
- `q91_p2_registered_nodes = 0` across the entire corpus.
- `hex82_in_r1_component_nodes = 0` across the entire corpus — computed
  via the *general* union-find `component_summary` query (not a shortcut
  reading only q91's own mask bit), which is what makes this check able to
  catch any alternative registration mechanism (a different Z3, an
  alternate phase, an alternate incidence path, an earlier component
  merger), not merely the one specific route Codex described in prose.
- M1 (orbit/phase macro-target matches) = 155,538; M2 (structural state
  matches) = M3 = M4 (exact legal non-colliding C4) = M5 (FZ1 witnesses)
  = 0.
- Hexagon-82's full rotation table was independently recomputed from
  scratch (`core.orbit(core.ROT_REPS[82], core.SIGMA)`), confirming
  exactly five non-q91 routes and no sixth route omitted.

### The implication chain

```
T2b (all five h82 routes exact-unreachable)
  -> T2+ (complete C4 prerequisite space closed in the 84-anchor family:
          h82's five routes plus the {40,90,91,92} obstruction (T2a)
          jointly exhaust every candidate incidence into orbit 91's
          hexagon set)
  -> T3  (no first component-changing Z3 possible in this family, since
          any such Z3 must target a hexagon in that set, and T2+ closes
          all of them)
  -> T4  (no pre-R2 bridge possible: any pre-R2 bridge either changes
          C_R1's membership when it fires -- requires a prior
          component-changing Z3, blocked by T3 -- or it does not, so it
          must itself be a direct bridge from single-orbit C_R1, blocked
          by the direct-Z2 lemma above. These two cases are exhaustive
          and mutually exclusive by definition.)
```

**Reproducibility.** Report
`research/RR_SHORT_ELL2_R1_37_HEX82_C4_CLOSURE_CODEX.md` +
`RR_SHORT_ELL2_R1_37_H40_FULLNESS_AUDIT_CODEX.md` (codex tip, commit
`1f9efff0809c47e7ca1857ed6c7734c20e78f081`); independent verification
`research/RR_SHORT_ELL2_R1_37_T4_FINAL_VERIFICATION_CLAUDE.md` +
`outputs/rr_short_ell2_r1_37_t4_final_verification_claude.json` (this
project's Claude branch, end token `CLAUDE_T4_VERIFIED`). Both the commit
and all 14 referenced artifact files were independently hash-verified
against the remote branch before the theorem was accepted as verified.

---

## 8. The generic VNTS lemma

**`[HP]`** (engine-universal core) **+ `[EC]`** (per-branch instantiation)

> **Lemma (Visited Non-Terminal Source, VNTS).** Let `tau` be any literal
> permutation window that is the target of the engine's unique weight-2
> move, and let `sigma` be its unique weight-2 predecessor. Let `A` be a
> finite family of frozen `ExactState` anchors. If (H1) `sigma` is visited
> at every anchor in `A`, and (H2) no anchor in `A` has current endpoint
> equal to `sigma`, then no exact descendant of any anchor in `A` can ever
> have `sigma` as its current endpoint, and the weight-2 move into `tau`
> can never fire in any descendant of `A`.

**Engine-universal assumptions.** `extend()` copies occupancy and only
ever OR-sets bits (never clears); `extend()` rejects any transition
targeting an already-visited window; the engine has exactly one weight-2
move among 550 total, and its action is a bijection on the
720-permutation space, so every target has a unique weight-2 predecessor.

**Per-anchor assumptions.** H1 and H2 above — both finite, directly
checkable facts about a specific frozen anchor family, not engine laws.

**Full-Hex corollary.** If an entire hexagon `h` (all six windows) is full
and no anchor's endpoint lies in `h`, VNTS applies simultaneously to all
six windows of `h` as sources — a coarser, batched certificate.

**Cross-hexagon use, and why h82 is not itself a fullness obstruction.**
VNTS never requires the *target's own* hexagon to be full — only that
*some* hexagon, wherever the target's unique predecessor happens to live,
is full-and-non-terminal. The `short_ell2_r1_37` h82 case is exactly this:
hexagon 82's own occupancy is irrelevant and mostly empty (histogram
`{0:81,2:1,4:1,63:1}`); the obstruction comes entirely from hexagon 40 (a
different hexagon) being full and non-terminal. Framing h82 as an
"exceptional case" was an artifact of implicitly expecting source and
target hexagon to coincide; under the general lemma this cross-hexagon
pattern is not exceptional at all.

**What remains unverified about generalizing this to other children.**
Whether the hub's touched-hexagon set is engine-universal (fixed for any
choice of R1-target orbit) or itself branch-specific is explicitly left
open — not assumed either way. A future branch inherits T4 automatically
only by supplying the seven-item finite certificate checklist in
`research/RR_SHORT_T4_GENERIC_THEORY_CLAUDE.md` §7 (hub disjointness,
full candidate enumeration, per-candidate discharge, anchor ledger,
full-corpus monotonicity replay, full-corpus general
component-membership replay) — none of which has yet been attempted for
any branch other than `short_ell2_r1_37`.

**Reproducibility.** `research/RR_SHORT_T4_GENERIC_THEORY_CLAUDE.md` +
`outputs/rr_short_t4_generic_theory_claude.json` (this project's Claude
branch, end token `CLAUDE_T4_GENERIC_THEORY_READY`).

---

## 9. Evidence grading

Every major claim in this document carries one or more of these tags.
Bounded observations (`[BO]`) are never described as proof.

| tag | meaning |
|---|---|
| `HP` | hand proof |
| `EC` | exact complete finite certificate |
| `ER` | exact exhaustive replay |
| `IV` | independent verification |
| `BO` | bounded observation |
| `HE` | heuristic / exploratory |
| `RF` | refuted / invalid |
| `OPEN` | unresolved |

Example: `[T4][HP+EC+ER+IV]` — the T4 theorem combines a hand-proof
implication chain, exact finite certificates (the 84-anchor h40 ledger),
an exact exhaustive replay (1,325,392 nodes), and independent verification
by a second analyst (this project's Claude branch) before being accepted.

---

## 10. Quantitative ledger

All figures below are copied verbatim from the cited JSON's own top-level
field names — field names are not relabeled, so "expanded," "nodes," and
"frontier" below mean exactly what that file calls them, and are not
interchangeable. All files are on the Codex tip
(`codex/round-r1-37-hex82-t4`, commit `1f9efff`) unless noted.

| stage | file | child / branch count | expansion count | replay-node count | R2 / M1 count | frontier count | exhausted / capped | bridge count | Target A/B count |
|---|---|---|---|---|---|---|---|---|---|
| v5 top-8 pilot (source) | `rr_short5_child_outcomes.json` | children=439 | total_expansions=596537 | N/A | N/A | N/A | NATURALLY_EXHAUSTED=326, CAPPED_INCOMPLETE=113 | N/A | N/A |
| v6 endpoint (top-8 ledger) | `rr_short5_top8_official_ledger.json` | top_children=8 | additional_expansions=167820 | N/A | r2_literal_replays=99438 | N/A | naturally_exhausted=6, capped_nonempty=2 | bridge_template_occurrences=0 | literal_target_a_hits=0, target_b_survivors=0 |
| v7 continuation (v6-continuation study; **true v7 replay is plan-only, never executed**) | `rr_short5_top8_continuation_verified.json` | branches=8 | N/A | N/A | r2_paths=99438 | N/A | NATURALLY_EXHAUSTED=6, CAP_REACHED_NONEMPTY_FRONTIER=2 | bridge_template_matches=0 | literal_target_a_hits=0 |
| v7 replay plan | `rr_top8_v7_replay_manifest.json` | per_capped_child=2 | N/A | N/A | N/A | N/A | status=PLAN_ONLY_NO_SEARCH_STARTED | N/A | N/A |
| all-13 pilot | `rr_short_ell2_r1_37_all13_pilot_results.json` | 13 states | expansions=66096 (cap 130000) | N/A | N/A | frontier_size=84 | EXHAUSTED_NO_BRIDGE=7, INCOMPLETE=6 | bridges=0 | literal_Target_A=0, Target_B_survivors=0 |
| depth-4 graph | **not found** in the RR-short line on either tree (the only "depth4"-named file belongs to the unrelated, earlier A2 program) | — | — | — | — | — | — | — | — |
| Stage D (first_component_z3) | `rr_short_ell2_r1_37_first_component_z3_results.json` | 84 start states, 6 seed branches | expansions=1256023 | N/A | N/A | frontier=69369 | status=FIRST_COMPONENT_Z3_SEARCH_INCOMPLETE, stage=D | N/A | Target_A=0, Target_B=0, first_component_change_witnesses=0 |
| Stage E (FZ1 candidate-distance) | `rr_short_ell2_r1_37_stage_e_verified.json` | 2 branches (seeds 3, 6) | expanded_nodes_replayed=1000000 | nodes_replayed=1010043 | R2_candidates_rechecked=487846 | frontier_replayed=10043 | status=STAGE_E_INCOMPLETE | N/A | Target_A_rechecked=0, Target_B_rechecked=0 |
| C4 ledger / collision | `rr_short_ell2_r1_37_c4_verified.json` | 6 branches | N/A | N/A | N/A | N/A | theorem_level="T2: all observed C4 states collide; T2+ not established" | N/A | C4_attempts=253537, exact_signatures=86, left_s6_canonical_signatures=17 |
| C4 predecessor closure | `rr_short_ell2_r1_37_c4_predecessor_closure.json` | N/A | N/A | observed_predecessor_closure_nodes=712083 | N/A | N/A | closure_stabilized_inside_observed_DAG=true; complete_finite_C4_prerequisite_closure=false | N/A | N/A |
| final 1,325,392-node replay (hex82/T4 closure) | `rr_short_ell2_r1_37_hex82_verified.json` | 6 seed branches | full_replay.expanded=1256023 | **full_replay.nodes=1325392** (monotone_macro_edges_checked=1325308) | M1_total=155538 (M2-M5=0) | full_replay.frontier=69369 | N/A | N/A | N/A |

Gaps found (reported rather than guessed at): no `depth4`-named JSON
exists anywhere in the RR-short line; v7 was **planned but never
executed** as its own search — what is often informally called "v7"
elsewhere is actually the v6-continuation study.

---

## 11. What is proved now? / What is NOT proved?

### What is proved now?

**A. Unconditional / project-independent facts.** `L(6)>=867`
(literature, cited); `L(6)<=872` (explicit witness, verified in this
repo); `L(1..4)` proved exactly by exhaustive search in this repo;
foundational E-orbit/hexagon/cover-theorem group theory (§4).

**B. NR6-conditional results.** Everything in the RR/short-root program is
conditional on NR6 (§2) — this includes items C, D, E below in their
entirety.

**C. RR-short family results.** The `18 -> 0` known Target-B closure
(§4.10); the direct-Z2 lemma (orbit 91's hexagon set disjoint from the
hub's, §7); Stage-D's `first_component_change_witnesses = 0` over
1,256,023 expansions (§10); the C4 collision observation (T2, 253,537
attempts, all collide) — note T2 itself is `[BO]`-flavored (an observed,
not yet exhaustively-certified-complete, collision count) until combined
with the exact finite closures of T2a/T2b.

**D. `short_ell2_r1_37`-specific T4 theorem.** `[T4][HP+EC+ER+IV]`, §7 —
the strongest result in the project. Scope: the 84 frozen Stage-D anchors
and their exact descendants, post-R1/pre-R2, exact no-repeat semantics,
this one branch only.

**E. Generic VNTS lemma.** `[HP]`, §8 — a reusable proof template, stated
and proved generically, but **not yet applied to any branch other than
`short_ell2_r1_37`**.

### What is NOT proved?

- **`L(6) >= 872` unconditionally.** Not proved. Only the literature's 867
  is unconditional.
- **`L(6) = 872`.** Not proved, not close to proved.
- **NR6 universality** (that NR6 is even true). Not addressed by this
  project at all — an explicitly separate open question per this
  project's own framing.
- **All 439 short children closed.** Not proved. Only
  `short_ell2_r1_37` has a completed T4 argument; the other 431 (7 of the
  original top-8 minus this one, plus the 431 not selected into top-8) are
  either naturally exhausted at v6 (6 of the top-8, without a T4-style
  theorem being needed since they terminated) or entirely unexamined at
  this level of rigor.
- **All short roots T4.** Not proved. T4 is proved for exactly one
  residual branch of one of five short roots.
- **All Target A eliminated globally.** Not proved. Only the 18
  originally-known Target-A boundaries were closed against Target B; the
  1,398 later-found boundaries (Rounds 35-37) were never run through that
  ledger (§4.10).
- Any claim that the RR-short program as a whole "closes" the search for
  a length-873-or-shorter obstruction. It does not; it closes one specific
  finite family within one specific branch.

---

## 12. Remaining open problems, ranked

1. **Generalize the VNTS/T4 template to the other top-8 children.** This
   is the most immediately actionable next step: the certificate
   checklist in `RR_SHORT_T4_GENERIC_THEORY_CLAUDE.md` §7 is explicit
   about what's needed. Matters because it is the only currently-known
   path to extending T4-level rigor beyond a single branch.
2. **Determine hub-component universality vs. branch dependence.**
   Explicitly left open in §8; the direct-Z2 lemma's disjointness
   argument depends on it. Matters because every future branch's T4
   attempt needs to know whether this is a free fact or a per-branch
   certificate obligation.
3. **Apply the automatic certificate checklist to sufficiently-covered
   short children** (the 6 that naturally exhausted at v6, plus any of
   the 431 non-top-8 children with enough existing search depth). Matters
   as the most direct way to grow the number of T4-proved branches without
   new search infrastructure.
4. **Resolve the remaining capped/incomplete children** (2 of the top-8
   were `CAP_REACHED_NONEMPTY_FRONTIER` at v6; the 431 non-top-8 children
   are largely unexamined at this depth). Matters for eventually claiming
   completeness over the full 439-child corpus, which T4-for-one-branch
   does not by itself provide.
5. **Bridge from RR-short results to a wider NR6 lower-bound proof.** Even
   a T4 theorem for all 439 children would only be a statement inside the
   RR/`ExactState` model; connecting that back to an actual `L(6)` bound
   requires either establishing NR6 or a separate argument that doesn't
   need it. This is the largest, least well-defined open item.
6. **Ultimately establish `k+N+H >= 5`** under the project's own full
   coordinate scope (`L = 867+(k+N+H)`, §3) — the actual quantity that
   would need to be shown to raise the bound to 872. Nothing in this
   project currently constrains `k+N+H` globally; the Cover theorem (§4.1)
   gives `k+N+H`-adjacent partial leverage (`5S+4F>=120`) but not this
   bound directly.

---

## 13. Novel contributions / discoveries (conservative)

The following appear original within this project. **No literature
priority search has been performed; "original within this project" does
not mean "first in the world."**

- The explicit parity/`k>=1` counterexample and its own subsequent
  self-correction (§5.1) — original within this project; external
  priority not established.
- The macro-entry vs. literal-joint-source-semantics false-positive
  diagnosis (38,405 figure, §5.4) — original within this project;
  external priority not established.
- The helper-free re-audit closing the known-18 Target-A boundaries
  against Target B without `true_phase_walk_capacity` (§4.10, §5.5) —
  original within this project; external priority not established.
- The `short_ell2_r1_37` branch-local T4 theorem (§7) — original within
  this project; external priority not established.
- The generic VNTS lemma and its Full-Hex / cross-hexagon corollaries
  (§8) — original within this project; external priority not established.
- The recognition that the h82 case is a cross-hexagon VNTS instance
  rather than a special case (§8) — original within this project;
  external priority not established.
- The **Φ / unique-bridge invariant** `6r <= 11 - Phi` and its corollary
  that at most one hexagon of the incidence forest ever has degree 2,
  hence at most one E-orbit pair is ever co-component and that pair is
  frozen once created — plus the σ-adjacency admissibility lemma
  (two co-hexagonal orbits admit a weight-3 transition iff their ports
  are rotation-neighbours, 1,800/1,800 exhaustive) and the resulting
  `root_ell ∈ {1,2,3}` closure of 1,415 of the 1,818 Round-68 residual
  anchors (Round 69, Claude branch;
  `research/RR_SHORT_G3_COCOMPONENT_INVARIANT_CLAUDE.md`), completed in
  Round 69b by the ELL4 unique-bridge Target-A normal form
  (`research/RR_SHORT_ELL4_UNIQUE_BRIDGE_NORMAL_FORM_CLAUDE.md`), which
  closes the remaining 403 `root_ell = 4` anchors and identifies the
  family's only three same-component R2 boundaries as known-18
  `ell4_P2_*` — so the 24 residual families contribute **0 new Target-A
  classes** at Q2 scope. Original within this project; external priority
  not established. **Scope: this
  is a Q2-level result — it consumes `Phi >= 0`, i.e.
  `remaining_window_capacity_prune`, which the committed `is_target_a`
  enforces but which is not available for the pure Q1 question.**
- The computational certificates themselves (the 1,325,392-node exact
  replay, the 84-anchor h40 ledger, the finite backward-closure
  H0-H5 classification) — original within this project as artifacts;
  external priority not applicable (these are project-specific
  computations, not mathematical claims with independent prior art to
  check).

---

## 14. Reproducibility map

| result | report | raw data | independent verification | verifier source | commit / tree | status |
|---|---|---|---|---|---|---|
| 439-child v5 ledger | `research/RR_SHORT5_CORRECTED_PILOT_CODEX.md` (codex) | `outputs/rr_short5_child_outcomes.json`, `rr_short5_child_classes.json` (codex) | `outputs/rr_short5_v5_proof_significance_claude.json` (Claude branch) | `src/verify_rr_short5_corrected_pilot.py`, `verify_rr_short5_search.py` | codex_tip / Claude branch (separate) | `[BO]` significance analysis, not exhaustive |
| Top-8 selection / v6 endpoint | `research/RR_SHORT5_TOP8_FINAL_STATUS_CODEX.md` | `outputs/rr_short5_top8_official_ledger.json` | `outputs/rr_short5_v6_endpoint_verification_claude.json` (end token `CLAUDE_V6_ENDPOINT_VERIFIED`) | `src/analyze_rr_short5_top8_completed.py` | codex_tip / Claude branch | `[IV]` verified |
| v7 / "7-of-8" exhaustion claim | `research/RR_TOP8_V7_REPLAY_PLAN_CODEX.md` | `rr_short5_top8_continuation.json`, `..._verified.json`, `rr_top8_v7_replay_manifest.json` (**plan-only**) | `outputs/rr_top8_7_of_8_claims_claude.json` (end token `CLAUDE_TOP8_7_OF_8_ANALYSIS_READY`, flags v7 as unverified) | `search_rr_short5_top8_continuation.py`, `prepare_rr_top8_v7_plan.py` | codex_tip / Claude branch | `[BO]`, v7 itself never run |
| all-13 pilot | `research/RR_SHORT_ELL2_R1_37_ALL13_PILOT_CODEX.md` | `rr_short_ell2_r1_37_all13_pilot_results.json`, `..._bridge_ledger.json` | `outputs/rr_short_ell2_r1_37_all13_pilot_verification_claude.json` (end token `CLAUDE_ALL13_PILOT_VERIFIED`); codex's own `..._all13_verified.json` (verified=true) | `search_..._all13_pilot.py`, `verify_..._all13_pilot.py` | codex_tip / Claude branch | `[IV]` verified |
| Stage-D component-Z3 search | `research/RR_SHORT_ELL2_R1_37_FIRST_COMPONENT_Z3_CODEX.md` | `rr_short_ell2_r1_37_first_component_z3_results.json`, `..._witnesses.json` (0 witnesses) | `outputs/rr_short_ell2_r1_37_first_component_z3_theory_claude.json` (end token `CLAUDE_FIRST_COMPONENT_Z3_THEORY_READY`); codex's `..._component_change_verified.json` (verified=true, T1+) | `search/verify_..._first_component_z3.py` | codex_tip / Claude branch | `[ER]` Stage D, `[BO]` re: reachability beyond corpus |
| C4 collision obstruction | `research/RR_SHORT_ELL2_R1_37_C4_COLLISION_OBSTRUCTION_CODEX.md` | `rr_short_ell2_r1_37_c4_collision_ledger.json`, `..._predecessor_closure.json` | `outputs/rr_short_ell2_r1_37_c4_collision_theory_claude.json` (end token `CLAUDE_C4_COLLISION_THEORY_READY`, flags contradictions with Round 59/Stage-E claims); codex's `..._c4_verified.json` (verified=true, T2 only) | `analyze/verify_..._c4_collision.py` | codex_tip / Claude branch | `[BO]` at T2, `[EC]` for T2a specifically |
| hex82 5-route closure / final replay | `RR_SHORT_ELL2_R1_37_HEX82_C4_CLOSURE_CODEX.md`, `H40_FULLNESS_AUDIT_CODEX.md` | `rr_short_ell2_r1_37_hex82_routes.json`, `..._mitm.json`, `..._occupancy_audit.json`, `..._backward_closure.json` | `rr_short_ell2_r1_37_hex82_theory_claude.json` (`CLAUDE_HEX82_PARTIAL`, flagged a gap) superseded by final `..._t4_final_verification_claude.json` (`CLAUDE_T4_VERIFIED`), which itself supersedes the interim `..._t4_verification_claude.json` (`REMOTE_DATA_INSUFFICIENT`, written when the round-61 commit was not yet fetchable); codex's `..._hex82_verified.json` (verified=true) | `analyze/verify_..._hex82_closure.py`, `test_..._hex82_closure.py` | codex_tip commit `1f9efff` / Claude branch | `[T4][HP+EC+ER+IV]` |
| Final T4 theorem | claim lives inside the two hex82 markdown files above (no separate `..._T4_...CODEX.md` file exists) | same hex82 outputs (no separate "t4" JSON on the Codex side) | `outputs/rr_short_ell2_r1_37_t4_final_verification_claude.json` (author: this project's Claude branch, end token `CLAUDE_T4_VERIFIED`, confirms head `1f9efff` and all 14 referenced files/hashes) | analytical cross-check against engine tables (no standalone script) | codex_tip commit `1f9efff` / Claude branch | `[T4][HP+EC+ER+IV]` |
| ELL4 unique-bridge Target-A normal form, Round 69b | `research/RR_SHORT_ELL4_UNIQUE_BRIDGE_NORMAL_FORM_CLAUDE.md` (Claude) | same Round-68 corpus; plus `outputs/rr_target_a_known18_regression.json` and `outputs/rr_target_b_18_boundary_corrected_ledger.json` (commit `9b345c4`) | `outputs/rr_short_ell4_unique_bridge_normal_form_claude.json` | `src/analyze_rr_cocomponent_invariant.py` §7 | Claude branch | `[HP]`+`[EC]`+`[IV]`; **Q2-scope only** |
| Φ / unique-bridge invariant, Round 69 | `research/RR_SHORT_G3_COCOMPONENT_INVARIANT_CLAUDE.md` (Claude) | Round-68 residual corpus supplied by the user as three JSON parts (`payload_sha256 eae160b9…`, `source_round62_sha256 5e8b9650…`); **not present in any git ref at time of writing** | `outputs/rr_short_g3_cocomponent_invariant_claude.json` | `src/analyze_rr_cocomponent_invariant.py` (runs standalone; `--corpus` optional) | Claude branch | `[HP]` T1/T2/T3/T5/T6/T8, `[EC]` T4/T7, `[BO]` the 960k-node probe; **Q2-scope only (see §13)** |

Prefer the currently-verified remote commit (`1f9efff0809c47e7ca1857ed6c7734c20e78f081`
on `codex/round-r1-37-hex82-t4`) over any historical local-only reference
when reproducing the T4 result specifically.

---

## 15. Research timeline appendix

Full commit chain (single linear history from `7dce52e` "Initial commit"
through `codex/round-r1-37-hex82-t4`'s HEAD, confirmed via
`git log --oneline --reverse`):

| round(s) | headline event | commit |
|---|---|---|
| 1-9 (unlabeled early rounds) | E-orbit/hexagon foundations, J-branch discovery and closure attempts, capacity-obstruction proof | `0626f9c`..`d72520b` |
| 10-20 | Unique weight-2 move proof, RR same-component<=>chaining, Unique Hub Hexagon lemma, Hub Touch Count<=2, corpus-completeness correction | `9b754f4`..`4c8b8ad` |
| 21-28 | Preparation-parity conjecture proposed, then refuted (§5.1), corrected identity | `e775b1b`..`4d9bdc7` |
| 29-34 | Terminal normal form, Target B defined, known-18 Target-A ledger closed to 0 (§4.10) | `129d73a`..`d664019` |
| 35-38 | Target A search rebuilt (+1,398 boundaries), capacity-helper firewall (§5.5), five short roots identified as still-open | `d07d267`..`232718e` (Claude branch), `aeafd1c`..`9b345c4` (codex) |
| 40 | v1 R1-completeness bug found+fixed (§5.2); short-root traversal corrected | `abfcdca`, `d8600b9`, `e9ff19c` |
| 41-42 | v2 `O>25` prune bug found+fixed (§5.3) | `d90b69a`, `785ddab` |
| 43-48 | v3 taxonomy; hierarchy macro-entry bug found+fixed, 38,405 false positives corrected (§5.4) | `24002fd`..`b09f1d5` |
| 49-51 | Corrected short-root ledger; v5 fair pilot; 439-child ledger; top-8 selection | `1f3d11a`..`dfc314f` |
| 52-54 | v6 endpoint frozen; v6/v7 provenance-loss bug found (§5.6); frontier analysis narrows to `short_ell2_r1_37` | `06dae7c`..`fae8ded` |
| 55-56 | all-13 pilot planned and run: 7 closed, 6 survive, 84-state frontier | `c394624`, `e280d32` |
| 57 | Dangerous-entry realizability audit: 196 mechanisms, T1-level | `6811132` |
| 58 | Stage D: full first-component-Z3 search over 6 checkpoints, 1,325,392 nodes | `9342018` |
| 59 | FZ1 provenance audit; 144-Z3 bound proof method retracted (§5.7); bounded Stage E | `bb3e9e1` |
| 60 | C4 collision obstruction: T2 (253,537 collisions), T2a (four-hexagon closure) | `2b3fb8f` |
| 61 | Hex-82 five-route closure (T2b); h40-fullness follow-up audit; T4 asserted | `19d484b`, `1f9efff` |
| 61 (this project's Claude branch) | Independent T4 verification (`CLAUDE_T4_VERIFIED`); generic VNTS theory | this branch, commits `3f24a49`, `f7a7211` |
| 62-68 (Claude branch) | Master status document; G3 residual theory; Ω projection soundness/monotonicity/termination; Round-68 1,818-anchor corpus analysis; singleton `short_ell1_r1_94:frontier:76` resolved as generic | this branch, commits `2730c99`, `ab51db1`, `c4eaff9`, `f47a24a`, `af1f57a`, `eb7fc72`, `3370be4` |
| 69 (Claude branch) | Φ / unique-bridge invariant `6r <= 11 - Phi`; σ-adjacency admissibility lemma; 1,415 of 1,818 residual anchors permanently closed; 960k-node bounded falsification probe (3 same-component witnesses, all `root_ell = 4`) | this branch, `research/RR_SHORT_G3_COCOMPONENT_INVARIANT_CLAUDE.md` |
| 86 (Claude branch) | **Phase-chain: closure 0, ceiling 18; two Codex corrections accepted.** The (orbit, phase) table has G5_phase out-degree exactly 2 (1,440 edges) and Gshort_phase 15, because at ell = 5 the joint w3:120 is same-orbit in 720/720 cases while w3:201 and w3:210 are other-orbit in 720/720. The engine confirms a Z3 opening leaves NO phase freedom: the new endpoint is the joint target itself and the landing port is the registered port. But the only ell = 5 same-orbit moves are E^1 (+1, cost 0) and E^2 (+2), and E^1 alone generates the whole 5-cycle, so under any sound over-approximation the phase correlation is entirely erased and the relation collapses to orbit level. Two-step chains drop 80% (14,400 -> 2,880) if repair is forbidden, and 0% if it is not. An adversarial ceiling with repair banned outright (deliberately unsound) closes only **18 states (0.27%)**, all in the c = 5 band, so adding global occupancy to block the collapse cannot be worth the cost. Corrections accepted: the <=2 lemma proof now uses the global pass count P = 120 + F = 121, and the minimum-exception histogram is {0: 6396, 1: 231, 2: 17, >=3: 13} -- my 147/101 split came from a real bug (solve() returned at the first cover solution with e <= maxexc), though the 13 closures were complete enumerations and stand | this branch, `research/RR_PHASE_CHAIN_CLAUDE.md` |
| 85 (Claude branch) | **2-exception budget: 13 closed -- the first non-zero orbit-level payoff since Round 80.** Round 84's lemma is restated with its true scope and reproved: F = 1 forbids future abandonment, so a pass entering a fresh hexagon must fill it and depart with ell = 5, so no new partial hexagon is ever created, so the only edges that can depart with ell < 5 are the current pass and the fragment repair -- **at most two, over ALL future macro edges**, which makes spending the budget on opening edges only a safe relaxation. G5 (ell = 5) has 1,440 edges and out-degree 10 against the full Z3 relation's 7,920 and 55, a 5.5x sparsening, while Gshort alone already equals the full Z3 relation. The zero-exception diagnostic fails only 261 states; the sound <=2 test returns **248 SAT, 13 UNSAT, 0 UNKNOWN**, with minimum-exception histogram {0: 6396, 1: 147, 2: 101, >=3: 13}. The 13 closed states are extreme instances whose slack-cover admits only 1-4 solutions; an independent reimplementation of min_exceptions and a non-MRV re-decision both agree with 0 disagreements. Residual **6,644** | this branch, `research/RR_TWO_EXCEPTION_CLAUDE.md` |
| 84 (Claude branch) | **Z3-only generation: closure 0; orbit-level generation exhausted.** The Z3-only fresh-opening relation is IDENTICAL to Round 81's generic 4-joint relation -- 7,920 edges, out-degree 55, one SCC, verified as per-orbit set equality rather than equal counts, with the weight-2 edges a strict subset -- so Round 83's 'every future opening must be a Z3' is invisible at orbit level. Proved the generation-necessity equivalence: the selected set S can be opened in some legal order iff every member is reachable from the open set A INSIDE the induced graph G[A u S], which is strictly stronger than full-graph reachability and was never tested before. Stage B closed 0 (the Z3 closure reaches every cover candidate in every state); 6,181 states admit a cover inside the one-step image of A, so the induced condition holds trivially; the exact joint cover+generation solve on the remaining 476 returned 476 SAT, 0 UNSAT, 0 UNKNOWN over 170,250 nodes, examining exactly 476 cover solutions -- the first cover found was induced-reachable every time. A sound derived lemma is recorded but unexploited: with F = 1 and the Round-76/78 pass count, at most two future macro edges can have ell < 5, and the ell=5 Z3 relation is 5.5x sparser (out-degree 10) -- yet its full closure still reaches every candidate, so even that closes 0 | this branch, `research/RR_Z3_GENERATION_CLAUDE.md` |
| 83 (Claude branch) | **Fragment repair: no payoff; blocked-w2 lemma PROVED.** All 6,657 residual states carry F = 1, so no further abandonment is legal and no new fragment can be created -- fragment creation requires an abandonment. The remaining joint alphabet is exactly {rotation, Z2, Z3, R}, every remaining orbit opening must be a Z3 at dNdef = 0, and all 144 orbits admit a Z3 opening (56 source orbits each), so M_def = 0 for every state and the payoff gate stopped the round at closure 0. The round's product is foundational instead: `N_exceeded_monotone` is a Q1-SAFE prune used by every search here and rested on a blocked-w2 lemma that this repo cited from prior work and recorded in src/analyze_j_completion.py as 'a bounded empirical check, not a proof'. It is now proved -- exhaustively `t = E(sigma(p'))`, so the w2 target shares the blocking window's E-orbit one phase on, and the no-repeat rule forces a visited blocker to have been a registered joint target, making the fresh-orbit case impossible. Hence dNdef >= 0 on every legal macro joint and the prune is sound. Confirmed by 0 occurrences in 2.6M macro edges and pinned by tests/test_blocked_w2_lemma.py | this branch, `research/RR_FRAGMENT_REPAIR_CLAUDE.md` |
| 82 (Claude branch) | **Port occupancy / E^1 phase repair: no payoff, with a measured ceiling of 13.** Literal E^1/E^2 availability taken from the engine's own no-repeat predicates: 448 of 6,657 states cannot move phase at all, the maximal consecutive E^1 chain is 4 (Round-77 cross-check; identical with and without the Area-A prune, so the closure is decided purely by no-repeat), and 45 states have E^1 blocked but E^2 available. From a pinned phase closure only 4-54 of a ~130-orbit candidate family are openable -- a genuine restriction. **Closure 0, 0 UNKNOWN.** Decisive measurement: a deliberately unsound strengthening forbidding ALL phase repair would close only **13 of 6,657**; with the true phase closure, **1**. So E^1 is not the bottleneck this time -- the predicate is: a first-open test closes only when every openable orbit is cover-incompatible, and ~90% of orbits are individually cover-compatible because SLACK-COVER constrains K-subsets rather than single orbits. First-open tests are exhausted at orbit and (orbit,phase)+occupancy level alike | this branch, `research/RR_PORT_OCCUPANCY_CLAUDE.md` |
| 81 (Claude branch) | **Cover-compatible orbit ordering: no payoff; orbit-level ordering exhausted.** A maximally conservative opening relation (all 5 phases x 6 rotation lengths x 4 joints, every excluded pair justified by exhaustion over the fixed group action rather than search absence, and `w2:10` retained because a weight-2 joint into a fresh orbit is a legal engine transition) reproduces Round 75's 7,920 pairs at out-degree 55. **Closure 0 of 6,657, 0 UNKNOWN**: the reachable fixpoint contains every cover-compatible candidate in every state, so the joint cover+reachability stage is provably identical to Round 79 and was not attempted. Measured causes: SLACK-COVER leaves a median 128 of 144 orbits individually cover-compatible, and the relation is 38.5% dense. The wall is located precisely -- the (orbit,phase) relation has out-degree 17 and a pinned walk could open as few as 0 candidates, but E^1 moves phase for free, so port-level occupancy is the only lever that could pin it. Round-79 counts now independently confirmed by Codex from the Round-80 archive | this branch, `research/RR_COVER_ORDER_CLAUDE.md` |
| 80 (Claude branch) | **Artifact repair only, no new theorem.** Round 79 preserved only aggregate counters, so its 38,141 / 6,657 could not be reproduced independently. Exported the full audit archive: 44,650-state input ledger with stable sha256 ids and root+index provenance, all 43,643 distinct slack-cover instances **including the 37,630 UNSAT**, candidate blocks, an explicit K-block witness for each of the 6,013 SAT instances, the 148 c=5 survivors, a pinned orbit/hexagon incidence table and a schema note. Re-derivation from the checkpoint archive matched Round 79 with **0 mismatches, 0 duplicate ids**; a stdlib-only verifier replays every band and the 6,657 total from the artifact alone. Round-79 ledger status set to THEOREM SOUND / STATE COUNTS CLAUDE-REPRODUCED / INDEPENDENT COUNT AUDIT PENDING | this branch, `outputs/rr_slack_cover_archive/SCHEMA.md` |
| 79 (Claude branch) | **SLACK-COVER: major payoff.** Generalises Round 78 to `c < 5`. Derived from the collision identity that the future excess is **exactly** `b = 5 - c` once U is covered -- so an 'excess <= b' budget is not an independent constraint; the real condition is that exactly `K = 25 - O` currently-closed orbits must COVER U, each wasting at most b. Reduces to the Round-78 exact cover at b = 0. Closes **38,141 of 44,650 (85.42%)**, 0 node-cap UNKNOWNs, with a positive control of 620 synthetic guaranteed-satisfiable instances (0 failures), 8,141 UNSAT instances re-decided under a different variable order (0 disagreements), 6,013 SAT witnesses verified, and E^1 confirmed to leave O, C, U, c and the candidate family unchanged over 4,325 steps. Residual **6,657** in **761** classes; 28 of 33 roots clear. Closure decays 97.4% -> 87.7% -> 40.1% -> 0% as slack grows, so the static incidence condition is saturated | this branch, `research/RR_SLACK_COVER_CLAUDE.md` |
| 78 (Claude branch) | **EXACT COVER at COLLISIONS=5: major payoff.** At the Round-77 bound's ceiling the whole collision budget is spent, so the `K = 25 - O` orbits still to open must form an exact cover of the uncovered hexagon set U by 5-element incidence blocks; the identity `|U| = 5K` holds on all 33,564 states (0 failures). Coverability closes 24,419 states, forced-orbit conflict 5,315, complete Algorithm X 3,682 -- **33,416 of 33,564 (99.56%)** -- with **0** node-cap UNKNOWNs, all 3,570 search-UNSATs re-decided under a different variable order (0 disagreements), and E^1 verified to leave U and the candidate family unchanged over 1,402 steps. 148 SAT survivors, none with a unique cover. Residual **44,798** in **1,050** classes; 26 of 33 roots clear | this branch, `research/RR_EXACT_COVER_COLLISION5_CLAUDE.md` |
| 77 (Claude branch) | **E^1 QUOTIENT -> ORBIT-HEXAGON COVER: major payoff.** E^1's closure is bounded (phase 5-cycle, chain <= 4, always needs a fresh hexagon). Classifying every quantity over 7,332 E^1 steps: `D`, `P` and orbit-reentry demand are freely repairable by E^1 (which is why Rounds 74-76 died), while `O`, coverage and incidence collisions are strictly invariant. New theorem: the 25 final open orbits carry 5*25=125 (orbit,hexagon) incidences over 120 hexagons each needing >=1, so `COLLISIONS = 5*O - covered <= 5`, monotone. Closes **122,194 of 200,408 (60.97%)**; residual **78,214** in **1,312** classes; 25 of 33 roots now fully closed | this branch, `research/RR_ORBIT_HEXAGON_COVER_CLAUDE.md` |
| 76 (Claude branch) | BRIDGE-CHARGE payoff test: **REFUTED**. `r = 0` is 196,056 of 200,408 (97.83 %), so the candidate had real leverage (83,914 states, 41.9 %, had it held) -- but exactly one macro transition type is free in every budgeted resource, `(ell=5, w2:10) = E^1`, and it realises a bridge: 10 Q2-admissible corpus witnesses plus an independent 3-edge walk from `initial_state` create the first bridge with `dPhi = dNdef = dO = dF = 0`. The event is exactly `capacity_slack`-neutral. **0 states closed** | this branch, `research/RR_BRIDGE_CHARGE_CLAUDE.md` |
| 75 (Claude branch) | Inter-orbit sequencing: orbit-only graph **insufficient** (0 of 7,920 transitions are phase-universal), but the required (orbit,phase) refinement and the free-movement subgraph are **strongly connected** -> condensation crossings 0, **predicted closure 0**. Caught a near-miss: a 15-SCC free graph that omitted `E^1` would have given an unsound bound. Retires reachability-based bounds at both granularities | this branch, `research/RR_ORBIT_SEQUENCING_CLAUDE.md` |
| 74 (Claude branch) | TOTAL RE-ENTRY LOWER BOUND payoff test: **sound but vacuous**. `seg_max(q) = |live(q)|` for all 32 masks, so the per-orbit ceiling never exceeds 1 and the bound degenerates to Round-71 ORBIT-REENTRY with +1 on both sides. **Predicted closure 0**; stop rule triggered before proof development. Retires the whole per-orbit segment-count family | this branch, `research/RR_TOTAL_REENTRY_PAYOFF_TEST_CLAUDE.md` |
| 73 (Claude branch) | **SKIP-COST RETRACTED** after Codex's audit (independently witnessed): the evaluator omitted q0 re-entry and repeated re-entry, so the supply-side upper bound under-estimated. 95,225 closures void; evaluator marked UNSOUND. Engine facts preserved and separated. Repaired proof-valid Q2 residual **200,408** in 1,570 classes (I do not adopt Codex's 273,125: it discards the sound demand-side orbit-reentry closure of 72,717) | this branch, `research/RR_Q2_LEDGER_REPAIR_CLAUDE.md` |
| 72 (Claude branch) | ~~SKIP-COST closes 114,298~~ **RETRACTED in Round 73**; the E^1/E^2 engine facts survive | this branch, `research/RR_SKIP_COST_THEOREM_CLAUDE.md` |
| 71 (Claude branch) | Q2/Area-A proof frontier rebuilt: the 33 coverage searches were never exhausted (3,321,753 queued states); Q2-admissible 3,248,890, closed 3,048,482 (capacity_slack + two new inequalities), **residual 200,408 in 1,570 classes**, 22 of 33 roots fully closed; the exact gap is boundary-list incompleteness, not a surviving mechanism | this branch, `research/RR_Q2_AREA_A_PROOF_FRONTIER_CLAUDE.md` |
| 70 (Claude branch) | 1,398 Rounds-35-37 Target-A boundaries fully reclassified: 1,398/1,398 replay-verified, only 6 Q2-admissible (all known-18), 7 mechanism classes (3 R2 shapes, one bridge hexagon), Target B closed 1,398/1,398 by the margin identity `margin = 12 - D`; 0 survivors | this branch, `research/RR_TARGET_A_1398_RECLASSIFICATION_CLAUDE.md` |
| 69b (Claude branch) | ELL4 unique-bridge Target-A normal form: the remaining 403 `root_ell = 4` anchors closed; the 3 same-component boundaries identified as known-18 `ell4_P2_*` with the helper-free `EXHAUSTED_NO_PATH` certificate reusable; 0 new Target-A classes | this branch, `research/RR_SHORT_ELL4_UNIQUE_BRIDGE_NORMAL_FORM_CLAUDE.md` |

This appendix is intentionally terse — the logical structure in §6-8 is
the primary account of this program; this table exists only to anchor
round numbers to commit hashes for anyone who needs to `git show` a
specific point in the history.
