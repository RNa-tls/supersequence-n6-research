# The Target A source universe: every root, where it came from, and whether any overlap

Round 36, Part A. Source `src/build_rr_target_a_root_universe.py` →
`outputs/rr_target_a_root_universe.json`.

## 1. Source classification (§1)

| source | count | count unit | produces |
|---|---|---|---|
| **short-family roots** | 5 | raw abandonment `ExactState` roots (one per abandonment ℓ) | 12 of the 18 currently known boundaries (3 at ℓ=0, 9 at ℓ=4; ℓ=1,2,3 produce 0) |
| **long FOUND roots** | 6 | long-excursion-prefix `ExactState` roots | the other 6 of the 18; each search stopped at its first witness |
| **long INCOMPLETE roots** | 22 | long-excursion-prefix `ExactState` roots | 0 (Round 35: Q2 exhausted at all 22, Q1 still open) |
| **abandonment ℓ classes** | 5 | — | ℓ ∈ {0,1,2,3,4}, exhaustively confirmed (§1.d) |
| **first-return L classes** | 2 | distinct L among 186 historical ℓ=4 excursion prefixes | L=7 (10 prefixes), L=8 (176 prefixes) |
| **historical capped corpus** | — | not re-derived | Rounds 19-25, documented in `RR_DEPTH_CAP_ARTIFACTS.md` |

Every entry names its exact source file and JSON key in the output; nothing
here is asserted without a code/JSON citation.

## 2. Provenance, in code terms

* **Short-family roots**: `abandonment_root(init, ell)` in
  `superperm_partial_f1_macro.py`, consumed by
  `analyze_rr_ell0_family.py::enumerate_same_component`, recorded in
  `outputs/rr_preparation_words.json['results_by_ell']`.
* **Long roots (found + incomplete)**: both come from the same 28 surviving
  prefixes in `outputs/rr_long_excursion_prefixes.json`
  (`r_budget_obstruction.surviving_indices`, reduced from 186 historical
  ℓ=4 prefixes by the R-budget obstruction — a prefix strictly before R2
  carries at most one R, 손증명). The **only** difference between the FOUND
  6 and the INCOMPLETE 22 is what `src/search_rr_long_prefix_extensions.py`
  did with each: `--stop-on-first` for the 6, node-cap-8000/depth-ceiling-12
  for the 22.

## 3. The 5-abandonment-root hand proof (§1.d)

Claimed: the abandonment ℓ can only be 0, 1, 2, 3, or 4 — no 6th value is
reachable. Verified **exhaustively against the engine**, not assumed: for
every `ell` in `0..9`, the module attempts to literally replay `ell`
rotations from the identity followed by the abandonment edge and records
whether that replay succeeds and is genuinely an abandonment.

```
ell_values_checked:                    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
ell_values_where_abandonment_is_legal: [0, 1, 2, 3, 4]
exactly_five_values:                   true
```

Grade: **exact exhaustive search**.

## 4. Count units, stated once (§2)

| unit | meaning |
|---|---|
| raw literal root | a specific literal joint-label sequence identifying one prefix in `rr_long_excursion_prefixes.json['prefixes']` |
| `ExactState` root | the state produced by literally replaying a raw literal root, compared via `stable_key()` |
| decorated continuation root | an `ExactState` root plus `r_count` (§11 of `RR_TARGET_A_UNIFIED_ENUMERATOR.md` proves nothing more is needed) |
| canonical root | the left-S6 lexicographically-least translate (`exact.canonicalize`), compared via `stable_key()` |
| symbolic first-return class | the `(L, return_exponent, symbolic_word)` triple describing an excursion's shape, independent of which literal orbit/phase it occupies |

Every table and JSON field in this round's outputs states which of these
five units it uses; none is left to be inferred from context.

## 5. Overlap audit (§3) — no merges performed

All 33 root `ExactState`s (5 short-family + 28 long-excursion, both FOUND
and INCOMPLETE) were literally replayed and compared pairwise at five
levels:

| level | long-internal collisions | short-internal collisions | cross collisions |
|---|---|---|---|
| literal state (permutation `p` only) | **18** | 0 | 0 |
| exact state (`stable_key()`) | **0** | **0** | **0** |
| left-S6 canonical | **0** | **0** | **0** |

**No merge was performed at any level.** The 18 literal-state collisions
among the long roots are expected and are *not* a merge candidate: two
prefixes can stand on the same permutation while having visited different
hexagon/orbit history, and therefore have different Target A reachability —
exactly why literal-permutation equality is the wrong level for this
predicate and `exact_state_equality` (which does collapse to zero
collisions) is the one that matters.

At the levels that matter, **the short-family and long-excursion corpora
are exactly disjoint**, confirming (rather than merely repeating) Round
35's unverified assumption of disjointness.

Decorated-continuation equality was not separately re-checked by replay: it
is a strict refinement of exact-state equality (it adds `r_count` on top),
so since no two roots share even exact-state equality, decorated equality
cannot hold either — recorded as a derived conclusion, not an additional
computation.

**Proven continuation-equivalence** (two non-identical states with provably
identical future Target-A reachability, beyond the decorated-key argument
of `RR_TARGET_A_UNIFIED_ENUMERATOR.md` §11) was not attempted at the root
level this round. Grade: **open**.

## 6. Scope limit, stated explicitly

This classification covers every root source **present in the repository
today**. It is not a proof that these are the only possible Target A root
sources in the full RR prefix space: L>8 excursions and non-RR-alphabet
prefixes were never generated at all, so a 7th source class could exist and
is not ruled out here (see `RR_BRANCH_CLOSURE_SCOPE.md`, Round 35, gaps (d)
and (e), both still open).
