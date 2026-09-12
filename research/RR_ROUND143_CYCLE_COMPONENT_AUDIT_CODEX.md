# Nonpure-cycle component accounting

This is a necessary-model hand proof and independent review for the d>0
remainder. It does not assert a new threshold closure.

## Component resources

After removing c pure E circuits, exactly d+1 beta components remain:
one dummy path and d nonpure cycles. A nonpure cycle contains a non-E
edge. Opening it at one such edge preserves all vertices, E-run blocks,
orbit and hex sets, and D_i=5O_i-P_i and R_i=P_i-distinct_hex_i.

If the cycle has n non-E edges, its opened path has n E blocks. Hence
b_i=n-O_i is exactly the opened path's ordinary old-orbit-entry count.
It is nonnegative: every orbit occurring on a nonpure cycle must have a
non-E entry, or else the entire component would be that orbit's pure E
cycle. **Do not charge another b on closing into the root.**

The A/B subgraph of each genuine component has indegree and outdegree at
most one and follows a common strict first-occurrence order. It is thus
acyclic. Its edges join ports of the same hex, so it is a forest inside
each hex. Summing its edge bound over hexes gives

    A_i + Qs_i <= R_i.

This includes the closing A/B edge. It is a necessary condition from
chronological provenance, not an automatic identity of arbitrary relaxed
closed port sequences. The enumerators explicitly impose the inequality.

Let s_comp=sum O_i-(O-c). The total number of E blocks is S+A+1, including
the dummy path's initial block. Consequently

    sum b_i = B*-s_comp,
    sum D_i = 5k-G+5s_comp,
    sum P_i = 120+G-5c,
    0<=s_comp<=B*,
    sum R_i = R_int <= A+Z-d.

A_i and Qs_i sum to the exact total A and Qs. Allowing heavy-cost sum at
most H is a safe relaxation. No cross-component collision is charged to
R_int; ignoring cross-component port/hex compatibility only enlarges
the resulting capacity convolution.

## Rooted cycle enumerator

A cycle with A>0 can always be opened at an A edge; if A=0 and Qs>0 it
can be opened at a B edge. Otherwise allow any non-E closing edge. Value
renaming maps the chosen opening target to 012345. This is the proved
left-S6 action, not arbitrary orbit relabeling. The scheme need not count
unrooted cycles exactly once: it only needs to contain a representative
of every genuine component for a capacity upper bound.

Enumerate a distinct-port path from that root. At a closure candidate,
check the literal shortest full-pass connector from the current endpoint
back to the root. Require non-E and the chosen A/B type when applicable.
Add its A, B, and heavy costs, but **no vertex, b, D, or R**. The root is
already present, so this special closure deliberately bypasses the usual
occupied-port insertion check. All other insertions retain that check.

For an A or B closing type the last source port is uniquely fixed as
sigma^-1(root) or sigma^-2(root). It cannot be visited earlier and later
revisited. Stopping its continuation after testing closure is therefore
safe. Positive controls include a 20-port clean cycle and the 10-port
E/A cycle with two sigma edges, zero D, zero b, and R=2. In particular,
the false claim that every nonpure cycle has a non-A/non-B opening is
not reintroduced.

## Exact-P versus capacity mode

Exact-P mode can use the audited ordinary suffix bounds only after
reserving the unknown closing edge's A/B/heavy cost. It reserves no R,
b, or aggregate deficit for closing. In particular, the pending closing
A/B must not be included in the internal-suffix inequality r>=a+q: its
root-hex repeat may already have been paid by a different visited vertex.
For unrestricted closings maximize over clean-w3 and heavy costs.

Capacity mode uses P=0 as an explicit sentinel. It has no exact-P suffix
pruning and visits all finite distinct-port paths within the resources,
up to the rigorous P<=120+R bound. It records maxima by actual b,D and
retains an independently replayable witness for each nonzero grid cell.
Two independently structured engines must agree on the complete grid
and accepted-cycle count. A cap leaves UNKNOWN and supplies witnesses
only. Their different node counts are not expected to match.

## Verification sources

- `RR_ROUND142_REPEAT_DOMAIN_OUTER_CODEX.md`: beta topology and resources.
- `RR_ROUND143_ONE_PATH_SUFFIX_AUDIT_CODEX.md`: rebasing and suffix proof.
- `round143_cycle_runs_codex.c`: whole-run recurrence, explicit tail geometry.
- `round143_cycle_ports_independent.c`: individual-port recurrence, literal
  exhaustive overlap geometry.
- `verify_round143_cycle_controls_codex.py`: third short tuple oracle,
  closure replay, six bound-on/off paired controls, paired small grid.

The component accounting and closing reservation were separately audited
by the independent proof-review agent. No computational closure is inferred
from these local controls alone.
