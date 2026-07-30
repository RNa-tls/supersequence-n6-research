# Round 35 local handoff validation

## Repository identity

Local checkout:

```text
repository  RNa-tls/supersequence-n6-research
branch      claude/n6-supersequence-length-rn17wf
HEAD        d6640193649a520f5b2ea209dec273fcb2048ae1
```

The checkout was clean before this Round-35 audit/plan change.  `main` was not
used.

## Local verification results

The repository test suite was run locally with:

```powershell
& $py -m unittest discover -s tests -v
```

Result: **38 tests in 2.963 seconds, `OK`**.

The witness checks in that suite and the local verifier establish for
`data/verified_872_witness.txt`:

| property | result |
|---|---|
| string length | 872 |
| alphabet | exactly `123456` |
| distinct length-6 permutation windows | 720 |
| coverage | all of \(S_6\) |

Round-34 lightweight entry points were replayed locally:

```powershell
& $py src\build_rr_segment_successors.py --out <temporary-output>
& $py src\search_rr_target_b_flow.py --out-models <temporary-models> --out <temporary-output>
& $py src\verify_rr_target_b_flow.py --out <temporary-output>
```

The successor index and model artifacts agree semantically with their stored
forms.  (The flow-search JSON has a nondeterministic elapsed-seconds field,
so byte identity is neither expected nor required.)  The engine-level
verification reports all seven main survivors as `EXHAUSTED_NO_PATH`, seven
weak Area-A-only variants as `INCOMPLETE`, no contradiction, no SAT
certificate, and no reached R5/component model.  Engine-level exhaustive
counts are finite and self-terminating; this is not a timeout result.

## Round-27 local reproduction

The old targeted continuation command was replayed exactly:

```powershell
& $py src\search_rr_long_prefix_extensions.py `
  --ceiling 12 --node-cap 8000 --stop-on-first `
  --output <temporary-output>\rr_long_prefix_extension_results.json
```

The temporary result is record-for-record equal to
`outputs/rr_long_prefix_extension_results.json`:

| `FOUND` | `INCOMPLETE` | `EXHAUSTED_IMPOSSIBLE` |
|---:|---:|---:|
| 6 | 22 | 0 |

All incomplete roots stop only because of the 8,000-node cap.  Their frontier
does not naturally empty; they remain unfinished.  The independent
certificate command

```powershell
& $py src\verify_rr_long_extension_certificate.py `
  --results <temporary-output>\rr_long_prefix_extension_results.json `
  --output <temporary-output>\rr_long_prefix_certificates.json
```

replayed all six found literal witnesses: 6 agreements, 0 disagreements.

## Round-35 handoff boundary

The next work item is a new, conservative decorated Target-A traversal as
specified in `research/RR_TARGET_A_SEARCH_PLAN.md`; it has **not** been
started by this handoff.  Its roots and all known missing fields are fixed in
`research/RR_TARGET_A_ROOT_AUDIT.md` and the two corresponding JSON files.

No exhaustive claim follows from the 22 old capped results.  No claim about
Target B, Target C, or the full NR6 statement is made here.
