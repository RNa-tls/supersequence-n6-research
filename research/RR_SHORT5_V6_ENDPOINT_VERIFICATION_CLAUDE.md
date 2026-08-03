# v6 endpoint / v7 plan: independent verification

Branch `codex/round-v6-endpoint-v7-plan` fetched directly this round.
Every claim below was checked against the actual committed files (not
restated from the prompt), including reading the two cited source files
line-by-line to confirm the provenance-loss claim independently rather
than trusting the audit's own self-report. No search run; nothing below
required any exploration beyond reading committed files and one
deterministic arithmetic/hash cross-check pass.

## 1. Remote verification

- `git fetch origin codex/round-v6-endpoint-v7-plan` succeeded.
- `git rev-parse origin/codex/round-v6-endpoint-v7-plan` =
  `479289107591ce887097550d370dd7f3785475d9` — **exact match** to the
  claimed HEAD.
- `git log --oneline`: `4792891 → 06dae7c → dfc314f → 673bd9f → ...` —
  **matches the claimed commit order exactly**
  (`673bd9f → dfc314f → 06dae7c → 4792891`).
- All 8 required files exist at this commit (`git show` succeeded for
  each; none returned an error). No Git LFS pointers found in any of
  them (`git-lfs` marker search on all 5 JSON + 3 markdown files: none
  matched) — consistent with "no LFS required."
- **`independent_ledger_verifier`: `"passed"`** is recorded inside
  `rr_short5_top8_official_ledger.json` itself; this document's own
  independent recomputation (below) reaches the same conclusion by a
  separate route (direct summation and cross-file hash comparison), not
  by re-reading that same flag.

## 2. Endpoint-count verification, independently recomputed

All of the following were recomputed directly from the raw JSON records,
not read from any summary line:

- `len(exhausted_certificates) == 6`, `len(capped_children) == 2` in
  `rr_short5_top8_official_ledger.json` — **8 total, matches**.
- Capped child IDs are exactly `short_ell2_r1_70` and `short_ell2_r1_37`
  — **matches**.
- Both capped children: `total_expansions == 55000`, `max_depth == 100`,
  `frontier_size` = 11 (`short_ell2_r1_70`) and 19 (`short_ell2_r1_37`)
  — **matches exactly**.
- `sum(additional_v6_expansions for all 8 children) == 167820` —
  **matches** the aggregate's `additional_expansions` field by direct
  summation.
- In `rr_short5_top8_continuation_verified.json`: `sum(r2_paths for all
  8 branches) == 99438` and `sum(repair_events for all 8 branches) ==
  207842` — **both match** the file's own `aggregate` block by direct
  summation, an independent check, not merely reading the aggregate.
- `component_merges == 0` and `bridge_template_matches`/
  `bridge_template_occurrences == 0` for **every one of the 8 branches
  individually**, not just at the aggregate level, checked directly in
  both `rr_short5_top8_continuation_verified.json` and
  `rr_short5_top8_continuation_analysis.json`.
- `literal_target_a_hits == 0` and `target_b_survivors == 0` — confirmed
  at the aggregate level in the ledger; no `target_a_hits` array in any
  branch's `r2` record is nonempty (`[]` in every checked branch,
  spot-checked `short_ell2_r1_70`).
- **Checkpoint SHA-256 cross-check**: every one of the 8 children's
  `checkpoint_sha256` in `rr_short5_top8_official_ledger.json` matches
  its counterpart in `rr_short5_top8_continuation_verified.json` exactly
  — an independent cross-file consistency check, not a self-report.
- **Hash-format sanity check**: every hex string matching a
  SHA-256-shaped pattern across all 5 JSON files was checked
  programmatically for exactly 64 hex characters — no anomalies found.
- **CRLF cross-platform artifact, same benign pattern as every prior
  round**: `rr_short5_top8_official_ledger.json`'s recorded
  `analysis_sha256` and `verification_sha256` do not match a raw
  byte-hash of `rr_short5_top8_continuation_analysis.json` /
  `rr_short5_top8_continuation_verified.json` on first check; both match
  exactly after the established CRLF round-trip. Not a data-integrity
  concern, confirmed by direct test rather than assumed.
- **New, deeper finding beyond what the task asked to check**: every one
  of the 8 branches carries `r1_target_component_isolated_from_hub_at_
  admission: True` with `r1_target_orbit` values `{3, 96, 58, 34, 56, 91,
  44, 56}` for `{short_ell2_r1_70, short_ell4_r1_12, short_ell1_r1_98,
  short_ell2_r1_40, short_ell3_r1_64, short_ell2_r1_37,
  short_ell2_r1_107, short_ell3_r1_56}` respectively — **this exactly
  reproduces this session's own independently hand-verified `R1`-target
  orbit numbers from three rounds ago**, an unprompted cross-validation
  between Codex's and this analyst's independent computations that
  neither round could have copied from the other's document.

## 3. Provenance-loss verdict

**Confirmed independently by reading the actual source code, not by
trusting the audit document's self-report.**

