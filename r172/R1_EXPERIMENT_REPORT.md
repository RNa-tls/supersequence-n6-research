# Round 172: R1 token-split, bounded side-by-side experiment

**EXPERIMENTAL. R1 has NOT been adopted into the production proof system.**

Scope of this round:
- No production certificate was generated or promoted.
- No trust entry was added.
- `codex/round171-joint-audit` was not modified.
- R2 (ρ / dead-branch refinement) was not implemented.

Base: `0a9884e` (the pushed Round-171 audit checkpoint). Every pre-existing file is byte-unchanged (`git diff 0a9884e -- . ':!r172'` is empty). Everything new lives in `r172/`.

## 1. Format separation
- **`L6-EXTREE-4`.** Line 2 must be exactly `rule R1 token_split_v1 leaves=L:b,f,p S:r1`. It is part of the hashed plain text, so every container hash binds the rule.
- **Leaf tokens.**
  - `L` keeps the Round-152 meaning: (b), (f) or scalar (p) only.
  - `S:<d0>:<r>=<U>,...` (or `S:<d0>:-`) is the R1 leaf.
- **Old formats.** `L6-EXTREE-1/2/3` are verified only by the unchanged code (`extree152`, `verifyA168`, `verify168`, `routeb164`). A4 and B4 delegate those formats to it and never apply R1.

## 2–3. Theorem and accounting proof
- **Theorem.** `r172/THEOREM_R1.md` gives the full statement and proof.
  - Lemma 1: the suffix is a legal walk.
  - Lemma 2: the per-move accounting.
  - Lemma 3: `0 ≤ r_W ≤ t` and `d0 + 5r_W ≥ 0`.
  - Theorem: `n − m + 1 ≤ cap(t − r_W, d0 + 5r_W, Res)`.
  - Leaf corollary (with `≥ 0`), tree soundness, and conservativity.
- **Finite case proof.** `r172/certs/case_table_R1.json`, from `casetable172.py`:
  - 160 combinations of (kind × orbit-freshness in W/S × current × hexagon-newness in W/S);
  - 109 are impossible, each with its reason;
  - 51 are possible, and **all 51 satisfy the per-move identity**;
  - 12 rows are first re-entries into a non-current prefix orbit, each with (Δtoken, Δdeficit) = (1, 5).
- **Regression (not the proof).**
  - 0 flag mismatches between the table and the engine's own move flags;
  - 134,300 split points (6,697 with r ≥ 1) and 0 identity violations;
  - 22 of the 51 possible rows were never realised in the sample; the symbolic check alone covers them.

## 4. Two independent verifiers

| | A4 `r172/src/verifyA172.py` | B4 `r172/src/verifyB172.py` |
|---|---|---|
| derived from | `extree152` Validator + `verifyA168` streaming driver | `routeb164.TreeVerifier` (with its incremental-histogram check) + `verify168` driver |
| Live(s) | filter `r = 0..t` by `d0 + 5r ≥ 0` | closed form `r_lo = ⌈−d0/5⌉⁺ .. t` |
| annotation parsing | split-based | regex grammar |
| trusted from the file | nothing: `d0`, Live, branch U recomputed from the replayed state; annotation must equal recomputation | same |

- A4 and B4 share no R1 code.
- Branch values come only from `dep`-declared, hash-checked predecessors, the (P2) fallback and the P1 closure.
- No Round-152 value enters any R1 dependency. Round-152 values appear only in Round-171 diagnostics.

## 5. Old-rule conservativity and old-format regression
- **Proof.** THEOREM_R1 §7: `U` is monotone and `(t−r, d0+5r) ≤ (t, d0+5t)`, so every old (p) node is an R1 node.
- **Audit.** At every node closed by old (p), R1 was also evaluated:
  - **24,166,273 old-(p) leaves across all 16 experiment runs;**
  - **0 R1 failures**.
