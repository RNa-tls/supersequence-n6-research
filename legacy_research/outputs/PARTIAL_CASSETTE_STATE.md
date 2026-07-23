# Exact partial-cassette state for `F < 5`

This note gives an exact Markov state for the branches not covered by the
saturated-port lemma.  It does **not** claim that the state space is small, or
that this is a minimal sufficient statistic.

All statements remain conditional on the no-repeat permutation-walk
hypothesis.

## State

Let `H` range over the 120 rotation hexagons and `Q` over the 144 `E`-orbits.
For a walk prefix ending at a permutation `p`, retain:

1. `p`, the current terminal permutation;
2. `M_H ⊆ H` for every hexagon, as a six-bit rotation mask of visited
   permutations;
3. `B_Q ⊆ Q` for every `E`-orbit, as a five-bit `E`-phase mask of pass
   starts that have already occurred;
4. the counters `(F,S,H)`.

Write

\[
 \Omega_{\rm exact}=
 \bigl(p;(M_H)_{H};(B_Q)_{Q};F,S,H\bigr). \tag{1}
\]

The masks are sparse in a short prefix and are natural candidates for a
hash-consed or bit-packed implementation.  They are nevertheless part of
the mathematical state, not merely a cache.

## Sufficiency proposition

**Proposition.** Given (1) and an indecomposable tail `g_pi`, each of the
following is determined:

- whether appending `g_pi` is legal without repeating a permutation;
- the successor state;
- the increments of `F`, `S`, and the heavy excess
  `H=sum (w-3)_+`;
- the newly occupied pass-start phase, when the weight is at least two.

**Proof.** The exact visited set is reconstructed as

\[
 V=\bigcup_H M_H.
\]

The finite sequence of intermediate permutation windows produced by appending
`g_pi` is a function of `p` and `pi`.  The tail is legal precisely when all
new windows are outside `V`.  In that case their hexagon-mask bits are
inserted explicitly.  A tail of weight at least two begins a new pass, so its
terminal window inserts one phase bit of the unique `B_Q` containing that
window.  The prior pass is an abandonment exactly when `p sigma` is outside
`V`; whether the new tail starts a strand and its heavy increment are,
respectively, the predicates `w>=3` and `(w-3)_+`.  Hence every listed
quantity is a function of (1). ∎

At completion, the coordinate system is recovered without additional
history:

\[
 O=\#\{Q:B_Q\ne\varnothing\},\quad
 P=\sum_Q|B_Q|,\quad D=5O-P,
\]

and `N=S+F-O`.

## Why the phase masks alone are insufficient

The vector `(B_Q)_Q` says which windows started passes, but not which
interior rotation windows have already been traversed.  Two prefixes can have
the same terminal permutation and the same pass-start masks while differing
on an interior hexagon vertex.  A prospective tail ending at that vertex is
legal in one prefix and illegal in the other.  Thus no state which keeps only
`B_Q` can serve as the required membership oracle without an additional
theorem recovering all `M_H` from it.

This also explains the distinction between a fragment and the saturated
`F=5,D=0` branch: a fragment can split a hexagon into two or more directed
arcs, and the locations and orientations of those arcs are information in
the `M_H` layer.

## Relation to the port model

If `(F,D,N)=(5,0,0)`, every occupied orbit has all five pass-start phases.
For a fixed 25-orbit cover the hexagon masks are then forced into the cyclic
arc decomposition between consecutive ports.  The large state (1) collapses
to the 125-port permutation `f=rho E`, which is why the port-lift DP is exact
in that branch.

For `F<5` the collapse is unavailable: some `B_Q` are proper masks and the
same port cover admits genuinely different fragment chronologies.  Any
computer-assisted proof of those branches must either retain (1), or prove a
smaller quotient sufficient before using it.