`src/search_rr_short5_top8_continuation.py` (fetched from this branch,
lines 45-49): the bootstrap path sets
`base['top8_continuation'] = {'schema': ..., 'source_checkpoint': ...,
'source_sha256': ..., 'base_expanded': ..., 'additional_budget': ...}`
directly on the loaded `base` dict — this is the *only* place this field
is ever constructed, and it is set once, before the first call to the
shared `pilot.run_branch(...)`.

`src/search_rr_short1_4_corrected_fair.py` (fetched from this branch):
`checkpoint_payload()` (lines 311-318) is a **plain function that
constructs a brand-new dict from scratch** — `{"schema": ..., "config":
..., "root": ..., "child": ..., "frontier": ..., "seen_keys": ...,
"nodes": ..., "repair_events": ..., "r2_paths": ..., "stats": ...,
"next_node": ..., "next_repair": ..., "complete_frontier_snapshot":
True}` — **`top8_continuation` does not appear anywhere in this
construction**, confirmed by reading the literal source. The write site
(`atomic_json(path, checkpoint_payload(...))`, both at the periodic
checkpoint interval and at the final write) **replaces the entire file
with this freshly-built dict**, not a merge with whatever was already on
disk.

**Verdict: the described bug is real and exactly as characterized.** The
`top8_continuation` wrapper exists only in the bootstrap-time in-memory
`base` dict and the very first on-disk write; the shared writer's first
subsequent atomic rewrite silently drops it, because the writer builds
its payload as an explicit whitelist, never as a merge with the prior
file. Every field the audit claims survives (`schema`, `config`, `root`,
`child`, `frontier`, `seen_keys`, `nodes`, `repair_events`, `r2_paths`,
`stats`, `complete_frontier_snapshot`) is **directly present, by name,**
in `checkpoint_payload`'s own returned dict — independently confirmed,
not merely repeated from the audit's own claim.

**Consequences, confirmed**:
- **Engine state, frontier, and parent DAG are intact** — they are part
  of the whitelist, hence written on every checkpoint, hence never lost.
- **Completed v6 analysis is valid** — its correctness depends only on
  the whitelisted fields (which round-trip correctly), not on the lost
  wrapper (which the analysis never reads).
- **Direct v6 resume is unsafe** — confirmed by reading the resume guard
  itself (`search_rr_short5_top8_continuation.py` lines 46-48): it
  checks `existing.get('top8_continuation',{}).get('source_sha256')`
  against a freshly-recomputed hash and raises `AssertionError` on
  mismatch — since the field is simply absent after the first rewrite,
  `.get(..., {})` returns `{}`, `.get('source_sha256')` returns `None`,
  and the guard will reliably fire (a safe failure mode, not a silent
  corruption — the code correctly refuses to resume with reconstructed
  provenance it cannot verify, rather than proceeding on an unverifiable
  assumption).
