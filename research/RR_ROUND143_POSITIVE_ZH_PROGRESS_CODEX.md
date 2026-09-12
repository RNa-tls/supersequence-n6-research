# Positive-Z/heavy threshold refinement

The previous paired exact-P certificates exclude the complete `Z=H=0`
length-871 domain. They do not exclude general length 871. The established
unconditional interval remains **871 <= L6 <= 872**.

## Odd retained-sigma capacities

General coupled extraction can delete individual sigma edges. Thus neither
retained A nor the A count of a piece inherits an even-parity restriction.
Ten additional exact-A cells were exhausted independently by whole-E-run
and port-at-a-time implementations. All maxima, accepted-prefix counts and
endpoint arrays agree; no node cap was used. Source and executable hashes,
compiler, arguments, node counts and times are in the paired artifact.

| A | b | D | Maximum ports |
|---|---|---|---|
| 1 | 0 | 13 | 83 |
| 1 | 1 | 8 | 82 |
| 1 | 2 | 3 | 62 |
| 3 | 0 | 11 | 84 |
| 3 | 1 | 6 | 69 |
| 3 | 2 | 1 | 29 |
| 5 | 0 | 9 | 61 |
| 5 | 1 | 4 | 31 |
| 7 | 0 | 7 | 33 |
| 7 | 1 | 2 | 0 |

Backward allocation and independent forward allocation agree on all 635
requested scalar convolution cells. Reapplying the already verified 84
exact-P queries produces this length-871 ledger:

| Status | Necessary arithmetic rows |
|---|---:|
| Strict capacity exclusion | 874 |
| Sigma-deficit obstruction | 339 |
| Exact-P empty model | 152 |
| All exact prefixes fail static completion | 1 |
| Equality, still unresolved | 45 |
| Capacity above requirement, still unresolved | 137 |
| Total | 1548 |

The unresolved count falls from 271 to 182. These are arithmetic rows,
not canonical literal topologies or covering walks. Every unresolved row
has positive Z or positive H. Length-869 and length-870 certificates are
unchanged and remain complete.

## Tested endpoint refinement does not add a closure

The independent endpoint audit proves the proposed interpiece full/full
charge, but also proves its redundancy: the number of designated seams is
already no greater than the allowed bad-seam count. The implemented backward
and forward recurrences agree on 468 allocations and do not close an extra
row. This is recorded as a tested dead end, not as another strengthening.
The independent edge-count check `A-Aret <= m-1` is included and is sound.

## Next restricted model

When d=0, one beta path remains after the pure E circuits are removed.
Keeping heavy and sigma-squared joints in this path avoids the geometric
information lost by splitting them. The new hand-audited necessary model
uses distinct ports, exact A and Qs, at most A+Z repeated-hex arrivals,
heavy cost at most H, b<=B*, D<=5k-G, and exact required P. Its suffix
upper bound is derived from the existing independently certified coupled
capacities with an aggregate D+5b budget. No new threshold exclusion is
asserted until paired exhaustive queries and controls finish.

## Sources

- `rr_round143_t4_odd_dominant_codex.json`: paired uncapped capacities.
- `rr_round143_t4_odd_refined_codex.json`: scalar allocation certificate.
- `rr_round143_t4_combined_codex.json`: complete arithmetic ledger.
- `rr_round143_t4_coupled_endpoint_codex.json`: redundant endpoint test.
- `RR_ROUND143_COUPLED_SIGMA_INDEPENDENT_CODEX.md`: general inclusion.
- `RR_ROUND143_COUPLED_ENDPOINT_INDEPENDENT_CODEX.md`: endpoint proof and limits.
- `RR_ROUND143_ONE_PATH_SUFFIX_AUDIT_CODEX.md`: one-path suffix inclusion.

All files are local repository sources; hashes of computational dependencies
are preserved in the machine-readable artifacts. No old frontier or NR6
normalization search is used.
