# Unconditional exclusion of lengths 869 and 870

This is an intermediate Round143 result, not Chapter1 completion. The
remaining length871 has NOT been excluded. The independently checked
computations and hand reductions below give **871 <= L6 <= 872**.

## Starting point and hypotheses

Round142 already excludes every covering word of length at most868 without
NR6. For a hypothetical shorter counterexample, take its first-occurrence
maximum-overlap fixed representative. This preserves coverage and does not
increase length. No assumption of a repeat-free representative is made.
Use the exact definitions and proof of MASTER-142 in
`RR_ROUND142_REPEAT_DOMAIN_OUTER_CODEX.md`:

    L=867+k+Z+H+B*,  G=P-120, O=24+k,
    d=K-1-c, A=D2, Z=2g+d-A, Qs<=Z,
    A+Qs<=R_int<=2g, G=c+A+Z.

Here S counts weight>=3 selected joints, not strands; B*=S+1+A-O+c.
The repeat bounds10/15/20 apply to fixed representatives at869/870/871,
not to an unchanged arbitrary input word's repetitions.

## New hand reductions

`RR_ROUND143_ENDPOINT_CORRECTION_CODEX.md` proves the companion-hex
endpoint loss and explicitly allows an A/B edge to be a cycle opening.
Its paired endpoint recurrence already excludes all92 rows at869.

`RR_ROUND143_SIGMA_DEFICIT_CODEX.md` proves the stronger block-deficit
inequality

    Delta=5k-G+5B* >= A+Qs-Z-d.

It charges each forbidden sigma-connected pattern5,4,...,4,5 to a distinct
extra repeated-hex E entry. This is an induction and event-injective
counting proof, not an extrapolation of a finite sequence.

The general extraction audited in
`RR_ROUND143_COUPLED_SIGMA_INDEPENDENT_CODEX.md` yields necessary pieces
in which every non-A entry uses a new hex and each A edge is exactly
v->sigma(v). All selected entry ports remain distinct. The bounds are

    1<=m<=Z+d+1+h,
    max(0,A+Qs-Z-d)<=sum A_j<=A,
    sum b_j=B*-s', sum D_j=5k-G+5s', 0<=s'<=B*.

The NEW sharing s' is maximized independently of the sharing value from
the older extraction. No continuation-equivalence quotient is assumed.

## Finite capacities and independent verification

The whole-E-run producer and literal-overlap port-at-a-time checker have
different traversal and geometry implementations. Every capacity actually
used as an upper bound completed in both implementations, with equal
maximum, accepted-prefix count, and available endpoint tables. Capped
pilot cells were excluded as upper bounds. Every maximum witness was
separately replayed from literal endpoint overlaps.

Capacity is exact in A and monotone only in its upper budgets b,D. Important
dominating cells (A,b,D -> maximum entry ports) include

| A | b | D | maximum |
|---:|---:|---:|---:|
| 2 | 0 | 13 | 87 |
| 2 | 1 | 8 | 87 |
| 2 | 2 | 3 | 57 |
| 4 | 0 | 11 | 80 |
| 4 | 1 | 6 | 64 |
| 4 | 2 | 1 | 30 |
| 6 | 0 | 9 | 51 |
| 6 | 1 | 4 | 26 |

The small odd-A capacities are also included because cutting can remove
one A edge. For example C(1,0,6)=54 and C(3,0,6)=54. Neither the original
parity of A nor global geometric feasibility is imposed on these pieces.

`verify_round143_coupled_extraction_codex.py` computes both a backward
resource recursion and an independent forward allocation convolution.
They agree on635 distinct requested convolution cells in the current
869--871 audit. Unknown cells propagate UNKNOWN rather than a numeric
upper bound. Equality is never promoted to closure.

## Threshold certificates

The final ledger is `outputs/rr_round143_coupled_extraction_codex.json`.
All counts here refer to necessary arithmetic rows, not literal walks.

| Length | Arithmetic rows | Strict capacity | Deficit contradiction | Unresolved |
|---:|---:|---:|---:|---:|
| 869 | 92 | 67 | 25 | 0 |
| 870 | 427 | 321 | 106 | 0 |
| 871 | 1548 | 765 | 339 | 444 |

At871 the444 unresolved rows are61 missing-capacity rows,43 equality
rows and340 open-capacity rows. They are NOT claimed realizable, but
neither are they excluded by this certificate.

Every arbitrary cover of length<=870 has a fixed representative of
length<=870. Length<=868 contradicts Round142. At869 or870 its arithmetic
row is in the respective complete ledger and violates a hand necessary
inequality or a strictly insufficient independently exhausted capacity.
This proves L6>=871 without NR6. The established explicit872 witness
gives the other side of the interval. No claim of L6=872 is justified yet.

## Reproduction and retained limitations

Run the paired capacity drivers using the argv stored in each input JSON,
then run the coupled-extraction verifier with those inputs. Source commit,
committed/runtime hashes, compiler, binaries, node counts, elapsed time,
cap flags and deterministic traversal digests are recorded in the capacity
files. `tests/test_round143_dirty_capacity_codex.py` checks the accounting,
two convolution forms, unknown propagation and literal SIGMA replay.

The rich triple-endpoint exploratory recurrence is NOT needed for this
closure and its pending independent verification has not been promoted.
The old uncommitted general-endpoint draft with the invalid cycle-opening
assumption is NOT a proof source. Extending the remaining capacity tables
and testing equality reconnections are still active work, not routes
declared exhausted.
