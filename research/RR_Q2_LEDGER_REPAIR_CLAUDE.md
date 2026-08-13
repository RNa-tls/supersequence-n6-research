# Q2 ledger repair: SKIP-COST retracted, dependency graph rebuilt

**Author:** Claude (independent verification track)
**Round:** 73
**Trigger:** Codex's independent audit and deterministic reconstruction of all 33 roots
**JSON:** `outputs/rr_q2_ledger_repair_claude.json`
**Scope:** Q2 / Area-A throughout. No search was run; no bounded continuation is used as evidence.

---

## 1. Codex's soundness objection: **CONFIRMED**

Codex reports that the historical SKIP-COST evaluator omitted (a) re-entry into the current orbit
`q0` and (b) repeated re-entry into the same orbit. Reading the committed evaluator
(`src/prove_rr_skip_cost.py`) both omissions are literal and visible:

```python
re_ = sorted((BESTREACH[LM[q]][e] for q in openq if q != q0), reverse=True)[:g]
#                                            ^^^^^^^^^^^ q0 excluded
#                                                                        ^^^^ g DISTINCT orbits
```

I did not take this on report. I searched for a `q0`-return witness with the exact engine,
independently of Codex's, and found one from `initial_state` (orbit 0):

| macro edge | `joint_kind` | lands in orbit |
|---|---|---|
| `rot^1;w2:10` | `Z2abandon` | 33 |
| `rot^5;w3:120` | `R` | 33 |
| `rot^5;w3:201` | `R` | **0 — back in `q0`** |

Final state: `Ndef = 2`, `Φ = 2`, `area_a_prune_reason = None`. **A `q0` return is legal inside the
Q2 slab.**

**Why this is fatal to that particular bound.** SKIP-COST was a **supply-side** estimate — an
*upper* bound on the ports the walk can still register. Deleting `q0` from the re-entry candidates
and forbidding repeats *removes reachable ports*, so the estimate came out **too small**, and the
closure test `UB < B` fired on states where no contradiction exists. An upper bound that
under-estimates is not an upper bound. **The objection is correct and the closure is void.**

### Repairs applied

1. **RETRACTED**: the claim that SKIP-COST closes 95,225 states. All 95,225 are restored to the
   residual.
2. **UNSOUND**: `src/prove_rr_skip_cost.py`'s segment evaluator is marked unsound and must not be
   cited. Its adversarial gate against `long_found_142` passed and was necessary but *not
   sufficient*: that gate tests only the hexagon-vs-port conflation, not the entry-multiplicity
   assumption. A gate that checks one failure mode does not license a bound against a second.
3. **PRESERVED, and separated**: the engine facts stand and are untouched by this —
   exactly two macro generators preserve the endpoint's E-orbit, `(ℓ=5,w2:10) = E¹` (`Z2`, free)
   and `(ℓ=5,w3:120) = E²`, which is **always an `R` costing exactly `Ndef` +1** (24 × 720
   exhaustive, 0 partial cases; 3,073/3,073 sampled `E²` edges). These are statements about single
   edges. What was wrong was the *future-capacity bound built on top of them*, not the facts.

---

## 2. Where I disagree with the audited baseline: **273,125 is too pessimistic**

Codex's proof-valid figure is `292,198 − 19,073 = 273,125`, i.e. the capacity-slack survivors minus
the LIVE closure only. That **discards the Round-71 orbit-re-entry closure of 72,717 states**, and
I believe that closure is unaffected by the bug. This is the concrete contradiction the brief
invited me to look for, so I state it explicitly rather than adopting the number.

**The decisive distinction is the direction of the bound.**

| | SKIP-COST | ORBIT-REENTRY (Round 71) |
|---|---|---|
| what it estimates | **upper** bound on ports the walk can still register (supply) | **lower** bound on segment starts the walk must still pay for (demand) |
| closure test | `UB < B` | `need > R_cap + Φ` |
| effect of omitting `q0` | removes reachable ports → estimate too small → **unsound** | `q0` excluded from the demand set → `need` too small → **fewer** closures |
| effect of forbidding repeats | removes reachable ports → estimate too small → **unsound** | each orbit counted once → `need` too small → **fewer** closures |

