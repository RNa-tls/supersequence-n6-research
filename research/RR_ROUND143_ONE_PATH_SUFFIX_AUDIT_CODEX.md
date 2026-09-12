# One-path suffix-capacity audit

## Verdict and scope

The proposed one-path inclusion and suffix decomposition are sound under
the boundary and aggregate-resource conventions below. This is a hand
audit only: no new search, arithmetic-row exclusion, or capacity result
is asserted.

The suffix bound must maximize over every possible retained sigma count
in its stated interval. Exact-sigma capacities cannot silently be treated
as monotone in that count. The deficit constraint is an aggregate
`sum D_j + 5 sum b_j` constraint, not a bound on each piece's D obtained
by subtracting the prefix's D.

## Inclusion when d=0

Use the fixed-point first-occurrence representative and spliced beta
geometry from Round142. When `d=K-1-c=0`, removal of the c pure E circuits
leaves exactly one beta path. The removed circuits each use all five
ports of an E-orbit, so those orbits have no entry ports elsewhere.
All remaining entry ports are distinct. The path has

    P = 120+G-5c,
    Q = 24+k-c,
    D = 5Q-P = 5k-G.

Let A count sigma edges and Qs count sigma-squared edges. They are
respectively the spliced dirty weight-two and same-hex dirty weight-three
edges. The number of maximal E-runs is `S+1+A`, so its number of non-E
entries into already opened orbits is

    b = S+1+A-Q = B*.

The path's number of repeated-hex arrivals is its within-component hex
excess. Since `d=0`, the established topology inequality gives

    repeated-hex arrivals = R_int <= 2g = A+Z.

Pure E circuits have zero within-component hex excess. Cross-component
hex intersections are not added to this count.

The spliced full-pass source endpoint equals the original joint source
endpoint. Consequently, retaining every literal shortest connector from
that endpoint includes every actual spliced edge. This invokes the
fixed-point joint-geodesicity hypothesis, not distinct ports alone.
Original joints have weight at least two because selected passes are
maximal consecutive first-occurrence windows. Shortest connector weights
are at most six; weight one would also target the spliced source entry
port again, which distinct entry ports forbid. Thus using all shortest full-pass connectors
of weights `2..min(6,H+3)`, with cost `max(weight-3,0)`, and total cost at
most H, is a necessary relaxation. The source endpoint here is the last
six-symbol window of a full pass, not the entry port itself. Omitting
external hidden-window history constraints only enlarges the model.

This inclusion does not apply without modification when `d>0`: nonpure
cycles would remain and cycle-opening bookkeeping would be necessary.

## State at a non-E boundary

The prefix must end after a completed maximal E-run. Consume the chosen
non-E boundary edge before invoking the suffix bound, but count its
target as the first suffix port, not as a prefix port.

Let `P_pre`, `R_pre`, and `b_pre` be the prefix port count, completed
E-run count, and old-orbit non-E-entry count. Define

    Delta_pre = 5 R_pre-P_pre = D_pre+5b_pre,
    Delta_cap = Dcap+5B-Delta_pre.

For boundary target t, let epsilon_Q indicate that its orbit was opened
in the prefix and epsilon_h indicate that its hex was visited there.
The suffix resource limits are

    B_rem = B-b_pre-epsilon_Q,
    r = global_repeat_cap-prefix_repeat_count-epsilon_h,

with the boundary edge also subtracted once from the exact A or Qs count
when appropriate, and its heavy cost subtracted once from H. Write a,
q, and h for the resulting internal suffix sigma count, sigma-squared
count, and heavy-cost allowance. A negative remaining exact count or
allowance makes this boundary branch infeasible.

Rebase the suffix at its first port by clearing prefix orbit and hex
occupancy. This cannot increase the suffix's old-orbit-entry count or
repeated-hex-arrival count: an orbit or hex already seen within the
suffix was also already seen globally. Therefore its rebased counts
obey `b_suffix <= B_rem` and `repeat_suffix <= r`. Its first port is
uncharged after rebasing, consistently with the boundary charges above.
The upper-capacity relaxation may also forget prefix-port exclusions;
that only enlarges the standalone suffix family. The actual one-path
enumeration must still reject a globally repeated entry port.
Rebased A/B arrivals remain repeated hexes because their immediate
predecessors are inside the suffix, so necessarily `r >= a+q`.

