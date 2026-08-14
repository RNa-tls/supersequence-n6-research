# Round log — n = 6 minimal superpermutation length

One line of history per research round, oldest first. This is the **chronological**
view; the **logical** account of what is actually proved lives in
[`research/SUPERPERMUTATION_N6_MASTER_STATUS.md`](research/SUPERPERMUTATION_N6_MASTER_STATUS.md)
and the headline claims in [`STATUS.md`](STATUS.md).

> **This project has not proved `L₆ ≥ 872`.** Unconditionally established: `867 ≤ L₆ ≤ 872`
> — the upper bound by an explicit witness verified in this repo, the lower bound cited from
> Houston/Pantone/Vatter (arXiv:1408.5108) and not re-derived here.

**Evidence tags:** `HP` hand proof · `EC` exhaustive computation · `ER` exact replay ·
`IV` independently verified · `BO` bounded observation (never proof) · `RF` refuted ·
`OPEN` unresolved.

---

## How to update this file

Append one row per round at the **bottom** of the table below, then update the
*Current ledger* block. A row is not complete without: the round number, a one-sentence
headline that states the **outcome** (not the intention), the deliverable path, and the
commit. Retractions get their own row **and** a strikethrough edit of the row they retract —
never a silent deletion. Rounds that produced no closure are recorded exactly like rounds
that did; the negative results are the reason the positive ones are trustworthy.

---

## Current ledger (update every round)

| | |
|---|---|
| Proof-valid Q2 / Area-A residual | **6,657** states *(independently audited)* |
| Canonical residual classes | **761** *(Claude-computed; not independently audited)* |
| Roots with empty Q2 residual | **28 / 33** (every long root clear) |
| Q2-admissible frontier (Round 71) | 3,248,890 |
| Last round | **83** — fragment repair: closure 0 (obligation cannot exist); **blocked-w2 lemma proved** |
| Unconditional bounds | `867 ≤ L₆ ≤ 872` |

---

## Phase I — foundations and the J branch (rounds 1–20)

| round | outcome | artifact / commit |
|---|---|---|
| 1–9 | E-orbit and hexagon foundations laid; J-branch discovered; capacity-obstruction proof | `0626f9c`..`d72520b` |
| 10–20 | Unique weight-2 move proof; RR same-component ⟺ chaining; Unique Hub Hexagon lemma; Hub Touch Count ≤ 2; corpus-completeness correction | `9b754f4`..`4c8b8ad` |

## Phase II — the parity detour (rounds 21–28)

| round | outcome | artifact / commit |
|---|---|---|
| 21–28 | Preparation-parity conjecture proposed and then **refuted** `[RF]`; corrected identity kept. Round 27's own `k ≥ 1` reading was itself wrong and was corrected to `k = 0` in Round 28 | `e775b1b`..`4d9bdc7`, `research/RR_PARITY_CONJECTURE_REFUTATION.md` |

## Phase III — Target A / Target B (rounds 29–38)

| round | outcome | artifact / commit |
|---|---|---|
| 29–34 | Terminal normal form; Target B defined; the known-18 Target-A ledger closed 18→9→8→7→**0** | `129d73a`..`d664019` |
| 35–38 | Target-A search rebuilt, finding **+1,398** new boundaries; capacity-helper firewall erected; five short roots identified as still open | `d07d267`..`232718e`, `aeafd1c`..`9b345c4` |

## Phase IV — four search bugs, found and fixed (rounds 40–54)

Every one of these invalidated a previously reported number. They are listed because the
corrected ledger is only meaningful alongside them.

| round | outcome | artifact / commit |
|---|---|---|
| 40 | **v1 R1-completeness bug** `[RF]`: R-kind macro edges were all treated as terminal; bare short roots must enqueue the first R edge. Fixed | `abfcdca`, `d8600b9`, `e9ff19c` |
| 41–42 | **v2 `O > 25` prune bug** `[RF]`: `O ≤ 25` is a Target-B coordinate and was wrongly applied before the Target-A test, discarding legal states. Fixed | `d90b69a`, `785ddab` |
| 43–48 | v3 taxonomy; **hierarchy macro-entry bug** `[RF]` found and fixed — 38,405 false positives corrected | `24002fd`..`b09f1d5` |
| 49–51 | Corrected short-root ledger; v5 fair pilot; 439-child ledger; top-8 selection | `1f3d11a`..`dfc314f` |
| 52–54 | v6 endpoint frozen; **v6/v7 provenance-loss bug** `[RF]`; frontier narrows to `short_ell2_r1_37` | `06dae7c`..`fae8ded` |

