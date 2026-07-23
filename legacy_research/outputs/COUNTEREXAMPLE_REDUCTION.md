# Conditional reduction of a putative length-871 counterexample

Assume the no-repeat permutation-walk hypothesis.  Let `F,S,H,O,P,D,N,k`
have the meanings fixed in the research record, with `H=sum (w-3)_+` and
`k=O-24`.

The following are identities or previously proved inequalities:

\[
 P=120+F,\qquad D=5O-P=5k-F,\qquad N=S+F-O\ge0,
\]

\[
 \operatorname{cost}=F+S+H=O+N+H=24+k+N+H,
\]

and hence

\[
 L=843+\operatorname{cost}=867+(k+N+H). \tag{1}
\]

Therefore a conditional counterexample to `L>=872` must satisfy

\[
 k+N+H\le4. \tag{2}
\]

The proved `F=0` full-cassette result rules out `k=0` in this range.  Also
`D>=0` gives `F<=5k`.  Thus only the following finite coordinate slabs
remain:

| `k` | fragment range | residual budget |
|---:|:---|:---|
| 1 | `1 <= F <= 5` | `N+H <= 3` |
| 2 | `1 <= F <= 10` | `N+H <= 2` |
| 3 | `1 <= F <= 15` | `N+H <= 1` |
| 4 | `1 <= F <= 20` | `N=H=0` |

For every row,

\[
 O=24+k,\qquad S=24+k-F+N. \tag{3}
\]

The saturated case treated by `F5_PORT_LIFT_LEMMA.md` is only the corner

\[
 (k,F,D,N)=(1,5,0,0),\qquad H\le3.
\]

It is strategically useful because all 25 occupied `E`-orbits are full and
the exact port model applies.  It must not be substituted for the other rows
of the table: when `F<5` or `D>0`, an occupied orbit can have a proper phase
mask and fragment chronology is not determined by the cover alone.  Those
rows require the exact partial-cassette state in
`PARTIAL_CASSETTE_STATE.md`, or a separately proved quotient of it.

Thus a complete conditional proof of `L_6>=872` consists of (i) closing the
saturated corner by an exhaustive general-cover/lift computation or a new
invariant, and (ii) ruling out the remaining three slabs and the unsaturated
part of `k=1` with a state-space proof.  None of these unfinished tasks may be
silently inferred from the saturated computation.
