# R1: the token-split suffix bound (Round 172, EXPERIMENTAL; not adopted)

Status: **experimental architecture under test**. Nothing here enters the production proof system until the promotion gate in §9 is met and the owner approves. R2 (ρ and dead-branch refinement) is **deliberately excluded**.

## 1. Setting

These are the existing definitions, restated so that the proof is self-contained.

- **Ports, orbits, hexagons.**
  - There are 720 ports: the permutations of 123456.
  - Each port lies in one orbit (144 orbits, 5 ports each; a port's position in its orbit is its *phase*) and in one hexagon (120 hexagons).
  - The move catalogue `MOVES[v]` lists, for each port v, the moves `(t, kind, cost)` with `kind ∈ {E, A, B, P, H}` (r149/PROOF.md §2.2–2.3).
- **Legal walk.** A walk `w_1 … w_n` is legal for a cell `K = (b, d, a, bb, e, h)` if all of the following hold:
  - each step is a catalogue move;
  - no port (equivalently, no orbit phase) repeats;
  - an `E` move stays in the orbit of the current port;
  - the running counts never exceed the budgets. The counts are tokens `Σc ≤ b`, A-moves `≤ a`, B-moves `≤ bb`, e-charges `≤ e`, and heavy cost `≤ h`.
- **Charging rules** (identical in every generator and verifier). A move into orbit `q` and hexagon `x`:
  - token `c = 0` if `kind = E` or `q` is untouched so far (*fresh*), else `c = 1`;
  - deficit `+4` if `q` is fresh, else `−1`;
  - e-charge `1` if `x` was already touched and `kind ∉ {A, B}`, else `0`;
  - `a += [kind = A]`, `bb += [kind = B]`, `h += cost·[kind = H]`.
- **Deficit.** The start port contributes deficit 4. By induction, the running deficit equals `Σ_{touched orbits O} (5 − |phases of O used|)`, which is **≥ 0**.
- **Capacity.** `cap(K)` is the maximum number of ports of a legal walk starting at `123456` whose **final** deficit is `≤ d`.
- **Existing proven facts used here** (r152/src/dag152.py nodes and research/RR_L6_R147_SOUND_UB.md):
  - **H.wlog.** Left S6 acts transitively on ports and preserves orbits, hexagons, move kinds and costs, so the start port is fixed without loss of generality.
  - **P1.** `K ≤ K′` componentwise implies `cap(K) ≤ cap(K′)`, because every budget is only an upper bound.
  - **P2.** `cap(K) ≤ 120 + a + bb + e`.
  - **(S), the Round-144 suffix bound.** This is the scalar (p) rule.

## 2. Prefix state

A prefix `w_1 … w_m` of a legal walk for `K = (b, dmax, amax, bmax, emax, hmax)` determines the engine state `s`:

| symbol | meaning |
|---|---|
| `m` | ports so far |
| `D` | deficit so far |
| `t` | remaining token budget, `b − Σ_{i≤m} c_i` |
| `au, bu, eu, hu` | resource use so far |
| `Res` | `(amax−au, bmax−bu, emax−eu, hmax−hu)` |
| `c0` | the orbit of `w_m` |
| `P` | the orbits touched by the prefix |
| `d*` | `dmax − D + 4 + 5t`, the scalar (p) rule's query coordinate |
| `d0` | `d* − 5t = dmax − D + 4` |

For a legal completion `W = w_1 … w_n` of `s`:

- `r_W` = the number of **distinct orbits of `P ∖ {c0}`** that `W` enters at some position `> m`.
- `S = w_m w_{m+1} … w_n` is the standalone suffix. It is **read as a walk on its own**: its start port `w_m` counts as a fresh orbit with deficit 4, and its own history is only `S`.

## 3. Definitions of the rule

```
Live(s)  = { r ∈ ℤ : 0 ≤ r ≤ t  and  d0 + 5r ≥ 0 }        (">= 0", never "> 0")
U_R1(s)  = max_{r ∈ Live(s)} U(t − r, d0 + 5r, Res)
R1 leaf  : Live(s) = ∅   or   m − 1 + U_R1(s) < J + 1
```

- **Structural admissibility.** In R1, "branch r is structurally admissible" means exactly `0 ≤ r ≤ t` and `d0 + 5r ≥ 0`. No ρ, no per-orbit feasibility and no other state enters.
- **The function `U`.** It is any function with `U ≥ cap` pointwise, built only from:
  1. genuinely certified predecessor bounds (cells whose trees were verified earlier, named by hash in the file header);
  2. the analytic fallback `120 + a + bb + e` (P2);
  3. the approved P1 closure, `U(K) = min(fallback, min{cert(K′) : K′ ≥ K certified})`.

  **No historical Round-152 value is an input.**

## 4. Lemma 1: the standalone suffix is a legal walk

Let `W` be a legal walk for `K`, split at `m`. Then `S` (relabelled so that `w_m ↦ 123456`, by H.wlog) is a legal walk. It has the same moves, kinds and costs, and the resource counts of Lemma 2.

*Proof.* Every step of `S` is a step of `W`, so it is a catalogue move. `S`'s ports are a subset of `W`'s, so they don't repeat. An `E` step of `W` stays in the orbit of its current port, which is also the current port in `S`.

Budget legality is checked at each step against `S`'s own counts, which Lemma 2 bounds by `W`'s suffix counts:

- **A-moves.** `au_S(j) = au_W(j) − au(s)`, and `W`'s check `au_W(j) < amax` gives `au_S(j) < amax − au(s)`.
- **B and H.** Identical.
- **e-charges.** An S-charge implies a W-charge (Lemma 2, row property), so `eu_S(j) ≤ eu_W(j) − eu(s)`. Whenever `S` must check `eu_S(j) < Res_e`, `W` checked `eu_W(j) < emax`.
- **Tokens.** `S`'s charges are non-negative and sum to at most `t − r_W` (Lemma 2), so every prefix sum is at most that too.

Relabelling by the S6 element that sends `w_m` to `123456` preserves all of this (H.wlog). ∎

## 5. Lemma 2: per-move accounting (finite case proof)

For each suffix move (step `j → j+1` with `j ≥ m`), compare the charges computed in `W` (history `w_1..w_j`) with those computed in `S` (history `w_m..w_j`).

**Case variables.** A move is determined, for accounting, by:

| variable | values |
|---|---|
| kind | 5 values |
| orbit fresh in `W` / in `S` | a pair |
| target orbit is the current orbit | yes / no |
| hexagon new in `W` / in `S` | a pair |

That gives `5 × 8 × 4 = 160` combinations. They are all enumerated in `r172/certs/case_table_R1.json`, generated and checked by `r172/src/casetable172.py`.

**109 combinations are impossible.**
- `S`'s history is a subset of `W`'s. So "fresh in `W`, not fresh in `S`" and "new hexagon in `W`, old in `S`" cannot happen.
- The current orbit is always touched in `S`.
- An `E` move always targets the current orbit.

**51 combinations are possible.** For each one the table records the six charges in `W` and in `S` and checks the per-move identity:

| row type | tokens `c_W − c_S` | deficit `Δdef_S − Δdef_W` | e-charge `e_W − e_S` | a, bb, h |
|---|---|---|---|---|
| first entry of the suffix into an orbit of `P ∖ {c0}` (12 rows, all non-E) | **1** | **5** | ∈ {0, 1} | equal |
| fresh-orbit entry (untouched by `W`) | 0 | 0 | ∈ {0, 1} | equal |
| current-orbit continuation | 0 | 0 | ∈ {0, 1} | equal |
| return to an orbit already touched in the suffix (incl. `c0`, and repeated re-entry of a prefix orbit) | 0 | 0 | ∈ {0, 1} | equal |

All 51 rows satisfy the identity (`all_possible_rows_satisfy_identity: true`).

**Counting first entries.** Each orbit of `P ∖ {c0}` entered after `m` is entered for the *first* time in the suffix exactly once, and that move is in the first-entry row type. Every later entry into it is a "return" row. So the number of first-entry moves is exactly `r_W`.

Summing the rows over the suffix, with `S`'s start (`tokens 0, deficit 4, e 0`) and `W`'s state at `m` (`D`, and `t` tokens left):

```
(I1)  final_S  = 4 + Σ Δdef_S = 4 + (final_W − D) + 5 r_W
(I2)  tokens_S = Σ c_S = (Σ_{suffix} c_W) − r_W
(I3)  e_S ≤ Σ_{suffix} e_W ;   a, bb, h of S = suffix a, bb, h of W.        ∎
```

**Regression (not part of the proof).** `casetable172.py` also:
- classifies every suffix move of random legal walks into a row, and checks the engine's own flags against it (0 mismatches);
- re-runs the split-point identity check (134,300 split points, 6,697 with `r ≥ 1`, 0 violations);
- reports rows never realised by the sample (22 of 51; they are covered only by the symbolic check).

The round-171 figure of 181,240 split points came from a different random seed and sample.

## 6. Lemma 3: bounds on r_W

For every legal completion `W` of `s` with `final_W ≤ dmax`:

- **(a) `0 ≤ r_W ≤ t`.** `r_W ≥ 0` because it counts something. By (I2), `r_W = Σ_{suffix} c_W − tokens_S`. Here `tokens_S ≥ 0`, and `Σ_{suffix} c_W ≤ t` because `W` never exceeds its token budget.
- **(b) `d0 + 5 r_W ≥ 0`.** By (I1), `final_S = final_W − D + 4 + 5r_W ≤ dmax − D + 4 + 5r_W = d0 + 5r_W`. Also `final_S ≥ 0`, since it is a deficit (§1).

So `r_W ∈ Live(s)`. ∎

## 7. Theorem (token-split suffix bound) and leaf soundness

**Theorem.** Let `W` be any legal walk for `K` with final deficit `≤ dmax` that extends the prefix state `s`. Then `r_W ∈ Live(s)`, and

```
n − m + 1  ≤  cap(t − r_W,  d0 + 5 r_W,  Res(s)).
```

*Proof.*
1. By Lemmas 1–2, relabelled `S` is a legal walk from `123456`.
2. It uses at most `t − r_W` tokens (I2), since `Σ_{suffix} c_W ≤ t`.
3. Its final deficit is at most `d0 + 5r_W` (Lemma 3b).
4. Its a/bb/h/e use is at most `Res(s)` (I3).
5. So `S` is admissible in the cell `(t − r_W, d0 + 5r_W, Res)`, and its port count `n − m + 1` is at most that cell's capacity. ∎

**Corollary (leaf soundness).** Let `U ≥ cap` pointwise.
- If `Live(s) = ∅`, no legal walk with final deficit `≤ dmax` extends `s`, by Lemma 3.
- Otherwise every such walk has `n ≤ m − 1 + U(t − r_W, d0 + 5r_W, Res) ≤ m − 1 + U_R1(s)`.

In both cases, an R1 leaf (`Live = ∅`, or `m − 1 + U_R1 < J + 1`) has no extension reaching `J + 1` ports. ∎

**Tree soundness.** An `L6-EXTREE-4` tree is a finite case analysis: every internal node lists exactly its legal children, and every leaf is justified by (b), (f), scalar (p) or R1. So, by the Round-152 induction extended with this leaf type, a valid tree for `(K, J)` proves `cap(K) ≤ J`.

### Relation to the old (p) rule and conservativity

- **Old rule as a relaxation.** The old rule bounds `S` in the single cell `(t, d0 + 5t, Res)`. This is the relaxation `r_W ≤ t` applied to the deficit coordinate **and** `r_W ≥ 0` applied to the token coordinate: the same `r_W` is counted in two incompatible ways.
- **Monotonicity of `U`.** For `K1 ≤ K2`, `{K′ ≥ K2} ⊆ {K′ ≥ K1}`, and the fallback depends only on `a, bb, e`. So `U` is monotone (RR_L6_R147_SOUND_UB §3).
- **Comparison.** For every `r ∈ Live(s)`, `(t − r, d0 + 5r, Res) ≤ (t, d0 + 5t, Res)`. So `U_R1(s) ≤ U(t, d0 + 5t, Res)`.
- **Consequence.** **Every node closed by the old (p) rule is also closed by R1.** R1 never weakens a leaf.
- **Format level.** An `L` leaf in `L6-EXTREE-4` keeps its old meaning ((b)/(f)/(p) only), and `L6-EXTREE-1/2/3` files are verified by the unchanged Round-152/164/168 code. Old certificates and trust entries are unaffected.

## 8. Proof-object format and verifier obligations

```
L6-EXTREE-4
rule R1 token_split_v1 leaves=L:b,f,p S:r1        <- hashed header declaration (line 2, exact)
ref / dep lines exactly as L6-EXTREE-3
tree <cell> <J>
<preorder tokens: N<k> | L | S:<d0>:<r>=<U>,... | S:<d0>:->
```

The `S` annotation is a **claim**. Each verifier must do all of the following:

1. Recompute `(t, D, Res)` by replaying the path from the root. No stored `d0`, Live set, branch value or ρ is used.
2. Recompute `d0`, `Live(s)` (with `≥ 0`) and every `U(t − r, d0 + 5r, Res)`, using only `dep`-declared predecessors, the fallback and the P1 closure.
3. Require the annotation to equal the recomputation exactly.
4. Accept iff `Live = ∅` or `m − 1 + U_R1 < J + 1`.
5. Never apply R1 to an `L` token. Reject `S` tokens outside `L6-EXTREE-4`.

Verifier A (`r172/src/verifyA172.py`, extree152-derived) and verifier B (`r172/src/verifyB172.py`, `routeb164.TreeVerifier`-derived) implement these steps with no shared R1 code:
- **A** filters `r = 0..t` by `d0 + 5r ≥ 0`.
- **B** uses the closed form `r_lo = ⌈−d0/5⌉⁺` and a regex grammar.

## 9. Promotion gate (from the approval)

R1 may enter production only if **all** of the following hold:
- the formal accounting proof (§4–7 and the case table);
- A accepts;
- B accepts;
- A and B agree on the result, on per-batch node counts and on leaf-class counts;
- the mutation suite passes;
- the old-format regression passes;
- the bounded side-by-side experiment shows real pruning benefit;
- no unexplained semantic discrepancy remains.

Performance improvement alone is not sufficient.