## Phase V — the T4 program (rounds 55–61)

| round | outcome | artifact / commit |
|---|---|---|
| 55–56 | All-13 pilot: 7 closed, 6 survive, 84-state frontier | `c394624`, `e280d32` |
| 57 | Dangerous-entry realizability audit: 196 mechanisms, T1-level | `6811132` |
| 58 | Stage D: full first-component-Z3 search over 6 checkpoints, 1,325,392 nodes | `9342018` |
| 59 | FZ1 provenance audit; **144-Z3 bound proof method retracted** `[RF]` (the numeric value is not disproven, only the method) | `bb3e9e1` |
| 60 | C4 collision obstruction: T2 (253,537 collisions), T2a four-hexagon closure | `2b3fb8f` |
| 61 | Hex-82 five-route closure (T2b); T4 asserted — still the strongest single result in the program | `19d484b`, `1f9efff` |
| 61 | **Independent T4 verification** (`CLAUDE_T4_VERIFIED`); generic VNTS theory | `3f24a49`, `f7a7211` |

## Phase VI — independent verification track (rounds 62–)

From here the work is the independent verification track: every Codex-produced datum is
re-derived from raw per-record data before use, and each round ends in a single verdict token.

| round | outcome | artifact |
|---|---|---|
| 62–68 | Master status document; G3 residual theory; Ω-projection soundness / monotonicity / termination; 1,818-anchor corpus analysis; the `short_ell1_r1_94:frontier:76` singleton resolved as generic | `2730c99`..`3370be4` |
| 69 | **Φ / unique-bridge invariant `6r ≤ 11 − Φ`** ⟹ `r ≤ 1`; σ-adjacency admissibility lemma; 1,415 of 1,818 residual anchors closed | `research/RR_SHORT_G3_COCOMPONENT_INVARIANT_CLAUDE.md` |
| 69b | ELL4 unique-bridge Target-A normal form: the remaining 403 `root_ell = 4` anchors closed; 0 new Target-A classes | `research/RR_SHORT_ELL4_UNIQUE_BRIDGE_NORMAL_FORM_CLAUDE.md` |
| 70 | All 1,398 Rounds-35–37 Target-A boundaries reclassified: only 6 are Q2-admissible and they are exactly the known-18; Target B closed **1,398/1,398**; 0 survivors. *(Self-caught error: a "Φ-free" claim in this round was wrong and was corrected in place in Round 71 — the totals were unaffected.)* | `research/RR_TARGET_A_1398_RECLASSIFICATION_CLAUDE.md` |
| 71 | Q2/Area-A proof frontier rebuilt. The 33 coverage searches **were never exhausted** (3,321,753 states left queued). Q2-admissible 3,248,890 → **residual 200,408** in 1,570 classes; the real gap is boundary-list incompleteness, not a surviving mechanism | `research/RR_Q2_AREA_A_PROOF_FRONTIER_CLAUDE.md` |
| 72 | ~~SKIP-COST closes 114,298~~ — **RETRACTED in Round 73**. The `E¹`/`E²` engine facts survive | `research/RR_SKIP_COST_THEOREM_CLAUDE.md` |
| 73 | **SKIP-COST retracted** after Codex's audit, independently witnessed with my own `q0`-return walk: the evaluator omitted `q0` re-entry and repeated re-entry, so a supply-side upper bound under-estimated. 95,225 closures void. Repaired residual **200,408** — I did not adopt Codex's 273,125, which discards the sound demand-side orbit-re-entry closure of 72,717 | `research/RR_Q2_LEDGER_REPAIR_CLAUDE.md` |
| 74 | TOTAL RE-ENTRY LOWER BOUND: **sound but vacuous**. `seg_max(q) = |live(q)|` for all 32 masks, so the bound degenerates to Round-71 ORBIT-REENTRY with +1 on both sides. Closure **0**. Retires the per-orbit segment-count family | `research/RR_TOTAL_REENTRY_PAYOFF_TEST_CLAUDE.md` |
| 75 | Inter-orbit sequencing: the orbit-only graph is **insufficient** (0 of 7,920 transitions are phase-universal), but the required `(orbit, phase)` refinement is strongly connected → crossings 0, closure **0**. Near-miss recorded: a free-movement graph omitting `E¹` showed 15 SCCs and would have produced an unsound bound | `research/RR_ORBIT_SEQUENCING_CLAUDE.md` |
| 76 | BRIDGE-CHARGE: **refuted**. `r = 0` covers 196,056 of 200,408 (97.83 %), so the candidate had real leverage — but `E¹` creates the first bridge with `ΔΦ = ΔNdef = ΔO = ΔF = 0`, witnessed on corpus and by an independent 3-edge walk from `initial_state`. Closure **0** | `research/RR_BRIDGE_CHARGE_CLAUDE.md` |
| 77 | **ORBIT-HEXAGON COVER — major payoff.** Quotienting out `E¹` first: its closure is bounded (≤ 4 steps on `q0`'s phase 5-cycle) and it freely repairs `D`, `P` and re-entry demand — which is exactly why rounds 74–76 died — but leaves `O`, coverage and incidence collisions strictly invariant. New theorem: `COLLISIONS = 5·O − |covered| ≤ 5`, monotone and demand-side. Closes **122,194 of 200,408 (60.97 %)** → residual **78,214** in **1,312** classes, 25/33 roots clear | `research/RR_ORBIT_HEXAGON_COVER_CLAUDE.md` || 78 | **EXACT COVER at `COLLISIONS = 5` — major payoff.** With the collision budget spent, the `K = 25 − O` orbits still to open must exactly cover the uncovered hexagon set; `|U| = 5K` verified with 0 failures on all 33,564. Coverability closes 24,419, forced-orbit conflict 5,315, complete Algorithm X 3,682 — **33,416 of 33,564 (99.56 %)**, with **0** node-cap UNKNOWNs and all 3,570 search-UNSATs re-decided under a different variable order (0 disagreements). 148 SAT survivors, **none with a unique cover** (min 6 covers). Residual **44,798** in **1,050** classes, 26/33 roots clear | `research/RR_EXACT_COVER_COLLISION5_CLAUDE.md` || 79 | **SLACK-COVER — major payoff.** Derived (not assumed) that the future excess is **exactly `b = 5 − c`, forced**, the moment `U` is covered — so "excess ≤ b" is the counting slack, not a constraint; what restricts is *K closed orbits must cover U*, with every block wasting ≤ b. Reduces to Round 78 at `b = 0`. Closes **38,141 of 44,650 (85.42 %)** with **0** UNKNOWNs, validated by 620 synthetic guaranteed-SAT instances (0 failures), 8,141 UNSATs re-decided under a different variable order (0 disagreements) and 6,013 verified SAT witnesses. Residual **6,657** in **761** classes, 28/33 roots clear. Power decays 97.4 % → 87.7 % → 40.1 % → **0 %** as slack grows: the static condition is saturated | `research/RR_SLACK_COVER_CLAUDE.md` || 80 | **Artifact repair, no new theorem.** Round 79 preserved only aggregate counters, so Codex could not reproduce 38,141 / 6,657. Exported the full audit archive to `outputs/rr_slack_cover_archive/`: the 44,650-state input ledger (stable sha256 ids, root+index provenance, `c`/`b`/`O`/`K`, `C`/`U`/open-orbit masks), all **43,643** distinct instances **including the 37,630 UNSAT**, with candidate blocks and an explicit `K`-block witness for every SAT, the 148 `c=5` survivors, a pinned incidence table and a schema note. Re-derivation matched Round 79 with **0 mismatches and 0 duplicate ids**, and a **stdlib-only verifier** replays every band and the 6,657 total from the artifact alone. Round 79 now carries: theorem SOUND / counts CLAUDE-REPRODUCED / **independent count audit PENDING** | `outputs/rr_slack_cover_archive/SCHEMA.md`, `src/verify_rr_slack_cover_archive.py` || 81 | **Cover-compatible orbit ordering — no payoff, and a located wall.** Built a maximally conservative opening relation (all 5 phases x 6 rotation lengths x 4 joints; every excluded pair excluded by exhaustion over the group action, not by search absence; `w2:10` deliberately kept since a weight-2 joint into a fresh orbit is a legal engine transition). It reproduces Round 75's 7,920 pairs, out-degree 55. **Closure 0 of 6,657**, 0 UNKNOWN: the reachable fixpoint contains *every* cover-compatible candidate in *every* state, so stage D is provably identical to Round 79 and was not attempted. Two measured reasons: SLACK-COVER leaves a median **128 of 144** orbits individually cover-compatible, and the relation has 38.5 % density. **Negative structural result: static incidence + orbit-level ordering is exhausted.** The wall is located — the phase-refined relation has out-degree **17** and a pinned walk could open as few as **0** candidates, but `E¹` moves phase for free, so port-level occupancy is the only lever that could pin it | `research/RR_COVER_ORDER_CLAUDE.md` || 82 | **Port occupancy pins the phase, and it still closes nothing — with a measured ceiling.** Literal `E¹`/`E²` availability from the engine's own no-repeat predicates: **448 states cannot move phase at all**, the maximal `E¹` chain is **4** (Round-77 cross-check, identical with and without the Area-A prune), and 45 states have `E¹` blocked but `E²` available. From a pinned phase closure only **4–54** of ~130 candidate orbits are openable — a real restriction. **Closure 0 of 6,657, 0 UNKNOWN.** The decisive number: under a deliberately *unsound* strengthening forbidding all phase repair, the first-open test would close **13 of 6,657 (0.20 %)**; with the true closure, **1**. So `E¹` costs this direction 12 states and the direction was worth ≤ 13 throughout. Cause is not `E¹` but the predicate: a first-open test closes only if *every* openable orbit is cover-incompatible, and ~90 % of orbits are individually cover-compatible. **First-open tests are exhausted at every refinement level** | `research/RR_PORT_OCCUPANCY_CLAUDE.md` || 83 | **Fragment repair is not the bottleneck — and the blocked-w2 lemma is now proved.** All 6,657 residual states have `F = 1`, so no further abandonment is legal and **no new fragment can be created**; every remaining opening must be `Z3` at `ΔNdef = 0`, and all 144 orbits admit one. `M_def = 0` everywhere, so the payoff gate stopped the round: **closure 0**. The real product is foundational: `N_exceeded_monotone` is Q1-SAFE and used by every search, and rested on a blocked-w2 lemma the repo cited from prior work and recorded as *"a bounded empirical check, not a proof"*. Exhaustively, `t = E(σ(p'))` — the w2 target shares the blocking window's orbit one phase on — and no-repeat forces a visited blocker to have been a *registered* joint target, so the fresh-orbit case is impossible. Hence `ΔNdef ≥ 0` and the prune is **sound**. Pinned by `tests/test_blocked_w2_lemma.py` | `research/RR_FRAGMENT_REPAIR_CLAUDE.md` |

---

## Standing methodological rules earned the hard way

1. **Supply-side upper bounds are fragile; demand-side lower bounds are not.** Any bound of
   the form "the walk cannot reach more than X" must model `q0` return and arbitrary repeats
   or it is unsound. (Round 73, after SKIP-COST.)
2. **Classify a candidate quantity under free `E¹` motion before proposing any inequality on
   it.** `E¹` freely repairs `D`, `P` and orbit-re-entry demand. (Round 77, after three
   rounds died to it.)
3. **A gate that checks one failure mode does not license a bound against a second.**
   SKIP-COST passed the hexagon-vs-port gate and still died to entry multiplicity. (Round 73.)
4. **When uncertain about a quotient graph, ADD edges rather than remove them.** Omitting a
   free move deletes legal transitions and inflates a lower bound. (Round 75.)
5. **Never treat a bounded continuation search as impossibility evidence**, and never treat a
   timeout as UNSAT.
6. **A round that reports state counts must preserve the per-state ledger and the instance
   archive — SAT and UNSAT alike — in a form an independent verifier can replay without
   importing our code.** Aggregate counters are not reproducible. (Round 80, after Round 79.)
7. **Never claim exhaustion**, and never derive a parity or congruence claim from corpus
   statistics. (Rounds 21–28.)