- **Old-format regression** (`r172/certs/old_format_regression.json`).
  - The production certificate `1_4_5_0_1_0_c10000000_e0` was replayed, with its trust entry removed.
  - Four paths replayed it: unchanged A (verifyA168), unchanged B (verify168), and the A4 and B4 delegation paths.
  - All four accept at exactly the recorded **7,270,523** nodes. PASSED.
- **Reproduction.** Old mode reproduces the certified production proof of `1|6|3|1|0|0` byte for byte: plain sha `819c1cd9…` equals the certified one.

## 6–7. Mutation suite (`r172/certs/mutation_suite_R1.json`): 48/48 passed

**Positive controls (10):**
- A genuinely R1-only tree is accepted by A4 and B4.
- The same tokens declared as the old format are refused by the unchanged A3 and B3.
- An old-format tree is accepted by A3, B3, A4 and B4.
- An old L-only tree re-declared as EXTREE-4 is accepted by A4 and B4.

**Text mutants (16), each rejected by both A4 and B4 for the intended reason:**
- dropped r branch;
- fabricated empty Live;
- `>0` substituted for `≥0` (the zero branch dropped);
- `r > t` branch stated;
- negative `d0+5r` branch stated;
- wrong `t−r`;
- wrong `d0`;
- stronger unsupported branch bound;
- old leaf interpreted as R1 (`S`→`L`, which gives an unjustified L leaf);
- altered predecessor container hash;
- altered predecessor plain hash;
- dep claiming a stronger cap;
- non-predecessor certificate dep;
- R1 leaf placed in EXTREE-3 (also rejected by the unchanged A3 and B3 as a bad token);
- missing rule line;
- wrong rule line.

**Search mutants (22).** Each wrong rule actually prunes. The faithful variant writes the wrong annotation; the honest variant writes the true one, so the rejection must come from the inequality.
- **Rejected by both verifiers in both variants:**
  - dropped branch;
  - fabricated empty Live;
  - `>0`;
  - wrong `t−r` (honest variant exercised on `1|6|1|0|0|0` at the root);
  - wrong `d0+5r`;
  - non-predecessor certificate;
  - stronger bound;
  - off-by-one `m−1`;
  - off-by-one `J+1`.
- **Conservative mutants.** Admitting `r > t`, or a branch with `d0+5r < 0`, adds terms to a max, so it can only make the bound **weaker**.
  - Their honest trees are sound and are **correctly accepted**.
  - The faithful `d0+5r<0` tree is rejected because it states a wrong annotation.
  - The faithful `r>t` mutant never closed a node with the extra branch present, so its tree is sound and correctly accepted.
  - A file that actually states an `r>t` branch is rejected (text layer).

## 8–10. Bounded side-by-side experiment (`r172/certs/side_by_side_R1.json`)

Both modes were run with:
- the same certified environment, re-hashed with the recorded `predecessor_set_sha256` reproduced;
- the same J;
- the same move order (`gen168._legal`);
- the same node-cap semantics.

The generator hash was `7d7453f9…` for every run. Wall-clock times in the JSON are noncanonical and were measured under concurrent load. The clean single-process timing (`timing_R1_1M.json`) is **23.7–25.6 µs/node in both modes (within ±4%)**, so R1 has no measurable per-node overhead.

### Primary target `1|6|3|0|1|0`, J = 76, environment e5 (136 cells)

| cap | old | R1 | old-(p) prunes, old run | old-(p) prunes, R1 run | R1-only prunes | dead |
|---|---|---|---|---|---|---|
| 1M | DEFERRED | DEFERRED | 57,216 | 107,463 | 95,459 | 0 |
| 10M | DEFERRED | DEFERRED | 571,392 | 456,916 | 626,284 | 0 |
| 50M | DEFERRED | DEFERRED | 1,593,318 | 2,224,833 | 2,170,211 | 0 |

