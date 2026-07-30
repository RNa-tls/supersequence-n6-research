# The Target A backward filter: what it would need, and why it does not exist

Round 35, sections 6, 9, 11. Source
`outputs/rr_target_a_predecessor_universe.json`.

## 1. What was asked

Use the hand-proved ell=4 terminal geometry — completer target (1,4), post-C
ℓ = 0, second R joint `w3:120`, Φ = 0 — to enumerate the predecessor
boundaries immediately before Target A, and prune forward states that cannot
reach that predecessor universe.

## 2. What the known corpus actually shows

Measured across all 12 known short boundaries:

| branch | count | R2-edge ℓ | second R joint | terminal Φ |
|---|---|---|---|---|
| ell = 4 | **9** | **0** | `w3:120` | 0 |
| ell = 0 | **3** | **5** | `w3:120` | 0 |

The joint and the terminal Φ are uniform. **The R2-edge ℓ is not.** It is 0
throughout the ell=4 branch and 5 throughout the ell=0 branch, and those two
values sit at opposite ends of the Φ cost scale (`5 − ℓ` = 5 versus 0).

So there is no single predecessor class to filter against. A backward filter
built on the ell=4 normal form would be **wrong for the ell=0 branch**, and
the 22 roots span abandonment ell = 0, 1, 2, 3 — every one of them outside
the branch the normal form was proved for.

Grade: **scope correction**. `usable_as_a_forward_prune: false` is recorded
in the output rather than a filter that would silently lose boundaries.

## 3. The one sound consequence

The Φ arithmetic survives, and it is the honest content of §6:

> an R2 edge of length ℓ costs `5 − ℓ` of Φ, and a root with Φ = `ell + 1`
> can therefore only afford R2 edges with `ℓ ≥ 4 − ell`.

Tabulated per root class in `phi_budget_per_root_class`. This is already
implied by `area_a`'s own Φ prune, so it prunes nothing new — but it is the
exact statement that separates the ell=4 branch (can afford ℓ = 0) from the
rest (cannot), and it explains the branch structure that previous rounds
recorded only as an observed dichotomy.

## 4. CH2 predecessor universe (§9) — not applicable at these roots

§9 asked for the exact predecessor classes in the CH2 case: orbit 1 phase 4
as the C target, orbit 1 already opened, an earlier R1 present, R2 at or
after C.

At all 22 roots the hub hexagon is **incomplete** — popcount 1 to 5, never
6 — so **no hub completer exists yet**. C lies in the extension, not in the
prefix, and the CH1/CH2 branch is therefore a property of the extension
rather than of the root. The classifier returns `CH_none` for all 22, which
is the correct answer and not a failure to classify.

Consequence for the round's result: because the Q2 search explores **every**
extension of each root, it covers both branches. There is nothing the CH1/CH2
split would have added to the Q2 verdict, and splitting the search would have
been bookkeeping without content. See `RR_CH1_CH2_EXTENSION_SEARCH.md`.

## 5. The reachability filter (§11) — measured and vacuous

The over-approximated port graph — one macro edge, all ℓ ∈ 0..5, all four
joints, collisions dropped — is **complete**: out-degree 720 at every one of
the 720 nodes. Distance from every root endpoint to (1,4) is **1**.
Unreachability would have been a safe prune; reachability proves nothing, and
here everything is reachable. Grade: **scope correction**.
