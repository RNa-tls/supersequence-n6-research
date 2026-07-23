# Multiplicity-two theorem for saturated 25-orbit covers

## Theorem

Let `C` be any 25-element family of `E`-orbits covering all 120 rotation
hexagons.  Then its hexagon multiplicities are exactly

\[
 115\times1+5\times2. \tag{1}
\]

In particular, no covered hexagon has multiplicity three or more.

## Proof

There are 125 incidences and 120 covered hexagons, so the total excess is
five.  If a hexagon had multiplicity at least three, choose any three of the
`E`-orbits meeting it.  Their excess is at most five by monotonicity.

The finite command

```powershell
python work\superperm_port_lift.py enumerate-triple-hex-seeds `
  --max-excess 5 --output outputs\triple_hex_seeds.json
```

enumerates all such triples.  It finds 2,400 labelled triples, in exactly four
left-`S_6` classes:

\[
 \{0,1,3\},\quad\{0,1,9\},\quad\{0,1,33\},\quad\{0,3,33\}. \tag{2}
\]

The first class was already rejected by the genus-core completion certificate.
The other three are rejected by exhaustive nondecomposable completion searches:

```powershell
python work\superperm_port_lift.py complete-seed-cover --seed 0,1,9 `
  --node-limit 1000000 --output outputs\triple_seed_0_1_9.json
python work\superperm_port_lift.py complete-seed-cover --seed 0,1,33 `
  --node-limit 1000000 --output outputs\triple_seed_0_1_33.json
python work\superperm_port_lift.py complete-seed-cover --seed 0,3,33 `
  --node-limit 1000000 --output outputs\triple_seed_0_3_33.json
```

They terminate with no extension after 4,721, 8,069, and 27,014 nodes,
respectively.  Thus no nondecomposable saturated cover contains a triple
hexagon.

For a decomposable saturated cover, 24 of the orbits form an exact partition,
and the 25th orbit meets five distinct hexagons.  It therefore produces
exactly five double hexagons and no triple hexagon.

Every saturated cover is either decomposable or nondecomposable, proving that
all multiplicities are at most two.  Since their total excess is five, (1)
follows. ∎

## Collision forest formulation

By (1), each double hexagon joins exactly two `E`-orbit vertices.  Contract
the 115 pendant single hexagons and replace the five double hexagons by their
five orbit--orbit edges.  The resulting five-edge multigraph has first Betti
number equal to the incidence-graph `beta`.

Combining this with `GENUS_ZERO_CERTIFICATE.md` gives the exact statement

\[
 c(f)=20\quad\Longleftrightarrow\quad
 \text{the five-edge collision multigraph is a forest}. \tag{3}
\]

This is the valid global form of the “five double hexagons” interpretation.
