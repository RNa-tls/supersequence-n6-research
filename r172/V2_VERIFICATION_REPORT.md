# Round 172 V2: hardening the R1 proof (EXPERIMENTAL; nothing promoted)

**Task.** Verify, on my own initiative, what the first R1 round did not test.

**Scope.**
- Nothing outside `r172/` was modified.
- No trust entry was added.
- `codex/round171-joint-audit` was not touched.
- Every check uses only the model definitions and hash-checked genuine predecessors, plus the proven prunes (P2), (f) and P1. No historical capacity is an input anywhere; Round-152 values appear only as noted diagnostics.

## V2.1 Exhaustive check of the theorem (`src/exhaust172.py`, `certs/v2/exhaustive_*.json`)

Method:
1. Enumerate **every** legal walk from 123456 with final deficit ≤ dmax. The only pruning is the proven (f) prune, which never removes a completable walk.
2. At **every split point of every such walk**, check T1–T7:
   - T1: `0 ≤ r_W ≤ t`.
   - T2: `0 ≤ final_S ≤ d0 + 5r_W`.
   - T3: the identities I1, I2, I3.
   - T4: `S` re-checked step by step as a legal walk under the branch budgets `(t − r_W, Res)`.
   - T5: the concrete S6 relabelling `g(w_m) = 123456`. The image must start at port 0, keep the same move kind and cost at every step, preserve the same-orbit and same-hexagon relation on all pairs, and have identical accounting. This makes H.wlog concrete.
   - T6: `|S| ≤ cap_exact(branch)`.
   - T7: the R1 leaf inequality with exact capacities.
3. Exact capacities come from the same enumeration.

Results:

| measure | value |
|---|---|
| cells fully enumerated | 45 (b = 1, 2, 3; a, bb, e, h budgets up to (2, 1, 1, 2); exact caps 35–75) |
| valid walks | 491,234 |
| split points | **15,049,715** (4,833,484 with r ≥ 1) |
| T5 relabel replays | 4,380,230 (every split point in cells with ≤ 20k walks; every 50th otherwise) |
| T6 / T7 checked | 9,360,303 / 8,946,476 (the rest skipped only where the branch capacity was not exactly computable within the limit; every skip is counted) |
| **failures** | **0** |

Not completed within 30M enumeration nodes:
- `1|1|0|0|0|2`
- `1|2|0|0|0|2`
- `1|3|0|0|0|2`
- `1|3|2|1|1|0`
- `1|4|0|0|0|1`
- `1|4|0|0|0|2`
- `1|4|2|1|1|0`
- `2|1|0|0|0|1`
- `2|2|0|0|0|1`

**Independent consistency.** Two enumerated values match facts established elsewhere:
- `(0,10,0,0,0,0)` needed exactly **13,780,945** nodes, the count Round 144 recorded independently.
- The exact capacities `2|2|0|0|0|0 = 63` and `1|2|0|0|0|0 = 48` equal the Round-171 witnesses.

## V2.2 End-to-end check against exact capacities (`src/e2e172.py`, `certs/v2/e2e_exact.json`)

For every cell with an exact capacity `c` (b ≥ 1), the test uses two environments:
- **E1:** genuine e5 predecessors, dominators removed.
- **E2:** an adversarial table of *all* exact capacities, the tightest U possible.

In each environment:
- old and R1 must **complete at J = c**;
- old and R1 must **find a walk at J = c−1**, i.e. never prove a false bound.

The E1 R1 tree is written and dual-verified.

**Result: 62 cells (b=1: 50, b=2: 10, b=3: 2; exact caps 35–75), 0 problems.**

| check | outcome |
|---|---|
| J = c−1: old and R1, E1 and E2 | **248 / 248 found a walk** (no false bound) |
| J = c, R1 | 60 completed, 2 hit the 5M-node test cap (`2|2|0|0|1|0`, `3|1|0|0|0|0`) |
| J = c, old | 55 completed, 7 hit the cap (R1 completes in 5 cells where old does not) |
| E1 R1 trees | 60 / 60 accepted by both A4 and B4, identical nodes and leaf classes, generator counts match |
| dead-first trees | 60 / 60 dual-accepted, **9,671,137 dead leaves**, **0 Lemma-4 violations** |

## V2.3 The dead-leaf path and Lemma 4
- **Lemma 4** (THEOREM_R1 §7): `Live(s) = ∅` ⇒ (f) closes `s`. That is why the standard generator never produced a dead leaf, and why the verifiers' dead path had never run.
- **Exercising the dead path.** A test prover that writes `S:<d0>:-` *before* trying (f) produced trees with **9,671,137 dead leaves** over 60 cells.
- **Result.** All 60 trees are accepted by both A4 and B4, with identical leaf classes. There were **0 Lemma-4 violations** over every node visited.

## V2.4 Catalogue agreement between A and B
- The catalogues from `checker152` (A) and `routeb164` (B) are built independently.
- For all 720 ports they have identical child order and identical HEX, ORB and PHASE.

## V2.5 Larger bounded cap on the primary target (measured, not extrapolated)

`1|6|3|0|1|0`, J = 76, e5 environment (136 genuine predecessors), same move order:

| cap | mode | status | visited nodes | old-(p) leaves | R1-only leaves |
|---|---|---|---|---|---|
| 200M | R1 | **COMPLETED** | **72,657,745** | 3,766,212 | 2,830,368 |
| 200M | old | **COMPLETED** | **173,815,277** | 7,533,778 | 0 |

- **Ratio.** R1/old = **0.418**, i.e. 58.2% fewer nodes.
- **Dual verification of both trees.**
  - The **R1 tree** (EXTREE-4, plain sha `45880468…`) is accepted by A4 and B4. Both report 72,657,745 nodes (B's histogram checks equal that count) and identical leaf classes: R1 2,830,368, p 3,766,212, f 52,414,283. Both match the generator.
  - The **old tree** (EXTREE-3, plain sha `7da9f880…`) is accepted by the **unchanged** Round-168 verifiers A (`verifyA168`/`extree152`) and B (`verify168`/`routeb164.TreeVerifier`, trust set up exactly as in Round 171). Both report 173,815,277 nodes (histogram checks equal), with 136 declared dependencies.
- **Conservativity audit on these runs.** 3,766,212 + 7,533,778 old-(p) leaves, all closed by R1: 0 failures.
- **Consequence.** `cap(1|6|3|0|1|0) ≤ 76` now has a dual-verified certificate **in the existing production architecture**. The 50M DEFERRED results were a cap limit. Direct escalation to about 174M nodes suffices; R1 is a 2.4× accelerator, not a necessity, for this target. (Diagnostic only: the historical Round-152 upper value is 74, below J = 76, so the two are consistent.)
- **`2|6|4|0|0|0`.** R1 at 200M is **DEFERRED** (27,938,876 R1-only leaves). Its frontier is still in the first of 7 root children (depth-4 profile 1,1,1,4). Old was not run at 200M.

## V2.6 Harness errors found and fixed (none in the verifiers or the rule)
- Twice, `pkill`/`pgrep -f` matched my own shell command line and killed it. No results were lost; the affected steps were re-run.
- The first `e2e172` pass read only one file-name pattern, so it missed pass-2 capacities. It was fixed and extended.
- The single-cell rerun of `3|1|0|0|0|0` lost its printed output but wrote its result file, which is included.

## Status
Nothing is promoted. Adopting either certificate for `1|6|3|0|1|0` is the owner's decision:
- the EXTREE-3 old-rule tree, which needs no architecture change;
- the EXTREE-4 R1 tree, which needs R1 adoption.
