# Round 35 — Round 27 Target-A root audit

## Scope and grade

This is a **local read/replay audit** of the frozen Round 27 long-prefix
corpus.  It neither changes the corpus nor treats a node cap as an
impossibility proof.

Inputs:

* `outputs/rr_long_excursion_prefixes.json`;
* `outputs/rr_long_prefix_quotient.json`;
* `outputs/rr_long_prefix_extension_results.json`.

The machine-readable ledger is
`outputs/rr_target_a_22_root_ledger.json`; its quotient companion is
`outputs/rr_target_a_root_quotient.json`.  The audit utility is
`src/audit_rr_target_a_roots.py`.

## The counting unit

The unit is a **state-bearing prefix pair**

\[
  (\text{literal joint word},\;\ell),\qquad \ell\in\{0,1,2,3,4\},
\]

where \(\ell\) specifies the abandonment root.  It is not merely a word:
the same word can replay legally from several \(\ell\)'s and can lead to
different exact states.  `build_rr_long_excursion_roots.py::replay_prefix`
calls this distinction out explicitly.  The full frozen corpus contains 186
such pairs, whereas its "38" historical count is a count of legal words.

After the RR two-\(R\) budget filter there are 28 prefix pairs.  Their old
bounded Target-A search outcomes are

| result | number | interpretation |
|---|---:|---|
| `FOUND` | 6 | exact Target-A witness; literal replay certified |
| `INCOMPLETE` | 22 | cap-only bounded result, **not** an exclusion |
| `EXHAUSTED_IMPOSSIBLE` | 0 | none |

Every one of the 22 selected records has `nodes_expanded=8000`,
`truncated_by_node_cap=true`, and `truncated_by_ceiling=false`.  The old
artifact does not serialize a prior maximum reached depth.  The ledger
therefore records that field as `null` with status `MISSING_NOT_SERIALIZED`;
it is not inferred from the ceiling.

For each root the ledger records the literal word, \(\ell\), \(L\),
\(G=L-1\), R count, \(F_{\rm sym}\), \(F_{\rm def}\), \(\Phi\),
\(O\), `N_def`, visited count, exact stable-key hash, old bounded-search
statistics, and source/reconstruction functions.  Direct replay verifies
both stored post-return stable key and state hash for all 22.

## Proven quotient audit

The following distinctions were checked by exact replay, not guessed from
the resource ledger.

| equivalence tested | classes among 22 | result |
|---|---:|---|
| raw state-bearing `(word, ell)` roots | 22 | baseline |
| exact post-return `ExactState.stable_key()` | 22 | no duplicate |
| existing left-\(S_6\) canonical decorated pair `(state, O*, R1 target)` | 22 | no duplicate |
| conservative history-preserving key `(state,O*,R1 target,R-count,ell)` | 22 | no duplicate |

Thus the current cohort can simultaneously be described as **22 raw roots**
and as **22 singleton classes under each existing, proved quotient**.  No
reduction follows from the audit because no two records merge.

`terminal-relevant history equivalence` is **not proved**.  It must not be
used to merge roots.  In particular, later CH1/CH2/chaining predicates carry
R1-target and completer history not recoverable from bare `ExactState`.
The conservative key is intentionally an over-refinement, not a proof of a
minimal continuation key.

## Reconstruction and independent checks

The replay chain is:

1. `src/build_rr_long_excursion_roots.py::replay_prefix` produces the root
   record;
2. `build_rr_long_excursion_roots.py::replay_state` reconstructs the exact
   post-prefix state;
3. `build_rr_long_excursion_roots.py::canonical_pair_key` applies the
   existing tied-left-action canonicalization while transporting \(O_*\) and
   the R1 target;
4. `src/search_rr_long_prefix_extensions.py::search` is the old bounded
   Target-A traversal; and
5. `src/verify_rr_long_extension_certificate.py::replay_witness` independently
   replays every found literal trace.

The Round 35 rerun used the original settings

```powershell
& $py src\search_rr_long_prefix_extensions.py `
  --ceiling 12 --node-cap 8000 --stop-on-first `
  --output <temporary>\rr_long_prefix_extension_results.json
```

Its 28 result records are byte-for-field equal to the frozen stored result.
The separate certificate verifier replayed the six `FOUND` traces successfully
(`6` agreements, `0` disagreements).  The 22 capped records deliberately
remain `bounded incomplete` in that verifier.

## Consequence

Round 35 begins with 22 nonmerged, reproducible unfinished roots.  This audit
does **not** establish that any is impossible, and it does not claim a result
about Target B, Target C, or the global NR6 problem.
