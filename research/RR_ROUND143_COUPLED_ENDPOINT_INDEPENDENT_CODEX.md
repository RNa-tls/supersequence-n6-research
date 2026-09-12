# Independent audit: endpoints after general coupled extraction

Author: CODEX independent hand audit, 2026-09-12.
Reviewed baseline: `2d5cc68`. No capacity search or closure is asserted.

## Result and scope

Use the fixed-representative R142 coordinates and the general extraction
proved in `RR_ROUND143_COUPLED_SIGMA_INDEPENDENT_CODEX.md`. Put A=D2.
The proposed endpoint constraint is a safe necessary relaxation, including
for E+A cycles, but **it is vacuous with the stated extraction budgets**.
Endpoint masks alone cannot improve that convolution by this constraint.

The extraction supplies coupled pieces with

    m<=Z+d+1+h,
    max(0,A+Qs-Z-d)<=A_ret<=A,
    0<=s'<=B*, sum b_j=B*-s', sum D_j=5k-G+5s'.

As before, s' is sharing for these new pieces, not the sharing of an older
extraction. A_ret and the individual retained A counts are exact integer
counts, with no inherited parity restriction.

## Number of actual interpiece A seams

Let x and y count A and B edges used to open the d nonpure cycles,
respectively, with x+y<=d. Every other removed A edge is an interpiece
boundary in the original component's linear order. Hence their number is

    r=A-A_ret-x >= a=max(0,A-A_ret-d).

Keep the final pieces in order within each original component, then
concatenate the component lists. These additional concatenation joins are
arbitrary relaxation joins, not asserted original edges. Designate any a
of the r actual interpiece A seams and demote all other joins to arbitrary
joins. This retains every original candidate. In particular, an A edge
used to open an E+A cycle is NOT silently counted as an interior seam.

## Full/full charging without hex-simple pieces

Perform the charging in each ORIGINAL component after its one cycle
opening, before heavy, B, or greedy extra cuts. Every remaining A or B
edge contributes a repeated-entry vertex, because its target has its
predecessor's hex. There are A-x+Qs-y such vertices.

Consider an actual interpiece A seam whose incident E blocks both have
five ports. Write v for the left block's last port. Its first port is
E(v), the right block starts at sigma(v), and its fifth port is

    E^4 sigma(v) = sigma^-1 E(v).

The right fifth port therefore has the hex of the left first port. It is
another repeated-entry vertex. Its incoming edge is E, so it is distinct
from every A/B target counted above, including targets of A edges retained
inside the final coupled pieces. Distinct seams have distinct right blocks
and hence distinct fifth-entry witnesses. Shared hex names do not merge
these charges: repeated-hex excess counts repeated VISITS, not distinct
hex names that happen to repeat.

Thus, for all full/full actual interpiece A seams together,

    R_int >= A-x+Qs-y+bad,
    bad <= Z-Qs-d+x+y <= Z-Qs.

This vertex proof does not require the final pieces to be hex-simple.
Charges are summed before concatenating different original components;
cross-component hex sharing is never charged to R_int. Restricting to any
designated subset of the seams preserves the same upper bound on bad.

Consequently C(A_j,b_j,D_j,mask) capacities may safely enforce at most
Z-Qs full/full designated joins, while relaxing all other joins. The masks
must describe the first and last ORIGINAL E blocks. No extraction cut
splits an E block, so these are the same blocks recorded by the coupled
capacity implementations.

## Why the proposed mask constraint cannot strengthen the bound

The retained-A lower bound immediately gives

    a=max(0,A-A_ret-d)<=Z-Qs.

Therefore every designated seam may be full/full without exceeding the
proposed allowance. The endpoint condition removes no mask sequence.
Even exact opening data do not repair this issue for these compulsory
cuts: the extraction proof gives

    r=A-A_ret-x <= e0 <= Z-d-Qs+x+y,

and the last quantity is exactly the sharper full/full allowance. The
companion witness is charging surplus already spent to justify the cut,
not an additional independent cost. Subject to the same ordinary
piece/join-count feasibility, introducing endpoint masks with these
allowances cannot improve the corresponding scalar capacity convolution.

One separate structural check is A-A_ret<=m-1: before cuts, the one path
and d cycles together have P'-1 edges; the final m paths have P'-m edges.
Thus exactly m-1 non-E edges were deleted, including cycle openings, and
at most that many were A. This check is independent of endpoint fullness.
At the maximal padded piece count Z+d+1+h it is already implied by the
stated retained-A lower bound, but it may help exact-piece-count ledgers.

## A separate possible refinement: voluntary A cuts

After obtaining a coupled piece, one may deliberately cut a retained A
edge. Its incident E blocks cannot both be full: the same fifth-entry
identity would otherwise produce a non-A repeated-hex landing INSIDE
that piece, forbidden by the coupled model. Thus each such voluntary cut
creates an actual A seam guaranteed to have at least one partial endpoint.

The two resulting subpaths remain coupled pieces. More precisely, a
coupled path has repeated-hex excess exactly its A count. Cutting an A
edge reduces that count by one and reduces excess by at least one, while
the remaining A targets still witness all their repeats. The excess drop
is therefore exactly one; the new subpaths satisfy the same model.

For any available v retained A edges, voluntary cuts add v pieces, reduce
A_ret by v, preserve all whole E blocks, and leave the same sharing and
resource identities valid with the NEW sharing value. These v seams are
individually known not to be full/full. This supplies a genuine possible
endpoint restriction, at the cost of more pieces, and interpolates between
coupled and all-A-cut extractions. Choosing v universally requires v to
be available in every relevant retained-A case, or separate case handling.
Its capacity benefit needs a new correctly budgeted recurrence; none is
claimed here.
