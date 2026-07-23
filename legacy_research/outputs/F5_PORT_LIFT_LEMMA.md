# Saturated-port lemma for the `(F,D,N)=(5,0,0)` branch

This note uses the right-action conventions implemented and independently
checked in `work/superperm_port_lift.py`.  Its conclusion is conditional on
the **no-repeat permutation-walk hypothesis**: the 720 permutation windows
of the candidate word are all distinct.

The scope is deliberately narrow:

\[
 n=6,\qquad F=5,\qquad D=0,\qquad N=0.
\]

It is a necessary-condition lemma for a hypothetical word with
`L <= 871`; it is not yet a proof that this branch is empty.

## 1. Saturation and ports

The identities

\[
 P=120+F,\qquad D=5O-P,\qquad N=S+F-O
\]

give

\[
 P=125,\qquad O=25,\qquad S=20.
\]

Each used `E`-orbit has at most five pass starts.  Since `P=5O`, every one
of the 25 used `E`-orbits has exactly five.  Call these 125 pass starts
**ports** and denote their set by `U`.

Every rotation hexagon contains a port: every permutation in that hexagon is
visited, and the maximal rotation pass containing it has its start in that
same hexagon.  Thus the 25 full `E`-orbits give 125 port--hexagon incidences
on the 120 rotation hexagons.

Nothing here says that 24 of the 25 `E`-orbits form an exact partition.  In
fact `outputs/random_nonpartition_cover.json` is an incidence-level
counterexample: it has 115 singly and five doubly covered hexagons, but no
one of its 24-subsets is an exact partition.  Consequently all statements
below are phrased for an arbitrary saturated 25-orbit cover.

## 2. The intrinsic weight-two permutation

For a rotation hexagon `H`, cyclically order the ports in `U ∩ H` by the
rotation `sigma`.  Let `rho(u)` be the next port in that cyclic order.  The
rotation pass beginning at `u` has the forced length equal to the clockwise
distance from `u` to `rho(u)`; otherwise it either repeats a permutation or
passes through another pass start.  Hence its endpoint is

\[
 b=u\sigma^{\ell(u)-1}=\rho(u)\sigma^{-1}.
\]

The unique weight-two continuation has target

\[
 b\tau=\rho(u)\sigma^{-1}\tau=\rho(u)E,
\]

because `sigma^{-1} tau=E`.  Define

\[
 f(u)=\rho(u)E. \tag{1}
\]

Both factors are permutations of `U`: `rho` permutes ports hexagon by
hexagon, while `E` permutes the five ports of every full `E`-orbit.  Thus
`f` is a permutation of all 125 ports.  This construction is valid for every
hexagon split, including three or more arcs; no false “24-partition plus one”
normal form is used.

## 3. Cycle obstruction

Let `c(f)` be the number of cycles of `f`.

**Theorem.** In the stated branch, `c(f) >= 20` and `c(f)` is even.  If a
no-repeat walk realizing this branch exists, then `c(f)=20`.

**Proof.** Before the port switches `rho`, the restriction of `E` is 25
disjoint 5-cycles.  If a hexagon has `m_H` ports, the corresponding cycle of
`rho` has transposition length `m_H-1`.  Since

\[
 \sum_H(m_H-1)=125-120=5,
\]

`rho` is a product of five transpositions.  Right multiplication by one
transposition changes the number of cycles by at most one, so `c(f) >= 20`.
Moreover `E|_U` is even, while

\[
 \operatorname{sgn}(\rho)=(-1)^5=-1.
\]

Therefore `f` is odd.  On 125 points,
`sgn(f)=(-1)^{125-c(f)}`, so `c(f)` is even.

There are exactly `S-1=19` deep joints (weight at least three) between
successive passes.  If all ports of one `f`-cycle used their `f`-successor,
that directed cycle would be a subcycle of the one Hamilton path; this is
impossible except that the single terminal port has no outgoing transition.
Thus at least `c(f)-1` ports require a deep joint, so `c(f)-1 <= 19`.
Together with `c(f) >= 20` and parity, this forces `c(f)=20`.  ∎

## 4. Exact port lift

There are 20 `f`-cycles, exactly 19 deep exits, and one terminal exit.
Consequently there is exactly one exit in every `f`-cycle.  If the path enters
an `f`-cycle at `v`, all its other transitions inside that cycle are forced:
it follows `f` until the unique exit `f^{-1}(v)`.

For a deep tail taking an exit `u` to a port `t`, the forced exit of the next
cycle is therefore

\[
 u_{\mathrm{next}}=f^{-1}(t). \tag{2}
\]

The port-lift dynamic programme enumerates the paths induced by (2): it
chooses a starting `f`-cycle, visits each of the other 19 cycles once by an
allowed indecomposable deep tail, and records the accumulated heavy excess
`sum (w-3)_+`.  In particular, it retains the forced *port* lift, which is
strictly stronger than merely asking for a Hamilton path in the 20-vertex
cycle-transition graph.  Failure with budget `H <= 3` is therefore a valid
necessary-condition obstruction for the `(5,0,0)` branch.

The DP remains a relaxation of a full word: it does not encode the chronology
which pairs fragment cuts and repairs.  Consequently success would not prove
a walk exists; it merely means this necessary condition has not ruled the
cover out.

## 5. Completed finite checks and current gap

The exact-partition-plus-one subclass is complete:

- all 10,068 labelled 24-orbit exact partitions were enumerated;
- they have 29 orbits under the genuine left value-relabeling action of
  `S_6`;
- after adding a 25th orbit, 248 left-`S_6` classes have `c(f)=20`;
- all 248 fail the exact port-lift DP at heavy budget `H <= 3`.

All other pairs have `c(f)=22` or `24`, and fail already by the cycle
theorem.  This is a computer-assisted proof for the
**exact-partition-plus-one subclass only**.

`GENUS_ZERO_CERTIFICATE.md` now gives the additional exact characterization

\[
 c(f)=20\quad\Longleftrightarrow\quad\beta(B)=0,
\]

where `B` is the port-incidence graph.  Hence only forest covers can survive
to this lift DP.  The code uses sound left-`S_6` canonical augmentation rather
than unsafe depth-wise lexicographic pruning.  A complete enumeration of the
remaining forest cover classes, followed by the same exact port lift, is
still required to close the full `(F,D,N)=(5,0,0)` branch.
