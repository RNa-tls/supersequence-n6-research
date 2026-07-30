# Round 38 — Round 35 Target-A traversal versus Round 37 root envelope

**Audit commit:** `0dcde297a3d87686e0a6bb8dd0bbfceabca02d84`
**Local verification commit:** recorded with the accompanying Round-38 files.
**Status:** the 22 Round-35 roots are superseded **only for the Q2 question**. Their preserved Q1 checkpoints remain valid historical partial searches.

## Unit of comparison and method

Names were not used as identity evidence.  For every Round-35 root in
`outputs/rr_target_a_22_root_ledger.json`, the audit independently replayed

1. its abandonment rotation `ell`;
2. the literal `w2:10` abandonment;
3. its entire literal long-excursion joint word.

It then compared the resulting exact `stable_key()` SHA-256 with the Round-35
`post_return_state_hash`, as well as the prefix index, `ell`, and literal
word.  All 22 comparisons match.  The row-level evidence is in
`outputs/rr_round35_round37_root_mapping.json`.

In particular:

| Round 35 root | Round 37 root | exact replay | envelope | decision |
|---|---|---:|---:|---|
| `R27-prefix-6` | `long_q1_6` | matching SHA-256 | −4 | `LONG_Q2_IMPOSSIBLE` |

`R27-prefix-6`'s incomplete pilot checkpoint must therefore be retained but
must not be resumed to answer Q2.  It is not evidence that the Q1 traversal
was complete or empty.

## Q1 and Q2 are different predicates

For a root `r`, with `Reach(r)` the exact RR-alphabet reachability relation:

```text
Q1(r) := ∃b ∈ Reach(r): TargetA(b)
Q2(r) := ∃b ∈ Reach(r): TargetA(b) ∧ CompletionCompatible(b)
```

Thus `Q2(r) ⇒ Q1(r)` by conjunction elimination.  The converse fails for
each of the **26** long roots with one or more of the independently replayed
1,398 Target-A boundaries: they witness Q1, while their negative envelopes
prove Q2 false.

This audit found a documentation/provenance error in Round 37's stronger
wording “all 28 long roots have Q1 true.”  The fixed ledger contains no Q1
witness for `long_q1_140` or `long_q1_178`; its bounded Q1 searches found
zero boundaries.  The envelope proves Q2 false for those two, but does not
prove Q1 either way.  The correct exact counterexample family has 26
exhibited Q1 witnesses, not 28.

## Search relevance

The Round-35 search recognizes **Q1** boundaries and intentionally does not
apply a completion-only prune.  The Round-37 theorem says that no
completion-compatible Target-A boundary can be reached from any of the 28
long roots.  Hence a further Q1 search cannot change the Q2/lower-bound
branch reduction; it is obsolete for that purpose, but it is not a proof
that Q1 is false.

All 22 Round-35 roots are therefore labelled
`SEARCH_OBSOLETE_BY_Q2_CERTIFICATE` with this explicit scope qualifier.  The
five `short_ell0`–`short_ell4` roots have positive envelope `+14`; they are
`SHORT_UNRESOLVED`, not closed and not launched by this audit.

## Infrastructure

Round 35's literal engine, root replay, canonical state decoration,
checkpoint format, and exact Target-A recognizer remain reusable.  To use it
for a short root, replace the long-prefix construction with the bare
abandonment root and preserve the fact that two R events, rather than one,
are still required.  No semantic change is needed to the exact transition or
collision checks.  Its result must still be described as Q1 unless a
completion-compatible predicate is explicitly added and independently
verified.
