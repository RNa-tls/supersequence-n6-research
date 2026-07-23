# The F=1, D=4 port skeleton

## Scope

Assume a complete NR6 permutation walk with

\[
F=1,\qquad P=121,\qquad O=25,\qquad D=4.
\]

No hypothesis on `N` or `H` is needed in this note.  In particular, this is
not the saturated `F=5` forest calculation and does not use its port-lift
conclusion.

## Lemma 1 (one double rotation hexagon)

Exactly one of the 120 rotation hexagons contains two passes; every other
hexagon contains one pass.

**Proof.** Every rotation hexagon is visited by the completed walk, hence has
at least one maximal rotation pass.  Their total number is
`P=120+F=121`.  Thus the nonnegative excesses over one sum to one. \(\square\)

## Lemma 2 (five distinct hexagons per E-orbit)

The five phase ports of every `E`-orbit lie in five distinct rotation
hexagons.

This is a finite group lemma for the fixed actions
`E=(0 1 2 3 4)` and `sigma=(0 1 2 3 4 5)`.  It is independently checked over
all 144 E-orbits in `work/verify_f1_port_skeleton.py`.  A hand proof can be
obtained by observing that an equality
`x E^i = x E^j sigma^r` would force the position permutation
`E^{i-j}` to be a nontrivial power of the six-cycle `sigma`, impossible since
the former fixes one position and the latter fixes none unless it is the
identity.

## Theorem 3 (F=1 port-incidence forest)

Make a bipartite graph with the 25 used E-orbits on the left, the 120 rotation
hexagons on the right, and one edge for every pass start.  Then this graph is
a forest with 24 components.  Its unique degree-two hexagon joins two distinct
E-orbits; all other hexagons have degree one.

**Proof.** Lemma 1 gives one hexagon of degree two and 119 of degree one.
Lemma 2 prevents the two incident edges at the double hexagon from having the
same E-orbit endpoint.  A bipartite cycle requires at least two distinct
right-side vertices of degree at least two, so no cycle exists.  The graph has
`25+120=145` vertices and `P=121` edges, hence its number of components is
`145-121=24`. \(\square\)

Equivalently, after contracting all degree-one hexagon leaves, the collision
graph on the used E-orbits has one ordinary edge and 23 isolated vertices.

## Corollary 4 (deficit normal forms)

The 25 nonempty E-phase masks have total deficit four:

\[
\sum_{Q\text{ used}} (5-|B_Q|)=4.
\]

Hence the multiset of nonzero deficits is exactly one of

\[
[4],\ [3,1],\ [2,2],\ [2,1,1],\ [1,1,1,1].
\]

At least 21 of the 25 E-orbits are therefore full five-phase orbits.  This is
an exact structural split for later exact-state or semi-saturated analysis;
it says nothing about chronological ordering of the ports.

Modulo rotation of the five phases inside one isolated E-orbit, the partial
phase masks have one type at deficits one and four, and two types at deficits
two and three.  Combining these with the five deficit partitions gives nine
local deficit-shape families.  This is only a **local classification**:
independent E-phase rotations are not asserted to be a global symmetry of an
exact state.

## Role in the next architecture

The semi-saturated model keeps this forest skeleton, the five possible deficit
partitions, and port-to-hexagon incidence.  It must still add literal rotation
arcs, fragment repair pairing, and N-credit chronology before it can exclude
an exact walk.  Therefore the skeleton is a proved necessary condition, not a
new pruning rule for the active exact engine.
