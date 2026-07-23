# The port-incidence ribbon surface

This is the topological identity underlying the genus-zero certificate in
`GENUS_ZERO_CERTIFICATE.md`.

## Ribbon graph

Let `U` be the 125 ports of a saturated cover.  Form the bipartite incidence
graph `B` whose black vertices are the 25 occupied `E`-orbits, whose white
vertices are the 120 rotation hexagons, and whose 125 edges are the ports.
Every white vertex has positive degree.  Give black vertices the cyclic order
induced by `E`, and white vertices the cyclic order induced by rotation
`sigma`.

Let `beta(B)=|E(B)|-|V(B)|+C(B)` be its first Betti number, where `C(B)` is
the number of connected components.  Since `|E(B)|=125` and
`|V(B)|=25+120`,

\[
 \beta(B)=C(B)-20. \tag{1}
\]

The cyclic orders thicken `B` to an oriented ribbon surface.  Its black
vertex permutation is `E|_U`; its white vertex permutation is `rho`; and,
up to replacing all cyclic orders by their inverses, its face permutation is
the port successor

\[
 f=\rho E.
\]

Consequently the number of faces is exactly `c(f)`.  Applying Euler's formula
componentwise gives the identity

\[
 25+120-125+c(f)=2C(B)-2g(B),
\]

or equivalently

\[
 \boxed{\;c(f)=20+2\beta(B)-2g(B).\;} \tag{2}
\]

Here `g(B)` is the total genus of the ribbon surface.  This derivation uses
only the port incidences and the two intrinsic cyclic orders; it is independent
of pass chronology.

## Consequences that are proved

- Equation (2) explains the even parity of `c(f)` a second way.
- If the collision/incidence graph is a forest (`beta(B)=0`), then necessarily
  `c(f)=20` and the saturated-port lift is the sharp 20-cycle case.
- Before genus zero is proved, a putative `c(f)=20` nonforest cover would
  have to satisfy `g(B)=beta(B)`.

## Finite checks

For all 3,480 exact-partition-plus-one skeletons from the 29 left-`S_6`
partition representatives, the observed pairs were

\[
 (c(f),\beta(B))=(20,0)\;[500],\quad(22,1)\;[2480],\quad(24,2)\;[500].
\]

The same equality `c(f)=20+2 beta(B)` held in the independent random sample
of 1,000 general covers: 330, 548, and 122 samples respectively had the three
pairs above.  These were initially only evidence.  The small-core completion
argument in `GENUS_ZERO_CERTIFICATE.md` now supplies the missing proof for
all saturated covers.

## Use in the remaining search

The genus-zero theorem upgrades the identity to the exact formula

\[
c(f)=20+2\beta(B).
\]

Thus `beta>0` is now a sound immediate rejection of a 20-cycle port-lift
candidate, while `beta=0` is exactly the forest case to which the lift DP
must be applied.
