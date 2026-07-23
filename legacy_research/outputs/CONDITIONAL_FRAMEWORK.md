# Conditional framework and proof boundary

## Hypothesis NR6

Every shortest six-symbol superpermutation admits a realization in which its
720 permutation occurrences are all distinct.  Equivalently, the occurrence
sequence is a Hamilton path in the directed overlap transition system on
(S_6).

This hypothesis is **assumed**, not proved here and not attributed here to a
named theorem.  All lower-bound statements below are conditional on NR6.

## Exact coordinate identities under NR6

For a complete walk, let (P,F,S,H,O,D,N,k) have the meanings established in
the research record.  Then

[
P=120+F,qquad D=5O-P,qquad N=S+F-O,qquad k=O-24,

]

and therefore

[
D=5k-F,qquad
\operatorname{cost}=F+S+H=O+N+H=24+k+N+H,

]

[
L=843+\operatorname{cost}=867+(k+N+H).

]

Thus the desired conditional bound (L\ge872) is exactly

[
k+N+H\ge5.

]

## Already rigorous inputs

* Theorem A: (O\le S+F) (equivalently (N\ge0)).
* The blocked-(w=2) lemma from (sigma^{-1}	au=E).
* The direct (R)-flip obstruction (w\ge4).
* The complete-cassette (F=0) result (H\ge6), hence (L\ge873), in its
  stated scope.
* `F5_PORT_LIFT_LEMMA.md`: a general, normal-form-free reduction for the
  saturated ((F,D,N)=(5,0,0)) branch.

## What the new computer calculations prove

The incidence system of 144 (E)-orbits against 120 rotation hexagons has
exactly 10,068 labelled 24-orbit exact partitions, in 29 left-(S_6) orbits.
For the subclass “one such exact partition plus one (E)-orbit”, every
(c(f)=20) port-lift representative fails for heavy budget (H\le3); all
other representatives have (c(f)>20) and fail earlier.

This is a complete computer-assisted theorem for that subclass.  It is not
yet a theorem for all ((F,D,N)=(5,0,0)) walks, because a 25-orbit cover need
not contain a 24-orbit exact partition.
