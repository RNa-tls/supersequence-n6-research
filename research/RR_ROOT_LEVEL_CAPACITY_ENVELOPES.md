# Root-level capacity envelopes: proving Q2-impossibility without enumeration

Round 37, Parts A, B, sections 5, 6, 7, 10. Source
`src/analyze_rr_root_capacity_envelopes.py` →
`outputs/rr_root_capacity_envelopes.json`.

## 1. Goal

Round 36 found 1,398 Target A boundaries and showed every one fails the
coarsest capacity theorem. Goal A of this round is to compress that
boundary-by-boundary result into a root/class-level theorem. This module
delivers exactly that: **a provable upper bound on the achievable capacity
margin, computed from a root's own state alone, requiring no enumeration
of any boundary.**

## 2. The conservation law (§7)

Every macro edge in the RR alphabet is exactly one of three kinds, and each
has an exact, fixed effect on `M := P - 5·O`:

| kind | `dP` | `dO` | `dM` |
|---|---|---|---|
| `Z2` (orbit-preserving) | +1 | 0 | **+1** |
| `Z3` (fresh orbit) | +1 | +1 | **-4** |
| `R` (re-entry) | +1 | 0 | **+1** |

Checked directly against the engine across a 3,000-node BFS sample from the
true initial state (not assumed): every occurrence of each kind shows the
identical `(dP, dO)` pair, confirmed by assertion inside
`conservation_law_check()`. `Z2abandon` (weight-2 abandonment) and `other`
(everything outside the RR alphabet) are excluded from the theorem — they
never occur inside an extension already past its abandonment.

## 3. The algebraic identity

With `R_cap := max(n_limit - Ndef, 0)` and `TARGET_O=25`, `TARGET_P=121`
(so `5·TARGET_O - TARGET_P + 3 = 7` exactly):

```
margin_1(state) := bound_1(state) - (B(state)+1)
                 = 5·(O_cap+R_cap)+4 - (TARGET_P-P+1)
                 = M(state) + 7 + 5·R_cap(state)
```

a pure algebraic rearrangement, not an approximation.

## 4. The envelope theorem

A Target A boundary reachable from root `r` needs exactly `k` more R
events: `k=1` if `r` already carries one R in its prefix (the 28
long-excursion roots), `k=2` for a bare abandonment root that has not yet
placed R1 (the 5 short-family roots).

Each R event costs `Ndef` exactly `+1` (an "R" edge by definition targets an
already-opened orbit, so `dO=0`, giving `dNdef = dS+dF-dO = 1+0-0 = +1`),
and no other edge type changes `Ndef`. So:

```
Ndef(boundary) = Ndef(root) + k                          exactly
R_cap(boundary) = max(n_limit - Ndef(root) - k, 0)        exactly
```

Between R events, the walk runs any number of `Z2`/`Z3` edges. A legal
preserving run has length **at most 4** — an occupancy-*independent*
structural fact (no legal preserving word of length ≥5 exists, established
since Round 33) — so within any one segment `n_Z2 ≤ 4` regardless of the
state's occupancy, and using `Z3` only ever worsens `dM` (+1 vs -4), so the
margin-maximizing strategy never opens a fresh orbit. With `k` segments
(one ending at each required R event):

```
max(ΔM_total) ≤ 4k + k = 5k

ENVELOPE(root) := M(root) + 5k + 7 + 5·max(n_limit - Ndef(root) - k, 0)
```

**`margin_1(boundary) ≤ ENVELOPE(root)` for every Target A boundary
reachable from `r` — proved without enumerating any of them.**

## 5. A rejected refinement, and why

An earlier draft tried to tighten the "4 per segment" term using
`true_phase_walk_capacity` (Round 33's occupancy-aware initial-segment
refinement). **This is unsound for the present purpose**, and the
counterexample is exact: at root `long_found_142`, `true_phase_walk_
capacity` predicts a maximum of **3 ports**, but the engine literally
stands on **4**. *(Figures corrected in Round 38; this document originally
said 2 vs 3. The direction of the finding — the helper undercounts — is
unchanged, and no result here depended on the numbers: the envelope
rejected the helper outright. See `RR_CAPACITY_HELPER_SOUNDNESS_AUDIT.md`.)* The function requires the *landing* hexagon of every
step — including the last one before a transition — to be completely
fresh; but only the *starting* hexagon of each step's rotation run needs
that. The final landing permutation just needs its own single slot free,
and a hexagon with 5 of 6 slots already visited can still supply exactly
that free slot (verified directly: the third macro edge lands in a hexagon
of popcount 5, succeeding because the specific target port was the one
free slot).

This does **not** retract Round 33-35's own use of the function — there it
measures hexagons completable toward full coverage, a different, correctly
-posed question the counterexample does not touch. It is recorded here as a
genuine, newly found scope caveat: **`true_phase_walk_capacity` is not a
valid upper bound on "legal steps before some other event," only on
"hexagons fully completable."** The occupancy-independent universal bound
of 4 is used instead, and is verified sound (below).

## 6. Verification against all 1,398 known boundaries

`ENVELOPE(root)` was computed for every one of the 33 roots and checked
against the maximum `margin_1` actually observed among that root's found
boundaries (where any exist):

**Zero violations across all 26 roots with observed boundaries.** Every
`max_margin_1_observed ≤ ENVELOPE(root)`, exactly as the theorem requires.

## 7. The certificate itself

| root class | `k` | `Ndef(root)` | `ENVELOPE` | certified Q2-impossible? |
|---|---|---|---|---|
| 28 long-excursion roots (6 found + 22 incomplete) | 1 | 1 | **-13 or -4** | **YES, all 28** |
| 5 short-family roots | 2 | 0 | **+14** | inconclusive |

**28 of 33 roots are now certified Q2-impossible directly from their own
state — no search, no enumeration, no dependence on the 1,398 found
boundaries (which merely corroborate it).** This includes the 2 roots
(`long_q1_140`, `long_q1_178`) that found zero boundaries within the Round
36 search budget: the envelope theorem resolves them completely, converting
2 of the 7 previously-`INCOMPLETE` roots into genuine `EXHAUSTED_NO_TARGET
_A`-for-Q2 certificates.

The 5 short-family roots' envelope is **positive** (+14), meaning this
particular theorem does not resolve them — an honest result, not a gap
papered over. See `RR_INCOMPLETE_ROOT_AUDIT.md` for what that does and does
not imply.

## 8. Section 6: prefix monotonicity, stated precisely

The brief asked for a safe upper bound `M_max(s)` on completion margin at
any search prefix `s`, with the explicit caution that this is a **Q2
prune, not a Q1 prune**. `ENVELOPE(root)` *is* exactly this quantity,
evaluated at the root rather than at an arbitrary prefix — and the same
derivation applies unchanged at any intermediate prefix reached during a
Q2-mode search (replace "root" with "current state," "k" with "R events
still needed from here"). It is not registered as a Q1 prune anywhere in
this round's code, and `q1_forbidden_prune_check` would reject it if it
were (its very construction uses `TARGET_P`/`TARGET_O`/`n_limit`
completion-scoped quantities).

## 9. What this does not say

The envelope's soundness rests on the conservation law and the
occupancy-independent segment bound — both proven exactly. It says nothing
about `L_6`, nothing about the 5 short-family roots' true status, and
nothing about Target B for the known 18 (untouched this round). It also
does not claim the envelope is *tight* — only that it is a valid upper
bound; the true maximum achievable margin at the 28 certified roots may be
(and empirically is) substantially below the envelope value.
