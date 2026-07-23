# Partial-F1 reduction safety: current boundary

This note records the rules that are safe to use while the exact
`F=1,H=0,N=0` calculation is running, and equally importantly the reductions
that are **not** safe to install.

## Proven: no residual value-relabel stabilizer

The exact state retains its ordered terminal permutation `p`.  If a left value
relabeling `alpha in S_6` fixes this state, then in particular
`alpha(p_i)=p_i` for every position `i`.  Since `p` contains all six values,
`alpha` fixes every value and is the identity.  Hence the stabilizer of an
exact state under the left value action is trivial.

The current canonical-child quotient by all 720 left relabelings is therefore
already the full available **value-relabel** quotient.  A further quotient
would need a different, proved symmetry (for example a normalizer of the full
right-tail transition system); none is assumed here.

## Not proven, and not installed: visited-mask dominance

For masks with `V(x) subset V(y)`, neither state dominates the other merely by
inclusion.  A completion suffix from `y` leaves `V(y)\\V(x)` unvisited if
replayed from `x`; a completion suffix from `x` can collide with precisely
that difference if replayed from `y`.  Thus inclusion alone does not preserve
existence of a completion.

Any usable dominance relation must supply an explicit extension simulation or
a coverage compensation certificate.  Until then, memoization remains exact
state equality after the existing left-`S_6` canonicalization.

## Architecture for F=2,3,4: semi-saturated port envelope

For a putative `L<=871` counterexample define `k=O-24`.  Every coordinate
tuple must obey

\[
 P=120+F,\quad O=24+k,\quad D=5k-F,\quad
 S=24+k-F+N,\quad k+N+H\le4.
\]

The semi-saturated model keeps the selected phase ports `(Q,j)` of the 144
five-point E-orbits.  It imposes only the following **necessary** conditions:

1. exactly `P` selected ports in `O` nonempty E-orbits with deficit `D`;
2. every one of the 120 rotation hexagons receives at least one selected port;
3. the total multiplicity excess over those hexagons is exactly `F`.

It deliberately omits chronological ordering, literal collisions, rotation
arc partitioning, the `N` credit history, repair pairing, and deep-tail
weights.  Therefore an infeasible port instance rules out an exact walk, but
a feasible port instance is only a relaxation witness.

`work/superperm_semisaturated_model.py` implements validation of this
envelope and a read-only forest control.  It is not an enumerator.
