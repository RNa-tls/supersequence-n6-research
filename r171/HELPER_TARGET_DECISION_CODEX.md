# Round 171 — one helper / one target production decision

Base: `424953a3b86f3361baf4e059e2f784dd1feba6c5`, `codex/round171-joint-audit`.
No endpoint rescan, historical re-audit, new helper generation or other large target search.

## Matched 200k measurements

The old files omitted fallback/first-prune telemetry. Only these six bounded runs were repeated to fill it.
Every run deferred at 200,000 processed / 200,001 attempted visits. `(p)` counts are leaf occurrences.

| Cell | J / target | Direct fallback | Helper fallback | Direct / helper (p) leaves | New-helper essential (p) | First depth |
|---|---:|---:|---:|---:|---:|---:|
| (1,4,5,1,0,0) | 121 / 122 | 47.484991% | 26.603454% | 30,612 / 63,649 | 2,448 | 17 |
| (1,6,3,1,0,0) | 111 / 112 | 20.590624% | 20.590624% | 105,184 / 105,184 | 0 | None |
| (1,8,1,1,0,0) | 105 / 106 | 30.169305% | 30.169305% | 89,469 / 89,469 | 0 | None |

## Selection and staged execution

Selected `1|4|5|1|0|0`: the only target with positive observed counterfactual helper-prune effect.
Selection clarification: the second target has a lower **absolute** fallback but zero measured helper effect.
We prioritized measured effect before applying fallback/count/depth ranking; this is not the literal absolute-fallback-only ordering.
At a new-helper-essential leaf, the direct certified upper bound would not prune the same state.
Different pruned traversals are not identical samples; leaf-count ratios are not cost ratios.

| Cap | Actual attempted visits | Result |
|---:|---:|---|
| 500,000 | 500,001 | DEFERRED |
| 1,000,000 | 1,000,001 | DEFERRED |
| 2,000,000 | 2,000,001 | DEFERRED |
| 5,000,000 | 2,471,741 | TREE_BUILT |

Staged restarts actually consumed **5,971,744** visits, not just the final tree size.
Paired probes: 1,200,006; direct control: 2,594,635; current-round total: **9,766,385**.
This total excludes previous-round work and validation replay. It is not the reusable certificate cost.

## Economics

- Direct route: **>2,594,634** nodes; capped, not refuted.
- Helper-assisted target tree: **2,471,741** nodes.
- Genuine helper investment: **122,892** nodes.
- Reusable helper + target proof: **2,594,633** nodes.
- Certified-cost saving lower bound: **at least 2 nodes**. Exact saving and percentage remain unknown.

The control was deliberately stopped just above break-even. This proves positive amortized node benefit, not a large speedup.
Exploration/restarts are sunk measurement work, not silently charged as zero and not included in that reusable-proof comparison.

## Certification and scope

A ACCEPT / B ACCEPT; both cap 121, nodes 2,471,741; histogram mismatches 0.
Certificate: `r171/certs/extree_J_helper_decision_codex_171.txt.gz`; container SHA-256 `08f61a8bab4a0a7cfb0c1e65c590602d1baab544c66a817a245ab5d95b1d9707`.
All dependencies are genuine hash-pinned accepted predecessors, including the dual-accepted 122,892-node helper.
Two new wrapper non-interference tests passed. Previously passing regression tests were not rerun.
Independence-restricted census, with historical basis fallback disabled: 180 exposed strict rows; full tally 1,607 strict and two equality rows.
The remaining 29 J bounds remain production assumptions in that sufficiency census, not certified theorems.
**Genuine load-bearing progress: 6/35; remaining historical load-bearing dependencies: 29.**
The frozen initial J dossier is unchanged; `production_progress_codex_171.json` is the updated progress ledger.

ROUND171_HELPER_TARGET_CERTIFIED
