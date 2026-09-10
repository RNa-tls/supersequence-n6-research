# Round 142A — NR-UNIVERSAL and the exact cost of local cleaning

Author: CODEX. 2026-09-11. Route A is reported separately from Route B.
No global superpermutation DFS was performed. The n=5 billion-node counts
quoted in the incoming brief were not supplied as replayable artifacts here
and are not newly certified by this report.

## A1. Exact graph formulation

For distinct permutations p,q let d(p,q) be their ordinary maximum-overlap
distance. Let c(p,q) be the shortest appended length with q as the **first
permutation window after p**. This is an indecomposable, direct clean edge.
It is not the metric closure of clean edges, and c can exceed n.

With Hamilton orders ranging over all n! permutations,

    minimum covering length = n + min sum d(p_i,p_{i+1}),
    minimum NR length       = n + min sum c(p_i,p_{i+1}).

Proof of the first equality: shortcut any covering word along the order of
first appearances, retaining maximum overlaps; length cannot increase and
all permutations remain covered. Conversely every Hamilton spelling covers.
For the second, a clean edge has no intermediate permutation window, so
concatenating these edges along a Hamilton order produces exactly n! windows.
Every NR word has such a clean-edge decomposition and can replace each edge
by its minimum clean realization.

Thus NR-UNIVERSAL(n), “every cover is dominated in length by an NR cover,” is
equivalent to equality of the two minima. It is also equivalent to existence
of an NR global minimizer, not to every minimizer being NR. The nonempty
unrestricted formulation is useful, but the equality itself is still the
global goal; it is not presented as a new intermediate lemma.

**NR-UNIVERSAL(6): UNPROVED.** No counterexample to it was found or claimed.

## A2. Direct-clean connector theorem — HAND PROOF

For every n>=3 and p!=q,

    d(p,q) <= c(p,q) <= n+1.

Let j be the rightmost mismatch and a=p[j]. The word `p + a + q` is clean.
An intermediate window starting at s=1,...,n is

    p[s:] + a + q[:s-1].

If s<=j, a occurs twice. If s>j, p[s:]=q[s:], and q[s-1] is absent:
for s=j+1 it differs from a by the mismatch; for s>j+1 it differs from a
by distinct symbols in p. Therefore no intermediate window is a permutation.

There is at most one positive overlap of distinct permutations: two overlap
lengths would put q[0] at two distinct positions of p. Hence the exact formula is:

1. If the shortest-overlap connector is clean, c=d.
2. Otherwise, if p+q is clean, c=n.
3. Otherwise c=n+1.

This is independently checked by a character-suffix BFS in which permutation
windows are absorbing. The BFS calls no overlap or closed-form helper.

| n | suffix vertices exhausted | character edges | distinct targets |
|---|---:|---:|---:|
| 3 | 9 | 27 | 5 |
| 4 | 64 | 256 | 23 |
| 5 | 625 | 3,125 | 119 |
| 6 | 7,776 | 46,656 | 719 |

At n6, c=1,...,7 has counts **1,1,3,13,71,372,258**. All decisions completed
without a cap. These are local endpoint distances, not a covering search.

## A3. Local domination and unweighted dominators are REFUTED

Normalize p=012345, q=234501. The prefix

    123450012345

contains exactly the two permutation windows 123450 and p. Append `01`:

    12345001234501.

The new window sequence is the old 123450 followed by the first q. This
repeat-bearing connector has cost 2. An exact clean p-to-q connector costs
**6**, not 2. The prefix is extended by clean edges in the artifact to a
literal complete n6 cover of length 5,027 with 721 windows. Thus the local
counterexample occurs in a nonempty complete-cover domain.

The same construction produces boundary/coverage counterexamples for all
**322** dirty minimum connectors. Cleaning costs increase by
1/2/3/4 in **307/11/3/1** cases. In **11** cases the increase even exceeds
the number of hidden repeated windows. For example `345021` costs 3 with
one hidden window but costs 6 clean: deleting one repeat can cost three.
Therefore neither “clean each ear at no cost” nor “pay at most one per
repeat locally” is sound.

The clean graph has a direct edge between every two distinct vertices by
A2. An internal repeated vertex is therefore not an unweighted connectivity
dominator, yet the example shows it can be essential to a low-cost local
realization. “Every non-dominator repeat is cheaply removable” is false
for ordinary reachability dominators. A cost-and-coverage domination claim
would require new mathematics, not a change of terminology.

These examples do not refute a global exchange, NR-UNIVERSAL, or the +1 gap.

## A4. Repeat penalty: what is and is not established

Writing actual literal-window counts, define

    R = M-n!,    Xrun = P_actual-(n-1)!,
    Hvy = sum_actual_joints(w-2) = S_actual+H_actual.

Here S counts w>=3 joints and H=sum(w-3)+. Hvy is **not H alone**.
Then, without NR,

    L = n+n!+(n-1)!-2 + R+Xrun+Hvy.

For n6 the base is 844. Use calligraphic D for R+Xrun+Hvy, to distinguish
it from the port deficit D_phi=5O-P. Repeats trade against the other defects;
they are not an additive cost independent of the remaining geometry.

The universal strict gap `min L(repeated)>min L(NR)` is UNPROVED at n6.
Appending one rotation character to the verified NR872 witness produces
a repeated cover of length 873, so the repeated minimum is at most 873.
Equality to 873 has not been proved. The known +1 examples at small n are
not extrapolated. Route B proves a different, weaker structural inequality
and an unconditional lower bound 869; see the other report.

## A5. Arc/trim audit

The Arc Lemma has a short general proof. If every multiply-visited window
were internal to a rotation run, all its occurrences would be followed by
the next rotation, which would also be multiply visited. Continuing around
the rotation class would make every member multiply visited and none able
to be a run endpoint, contradicting finiteness. Thus a repeated run endpoint
exists.

The proposed trim dichotomy needs its hypotheses. For a nonterminal endpoint
with an incoming rotation and a **minimum-overlap clean** exit of weight w<=n,
removing that endpoint from the occurrence walk is a literal no-op for w<n
and strictly shortens for w=n. Complete n6 local checks give 89 no-ops and
308 strict cases among the 397 clean minimum-overlap edges.

This is not an unrestricted iff theorem for all clean graph edges: A2 includes
minimum direct clean edges of weight n+1, and trimming those also strictly
shortens. Singleton runs and terminal endpoints require separate treatment.
No claim of a universal nonincreasing global cleaning operation is inferred
from this local trim table.

## A6. Result and remaining mechanism

Route A supplies an exact direct-clean metric, explicit failures of local
domination, and a finite complete 719-connector/322-ear catalogue. It does
not supply the global exchange needed for NR-UNIVERSAL. The useful hybrid
is to demand cleaning of light joints only; Route B proves that condition
is sufficient for the lower bound while allowing dirty heavy joints.
The transformation into that class is still unproved.

Artifacts: `outputs/rr_round142_route_a_codex.json`,
`outputs/rr_round142_dirty_catalog_codex.json`. Their source and independent
algorithms are `research_round142_route_a_codex.py` and
`verify_round142_dirty_catalog_codex.py`.
