# Path and nonpure-cycle capacity convolution

This necessary model supplements the independently reviewed component
identities in [Cycle component accounting](RR_ROUND143_CYCLE_COMPONENT_AUDIT_CODEX.md).
It does not identify different components' literal ports or assume they can
be simultaneously embedded. Removing these compatibility conditions enlarges
the model and therefore is legitimate for an upper capacity bound.

## Resource allocations

There is one path and exactly d nonpure cycles. In component i, let a_i,q_i
be the exact A/B counts, let r_i be its repeated-hexagon incidence excess,
and let h_i be its heavy cost. The chronology argument gives r_i>=a_i+q_i.
Put e_i=r_i-a_i-q_i. Global resources imply

    sum a_i=A, sum q_i=Qs,
    sum e_i <= Z-d-Qs, sum h_i <= H.

Unused e and h budgets can be assigned to the path, since each component
oracle treats R and H as upper budgets. Consequently it is safe to convolve
with equality on their allocated upper budgets. This does not turn a_i or
q_i into monotone quantities: those two remain exact throughout.

For every possible component sharing s in [0,B*], independently of the old
extraction's sharing, use

    sum b_i=B*-s, sum D_i=5k-G+5s.

These are actual b/D resources. All their nonnegative allocations are
included. A cycle closure adds its A/B/heavy cost but no new vertex, b, D,
or r. Treating the closing target as another entry would invalidate the
10-port E/A cycle positive control.

The actual deficit also forces P_i=-D_i modulo five, because
D_i=5O_i-P_i. Round any scalar path upper bound down to the largest
nonnegative number in this residue class. The same rounding applies to
an opened-cycle path upper bound. This uses actual component D, not an
arbitrary bounding rectangle's D cap.

## Bounds and missing data

For each allocation, sum an upper capacity for the path and for each cycle.
The maximum over all allocations is an upper bound for the required total
ports. A strict shortfall excludes the row. Equality alone does not.

Cycle tables enumerate the exact A/Q class under upper R/H/b/D. Within a
completed table, a grid entry records the maximum at its exact actual b/D.
Thus an exact b/D allocation can use that cell (zero if absent), provided
the table's search rectangle contains it. R/H may be relaxed upwards.
Taking the minimum of several applicable upper bounds is sound. A capped
table supplies no upper bound, regardless of its largest observed witness.

If a cycle table is absent, open a preferred non-E edge. If A>0, choose an
A edge; otherwise if Qs>0 choose B. This lowers the path's exact A or B
count by one and leaves R,H,b,D unchanged. In the remaining case one may
open a clean w3/heavy edge and conservatively allow the original H upper
budget. The existing generic path-capacity bound then applies. Finally,
P<=120+R is always a valid universe bound. No unknown or capped observed
maximum is silently used as a finite exhaustive maximum.

## Independent finite checks

`verify_round143_component_convolution_codex.py` evaluates every queried
allocation both recursively by removing the first cycle, and independently
by multiplying cycle resource polynomials then adding the path. It requires
exact equality before using a bound. The generic path bound also retains
its prior independent backward/forward checks.

The regression suite compares both recurrences with literal Cartesian
enumeration on deliberately nonmonotone exact-resource toy tables, and
preserves the zero-b closing control. Complete cycle grids are accepted only
after their two literal engines agree and every grid witness is independently
replayed. This verifier performs resource allocation and certificate replay,
not any continuation search.
