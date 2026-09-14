# Round 150 final report

**ROUND150_FEAS_FULLY_CERTIFIED — success route A.**

This means the specified `feas()` condition has a universal hand proof over
the full admissible single-chain state domain, plus independent implementation
and finite falsification checks. It does not mean a proof-assistant formalization,
a full replay of every historical capacity run, or disappearance of all hand
lemmas in the n=6 proof. Other R148/R149 premises are accepted as requested.

## 1–5. Source, state, clauses, proofs and directions

The exact five C bodies and their definition/call lines are exported in
`certs/source_conformance.json`: production A and B in `r147/src`, and three
historical chain/marked variants under `src/`. The Python R149 `feas_tot` is a
corroborative restatement, not an additional independent implementation.

`PROOF.md` defines the completion problem from ports, orbit partition and
charging rules. There is one rejection condition, **tot > DMAX**. All other
branches construct a lower bound; their individual directions are listed in
`certs/clauses_and_monotonicity.json`.

For old noncurrent orbit deficits u_q and remaining tokens k,

    L = min_{|S|<=k} sum_{q not in S} u_q
      = max_{lambda=0..4} [sum_q min(u_q,lambda) - k*lambda].

Every completion has D_final>=L: changing a previously opened noncurrent
orbit requires its own first token-spending re-entry. At most k such orbits
can be touched. Giving each touched orbit unlimited free filling is an
optimistic relaxation. The argument covers all phase masks, q0/repeated
returns, all dirty/ordinary/heavy categories and arbitrary chain lengths.
Free restarts at multiple endpoints are explicitly excluded from a single
query; cycle opening and splitting allocate separate queries beforehand.

## 6. Monotonicity

All six budgets are upper budgets. Increasing tok or d cannot turn acceptance
into rejection; feas does not read a, bb, e or h. The true completion set is
also componentwise monotone in all six. Current deficit itself need not be
monotone, and no such premise is used. Exact-label suffix models from other
rounds must not be substituted for this at-most model.

## 7–9. Arbitrary states, counterexamples and third algorithm

* Compiled conformance: 179,850 cases across all five C functions, zero
  disagreement with independent dual-certificate/subset-DP calculations.
* Arbitrary bitmask DP: 104,448 states, covering every mask/current pair in
  two stated finite phase graphs. No production feas call, no cap. All
  146,784 rejected state/deficit-budget pairs are truly infeasible there.
* n6 completed-orbit DP: 16 exact small cells, 16 fresh production matches,
  zero UNKNOWN. Twelve were already in the archive; four were newly compared.
* Smallest actual production counterexample: none found. Mutant witnesses
  are explicitly abstract-model violations, not alleged literal covers.

The finite models alone do not prove the lemma. The universal first-entry
injection/dual argument does. The completed-orbit DP uses the independent
b=d=0 forced-full-run argument, not the production feasibility routine.

## 10. t<=4 and a row-unit correction

Recomputed maxima `(b,d,a,bb,e,h)=(4,20,20,3,3,4)` lie inside declared limits
`(5,40,24,24,24,6)`. The lemma itself does not depend on t. The 905 explicit
load-bearing cells have maxima `(3,18,12,2,2,3)`.

Counting units matter: there are **1,609 coordinate groups**, but **2,178
s-expanded variants** over t=0..4. Per t, groups are 1/14/85/353/1156; variants
are 1/15/100/453/1609. R149's phrase "1,609 including s" conflated these units.
The independently recomputed budget maxima agree and no row is removed by
this correction. No capacity frontier was reconstructed.

## 11. Mutations and a visible verifier correction

Eighteen targeted feasibility mutations: 12 unsafe strengthenings detected;
6 provable weakenings retain soundness and are correctly not called failures.
This does not claim that every imaginable mutation was tested.

The unchanged historical master mutation suite reproduced **17/18**, not
18/18: `10_source_hash_changed` actually changes the *phase-2 executable hash*,
whose old binary is optional in the committed clean checkout. The old master
does not compare that archival field when the binary is absent.

The new, separate `master150.py` adds one explicit provenance relation:
that field must equal the producer SHA stored in all 1,101 capacity records.
No production solver or legacy verifier file is edited. With this added check,
the same unchanged 18 mutations are detected **18/18**, and all modified
private-clean-checkout input artifacts are restored. Both before and after
results are preserved; the escape is not silently rewritten as an earlier pass.
This check detects inconsistent provenance, not the authenticity of an absent
binary. The committed rebuilt binary is independently byte-checked by the
existing master, and the accepted reproduction certificate links it to the
old capacities.

## 12–14. Trusted base, DAG, master and regression

The `feas()` implementation is justified by a universal audited hand theorem.
`certificate150.py` additionally verifies a rejection from one lambda and raw
masks without trusting the production greedy algorithm. It is a prospective
API; old runs did not export every prune certificate, so route B is not claimed.

The extended DAG explicitly adds H.feas to the chain/marked capacity ancestors.
Remaining PURE_HAND_PROOF nodes on L6=872 are **H.models and H.feas**. No
forbidden/retracted node occurs on the accepted conclusion paths. Neither
node is relabelled computational merely because examples passed.

Windows CRLF checkout conversion first caused C12 source-SHA failure. A separate
LF, byte-exact checkout of the same commit passed all 18 original master checks;
the new nineteenth provenance check also passes. No hash gate was weakened.
The fresh seven-test regression suite passes, all audit Python compiles, and
the 18 master mutations pass with the new checker. The clean-checkout exercise
replays artifact verification, NOT the billion-node historical enumerations.

## 15–16. Delivery and remaining risk

Branch: `codex/round150-feas-audit`, parent
`195d11bdbfa68666b118010232258686195893fc`.
The ending commit and remote SHA are reported in the final response; Git
records them without placing a circular commit hash inside its own content.
Only `r150/` audit artifacts are added. Earlier research, checkpoint and
solver files remain unchanged. Generated executable/pyc build products are
not proof inputs and need not be pushed; their as-run hashes are recorded.

Under the accepted R148/R149 proof dependencies, this discharges the specified
last feasibility-pruning obligation and retains L6=872. The cheapest remaining
way the broader theorem could be wrong is a mistake in an accepted extraction
or charging premise, or a state-maintenance implementation error outside this
function. Those are not made impossible by A/B agreement. This audit reports
neither such a counterexample nor a claim that ordinary hand proofs are formal
machine proofs.

## Reproduction

Use a fresh audit output directory/check-out: scripts refuse overwriting their
prior result files. Preserve committed `r150/certs` before rerunning generators.
Run `audit_feas150.py --compiler <zig.exe>`, `blocks150.py`,
`compare_blocks150.py --compiler <zig.exe>`, `coverage150.py`; then the seven
tests with `python -m unittest discover -s r150/src -p test_feas150.py`.
For master verification set `R150_MASTER_ROOT` to an LF checkout of the input
commit and run `master150.py`. `replay_master_mutations150.py <clean-checkout>`
uses that disposable checkout and restores its mutated inputs. Finally run
`finalize150.py`; `--refresh` only refreshes this round's generated summary/DAG.

ROUND150_FEAS_FULLY_CERTIFIED
