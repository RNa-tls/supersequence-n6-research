# Round 50 - corrected fair pilots for `short_ell1` through `short_ell4`

## Scope

This is a **bounded observational pilot**, not an exhaustion claim.  The
admission traversal spent `250` pre-R
expansions per bare root.  Every observed R1 provenance child then received
the equal positive cap `5000` in a distinct v5
checkpoint.  A nonempty frontier is always `INCOMPLETE` for absence purposes.

The v5 schema is `rr-short1-4-corrected-fair-checkpoint-v5-literal-r2-source`; its recognizer is
`R2_LITERAL_JOINT_SOURCE_V1`.  Literal R2 source-sensitive predicates
consume `edge.run.state`; the run uses Target-A-safe pruning only.

Independent verification returned `VERIFIED_CAPPED_PILOTS` and replayed
`3` literal Target-A hit(s).

## Per-root telemetry

| root | observed R1 children | expansions | frontier | repairs | repaired R2 paths | literal Target-A hits | bounded status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `short_ell1` | 99 | 146071 | 1392 | 147364 | 64727 | 0 | `ROOT_NO_TARGET_A_IN_PREFIX` |
| `short_ell2` | 111 | 141748 | 1280 | 142917 | 65274 | 0 | `ROOT_NO_TARGET_A_IN_PREFIX` |
| `short_ell3` | 107 | 142541 | 1300 | 143734 | 64070 | 0 | `ROOT_NO_TARGET_A_IN_PREFIX` |
| `short_ell4` | 122 | 166177 | 1360 | 167415 | 76357 | 3 | `ROOT_ALL_OBSERVED_TARGET_A_CLOSED` |

The per-child fair-budget assertion is `True`.
Different roots can have different total work because they can have different
numbers of admitted R1 provenance children.

## Target-A to Target-B ledger

Literal witness count: `3`.
Exact decorated boundary states: `3`.
Canonical boundary classes: `3`.
New canonical classes: `0`.

| canonical boundary | literal multiplicity | known-18 comparison | helper-free Target-B disposition |
| --- | ---: | --- | --- |
| `20585475b28fe99d` | 1 | EXACT_KNOWN18_MATCH | `KNOWN18_HELPER_FREE_CERTIFICATE_REUSED` |
| `79f21d2facc1ce2a` | 1 | EXACT_KNOWN18_MATCH | `KNOWN18_HELPER_FREE_CERTIFICATE_REUSED` |
| `f1a925551da6109e` | 1 | EXACT_KNOWN18_MATCH | `KNOWN18_HELPER_FREE_CERTIFICATE_REUSED` |

## Reproducibility

- `outputs\rr_short1_4_corrected_fair_results.json` - SHA-256 `858bf5dadf79985a4658158a732c95f1e7349e23882bee073bc03d4b6dcff115`
- `outputs\rr_short1_4_target_a_classes.json` - SHA-256 `f5d80e2301058266b72f3d7377981f6530f830cececda6d9429678c3586b3ef8`
- `outputs\rr_short5_cross_root_profiles.json` - SHA-256 `35afbfad2f10daa6c2b16a503aad2d25b7393ae25a6ea179feef0ddf79113aa0`
- `outputs\rr_short1_4_corrected_fair_verified.json` - SHA-256 `95ecc3ecb6937d16593dfdc5b74eb4919cb1ab1cf22be65f1e9b06988ad7dfe0`

- pilot driver SHA-256: `bc93957c39bd601a712f4bf3ca377f33273325b39e5a03c7bebc9babe1c6bd2a`
- exact engine SHA-256: `5388bf46a0eb1d56223193c35c842cf19a7a6d6bba7b1b1ade11e785d427d649`
- checkpoint schema: `rr-short1-4-corrected-fair-checkpoint-v5-literal-r2-source`

No frequency reported here is a theorem or an exhaustion result.
