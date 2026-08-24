# Status: n = 6 minimal superpermutation length

A round-by-round log of the research program lives in [ROUNDS.md](ROUNDS.md).

> **Audited Q2 / Area-A residual: 4,782 states.** Rounds 103–104 identified the engine's
> `Ndef + H ≤ 3` budget and used it to close the whole remaining population provisionally.
> Round 105 attacked that result: the component lower bound `L2 = c − 1` is **false for general
> 0/1 digraphs** (111 brute-force counterexamples) and silently requires cost-0 out-degree ≤ 1 —
> a precondition that holds on all 173,409 real assignments and is now asserted, so the counts
> survive with a corrected statement.
>
> **Round 118 (F=1, k=3) — read this first.**
> **The cell `(3,1)` is NOT closed.** Its resource budget is now completely pinned down and
> **6 of its 9 subcases are excluded exhaustively**; three remain open. Claude-closed outer
> cells stay at **6 of 55**.
>
> With `k = 3, F = 1`: `P = 121`, `O = 27`, `D = 5k−1 = 14`, `L = 845 + S + H`. From
> `S = 26 + e + x − f_out` and Round 117's Lemma E (`f_out ≤ 1+e`) one gets **`H ≤ 1 − x`**, so
> `H ≤ 1` and `x ≤ 1` are *derived*, not assumed, and `H = 1` needs `x = 0`, `f_out = 1+e`.
> That leaves exactly **7 resource rows**, or **9 subcases** once `H` is split out, with no
> hidden slack (`e ≥ 3` and `x ≥ 2` both force `H < 0`).
>
> `H = 0` forces `t = 1` — one all-light 121-pass chain. `H = 1` means **exactly one weight-4
> joint** and nothing heavier, which splits the chain into `t = 2`. The hub-tax-1 moves are
> exactly the **13 weight-4 tails**, and all 13 always change orbit and always leave the source
> hexagon (720/720); 12 are hexagon-disjoint, one shares 2 hexagons. So the heavy joint can
> never sit inside the forced τ-block between the two `h*` passes.
>
> Round 117's forced 5-pass separation survives only at `e = 1, x = 0`; one `W3a` jump widens
> it to `{4,5}`, and **`e = 2` breaks it entirely** because both `h*` orbits can then take a
> second run. Those are exactly the two freedoms `k = 3` opens.
>
> Twenty exact runs (4 groups × 5 splits) return **all `UNSAT_COMPLETE`, 77,632,127,455 nodes,
> zero cap hits**, reaching 109 of 121 passes. The three remaining subcases — `(1,1,2)ᴴ⁼⁰`,
> `(2,0,2)ᴴ⁼⁰`, `(1,0,2)ᴴ⁼¹` — all exceeded 2–3×10¹⁰ nodes even after structural splitting, and
> are recorded as **UNKNOWN**, not UNSAT; no speculative multi-hour sweep was launched.
>
> Ledgers stay **4,782** and 6,396/6,396. Round 115 is PARTIAL under Codex audit; Round 117 and
> this round have **no independent audit** (Codex quota exhausted). This project has not proved
> `L₆ ≥ 872`.
>
> **Round 117 (F=1 cell closure) — read this first.**
> **The cell `(k,F) = (4,1)` is closed** — the first of the four `F = 1` cells. Under NR6 no
> length-≤871 superpermutation has `F = 1` and `O = 28`. With the `F = 0` column that makes
> **6 of the 55 outer cells closed, 49 remaining**; `(3,1)`, `(2,1)`, `(1,1)` are untouched.
>
> **Lemma E (new).** At `F = 1`, `f_out ≤ 1 + e`. Writing the two `h*` passes in walk order as
> `X` (entry `v`, length `b`) and `Y` (entry `σ^b v`, length `6−b`), their free successors cross
> exactly: `X → τ(entry_Y)` and `Y → τ(entry_X)` (3600/3600). If both exit freely, each free
> successor opens a run of the *other's* orbit, and if both stay in the same run as their short
> pass the walk closes a cycle `X → orb(Y) run → Y → orb(X) run → X` — impossible in a path. So
> `f_out = 2` forces `e ≥ 1`. The proof uses `h*`'s unique complementary pair, and the n=4
> exhaustive data confirms the scope exactly: **0 violations at `F = 1`, 450 at `F ≥ 2`.**
>
> **Corollary.** At `F = 1`, `O ≤ 1 + S + F` is *equivalent* to `f_out ≤ 1 + e + x`, so Lemma E
> **proves Round 110's Theorem A for `F = 1`** — it had only been verified empirically. The whole
> column's `H` bounds (`k = 1,2,3,4 → H ≤ 3,2,1,0`) are now proved rather than assumed.
>
> Lemma E pins the `(4,1)` budget to **exactly two sub-cases**, both with `S = 26`, `H = 0` and
> therefore `t = 1`: a counterexample would have to be one single all-light chain of 121 passes.
> Sub-case B1 reduces further — `X` must be in case (ii) and `Y` in case (i), so the two short
> passes sit **exactly 5 passes apart** with the block between them forced. An exact search over
> both sub-cases and all five splits returns **10/10 `UNSAT_COMPLETE`, 269,082,235,020 nodes,
> zero cap hits**, reaching 109 of the required 121 passes. False rejection 0.
>
> Q2's zero result is **not** counted as closure of generic `(1,1)`. The ledgers stay **4,782**
> and 6,396/6,396. This project has not proved `L₆ ≥ 872`; NR6 and 49 cells remain open, and
> this round has no independent audit.
>
> **Round 116 (F=1 structure) — read this first.**
> A structure round: **no cell is closed.** It fixes the generic `F = 1` column from the
> definitions alone, importing nothing from the Q2 archive.
>
> `P = 121`, `O = 24+k`, `D = 5O − P = 5k − 1`, `L = 845 + S + H`. Since `D ≥ 0`, **`F = 1`
> forces `k ≥ 1`** — the cell `(k,F) = (0,1)` does not exist arithmetically — and `O ≤ 1+S+F`
> with `S+H ≤ 26` caps `k ≤ 4`. **The `F = 1` column is exactly the four cells `k = 1,2,3,4`**,
> of which Q2 ever touched only `(1,1)`.
>
> The re-entry structure is completely forced. `Σ_h (e_h − 1) = 1` with `e_h ≥ 1` has one
> integer solution, so **exactly one hexagon `h*` is entered twice**; the per-hexagon shortfall
> identity then forces **119 passes of length exactly 6** and the two passes of `h*` to have
> lengths `(a, 6−a)`. **The short passes are exactly the two visits to `h*`** — locality in its
> strongest form — and they can **never be consecutive**: the exit word of one is σ-adjacent to
> the entry word of the other, and σ-adjacency is a rotation, not a joint. Only **3 of the 11
> partitions of 6** are realizable as deficit patterns.
>
> Recomputing the light moves for every pass length (720 words × `ℓ = 0..5`, uniform 720/720):
> the `ℓ = 5` row is exactly the `F = 0` classification, but for **every `ℓ < 5` all four light
> moves leave the orbit**. So a short pass can carry a **free inter-run connector** — impossible
> at `F = 0`. That gives the exact accounting `S = (r−1) + x − f_out` with **`f_out ≤ 2`**, hence
> `cost ≥ 22 + k + e + x + t − f_out` and `L ≤ 871 ⟺ k + e + x + t − f_out ≤ 4`. The theorem
> needed to close the column is **`k + e + x + t − f_out ≥ 5`**. `(4,1)` is the tightest cell:
> `H = 0` is forced, so `t = 1` — the whole walk is a single all-light chain.
>
> Only two Q2 conditions turn out to be generic at `F = 1`: `P = 121` and `Φ ≥ 0`. Everything
> else — `O = 25`, `D = 4`, `Ndef+H ≤ 3` (which actually means `L ≤ 872`), forced `ℓ` values,
> fragment locality, Area-A boundaries, the pass↔hexagon bijection, intra-orbit free arcs — is
> Q2-specific and was not used.
>
> Verified against **971 exhaustive `n = 4` `F = 1` walks**: every structural claim holds,
> false rejection 0, and all 813 `F = 0` walks have `f_out = 0`. The ledgers stay **4,782** and
> 6,396/6,396. This project has not proved `L₆ ≥ 872`; 50 cells and NR6 remain open.
>
> **Round 115 (F=0 column) — read this first.**
> **The whole `F = 0` column is now closed.** Under NR6, every walk with `F = 0` has
> `L ≥ 872` — equivalently `H + k + e + x ≥ 5`. **Correction (Round 116):** this does
> **not** imply `H + k ≥ 5`; `e` and `x` must stay explicit. **Codex audit of Round 115:
> PARTIAL** — `k = 0, 1, 4` independently confirmed; for `k = 2, 3` Claude's search was
> reproduced but Codex's independent SMT formulation timed out, so those two cells are
> CLAUDE-REPRODUCED, NOT INDEPENDENTLY CONFIRMED.
> All five cells `(k,F) = (0,0), (1,0), (2,0), (3,0), (4,0)` fall; **50 of the 55 outer cells
> remain, and every one of them has `F ≥ 1`.**
>
> The key new structural fact is **Lemma A**: with `F = 0` there are 120 passes and 720
> permutations, and a pass is a maximal rotation run so it has length ≤ 6 — therefore every
> pass has length **exactly** 6 and sweeps one whole hexagon, so **passes correspond
> bijectively to hexagons** and no two used words may share a hexagon. That is the exact
> generalisation of Round 113/114's orbit-level statement, and it is a hard constraint rather
> than a budget. It also identifies `D`: for `F = 0`, `Σ_h (mult(h) − 1) = 5O − 120 = 5k = D`,
> so `k` measures exactly the departure from a 24-orbit exact cover.
>
> The `k = 0` light-move classification does **not** transfer. `W3a` (always same orbit) and
> `W3c` (always hexagon-disjoint) are unchanged 720/720 facts, but **`W3b` can become legal
> once `k > 0`** — its source and target orbits share exactly one hexagon, which is precisely
> what `k = 0` forbade. Charging `W3b` to the defect budget does not work either: at a hexagon
> of multiplicity `m` the defect is `m − 1` while up to `m` of its `W3b` arcs are usable, so the
> usable count runs to `10k`, twice the budget.
>
> The rigidity that Round 113/114 exploited has an algebraic reason: every move is right
> multiplication in `S₆`, and the block map `D(u) = W3c(τ⁴u)` has **order 4 on all 720 words**.
>
> Round 115 counts **passes, not orbits** — orbits can be shared between chains, passes
> partition them exactly (`Σ πᵢ = 120`). An exhaustive search (91 budget cells, **zero cap
> hits**, 335 s) gives the chain capacity `N*(b,g,s)`; its `s = 0` axis reproduces Round 114's
> `M*(B) = 3B + 4` exactly, and it saturates at 24 orbits / 103 passes for `s ≥ 17`. That closes
> `k = 0, 1, 4` outright and leaves three subcases, which a joint multi-chain search — adding
> the constraint that chains are mutually hexagon-disjoint and together cover all 120 hexagons
> — kills exhaustively (19.1 G / 2.2 G / 2.2 G nodes, no cap hits).
>
> **Correction to Round 114.** Its conclusion stands and is re-derived here, but its model
> charged one budget unit for *every* incomplete orbit, while its own telescoping identity
> leaves one chain per split orbit uncharged. Under the corrected (more permissive) charging,
> Round 114's *orbit-counting* step no longer closes `(k,e,x,t) = (0,3,0,2)`; the pass-counting
> argument does. Round 114's document is preserved with a correction box.
>
> The greedy 873 walk is accepted with **false rejection 0** and attains the bound exactly:
> six chains of exactly 20 passes each, `= N*(0,0,0)`. The ledgers stay **4,782** and 6,396/6,396.
> This project has not proved `L₆ ≥ 872`; NR6 and 50 cells remain open.
>
> **Round 114 (phase-correlated run) — read this first.**
> **The `(k,F) = (0,0)` cell is now closed.** Under NR6, every walk with `F = 0` and `O = 24`
> has `L ≥ 872` — so no length-≤871 superpermutation can live there. This is the cell in which
> a length-867 walk (the Houston bound) would have to sit, and it is the first of the 55 outer
> cells to fall. **54 remain untouched.**
>
> The accounting unifies `r = 24…28` into a single requirement. Since every free arc is
> intra-run, `S = (r−1) + x` exactly (`x` = non-free intra-run arcs) and `H ≥ t−1` (`t` =
> number of maximal all-light chains), so `cost ≥ 22 + e + x + t` with `e = r−24`, and
> `L ≤ 871` demands `e + x + t ≤ 5`. Re-checking the light moves outside Round 113's scope:
> `W3b` remains unusable at **every** run endpoint (its target orbit always shares a hexagon
> with the source, 720/720, while the cover is pairwise disjoint), but **`W3a` can become legal
> at a short run end** — Round 113's exclusion only covered `m = 5`. Since `W3a` stays in the
> orbit it is an intra-run arc, charged to `x`, so the conclusion survives.
>
> Keeping `(orbit, used phases, current phase)` — never quotienting phase away — and allowing a
> run to jump to any unused phase at a charge of 1, an exhaustive search (no cap hits, using the
> transitive `S₆` relabelling symmetry) gives **`M*(B) = 3B + 4`**, the maximum number of
> distinct orbits one all-light chain can cover with budget `B = e + x`. Per-chain budgets
> telescope exactly, so `24 ≤ 3B + 4t`, hence `B + t ≥ (24+B)/4 ≥ 6`, hence `cost ≥ 28` and
> `L ≥ 872`. The greedy 873 walk sits exactly at the extremal point `B + t = 6` and is not
> falsely rejected. The ledgers stay **4,782** and 6,396/6,396.
> This project has not proved `L₆ ≥ 872`; NR6 and 54 cells remain open.
>
> **Round 113 (hub defect) — read this first.**
> A real sub-case falls. At `(k,F) = (0,0)` with `S = 23` — equivalently 96 free arcs,
> equivalently each of the 24 orbits traversed as one contiguous `τ`-run — **`H ≥ 5`, hence
> cost ≥ 28, hence `L ≥ 872`**. No length-≤871 counterexample can live there.
>
> The mechanism is a complete classification of the weight-≤3 moves (all verified 720/720):
> `W2 = τ` is free and stays in the E-orbit; `W3a` stays in the orbit at phase +2 and from a
> block end returns to an already-visited entry; **`W3b` is never usable**, because its target
> orbit always shares a hexagon with the source orbit while the cover's 24 orbits must be
> pairwise hexagon-disjoint; so **`W3c` is the only light connector**. Light connectors then
> follow the deterministic map `D(u) = W3c(τ⁴u)`, and a `D`-chain holds **exactly four**
> pairwise-disjoint orbits (720/720). Six chains are therefore needed for 24 blocks, forcing
> ≥ 5 heavy connectors, each of weight ≥ 4 and hub tax ≥ 1.
>
> **The bound is attained.** This repository's greedy 873 walk is exactly of this form: 24
> blocks, six light chains of lengths `[4,4,4,4,4,4]`, exactly five heavy connectors
> (`W3c`×18 + `w=4`×4 + `w=5`×1, hub tax 6).
>
> What remains at `(0,0)` is `r ∈ [25,28]` (`r` = orbit-run count); `r = 24` is the theorem and
> `r ≥ 29` is trivial. For `r ≥ 25` a run's exit is no longer forced to `τ⁴`, the chain map
> stops being deterministic, and the natural over-approximation collapses (chains of length
> ≥ 24) — a finer `(orbit, entry phase, exit phase)` state is needed. No cell is fully closed;
> the ledgers stay **4,782** and 6,396/6,396. This project has not proved `L₆ ≥ 872`, and NR6
> remains a separate assumption.
>
> **Round 112 (sharpened free-component bound) — read this first.**
> Exploiting the shortfall budget sharpened the bound threefold: the per-hexagon identity
> `Σ(5−ℓ) = 6(e_h−1)` forces every pass of a multiply-entered hexagon to be short, so the
> number of short passes is `F + m ≤ 2F`, not `6F` — and that is tight on the 872 witness
> (50 = 2·25). Hence `c(G₀) ≥ (24+k) − 2F` and `F + c ≥ 24 + k − F`, whose maximum over the
> feasible cells is **28 at (k,F) = (4,0)** — exactly one short of the 29 needed. A path-cover
> theorem was also proved (`non-free ≥ p − 1` with `p = I₀ + Z_bare` for out-degree-≤1
> digraphs), but `p = c` on both real walks because branching requires short passes and `τ` is
> injective at `F = 0`, so it gains nothing.
>
> **The target tradeoff is refuted.** `F + Q(G₀) ≥ 29` is false: this repository's own greedy
> n=6 superpermutation has `F = 0`, `c(G₀) = 24`, so `F + c = 24`. It is sufficient for
> `L ≥ 872` but not necessary, so it cannot be proved universally.
>
> The diagnosis is sharp. On **both** real walks the arc-*count* bound `S ≥ c − 1` is **exactly
> tight** (872 witness `S = 3 = c−1`; greedy 873 `S = 23 = c−1`). The entire residual gap is
> `H` — heavy joints of weight ≥ 4. The free-arc structure determines how many non-free arcs
> are needed, perfectly, and is blind to what they weigh. At `F = 0` the bound gives
> `L ≥ 867 + k`, reproducing the Houston constant exactly and no more; the missing statement
> is `H + (c − (24+k)) ≥ 5 − k`, i.e. `H ≥ 5` at `k = 0` — a claim about hub defects, not
> about `G₀`. No cell closed. The ledgers stay **4,782** and 6,396/6,396.
> This project has not proved `L₆ ≥ 872`.
>
> **Round 111 (generic (k,F) extension) — read this first.**
> The Q2 weighted argument generalises cleanly to arbitrary `F`. The right generic object is
> the set of **`120 + F` entry obligations** (hexagon, occurrence index), not 120 hexagons, and
> all four load-bearing hypotheses survive unchanged: the resource budget, the unique cost-0
> tail `T1` (there is exactly one weight-2 indecomposable tail), cost-0 out-degree ≤ 1 (entry
> words are distinct, so re-entries never collide), and the restricted component bound. The
> free arc was identified: `u ↦ T1(σ^ℓ(u))` equals `τ(u)` — the next phase of the same E-orbit
> — **exactly when `ℓ = 5`**, which is where `P ≤ 5O` and `D = 5k − F` come from. The rotation
> shortfall satisfies `Σ(5−ℓ) = 6F`, so `F = 0` forces every pass to be full and gives
> ℓ-forcing for free.
>
> These combine into one inequality: **`L ≥ 843 + F + c(G₀)`**, where `c(G₀)` counts the weak
> components of the free-arc graph on entries. So `L ≤ 871` requires `F + c(G₀) ≤ 28`, and
> proving `F + c(G₀) ≥ 29` for every non-repeating walk would give `L₆ ≥ 872` under NR6 — the
> 55-cell table compresses to a single line. The verified 872 witness attains **equality**
> (`F = 25`, `c = 4`, `843 + 29 = 872`), so the theorem is as strong as it can be. At `F = 0`
> it yields `L ≥ 867 + k`, recovering the Houston constant at `k = 0`.
>
> **But it closes none of the 55 cells.** All 55 remain arithmetically feasible, and the
> 6,396-state archive has `F = 1` throughout, so it represents exactly one cell, `(k,F)=(1,1)`;
> the other 54 contain zero states. A falsification pass also killed a tempting stronger claim:
> `O = 1 + S + F` holds with equality on all five named walks but fails on 85 of 169 exhaustive
> `n=4` walks — only the inequality survives. The audited ledger stays **4,782** and the
> full-joint Q2 result stays 6,396/6,396. This project has not proved `L₆ ≥ 872`.
>
> **Round 110 (outer reduction) — read this first.**
> Returning to the outer obligation turned up an error in the project's own foundation. The
> KO-RECORD's boxed length identity `L = 843 + cost = 867 + (k+N+H)` is **false on both real
> superpermutations this repository holds**: it gives 871 for the verified 872 witness and 872
> for the greedy 873. The corrected identity is **`L = 844 + F + S + H = 868 + (k+N+H)`**
> (general `n`: `L = n + n! - 2 + n!/n + F + S + H`), verified on five strings. The same
> off-by-one makes Theorem A `O <= S + F` false; the corrected `O <= 1 + S + F` holds with
> equality on both. The cause is that the first pass start opens an orbit without consuming a
> joint. `P = 120 + F` and `D = 5k - F` are correct as stated.
>
> Consequences: the conditional goal is `k+N+H >= 4`, not `>= 5`, and the engine's
> `final_target` corresponds to **`L <= 872`**, not `<= 871` — so the Q2 exclusion covers one
> unit more than needed, which does not weaken it. The corrected slab table for `L <= 871` is
> `k + H <= 4` and `F <= 5k`, giving **55 `(k,F)` cells**; Q2 covers exactly one of them,
> `(k,F) = (1,1)`. **54 cells are untouched**, and the original table omitted `k = 0` and
> `F = 0` entirely. The real 872 witness sits at `k=5, F=25`, one cell above the target band.
>
> What remains between a hypothetical `<= 871` superpermutation and the excluded Q2 population
> is therefore **not one theorem but three independent ones**: NR6 in its length-non-increasing
> form (currently an explicit assumption, not a proved normalisation), the `F` reduction, and
> the `k` reduction. An exhaustive small-`n` probe shows "no repeated window" holds exactly at
> the minimum length and breaks one character above it, so NR6 is not a free normalisation.
> The audited ledger stays **4,782** and the full-joint Q2 result stays 6,396/6,396.
> This project has not proved `L₆ ≥ 872`.
>
> **Round 109 (narrow completion) — read this first.**
> The 166 states Round 108 left open purely on the node cap are now all closed. They were
> frozen and hashed first (sha256 `d5d93ab8…`; verified inside the 6,396 population, inside
> the 1,353 conditional block, disjoint from the 5,043 robust block, no SAT pair, no stored
> witness), a regression control confirmed they still reproduce `UNKNOWN` at the old cap, and
> the **unchanged Round-108 full-550-tail model** was then re-run with staged per-call caps:
> 50,000 closed 104, 400,000 closed 47 more, 3,000,000 closed the last 15. Open assignments
> fell 4,032 → 421 → 35 → **0** over 256M search nodes and 9.67 h. Final: **166/166
> `UNSAT_COMPLETE`, 0 SAT, 0 UNKNOWN**, every one with an exhausted frontier.
>
> Together with Round 108's 6,230 this gives **6,396 / 6,396 of the Q2/Area-A residual
> population excluded in the full-joint model — 0 UNKNOWN, 0 SAT — with (H5) never used.**
> Every row records `h5_used: false` and `tails: 550`; no cap hit was ever counted as a
> closure. The audited ledger stays **4,782** and nothing here is independently audited.
> This project has not proved `L₆ ≥ 872`, and the outer Q1/NR6 reduction is untouched.
>
> **Round 108 (H5 resolution) — the current top of the ledger.**
> Round 107 exposed hypothesis (H5): the obligation graph used only the four weight-≤3 joints
> while the engine has 550 indecomposable tails. Round 108 split (H5) into three versions and
> settled them. **H5-local is false** — a literal weight-4 joint from an archived state lands on
> an obligation entry word and the engine does not prune it. **H5-replacement is false** — 11,200
> component pairs are joined only by heavy arcs against 1,869 joined by light ones. The hoped-for
> one-line corollary from the "H = 0 slab" **does not exist**: the `H_positive` prune is justified
> by *Target A's recognizer requiring H == 0 at the boundary*, which says nothing about the
> continuation, and `final_target` allows H ≤ 3.
>
> What replaced (H5) are two proved lemmas. **Theorem Z**: cost(w)=0 iff w=2 and there is exactly
> one weight-2 indecomposable tail, so `T1` remains the unique free arc even under all 550 tails —
> the zero-cost graph and the component bound are untouched. **Heavy-arc budget lemma**: with
> s = B − L2(ROOT), any in-budget completion satisfies Σ(cost−1) ≤ s over heavy arcs, so **s = 0
> makes heavy joints impossible and (H5) a theorem for that instance**. On the real population
> 81 % of assignments have s ≤ 0.
>
> Recomputing the 1,353 H5-dependent states with all 550 tails and **no (H5) assumption**:
> 240,756 assignments → 234,851 UNSAT, **0 SAT**, 5,905 node-cap UNKNOWN; per state **1,187 UNSAT
> COMPLETE, 166 UNKNOWN, 0 SAT**. Heavy arcs rescued nothing (`heavy_edges_in_surviving_paths` is
> empty). So the **H5-independent residual falls from 1,353 to at most 166**, and 6,230 of 6,396
> states are excluded regardless of joint weight. Classification: **C (PARTIAL)** — finishing the
> 166 at a larger node cap is the next step. Audited ledger stays **4,782**.
>
> **Round 107 (proof extraction).**
> Extracting the proof skeleton shrank the dependency chain and, in the same pass, exposed an
> **unstated hypothesis**. Shrunk: W-A, the (P) propagation, W-C/W-D/W-E, the exact
> graph-Hamilton closures and even the **Hall filter** all drop out — starting from all 90,396
> state–cover pairs and all 6,396 states, 707,007 concrete assignments are still UNSAT with 0
> cap hits and 0 survivors. The fragment `ΔF = 0` geometry lemma also drops out: `F` is
> monotone, every archived state already has `F = 1`, and the target demands `F = 1`.
> Exposed: the obligation graph is built from only the **four weight-≤3 joints**, but the
> engine has **550** indecomposable tails, and a weight-4 joint costs 2 against a budget of
> ~21 — the budget does not forbid it. Measured on 1,030 assignments, **12,062,293**
> obligation→obligation arcs reachable only by heavier joints are missing from the model.
> Consequently the result splits: the zero-cost arcs are `T1` alone even under the full move
> set, so the component bound survives, and **5,043 of 6,396 states are excluded regardless of
> joint weight**; the other **1,353** are excluded only under the added hypothesis (H5) that
> every future joint has weight ≤ 3. Two Round-106 statements are corrected: its node cap was
> a run-wide budget, not per-call (59.7 % consumed, not 0.6 %), and the resulting claim that
> "`B+1` revives 2,271 states / the collapse has no margin" is **retracted** — with the fix,
> `B+1` still closes everything.
>
> **Round 106 (closure hardening).** The corrected statement is now Theorem 1 (with the
> hypothesis and the `c` vs `c−1` case split), the hypothesis is proved structurally for Q2
> (Theorem 2) and checked 93.3 M times with 0 violations, and every weighted verdict was
> recomputed from scratch over a **superset** of the earlier population — all 27,095 Hall-passing
> pairs / 5,030 states, using none of the layers A/B2/D1/D4b and importing no Round-104 verdicts.
> 184,661 assignments, all UNSAT, **0 cap hits**, 0 surviving states; restricted to the archive
> population the subtotals reproduce Round 100/104 exactly (4,230 / 15,781 / 173,409). A
> standalone 17,350-row certificate and a separate verifier that does not import the certifier
> end with `VERIFIED — remaining states = 0`.
>
> ~~The collapse is nonetheless **fragile**, and Round 106 measured how fragile: raise the budget
> by exactly 1 and 2,271 states survive (as cap-induced UNKNOWN, not SAT).~~ **Retracted in
> Round 107 — that was a node-cap artifact; `B+1` closes everything too.** Strongest permitted
> wording: *within the current conditional Q2/Area-A pass model, Claude's independently
> reimplemented/replayed certificate exhausts the residual to zero.* That is **not** an audit,
> **not** an unconditional Q2 theorem, and **not** a proof of the lower bound. The audited ledger
> stays **4,782**. This project has not proved `L₆ ≥ 872`.

