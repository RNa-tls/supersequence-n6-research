# Sound symmetry reduction for general 25-orbit covers

This note records exactly what the `--quotient` mode in
`work/superperm_port_lift.py` proves.  It is included because a tempting
alternative — reject every partial set which is not lexicographically least
in its `S_6` orbit — is not complete.

## Objects and group action

Let `Q` be the 144 `E`-orbits and let `K(q)` be the five rotation hexagons
met by `q`.  A saturated cover is a 25-element subset `C ⊆ Q` satisfying

\[
 \left|\bigcup_{q\in C}K(q)\right|=120,
 \qquad \sum_{q\in C}|K(q)|=125.
\]

Value relabeling by `a ∈ S_6` commutes with all right position actions, so it
acts on `Q` and preserves every incidence `H ∈ K(q)`.  For a finite subset
`A ⊆ Q`, let

\[
 \operatorname{can}(A)=
 \min_{a\in S_6} aA
\]

where sets are compared by their increasing lists of orbit identifiers.

The implementation evaluates this minimum without assuming an additional
position or reversal symmetry.  For a nonempty `A`, it is enough to examine
the `5|A|` group elements which send one selected orbit to orbit 0: a
lexicographically least image must contain orbit 0, and the stabilizer of an
`E`-orbit in this action has order five.  A 500-random-mask direct comparison
against all 720 group elements is part of the executable regression check.

## Canonical-augmentation lemma

At a canonical partial set `A`, choose the least uncovered hexagon `h(A)`.
For each unselected `q` with `h(A) ∈ K(q)`, recurse on

\[
 \operatorname{can}(A\cup\{q\}). \tag{1}
\]

Prune only by the monotone, isomorphism-invariant conditions

\[
 5|A|-\left|\bigcup_{q\in A}K(q)\right|\le5,
 \qquad
 \left\lceil\frac{120-\left|\bigcup_{q\in A}K(q)\right|}{5}\right\rceil
 \le25-|A|,
\]

and stop when a cover becomes full before depth 25.

**Lemma.** If a saturated 25-orbit cover exists, this recursion visits a
canonical image of it.

**Proof.** Let `C` be a saturated cover and suppose the recursion has reached
a state `A` contained in some relabeling of `C`.  Since `h(A)` is uncovered,
some `q ∈ C\A` covers it.  Equation (1) produces
`A' = g(A ∪ {q})` for a relabeling `g`.  The set `gC` is again a saturated
cover and contains `A'`.  Thus an extendible state always has an extendible
canonical child.  Induction on the depth reaches a canonical image of a
25-element cover.  The displayed pruning conditions hold for every subset
of a saturated cover because both its excess and its maximum possible future
coverage are monotone.  A full cover before depth 25 would contain a
24-orbit exact partition, hence is deliberately outside the nonpartition
search. ∎

The recursion can reach one final orbit class by more than one construction
history; a memoized set of canonical masks removes those duplicates.  When
the search is divided at a fixed depth for parallel execution, output classes
must be canonicalized and deduplicated again at the merge.  This affects only
runtime, not completeness.

## Status

The reduction is a proof of *soundness of the enumeration method*, not a
claim that the currently configured node cap has exhausted the search.  The
current `F=5` general-cover run is therefore labelled incomplete until every
canonical branch has terminated without a surviving port lift.
