# TOTAL RE-ENTRY LOWER BOUND — payoff test: the bound is sound and vacuous

**Author:** Claude (independent verification track)
**Round:** 74
**JSON:** `outputs/rr_total_reentry_payoff_claude.json`
**Baseline:** 200,408 theorem-backed Q2 residual states (Round-71 ORBIT-REENTRY confirmed sound by
Codex; SKIP-COST retracted in Round 73 and not revisited).
**Scope:** Q2 / Area-A. No search, no frontier re-run, no bounded continuation.

---

## Result, up front

> **Predicted closure: 0 states.** The candidate is **sound** — it passes all four adversarial
> witnesses — but it is **provably vacuous**: its per-orbit ceiling can never exceed 1, so it
> degenerates into the Round-71 ORBIT-REENTRY inequality with `+1` added to both sides.
>
> This was settled by a 32-case exhaustive computation, **before** the residual sweep. Per the
> brief's stop rule (< 10,000), no sweep was run and no proof was attempted.

---

## 1. Definitions — literal port visitation only

For an E-orbit `q` with its 5 ports, at state `s`:

* `reg(q)` = ports of `q` already registered = `popcount(orbit_masks[q])`;
* `live(q)` = ports of `q` **unvisited** — a single-permutation test against `hex_masks`, never a
  hexagon popcount;
* `dead(q)` = `5 − reg(q) − live(q)` — visited but unregistered, hence unregistrable forever.

**`need(q)`** = ports of `q` a completion must still register. At the Area-A target every port is
visited and exactly 4 stay unregistered across the 25 open orbits, so
`Σ_q (live ports of q left unregistered) ≤ 4 − D_dead(s)`; `need(q) ≤ live(q)` always.

**`seg_max(q)`** = an **upper** bound on the ports **one** segment can register in `q`. A segment
is a forward `+1/+2` walk on the orbit's 5-cycle (`E¹` free, `E²` costing one `Ndef`) landing only
on currently-unvisited ports, with total forward displacement ≤ 4 — a 5-cycle cannot be traversed
further without revisiting. `seg_max` is computed **giving every skip away free**, which is the
sound (enlarging) direction for a per-segment upper bound.

**The candidate.** `q0` is included with its own `need(q0)`; an orbit may be entered arbitrarily
often, and each entry after the current segment is a segment start:

```
Σ_q  ⌈ need(q) / seg_max(q) ⌉   ≤   1 + O_cap + (R_cap + Φ)
```

the right side counting the current segment, the `O_cap` fresh openings, and the shared re-entry
budget.

## 2. Adversarial witnesses — all pass

`seg_max` must over-estimate, never under-estimate, on each:

| witness | `q0` | `live(q0)` | `seg_max(q0)` | orbits anywhere with `seg_max < live` |
|---|---|---|---|---|
| `long_found_142` (the hexagon-vs-port refutation) | 1 | 3 | 3 | **0** |
| the Round-73 `q0`-return witness | 0 | 3 | 3 | **0** |
| repeated-entry continuation (two further `E²` inside `q0`) | 0 | 1 | 1 | **0** |
| a residual-band state restored by the SKIP-COST retraction (`short_ell4`, `P∈{13,14}`, `Ndef=0`) | 92 | 0 | 0 | **0** |

No under-estimate anywhere. **The bound is sound.** It also does not assume an orbit is entered at
most once, and no hexagon popcount enters the definition.

## 3. Why it is vacuous — the 32-case computation

Enumerating every live-port mask of a 5-port orbit:

| `|live(q)|` | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| `seg_max(q)` | 0 | 1 | 2 | 3 | 4 | 5 |

**`seg_max(q) = |live(q)|` for all 32 masks. Zero exceptions.** Since `need(q) ≤ live(q)`:

```
⌈ need(q) / seg_max(q) ⌉  ≤  ⌈ live(q) / live(q) ⌉  =  1     for every orbit, always
```

So the left side collapses to *the number of orbits that still need at least one segment*, i.e.
`O_cap + |Q| + [q0 needs a further segment]`, and the inequality becomes

```
|Q| + [q0]   ≤   1 + (R_cap + Φ)
```

which is the Round-71 ORBIT-REENTRY inequality `|Q| ≤ R_cap + Φ` with `1` added to **both** sides —
strictly no stronger, and weaker whenever `q0` does not itself need a further segment.

**Predicted closure on the 200,408 residual: exactly 0.** No sweep is needed to know this; the
degeneracy is a property of the 5-cycle, not of the corpus.

### The structural reason

A forward `+1/+2` walk with displacement ≤ 4 sweeps the **entire** 5-cycle from a suitably chosen
entry: a single dead port is stepped over by `+2`, and any run of dead ports can always be placed
*behind* the chosen entry port. With only five ports per orbit there is never a live port a single
segment cannot reach.

> **No orbit ever needs two segments on within-orbit port-supply grounds.**

## 4. What this kills, and what it leaves

This retires the whole family of *per-orbit segment-count* bounds, not just this one candidate. Any
theorem of the form "orbit `q` requires ≥ 2 entries" cannot be derived from within-orbit capacity;
it would have to come from somewhere else entirely.

**The only way to force `seg_max(q) < live(q)` is to charge the `E²` skips** — making `seg_max`
budget-dependent. But `R_cap + Φ` is a single global budget, so attributing it per orbit is exactly
the shared-budget, supply-side reasoning that was retracted in Round 73. In its safe, budget-free
form the family is dead; in its budget-dependent form it is the retracted argument again. I am not
reviving it.

**Where a real bound would have to live.** Not in per-orbit capacity but in **inter-orbit
sequencing**: consecutive segments must be linked by a *legal* orbit-changing joint, so the
sequence of orbits visited is a walk in a fixed digraph on the 144 orbits, not an arbitrary
selection. The counting resource there is reachability/adjacency between orbits, which the current
bounds — all of which treat the orbit set as an unordered supply — ignore completely. That is a
qualitatively new mechanism rather than another local heuristic, but it is a new investigation and
nothing here establishes it.

## 5. Ledger

| | |
|---|---|
| Q2 residual (unchanged) | **200,408** |
| canonical classes (unchanged) | **1,570** |
| states closed by this candidate | **0** |
| stop rule (< 10,000) | **triggered — stopped before proof development** |

**This project has not proved `L₆ ≥ 872`, and nothing here bears on that.**