## The problem

A *superpermutation* on n symbols is a string containing every one of the
n! permutations of those symbols as a contiguous substring. Let L(n) be the
length of the shortest one. This repository's goal is to determine L(6).

## What is actually established (checked by code in this repo)

| n | proven minimal L(n) | source |
|---|---|---|
| 1 | 1  | `tests/test_exact_solve.py` — exhaustive search, proven in this repo |
| 2 | 3  | exhaustive search, proven in this repo |
| 3 | 9  | exhaustive search, proven in this repo |
| 4 | 33 | exhaustive search, proven in this repo (matches Ashlock & Tillotson) |
| 5 | 153 | **not** re-proven here (see below); cited from Chaffin, Diehl, Johnston, Kuperberg (2014) |
| 6 | **unknown**, in [867, 872]; upper bound 872 verified here, lower bound 867 | see below |

`src/exact_solve.py` implements a plain IDA* search and, run with no special
tricks, proves L(1)=1, L(2)=3, L(3)=9, L(4)=33 outright (`python -m
src.exact_solve`, `tests/test_exact_solve.py`). Run against n=5 with an 8-15
million node budget it does **not** finish — which is itself informative:
even n=5 needs smarter methods than textbook brute force, and that's a
solved case. n=6 is far further out of reach; see
`experiments/n6_search_baseline.py`, which runs the same solver against
n=6 and reports, honestly, that it is inconclusive after several million
nodes.

## The n=6 gap