Every omission the orbit-re-entry inequality makes *reduces* the demand it computes. Its statement
is: each open orbit `q ≠ q0` still holding a live unregistered port must either receive at least
one further registration — which requires at least one orbit-changing joint landing in `q`, and
every such joint costs one unit of `R_cap + Φ` — or be abandoned entirely, its live ports dying
against the budget `4 − D_dead`. Orbits that are *partly* re-entered and *partly* abandoned are
charged only once, to whichever branch is cheaper for the adversary.

A lower bound that under-counts is still a lower bound. **The `q0`-return and repeated-entry
witnesses make the true demand larger, never smaller, so they cannot invalidate a closure.** The
same holds a fortiori for the dead-port bound `D_dead ≤ 4`, which mentions neither segments nor
entries nor reachability.

**Repaired proof-valid Q2 residual: 200,408** = 292,198 − 19,073 (LIVE / dead-port) − 72,717
(orbit-re-entry).

I flag this as the one open disagreement with the audit. If Codex has a specific defect in the
orbit-re-entry inequality — as opposed to not having applied it — I have not been shown it and
would want to see it; absent that, 200,408 is the number I can defend.

---

## 3. Downstream dependency repair

| artifact | depended on the 95,225? | action |
|---|---|---|
| `research/RR_SKIP_COST_THEOREM_CLAUDE.md` (Round 72) | **yes** — its headline result | retraction banner added; the closure table is void; §1–§4 (engine facts, adversarial gate, the two inequality *statements*) survive |
| `outputs/rr_skip_cost_claude.json` | **yes** | `verdict` → `SKIP_COST_RETRACTED`, closure counts marked void |
| master status Round-72 row and JSON entry | **yes** | rewritten to the retraction |
| `outputs/rr_q2_area_a_frontier_claude.json` (Round 71) | **no** — predates SKIP-COST | unchanged; its 200,408 becomes the current figure again |
| `research/RR_Q2_AREA_A_PROOF_FRONTIER_CLAUDE.md` (Round 71) | **no** | unchanged and now current |
| Rounds 69 / 69b (1,818 anchors) | **no** | unchanged |
| Round 70 (1,398 boundaries) | **no** — closed by `capacity_slack` + `Φ ≥ 0` | unchanged |
| known-18 closure | **no** | unchanged |
| `LIVE-PORT SUPPLY` (19,073) | it is a supply bound — **audited separately** | **stands**: it caps registrations in orbit `q` by `live(q)`, the count of ports unvisited *now*. Entry multiplicity is irrelevant — however many times `q` is entered, no walk can register a port that is already visited. |

The `E¹`/`E²` engine facts are moved out of the retracted document's dependency chain and recorded
as standalone verified facts.

---

## 4. Reclassification of the repaired residual

Derived from the Round-71 sweep, which is unaffected by the bug — no re-run was performed.

| | |
|---|---|
| **repaired residual** | **200,408** |
| **canonical classes** | **1,570** |
| roots with residual | **11 / 33** (22 fully closed) |
| short-root share | **200,239 (99.92 %)** |

**Concentration.** Top 5 classes 15,525 (7.7 %); top 10 27,431 (13.7 %); top 20 44,933 (22.4 %).
Largest class `Ndef=0, Φ=5, R_cap=3, O=10, P=13, D=37, D_dead=1, need=8, used=1` — **3,969**
(1.98 %).

**This answers the question the brief posed.** The residual is **not** one normal form repeated —
no class exceeds 2 %, and the top 20 hold under a quarter. But it is also not 200,408 distinct
mechanisms: it is one narrow *region* finely stratified by coordinates.

| coordinate | distribution |
|---|---|
| `Ndef` | `{0: 200,239, 1: 169}` — essentially all at `Ndef = 0` |
| `R_cap` | `{3: 200,239, 2: 169}` — maximal re-entry budget |
| `P` | `{13: 93,258, 14: 106,981, 20: 12, 21: 157}` — two values carry everything |
| `O` | 3 … 10, peaking at 8 (66,499) and 9 (59,589) |
| `Φ` | 0 … 5, rising monotonically to `Φ=5` (79,847) |
| `D_dead` | `{0: 42,084, 1: 65,035, 2: 51,129, 3: 29,562, 4: 12,598}` |
| per root | `short_ell4` 80,733; `ell3` 61,982; `ell2` 35,456; `ell1` 15,981; `ell0` 6,087; long roots 169 total |