- **Branch-count histogram, R1 prunes at 50M:** 1 branch: 2,079,757; 2 branches: 90,454.
- **DFS progress.** Nodes entered at depths 1–9, identical child order in both runs:

  | run | depths 1–9 |
  |---|---|
  | old @ 50M | 1,1,1,1,2,8,49,88,552 |
  | R1 @ 10M | **1,1,1,1,2,8,49,88,552** |
  | R1 @ 50M | 1,1,1,3,13,84,320,996,3,427 |

  R1 reached old's 50M frontier within 10M nodes. Neither run left the first of 7 root children.
- **Probe prediction vs measurement.** The complete failed-call probe predicted that R1 closes 9,128 of 23,253 failed calls in the first 100,001 nodes. That is exact per call, and it is **not** a tree-size prediction. Measured, R1-only prunes are 95,459 in the first 1M nodes.

### Second blocked target `2|6|4|0|0|0`, J = 95, environment e5

**Complete failed-call probe first** (`r172/certs/probe/2_6_4_0_0_0_n100000_e5.json`):
- 28,725 ub calls, of which **24,798 failed** and 17,685 were fallback-valued;
- R1 closes **19,499 (78.6%)**.

The Round-171 candidate slice (562 calls) is superseded by this probe.

| cap | old | R1 | old-(p) prunes, old run | old-(p) prunes, R1 run | R1-only prunes |
|---|---|---|---|---|---|
| 1M | DEFERRED | DEFERRED | 31,228 | 48,175 | 237,092 |
| 10M | DEFERRED | DEFERRED | 221,849 | 466,281 | 1,726,576 |
| 50M | DEFERRED | DEFERRED | 946,878 | 1,788,116 | 6,103,590 |

- **DFS progress:** the first depth with more than one node entered is 11 for old @ 50M, 7 for R1 @ 10M, and 5 for R1 @ 50M.
- **Result:** R1 goes much further, but does not complete within 50M.

### Controls

| control | old | R1 | effect |
|---|---|---|---|
| **A** `1\|6\|3\|1\|0\|0`, J = 111, e0 (easy under old) | COMPLETED 7,037,801 nodes | **COMPLETED 5,242,972 nodes (−25.5%)**, 32,958 R1 leaves | dual-verified: A4 = B4 (5,242,972 nodes; p 2,535,362, f 1,756,466, R1 32,958); old tree A3 = B3 |
| **B** `1\|8\|1\|1\|0\|0`, J = 105, e5 (probe predicted 1.9% gain) | DEFERRED @10M | DEFERRED @10M | 44,043 R1-only prunes (0.44% of nodes); no pathology; per-node time equal |
| fixture cells (dominators removed) | 15,356 / 64,502 / 409,955 / 170,787 | 10,313 / 19,102 / 50,942 / 50,971 | 1.5×–8× fewer nodes; all accepted by A4 and B4 |

## 11. R2
Not implemented. It is the next separately measurable step (old → R1 → R1+R2).

## 12. Promotion gate status

| condition | status |
|---|---|
| formal accounting proof | done (THEOREM_R1 + 51/51 case table) |
| verifier A accepts | yes: control-A R1 tree and all fixtures |
| verifier B accepts | yes: same trees |
| A/B agree | yes: nodes, histogram checks, leaf classes; generator counts match (`dual_verification_experiment.json`) |
| mutation suite | 48/48 |
| old-format regression | passed |
| real pruning benefit | yes on completed trees (−25.5% on control A; 1.5–8× on fixtures) and in DFS progress on both blocked targets |
| unexplained semantic discrepancy | none. Discrepancies found this round were all in the test harness (shell quoting, header-token scan, conservative-mutant expectations), were fixed, and are recorded |

Every gate condition is met, but R1 is **not promoted**. Promotion is the owner's decision.

## 13. First verdict
R1 is sound, dual-verified and a real improvement, but **within the bounded 50M cap it closes neither blocked target**. Both remain DEFERRED in both modes, and R1 is still inside the first of 7 root children of each. No projection to larger caps is made.

**R1_SOUND_BUT_INSUFFICIENT**
