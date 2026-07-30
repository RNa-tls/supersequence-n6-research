# R3 certificates: what is certified, and exactly how far it reaches

Round 34, sections 16–19. Source: `outputs/rr_flow_certificates.json`.

## 1. The label vocabulary actually used

The brief allowed five statuses. Three of them do not appear, and the
reasons matter more than the ones that do.

| label | count | why |
|---|---|---|
| `EXHAUSTED_NO_PATH` | **7** | the whole flow tree was explored; `truncated: false`; largest tree 1,499 nodes against a 20,000,000 cap |
| `FOUND_TARGET_B` | 0 | no continuation exists to find |
| `INCOMPLETE` | 0 (flow model) / **7** (engine variant A) | no flow-model run was truncated; the area_a-only engine variant was, and says so |
| `SAT_MODEL_UNSAT_WITH_CERTIFICATE` | **0** | **no SAT model was built.** A SAT certificate cannot be claimed for a search that was not run through a SAT encoding, so this label is left unused rather than borrowed |
| `FLOW_RELAXATION_FEASIBLE` | **0** | no relaxed flow model was solved separately; the exact model was decided directly |

## 2. The certificate content

Each of the seven certificates in `outputs/rr_flow_certificates.json`
carries, per survivor:

* the boundary state's identity — `canonical_state_hash`, `root_ell`,
  `P_core` — plus its measured invariants `Φ = 0`, `P`, `O`, `Ndef = 2`,
  `visited_count`;
* the **flow-model** verdict, node count, truncation flag, deepest segment
  count and maximum hexagons covered;
* the **engine** verdict from `macro.macro_edges` +
  `area_a_prune_reason(·, AREA_A)` + the re-derived (B+R) capacity bound,
  with node count, macro depth, `720 − max visited`, per-reason prune
  counts, and the set of surviving ℓ values;
* the **area_a-only** engine verdict, node count and truncation flag;
* an explicit `contradiction` field, `null` at all seven;
* input fingerprints: SHA-256 of the successor index and the flow results,
  plus `CODE_SHA256` and `CORE_SHA256` of the engine itself.

Grade: **independently verified UNSAT** at 7 / 7 — meaning two searches
that share no bookkeeping (one over segments and hexagon masks, one over
`ExactState` transitions) both exhausted with no completion, and neither
was truncated.

## 3. What "independent" means here, precisely

Not "a second implementation of the same model". The engine search:

* uses `exact.extend` for every step, so all legality, window-collision and
  counter arithmetic comes from the engine, not from the option corpus;
* never consults `outputs/rr_segment_options.json`, the successor index, or
  any Round 33 artefact;
* has no notion of a segment, a preserving word, a hexagon cover, or a
  capacity profile;
* recomputes the one shared ingredient — the Round 32 (B+R) capacity bound
  — from `ExactState` fields (`P`, `O`, `Ndef`, `orbit_masks`), and that
  bound is stated in the output with its own grade (**safe capacity bound**)
  so a reader can reject it separately without touching the rest.

The two prunes are provably safe but *not* identical: on a re-entry the
engine's is stricter by `used_ports − 2`. That is why the depth cross-check
agrees to ±1 rather than exactly, and it is a feature — an exact match
would have been weak evidence, since it would suggest the same computation
run twice.

## 4. Scope — stated so it cannot be over-read

**Certified.** For each of the 7 remaining known Target A boundary states,
there is **no** Target B continuation inside Area A (`F_def = 1`, `H = 0`,
`Ndef ≤ 3`). With the 11 removed in Rounds 30–32, all **18 of 18** known
Target A boundary states are now closed for Target B.

**Not certified, and not implied:**

1. **Target B is not proved impossible.** The 18 come from the Round 27
   enumeration that returned **6 FOUND, 22 INCOMPLETE** at a node cap of
   8,000. Twenty-two truncated roots is a concrete reason the set of Target
   A boundary states may be incomplete. "All known ones are closed" is the
   claim; "there are no others" is not.
2. **Nothing about `L_6 ≥ 872`.** Held unchanged, and deliberately
   restated here (§18 of the brief):
   * `L_6 ≤ 872` — **verified in this repository** (`data/verified_872
     _witness.txt`, `tests/test_872_witness.py`: 872 characters, 720
     distinct permutation windows, all of S₆, passes `src/verify.py`);
   * `L_6 ≥ 867` — **proved** (the only proved lower bound here);
   * `L_6 ≥ 872` — **open**; this is the target, and the 872 witness is an
     upper-bound witness, not a minimality proof.
   The Target B result is a statement about one branch of one search
   strategy inside Area A. It moves neither bound.
3. **Nothing about T3.** T3 remains **exact observation 15 / 15**. Round 31
   already excluded three derivation routes for it, one of them being
   "Target B capacity" — Target A does not require Target B. These
   certificates therefore cannot upgrade T3, and no such upgrade is
   claimed.
4. **Nothing about CH2** (frozen), **Target C**, the U/J branches, or the
   **N=0 checkpoint** (untouched, as instructed).
5. **Nothing about the component condition.** Target B's final component
   requirement is still uncharacterised; no survivor reached R5, so nothing
   here depends on it and nothing here says anything about it.

## 5. One prior statement re-read, not withdrawn

Round 33 recorded `NO_ORDER_FOR_THIS_COVER` for four covers and explicitly
refused to call it an R3 obstruction, noting that "only an exhaustive
enumeration of covers could turn this into an R3 obstruction, and that was
not done."

That refusal was correct, and Round 34 shows it was correct for a stronger
reason than caution: over the whole option universe the mean successor
out-degree is ~26, not 0–1, so those covers were unrepresentative by
construction. Round 34 does not reach the R3 obstruction by enumerating
covers either — it never builds a cover at all. It exhausts the *walks*
directly, which is a different and sufficient argument.

So the R3 layer is now decided for these seven states — but by the flow
model, not retroactively by Round 33's covers. Round 33's status labels
stand as written.