- **Lower bound: 867.** Proven. First given by an anonymous poster on the
  4chan `/sci/` board (September 2011); formalized and published by Robin
  Houston with Jay Pantone and Vince Vatter:
  R. Houston, "Tackling the Minimal Superpermutation Problem",
  [arXiv:1408.5108](https://arxiv.org/abs/1408.5108) (2014).
  Formula: `L(n) >= n! + (n-1)! + (n-2)! + n - 3`, implemented in
  `src/lower_bound.py::houston_lower_bound`. For n=6 this evaluates to
  720+120+24+3 = **867**.

- **Upper bound: 872. Verified in this repository.** An explicit
  length-872 n=6 superpermutation (first found by Robin Houston in 2014
  with a TSP solver; archived at
  [github.com/superpermutators/superperm](https://github.com/superpermutators/superperm)
  under `superpermutations/6/`, which collects **44,120** distinct
  length-872 examples — treelike 42,288, nonstandard 1,024, slack1 772,
  slack2 36) has been checked directly here: all 720 length-6 windows are
  present and pairwise distinct. The string is
  `data/verified_872_witness.txt`; the replay check is
  `tests/test_872_witness.py`, which runs it through
  `src/verify.py::verify_superpermutation`, the same ground-truth checker
  used for every other claim in this repository. Its walk-weight
  fingerprint is 575 steps of weight 1, 141 of weight 2 and 3 of weight 3
  (6 + 575 + 282 + 9 = 872). At least **four non-isomorphic structural
  families** are known in the archive (treelike, nonstandard, slack1,
  slack2), differing in fragment count F and E-orbit count O.

- **This repository's own from-scratch search independently reaches 873.**
  `src/construct.py::greedy_construct` gives a self-verified n=6 witness of
  length **873**, matching the classical sum-of-factorials bound
  (720+120+24+6+2+1); see `experiments/n6_search_baseline.py`. It has not
  found the 872 improvement, which requires the non-greedy structure
  documented in the archive. That baseline is honest and stands.

- **The open problem is the LOWER bound, not the existence of 872.** A
  length-872 superpermutation demonstrably exists — that is settled, and
  verified above. What remains open is whether 872 is *minimal*, i.e.
  whether `L(6) >= 872`. The only proved lower bound available here is
  **867**. In this repository's coordinates `L = 867 + (k + N + H)`, the
  verified witness sits at `872 = 867 + 5`.

  A previous revision of this file recorded "no such string was available
  to independently check, and fabricating one would be worse than not
  having it", and described the *existence* of 872 as apparently open.
  That conflated an environment access limitation with a mathematical
  fact, and is **withdrawn**: the string above is a checkable element of a
  public archive, not a fabrication, and this repository now verifies it.

## About the research summary this repository started from

A long, highly detailed "progress summary" was provided as the task
description for the session that wrote the code in `src/`, `tests/`, and
`experiments/` (frag/rotation-pass decomposition, `F`, `P`, `S`, `H`, `O`
quantities, an `L = 867 + (k+N+H)` coordinate system, claims of a completed
forest-enumeration computation with specific certificate counts, a
partially-run exact-state search with specific node/state counts, etc.).

At that point **none of it was backed by anything in this repository** —
the repo contained a single commit: a one-line README. That part of this
document is no longer current: the actual local research corpus behind
that summary was uploaded afterward and is now integrated at
[`legacy_research/`](legacy_research/README.md). It is real, substantial,
and internally disciplined about proof status (it distinguishes proved /
finite-computation-certified / experimental-only / disproved throughout,
and its own final status table already marks the headline claims as
open). See `legacy_research/README.md` for the exclusions applied
(one 696MB in-progress checkpoint, `__pycache__`, compiled `.pyc` files)
and a summary of what that corpus does and does not establish.

**Three states need to stay distinct here, and the wording below is
deliberately precise about which one each number describes:**

1. **Latest state contained in the imported repository snapshot.** The
   numbers `expanded=36,250 / accepted=114,182 / frontier=77,932 /
   terminal=142 / success=0` are the last **committed** record inside the
   uploaded ZIP (`legacy_research/outputs/F1_N0_COMMITTED_RESUME_FINAL_STATUS.md`).
   This is a snapshot of one run at one point in time, not a live value.
2. **External live search state: unknown to this repository.** The
   external Windows process that produced that snapshot may have continued
   running afterward, on a different machine this repository has no access
   to. This repository cannot see, and does not claim to know, whatever
   that process's state is *now*. Any statement of the form "the search is
   currently at X" would be a fabrication — nothing here can observe that.
3. **`N=0` exhaustive search: incomplete**, independent of (1) and (2).
   Every checkpoint captured in this corpus records `completed=false` / an
   interrupted run; no artifact anywhere in this repository shows the
   `F=1,H=0,N=0` search reaching a terminal, verified conclusion.

None of the three licenses a claim that `L_6 >= 872` (conditionally, under
`NR6`) or `L_6 = 872` (unconditionally) is proved. The imported corpus's
own status table agrees, listing both as open, and nothing added in this
repository changes that.

## What this repository actually contains now

- `src/perms.py`, `src/verify.py` — permutation utilities and a
  ground-truth superpermutation checker (the thing everything else is
  checked against).
- `src/lower_bound.py` — the published, citation-backed Houston lower
  bound formula, and the classical sum-of-factorials upper bound formula.
- `src/construct.py` — a simple, correct, self-verified greedy
  constructor (not claimed optimal).
- `src/exact_solve.py` — a plain IDA* exhaustive solver, which proves
  L(1..4) from scratch and honestly fails to resolve L(5) or L(6) within a
  bounded node budget.
- `experiments/n6_search_baseline.py` — runs the above against n=6 and
  reports the (inconclusive) result plainly.
- `tests/` — 134 passing tests (`python -m unittest discover -s tests`)
  covering all of the above, including independent verification of a
  literature-sourced n=4 witness string.
- `legacy_research/` — the actual (much larger, much further along) local
  research corpus this project had already produced, integrated as-is;
  see its own README for scope and exclusions.
- `src/analyze_j_completion.py`, `src/verify_j_normal_forms.py`,
  `src/recover_j_witnesses.py`, `src/verify_j_witnesses.py`,
  `src/search_j_afterstate.py`, `research/*.md`, `outputs/j_*.json` — an
  audit of, and now full literal recovery for, the F=1,H=0,N=2 "J"
  charge-2 joint (abandonment weight>=3 into an already-used E-orbit).
  See "J-branch findings" below.

## J-branch findings (F=1,H=0,N=2, the charge-2 joint J)

Full detail in `research/J_COMPLETION_OBSTRUCTION.md`,
`research/J_FUTURE_DEMAND_BOUND.md`, `research/J_NORMAL_FORMS.md`,
`research/J_230_WITNESS_RECOVERY.md`, `research/J_EXACT_NORMAL_FORMS.md`,
`research/J_DECISIVE_EVENT_SEARCH.md`, `research/J_BRANCH_CLOSURE_STATUS.md`,
`research/N2_BRANCH_DECOMPOSITION.md`, `research/N2_CLOSURE_STRATEGY.md`.
Summary:

- **Proved, from definitions alone (no search):** once J occurs, F is
  exhausted (=`TARGET_F`), so no further abandonment is possible for the
  rest of that walk, and at most one further `R`-type joint is possible
  before the N budget (`Ndef+H<=3`) is exceeded. Every other remaining
  joint is forced into a narrow zero-charge alphabet. This reduces
  J-branch completion to the same kind of zero-charge scheduling problem
  as the still-unsolved `N=0` branch — a genuine reduction, not a
  shortcut. A further general argument (`R_blocked_w3_existing` and
  `Z2_blocked_w2_existing` have identical effect on F/O/D/P, differing
  only in N) shows `R` is **never arithmetically required** by any of
  the 230 J states — if it's ever geometrically required, that reason
  hasn't been found.
- **All 230 recorded J states now have a recovered, independently
  verified literal witness** (previously only 1 of 230 did). Recovery
  reproduced the exact same bounded search this corpus's own
  checkpoint_header already specifies (`node_limit=20000,
  max_macro_depth=6` — not a new or larger search) and found all 230
  target hashes just before that same node limit. Independent replay
  (`src/verify_j_witnesses.py`, calling the engine directly, not reusing
  the recovery script's own bookkeeping): **230/230 pass** every check
  (hash match, per-step transition reproduction, N<2 before J, N==2 at
  and after J, exact J deltas, final F/H/N).
- **A coarse per-state normal-form fingerprint (fragment shape, current
  shape, steps-since-J) groups the 230 into 21 classes, but that quotient
  is provably lossy**: 75 pairs of states share a fingerprint yet have
  different 1-step legal-continuation shapes (minimal counterexample
  recorded in `outputs/j_exact_normal_forms.json`). No coarser-than-exact
  normal form was found that guarantees isomorphic continuation trees.
- **A bounded, capped decisive-event search across all 230 seeds** (macro
  depth <=6, edge cap 3,000 each, raw/uncanonicalized for speed) found
  zero completions (expected — completion needs ~100+ more joints) but
  did find `remaining_cover_capacity_impossible` firing on at least one
  branch for 45 of the 230 seeds — the first empirical sign of an
  obstruction beyond pure resource arithmetic, though only on some
  branches of some seeds, not a proof.
- **J completability is still open**, and the closure-status classification
  is explicitly "C: reduction insufficient so far" (not "closed", not
  "reduced to fixed families") per `research/J_BRANCH_CLOSURE_STATUS.md`.

## Capacity obstruction: a proved monotone potential (F=1,H=0 slab-wide)

Full detail in `research/J_CAPACITY_OBSTRUCTION.md`,
`research/J_CAPACITY_CORE_CERTIFICATES.md`, `research/J4_COMPONENT_ANALYSIS.md`.
Following up on the 45/230 `remaining_cover_capacity_impossible` signal
above:

- **Proved (and verified against 11,920 real transitions with zero
  exceptions):** `Phi(S) = 5 + 6*(TARGET_P - S.P) - (720 - S.visited_count)`
  is a monotone potential — `Phi(child) = Phi(parent) + (rotation_run_length
  - 5)`, so it never increases along any legal move, and going negative
  proves the rest of that walk cannot complete. This re-derives the
  engine's existing (but previously just-cited) capacity prune as a real
  theorem, not a black box.
- **Slab-wide fact, not J-specific:** `Phi` at the very start of *any*
  complete F=1,H=0 walk is exactly 6 — across all 121 joints in the whole
  slab, total tolerable rotation shortfall is at most 6. All 230 J states
  inherit an already-tiny remainder of that budget: `Phi` is in
  `{0,1,2,4,5}` for every single one of them (216 of 230 at exactly 4).
- **All 45 observed capacity failures are now fully, mechanically
  explained and independently re-verified (45/45 pass):** each is exactly
  a state with small `Phi` followed by a short rotation run (`ell` mostly
  0) that exceeds it — nothing else is needed. R usage is provably
  irrelevant to this mechanism (R and Z2 have identical effect on `Phi`).
- **Extending the same search (still bounded, depth<=6, larger edge cap)
  found the same failure in 156 of the 230 seeds**, not just the original
  45 — strong evidence (not proof) that the 45/185 split was an artifact
  of how shallow the first search was, not a real distinction between
  seeds.
- Whether *every* J state (or the whole F=1,H=0 slab) is arithmetically
  doomed this way remains a conjecture, not a theorem — proving it would
  require showing no collision-free schedule can stay within the 6-unit
  slab-wide shortfall budget, which is a geometric question this
  potential argument alone cannot answer.

## Follow-up: full boundary formalization, finite charge-word reduction, deeper search

Full detail in `research/SHORTFALL_BUDGET_THEOREM.md`, `research/ZERO_CHARGE_SKELETON.md`,
`research/J_74_SURVIVOR_CLASSIFICATION.md`, `research/FUTURE_SHORTFALL_LOWER_BOUND.md`,
`research/J_BRANCH_BUDGET_CLOSURE.md`.

- **A self-caught-and-corrected error, recorded rather than hidden:** an
  early pass in this follow-up concluded completion requires `Phi>=5`
  throughout (not just `Phi>=0`), which would have meant 229 of 230 J
  states were already arithmetically dead. That was **wrong** — it missed
  that a walk can complete via a trailing rotation-only suffix after the
  last-ever joint. The corrected, verified conclusion:
  **`Phi>=0` is already the tightest bound obtainable from pure
  (P, visited_count) counting** — it cannot be scalar-strengthened without
  genuinely new (geometric) information. Section 3 of
  `SHORTFALL_BUDGET_THEOREM.md` documents the wrong claim and its fix.
- **Finite reduction achieved:** every future "shortfall word" compatible
  with a state's budget `Phi` collapses to a small enumerable catalogue of
  charge multisets — 1, 2, 4, 12, or 19 families depending on whether
  `Phi` is 0, 1, 2, 4, or 5 (all 230 states fall in this range). Also
  clarified: `Phi` oscillates (rises during rotation, drops at each joint)
  at the literal step level and is only non-increasing at joint
  boundaries — an important precision the original theorem statement
  glossed over.
- **Deeper bounded search, not a new full Area-A search:** extending the
  same minimal-failing-path search to depth<=15 with a larger (but still
  finite, single-run, no-checkpoint) edge budget found the same capacity
  failure in **221 of the 230 J states (96%)**, up from 156. Only 9 remain
  unresolved within this bound (3 of which are the most constrained,
  `Phi=0`, single-charge-word states).
- **Important logical caveat, explicitly flagged:** finding that *some*
  branch from a seed hits `Phi<0` does **not** show that seed itself
  cannot complete — other branches (different rotation-length choices)
  might avoid the collision. This work found failing branches, not proof
  that every branch from a given seed fails. That gap is exactly why this
  is reported as a strong bounded pattern, not a closure.
- No nontrivial arithmetic lower bound stronger than `Phi>=0`, and no
  useful vector potential beyond the scalar `Phi`, were found — both
  reported as honest negative results, not forced into false theorems.

## Follow-up: attempted seed-level exact closure of the remaining 9

Full detail in `research/J_9_SEED_LEDGER.md`, `research/J_9_EXACT_CLOSURE.md`,
`research/J_230_BOUNDED_SEED_CLOSURE_STATUS.md`.

- Built a canonical-memoized exhaustive search
  (`src/search_j_9_exact.py`) plus an independent pure-rotation-suffix
  decision procedure (`src/verify_pure_rotation_suffix.py`, 5/5 boundary
  cases pass against real engine rotation mechanics) and a read-only
  certificate verifier (`src/verify_j_9_certificates.py`, 9/9 pass).
- Ran it on all 9 remaining seeds. **All 9 came back `INCOMPLETE`** (not
  `CLOSED`, not `SUCCESS`) — at a node cap of 800 canonical states per
  seed (~38s each; canonicalization's 720-relabel cost limits throughput
  to ~20 states/sec), the frontier was still growing roughly 3x with
  essentially zero canonical-state merging. That means the true reachable
  canonical state count from here is very likely in the tens of thousands
  or more — well beyond what this session can exhaustively search.
- **A more conservative correction to how the 221/230 figure above should
  be read, made explicit here:** finding that *some* branch from a seed
  fails does not prove that seed cannot complete. So, strictly, **no
  single one of the 230 J states — not even the 221 — has been proven
  unable to complete.** The 221 figure means "at least one failing branch
  found," not "closed." This is more conservative than earlier summaries
  may have implied, and is corrected here explicitly.
- `search_j_9_exact.py` supports checkpoint/resume, so a future session
  can continue with a much larger node cap without restarting.

## Follow-up: hunting for a safe state-space reduction (not more node cap)

Full detail in `research/J_STATE_SPACE_REDUCTION.md`, `research/ZERO_CHARGE_GRAPH_STRUCTURE.md`,
`research/J_DOMINANCE_RULES.md`, `research/J_TERMINAL_DEMAND_PRUNES.md`.

- **Explained the branching, precisely:** at every depth measured (0-3,
  all 9 seeds), zero canonical duplicates appeared, and every legal child
  of a state shares the exact same `visited_count` — the ~3-4x growth per
  level is genuine width from *which orbit to jump to*, not from rotation-
  length variation or redundant re-exploration.
- **Proved a general "forced-ell" lemma:** at a state with budget
  `Phi=k`, the very next rotation-run length must satisfy `ell>=5-k` (an
  immediate corollary of the already-proved monotonicity identity). For
  the 3 `Phi=0` seeds this forces `ell=5` on every remaining step. It does
  **not** reduce branching, though: the joint-target choice (which orbit)
  is untouched by this lemma, confirmed empirically (149 unique states at
  depth 3, same as without it — a 0% reduction, reported honestly rather
  than oversold).
- **Proved the state-transition graph is acyclic** (a one-line
  consequence of `visited_count` strictly increasing every legal step) —
  but this only guarantees finiteness, not narrowness, and does not
  explain or fix the branching-width problem.
- **Tested 5 candidate dominance rules against real state pairs; 2
  falsified with concrete counterexamples, 3 left undetermined** (no
  qualifying pair found in a 6,045-state pool — not claimed safe).
- **Investigated, and could not establish:** any symmetry stronger than
  the existing left-S6 canonicalization, any provably-safe way to drop
  stale visited bits, or any arithmetic lower bound tighter than the
  already-proved `Phi>=0`. All reported as honest negative results.
- **No method met the requested 50% state-space reduction bar.** This
  round's contribution is explanatory (why the branching happens) and a
  filtered-out set of naive ideas that don't work, not a working
  reduction.

## U-branch (two-charge-1-defect words) findings

Full detail in `research/U_BRANCH_ARCHITECTURE.md`,
`research/RA2_EXACT_ANALYSIS.md`, `research/A2R_IMPOSSIBILITY_STATUS.md`,
`research/RR_INTERACTION_INVARIANT.md`, `research/RA3_A3R_ASYMMETRY.md`.

The N=2, depth<=6 corpus (25,660 states) splits exactly into J-branch
(single charge-2 defect, 230 states, see above) and U-branch (two
charge-1 defects, five ordered words: RR 4,470 / RA2 24 / A2R 0 / RA3
9,952 / A3R 10,984). This round advanced the U-branch side without
touching the N=0 search/checkpoint and without any new large-scale
search — witnesses were recovered by reusing the existing J-witness
recovery checkpoint's parent chains.

- **RA2 (24 states, all recovered literally): 20/24 proved unable to
  complete** via the same Phi capacity potential already proved for
  J-branch (finite exhaustive continuation search found a concrete
  Phi<0 killer for each). The remaining 4 (all Phi=5) stayed unresolved
  even at depth<=18/edge_cap=1.5M — reported as genuinely unresolved,
  not forced closed. **Not** "RA2 fully CLOSED."
- **A2R (0 observed in the corpus): the conjectured impossibility is
  DISPROVED.** A concrete, literally-verified witness reaches word A2R
  at macro-depth exactly 6 from the initial state (raw BFS), matching
  the corpus's own recorded depth bound. Of 5 candidate explanations for
  the non-observation, 4 are refuted by this witness; the remaining one
  (an artifact of the original `node_limit=20000` canonical search's
  node budget/ordering) is the best-supported explanation by elimination,
  though not directly proved.
- **RR interaction:** over the full 4,470-record corpus (not a sample),
  every state where the two R's resolve to the same incidence-component
  (10/4,470) is also a "chaining" state (first R's target = second R's
  source) — an exact implication with zero counterexamples. The converse
  fails (65/75 chaining states still show unresolved components). The
  structural reason for the forward implication is not proved (flagged
  as conjecture).
- **RA3/A3R order asymmetry — the strongest result this round.** Proved
  (deductively, from the model's F<=1 abandonment budget and the
  definition of `fragment_hex`) a single theorem explaining, for all
  four words RA2/RA3/A3R/RR at once, exactly when a "fragment" structural
  signal can appear: it requires an earlier abandonment in the same walk,
  and F<=1 permits only one. Verified exactly against the full corpus
  (25,430 records, 8/8 slot predictions match with zero exceptions) and
  the causal mechanism itself (a hidden zero-charge abandoning joint
  firing before the second event) was confirmed by literal replay on a
  20-state RR sample (20/20 confirmed).
- None of the four literal success criteria from the originating request
  were met exactly as stated; (2) is met in reversed form (disproof
  instead of proof) and (4) is met in the spirit requested (one unified
  interaction theorem) rather than as a state-count reduction. Recorded
  honestly in `U_BRANCH_ARCHITECTURE.md` rather than claimed as full
  success.
- The section-7 "Theta" composite potential was not attempted this
  round — explicitly left as future work, not silently skipped.

## RA2's 4 remaining unresolved states, and a second RR structural lemma

Full detail in `research/RA2_FOUR_SURVIVORS.md`, `research/FRAGMENT_DEBT_LEMMA.md`,
`research/RA2_THETA_POTENTIAL.md`, `research/RA2_COMPLETION_OBSTRUCTION.md`,
`research/RR_CHAINING_PROOF_STATUS.md`.

Follow-up round targeting the 4 RA2 states left unresolved above, plus
strengthening the fragment-asymmetry theorem into a quantitative
obstruction, plus another attempt at the RR chaining proof. No new
large-scale search; N=0 untouched.

- **The 4 U4 states are proved pairwise non-isomorphic.** Their R and A2
  events are literally identical across all 4 (same source/target
  orbit+phase for both); the only difference is how many zero-charge
  joints intervene. A shallow abstracted-signature comparison suggested a
  misleading "2+2" grouping at depth 1, but depth 2 refutes it exactly --
  since the comparison uses only labeling-independent resource deltas
  (P/F/S/H/O/D/Ndef), the depth-2 mismatch is a deductive proof that no
  structure-preserving equivalence can merge them. Verdict: 4 independent
  exact states, not further reducible.
- **A proven sub-lemma:** once F=1 (the walk's one abandonment spent),
  every legal joint for the rest of the walk must be abandonment=False
  ("blocked" type only) -- a direct consequence of F<=1 and extend()'s
  abandonment formula, verified computationally (0 violations among legal
  transitions, 24/24 seeds).
- **The requested scalar "fragment debt > 0 implies incomplete" lemma is
  false and not salvageable as stated** -- it is a tautology (restates
  "this hex isn't full yet", true of every unfinished hex) rather than a
  reachability argument; documented with a minimal abstract counter-model.
  A genuine byproduct, though: among all 24 RA2 states, fragment-debt=1
  after A2 exactly identifies the 4 unresolved states (24/24, no
  exceptions) -- an exact but unexplained (conjectural) correlation.
- **Theta potential:** Phi and orbit-slack are the only candidate
  coordinates proved monotone; fragment/phase slack monotonicity was
  left genuinely unresolved (a swap mechanism could in principle break
  it; no counterexample was found in bounded search either). No usable
  RA2-specific potential beyond Phi was obtained.
- Per this round's own instruction not to widen search bounds without a
  validated >=30% reduction from a real new prune, the requested
  family-local re-search was run at the specified initial caps only (no
  new prune existed to add) and, as expected, found nothing new --
  reported honestly as 0% improvement rather than silently re-running at
  larger bounds.
- **A second, real RR lemma:** if the two R's chain (first R's target
  orbit = second R's source orbit), the second R's own component relation
  is *never* "unresolved" -- proved deductively (the source orbit is
  automatically a registered union-find node, since it equals the first
  R's own target) and verified exactly against the full 4,470-record
  corpus (75/75 chaining states resolve to same-or-different, zero
  unresolved). The originally-requested exact direction (same-component
  implies chaining) remains unproved and un-refuted -- honestly left
  open, no valid abstract counter-model constructed either (it would
  require replicating the real S6 E-orbit/hexagon combinatorics).
- None of this round's four success criteria (U4 fully closed; U4 reduced
  to few subcases; fragment-debt/Theta proof; RR chaining proof) were met
  in their literal form. Two genuine proven lemmas came out of the
  attempts anyway (post-F1 blocked-only; chaining-implies-resolved) and
  are recorded as real, if partial, progress.

## RA2's zero-charge history: a clean closed-form identity, and the fragment-debt obstruction hypothesis is refuted

Full detail in `research/RA2_ZERO_CHARGE_HISTORY.md`,
`research/FRAGMENT_REPAIR_OBLIGATION.md`, `research/RA2_REPAIR_COST_LEMMA.md`,
`research/RA2_U4_CAUSAL_DIFFERENCE.md`.

Third follow-up round on RA2's 4 unresolved states, targeting a
quantitative completion obstruction from the zero-charge history between
R and A2. No new large-scale search; N=0 untouched.

- **Main result, a genuine theorem:** `Phi(state right after A2) = 1 +
  ell_A2 = 6 - fragment_debt`, exactly, verified over all 24 RA2
  witnesses with zero exceptions. Proof: while F=0, `f1_normal_form`
  forces the current hex to be a single contiguous arc, so its rotation
  successor is always unvisited until the arc reaches full length --
  meaning any abandonment=False ("blocked") joint can only fire once its
  own hex is already FULL. Consequently every joint before A2 (R itself
  and every intervening zero-charge joint) is forced to use the maximal
  rotation length (ell=5), leaving zero residual debt; only A2 itself
  (which requires abandonment=True) can leave a hex incomplete. The
  elaborate zero-charge word structure turns out to be causally
  irrelevant to the eventual fragment debt -- only A2's own preceding
  rotation length matters. This is an exact zero-charge-history invariant
  separating U4 (ell_A2=4) from C20 (ell_A2 in {0,1,3,5}), with zero
  exceptions among all 24.
- **The fragment-debt-as-obstruction hypothesis is refuted, not
  confirmed.** A bounded repair-cone search found 11-15 legal repair
  witnesses per U4 state (within a 20,000-node cap), the shallowest
  costing exactly 0 Phi and 0 orbit slack -- fragment repair is cheap and
  plentiful, not a bottleneck. Of the requested repair-cost lemma
  candidates: R1 (a targeted joint is required) is trivially proved; R2
  (repair costs at least 1 unit of slack) and R3 (repair cost exceeds
  budget) are both refuted with concrete zero-cost witnesses; R4 (orbit
  reuse conflicts with other demand) is left untested since no completion
  witness of this slab exists anywhere to check against.
- The requested combined invariant Omega collapses: Phi and fragment
  debt are the same information (per the identity above), so Omega's
  four components reduce to effectively two (Phi, orbit slack) plus a
  repair-accessibility term that turns out not to be scarce for U4 either.
- **Minimal counterfactual edit found:** replaying the same A2 move at
  every rotation length ell=0..5 immediately before it shows debt =
  5,4,3,(illegal),1,(not-A2) purely as a function of ell -- U4's debt=1
  and a typical C20's debt=4 differ by exactly one rotation step, not by
  any orbit-target choice (only one legal A2-type move existed at that
  point in the tested case).
- An attempted unification with the RR "chaining implies resolved" lemma
  from the previous round was tried and explicitly declined: both share
  a "most of the intervening history is irrelevant" theme, but rest on
  different mechanisms (orbit-hexagon union-find registration vs.
  hexagon-arc rotation mechanics) -- no forced merge.
- Of this round's four success criteria, none were met in their literal
  form (U4 not proved impossible; repair cost does NOT exceed budget --
  the opposite was shown), but criterion 3 (an exact invariant separating
  U4 from C20) was met via the ell_A2/Phi identity, and criterion 4 (few
  exact subcases) is satisfied in the sense that U4 reduces to the single
  parameter value ell_A2=4.

## ell_A2=4 geometry: A2R-like non-observation resolved, and an A2/A3 common theorem

Full detail in `research/A2_ROTATION_LENGTH_CLASSIFICATION.md`,
`research/RA2_ELL4_BOUNDARY_GEOMETRY.md`, `research/RA2_ONE_HOLE_LEMMA.md`,
`research/RA2_TERMINAL_COMPATIBILITY.md`.

Fourth follow-up round on RA2, moving past the fragment-debt line
(refuted last round) to directly classify the A2 rotation-length
spectrum and the exact post-A2 geometry it produces. No new large-scale
search; N=0 untouched.

- **ell_A2=2, unobserved in the 24-state corpus, is NOT structurally
  impossible.** A genuinely exhaustive raw BFS at depth<=6 (frontier
  fully exhausted at 12,367 nodes, well under any cap) confirms it is
  absent within the corpus's own recorded bound -- but a concrete witness
  was found at depth 7, one step beyond that bound. Same pattern as the
  earlier A2R non-observation: a depth-6 search-boundary artifact, not an
  impossibility. ell_A2=5 remains proved structurally impossible (the
  full-hex argument).
- **A controlled counterfactual** (same R-to-A2 prefix, same A2 move,
  only the rotation length before it varied) shows U4's ell_A2=4 differs
  from ell=0,1,2 not only in Phi, but also in an independent geometric
  fact: at ell=4 the move happens to land in an ALREADY-visited orbit
  (new_orbit=False), while at ell=0,1,2 the same move lands in a fresh
  orbit (new_orbit=True) -- a genuine additional distinguishing fact, not
  reducible to the Phi/debt identity alone. Whether this, or just Phi
  being high, explains why capacity-failure search finds violations for
  ell=0,1,2 but not ell=4 remains open (the two co-occur, not separated).
- Of the four "one-hole geometry" candidates: H1 (repair breaks
  terminal-compatibility) is refuted -- repair witnesses pass every known
  necessary condition; H2 (repair forces reuse of an existing E-orbit) is
  proved true (4/4 shortest repair witnesses use new_orbit=False); H3
  (holding the hole traps future moves in one phase class) is refuted;
  H4 ("incidence parity") is left unresolved for lack of a precise
  definition of the term in this codebase.
- **A2/A3 common theorem, confirmed:** the F=0 full-sweep argument behind
  Phi=1+ell=6-debt never used the abandoning move's weight, so it applies
  identically to A3. Verified directly against 60 A3R witnesses: 60/60
  match the identity exactly, and all pre-abandonment joints use ell=5.
  A3R's ell_A3 distribution (sample of 100) covers all five values
  {0,1,2,3,4}, independently confirming ell=2's absence in RA2 was a
  small-sample artifact, not a structural gap.
- Of this round's four success criteria: (1) ell_A2=2's status is fully
  resolved (not impossible, depth-7 witness); (4) the A2/A3 common
  theorem is established with deductive proof plus computational
  confirmation. (2) and (3) were only partially advanced -- no full
  boundary-only obstruction was proved, and U4 reduces to one shared
  parameter value (ell_A2=4) but not a further geometric subclassification
  beyond that, since the 4 states' finer geometry is individually
  distinct (consistent with their proven pairwise independence).

## Abandonment target novelty: (ell, nu) is not a free 2D space, and every obstruction candidate this round was non-binding

Full detail in `research/ABANDONMENT_TARGET_NOVELTY.md`,
`research/RA2_ORBIT_REUSE_CHARGE.md`, `research/EXISTING_TARGET_ABANDONMENT_OBLIGATION.md`,
`research/RA2_ORBIT_DEMAND_MATCHING.md`.

Fifth follow-up round on RA2, examining whether the rotation length
(ell_A) and target-orbit novelty (nu_A: existing vs. fresh) jointly
determine a completion obstruction for U4. No new large-scale search;
N=0 untouched.

- **Central re-derivation:** (ell_A, nu_A) is not an independent 2D
  space. This project's own established joint taxonomy already fixes
  nu_A by which named event you're looking at -- "A2" is DEFINED as
  (weight=2, abandonment, new_orbit=False) and "A3" as (weight=3,
  abandonment, new_orbit=True); the other two weight/novelty
  combinations are different joint kinds entirely (Z2abandon,
  zero-charge; J, the charge-2 J-branch event, a disjoint corpus).
  Re-extracted and confirmed over 622 real abandonment events (RA2's 24,
  a 300-state RA3 sample, a 298-state A3R sample): every existing-target
  (nu=0) event is from RA2 (24/24), every RA3/A3R event is fresh-target
  (598/598). This decomposes the "2D truth table" into two already
  largely-understood 1D spectra (ell_A2, ell_A3) rather than a genuine
  2x2 combinatorial space.
- Direct computation shows U4 never actually faced an existing-vs-fresh
  *choice*: at every rotation length tested, at most one legal weight-2
  abandoning move existed, and its novelty was fully determined by that
  length -- there was no alternative to forgo. A local and a global
  version of the requested "orbit-reuse charge" rho_A were both
  evaluated and found non-binding (global orbit-opening slack is 92-93,
  nowhere near tight).
- H2 (repair reuses an existing orbit, proved last round) resisted every
  strengthening attempt: H2a (reuses A2's own target orbit) and H2c
  (repair costs exactly 1 unit of orbit slack) are refuted with concrete
  counterexamples; H2b (reuses A2's own source component) is refuted
  because that component isn't even registered at that point; H2d is
  left unresolved.
- A minimal Hall-type check (fragment hole as the sole demand, its found
  repair witnesses as supply) trivially holds -- no violating subset
  found, though a full bipartite model over all remaining completion
  demand was explicitly out of scope (would amount to the full
  completion search).
- Of this round's five success criteria, only (1) (a complete local
  truth table for (ell_A, nu_A)) was achieved -- and in a form that
  corrects the round's own premise rather than confirming it. Criteria
  (2), (3), (4), (5) were all attempted and came back non-binding or
  refuted; the round's honest conclusion is that existing-target
  novelty, as an axis, is not a further source of leverage on U4 beyond
  what the ell_A2 spectrum already gives -- closing U4 will need a
  different kind of argument than local rotation-length/orbit-novelty
  geometry.

## RA2 <-> A2R defect-order exchange: a proven adjacent-exchange theorem, a sharp A2R minimum-depth result, but no new leverage on U4

Full detail in `research/RA2_A2R_EXCHANGE_THEOREM.md`, `research/A2R_MINIMUM_DEPTH.md`,
`research/U4_EXCHANGE_OBSTRUCTION.md`, `research/U_BRANCH_DEFECT_ORDER_INVARIANT.md`.

Sixth follow-up round, moving from RA2's local post-A2 geometry to the
defect-order exchange structure between RA2 (R then A2) and A2R (A2 then
R). No new large-scale search; N=0 untouched.

- **Adjacent-exchange theorem, proved:** for all 10 RA2 witnesses where R
  and A2 are macro-adjacent (no zero-charge joint between them), swapping
  A2 before R is impossible for a single, general, structural reason: R's
  own pre-boundary hex is always forced to be fully swept (the F=0
  full-sweep theorem from an earlier round), so no further rotation is
  possible from that exact point -- any nonzero ell_A2 collides
  immediately. Verified 10/10; the analogous bubble-sort generalization
  to the full zero-charge word was attempted and refuted by a
  counterexample (a later joint in the word is often preceded by a
  freshly-restarted hex, not a full one, so the same obstruction does not
  automatically propagate).
- **A2R's minimum depth, pinned down exactly:** depth 6, with a UNIQUE
  canonical witness at that depth (exhaustive raw BFS, frontier fully
  consumed at 2,853 nodes). Explained quantitatively: A3 is legal as the
  walk's literal first move (3 legal options from the true initial
  state), R requires only that its own starting hex be fully swept
  (still the walk's first macro-edge), but A2 requires at least 4 prior
  joints (minimum depth 5) before any existing-target weight-2
  abandoning move becomes available -- confirmed by direct enumeration
  (0 legal existing-target weight-2 moves from the initial state).
- **U4 turned out to be outside this round's classification entirely:**
  all 4 U4 states have a nonzero zero-charge word between R and A2, so
  the proved adjacent-exchange theorem doesn't apply to them, and the
  exchange-distance measure chi (A2R's global minimum depth minus how
  deep each RA2 witness itself reaches A2) does not separate U4 from
  C20 -- both span the same {0,1} range.
- A new defect-order invariant emerged as a byproduct: the minimum
  macro-index at which each event type can first appear (A3: 0, R: 0 but
  gated by a full sweep, A2: 4) -- this offers a plausible (though
  unverified quantitatively) explanation for why RA3/A3R's corpora are
  ~400x larger than RA2's within the same depth<=6 bound.
- Of this round's five success criteria: (1) the adjacent R/A2 diamond
  lemma and (2) A2R's exact minimum-depth theorem were both achieved
  with genuine proofs. (3) (an exchange obstruction separating U4) and
  (5) (a general RA3/A3R exchange theorem) were not achieved -- reported
  honestly as another round where U4 itself resisted the specific new
  angle tried, even though the angle produced real theorems elsewhere.

## R-to-A2 word restart-block decomposition: a new exact U4 signature, and a generalized barrier lemma

Full detail in `research/U_BRANCH_RESTART_BLOCKS.md`, `research/A2_PREREQUISITE_DAG.md`,
`research/RA2_RESTART_BARRIER.md`, `research/U4_RESTART_ANCESTRY.md`,
`research/U_EVENT_FIRST_INDEX_THEOREM.md`.

Seventh follow-up round, decomposing the zero-charge word between R and
A2 into "restart blocks" to look for long-range prerequisite structure.
No new large-scale search; N=0 untouched.

- **Proved (deductive + exhaustive verification over all 107 relevant
  joints):** every joint before A2 fires (R itself and all intervening
  zero-charge joints) must target a completely FRESH hexagon (0 bits
  visited) -- f1_normal_form's F=0 single-partial-hex constraint rules
  out any other option. So at the hex level the requested 6-way restart
  classification collapses to a single case; the real per-block variation
  is at the orbit/component level.
- **A new, exact U4 signature found:** decomposing each RA2 witness into
  R + word-blocks + A2, the 11 witnesses with exactly one intervening
  block split perfectly along group lines -- all 9 C20 cases reuse R's
  own target orbit literally (component "same"); both U4 cases instead
  open a completely unrelated fresh orbit (component "unresolved"). The
  2 two-block U4 states contain exactly the C20 pattern as an optional
  first block, plus this same critical fresh-orbit block appended before
  A2. All 4 U4 states share this exact critical-restart signature with
  zero exceptions -- but it is necessary, not sufficient, for U4
  membership (one C20 outlier shares it too, differing only in the
  already-known ell_A2).
- **Restart-barrier lemma B1, proved and verified over all 107 full-swept
  block boundaries in the corpus (not just R's):** after any block that
  ends in a fully-swept hex, no nonzero-length rotation is possible from
  that exact boundary, generalizing last round's adjacent-exchange
  finding beyond the R-specific case.
- **Completed the event-first-index table** for all 7 joint kinds:
  A3/Z2abandon/R/Z2/Z3 all have minimum first-appearance index 0-1;
  A2 alone requires index 4; J (the other existing-target abandonment)
  needs only index 1 -- isolating "weight-2 existing-target" as the
  specific hard combination. Confirmed the arithmetic identity
  d_min(A2R) = i_min(A2) + 2 = 6 exactly.
- Of this round's four success criteria: (2) the barrier lemma
  generalization and (3) an exact restart-block invariant for U4 were
  both achieved (with the necessary-not-sufficient caveat stated
  honestly). (1) the full prerequisite-DAG proof of why i_min(A2)=4
  exactly stayed qualitative, not fully deductive. (4) RA3/A3R
  application produced a plausible explanation for corpus-size asymmetry
  but not a proven general theorem.

## Five-state focused comparison: a corpus-exact classifier, a methodological correction, and ell_A2 confirmed forced not chosen

Full detail in `research/RA2_FIVE_STATE_COMPARISON.md`, `research/RA2_CRITICAL_RESTART_CLASSIFIER.md`,
`research/RA2_CRITICAL_RESTART_ANCESTRY.md`, `research/A2_PREREQUISITE_DAG_PROOF.md`.

Eighth follow-up round, narrowing to exactly 5 states (U4's 4 plus the
one C20 outlier sharing U4's critical-restart signature) for a tight
comparison. No new large-scale search; N=0 untouched.

- **Methodological correction, found and fixed:** the prior round's
  per-block "component_relation" computed a block's "source" from the
  position *before* that block's own rotation run -- but canonicalize()
  resets the walk's literal position to the identity after every
  macro-edge, so that "source" was always orbit 0 regardless of which
  block was examined, a canonicalization artifact rather than genuine
  per-block information. Switched to a direct, unambiguous comparison
  (literal target-orbit index vs R's own target-orbit index) and
  reconfirmed the prior finding survives intact under the corrected
  definition.
- **Corpus-exact classifier achieved:** "critical-restart target orbit
  differs from R's own target orbit" AND "ell_A2=4" correctly classifies
  all 24 RA2 states (4 true positives, 0 false positives, 20 true
  negatives, 0 false negatives) -- though flagged honestly that ell_A2=4
  alone already fully determines this on its own; the restart-signature
  term adds no extra discriminating power within this corpus.
- **The critical restart is LITERALLY identical (same source, target
  orbit, phase) across all 4 U4 states and the C20 outlier** -- the only
  field that ever differs among these 5 states is ell_A2 itself (4 for
  U4, 0 for the outlier).
- **Proved ell_A2 is forced, not a free/lucky choice:** enumerating
  every rotation length 0-5 at the post-critical-restart boundary for
  all 5 states shows exactly one legal A2 option per state, and its
  length is fixed by the state (U4: only ell=4 works; outlier: only
  ell=0). Since the critical restart itself is identical, the forcing
  factor is the *accumulated* orbit-touching history from the blocks
  preceding it (the outlier passes through 3 extra preparation blocks
  U4's states skip), not the critical restart in isolation.
- A depth<=6 continuation-tree comparison across the same 5 states found
  zero capacity-failure prunes for any U4 state, versus 4 total for the
  outlier starting at depth 4 -- confirmed the already-known Phi gap
  under this tighter control, framed as a bounded "escape-transition"
  observation rather than a new independent mechanism.
- Ancestry theorem candidates C1-C4 were tested directly: C1 refuted
  with a concrete counterexample; C2/C3 left undefined for lack of a
  precise formalization; C4 true but a restatement of the already-known
  Phi/debt identity.
- A new, sharp asymmetry surfaced in the RA3/A3R ledger (sampled, no new
  search): A3R shows exactly 0/150 cases where the critical restart
  before R reuses A3's own target orbit, versus RA3's mixed 38/150 --
  reported as an observation/conjecture, not connected to a proven
  general theorem.
- The three-round-running open problem (a full deductive prerequisite-DAG
  proof for why i_min(A2)=4 exactly) remains unresolved; recorded
  honestly as still incomplete rather than forced.

## A2 legality predicate, minimal sufficient statistic, and an exact U4/outlier causal certificate

Full detail in `research/A2_LEGALITY_PREDICATE.md`, `research/A2_ELL_FORCING_HISTORY.md`,
`research/A2_MINIMUM_INDEX_PROOF.md`, `research/U4_HISTORY_CAUSAL_CERTIFICATES.md`,
`research/RA3_A3R_ORBIT_HISTORY_ASYMMETRY.md`.

Ninth follow-up round, formalizing exactly why a given rotation length
becomes the unique legal choice for A2. No new large-scale search; N=0
untouched. Two real bugs were found and fixed mid-round (see below).

- **Key simplifying fact:** this entire model has exactly ONE weight-2
  move (`w2:10`) -- explaining why every earlier round observed "at most
  one legal weight-2 abandoning move" at any boundary: there was never a
  second candidate to begin with.
- **Two bugs found and fixed while building the per-ell candidate
  table:** an initial version assumed A2 was always the last macro-edge
  in a witness's path (false -- some witnesses have trailing zero-charge
  joints after A2), and after fixing that, a second version returned the
  state already offset by that witness's own ell_A2 rotations rather
  than the true fresh-landing origin. Both were caught by cross-checking
  against the corpus's own recorded ell_A2 values and fixed; the
  corrected candidate table now reproduces the known ell_A2 exactly for
  all 24 RA2 states, with exactly one legal ell per state (matches prior
  rounds' 5-state finding, now confirmed corpus-wide).
- **Exact minimal sufficient statistic obtained and verified:** H_A2(S)
  = (S.p, plus for each ell=0..5 whether the single candidate target is
  visited and whether its orbit is pre-existing) provably determines A2
  legality by construction, and this was checked against real data
  (grouping the 24 witnesses by this statistic exactly separates them
  into consistent legal-vector classes).
- **Exact causal certificate for U4 vs the C20 outlier:** all 4 U4
  states share a literally identical 6-candidate table (same orbit
  sequence at every ell). The entire difference from the outlier is
  that orbit 1 is pre-touched in U4's accumulated history (making ell=4
  the unique legal choice) but not the outlier's, while orbit 120 is
  pre-touched in the outlier's history (making ell=0 its unique legal
  choice) but not U4's -- the two most literal, verifiable facts
  separating them.
- The three-round-running open problem (a deductive, BFS-independent
  lower-bound proof for i_min(A2)=4) remains unresolved for a fourth
  round -- reported honestly; the exhaustive-search-based proof stays
  solid (re-verified, frontier fully consumed).
- A new sharp fact confirmed over the FULL stored ledger (not a sample):
  A3R shows exactly 0/298 cases of the critical restart before R reusing
  A3's own target orbit, versus RA3's 75/300 -- reported as an exact
  corpus observation, explicitly not claimed as proven impossible (this
  project's repeated "non-observation is not impossibility" lesson from
  A2R and ell_A2=2 applies here too).

## Tenth follow-up round: unique weight-2 move proof, H_A2 necessity, and an A3R falsification

Tenth follow-up round. Explicitly told not to repeat the i_min(A2)=4
direct-proof attempt again; redirected toward (a) a genuine
group-theoretic proof of why there is exactly one weight-2 move, and
(b) the two-orbit occupancy structure behind A2 legality and U4. No new
large-scale search; N=0 untouched.

- **Genuinely proved (not enumerated) that `tail_permutations(2)` has
  exactly one element for ANY width-2 tail** (general fact, not
  n=6-specific): from the `is_indecomposable` definition, w=2 only
  checks one prefix condition (`pi(0)=0`), which exactly one of the two
  length-2 permutations violates. Also derived and verified (11 sampled
  p0 values) the closed form `target(ell) = compose(p0, Sigma^ell *
  action)` -- the six A2 candidates are p0 composed with 6 FIXED,
  p0-independent group elements. `research/UNIQUE_WEIGHT2_MOVE_THEOREM.md`.
- **H_A2 sufficiency proved by construction; necessity only 1/3
  confirmed by exact witness:** the `existing`-bit's necessity has a
  real witness pair (U4 vs the C20 outlier, identical `visited` status,
  differing `existing` status, differing legality); the `visited`-bit
  and `S.p` component necessity remain deductive-only, no exact witness
  pair found this round. `research/A2_MINIMAL_SUFFICIENT_HISTORY.md`.
- **Orbit 1 / orbit 120 given coordinate-invariant names:** orbit 120 is
  literally the E-orbit of the unique weight-2 action itself (its
  canonical rep equals SIGMA); orbit 1 is the ell=4 candidate's own
  fixed group element, sharing exactly one hexagon (hex 0) with orbit
  120. The two-bit table across all 24 RA2 witnesses shows
  `(existing(ell=4 cand)=T, existing(ell=0 cand)=F)` exactly
  characterizes U4 (4/4) and the reverse exactly characterizes the
  outlier (1/1) -- but the 4th combination `(T,T)` is unobserved (0/24)
  and `(F,F)` doesn't uniquely determine the legal ell by itself, so
  this stays a corpus exact observation, not a general theorem.
  `research/A2_TWO_ORBIT_CAUSAL_THEOREM.md`.
- **Unexpected structural finding:** replaying all 5 focus witnesses
  (U4 x4 + outlier) in a fixed, never-canonicalized frame shows NEITHER
  candidate orbit ever "opens" during the tracked pre-A2 history -- one
  of the two bits is already true from the word's absolute start
  (literally equal to orbit 0, the E-orbit of the starting identity
  permutation itself) and the other stays false the entire time. The
  requested opening-history counterfactual analysis doesn't apply to
  this corpus for that reason; the occupancy automaton built from these
  5 exact traces is consequently degenerate (zero transitions), so it
  cannot be promoted to an i_min(A2)=4 lower bound (would require the
  full state-space search this round was told not to repeat).
  `research/A2_OCCUPANCY_AUTOMATON.md`, `research/U4_ORBIT_HISTORY_CONFLICT.md`.
- A bounded post-A2 depth<=3 tree comparison (all 5 focus witnesses,
  frontier fully consumed) found no controlled way to test "same history
  delays capacity failure" (U4 and the outlier fire A2 at different ell,
  so it's cross-sectional, not controlled) -- reported inconclusive
  rather than confirmed. Of the four candidate U4-closure obstructions
  (O1-O4), only O1 was clearly refuted by this round's data; O2-O4
  stayed undecided for lack of evidence.
- **A3R reuse-impossibility hypothesis falsified:** a small bounded
  (depth=1, one `macro_edges()` call per state) search over the FULL
  298-witness A3R corpus found that a legal, unpruned R-kind joint
  reusing A3's own just-opened target orbit exists at depth 1 for
  298/298 witnesses. This means the earlier round's "0/298 no reuse"
  fact was about which specific path each stored witness's own recorded
  macro_path happens to take, not a structural endpoint/phase
  impossibility -- immediate reuse is trivially reachable everywhere it
  was checked. `research/A3R_TARGET_REUSE_STATUS.md`.
- The i_min(A2)=4 direct-proof attempt was NOT repeated this round, per
  explicit instruction; its status is unchanged from the ninth round
  (exhaustive-search-verified, not deductively proven).

## Eleventh follow-up round: RR same-component vs chaining, full 4,470-witness literal recovery

Eleventh follow-up round. Moved from the A2/U4 local-history axis (closed
out for this round per explicit instruction) to RR's open "two R events in
the same incidence component implies chaining" question. No new
large-scale search; N=0 untouched. Reused the existing depth<=6,
node_limit=20,000 J-witness recovery search (same bound as prior rounds)
to literally recover the FULL 4,470-witness RR corpus for the first time
in this session (previously only a 300-witness sample was available).

- **Full literal recovery**: all 4,470 RR witnesses (not a sample) now
  have complete macro_path replays in `outputs/rr_literal_witnesses.json`
  (12MB). This let every claim below be checked by independent literal
  replay, not just by cross-referencing the corpus's own precomputed
  fields.
- **same-component (R2's own source/target orbit roots equal) implies
  chaining (R1's target orbit == R2's source orbit): re-confirmed over
  the full 4,470, zero counterexamples, verified by two independent
  scripts** (`analyze_rr_chaining.py`'s own aggregation and
  `verify_rr_chaining_theorem.py`'s separate re-derivation from the raw
  per-witness rows).
- **New mechanism found and exhaustively verified (75/75, the full
  chaining subset): within the chaining witnesses, R2's own
  component_relation is "same" if and only if hex 0 -- the hexagon
  containing the WORD'S OWN STARTING PERMUTATION, uniquely registered
  from `initial_state()` itself -- was touched by some event before R2
  fires.** The sufficiency direction is fully deductive (plain
  union-find semantics once hex 0's special pre-registration is
  granted); the necessity direction is exhaustively verified over the
  full corpus but not proved as a fully general law.
- **Incidence forest property re-confirmed exhaustively**: across every
  pre-joint and post-joint state in all 4,470 RR witnesses (53,054 state
  checks) plus a broader 85,238-state depth<=6 sample, zero
  redundant/cycle-closing union-find merges were ever found.
- **Abstract countermodel constructed**: a small hand-built bipartite
  incidence model, respecting every graph-level axiom the corpus obeys
  (bipartite, degree caps, forest, R-legality) but NOT the specific
  permutation-level fact about hex 0, produces same-component with
  non-chaining -- proving the corpus's exact implication is not a pure
  graph theorem and requires the hex-0 pre-registration fact
  specifically.
- **One incidental correction**: literal replay showed RR words can
  contain a hidden zero-charge `Z2_abandon_w2_new` event that flips F
  from 0 to 1 partway through -- so the earlier "F=0 regime forces every
  joint's target hex fresh" theorem (proved for the strictly-before-A2
  window) does NOT generalize to all of RR as such; this round's own
  results do not depend on that theorem and were obtained by direct
  literal replay instead.

## Twelfth follow-up round: the Unique Hub Hexagon lemma, generalizing hex-0 necessity

Twelfth follow-up round, pushed specifically to go past re-confirming the
75/75 statistic and find either a real proof or the precise minimal axiom
gap. No new large-scale search; N=0 untouched.

- **New general, fully deductive lemma (Unique Hub Hexagon), proved from
  `f1_normal_form`'s own documented F<=1 invariant and re-confirmed
  exhaustively over all 4,470 RR witnesses (0 exceptions)**: in any
  F<=1-budget word, AT MOST ONE hexagon is ever the target of two or
  more different joints over the word's entire history (its "hub", if
  one exists at all). This generalizes last round's "hex 0" finding:
  orbit 0's component can only grow beyond the trivial pair {orbit 0,
  hex 0} if hex 0 itself becomes that hub -- i.e. if the word's one
  allowed abandonment fires while still inside hex 0 (the very first
  joint of the word).
- **Necessity direction narrowed to a single, precisely identified
  remaining gap**: same-component (R2) requires both R2's source and
  target orbit to connect through the hub -- proved in general. Within
  this depth<=6 corpus, the hub (when it exists) is exhaustively
  confirmed to be touched EXACTLY twice, and in all 10 same-component
  witnesses the second touch is always R1 itself (never a third,
  unrelated event) -- an exhaustive, corpus-exact fact, honestly
  labeled a "necessary axiom, not a general proof" since whether this
  holds beyond depth 6 is untested.
- **Abstract-model axiom ablation pinpointed the exact missing axiom**:
  adding a bare "at most one hub hexagon" cardinality cap to the round-11
  countermodel does NOT eliminate it; only additionally requiring "the
  hub's second touch must be R1 itself, not a third party" does. This is
  a genuinely new, precise result -- not a graph axiom, a fact about
  event roles within the word.
- **Bounded local search (depth<=5, exhaustive within bound, from all
  10 same-component witnesses' post-R1 states) found zero
  same-component-non-chaining candidates** -- strong local evidence,
  not a full proof.
- **New completion-cost finding**: R2's own already-proven-tight Phi
  potential is exactly 0 for all 10 same-component witnesses (vs. mean
  3.68 for non-chaining and 4.91 for chaining-but-different) -- these
  10 states sit exactly on the proven Phi>=0 completion boundary, with
  zero tolerance for any further ell<5 move. Reported as a corpus-exact
  correlation, not claimed as a proven causal mechanism.

## Thirteenth follow-up round: Hub Touch Count <=2 proved, "hub=R1" corrected, closure INCOMPLETE

Thirteenth follow-up round, explicitly pushed past re-confirming
statistics toward either a real proof or a precisely isolated gap. No
new large-scale search; N=0 untouched.

- **New lemma proved fully deductively (Hub Touch Count <= 2)**, purely
  from `current_hex`'s own code definition (`hexagon_id(state.p)`) plus
  the already-established F<=1 budget: whenever a hexagon receives a
  second joint-target (a "hub"), that event makes the hub the new
  current hex; since F is already spent, the hub can never again be
  abandoned, so its remaining positions can only be visited by pure
  rotation until it closes forever. Re-confirmed exhaustively over all
  4,470 RR witnesses (0 violations). This upgrades last round's
  corpus-exact-only observation to a genuine, depth-independent proof.
- **Self-correction: round 12's claim "the hub's second touch is always
  R1 itself" is FALSE.** Literal replay found 6/10 same-component
  witnesses where a separate zero-charge event -- not R1 -- completes
  the hub, reusing R1's own target ORBIT via a different phase/hexagon.
  The real, corpus-exact (10/10) necessary condition is purely about
  orbit identity, not event identity: "the hub completer's target orbit
  equals R1's target orbit," independent of which literal event
  performs the completion. The abstract-model axiom ablation (M2) was
  already encoding this correctly at the orbit level; only round 12's
  prose description was too strong.
- **Deep bounded re-search (depth<=9, exhaustive within bound, node_cap
  60,000 per witness) from all 10 same-component witnesses'
  post-abandonment states, exploring ALL reachable R1/R2 choices (not
  just the corpus's own recorded path)** -- one witness alone had 121
  alternative non-R hub-completing candidates before any R fired -- and
  still found zero same-component non-chaining counterexamples. This is
  substantially stronger local evidence than last round's depth<=5,
  fixed-R1 check.
- **Phi=0 continuation confirmed structurally forced by the F<=1
  budget** (not independently by Phi itself): every ell<5 candidate
  after R2 is pruned as `F_exceeded`, and the hub can never be
  re-touched (by the new Hub Touch Count lemma) -- both directly
  verified against `area_a_prune_reason`.
- **Bounded closure search (node_cap=30,000 per witness) toward actual
  completion from all 10 same-component witnesses' post-R2 states did
  NOT resolve** -- all 10 hit the node cap without the frontier
  emptying, so neither success nor exhaustive failure was established.
  Honestly reported as INCOMPLETE, consistent with this project's
  repeated experience that this scale of capacity question (orbit slack
  ~23) resists small bounded searches (cf. RA2's U4 states, unresolved
  even at depth<=18/edge_cap=1.5M).

## Fourteenth follow-up round: hub completer orbit theorem refined and falsified as originally posed

Fourteenth follow-up round, explicitly told not to reuse the false
"completer=R1" claim and to track orbit identity, not event identity.
No new large-scale search; N=0 untouched.

- **The round's originally-posed target theorem ("O != R1's target
  orbit candidates all violate some exact legality condition") is
  FALSIFIED by direct exhaustive enumeration**: from the one
  same-component witness whose abandonment leaves multiple hex-0
  positions open (`989d2261b458`, abandon at ell=0), all 5 remaining
  positions' orbits (1, 3, 9, 33, 120) are legally reachable hub
  completers -- via R, Z2, and even Z3 (fresh) events. Hub completer
  choice is NOT uniquely forced in general.
- **Sharper replacement discovered and proved for the dominant
  sub-case**: whenever the word's one abandonment fires at ell=4
  (9/10 same-component witnesses, and 206/4,470 of the full corpus),
  hex 0 has exactly ONE unvisited position left, so the hub completer
  orbit is uniquely forced by pure combinatorics (the position-orbit
  correspondence on hex 0, already established) -- no legality
  argument needed, the alternative candidates simply don't exist. This
  is a genuine, general, depth-independent proof for this sub-case.
  New corpus-exact finding: same-component NEVER occurs at abandon
  ell=1,2,3 (0/617), only at ell=4 (9/206) and ell=0 (1/200).
  The `ell<4` general case (besides the single ell=0 exception) remains
  open with no corpus data to test it.
- **Classified all 6 non-R1-completer same-component witnesses as one
  "same-orbit delayed completer" family**: R1 and the separate
  completer event always target the same orbit via different phases,
  confirming they are not exceptions but instances of a single pattern
  (2 sub-variants: R1-completer gap of 1 or 2 intervening zero-charge
  events).
- **Built the full RR relation implication lattice** (7 implications
  tested exhaustively over all 4,470 witnesses): only `same-component
  => chaining` and the pre-existing `chaining => not unresolved` hold
  without exception; every proposed generalization or strengthening
  (hub existence alone, same-target-orbit, hub+chaining together, or
  hub+orbit-match alone) is falsified with concrete counterexamples --
  showing the original theorem is already maximally tight.
- **Separated Phi=0 from the chaining argument**: confirmed Phi=0 is
  an independent arithmetic consequence of the specific macro-edge
  length/ell-sequence these witnesses share (traced exactly: Phi_initial=6,
  sum(5-ell)=6 for all 10), not a logical consequence of chaining or
  same-component -- avoiding the circular-argument risk the round
  explicitly warned against.
- Completion search was NOT expanded per instructions; a deep
  150,000-node targeted search (from the one multi-candidate witness,
  looking specifically for a same-component non-chaining pair with a
  non-R1 completer whose orbit differs from R1's target) found none,
  but the frontier did not empty (287,322 remaining) -- reported as
  additional local evidence, not proof.

## Fifteenth follow-up round: the abandonment-ell dichotomy, and why the "5-way ell=0 branch" is actually 1-way in practice

Fifteenth follow-up round, decomposing the same-component branch by the
abandonment event's rotation offset (ell) within hex 0. No new
large-scale search (only small bounded local BFS from real corpus
states, matching the scale of prior rounds' targeted checks); N=0
untouched.

- **Dichotomy theorem, finite complete verification**: replaying all
  4,470 RR witnesses (this corpus is an exhaustive enumeration of
  depth<=6 RR words, not a sample) confirms same-component occurs only
  at abandonment ell=0 (1 witness) or ell=4 (9 witnesses), never at
  ell=1,2,3 (0/2,777). `outputs/rr_abandonment_ell_table.json`.
- **New general fact, exhaustively verified (212/212 hub-completions,
  0 exceptions)**: whenever hex 0 receives a second touch at all
  (regardless of ell), the completer orbit is always exactly the
  *nearest* unvisited hex-0 position (position ell+1) -- never any
  farther residual position, even though a prior round's manual/local
  BFS had shown all 5 residual orbits are *legally* reachable at
  ell=0. Legal-in-principle and realized-in-the-actual-corpus are
  different questions. A bounded local-cost BFS from real
  post-abandonment states shows why: the nearest position always costs
  exactly 2 macro-edges to reach as completer, while every other
  residual orbit costs 4 or more -- inconsistent with the corpus's
  fixed 6-macro-edge total budget once R1 and R2 both still need to
  fit, except for one edge case (completer coincides with R1 itself)
  that the resource argument alone doesn't rule out but that never
  occurs in the exhaustive corpus (0/4,470) -- left honestly open.
- **New lemma, proved and exhaustively verified (212/212): Hub Exit
  Source Lemma** -- once F=1 is exhausted, any joint whose source lies
  within hex 0 must have source orbit exactly 1 (position 5, the only
  hex-0 position whose rotation successor wraps to the always-visited
  anchor). This is strictly stronger than the (already-falsified)
  "completer orbit = R1 target orbit" claim from Round 14.
  - Correction made mid-round: an initial buggy closure-tracking check
    (an `if False else None` no-op) wrongly suggested hex 0 never
    fully closes at ell<4; re-derived with the bug fixed, hex 0 in
    fact *always* fully closes once hub-completed, at every ell --
    this dead end was caught and discarded before being reported.
- **The originally-envisioned "5-way ell=0 branch" collapses to 1-way
  in the actual corpus**: all 43 ell=0 hub-completed witnesses use
  completer orbit 120 (the nearest position); orbits 1, 3, 9, 33 never
  occur as completers despite being legal in principle.
  `outputs/rr_ell0_normal_forms.json`.
- **Full exact trace of the single ell=0 same-component witness**
  (`989d2261b458`) reveals a second, *indirect* mechanism distinct from
  ell=4's direct one: R1 itself is the hub completer, reusing orbit
  120 (already touched at 3 different phases via 3 prior full-hex
  sweeps); after hex 0 forcibly closes and exits via orbit 1 (Hub Exit
  Source Lemma), R2 achieves "same" not through orbit 1 but by reusing
  orbit 120's fifth and final phase in a different hexagon -- all 5
  phases of orbit 120 end up visited across the word.
  `outputs/rr_ell0_completer_truth_table.json`.
- **Phi=0 generalized and cleanly separated from chaining, finite
  complete verification**: Phi(final)=0 holds for *all* 212
  hub-completed witnesses, not just the 10 same-component ones -- since
  Phi depends only on pass-count/visited-count (a pure macro-edge-count
  fact), this proves Phi=0 is fully independent of the
  union-find/component-identity structure that same-component and
  chaining depend on, resolving Round 14's open question without
  circularity. `outputs/rr_ell_branch_phi.json`.
- **Honest gaps left open**: the ancestry invariant Gamma (why exactly
  ell=1,2,3's 124 hub-completed witnesses never achieve same, beyond
  the exhaustive corpus fact itself), the full resource-budget
  impossibility proof (the R1-coincidence edge case), and
  generalizing the ell=0 branch's single exact witness into a proven
  pattern (only one instance exists in the corpus, no second case to
  confirm generality) all remain unresolved.

## Sixteenth follow-up round: a major corpus-completeness correction, plus a genuine minimum-cost theorem

Sixteenth follow-up round, attempting to prove the "nearest residual
completer" theorem Round 15 proposed. While trying to prove it, this
round found and confirmed a significant error in how Rounds 11-15
described the RR corpus. No new large-scale search; N=0 untouched.

- **Central finding: the RR corpus is a capped/bounded frontier
  replay, not a complete enumeration.** `legacy_research/work/
  analyze_f1_n2_defects.py`'s own docstring says its only exploration
  is "a capped continuation," and its scope note reads "finite
  complete replay of an existing bounded Area-A frontier; not an N=2
  enumeration." The underlying checkpoint
  (`A_F1_H0_Nle3_macro_depth6.checkpoint.json`) was capped at 65,340
  frontier states by some earlier round's search. This means every
  "finite complete verification" claim in Rounds 11-15 that relied on
  "the corpus is an exhaustive census of depth<=6 RR words" was an
  overclaim: the claims are true *within the 4,470-witness corpus*,
  but that corpus itself is not proven to cover all legal depth<=6
  states. A concrete counterexample state was constructed (weight
  sequence Z2abandon,R,Z3,Z2,R from the ell=0 abandonment root,
  landing R2 on hex 0's farthest residual position) that passes
  `area_a_prune_reason` (fully legal) and structurally matches "RR"
  (2 R events, F=1, H=0), yet is verifiably absent from the historical
  corpus by hash lookup.
- **Round 15's "nearest-only completer" claim is falsified** by a
  fresh, genuinely exhaustive re-derivation (BFS via
  `macro.macro_edges()`/`area_a_prune_reason()` from each abandonment
  root, independent of the historical corpus, frontier fully empties
  every time -- these state spaces are small, ~1,100-3,900 states):
  legal non-nearest hub completions occur at every ell<4, roughly as
  often as nearest ones.
- **What survives, reproven from scratch**: (1) a genuine, corpus-independent
  proof, via complete case enumeration over the model's only 4 joint
  moves (320 branches total), that cost=1 hub re-completion is
  impossible and cost=2 hub re-completion -- when legal -- always lands
  on the nearest residual position; (2) the same-component dichotomy
  (only ell in {0,4}, never {1,2,3}) is RECONFIRMED by the fresh,
  corpus-independent exhaustive search; (3) the ell=0 branch's
  single same-component exception is RECONFIRMED as unique via a
  fresh, genuinely exhaustive (frontier-emptying) search from the
  ell=0 abandonment root -- this conclusion holds even though the
  "nearest-only" premise it was partly built on did not.
- **Phi=0 refined**: a fresh exhaustive check finds hub-touched RR-final
  states reach Phi=0 in ~98% of cases (293/300), not 100% as Round 15
  claimed from the historical corpus -- 7 genuine counterexamples
  exist. The reverse direction (no hub touch implies Phi!=0) held
  300/300 in the same fresh sample.
- **R1/R2 self-completion**: constructed a concrete, legal,
  non-saturated-phase self-completion witness reaching a non-nearest
  orbit; 3 of 5 proposed obstruction candidates (S1, S2, S5) are
  directly falsified by it, 2 (S3, S4) remain untested. No clean
  obstruction theorem or normal form was established.
- **Methodological takeaway for future rounds**: claims resting on
  `legacy_research/outputs/f1_n2_defect_words.json` or
  `outputs/rr_literal_witnesses.json` should be labeled "within the
  historical bounded corpus" rather than "finite complete
  verification" unless independently reconfirmed via a fresh,
  corpus-independent exhaustive search the way this round did for the
  dichotomy and the ell=0 uniqueness result.

## Seventeenth follow-up round: full evidence audit, a formal exhaustiveness standard, and a corrected theorem dependency graph

Seventeenth follow-up round, explicitly tasked with auditing rather
than extending: reclassify every RR claim's proof status, cleanly
separate capped-corpus claims from genuinely corpus-independent ones,
and formalize what "exhaustive" is allowed to mean going forward. No
new large-scale search; N=0 untouched.

- **Reclassified 15 core RR claims** (`outputs/rr_claim_audit.json`,
  `research/RR_EVIDENCE_AUDIT.md`) into a standardized vocabulary:
  4 remain fully deductive proofs unaffected by the corpus issue
  (Unique Hub Hexagon, Hub Touch Count<=2, the Hub Exit Source Lemma's
  deductive core, abandon_ell=4's combinatorial uniqueness); most
  corpus-resting claims were downgraded from "finite complete
  verification" to "capped-corpus exact"; 2 were explicitly reconfirmed
  as falsified (nearest-only completer, hub-completed=>Phi=0
  universally) and 2 were upgraded to a new, stronger, genuinely
  corpus-independent category ("uncapped local exhaustive": the
  ell-dichotomy and the ell=0 witness uniqueness, both cross-checked by
  an independently-implemented DFS traversal that matches the BFS
  enumerator exactly on every count, every ell).
- **Formalized an exhaustiveness standard**
  (`research/RR_EXHAUSTIVENESS_STANDARD.md`): 9 required conditions
  (root-set completeness, transition-generator completeness, no
  node/edge/time cap, frontier-empty termination, canonicalization and
  prune soundness, deterministic replay, a full certificate, and an
  independent verifier pass) and 6 distinct terms (corpus replay,
  capped BFS, depth-bounded exhaustive, root-local exhaustive, globally
  exhaustive, naturally exhausted) that must not be used
  interchangeably going forward.
- **Found that fully uncapped enumeration (no declared depth ceiling
  at all) is NOT tractable here**: without a depth ceiling, the local
  state space is bounded only by this project's much larger global
  budgets (TARGET_P=121, TARGET_O=25), and a real attempt did not
  terminate within 590 seconds. What Round 16 called a "naturally
  small" state space was implicitly depth-capped all along; this round
  makes that ceiling an explicit, disclosed parameter instead
  (`--depth-ceiling`, reported in every certificate).
- **Built a genuinely uncapped-within-ceiling local enumerator**
  (`src/enumerate_rr_uncapped_local.py`) for root class 1
  (abandonment-instant state, 5 roots for ell=0..4) with a full
  certificate (expanded count, generated edges, unique canonical
  states, duplicate count, frontier-empty flag, max depth reached,
  engine SHA-256), cross-validated by an independently-coded DFS
  verifier (`src/verify_rr_exhaustive_certificate.py`) that agrees
  exactly on all 5 ell branches.
- **A genuine, general minimum-cost theorem** (`RR_COMPLETION_COST_THEOREM.md`):
  cost=1 hub re-completion is impossible and cost=2 always lands on
  the nearest residual position, both proved via a complete (not
  sampled) 320-branch case analysis over this model's only 4 joint
  moves. The converse ("nearest implies cost 2") is FALSE in general
  (using abandonment move w3:210 instead of the real w2:10 gives
  cost 5 to the same nearest orbit) but TRUE when conditioned on the
  real historical abandonment convention (w2:10, verified 4,470/4,470).
- **An unresolved discrepancy found and reported, not papered over**
  (**RESOLVED in Round 18 -- see that section below**): at ell=4, the
  historical capped corpus reports 9 same-component witnesses, but the
  fresh uncapped-local universe finds only 5. Round 17 flagged this as
  open rather than assuming a cause in either direction.
  `outputs/rr_old_new_corpus_diff.json`.
- **Phi=0 further quantified**: in the fresh local universe, hub-touched
  RR-final states reach Phi=0 in 283/290 (97.6%) of cases, not
  universally; the reverse direction (no hub touch implies Phi!=0) held
  991/991 (100%) in the same sample. The 7 counterexamples were not
  individually traced to a structural cause this round.
  `outputs/rr_corrected_phi_distributions.json`.
- **A corrected theorem dependency graph**
  (`research/RR_CORRECTED_THEOREM_GRAPH.md`) separates results into
  three tiers by evidence quality: a solid-line tier of pure deductive
  proofs plus this round's cross-checked uncapped-local results (safe
  to build on), a dashed-line tier of capped-corpus-exact observations
  (not yet falsified but not proven general), and a blocked-off tier of
  explicitly falsified claims that must not be reused as premises.
- **Root classes 2-5** (hub-completion-instant state, R1-precedent
  state, R2-precedent state) were defined conceptually
  (`research/RR_LOCAL_UNIVERSE.md`) but NOT implemented as separate
  enumerations this round -- flagged as the most direct next-round task
  rather than silently skipped.

## Eighteenth follow-up round: the ell=4 9-vs-5 discrepancy fully resolved (counting unit, not a missing witness)

Eighteenth follow-up round, tasked with resolving Round 17's one
outstanding discrepancy before proposing any new RR theorem. No new
search of any kind; N=0 untouched. Every number below comes from exact
replay of the 9 historical witnesses through the current engine.

- **RESOLVED: the gap was a counting-unit plus depth-scope difference,
  with no missing witness in either direction.** The historical
  corpus's unit is a complete 6-macro-edge WORD; the fresh enumerator's
  unit is a distinct post-R2 STATE. Replaying all 9 historical ell=4
  same-component witnesses shows they collapse onto exactly **3**
  distinct post-R2 states, and each of those 3 states has exactly **3**
  legal continuation macro-edges -- 3 x 3 = 9, matching the historical
  count exactly. All 3 states are present in the fresh 5-state set;
  the fresh set's other 2 sit at depth 6 past abandonment (7 total
  macro-edges), strictly outside the historical depth<=6 word scope.
  As post-R2 states, **H9 is a subset of L5** (H9 \ L5 = empty), so the
  direction is normal, not reversed as Round 17 feared.
  `research/RR_ELL4_DISCREPANCY_AUDIT.md`.
- **All 9 historical witnesses replay cleanly in the current engine**:
  every move legal, every step passing the current
  `area_a_prune_reason`, same-component reproduced 9/9, ell=4
  reproduced 9/9, zero divergences. So `HISTORICAL_RECORD_INVALID` and
  `CURRENT_ENGINE_DRIFT` are both ruled out by direct evidence.
- **The specific bug hypothesis raised when the gap appeared was tested
  and REFUTED**: re-running every root-local enumeration with the dedup
  key widened from `state.stable_key()` to `(state.stable_key(),
  r_count, r1_target_orbit)` changes nothing on any ell. A diagnostic
  counter shows **no state in this universe is ever reached with two
  different histories at all**, so the representation is Markov-complete
  for the same-component question here (a finite check over this
  universe, not a general proof).
  `research/RR_LOCAL_STATE_COMPLETENESS.md`.
- **Canonicalization / generator / prune all cleanly reconciled**: the
  historical generator hashes `exact.canonicalize(state)` while the
  Round 17 enumerator hashes the raw state -- canonicalizing this
  round's raw replays reproduces all 9 historical hashes exactly
  (9/9, raw 0/9). Both pipelines use the same child generator
  (`macro.macro_edges()`) and the same prune (`area_a_prune_reason`
  with `macro.AREA_A`); raw vs canonicalized child-label sets differ at
  0 states checked. `research/RR_SEARCH_SCOPE_RECONCILIATION.md`.
- **A real labeling error in Round 17's own output was found and
  fixed**: `outputs/rr_uncapped_local_universe.json`'s field
  `unique_canonical_states` actually counted RAW (uncanonicalized)
  states. Raw dedup is *safe* for completeness -- it can only
  re-expand left-S6-relabeled duplicates, never skip a reachable state
  -- so no Round 17 numeric result is invalidated, but the field is
  renamed `unique_raw_states` with an explicit `dedup_key` field, both
  scripts re-run, and the independent DFS cross-check still matches
  5/5 ell. Seven affected statements across STATUS.md, two research
  documents, two outputs, and two scripts were corrected, with a
  before/after/reason table in `RR_ELL4_DISCREPANCY_AUDIT.md` section
  13. No theorem was overturned by any of these corrections.
- Per the round's instruction, **no new general RR theorem is proposed
  here** -- the discrepancy had to be closed first, and it now is.

## Nineteenth follow-up round: the L5 local universe classified, and a real canonical enumerator

Nineteenth follow-up round. With the Round 18 discrepancy audit closed,
this round classifies the corrected root-local universe. No completion
search; N=0 untouched. Per the round's instruction, nothing here is
claimed as a global RR theorem.

- **A genuinely canonical enumerator was built** (Round 17's deduped on
  raw states, a labeling error Round 18 corrected). The real difficulty
  it had to solve: `exact.canonicalize()` returns the least left-S6
  translate but not the alpha achieving it, while history fields like
  "R1's target orbit" are raw orbit ids -- so the *pair* must be
  canonicalized, transporting history orbit ids through every tied alpha
  via `LEFT_ORBIT_ACTION` and taking the minimum. Result: duplicate
  count 0, every stabilizer tie count 1, and **every number identical to
  the raw enumerator**. So Round 17's raw dedup was not merely "safe" --
  in this universe it was exactly right, because the universe contains
  no two states that are left-S6 translates of each other.
- **The five ell=4 post-R2 states share one identical terminal
  signature** with no exceptions: R1 targets orbit 1, the hub completer
  lands precisely on (orbit 1, phase 4) = hex 0's position 5, R2 then
  fires immediately via `rot^0;w3:120` with source orbit 1 and target
  orbit 0, Phi=0, exactly 3 legal trailing edges, reached by exactly 1
  path. `research/RR_L5_LOCAL_UNIVERSE.md`.
- **The counting identity is exact**: 9 = 3 + 3 + 3, and *why* each
  state admits exactly 3 trailing edges is fully explained rather than
  observed -- once F=1 is spent, every ell<5 edge would be an
  abandonment (pruned `F_exceeded`), leaving only ell=5; there are only
  4 joints in the model; and one of them (`w3:120`) is still abandoning
  here. `research/RR_WORD_STATE_MULTIPLICITY.md`.
- **The proposed N2 theorem is FALSIFIED as stated.** N2 is not "H3 plus
  one inserted zero-charge block": it has two more preparation edges,
  its extra edges are Z3 fresh-orbit openings that H3 never uses at all
  (H3 holds O=2, N2 reaches O=4-5), and its hub completer is always R1
  while H3 contains both the R1-completer and Z2-completer variants. The
  corrected picture is **one shared terminal normal form reached by two
  structurally independent preparation families**.
  `research/RR_H3_N2_NORMAL_FORMS.md`.
- **No nontrivial necessary-and-sufficient chaining predicate was
  found** -- reported as 미완료 rather than dressed up: the only IFF
  predicate is `r1_target == r2_source`, which is chaining's own
  definition. What the ablation did establish: `same_component` is
  strictly sufficient but not necessary (fp=0, fn=23); it coincides
  exactly with "both R2 roots in the hub component"; `r2_source_orbit==1`
  alone is falsified as a predicate (fp=31); and `same_target` is
  disjoint from chaining (tp=0, 449 counterexamples), independently
  reconfirming a Round 14 corpus observation in a corpus-free setting.
  `research/RR_LOCAL_CHAINING_PREDICATE.md`.
- **Markov-completeness: the empirical check is VACUOUS, and the
  deductive answer is "no".** All 2,234 distinct post-R2 states at depth
  6 are reached by exactly one R2 boundary, so there are no two
  histories to compare -- the zero-collision fact proves nothing. The
  real answer is deductive: a post-R2 `ExactState` records which
  (orbit,phase) pairs are visited but not which edge was R1, so
  `r1_target_orbit` is not a function of it and chaining cannot be
  decided from the state alone. Both relations are boundary data, not
  state data, and the enumerator must carry the history fields.
- **Depth-7 stability check** (coverage confirmation, not a completion
  search; frontier exhausted naturally, no cap): the ell=4 five-state
  set is **completely stable** (still exactly 5, same H3/N2 split), the
  ell in {0,4} dichotomy still holds (ell=1,2,3 remain 0), and
  same-component => chaining still has 0 violations. Only ell=0 grows,
  1 -> 3.
- **A permanent counting-unit standard** was written to prevent the
  Round 18 confusion from recurring: four units (word / post-R2-state /
  event / history), mandatory unit-bearing field names, and the exact
  conversion identity between them.
  `research/RR_COUNTING_UNIT_STANDARD.md`. A full re-scan of Rounds
  11-18 for the affected phrasings found **no corrections needed beyond
  the 7 already made in Round 18**.

## Twentieth follow-up round: the decorated boundary state, and a refutation of Round 19's stability claim

Twentieth follow-up round. No completion search; N=0 untouched. Nothing
is claimed as a global RR theorem.

- **The decoration alone determines the relations.** Round 19 proved
  deductively that a post-R2 ExactState cannot decide chaining. This
  round defines the decoration to carry alongside (5 orbit-transported
  fields, 4 hexagon-transported, 18 left-S6-invariant), and finds the
  reverse: over all 2,234 R2 boundaries, the decoration WITHOUT the
  ExactState determines chaining, same-component, and the trailing-edge
  signature -- 2,216 distinct keys, zero conflicting groups.
  Grade: exact decorated quotient. `research/RR_DECORATED_BOUNDARY_STATE.md`.
- **The ablation was designed to avoid being vacuous, and its greedy
  result is reported with its caveat.** Including the ExactState in any
  key would separate every boundary (each state is reached once), making
  "drop a field, look for collisions" report every field as unnecessary.
  So the ExactState is excluded. Only `fresh_orbit_openings` is provably
  necessary; the other 26 fields are labeled "necessity undetermined",
  never "unnecessary". The greedy 7-field subset SEPARATES this finite
  universe but does not let one COMPUTE the relations from their
  definitions -- it omits `r1_target_orbit`, which chaining is defined
  in terms of. Separating-minimality and structural-minimality are
  different notions and the weaker one is flagged as such.
- **Same-component has an exact ancestry characterization.** Three
  predicates are all IFF (tp=6, fp=0, fn=0): the LCA form
  (`every shortest path between R2's endpoints passes through the hub`),
  `both endpoints at finite hub distance`, and Round 19's
  `both roots in the hub component`. The graph reason is the already-proved
  Unique Hub Hexagon lemma -- the hub is the only possible junction.
- **Chaining still has no non-trivial iff predicate** -- reported as
  open again. The best sufficient one improved from Round 19's
  `same_component` (a relation) to `r1_target_hub_distance ==
  r2_source_hub_distance == 1` (pure hub geometry), same confusion
  matrix, still not necessary (fn=4). `hub_completer_orbit ==
  r1_target_orbit` alone is falsified outright (fp=187).
- **Round 19's "the ell=4 set is completely stable" is REFUTED.** A
  depth-8 coverage run (root-local, no cap, frontier exhausted, 43,459
  nodes) grows the ell=4 same-component set from 5 to **9** states. The
  reason depth 6->7 showed no change is **parity**, not closure: ell=4
  boundaries occur only at EVEN depth from the abandonment root (4, 6,
  8) and ell=0 only at ODD depth (5, 7). Raising the ceiling to an odd
  number could not add anything at ell=4. No upper bound on preparation
  depth is established, and fresh-opening blocks can be inserted
  repeatedly (one state uses 5). `research/RR_TERMINAL_NORMAL_FORM_THEOREM.md`.
- **Round 19's "exactly 3 trailing edges" is also refuted, and replaced
  by a proved upper bound.** The F-exhaustion argument proves *at most*
  3 (ell<5 edges are all abandonments; the model has 4 joints; `w3:120`
  is still abandoning). 11 of the 12 states have exactly 3, but
  `cbfdf11e4a79` at depth 8 has only 2 -- an extra visited-collision, not
  `F_exceeded`.
- **A common terminal normal form holds across both branches** (12/12
  states, ell=0 and ell=4): R1 targets the nearest-residual orbit O*,
  the hub completer is the LAST preparation edge and lands on O*, R2's
  source is O* at phase 4 and its target is the initial orbit 0, Phi=0,
  and chaining is therefore forced. The branches differ only in O*
  (1 vs 120), the completer's landing phase (4 vs 0), the
  completer-to-R2 distance (1 vs 2), and depth parity.
- **H3 has a clean parameterized normal form**: preparation is exactly
  3 macro-edges, exactly one of which is R, and the three states are
  precisely the three placements of that R. Whether the completer is R1
  is not separate structure -- it is the i=3 case.
  `research/RR_H3_PREPARATION_NORMAL_FORM.md`.
- **N2 is NOT established as a single parameterized family** (2
  instances, differing Z3 counts and placements), and Round 19's
  "fresh-opening vs no-fresh-opening" dichotomy breaks at depth 8, where
  3 of the 4 new states have exactly one fresh opening. Preparation
  length (3, 5, 7 -- all odd) is the more stable classification axis.
- **The ell=0 family growth is characterized but its finiteness is
  NOT decided** -- reported as open. The 3 ell=0 states share a fully
  identical terminal signature and differ only in preparation length
  (4 vs 6) and Z3 count (0, 2, 3). Given that ell=4 gained a whole new
  preparation length at depth 8, unbounded growth is the better-supported
  expectation, and no evidence for finiteness exists.
  `research/RR_ELL0_FAMILY_GROWTH.md`.
- **Decorated Markov-completeness is partial, honestly.** Child legality
  is a pure function of the ExactState and decoration updates are local
  (both 손증명), but the strong form -- same decorated state implies same
  continuation tree -- is VACUOUS here, since no two histories reach the
  same decorated state. Left as 미완료.

## Twenty-first follow-up round: the preparation grammar, a parity proof, and three corrections

Twenty-first follow-up round. No completion search; N=0 untouched. The
one deep run (ell=0 at depth 9) was a grammar *prediction test*, run
only after the grammar candidate existed, to a separate output path.

- **Depth convention fixed and both stored everywhere.** Round 20's
  "ell=0 is odd depth" was in the abandonment-root convention. In the
  word-start convention (abandonment counted as edge 1) it is the
  reverse: ell=4 is ODD (5,7,9), ell=0 is EVEN (6,8,10). Not a
  contradiction, but it needed stating, and both fields are now on every
  record.
- **Parity is now largely hand-proved.** Decomposing each witness as
  `A_ell · P · C · T_ell · R2`, Lemma P1 proves the branch difference
  outright: the hub's only exit position is position 5 (orbit 1, by the
  Hub Exit Source Lemma), and chaining needs R2's source to be the
  nearest-residual orbit O*. For ell=4, O* IS orbit 1, so the hub-exit
  edge can be R2 itself, giving tail length 0; for ell != 4 it cannot,
  forcing one extra `Xh` edge, tail length 1. That single difference
  produces the whole parity split. The remaining gap is that `|P|` is
  even, which is observed (14/14) but not proved -- and is specifically a
  same-component phenomenon, since over ALL hub completions odd values
  genuinely occur.
- **Phi=0 upgraded from arithmetic coincidence to a consequence of the
  normal form.** A contributes (5-ell); the hub-exit edge fires after
  rotating from position ell+1 to position 5, so it contributes
  (1+ell); the sum is 6 for EVERY ell, which is exactly the Phi=0
  condition. All other preparation edges are ell=5 and contribute 0.
  This closes a question left open since Round 15.
- **A grammar relation was predicted and then confirmed.** The
  before-completer words satisfy `P(ell=0) = the Rh-free members of
  P(ell=4)`, at every length. Having seen this at lengths 2 and 4, the
  round predicted that ell=0 at depth 9 would gain exactly `EEFEEE` and
  `FFFEFF` -- and the run produced exactly those two, nothing else.
  The structural reason: at ell=0 the completer must BE R1, so no
  earlier Rh can exist.
- **The insertion/deletion theorem is FALSIFIED, 8/8 counterexamples
  each way.** No observed preparation word reduces to a shorter valid
  one by deleting a contiguous 2-block, and none is obtained from a
  shorter one by inserting a single contiguous 2-block (`FEFE` cannot
  come from `EE` -- it needs two separated insertions). Every observed
  P is irreducible, so the "finite base forms + repeated insertion
  block" grammar the round aimed for **does not exist** for this data.
  What survives is a hand-proved `T_ell` rule plus a per-length list of
  P words -- honestly graded bounded observation, not an exact grammar.
- **No nontrivial preparation-depth bound was found.** The obstruction
  is concrete: `E` edges (existing-orbit zero-charge transitions)
  consume no monotone resource at all -- O unchanged, no fresh orbit, no
  Phi cost -- and a length-7 preparation exists using only ONE fresh
  opening. Only the trivial finite-state-space bound remains, which the
  round explicitly excluded. Reported as 미완료.
- **The 2-vs-3 trailing predicate is found**: it is a single occupancy
  bit -- whether `w3:210`'s ell=5 target permutation is already visited
  -- and it is predicted exactly by the symbolic word `P = EEFEEE`
  (2/2 with, 12/12 without), across BOTH branches.

Three corrections to earlier rounds, all from this round's checks:
- **Round 20's "the hub completer is the last preparation edge (12/12)"
  is refuted**: true for ell=4 (9/9), false for ell=0 (0/5), where the
  completer is second-to-last. Round 20 generalized an ell=4 pattern to
  ell=0 without checking it.
- **Round 19/20's "w3:120 is removed by F_exceeded" is wrong**: no
  ell=5 RR joint is ever F_exceeded at these states (14/14); w3:120 is
  removed by a literal visited-collision. So the hand-proved trailing
  upper bound is 4 (the joint count), not 3.
- **Round 20's "the ancestry theorem follows from the Unique Hub
  Hexagon lemma" was an overclaim**: that lemma gives uniqueness of the
  twice-touched hexagon, but a once-touched hexagon can still hold two
  orbits, so "the hub is the only junction" does not follow. Two of the
  four directions are hand-proved; the other two are downgraded to
  root-local exhaustive with the missing assumption named.

## Twenty-second follow-up round: the parity route refuted, an automaton built, and two of my own claims corrected

Twenty-second follow-up round. No completion search; N=0 untouched. No
new depth runs -- everything reuses the naturally-exhausted ranges.

- **A self-correction found mid-round, before it reached any
  conclusion.** The first invariant search reported four functionals
  flipping on every preparation edge. It was measuring the wrong
  boundary -- comparing the post-rotation state with the post-joint
  state, i.e. only the joint, not the full macro-edge. Re-measured
  correctly over all 48 preparation edges: visited_count increments by
  6 (even, does NOT flip), n_hexes by 1, P by 1, and ell is always 5.
- **The proposed parity proof route is REFUTED.** Of 15 candidate mod-2
  functionals (permutation sign, hexagon/orbit/phase parities, endpoint
  coordinates, incidence-graph distances to the hub, and sums thereof),
  the only ones flipping on every preparation macro-edge are `n_hexes`
  and `P` -- and both are pure per-edge counters (+1 each). So "start
  and completer-ready have the same colour" is a restatement of "the
  edge count is even", and the argument is circular. The bipartite
  formulation of section 4 fails for the same reason: the transition
  graph is graded by n_hexes, hence trivially bipartite. |P| evenness is
  now reduced to the exactly equivalent statement "the touched-hexagon
  count at the completer-ready boundary is even", which was not
  independently characterized. **Success criterion 1: not achieved**,
  with the reason the proposed route cannot work now precisely
  identified.
- **A symbolic preparation automaton was built** (26 states in each
  branch, 97-104 transitions, alphabet E/F/Rh/Rx). Every transition is
  induced by a real exact edge, but the boundary state carries no
  visited mask, so accepted symbolic words are not guaranteed
  realizable. Graded honestly as a **sound over-approximation /
  necessary-condition automaton**, not an exact automaton. All 14 known
  preparation words parse, uniquely -- bounded coverage only.
- **Why Rh is absent at ell=0 is now settled, and two of the four
  proposed reasons are refuted.** Rh edges ARE locally legal in ell=0
  preparation prefixes (concrete witnesses found), which refutes
  candidates R2 and R3. The real reason (R4) is structural: at ell=0 the
  completer must BE R1, since the completer targets O* and chaining
  requires R1 to target O*, and an RR word has only two R events. Hence
  no earlier Rh can exist. That is a hand proof of Inclusion 1 of the
  Rh-free sublanguage identity; Inclusion 2 remains observation-grade
  because no branch transport map was constructed (**criterion 4: not
  achieved**).
- **The exact trailing-edge formula is established**: m(S) = 4 - #blocked
  candidates, holding 12/12, with zero duplicate targets so the
  correction section 17 asked about is unnecessary here. All four
  candidates legal was never observed but is not ruled out, since
  w3:120's blocking is a state-dependent visited-collision rather than
  a structural fact. **Criterion 6: achieved.**
- **Round 21's claim that E edges consume no monotone resource is
  WRONG, corrected here.** Direct measurement shows every preparation
  edge -- E included -- consumes one hexagon and six permutations. The
  accurate statement is that E consumes no ORBIT-level resource. The
  resulting bounds (|P| <= 118 or 119) are still essentially the trivial
  state-space bound, so the conclusion "no small structural bound"
  stands, but for a different reason than Round 21 gave.
- Correction log written to `outputs/rr_round22_correction_log.json`.
  The three statements section 18 asked to purge were already fixed at
  their primary sites in Round 21; this round scoped two residual
  occurrences and fixed one new Round-21 error.

## Twenty-third follow-up round: the parity source located, and three proposed routes closed

Twenty-third follow-up round. No completion search; N=0 untouched. No new
depth runs.

- **The source of |P| evenness is located.** Enumerating every hub
  completion that lands on the O* position gives a table identical in
  both branches: even |P| always has exactly ONE R event through the
  completer, while odd |P| has either zero or two. Since an RR
  same-component witness needs exactly one R through the completer (R1
  must target O* for chaining, R2 fires strictly after, and an RR word
  has exactly two R events -- a hand proof), the R-count is pinned to 1,
  which forces |P| even. The parity is therefore a consequence of the
  R-placement, not of any graph or counter structure.
  The remaining gap is one measured relation: |P| + #R(through C) is odd
  in every case (all five ell branches, root-local exhaustive),
  equivalently the number of zero-charge edges through the completer is
  even. That relation is not yet hand-proved.
- **Three proposed proof routes are closed, each by a hand proof or an
  explicit counterexample:**
  - *Group-level parity*: all preparation edges are forced to ell=5, so
    the transition graph is the Cayley graph of the four generators
    Sigma^5·action_j. Their signs are (+1,+1,+1,-1) -- not all in one
    coset of A6 -- and an explicit odd closed walk was found. The graph
    is **not bipartite**, so no such argument can exist.
  - *Completer-target constraint*: O*-landing completions occur at BOTH
    |P| parities (9 even, 10 odd) at every ell, so requiring the
    completer to hit O* does not force parity.
  - *Degree / handshake / forest*: every preparation edge makes the same
    degree change, so any degree-based quantity is a linear function of
    the edge count. The forest identity degenerates to n_O = c with k
    cancelling.
- **A second self-correction, caught by measurement.** This round first
  predicted the incidence graph would give each traversed hexagon degree
  6 (from the ell=5 sweep). Measurement refuted it: orbit_masks records
  only JOINT targets, not rotation steps, so every touched hexagon has
  degree exactly 1 and |E| = k+2. The corrected ledger is what the
  document and certificate now carry.
- **An exact branch transport map is proved IMPOSSIBLE.** The
  abandonment root at offset ell has visited_count = ell + 2 exactly, so
  root(0) has 2 visited permutations and root(4) has 6. Any map
  preserving exact legality must preserve the visited set's cardinality,
  since legality of every later joint is decided by whether its target is
  already visited. Hence no state-level bijection Q_4 -> Q_0 exists, and
  the route Round 22 left open for the Rh-free reverse inclusion is
  closed -- that inclusion stays root-local exhaustive with no general
  proof.
- **Automaton x resource ablation**: `r_count` and `hub_residual` refine
  the quotient not at all (state and transition counts unchanged), so
  both are removable; only `fresh_count` and `o_star_phase_mask` refine
  it. No combination reaches exactness, since none encodes the visited
  mask -- all graded sound over-approximation, as instructed.
- **m(S)=4 is not ruled out.** w3:120 is blocked in all 12 terminal
  states, but by a visited-target collision rather than
  area_a_prune_reason, which is state-dependent. So m(S)<=3 is
  root-local exhaustive only; the hand-proved bound stays at 4.

## Twenty-fourth follow-up round: why the parity cannot be proved additively

Twenty-fourth follow-up round, aimed at the single open proposition
|P| + #R = 1 (mod 2). No completion search; N=0 untouched.

- **Round 23's table was checked for an artifact, and survives.** That
  scan capped the R count at 2, so its "odd |P| has #R in {0,2}" could
  have been an artifact of the cap. The cap is removed here and the
  relation still holds, at every ell.
- **The relation is SHARP, and that is new information.** Classifying
  every hub completion by landing position shows |P| + #R is purely odd
  at the O* position (j = ell+1) and at j = ell+2, but MIXED at
  j >= ell+3. So it is not a property of hub completion in general -- it
  is tied to landing on the near residual positions, which points at
  where a real proof would have to come from.
- **The equivalence asked for is proved.** Through the completer there
  are |P|+1 events, split as #R + #zero, so |P| + #R = #zero - 1 (mod 2).
  Hence |P| + #R odd <=> #zero even. Pure arithmetic, hand proof.
- **A genuine impossibility theorem, which explains every failure of
  Rounds 22-24 at once.** Measuring the per-event increment of every
  ExactState field gives a constant per event kind (S: +1/0/+1, O:
  0/0/+1, P: +1/+1/+1, D: -1/-1/+4, Ndef: +1/0/0, visited: +6/+6/+6),
  and D = 5*O - P is an exact identity (0 violations / 1,399 states).
  Therefore every additive field is a fixed linear form in (#R, #E, #F),
  every Z/2 functional built from additive fields is a linear form in
  those counts, and such a form certifies "#E + #F even" only if it IS
  that statement -- circular. **No additive invariant can prove the
  parity.** This subsumes Round 22's 15 mod-2 candidates, Round 23's
  handshake/odd-degree/forest routes and n_hexes/P counters, the Cayley
  sign argument, and this round's own field ledger.
- **The endpoint-role route (section 3) is refuted by the same theorem.**
  A role whose transition depends only on the event kind is an additive
  invariant, so no such role can work; a richer role (hub membership,
  O*-membership, revisit status, O* phase count) was built and does not
  flip consistently either.
- **The odd-preparation exclusion is recorded but rests on the unproved
  relation.** At the O* position with odd |P|, #R is always even (0 or
  2): #R=0 makes chaining impossible, #R=2 makes R2 a third R event. So
  odd |P| is incompatible with same-component RR -- root-local
  exhaustive, not a hand proof, since it uses the relation itself.
- Per the round's instruction, the word-level branch relation (section
  10) was left untouched while the parity remains open.

**Net position on the parity**: still 미완료, but the search space is now
sharply cut. A proof must use a non-additive constraint -- the
orbit/position combinatorics that decide which hub position the completer
may land on -- and the sharpness result localizes exactly where that
constraint bites.

## Twenty-fifth follow-up round: order-dependence made explicit, and one surviving structural partition

Twenty-fifth follow-up round, targeting the non-additive cause of the
preparation parity. No completion search; N=0 untouched. No additive
feature scans, per the round's instruction.

- **Order-dependence is now demonstrated, not just argued.** Eleven
  exact pairs exist whose additive event counts (ell, #R, #Z, #F) are
  identical but whose landing class differs -- e.g. `FFEFR` lands on O*
  while `EFFFR` lands far, with the same counts. So the landing position,
  and hence the parity condition, is a function of the event ORDER, not
  of the counts. This is the empirical complement to Round 24's
  impossibility theorem.
- **The parity is confirmed on a much larger set, with no R-cap**: the
  zero-charge count is even in all 95 O*-landing completions and all 48
  landings at j = ell+2, and MIXED at j >= ell+3 (31 even, 13 odd). So
  the evenness belongs to the two nearest residual positions, and
  degrades in stages as the landing moves away.
- **One structural partition survives, and it is new.** Of five
  candidate pairing rules, four are killed by exact counterexamples
  (same target orbit: `FFEFR`; same target hexagon and same target
  phase: `EER`; same symbol: `RFERR`). The survivor is the split by
  "does this zero-charge event target O*": at O*-landing, BOTH blocks
  have even size, 95/95. That refines the single evenness into two finer
  ones. It fails at j = ell+2 (`ERFERF`) and beyond, so it is specific
  to O*-landing.
  Honest limit: even blocks are not an explicit matching, and the round
  does not claim one -- section 14's target is 미완료.
- **The minimal odd far-landing witnesses are exhibited** (section 11):
  13 exist, the smallest being `EFRRFR` (#Z=3) and `FFRFFE` (#Z=5).
  Why no analogue exists at the two near positions (0 out of 143) is
  **not explained** -- none of section 12's six candidate obstructions
  could be pinned to an exact transition-level contradiction.
- **The ordered group equation is written down explicitly**: since every
  preparation edge is forced to ell=5, landing at hub position j is
  exactly `Sigma^ell · a_2 · g_{x_1}···g_{x_k} · Sigma^m · a_c = Sigma^j`
  with non-commuting generators. A limitation worth recording: the
  symbols F and R can share a move label (they differ only by
  new_orbit), so a symbolic word does not determine the group product --
  which caps how far a purely symbolic argument can go.

**Net position on the parity**: still 미완료. This round did not prove
it, but it converted "additive approaches fail" into "landing is
provably order-determined", and found the first structural refinement
(the O*-targeting split into two even blocks) that is specific to the
landing class where the parity holds.

### The O* phase walk — the surviving partition explained, and the gap narrowed to one lemma

`src/analyze_rr_o_star_winding.py` -> `outputs/rr_o_star_winding.json`,
written up in `research/RR_ORDERED_PHASE_PARITY.md`. No new search: this
is a re-reading of the ordered-word ledger as a walk on the five phases
of the single orbit O* (the nearest residual orbit the abandonment
leaves open).

Six premises, with their grades:

- **(a) F never targets O*** — 손증명. An F event opens a NEW orbit, and
  O* is already open (the abandonment registered it). So the zero-charge
  events touching O* are exactly the E events. Measured: 0 exceptions
  in 95 O*-landing completions.
- **(b) every E step advances the O* phase by exactly +1** — measured,
  110/110. Not proved.
- **(c) every R step advances it by an even amount** — measured, +2
  115 times and +4 10 times, 125/125. Not proved.
- **(d) the total advance is 4 (mod 5) for every ell** — 손증명: hub
  position j has phase j-1 while the abandonment phase is j mod 5.
  Measured: advance = 4 in all 19 completions at each of ell=0..4.
- **(e) the five O* phases are pairwise distinct along the walk**, so
  the walk has at most 4 steps — 손증명 from `orbit_masks` (a visited
  (orbit,phase) cannot be revisited). Measured: 0/95 revisits, walk
  length histogram {1:10, 2:35, 3:45, 4:5}.
- **(f) at most 2 steps are R** — 손증명 from the RR definition (exactly
  two R events in the word). Measured: {0:5, 1:55, 2:35}.

From (a)-(d), with k the winding number of the phase walk
(`sum(deltas) = 4 + 5k`):

> **#Z_{->O*} ≡ k (mod 2)** — the evenness of the zero-charge events
> targeting O* IS the evenness of the winding number.

From (e),(f) a finite case analysis forces **k = 0**: all deltas are
positive and the sum is ≡ 4, so k ≥ 0; the maximum sum is 4+4+1+1 = 10
< 14, so k ≤ 1; and k = 1 needs sum = 9, whose only multiset over
{1} ∪ {2,4} with ≤ 4 entries and ≤ 2 non-1 entries is {4,4,1}, all three
orderings of which revisit a phase. An exhaustive alphabet search
confirms it mechanically: 0 witnesses under #R ≤ 2, and exactly 2
witnesses ((1,2,4,2) and (2,4,2,1), both with odd #E) once that bound is
dropped — so premise (f) is doing real work, not decoration.

Measured k across all 95 O*-landing completions: **k = 0 in every case**,
and (k, #E parity) = (0, 0) in every case. This is the structural cause
of the O*-targeting partition that survived section 14 — the evenness
comes from a phase winding number, not from any pairing rule, which is
why no matching rule needed to exist.

**What is still missing, precisely**: premises (b) and (c). The delta of
a step is measured relative to the previously visited O* phase, not a
local property of the event, so proving "E always lands on the phase
immediately after the last-visited one" needs its own lemma. Until then
the chain is 미완료 and `|P| + #R_{<=C} ≡ 1 (mod 2)` remains unproved.
Two further honest limits: this closes only the O*-targeting block, with
no argument yet for the evenness of #Z_{->other}; and the interval and
first/last-symbol routes were both **refuted** this round (5 of 95
completions leave two F's unclosed; 5 of 95 end their zero-charge run
on F rather than E).

The practical effect is a real narrowing: the parity problem went from
"find an additive invariant" (proved impossible in Round 24) to "prove
the O*-step alphabet is exactly {E:+1, R:even}" — a single local lemma,
after which the finite case analysis above closes #Z_{->O*} immediately.

### The O*-step lemma — premise (b) proved, premise (c) refuted in general, and a sharp threshold found

`src/verify_rr_o_star_alphabet.py` -> `outputs/rr_o_star_alphabet.json`,
`src/prove_rr_o_star_step_lemma.py` -> `outputs/rr_o_star_step_lemma.json`,
written up in `research/RR_O_STAR_STEP_LEMMA.md`. The second script runs
no search at all — it is a finite group computation in S_6.

**The key structural fact.** Every preparation macro-edge is forced to
ell=5, so each acts on the walk position by right-composition with one
fixed element `g_j = Sigma^5 o action_j`. Computing all four:

| joint | `Sigma^5 o action` | in `<E>`? |
|---|---|---|
| `w2:10` | (1,2,3,4,0,5) | **E** |
| `w3:120` | (2,3,4,0,1,5) | **E²** |
| `w3:201` | (2,3,4,1,5,0) | no |
| `w3:210` | (2,3,4,1,0,5) | no |

So the ell=5 `w2:10` edge *is* right-multiplication by the orbit
generator E, and `w3:120` is right-multiplication by E². Two hand proofs
follow immediately:

- **F is never `w2:10` or `w3:120`** — an orbit-preserving edge cannot
  open a new orbit. Measured: 4,629/4,629 and 4,283/4,283 have
  `new_orbit=False`. So every F is `w3:201` or `w3:210`.
- **Premise (b) is now 손증명, not measured**: from a port q of O*, a
  `w2:10` edge lands at q∘E — phase +1 exactly; `w3:120` lands at q∘E².

**Premise (c) in general is 반증됨.** The orbit-changing joints leave
O*, so their displacement is the `<E>`-exponent of the whole intervening
product, and the alphabet lemma becomes a free-monoid statement. An
exhaustive first-return BFS over S_6 (716 non-`<E>` elements reached)
finds **4 violations**: two first-return words of length 7 with exponent
3, and two of length 8 with exponent 1. The alphabet is therefore **not**
a pure group fact — it cannot be proved without legality constraints.

**But the same computation gives a sharp threshold.** Every first-return
word of length ≤ 6 has exponent 1 (single E), 2 (single E²), or even —
exact group computation, no exceptions. The first odd exponent appears at
length 7. Hence:

> If consecutive O* visits are at most 6 preparation edges apart, the
> alphabet lemma holds and the winding argument closes #Z_{->O*}
> evenness.

The observed first-return gaps in the local universe are 0 (for `w2:10`
and `w3:120`, which land immediately), 4 (for `w3:201`) and 3 or 4 (for
`w3:210`) — all below the threshold, which is *why* the alphabet holds
there. This changes the status of the long-standing "small preparation
depth bound" item: it is now known to be **sufficient**, and its needed
form is pinned down precisely — not a bound on word length, but a bound
of 6 on the O*-revisit gap.

**Universe-wide verification.** `verify_rr_o_star_alphabet.py` checks
every legal macro-edge from every reachable state at all five roots (not
only hub-completing edges): 18,778 legal edges, 180 O*-steps, identical
histograms at every ell (`E:+1` 14, `R:+2` 18, `R:+4` 4), and **0**
violations of the E delta, **0** odd R deltas, **0** phase revisits, **0**
F events targeting O*. That exhaustively confirms premises (a) and (e)
as well.

**Net**: the parity chain is now 손증명 at every step except one — the
O*-revisit gap bound — and even that is reduced to a concrete finite
threshold. Two honest limits remain: the gap bound itself is 미완료, and
closing it would give only #Z_{->O*}; the evenness of #Z_{->other}
(observed 95/95) still has no argument at all. So
`|P| + #R_{<=C} ≡ 1 (mod 2)` remains **미완료**.

### Round 26 — the O* revisit-gap bound is FALSE, and with it the alphabet route

`src/enumerate_rr_first_return_words.py`, `src/analyze_rr_length7_obstructions.py`,
`src/verify_rr_o_star_gap.py` -> `outputs/rr_first_return_table.json`,
`outputs/rr_length7_counterexamples.json`, `outputs/rr_o_star_excursions.json`,
`outputs/rr_gap_certificates.json`. Six write-ups, led by
`research/RR_O_STAR_REVISIT_GAP.md`. No completion search; the N=0 search
and checkpoint were not touched.

**Counting convention, fixed and corrected.** L = first-return word
length (macro-edges from the O* port up to and including the edge landing
back in O*); G = L−1 = the gap. Round 25's write-up compared observed G
values (0, 3, 4) against a group threshold stated in L (≤ 6) without
saying so. The conclusion was unaffected — L = 1, 4, 5 are all ≤ 6 — but
the units were mixed, and every table now carries both.

**The target proposition is 반증됨.** Enumerating legal first-return
excursions from all five abandonment roots to L ≤ 8 — a ceiling set
deliberately past the group threshold 6, so that "nothing exceeds 6"
would be a finding rather than an artifact — produces legal excursions of
**L = 7 with ODD return exponent 3, at every one of the five roots**:

```
joints   = w3:201, w3:201, w2:10, w3:210, w2:10, w3:210, w3:201
symbolic = F F E F E F R        (#R=1, #F=4, #E=2)
```

Enumerating every literal word of length 7 and 8 over the four ell=5
generators (81,920 words) and replaying each through the engine: of the
39 odd-exponent first-return words, **38 replay legally**. Exactly one is
removed, by `N_exceeded_monotone`. Section 3's goal — find a common
legality obstruction that kills all of them — has the opposite answer.

**No budget coordinate separates them.** Excursion length fails (L = 7
and 8 carry both odd and even). The R budget fails: the minimal
counterexample needs only 1 R, inside RR's budget of 2. The F budget
fails: odd excursions need #F ≥ 3, but a legal *even* excursion of length
5 (`FFEFR`) already has #F = 3, and observed same-component words reach
#F = 3 too — so no true F bound excludes them.

**The legal length spectrum is not an interval**: {1, 4, 5, 7, 8}.
L ∈ {2,3} are impossible group-theoretically; **L = 6 is
group-theoretically possible but killed by legality**. Since L = 6 is
impossible while L = 7 and 8 are legal, no monotone "longer ⟹ collision"
argument (section 5's prefix collision theorem) can exist. The group
graph and the legality-filtered graph differ in *both* directions.

**Why Round 25 saw no exceptions.** Its universe was depth ≤ 6 after the
abandonment, and a violating excursion needs L = 7 — there was no room
for one. Round 25's "0 violations in 18,778 edges" was the shadow of the
depth cap, not evidence for the alphabet. Using it to argue the alphabet
would be circular, and the Round 25 documents are corrected accordingly.

**What survives** (unchanged and still hand-proved): the four ell=5
composite generators, `w2:10` → E and `w3:120` → E²; F is always `w3:201`
or `w3:210`; from a port q, `w2:10` lands at q∘E (phase +1); the total
advance 4 (mod 5); phase injectivity; the winding reduction
#Z_{→O*} ≡ k (mod 2). What falls is the step that made k = 0 provable.

**Lemma A, newly hand-proved**: any excursion with L ≥ 2 must begin with
`w3:201` or `w3:210` — an orbit-preserving first edge would land back in
O* immediately, giving L = 1.

**Non-O* separation (kept strictly separate).** Across the 95 O*-landing
completions the aggregate #Z_{→other} is even 95/95, but **5 of 95
completions contain an individual orbit with an ODD zero-charge count**.
So "every non-O* orbit is entered and exited in paired excursions" is
**반증됨**; the aggregate evenness is not per-orbit and has no
explanation.

**Net**: `|P| + #R_{<=C} ≡ 1 (mod 2)` remains 미완료, and the O*
half — which Round 25 had reduced to a single lemma — is now known not to
follow from that lemma, because the lemma is false. One question is left
undecided and is stated exactly: whether a preparation prefix containing
an L ≥ 7 excursion extends to a completed same-component RR word.
Settling it needs a completion search, which this round was told not to
run.

### Round 27 — the preparation parity conjecture is REFUTED by exact witnesses

`src/build_rr_long_excursion_roots.py`, `src/search_rr_long_prefix_extensions.py`,
`src/verify_rr_long_extension_certificate.py` ->
`outputs/rr_long_excursion_prefixes.json`, `outputs/rr_long_prefix_quotient.json`,
`outputs/rr_long_prefix_extension_results.json`,
`outputs/rr_long_prefix_certificates.json`. Five write-ups led by
`research/RR_LONG_EXCURSION_EXTENSION.md`. No global RR search was
restarted — only 28 targeted roots. The N=0 search and checkpoint were
not touched.

**Terminology fixed first (it was a real trap).** Two different things
were called F: `F_def` = `ExactState.F`, the abandonment/defect counter
with `TARGET_F = 1`; `F_sym` = the fresh-orbit-opening event symbol (a Z3
joint), bounded only through `O <= TARGET_O = 25`. Round 26's "#F=4" is
`F_sym = 4` and is **not** a violation of `F_def <= 1`. Verified: all 186
prefixes have `F_def = 1`.

**Corpus and quotient.** Round 26's "38" counts WORDS legal from at least
one root; the unit that has a state is a (word, root ell) PAIR, of which
there are **186**. All 186 are distinct exact states *and* distinct
left-S6 canonical pairs (stabilizer ties all 1), so symmetry buys no
reduction in search roots.

**Hand-proved ledger obstruction removes 158 of 186.** An RR word has
exactly two R events and R2 is the last event, so a prefix lying strictly
before R2 carries at most one R. 106 prefixes already have three R's and
52 have two, leaving **28**. Nothing else in the ledger removes any of
them: Φ ∈ {1..5} all positive, hub touches 0, `O <= 8` against a budget
of 25, `N_def = 1` with exactly one R to spare.

**Target A** was fixed against the project's existing predicate (the one
`analyze_rr_ell0_family.py` uses): the second R event, child state with
`F_def = 1` and `H = 0`, and R2 source and target orbits in the same
component. Targets B (terminal continuation) and C (full NR6 completion)
were not attempted and nothing is claimed about them.

**Result: 6 FOUND, 22 INCOMPLETE, 0 EXHAUSTED_IMPOSSIBLE.** All six
witnesses were independently re-verified by literal edge-by-edge replay
(6/6 agree). The minimal one reaches Target A **two macro-edges** after
the prefix:

```
abandonment ell=4, rot^4;w2:10 -> (orbit 1, phase 0) = O*
prep 0..6 : FFEFEFR   (L=7 excursion, return exponent 3 -- ODD)
prep 7    : rot^5;w2:10  E -> (1,4) hex 0   <- HUB COMPLETER
R2   8    : rot^0;w3:120 R -> (0,2)
```

That is the established terminal normal form exactly — completer landing
on (orbit 1, phase 4) = hex0 position 5, last edge `rot^0;w3:120`,
chaining true, Φ = 0, tail length 0 at ell=4. Only the preparation
differs.

**Four propositions are refuted**, with |P| counted the same way as
`preparation_length` in `outputs/rr_preparation_words.json` (inclusive of
the completer and any tail):

| | historical ell=4 corpus (9 records) | the six witnesses |
|---|---|---|
| \|P\| | 3, 5, 7 — all **odd** | **8**, 11 |
| #R_{<=C} | 1 | 1 |
| (\|P\|+#R) mod 2 | **0** in 9/9 | **1** for the \|P\|=8 pair |
| #Z_{->O*} | even (95/95 observed) | **1 or 3 — all ODD** |

1. **#Z_{->O*} is even — 반증됨.** All six witnesses are odd.
2. ~~**The winding number k = 0 — 반증됨.** The hand-proved reduction
   #Z_{->O*} ≡ k (mod 2) still holds, and now it is the *tool*: #Z odd
   forces k odd, so k ≥ 1.~~ **[Round 28 correction: both halves of this
   are wrong.]** All six witnesses have **k = 0**, so `k = 0` is *not*
   refuted. What actually broke is the reduction itself: `#Z ≡ k` was
   never unconditional — it assumed every R step into O* has even phase
   displacement, which is exactly the alphabet premise refuted in Round
   26. Witness 0's O* steps are `[R(δ=3), E(δ=1)]`. See
   `research/RR_PARITY_CONJECTURE_REFUTATION.md` §1–2 and the corrected
   unconditional identity in the Round 28 section below.
3. **ell=4 preparation length is odd — 반증됨** by the two \|P\| = 8
   witnesses.
4. **\|P\| + #R_{<=C} invariant — 반증됨.**

**What survives**: every hand proof from Rounds 25–26 is untouched — F
never targets O*, the O* zero-charge events are exactly the E events, the
total advance is 4 (mod 5), phases are not revisited, at most two R steps
target O*, and #Z_{->O*} ≡ k (mod 2). The reduction was correct; the
conclusion drawn from it was not, because the alphabet premise was false.

**Why the earlier observations missed this.** A word containing an L = 7
odd excursion needs at least 9 macro-edges (1 abandonment + 7 excursion +
≥1 to R2), i.e. depth ≥ 8 after the abandonment. Every universe from
Rounds 19–25 was capped at depth 6 (comparison runs 7, one at 8). The
"95/95 even" and "0 violations in 18,778 edges" measurements were
**exactly correct within their scope** and simply could not contain a
counterexample. `research/RR_DEPTH_CAP_ARTIFACTS.md` lists every
observation that was scope-limited in this way.

**Honest limits**: the 22 INCOMPLETE roots were truncated at a node cap
of 8,000 and are **not** evidence of impossibility — `EXHAUSTED_IMPOSSIBLE`
was returned zero times. All six witnesses are at ell=4, consistent with
the established ell dichotomy, and nothing is claimed about ell=0. And
Target B/C remain untouched: these are same-component R2 boundaries, not
full completions. The parity proposition was always evaluated at the R2
boundary (the Round 18 counting-unit standard), so Target A is the right
level for the refutation — but it does not make these into NR6 solutions.

**Net**: the preparation parity conjecture, the target of Rounds 24–27,
is **closed as false**. `#Z_{->other}` evenness remains a separate open
question and is deliberately not combined with this result.

### Round 28 — certificates, the corrected identity, and a Round 27 error fixed

`src/verify_rr_counterexample_certificates.py`,
`src/analyze_rr_long_normal_forms.py`, `src/build_rr_target_b_ledgers.py`
-> `outputs/rr_six_counterexamples.json`,
`outputs/rr_counterexample_certificates.json`,
`outputs/rr_long_normal_form_classes.json`,
`outputs/rr_target_b_static_ledgers.json`. Six write-ups led by
`research/RR_PARITY_CONJECTURE_REFUTATION.md`. No global NR6 completion
search was started; no Target B search was run; the N=0 checkpoint was
not touched.

**Two Round 27 errors corrected.**

1. *The k claim.* Round 27 said the reduction `#Z_{->O*} ≡ k` survived
   and now detected `k ≥ 1`. Both halves are wrong: **k = 0 in all six
   witnesses**, so Conjecture C (`k = 0`) is **not refuted**. The
   *reduction* is what broke — it always assumed every R step into O* has
   even phase displacement, i.e. the alphabet premise refuted in Round 26.
2. *The |P| convention.* Five different lengths were being written |P|.
   Auditing the 12 historical records: `P_reported + #R_{<=C}` is 1 at
   ell=0 and 0 at ell=4 (**not uniform**), while
   `P_core + #R_{<=C}` is **1 in 12/12**. So Conjecture A is a statement
   about `P_core` (edges strictly before the completer). Round 27 quoted
   the baseline under the non-uniform convention; it identified the same
   violating witnesses, but the baseline was wrong.

**The corrected identity — unconditional, and the round's main survivor:**

> **#Z_{->O\*} ≡ k + #R_{odd-δ} (mod 2)**, where #R_{odd-δ} counts R
> steps into O* whose phase displacement is odd.

손증명: F never targets O* so #Z = #E; every E step has δ = +1
(Σ⁵∘τ = E); Σδ = 4 + 5k; reduce mod 2. Verified on all six witnesses
(6/6). In the historical 95 completions #R_{odd-δ} = 0, which is why the
identity *looked* like `#Z ≡ k` there.

**Certificates.**

| conjecture | baseline | violated by | verdict |
|---|---|---|---|
| A: `P_core + #R_{<=C} ≡ 1` | 1 in 12/12 | witnesses 0,1 (7+1=8) | **반증됨** |
| B: `#Z_{->O*} ≡ 0` | even 95/95 | **all six** (1 or 3) | **반증됨** |
| reduction `#Z ≡ k` | holds 95/95 | **all six** | **반증됨** |
| C: `k = 0` | 0 in 95/95 | **none** | **not refuted** |

**Minimality and quotient.** Witness 0 is minimal in *all seven*
criteria simultaneously (shortest excursion L=7, shortest extension 2,
fewest R before C, fewest F_sym=4, smallest k, smallest depth 10,
lexicographically least) — fixed as the canonical minimal
counterexample. At the **decorated R2 boundary** level all six collapse
to **one class**: (r1tgt, r2src, r2tgt, chaining, Φ) = (1, (1,4), (0,2),
True, 0). The counterexamples differ only in preparation, never in the
terminal block. The coarsest meaningful split is two classes: I
(witnesses 0,1; L=7, #Z=1, phase word [0,3,4]) and II (2–5; L=8, #Z=3,
phase word [0,1,2,3,4]).

**Parity accounting, measured and not assumed.** Zero-charge events
targeting O* occur **entirely outside the excursion** (0/1 and 0/3 —
none inside). And `#Z_{->other}` is **7 (odd)** in witnesses 2–5, so the
"non-O* total is even" observation is refuted too. Total #Z is 7 in
Class I and 10 in Class II — no conserved quantity was found, and no
"compensation elsewhere" was assumed.

**What got stronger.** Six witnesses all chain (r1tgt = r2src = 1), so
**same-component ⇒ chaining is not refuted** — these are six new
confirming instances at preparation lengths 7 and 10, well beyond the
historical maximum of 6. And the terminal normal form held in all six:
O* = orbit 1, completer at (1,4) = hex0 position 5, final edge
`rot^0;w3:120`, chaining, Φ = 0, tail 0. Across 15 cases spanning
preparation lengths 2–10 there are **zero exceptions** — this is now the
strongest surviving candidate for promotion to a hand proof.

**The 22 INCOMPLETE roots**, classified from the existing log only: all
share a symbolic excursion class with a FOUND root and differ only in
abandonment ell (FOUND all at ell=4, INCOMPLETE at ell∈{0,1,2,3}). Each
reached 7,662–7,825 R2 boundaries with no same-component hit, but **none
exhausted its frontier** — all hit the node cap. They remain **bounded
incomplete** and are not read as impossibility.

**Target B** was defined precisely (no further R, F_def = 1, H = 0,
area_a throughout, ending at a state admitting a pure-rotation suffix)
and kept strictly separate from Target C. Its static ledger at the six
post-R2 states: **Φ = 0 everywhere** (zero slab slack), exactly 3 legal
outgoing edges everywhere, 647–665 permutations still unvisited. **No
immediate static contradiction** — reported as "none", not dressed up as
a search failure, and explicitly not evidence that a continuation
exists. Five safe prunes were hand-proved for a future search; three
more (component merge deficit, terminal endpoint, remaining-cost bound)
are 미완료, and the remaining-cost bound is what a Target B search would
actually need.

**NR6 impact.** None of this touches `L_6 ≥ 872` or `L_6 ≥ 867`: a Target
A witness is a same-component R2 boundary, which has no logical
connection to an NR6 completion. What closed is the **parity program
this session itself built in Rounds 24–26**. The U/J branches are
untouched. The surviving RR routes are terminal-normal-form uniqueness
and same-component ⇒ chaining.

### Round 29 — the centre moves to terminal structure and Target B cost

`src/verify_rr_terminal_normal_form.py`,
`src/verify_rr_corrected_phase_identity.py`,
`src/analyze_rr_target_b_remaining_cost.py` ->
`outputs/rr_terminal_normal_form_ledger.json`,
`outputs/rr_corrected_phase_identity.json`,
`outputs/rr_target_b_transition_universe.json`,
`outputs/rr_target_b_demand_vectors.json`,
`outputs/rr_target_b_lower_bounds.json`. Six write-ups. No search of any
kind was run; the N=0 checkpoint was not touched; no refuted parity claim
was revived.

**Three base computations, from the engine's own tables.**

- (H1) hex0 position -> (orbit, phase): 0:(0,0) 1:(120,0) 2:(33,1)
  3:(9,2) 4:(3,3) **5:(1,4)**.
- (H2) a weight-1 rotation has dP=0, dvisited=1 (dPhi=+1); a joint has
  dP=1, dvisited=1 (dPhi=-5). Hence **dPhi = ell - 5** for a macro-edge,
  and Phi(initial) = 6.
- (H3) `remaining_window_capacity_prune` is true **exactly when Phi < 0**
  (400/400 agreement, and identical by definition). So **Phi >= 0 is Area
  A's own capacity prune**, not an extra assumption.

**Terminal normal form: 7 of 10 claims now hand-proved.**

| claim | grade |
|---|---|
| T2 completer targets (orbit 1, phase 4) | **손증명** |
| T4a the edge after C is forced to ell=0 | **손증명** |
| T4b if that edge is an R it is `rot^0;w3:120` | **손증명** |
| T5 R2 source orbit = 1 | 손증명 (given T3) |
| T6 R2 target orbit = 0 | 손증명 (given T3, T4b) |
| T7 Phi = 0 at the R2 boundary | **손증명** |
| T8 the R2 boundary is same-component | 손증명 (given T3, T4b) |
| T1, T3, T9 | **bounded observation 15/15 — not promoted** |

T2: at ell=4 the abandonment's run visits hex0 positions 0..4, a rotation
run moves only inside the current hexagon, so hex0 can be re-entered only
as a joint target; the completer is the first such edge and cannot
revisit, so it lands on the unique residual position 5 = (1,4).
T4a: from position 5 a rotation would go to position 0, visited since the
initial state. T4b: at that endpoint exactly one of the four joints is an
R (`w2:10` is Z2, `w3:201`/`w3:210` are Z3).
T7: 6 - 1 (A_4 at ell=4) - 0 (every preparation edge at ell=5) - 5 (R2 at
ell=0) = 0 — **the preparation length cancels exactly**, which is why
short and long preparations agree.
T8: orbit 0 has a port at hex0 position 0 (visited initially) and the
completer visits hex0 position 5, a port of orbit 1; both are incident to
hexagon 0. **So same-component is automatic at ell=4 once C fires — it is
not a constraint**, and chaining cannot follow from it.

**Minimal axiom set**: T2, T4a, T4b, T8 use **ell=4 alone**. T7 adds the
Phi slab and "every preparation edge is ell=5". The other eight candidate
assumptions (RR, same-component, F_def, N=2, Unique Hub, Hub Touch,
Hub Exit Source, R2 legality) are **all unnecessary**.

**T3 is not forced by legality**: at the post-C endpoint all four joints
are legal and three are not R. Six candidate obstructions were checked
and all six fail. 미완료.

**Chaining, partially proved.** CH1 (손증명): if the completer C is
itself an R, then C = R1 (R2 comes after C), and C's target is (1,4) by
T2, so R1's target orbit is 1 = R2's source orbit. That covers **5 of the
15** ell=4 cases (C = `w3:120` once, `w3:201` twice, `w3:210` twice). The
other 10 have C = `w2:10` and remain 미완료; the exact residue is CH2:
"when C is zero-charge, P_core contains an R targeting orbit 1". Note
CH1 uses no parity at all — only the R count and T2 — which is what the
long family required, since it breaks parity while keeping chaining
(preparation lengths 2–10, 15/15).

**Corrected phase identity, formalised standalone** (deliberately not
used by the terminal proof): `#Z_{->O*} ≡ k + #R_{odd-δ} (mod 2)`, 손증명,
verified 95/95 historically (where #R_{odd-δ} = 0, which is why the
collapsed form looked like a theorem) and 6/6 on the counterexamples
(where the collapsed form fails every time).

**Target B: exact reformulation.** The Phi=0 continuation theorem
(손증명): at Phi=0 every admissible macro-edge has ell=5, since dPhi =
ell-5 and Phi>=0 is the capacity prune. An ell=5 macro-edge completes the
hexagon the walk stands in and steps into the next, covering exactly 6
fresh permutations. The six post-R2 states have **one identical legal
transition signature** — 3 legal edges each (`rot^5;w2:10`/Z2 and two
Z3), everything else `F_exceeded`. Hexagon census: 1 partial hexagon and
**untouched hexagons = B exactly** (110 and 107). Therefore

> **Target B ≡ a Hamiltonian path on the remaining hexagons**, each
> completed by one macro-edge, ending with a pure-rotation suffix of 5.

**Remaining cost.** Phi = 0 is exactly the identity **U_perm = 6B + 5**
(665 = 6·110+5; 647 = 6·107+5). So the continuation must be a **perfect
packing with zero slack**. The permutation-coverage lower bound
ceil((U-5)/6) equals B exactly, giving **slack 0**; the orbit/phase and
component-merge bounds are 미완료 (no nontrivial safe bound follows).
Verdict per state: **"lower bound incomplete"**, not "no contradiction" —
slack 0 is neither a contradiction nor evidence of feasibility, and none
was manufactured.

**Why no search was run**: branching is at most 3 but depth is 110, and
with slack already 0 a single weak extra obstruction — a degree-1 vertex
or a disconnection in the hexagon graph — would settle it statically.
Building that graph is the natural next step and was not done here.

### Round 30 — Target B is IMPOSSIBLE from all six counterexample states

`src/build_rr_target_b_hexagon_graph.py`,
`src/analyze_rr_target_b_obstructions.py`, `src/analyze_rr_ch2_chaining.py`
-> `outputs/rr_target_b_hexagon_graphs.json`,
`outputs/rr_target_b_port_graphs.json`,
`outputs/rr_target_b_obstruction_certificates.json`,
`outputs/rr_ch2_witnesses.json`, `outputs/rr_orbit1_opener_ledger.json`.
Six write-ups. **No DFS was run** — and for these six states none is
needed, because the obstruction is a counting argument.

**Part A. The counting obstruction (손증명).**

> From a Phi=0 Target A state, a Target B continuation requires
> **B ≤ 5·(O_capacity + R_capacity) + 4**.

Proof: at Phi=0 every macro-edge has ell=5 (R29), and such an edge is
right-multiplication by one of the composite generators (R26). E and E²
preserve the E-orbit, so `w2:10` and `w3:120` can never open a new orbit
— `w2:10` is a Z2 and `w3:120` (weight 3) is **always an R**.
`w3:201`/`w3:210` leave the orbit, so each is a fresh opening (costing an
O slot) or an R (costing an R slot). Crucially, **at most 4 consecutive
orbit-preserving edges**: a run moves the entry port p → p·E^{s} with s a
partial sum of 1s and 2s, the ports must be distinct, p·E^s = p·E^{s'}
iff s ≡ s' (mod 5), and there are only 5 residues. Hence with m
orbit-changing edges, B = (preserving) + m ≤ 4(m+1) + m = 5m + 4, and
m ≤ O_capacity + R_capacity. ∎

| # | B | O_cap | R_cap | m_max | B_max | margin |
|---|---|---|---|---|---|---|
| 0,1 | 110 | 19 | 1 | 20 | 104 | **+6** |
| 2–5 | 107 | 17 | 1 | 18 | 94 | **+13** |

All six verdicts are `BUDGET_OBSTRUCTION`. R_capacity was set to 1 — the
*permissive* `AREA_A.n_limit = 3` — so the result does not depend on
Target B's own no-extra-R clause.

**Round 29's slack=0 was NOT used**, per the round's warning. The
argument uses only B, O and N.

**Scope, stated honestly**: the same inequality clears **9 of the 12**
historical short-preparation boundaries (O = 2,3,4 there). In closed
form the obstruction is `D = 5O − P > 13 − 5·R_cap`, so it is driven by
how many fresh orbits the preparation opened — which is exactly what the
long preparations did. **Target B remains open for short preparations.**

**The graph model, stated precisely before using the word Hamiltonian**:
the port graph p → p·g_j on permutations is **static**; the hexagon-level
graph is **not** (which H' is reachable depends on the entry port), and
legality is vertex deletion at hexagon level. A safe over-approximation
was built (edges dropped only when statically impossible): 660/642 ports,
~1,700 edges, out-degree ≤ 3 because `w3:120` is always an R. Terminal
compatibility turned out to have **no discriminating power** — every
untouched hexagon admits the 5-rotation suffix. SCC/cut tests were not
run: after the counting obstruction there is nothing left to test.

**Part B. CH2 chaining — the proposed architecture is refuted.**

The round's Lemma CH2-B ("orbit 1's first opener is R1") is **반증됨**:
at ell=4 the **abandonment joint itself** lands on (1,0) with
`new_orbit=True`, so orbit 1's first opener is the abandonment. The
first-opener route cannot give chaining, and §19's architecture must be
replaced.

The CH2 corpus is 10 cases (6 long + 4 historical), all with C =
`rot^5;w2:10` and all with R1 target orbit 1 (phases 1, 2, 3). A
root-local search over ell=5 preparations to depth 8 found **zero**
counterexamples with C zero-charge and R1 target ≠ orbit 1 — but it did
find **one legal completion with no R at all before C** (`#R_{<=C} = 0`).
That is precisely the scenario that blocks the CH2 argument: the walk can
reach (1,4) from the abandonment's (1,0) by pure E steps. Whether such a
prefix extends to an RR word was not determined. Search status: **bounded
incomplete** (frontier truncated at depth 8; real witnesses reach
P_core = 10).

**Terminal normal form status**: T2, T4a, T4b, T7 손증명 unconditionally;
T5, T6, T8 손증명 given T3; T1 and T9 proved only via CH1 (5 of 15); T3
remains an exact observation, not forced by legality.

**NR6 impact**: none claimed. Target B failing at six boundaries says
those six have no slab continuation; it says nothing about `L_6 ≥ 872`,
about Target C, or about the short-preparation boundaries that pass the
obstruction.

### Round 31 — 10 of 18 Target A boundaries lose Target B; CH2 still open

`src/analyze_rr_target_b_survivors.py`,
`src/build_rr_refined_capacity_bound.py`,
`src/analyze_rr_ch2_r_free_extension.py` ->
`outputs/rr_target_b_survivors.json`,
`outputs/rr_refined_phase_capacities.json`,
`outputs/rr_saturating_blocks.json`, `outputs/rr_ch2_r_free_prefix.json`,
`outputs/rr_ch2_extension_results.json`. Six write-ups. The long six were
not re-searched; the N=0 checkpoint was not touched; no global NR6 search.

**Cleaner derivation of the capacity theorem.** The continuation's entry
ports p_0..p_B split into orbit segments, one per maximal run of
orbit-preserving edges. There are at most m+1 segments and a segment uses
at most 5 ports of its orbit, so **B+1 ≤ 5(m+1)**, i.e. B ≤ 5m+4 with
m ≤ O_cap + R_cap. This needs only Phi=0 and the generator structure —
**not ell=4** — so it applies to the ell=0 boundaries too.

**Part A — the exact survivor set.** Over all 18 known Target A boundary
*states* (not words):

| class | states | CAPACITY_IMPOSSIBLE | survivors |
|---|---|---|---|
| long (P_core 7, 10) | 6 | **6** | 0 |
| short (P_core 2, 4, 6) | 12 | **3** | 9 |

The 9 survivors have 9 distinct canonical state hashes (no quotient
reduction) and only 2 distinct legal outgoing signatures. Margin
histogram `{1:1, 2:1, 8:3, 9:3, 10:1}` — **no equality case exists**; the
tightest is M=1. Equality would force every segment to use all 5 ports,
hence a strict alternation of length-4 saturating blocks and openings.

**Part C — only one saturating block is usable.** Preserving runs over
{E, E²} have 2/4/5/3/0 legal words at lengths 1..5, so length 4 is
maximal and there are exactly **three** saturating blocks: `EEEE`,
`E2EEE2`, `E2E2E2E2`. But `w3:120` = E² is *always* an R (orbit-preserving,
weight 3), and R_cap = 1 everywhere, so the latter two need 2 and 4 R
slots. **`EEEE` is the only usable saturating block** — 손증명. The
block-transition graph was not built: with no M=0 survivor there is
nothing it would apply to.

**Part B — refined phase/port capacity.** With
c(q) = #{ports of q whose hexagon is still unvisited}, the safe bound
B+1 ≤ c(q₀) + (sum of the O_cap largest c over unopened orbits) + 5·R_cap
removes **one more survivor** (ell=4, P_core=4, uniform margin +1). The
improvement is exactly 2 at every survivor and comes entirely from
c(q₀)=3; unopened orbits almost all still have all five ports, because
only 4–9 hexagons are visited at these boundaries. **8 survivors remain.**
Component-compatible capacity was *not* counted — the required final
component structure is uncharacterised, so no heuristic was used.

**Part D — the R-free-to-C prefix, pinned down.** It is startlingly
simple and unique in scope: `rot^5;w2:10` four times, i.e. the pure E-walk
climbing orbit 1 from the abandonment's (1,0) through (1,1), (1,2), (1,3)
to (1,4) = the completer. P_core = 3, zero R before C, post-C Phi = 5,
N = 0. **This is exactly what blocks CH2**: legality alone does not force
an R targeting orbit 1 before C, because there need be no R at all.

Section 18's hoped-for obstruction does **not** hold: after C the edge is
forced to ell=0 (T4a), but **all four joints are legal** there and three
are not R. Choosing `w3:120` would make R1 target orbit **0**, which with
an R2 sourced in orbit 1 would be a genuine non-chaining counterexample.

The extension search from the post-C state (extension depth ≤ 9, 64,500
nodes, node cap not reached) found **0 Target A boundaries** and **0
counterexamples**, but the frontier was **truncated by the depth
ceiling** — reported as **INCOMPLETE**, not as absence.

**Part E — T3's status sharpened.** T3 ("R2 fires on the edge right after
C") is **not** a local legality statement — all four joints are legal
there. Three derivation routes are now excluded: local legality
(반증됨), Target B capacity (Target A does not require Target B — Round
30 proved six boundaries have no continuation yet remain Target A), and
the RR two-R constraint (the R-free prefix is not excluded). T3 remains
**exact observation 15/15**.

**Net**: 10 of 18 Target A boundaries provably have no Target B
continuation; 8 short survivors remain open. CH2 and T3 remain 미완료,
with their obstructions now precisely located. Nothing here touches
`L_6 ≥ 872`, Target C, or the U/J branches.

### Round 32 — the orbit-reuse penalty; 7 survivors left

`src/build_rr_target_b_segment_graph.py`,
`src/analyze_rr_segment_capacity.py`,
`src/verify_rr_segment_certificates.py` -> `outputs/rr_segment_graphs.json`,
`outputs/rr_full_block_transitions.json`,
`outputs/rr_short_survivor_ledger.json`,
`outputs/rr_segment_defect_budgets.json`,
`outputs/rr_segment_verdicts.json`. Six write-ups. **No permutation-level
DFS**; the N=0 checkpoint was not touched; CH2 was not re-searched.

**Segment model.** A Phi=0 continuation is S_0 X_1 S_1 ... X_m S_m with
S_i a preserving run inside one E-orbit and X_i an orbit-changing edge.
Preserving runs, exhaustively: lengths 0–4 have 1/2/4/5/3 legal words and
length ≥5 has **none**, so capacity ≤ 5 and a capacity-5 segment needs
exactly 4 preserving edges.

**EEEE full-segment theorem (손증명).** The three length-4 saturating
blocks are `EEEE`, `E2EEE2`, `E2E2E2E2`, with E² counts 0, 2, 4 — **always
even**, so no saturating block uses exactly one E². Since `w3:120` = E² is
always an R and R_cap = 1 everywhere, the last two are unaffordable:
**`EEEE` is the only usable capacity-5 block.** The converse also holds —
EEEE from any entry phase visits all five phases — *provided* the five
ports' hexagons are free, which is exactly the distinct-hexagon condition.

**The new ingredient: the orbit-reuse penalty (손증명).** A segment
entered by an orbit-changing **R** lies in an already-open orbit — that is
precisely what makes the edge an R rather than a fresh opening
(`new_orbit=False`). An open orbit has at least one visited port, so such
a segment has capacity **at most 4**. Hence the refined bound's `5·R_cap`
term is an over-estimate and must be `4·R_cap`:

> **B+1 ≤ c(q₀) + Σ(O_cap largest c(q)) + 4·R_cap**

| ell | P_core | B+1 | (A) | (B) | (B+R) | verdict |
|---|---|---|---|---|---|---|
| 0 | 2 | 115 | 125 | 123 | 122 | survivor |
| **0** | **4** | **113** | 115 | 113 | **112** | **removed — by the R penalty** |
| 4 | 2 | 116 | 125 | 123 | 122 | survivor ×3 |
| **4** | **4** | **114** | 115 | **113** | 112 | **removed — already by (B)** |
| 4 | 6 | 112 | 120 | 118 | 117 | survivor ×3 |

**7 SEGMENT_SURVIVORs remain** (verdicts: 7 survivor, 2
SEGMENT_CAPACITY_IMPOSSIBLE, 0 incomplete). Cumulatively: 18 → 9 (R30) →
8 (R31) → **7**.

**The full-block graph gives nothing.** Nodes (orbit, entry phase) = 720,
EEEE-then-exit transitions = 1,440, **out-degree exactly 2 at every node,
zero dead ends**. Exactly half the transitions land in an orbit sharing no
hexagon with the source. No degree, sink, or terminal obstruction exists —
the graph is too regular to discriminate. That is itself informative:
**Target B's obstructions come from capacity accounting, not graph
topology**, now confirmed two rounds running. The "maximum realizable
segment chain" was therefore not computed separately — over the
over-approximation it is unbounded, and its finiteness *is* the capacity
bound.

**A methodology correction made mid-round.** The greedy hexagon-disjoint
orbit family is a **lower** bound on the maximum, so it can never certify
an obstruction. It initially appeared to block two survivors (greedy 20 <
f_min 21, 22); that was replaced by the safe ceiling
⌊#unvisited hexagons / 5⌋, which blocks **nothing**. Globally the maximum
pairwise hexagon-disjoint family is exactly **24**, and a perfect
partition of all 120 hexagons into 24 orbits exists — so no
disjointness contradiction is available at all.

**Still 미완료**: component-compatible capacity (the required *final*
component structure is uncharacterised, and no heuristic was substituted);
the 7 remaining Target B BOUNDARY survivors (a boundary-state count, unrelated to the later 7-ROOT continuation-audit count -- see `RR_ROUND37_COUNT_UNIT_CORRECTION.md`); CH2 (status fixed, not re-searched); T3
(exact observation 15/15 — the segment structure gave no new route to it).

**Next-round shape**: the full-block graph is small (720 nodes) but
topologically useless. An exact DP/SAT should be posed over **resource
allocation** — which unopened orbits are used, in what order, with how
many ports each — subject to O/R slots, hexagon disjointness, defect
budget ≤ M and total ports = B+1. That is an exact-cover/ILP, far smaller
than a depth-100 DFS, but it cannot be fully encoded until the component
condition is characterised.

### Round 33 — the exact-cover relaxation has no power; the bottleneck is order

`src/build_rr_target_b_exact_cover.py`,
`src/solve_rr_target_b_relaxations.py`, `src/verify_rr_target_b_unsat.py`
-> `outputs/rr_segment_options.json` (= `..._r33.json`),
`outputs/rr_target_b_ilp_models.json`,
`outputs/rr_target_b_relaxation_results.json` (=
`rr_segment_relaxation_results_r33.json`),
`outputs/rr_target_b_reconstructed_solutions.json`,
`outputs/rr_target_b_unsat_certificates.json`. Seven write-ups. No
permutation-level DFS; N=0 untouched; the long six were not re-searched;
the full-block graph's degree/SCC was not re-analysed.

**The model.** An ell=5 macro-edge completes exactly the hexagon it stands
in, so the chosen segments must PARTITION the residual hexagons. Binary
variable per option (orbit, entry phase, preserving word, exit type);
constraints on hexagon coverage (= 1 each), port uniqueness, segment
count, total capacity = B+1, R budget, O budget, exactly one initial
segment, and defect ≤ M. Corpus: 8,811–9,529 options per survivor, **zero
hexagons with no option**, and the residual hexagon count equals B+1
exactly. The generator prediction p → p·g_j was checked against
`macro.macro_edges()` at every survivor: **7/7 agree** (the corpus is not
built on our own bookkeeping).

No solver library exists here (`pulp`, `ortools`, `pysat`, `scipy` all
missing), so every layer is decided by hand-rolled exact reasoning or
marked bounded incomplete — nothing is delegated to an unverified oracle.

**R2 follows from R1 (손증명)**: each option uses exactly one port per
covered hexagon and an orbit's five ports lie in five distinct hexagons,
so a hexagon partition forces port uniqueness. R2 is not a separate
constraint.

**New hand proof — the phase-walk initial capacity.** Rounds 31–32 bounded
the first segment by `c(q₀)+1` = 3. That over-counts: the segment must be
a legal **phase walk**, its covered phases being partial sums of a word
over {+1,+2}. The true capacity is **2** (best initial word `E`) at all
nine CAPACITY_SURVIVORs, tightening the bound by exactly 1. It removes no
new survivor — but it **independently re-derives both Round-32 removals**
(ell0 P_core=4: 111 < 113; ell4 P_core=4: 111 < 114) by a completely
different route, so those two now have two independent proofs.

**R1 results: FEASIBLE 4, INCOMPLETE 3, EXHAUSTED_INFEASIBLE 0.** The four
feasible ones have explicit covers of 24–25 segments with total capacity
exactly B+1, found by a partition-seeded construction (the deterministic
greedy yields a perfect 24-orbit partition of all 120 hexagons; the
leftover hexagons are finished by Algorithm X).

**The round's real finding: the cover relaxation is powerless.** Looking
at those four covers as flows:

| survivor | segments | successor edges | segments with no successor | longest chain |
|---|---|---|---|---|
| ell0 P2 | 24 | **0** | 24 | **1** |
| ell4 P2 ×3 | 25 | **1** | 24 | **1** |

Among 24–25 segments there are **0 or 1** successor edges. Exact cover
constrains hexagons only, so the segment sets it produces are almost
completely disconnected as walks. **R1 discriminates nothing; the binding
layer is R3 (flow/order).** The next model must be flow-first — grow an
ordered path while consuming hexagon resources — not cover-first. Branching
there is small (≤ 2 exits × ≤ 5 words) over depth 24–25, far smaller than
a permutation-level depth-115 DFS.

**A self-correction made mid-round.** The draft recorded
`NO_HAMILTONIAN_ORDER` as `first_failing_layer = "R3"`. That is wrong: one
unorderable cover does not make R3 infeasible, since another cover of the
same state may be orderable. The status was renamed
`NO_ORDER_FOR_THIS_COVER`, `first_failing_layer` was set back to `None`,
and the note "only an exhaustive enumeration of covers could turn this
into an R3 obstruction, and that was not done" is recorded in the output.
`verify_rr_target_b_unsat.py` audits this mechanically: **7 statuses
audited, 0 violations, 0 UNSAT certificates claimed.**

**Component (R5) is not the bottleneck.** Round 29–32 repeatedly named it
as the next obstacle. It is not: no survivor passes R0–R4, so the question
"is component the real bottleneck?" has not yet become meaningful. R3
comes first. Component labels (attach/extend/merge/revisit/isolate) are
recorded but **never imposed**, because Target B's final component
requirement is still uncharacterised — a fact now stated explicitly rather
than deferred.

**None of the seven survivors was removed this round.** Recorded as an
honest result rather than forced: what was gained is four explicit R1
covers, the quantitative demonstration that order is the bottleneck, one
new hand proof, and independent confirmation of two earlier removals.

### Round 34 — flow-first: all 18 known Target A boundaries lose Target B

`src/build_rr_segment_successors.py`, `src/search_rr_target_b_flow.py`,
`src/verify_rr_target_b_flow.py` -> `outputs/rr_segment_successor_index.json`,
`outputs/rr_flow_first_models.json`, `outputs/rr_flow_search_results.json`,
`outputs/rr_flow_certificates.json`. Five write-ups
(`RR_TARGET_B_FLOW_FIRST_MODEL.md`, `RR_TARGET_B_SEGMENT_SUCCESSORS.md`,
`RR_TARGET_B_MEET_IN_THE_MIDDLE.md`, `RR_TARGET_B_FLOW_RESULTS.md`,
`RR_TARGET_B_R3_CERTIFICATES.md`) and `tests/test_rr_flow_first.py`.
No permutation-level depth-100 DFS; the N=0 checkpoint untouched; no cover
was built at any point.

**The model changed from cover-first to flow-first.** Round 33's covers had
0-1 successor edges among 24-25 segments. Round 34 measured the successor
relation over the **whole** option universe instead of inside a cover:
out-degree min/mean/max = **0 / ~26 / 30**, with 7,207 of 9,340 options at
the structural ceiling 30 = 2 joints x 15 words. So the 0-1 figure was an
artefact of the partition-seeded covers, and Round 33's refusal to call it
an R3 obstruction (`NO_ORDER_FOR_THIS_COVER`) is confirmed by measurement,
not merely by caution. Indexing is by exit/entry **port** — every
permutation is a port of exactly one E-orbit, so boundary keys and
permutations coincide, 720 slots, no O(n^2) pairwise comparison. Resources
(`R_used`, `O_used`, `F_def`, coverage) are deliberately **excluded** from
the key and enforced at traversal time.

**Hexagon-disjointness theorem (손증명, exhaustively machine-checked).** The
120 hexagons partition the 720 permutations into blocks of 6, and an ell=5
run from a port visits exactly the 6 permutations of that port's hexagon
(checked at all 720 ports). Therefore **hexagon-disjointness implies
permutation-disjointness**: R4 is implied by R1, no permutation conflict
mask is needed, and no counterexample exists. R2 follows too, since an
orbit's five ports lie in five distinct hexagons (all 144 orbits checked).
One exception keeps R4 alive: the initial partially visited hexagon, which
has popcount **1** at all seven survivors — a measured property of these
states, not an algebraic consequence, so it stays an engine-replay
obligation.

**Segment count is not forced but is pinned to two values (safe
relaxation).** Enumerating every arithmetically consistent profile:
`ell0_P2` in {24,25}, `ell4_P2` in {24,25}, `ell4_P6` in {23,24}; and every
profile needs **at least 17-18 capacity-5 `EEEE` segments** on pairwise
hexagon-disjoint orbits. This is the counting relaxation only — the
geometry is not enforced, so realisability is not claimed.

**Result: EXHAUSTED_NO_PATH at all 7, truncated=false at all 7.** Largest
tree **1,499 nodes** against a 20,000,000 cap; deepest walk 10 segments and
**42 of 116** hexagons. The dominant prune is the dynamic capacity bound
(5,538 cut-offs vs 1,357 nodes at `ell0_P2`). The mechanism is the
interaction of two facts never before combined: the segment count is
capacity-bound from above (`Ndef = 2` everywhere, so R budget exactly 1,
so the only usable capacity-5 word is `EEEE`), while the next segment's
orbit is **flow-forced** to `p_exit·g_j` for one of two joints. After a few
segments neither forced orbit still has five free hexagons, the defect
budget (3 of 5-10 units spent by the initial segment, whose phase-walk
capacity is only 2) runs out, and the bound closes.

**Independently verified UNSAT, 7/7, zero contradictions.** A claim of a
149-node tree is normally a bug, so it was re-run on the real engine
(`macro.macro_edges` + `area_a_prune_reason(., AREA_A)`) with no knowledge
of segments, options, or covers, plus the Round 32 (B+R) bound recomputed
from `ExactState` fields alone: EXHAUSTED_NO_PATH at all seven, 281-3,558
nodes, macro depth 27-41. Cross-check on a quantity the two searches do
not share — engine macro depth (= completed hexagons) vs model covered
hexagons — agrees to within **2** (six of seven within 1: 40/41, 33/32,
36/37, 41/42, 28/29, 35/33, 27/28). Not exactly, because the model checks
its bound at segment boundaries while the engine checks after every macro
edge, and the two safe prunes differ by `used_ports - 2` on a re-entry;
that is why the agreement is evidence rather than a tautology. **Surviving ell was {5} in all seven
trees**, confirming from the engine side that Phi=0 forces full rotation
runs. The engine's R charges were also re-derived from `Ndef = S + F - O`
with `dS = [weight>=3]`, `dO = [new orbit]`, `dF = 0` after a full run:
E costs 0, E^2 costs 1, fresh opening 0, re-entry 1 — exactly the model's
budget, from the engine's arithmetic.

A weaker **area_a-only** engine variant (no capacity bound) is **INCOMPLETE
at all seven** (36,374-62,657 nodes, macro depth 70-79, 60s each) and is
reported as such — not as agreement, not as disagreement. It is recorded
because it isolates which prune does the work.

**Three of the brief's five labels were left unused, deliberately.** No
`SAT_MODEL_UNSAT_WITH_CERTIFICATE`, because **no SAT model was built** and a
SAT certificate cannot be borrowed for a search that never ran through an
encoding. No `FLOW_RELAXATION_FEASIBLE`, because no relaxed model was
solved separately. No `FOUND_TARGET_B`. Likewise **no positional/subtour
encoding** was written: in a flow-first model subtours are structurally
impossible, and adding subtour elimination would reintroduce the cover-first
failure. Meet-in-the-middle was **scoped, measured, and then correctly not
built** — the forward frontier (deduplicated on the full DP key) peaks at a
few hundred states around depth 5-6 and hits **exactly 0** by depth 8-11,
so there is no layer 12 to meet. Backward terminal reachability is a
**scope correction**: Target B's terminal condition is `covered = H`, a
coverage predicate, so a boundary-only backward set excludes nothing and
none was computed. Failure-driven cuts: **미완료**, deliberately — the
largest tree is 1,499 nodes, so there is no cost to reduce.

**Component (R5) was correctly never reached.** Every survivor fails at R3.
Rounds 29-32 named the component condition as the next bottleneck three
rounds running and were wrong each time; Round 33's correction stands.
Target B's final component requirement remains uncharacterised and nothing
here assumes anything about it.

**Cumulative Target B ledger: 18 -> 9 (R30) -> 8 (R31) -> 7 (R32) -> 0
(R34).**

**Scope, stated so it cannot be over-read.** This is **not** "Target B is
impossible". The 18 are the *known* Target A boundary states, from the
Round 27 enumeration that returned **6 FOUND, 22 INCOMPLETE** at a node cap
of 8,000; twenty-two truncated roots is a concrete reason the set may be
incomplete. What is closed is Target B from these 18. It moves neither
bound on `L_6`: verified upper bound **872**, proved lower bound **867**,
open target lower bound **872**. It does **not** prove T3 (still exact
observation 15/15 — Round 31 already excluded the "Target B capacity" route,
since Target A does not require Target B), and says nothing about CH2
(frozen), Target C, the U/J branches, or the N=0 checkpoint.

### Round 35 — Target A coverage: Q2 closed for 22 roots, Q1 still open

`src/build_rr_target_a_roots.py`, `src/search_rr_target_a_exhaustive.py`,
`src/verify_rr_target_a_coverage.py` -> `outputs/rr_22_incomplete_roots.json`,
`outputs/rr_target_a_predecessor_universe.json`,
`outputs/rr_target_a_search_results.json`,
`outputs/rr_target_a_coverage_certificate.json`. Five write-ups
(`RR_TARGET_A_COVERAGE.md`, `RR_INCOMPLETE_ROOT_ANALYSIS.md`,
`RR_TARGET_A_BACKWARD_FILTER.md`, `RR_CH1_CH2_EXTENSION_SEARCH.md`,
`RR_BRANCH_CLOSURE_SCOPE.md`) and `tests/test_rr_target_a_coverage.py`.
The known 18 were not re-searched for Target B; N=0 untouched; no global NR6
search.

**The round forced a split that had not been made before.** Target A is a
LOCAL predicate on one macro edge and does not require the word to complete
-- Round 30 already proved six Target A boundaries have no continuation and
remain Target A. So:

| | question | capacity prune legal? | verdict |
|---|---|---|---|
| **Q1** | any Target A boundary beyond this root? | **no** | 22/22 `INCOMPLETE` |
| **Q2** | any Target A boundary that could still complete? | **yes** | 22/22 `EXHAUSTED_NO_TARGET_A` |

**New hand proof: the (B+R) capacity bound re-imported to Phi > 0.** Round 32
applied it only at Phi=0. Re-derived in the pass-start currency:
`TARGET_P - P <= (5 - used ports of the current orbit) + 5(TARGET_O - O)
+ 4((n_limit - Ndef) + Phi)`. The `+Phi` term is new and necessary: a
weight-2 joint at ell<5 can change orbit at zero N cost but always costs
Phi (at ell=5 it cannot change orbit at all, since `g_{w2:10} = E`; and a
weight-2 fresh opening needs an abandonment, which would push F past
TARGET_F=1). **Slack is non-increasing**, falling by `5 - used` whenever an
orbit is abandoned unsaturated -- that monotonicity is what makes Q2 finite.

**반증됨 as a Target A prune.** Replayed along the known boundaries' own
paths, the bound reaches **-2 before the R2 edge** on one ell=0 P_core=4
boundary, so using it for Q1 would delete a genuine Target A boundary. One
counterexample is enough. It is used for Q2 only, and
`tests/test_rr_target_a_coverage.py` fails if it ever leaks into Q1.
Reassuringly, every boundary at which it fires was already
capacity-impossible in Rounds 30-32.

**Q2 result: 22/22 exhausted, every frontier natural, 0 boundaries, no cap
and no ceiling.** 14 roots decided by the bound at the root alone (slack
-2, -3, -7, -11); the other 8 by exhaustive search at 2, 2, 25, 25, 242,
248, 10,335, 10,389 nodes (slack 1, 1, 2, 2, 6, 6, 10, 10). None of the 6
FOUND roots is killed by the bound.

**Phi = ell + 1 at every root, measured.** With `dPhi = ell - 5` this gives
the ell dichotomy in one line: an R2 edge of length ell costs `5 - ell` of
Phi, so a root with Phi = ell+1 can only afford R2 edges with
`ell >= 4 - ell_root`. All 9 ell=4 known boundaries use an `ell=0` R2 edge;
all 3 ell=0 ones use `ell=5`.

**Section 4: all 22 roots share exactly ONE explosion cause signature.** Mean
branching 2.49-2.57, `Z3` fresh openings dominant, and every R2 edge fails
the same way: **~95% `source_or_target_orbit_not_in_forest`**, ~5%
`different_components`, 0 Target A. The forest is built from pass-starts
only, and at an R2 edge the source orbit is `orbit(p0 . SIGMA^ell)`, which
for ell>0 is not itself a pass-start -- so its orbit is in the forest only
by coincidence. `ell=0` makes it automatic, which is exactly why the ell=4
branch uses it.

**Section 2 quotient: nothing collapses.** 22 distinct classes at the exact,
left-S6 canonical and decorated levels; 8 resource signatures; 3 symbolic
excursion classes.

**Three filters measured and reported vacuous rather than dropped.** The
ell=4 terminal-geometry backward filter is unusable because the R2-edge ell
is 0 across the ell=4 branch and 5 across the ell=0 branch, so no single
predecessor class exists (**scope correction**). The orbit/phase
reachability over-approximation is a complete graph -- out-degree 720/720,
distance to (1,4) equal to 1 from every root -- so it excludes nothing
(**scope correction**). CH1/CH2 cannot be assigned at these roots: the hub
is incomplete at all 22 (popcount 1-5), so C lies in the extension and the
branch is undetermined; the Q2 search covers both because it explores every
extension (**scope correction**).

**TWO NEW COVERAGE GAPS, neither on the brief's list.**

1. **The short-family enumeration was depth-truncated and its
   `frontier_empty` flag cannot detect that.** `analyze_rr_ell0_family.py`
   computes `frontier_empty = not cap_hit and len(frontier) == 0` **after**
   ceiling-depth states are dropped unexpanded, so a fully truncated run also
   reports an empty frontier. Counting the dropped states directly:
   ell=0/1/2/3 at ceiling 7 drop **9,143 / 8,710 / 9,245 / 9,189** of
   12,957 / 12,367 / 13,103 / 13,029 expanded; ell=4 at ceiling 8 drops
   **30,408** of 43,459. Roughly **70% of every frontier was discarded**.
   The 12 short boundaries are valid witnesses, but the claim that they are
   *all* the short boundaries has no support. This is the largest gap in the
   Target A list, and 12 of the 18 known boundaries came from it.
2. **The 6 FOUND long roots were searched with `--stop-on-first`** and
   abandoned after one witness each (2-14 nodes), so they may carry further
   Target A boundaries never enumerated.

**Section 16 outcome: C.** Not A (Q1 incomplete at all 22), not B (no new
boundary, so the section-14 pipeline is implemented and recorded as
untriggered). `root-local exhaustive` is claimed **only for Q2**.

**Scope.** RR is **not** closed. Closed: Target B from every known Target A
boundary (R34), and completable Target A from these 22 roots (R35). Open:
Q1; the short-family ceiling truncation; the stop-on-first roots; L>8
excursions; abandonment roots and short prefixes outside the 28 long-excursion
prefixes. The 22 roots are **disjoint** from the roots that produced the
known 18, so this round extends coverage sideways rather than re-deriving it.
Nothing here moves `L_6`: verified upper **872**, proved lower **867**, open
target **872**. T3 stays exact observation 15/15; CH2, Target C, U/J and the
N=0 checkpoint are untouched.

### Round 36 — Target A search semantics audited and rebuilt; 1,398 new boundaries found, 0 completable

`src/build_rr_target_a_root_universe.py`, `src/search_rr_target_a_unified.py`,
`src/run_rr_target_a_coverage.py`, `src/verify_rr_target_a_coverage_status.py`,
`src/process_rr_new_target_a_boundaries.py` -> `outputs/rr_target_a_root_universe.json`,
`outputs/rr_target_a_search_status_audit.json`, `outputs/rr_target_a_known18_regression.json`,
`outputs/rr_target_a_resumed_frontiers.json`, `outputs/rr_new_target_a_boundaries.json`.
Five write-ups (`RR_TARGET_A_ENUMERATION_SEMANTICS.md`,
`RR_TARGET_A_SOURCE_UNIVERSE.md`, `RR_TARGET_A_Q1_Q2_SEPARATION.md`,
`RR_TARGET_A_UNIFIED_ENUMERATOR.md`, `RR_TARGET_A_COVERAGE_STATUS.md`) and
`tests/test_rr_target_a_unified.py` (25 tests). Known 18 Target B not
re-searched; N=0 untouched; no global NR6 search.

**The bug this round fixes.** Round 35's "Q1" search still called the
bundled `area_a_prune_reason` on every intermediate state. That function
bundles 10 sub-conditions; 6 assume the walk reaches `TARGET_P=121`,
`TARGET_O=25`, `TARGET_D=4` (full Area-A completion) and 4 are genuinely
local monotone invariants. Using the bundle as a traversal prune had already
smuggled completion assumptions into Round 35's own "Q1" runs. Each
sub-condition is now decomposed and classified with proof
(`RR_TARGET_A_Q1_Q2_SEPARATION.md`): **Q1-SAFE** — `F_exceeded`,
`H_positive` (both monotone, and Target A's own definition requires the
child to have `F_def==1`, `H==0`), `N_exceeded_monotone` (monotone,
disclosed Area-A scope restriction), `F1_fragment_normal_form_impossible`
(a structural consistency check, no `TARGET_*` reference at all). **Q2-ONLY**
— `P_exceeded`, `O_exceeded`, `final_D_impossible` (proved trajectory-
invariant by direct simulation, but still Q2-only in principle),
`remaining_pass_starts_exceed_remaining_windows`,
`remaining_cover_capacity_impossible` (exactly the Round 32/34/35 capacity
bound Round 35 already proved unsound as a Target A prune),
`insufficient_future_orbit_opening_credit`. `q1_safe_prune_reason` is a
**separate re-implementation**, not a filter over the bundle, with a runtime
assertion that raises if a Q2-only reason ever appears in a Q1 run.

**Unified enumerator** (`search_rr_target_a_unified.py`) replaces three
ad-hoc searches with one: a 7-status vocabulary (`FOUND_TARGET_A`,
`EXHAUSTED_NO_TARGET_A`, `INCOMPLETE_NODE_CAP`, `INCOMPLETE_DEPTH_CEILING`,
`INCOMPLETE_TIMEOUT`, `STOPPED_AFTER_FIRST`, `INVALID_ROOT`) replacing the
single `frontier_empty` boolean that could not distinguish exhaustion from
ceiling truncation; full frontier accounting (expanded/generated/queued/
pruned-by-reason/dedup-merges); deterministic edge order
(`(rotation length, joint label)`); JSON checkpoint/resume reconstructing
`ExactState` directly from serialized fields. The minimal decorated key is
`(stable_key(), r_count)` — proved sufficient (§11): CH1/CH2, R1 source/
target, and component ancestry are all recoverable from the state at the
moment needed, never independent information.

**Root universe audit** (`build_rr_target_a_root_universe.py`): 33
exact-state roots across 3 sources (5 short-family, 6 long-FOUND, 22
long-INCOMPLETE), every source's code/JSON provenance recorded, count units
fixed (raw literal / exact-state / decorated-continuation / canonical /
symbolic-first-return-class). The 5-abandonment-ℓ claim is now an
exhaustive check (ℓ tried 0..9 against the real engine, legal only at
{0,1,2,3,4}), not an inherited assumption. Overlap audit at 3 levels: **0
collisions** at exact-state and left-S6-canonical equality between the
short-family and long-excursion corpora (18 collisions at literal-state
equality are expected and not a merge candidate — different visitation
history on the same permutation means different Target A reachability).

**Known-18 regression: 18/18 pass.** Two real bugs caught and fixed while
building it: (1) an early replay attempt called `macro.macro_edges()` on an
already-rotated state, double-applying the final rotation — fixed by
mirroring `build_rr_target_b_exact_cover.py::replay_state`'s already-
verified direct-`extend()` pattern; (2) `P_core = preparation_length - 2`
holds only for ℓ=0 — for ℓ=4 it is `preparation_length - 1` (the ℓ=4
branch's R2 edge is ℓ=0, the ℓ=0 branch's is ℓ=5). The regression script
uses neither formula: it looks up each replayed boundary's `P_core` in
`rr_target_b_survivors.json` by `(root_ell, raw_hash)`. With both fixed,
18/18 replay and the 7 Round-34 survivors correctly show `EXHAUSTED_NO_PATH`.

**Coverage execution, all 33 roots, budget 100k nodes / 90s each:**

| group | roots | status | hits |
|---|---|---|---|
| short-family (r_count=0) | 5 | all INCOMPLETE_TIMEOUT | 0 |
| long FOUND (r_count=1, no stop-on-first) | 6 | all FOUND_TARGET_A | 1 each (known witness re-found) |
| long INCOMPLETE-22 (r_count=1, Q1-safe) | 22 | 20 FOUND_TARGET_A, 2 INCOMPLETE_TIMEOUT | 0-126 each |

**26 FOUND_TARGET_A, 7 INCOMPLETE_TIMEOUT, 0 EXHAUSTED_NO_TARGET_A** across
all 33; not one frontier emptied naturally; no status ever upgraded.

**The headline finding.** The 22 roots Round 35 closed for Q2 (zero
*completable* Target A boundary) turn out to have **1,398 Target A
boundaries** under the completion-agnostic Q1 question (1,392 new, 6
re-discovered known witnesses), all independently re-verified by literal
replay (`process_rr_new_target_a_boundaries.py`: 1,398/1,398 reconfirmed).
**Zero of the 1,398 survive the capacity theorem.** This reconciles cleanly
with Round 35 rather than contradicting it: those roots are not scarce in
local Target A boundaries, they are scarce in *completable* ones — Q1
explains why Q2 closed the way it did, at a level of detail Q2 alone could
not supply. The new-boundary pipeline (exact replay -> canonicalize ->
compare vs the 18 -> CH1/CH2 -> capacity theorem -> Round 34 flow verifier
only for survivors) ran to completion and correctly never reached step 6,
since no capacity-theorem survivor occurred. Target B determination stayed
separate post-processing throughout, never assumed inside the enumeration.

**Discipline audit: 0 violations across all 33 roots** — no
`EXHAUSTED_NO_TARGET_A` without natural frontier emptying, no Q2-only prune
reason in any Q1 run's histogram.

**Why Q1 coverage is still open, honestly.** Every one of the 33 roots'
queues was still growing at cutoff (87,000-135,000 queued against
60,000-80,000 expanded) even at ~850+ nodes/second. Dropping 6 of 10
`area_a_prune_reason` sub-conditions removes most of the pruning power prior
rounds relied on; no larger node cap in this session would change the
qualitative picture. Checkpoints (`outputs/rr_target_a_checkpoints/`,
gitignored, ~130MB/root) allow exact resumption in a future round.

**Scope, unchanged bounds.** Referred to throughout as "18 **currently
known** Target A boundaries" -- never an exhaustive count. `L_6 <= 872`
verified, `L_6 >= 867` proved, `L_6 >= 872` open. Known-18 Target B not
re-searched; the 1,398 new boundaries were correctly never handed to a
Target B search either (0 capacity survivors). N=0 checkpoint, CH2, T3,
Target C, U/J branches untouched.

### Round 37 -- root-level Q2-impossibility certificate; 28 of 33 roots closed without enumeration

`src/build_rr_1398_boundary_ledger.py`, `src/analyze_rr_root_capacity_envelopes.py`,
`src/verify_rr_q1_enumerator.py`, `src/audit_rr_incomplete_roots.py` ->
`outputs/rr_1398_boundary_capacity_ledger.json`, `outputs/rr_root_capacity_envelopes.json`,
`outputs/rr_q1_q2_prune_ledger.json`, `outputs/rr_enumerator_statuses.json`,
`outputs/rr_incomplete_root_audit.json`. Six write-ups
(`RR_Q1_Q2_FORMAL_SEPARATION.md`, `RR_PRUNE_TAXONOMY.md`,
`RR_TARGET_A_ABUNDANCE_VS_COMPLETION.md`, `RR_ROOT_LEVEL_CAPACITY_ENVELOPES.md`,
`RR_INCOMPLETE_ROOT_AUDIT.md`, `RR_ENUMERATOR_CORRECTNESS.md`) and
`tests/test_rr_root_capacity_envelopes.py` (24 tests). No Target B flow
search; known-18 survivors not re-searched; no Q2-only prune used in Q1.

**Q1/Q2 formalized as predicates and Q2=>Q1 proved (손증명, one line from
the predicates' logical form).** The converse is refuted by an exact
counterexample family: all 28 long-excursion Target A roots have Q1 TRUE
(1,398 literally replayed boundaries) and Q2 FALSE (0 capacity-theorem
survivors, now proved two independent ways -- see below).

**The 1,398-boundary corpus fixed exactly.** 1,398 rows, 1,398 distinct raw
states, 1,398 distinct full literal words (an early draft hashed only the
extension and found spurious cross-root word collisions; fixed by hashing
the full path from the true initial state). Three capacity theorems
applied (coarse/Round 30, initial-phase-port/Round 31/34, true-phase-walk/
Round 33/35): **all 1,398 fail at the coarsest theorem alone** -- one
structural deficit, not several competing mechanisms. Smallest
capacity-relevant quotient: 15 distinct `(O_cap,R_cap,c(q0))` profiles.

**New hand proof: the conservation law.** M := P-5O; every macro edge has
dM=+1 (Z2 preserving or R re-entry) or dM=-4 (Z3 fresh-opening), checked by
assertion across a 3,000-node BFS sample from the true initial state.
Combined with the exact fact that an R event costs Ndef +1 (so
Ndef(boundary)=Ndef(root)+k exactly, k=1 or 2) and that no legal preserving
run exceeds length 4 (occupancy-independent), this gives a provable
ROOT-LEVEL ENVELOPE:
`ENVELOPE(root) = M(root)+5k+7+5*max(n_limit-Ndef(root)-k,0)`, an upper
bound on margin_1 for EVERY Target A boundary reachable from that root --
requiring no enumeration at all.

**A rejected refinement, found by testing the envelope against real data.**
An attempt to tighten the bound using `true_phase_walk_capacity` (Round
33's refinement) turned out UNSOUND for this purpose: at root
`long_found_142` it predicts a maximum of 3 ports, but the engine literally
stands on 4 (figures corrected in Round 38; direction unchanged) (a hexagon with 5 of 6 slots visited can still
supply the one free slot a single joint-landing needs, which the
refinement's occupancy check wrongly excludes). This does not retract
Round 33-35's own use of the function (a different, correctly-posed
question there); the occupancy-independent universal bound of 4 is used
instead, verified against all 1,398 known boundaries with **zero
violations**.

**Result: 28 of 33 roots certified Q2-impossible directly from their own
state, with zero enumeration.** This includes both `long_q1_140` and
`long_q1_178`, which found zero boundaries within Round 36's search budget
-- the envelope theorem now resolves them completely (converting 2 of the
7 Q1-INCOMPLETE ROOTS into Q2 closure; note the unit -- 7 counts roots whose Q1 search timed out, NOT roots left unresolved for Q2, which is 5). The 5 short-family
roots' envelope is **positive** (+14, k=2) -- an honest, non-forced result:
this particular theorem does not resolve them.

**7-incomplete-root audit.** Full accounting (nodes/frontier/checkpoint
size, 116-165MB each) with `interpreted_as_absence: false` on every row.
Symmetry quotient attempt on the 5 short-family roots: resource-signature
collapses all 5 to one class (expected, same P/O/Ndef counters) but raw and
canonical state hashes stay fully distinct (5 classes each) -- no
completeness-proved quotient found, none used to merge or prune, per the
round's own discipline. Distance bounds separated: proved lower bound = k
(1 or 2 macro edges); heuristic sibling-derived estimates explicitly NOT
computed or used. Continuation decisions: 2 roots (`long_q1_140/178`) ->
STRUCTURAL_ANALYSIS_FIRST (already resolved); 5 roots (`short_ell0-4`) ->
FRONTIER_TOO_LARGE (queued frontier exceeds expanded nodes by >30% at
cutoff). **No root marked RESUME_WORTHWHILE** -- simple timeout extension
is not recommended anywhere.

**Enumerator correctness re-certified.** Static source-level allowlist scan
(0 forbidden tokens in `q1_safe_prune_reason`), exhaustive runtime
assertion (10/10: all 6 Q2-only reasons raise, all 4 Q1-safe reasons pass),
and an adversarial leakage test (a corrupted variant re-introducing the
refuted capacity bound is caught immediately by the static/runtime check;
empirically it fired 55 times in a live run on `long_q1_0` but happened not
to change the found set within the tested budget -- reported honestly
rather than re-run for a favorable result, since the static/runtime check
is the actual load-bearing guarantee).

**Scope.** This is Q2 machinery applied as pure post-processing; no new
search was run to produce the 1,398-boundary results, and no Target B
search touched the known 18. `L_6 <= 872` verified, `L_6 >= 867` proved,
`L_6 >= 872` open -- unmoved. CH2, T3, Target C, U/J untouched.

### Round 38 -- capacity-helper firewall; 0 retractions; the five short roots stay open

`src/audit_rr_capacity_helpers.py`, `src/analyze_rr_short_root_envelope.py`,
`src/verify_rr_short_root_resource_model.py`, `src/build_rr_1398_boundary_ledger.py`
-> `outputs/rr_capacity_callsite_audit.json`, `outputs/rr_short_root_ledger.json`,
`outputs/rr_short_root_defect_bounds.json`, `outputs/rr_short_root_resource_results.json`.
Five write-ups (`RR_CAPACITY_HELPER_SOUNDNESS_AUDIT.md`,
`RR_ROUND37_COUNT_UNIT_CORRECTION.md`, `RR_SHORT_ROOT_ENVELOPE.md`,
`RR_SHORT_ROOT_DEFECT_THEOREM.md`, `RR_SHORT_ROOT_RESOURCE_MODEL.md`) and
`tests/test_rr_capacity_soundness.py` (28 tests). No large continuation
search; U/J, N=0, CH2, T3 untouched.

**Part A -- the soundness firewall.** Every capacity refinement counts a
port as usable only if its HEXAGON is entirely unvisited. That is exactly
right for the FULL-SEGMENT question (at Phi=0, ell=5 is forced and an ell=5
run visits all six permutations of the hexagon) and exactly wrong for the
SINGLE-LANDING question (a joint landing needs only its own target
permutation free). 20 call sites enumerated by AST parse; five helpers
classified: `c(q)` and `true_phase_walk_capacity` are
**SOUND_FOR_FULL_SEGMENT** (precondition Phi=0); the coarse segment bound,
`capacity_slack`/`orbit_capacity_bound`, and the Round 37 root envelope are
**SOUND_FOR_SINGLE_LANDING** (occupancy-independent). No helper is UNSOUND
or UNKNOWN. `assert_full_segment_context` now raises
`CapacityPreconditionError` when a full-segment helper is called at Phi != 0
-- verified live in both directions (raises at Phi=5, allows at Phi=0).

**A Round 37 misstatement corrected.** Round 37 recorded the
`long_found_142` counterexample as "predicts 2, engine achieves 3". The
exact figures, re-derived from the engine, are **predicts 3 ports, engine
achieves 4**. The undercounted port is offset 3 (phase 4, hexagon 0), whose
hexagon has popcount 5 -- the landing succeeds because the single remaining
free slot IS the target permutation. The DIRECTION of the Round 37 finding
is confirmed; only the numbers were wrong, and no Round 37 result depended
on them (the envelope rejected the helper outright and never used it).
Corrected in STATUS.md, `RR_ROOT_LEVEL_CAPACITY_ENVELOPES.md`, and the
module docstring. Grade: **corrected claim**.

**Part A.6 -- historical re-verification: 9 RETAINED, 0 RETRACTED.** All 18
currently known Target A boundaries replayed (12 short-family + 6 long).
**Phi = 0 at all 18**, so every historical use of a freshness-dependent
refinement was inside its valid domain. Of the 18, the 9 recorded
`CAPACITY_IMPOSSIBLE` were each re-proved by the freshness-INDEPENDENT
coarse segment bound, which consults no hexagon occupancy at all -- so none
is retained merely because the answer happened to match. The one genuine
scope violation found (Round 37's `bound_3` applied at boundaries with
Phi in {0,-3,-4,-8}) is **not load-bearing**: all 1,398 fail at `bound_1`
first, so `bound_3` never decided anything.

**Part B -- count-unit correction.** "7" had been used for two unrelated
objects. Corrected ledger: **33 = 28 Q2-closed + 5 Q2-unresolved**, and
separately **33 = 26 Q1-found + 7 Q1-timeout**; the 7 audited continuation
roots = **2 newly closed (long_q1_140/178) + 5 unresolved**. Both 7 and 5
are correct, of different questions. Unrelated collision flagged: the "7
remaining survivors" of Rounds 32-34 counts Target B boundary STATES, not
roots. Three invariants now enforced by test.

**Parts C-H -- the five short roots.** Ledgered in full and NOT merged
(identical resource signature `(P=2,O=2,Ndef=0)` but 5/5 distinct raw and
canonical hashes, differing Phi 1..5, orbit, phase, hub popcount 1..5). The
+14 margin decomposes exactly and identically at all five:
`-8 (M_root) + 8 (preserving) + 2 (re-entry) + 7 (terminal) + 5 (residual
R_cap) = 14`. Parts E, F and G each attempted a strengthening and each
produced **no improvement**: the entry-sensitive preserving bound gives
capacity 5 / defect 0; the best re-entry capacity is 4, so the tax stays at
Round 32's 1; a fresh opening still attains the full 5. The segment-defect
theorem therefore yields `D_min = 0 + 2x1 = 2` against a margin of 14 --
**0 of 5 roots closed**, a gap of 12. Reported as the negative result it is.

**Part I/J -- symbolic resource model.** A tiny integer-lattice relaxation
(ports, fresh/re-entry segments by capacity, `n_E2`), decided by exhaustive
enumeration since no certified ILP solver exists here. **Feasible at all
five** (120 ports required against a ceiling of 132), so no root is closed.
All five classify as **STRUCTURAL_SURVIVOR**.

**A Round 37 recommendation reversed.** Round 37 wrote "no root is
resume-worthy". That was not supported -- it rested on a frontier-growth
cost observation, not a certificate. Mathematically all five ARE
search-worthy; the cost argument is retained but now explicitly labelled
**HEURISTIC**, never used as a proof or a prune, and enforced as such by
test.

**A bug found and fixed mid-round.** The first entry-sensitive bound treated
the entry phase's own bit as a blocker, yielding `init_cap = 0` and a
nonsensical `init_defect = 5`. The walk already stands on its entry port;
fixed via `entry_already_occupied`, corrected value 5. A regression test
pins it.

**Scope.** `L_6 <= 872` verified, `L_6 >= 867` proved, `L_6 >= 872` open --
unmoved. Known-18 Target B status unchanged; N=0, CH2, T3, Target C, U/J
untouched.

## Open problems (genuinely open, not resolved by this repository)

1. **Closing the 867-872 gap for n=6.** This is the actual research
   question. It is unresolved in the literature available to this
   session, and this repository's naive search tooling is nowhere near
   capable of resolving it computationally (see baseline experiment
   above). Making real progress would require either:
   - reproducing and extending Houston/Pantone/Vatter's actual
     combinatorial lower-bound argument (a genuine, nontrivial piece of
     mathematics -- not something to re-derive casually), or
   - a search with domain-specific pruning far beyond textbook IDA*
     (symmetry reduction across the n=6 permutation group, exploitation of
     the recursive rotation-pass/deep-joint block structure, something
     closer to what Chaffin et al. needed just to close n=5).
2. Whether the specific `NR6` assumption described in the original prompt
   (that a minimal n=6 superpermutation is expressible as a
   non-repeating walk visiting all 720 permutations exactly once) is even
   true is, per that same prompt, a separate open question — not
   addressed here.
3. ~~Producing and independently verifying an actual 872-length n=6 string
   would at least pin down the upper bound side concretely; this
   repository does not have one to check.~~ **Done** — see the Upper bound
   entry at the top of this file and `tests/test_872_witness.py`. The
   upper-bound side is now pinned down concretely at 872; only the lower
   bound remains open.
4. Whether the F=1,H=0,N=2 slab's J-branch (or U-branch) can complete to a
   full walk — see "J-branch findings" above and `research/N2_CLOSURE_STRATEGY.md`.
   The overall conditional `L_6>=872` remains open regardless.

## How to run everything

```
python -m unittest discover -s tests -v   # 134 tests, ~35s
python -m src.lower_bound                 # prints the bound table
python -m src.construct                   # builds + verifies greedy witnesses n=1..6
python -m src.exact_solve                 # proves L(2), L(3) from scratch
python -m experiments.n6_search_baseline  # honest, inconclusive n=6 attempt
```