So: **shallow (`P ∈ {13,14}`), `Ndef = 0`, five short roots, with `R_cap` at its maximum of 3.**
That combination is exactly why `capacity_slack` cannot bite — the budget is as large as the slab
allows.

---

## 5. Next bottleneck — and the methodological rule it follows from

The retraction produces a rule I did not have before and which the brief's Task 4 is asking for
directly:

> **Supply-side upper bounds are fragile to entry multiplicity; demand-side lower bounds are
> immune.** Any bound of the form "the walk cannot reach more than X" must model `q0` return and
> arbitrary repeats or it is unsound. Any bound of the form "the walk must pay for at least Y
> segment starts" is only ever strengthened by them.

That rules out reviving SKIP-COST and points at Task 4-A. Note the orbit-re-entry inequality *is
already* a demand-side bound in this family — which is precisely why it survives the audit.

### Best next candidate: TOTAL RE-ENTRY LOWER BOUND

**Weakest precise statement worth proving.** Let `need(q)` be the number of ports of orbit `q` that
a completion must still register, and let `seg_max(q)` be an upper bound on the ports **one**
segment can register in `q` — a single `+1/+2` forward walk on the 5-cycle landing only on
currently-unvisited ports, hence at most `min(5, live(q))` and in general shorter. Then the number
of segments spent in `q` is at least `⌈need(q) / seg_max(q)⌉`, and

```
Σ_{q}  ⌈ need(q) / seg_max(q) ⌉   ≤   1 + O_cap + (R_cap + Φ)
```

the right side counting the current segment, the fresh openings, and the shared re-entry budget.

**Why it survives the audit.** `seg_max` bounds *one* segment, not the future; entering `q` again
simply adds another term to the left. `q0` is included with its own `need(q0)`. Repeats are the
mechanism the bound counts, not an assumption it forbids. Nothing is declared dead from hexagon
popcount — `live(q)` is literal port visitation.

**Predicted payoff.** From the Round-71 margin distribution, **86,654 residual states (43.2 %) sit
at `need = R_cap + Φ` exactly**. Any strengthening that raises the demand by 1 on those closes them.
The current inequality charges 1 per orbit; the proposed one charges `⌈need(q)/seg_max(q)⌉`, which
exceeds 1 whenever an orbit's outstanding ports cannot fit in one segment — common at `D_dead ≥ 1`,
which is 158,324 of the 200,408.

**Required assumptions.** Only: the Area-A completion target `(P,O,D) = (121,25,4)` with `Ndef ≤ 3`;
`Φ ≥ 0`; the no-repeat rule; and the `E¹`/`E²` generator facts of §1.

**Payoff test comes first.** Per the brief's Task 6 this must be evaluated on the residual before
any proof effort. **I have not run that evaluation** — it needs one sweep over the 292,198
capacity-slack survivors, and it is the immediate next action, not a result claimed here. The
86,654 figure above is a *prediction* from existing margins, not a measurement of the new bound.

### Adversarial protocol for the candidate (to run before, not after)

1. `long_found_142` — the hexagon-vs-port conflation;
2. the `q0`-return witness in §1;
3. a repeated-re-entry witness (same orbit entered twice);
4. a sample of states restored by this retraction — the new bound must **not** close them unless it
   can be shown sound against 1–3 first.

`seg_max` must over-estimate on every one of them.

---

## 6. Status

* Codex's soundness objection: **confirmed**, independently witnessed.
* 95,225 SKIP-COST closures: **retracted**.
* `E²` = `R` = `Ndef` +1: **preserved**, separated from the void bound.
* Repaired proof-valid Q2 residual: **200,408** (not 273,125 — see §2).
* Canonical classes: **1,570**; largest 3,969 (1.98 %); top-20 22.4 %.
* Best next candidate: **TOTAL RE-ENTRY LOWER BOUND**, payoff test pending.

**This project has not proved `L₆ ≥ 872`, and nothing here bears on that.**