- **Prior v5 results are unaffected** — `checkpoint_payload` and its
  whitelist predate the v6 wrapper by commit (`4785cc6` before
  `06dae7c`, confirmed in the branch's own `git log`); v5 never asserted
  the wrapper fields existed, so their absence is not a regression for
  v5's own claims.

## 4. v7 replay-safety verdict

**The v6 continuation has not yet been replayed under v7** —
`rr_top8_v7_replay_manifest.json` itself records
`"status": "PLAN_ONLY_NO_SEARCH_STARTED"`, so this section assesses
whether the *plan* is well-formed and sufficient, not whether an actual
replay has already succeeded (it has not, by the plan's own account).

**Cross-file consistency, independently checked**: the `trusted_anchor`
block for each capped child in the v7 manifest is **byte-identical** (as
a parsed JSON structure) to the `trusted_immutable_anchor` block already
recorded per-child in the official ledger — an independent equality
check across two separately-produced files, not a restatement. Both
also carry a matching `v6_frontier_engine_state_sha256` /
`v6_endpoint_sha256` pair. This gives genuine confidence the plan is
targeting the actual, already-hashed v6 endpoints, not a
freshly-invented or drifted reference.

**The plan's five required validation steps** (state/decoration/
decorated-key/frontier-digest equality; legal-successor-signature
equality; literal-R2-recognizer-output equality; a separate read-only
verifier before any traversal) are, on their face, **sufficient in
principle** to catch a mis-reconstruction: any divergence between a
literal replay from the immutable v5 anchor and the recorded v6 endpoint
would show up as a digest mismatch at one of these checkpoints before
any further expansion is scheduled. The plan explicitly forbids exactly
the failure mode section 3 identified (deserializing the missing
wrapper as if it existed) and explicitly forbids starting a search this
round.

**Verdict: the plan is well-designed and, if executed as specified,
would not resume the two capped branches on unverified provenance** —
but this is a statement about the plan's soundness, not a claim that the
replay has been performed or has succeeded. No v7 replay output exists
yet to check against.

## 5. Proof significance

Distinguishing exact certificates from bounded observations, as the
prior round's document already established and this round's data now
lets be stated far more precisely:

**Exact, per-branch (if the ledger's own `NATURALLY_EXHAUSTED` label is
sound, which the provenance audit gives no reason to doubt — the label
depends only on whitelisted, correctly-persisted fields)**: for each of
the six exhausted children, the *complete* reachable space contains zero
component merges, zero bridge-template matches, and zero Target A hits.
This is not a sample — "naturally exhausted" means the frontier is
genuinely empty, so whatever was or wasn't found during that exhaustion
is a complete fact about that one child.

**A newly available, much stronger exact fact for R2-failure
specifically**: independently recomputed per-branch `r2.hierarchy_
failures` for **all 8** branches (not just the six exhausted) shows
`{"repair_not_component_merging": total}` with **no other failure key
present, in every single branch** — every one of the 99,438 total R2
literal replays across the whole top-8 family fails for the identical,
single, named reason. This is an exact, uniform, hand-verifiable fact
about R2-attempt failure across the entire family studied so far — see
section 6 (task C) for why this is *not* the same as a common
frontier-exhaustion mechanism.

**Bounded observation, but now much larger and more specific than
before**: for the two capped children, within their explored 55,010 and
55,018 repair replays respectively, `target_hex_in_hub_component == 0`
for both. This is the *precondition* this analyst's own component-bridge
template (two rounds ago) requires before a merge can even be attempted
— and it has never fired, for either capped branch, across their entire
explored (though incomplete) space. This is meaningfully stronger
evidence than "zero merges" alone: it shows the specific geometric
coincidence the bridge mechanism depends on has not been observed even
once, in either open branch, within tens of thousands of literal repair
replays each. It remains a bounded observation — the two frontiers are
still nonempty, and the precondition could still occur beyond the
explored 55,000-expansion mark.

## 6. Mathematical assessment (task 5, A-D)

**A. Is v7 deepening still the best next step?** Strengthened, yes,
*conditional on the v7 validation steps actually passing when run*. The
new per-child `target_hex_in_hub_component == 0` data (section 5) makes
the case for continuing to explore these exact two branches stronger
than it was two rounds ago, since the specific bridge precondition has
now been checked, not merely the merge outcome, across a much larger
explored space, in both open branches individually. This recommendation
is conditional: if the v7 initialization validation itself reveals a
digest mismatch, that is a correctness problem to resolve before any
further expansion, not a result to act past.

**B. Are these two branches exactly the remaining cases for the top-8
bridge conjecture?** **Yes, but only for the top-8 subset specifically.**
Preserving the distinction the task asks for: within this specific
8-child set, 6 are closed with exact zero-occurrence certificates and 2
remain open — so, restricted to this family, `short_ell2_r1_70` and
`short_ell2_r1_37` are exactly the remaining cases. This says nothing
about the other 431 children in the 439-child corpus, or the other 105
capped children outside this top-8 — the conjecture as a family-wide
claim (not just a top-8 claim) remains open well beyond these two.

**C. Do the six exhausted certificates exhibit a common hand-provable
terminal mechanism?** **Split answer, precisely scoped, per the task's
own instruction not to infer beyond what the certificates support.**
*For why every R2 attempt fails*: **yes**, exactly, hand-verifiably —
`repair_not_component_merging` is the sole recorded failure reason for
100% of R2 attempts in all 8 branches, not just the six exhausted ones.
*For why each branch's frontier emptied entirely* (the task's other
listed candidates — literal collision saturation, `F` cap, hub-touch
restriction, `R`-budget, terminal geometry loss, legal-successor
exhaustion): **not determinable from the files provided this round** —
none of the 8 branch records in `rr_short5_top8_continuation_analysis
.json` carries a prune-reason histogram for frontier-level (as opposed
to R2-attempt-level) termination; that data existed for the top-8's
prior (pre-v6) state three rounds ago but is not repeated here for the
v6 continuation specifically. No common frontier-exhaustion mechanism is
asserted.

**D. Strongest honest statement about the top-8 family.** Of the eight
children examined since three rounds ago, six now have exact,
independently-hash-verified, complete-space certificates of zero Target
A hits and zero component-bridge occurrences; every R2 attempt across
all eight (not just the closed six) fails for one identical, named,
hand-verifiable reason. The two still-open branches
(`short_ell2_r1_70`, `short_ell2_r1_37`) have each been explored to
55,000 expansions with the same pattern holding throughout, including
the specific geometric precondition a bridge would require — but both
retain a small, nonempty frontier (11 and 19 nodes), so the bridge
conjecture and the search for a new Target A boundary both remain
genuinely open, for exactly these two branches, and only within this
top-8 subset of the much larger 439-child corpus.

## What this document does not do

- Does not claim the v7 replay has been performed or has succeeded —
  only that its plan is well-formed, per section 4.
- Does not extend any of this round's findings beyond the top-8 subset
  to the wider 439-child corpus or the other 105 capped children.
- Does not infer a frontier-level common exhaustion mechanism for the
  six closed branches — the data to support one was not provided this
  round (section 6, task C).
- Does not modify or resume any Codex artifact, checkpoint, or file.
- No search run.

CLAUDE_V6_ENDPOINT_VERIFIED