Every suffix E-run is disjoint from the completed prefix E-runs, giving

    Delta_suffix = 5 R_suffix-P_suffix
                 <= Dcap+5B-Delta_pre = Delta_cap.

This identity does not require the suffix to use fresh global orbits.
Do not subtract another `5 epsilon_Q` from Delta_cap: that would charge
the boundary twice in incompatible deficit coordinates.

## Greedy splitting into coupled SIGMA pieces

First cut every internal B edge and every heavy edge. There are q B
edges and at most h heavy edges. Work through each resulting path by
whole maximal E-runs, maintaining the current piece's hex occupancy.

- At an A boundary, its first-port repetition of the immediately
  preceding source hex is allowed. If another port of the new E-run
  would repeat a current-piece hex, cut before that whole run.
- At any other boundary, any current-piece hex collision in the new
  E-run likewise forces a cut before that whole run.

Each E-run has distinct hexes internally, so resetting occupancy before
the run resolves every collision in it. Every additional cut can be
charged to a distinct original suffix repeated-hex arrival that is not
an A or B target: it is either a non-A/B first entry or an internal E
entry. Clearing occupancy cannot invent such an old-hex arrival. If t
is the number of additional cuts, then

    t <= repeat_suffix-a-q <= r-a-q.

Each resulting piece has distinct entry ports, contains no B or heavy
edge, allows repeated-hex landings only on its retained A edges, and
otherwise uses the five permitted weight-three transitions or E. Thus
it belongs to the existing coupled SIGMA capacity relaxation. The piece
count m and retained A count a_ret satisfy

    m <= 1+q+h+t <= 1+h+r-a,
    max(0,2a+q-r) <= a_ret <= a.

The lower bound follows because only the additional cuts can remove
an A edge, and they remove at most t of them. Heavy cost h is safely
used as an upper bound on the number of heavy edges, since each such
edge costs at least one.

## Aggregate resources after splitting

For piece j, let `D_j=5Q_j-P_j` and let b_j count its non-E old-orbit
entries. All cuts were at non-E boundaries, so E-runs were never split:

    sum_j (D_j+5b_j) = Delta_suffix <= Delta_cap.

If `s=sum_j Q_j-Q_suffix` is orbit sharing between the pieces, then

    sum_j b_j = b_suffix-s <= B_rem.

These are the necessary allocation constraints. A safe suffix upper
bound therefore maximizes `sum_j C(a_j,b_j,D_j)` over

    1 <= m <= 1+h+r-a,
    max(0,2a+q-r) <= sum_j a_j <= a,
    sum_j b_j <= B_rem,
    sum_j D_j + 5 sum_j b_j <= Delta_cap,
    a_j,b_j,D_j >= 0 integers.

Here C is a proved upper capacity with exact a_j and at most the stated
b_j and D_j resources. All retained-count possibilities must be included;
fixing the count to the minimum is not justified by this audit. Missing
or incomplete/capped capacity cells require a safe fallback upper bound,
not the largest witness found so far.

## Concrete nonmonotone-deficit warning

The valid clean path

    012345 --w3--> 234015 --E--> 340125 --E--> 401235

uses four distinct ports and four distinct hexes of one E-orbit. The
first transition is a shortest weight-three full-pass connector: the
full-pass endpoint of `012345` is `501234`, and its suffix `234` overlaps
the target `234015`. Hence globally `D=1`, `b=1`, and `Delta=6`.

Take the one-port prefix `012345`. It has `Delta_pre=4`, and the boundary
enters an old orbit, so `B_rem=0`. The rebased three-port suffix has
`D_suffix=2`, `b_suffix=0`, and `Delta_suffix=2=6-4`.

Thus even this clean example has `D_suffix > D_global`. A prune using
`D_suffix <= Dcap`, `Dcap-D_pre`, or an additional subtraction of five
for the old-orbit boundary would reject a valid branch. The aggregate
Delta budget above handles it correctly.

Finally, the completed-E-run qualification is essential. Delta decreases
while an E-run is being extended. A bound computed by declaring the
current partial E-run complete is valid for the chosen non-E exit branch,
not for simultaneously pruning its still-unexplored E extensions.
