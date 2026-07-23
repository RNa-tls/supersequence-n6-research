# Execution log — 2026-07-22

All commands use the bundled Python runtime and
`work/superperm_port_lift.py`.

## Reproducible finite checks

```powershell
python work\superperm_port_lift.py basic
python work\superperm_port_lift.py find-partition --limit 100000 --output outputs\exact_partitions_100000.json
python work\superperm_port_lift.py classify-partitions outputs\exact_partitions_100000.json --output outputs\partition_classes_all.json
python work\superperm_port_lift.py generate-standard 6 --output outputs\standard_6.txt
python work\superperm_port_lift.py verify-word outputs\standard_6.txt --output outputs\standard_6_verification.json
```

Results:

* finite-group checksum: `3f13302d69d46e8c09555e951d48c3e80f5b76e7db1dae0a50cf2421106edf3b`;
* 10,068 labelled exact partitions, 29 left-(S_6) classes;
* exact-partition file SHA-256:
  `C476CF4A03936031F98B7C50619033A2FE34A64D5461B32028A66E30664B4EB9`;
* standard (n=6) word length 873, SHA-256
  `5dad2ee91a1fa8d98adc595a17c61241b58929d59a3c4aedd9983469c00c4de6`;
* standard coordinate output:
  ((F,S,H,O,D,N,k)=(0,24,6,24,0,0,0)).

## Exact-partition-plus-one subclass

For all 29 partition representatives and all 120 possible added (E)-orbits:

* 248 left-(S_6) classes have (c(f)=20);
* every one fails the exact port-lift DP at (H\le3);
* the rest have (c(f)=22) or (24), so need more than 19 deep exits.

The full DP result is `lift_classes_all_F5N0H3.json`, SHA-256
`A2A1FB941D272D4E090D7AC62FE4C8D6ADD36FFD1563AE420F5F47DE4BF68B5F`.

## Deliberate falsification of the normal form

`random_nonpartition_cover.json` gives a 25-orbit cover with multiplicity
(115\times1+5\times2) and no removable orbit that leaves an exact
24-partition.  Hence the exact-partition-plus-one result cannot be promoted
to all saturated covers without a new argument.

## Experimental, not proof

* 1,000 independently sampled general 25-orbit covers: 330 had (c(f)=20),
  548 had (c(f)=22), and 122 had (c(f)=24).  All 330 (c(f)=20) samples
  failed the port-lift DP with (H\le3).
* A bounded exact search of non-partition covers (orbit 0 fixed) found 2,906
  witnesses before a 10,000,000-node cap.  Their 1,290 left-(S_6) classes
  all had (c(f)=22) or (24), but the search was deliberately incomplete.

Neither experimental statement is a lower-bound proof.

## General saturated covers: sound quotient search

The rule “retain a partial cover only if it is already lexicographically
least” is unsound: a noncanonical partial subset can extend to a canonical
complete cover.  The command below instead performs **canonical
augmentation**.  It adds an orbit covering the least uncovered hexagon and
then maps the whole child set to its left-`S_6` canonical image.  An extension
of a child is carried to an extension of that image by the same
value-relabeling, so no isomorphism class is lost.

```powershell
python work\superperm_port_lift.py enumerate-nonpartition-covers `
  --quotient --limit 1000 --node-limit 1000000 `
  --output outputs\nonpartition_covers_quotient_1000_v3.json
python work\superperm_port_lift.py classify-covers `
  outputs\nonpartition_covers_quotient_1000_v3.json `
  --output outputs\nonpartition_covers_quotient_1000_v3_classes.json
python work\superperm_port_lift.py lift-cover-classes `
  outputs\nonpartition_covers_quotient_1000_v3.json `
  outputs\nonpartition_covers_quotient_1000_v3_classes.json --heavy 3 `
  --output outputs\nonpartition_covers_quotient_1000_v3_lift.json
```

This run reached the one-million-node cap and is therefore **incomplete**.
Before the cap it produced 797 non-isomorphic nonpartition 25-orbit covers.
Their exact cycle distribution was

\[
797 = 704\;(c(f)=22) + 93\;(c(f)=24).
\]

Every one fails the saturated-port lemma before the port-lift DP.  This is
evidence only, not a complete enumeration of the general cover space.

## Connectivity diagnostic: falsified as the proposed invariant

The suggested explanation “the cycle-transition graph is disconnected” was
tested directly on the 330 `c(f)=20` covers in the independent random sample
of 1,000 general covers.  At heavy budget three, every one of the 330
cycle-transition graphs has one weak component and one strongly connected
component, both of size 20; each graph has 400 directed transition arcs.
Nevertheless all 330 exact port-lift DPs fail.  Their largest reachable
cycle-subset sizes are 9 through 14 (the modal value is 13).

Thus ordinary connectivity, even strong connectivity, is **not** the missing
algebraic obstruction.  Any invariant that closes this branch must retain
the forced lifted port `f^{-1}(t)` in (2), rather than quotienting only to the
20 cycle labels.

## Port-incidence surface identity

`PORT_SURFACE_INVARIANT.md` proves the exact Euler identity

\[
c(f)=20+2\beta(B)-2g(B)
\]

for the ribbon graph of a saturated cover.  A finite check of all 3,480
exact-partition-plus-one skeletons found `(c,beta)=(20,0)`, `(22,1)`, and
`(24,2)` with multiplicities 500, 2,480, and 500 respectively.  The same
genus-zero pattern occurred in the 1,000-cover random sample.  This supports
but does not prove a global genus-zero conjecture, so the enumeration does
not prune positive-genus covers.

## Genus-zero theorem: completed finite core certificate

The last sentence of the preceding section has now been superseded by the
computer-assisted proof in `GENUS_ZERO_CERTIFICATE.md`.  The key finite
calculation is:

```powershell
python work\superperm_port_lift.py enumerate-positive-genus-cores `
  --max-size 5 --max-excess 5 `
  --output outputs\positive_genus_cores_canonical.json
```

It finds exactly three minimal connected positive-genus core classes:
`{0,1,3}`, `{0,1,33,138}`, and `{0,1,9,13}`.  Exact nondecomposable
completion searches for these roots terminate after 717, 4, and 3 nodes and
find no cover.  Combined with the already exhaustive exact-partition-plus-one
check, this proves genus zero for every saturated 25-orbit cover and upgrades
the formula to `c(f)=20+2 beta`.

## Expanded general-cover/lift sample

Four independent depth-two canonical augmentation branches were run to a
five-million-node cap each.  Their 5,462 raw leaves merge to 1,713 left-`S_6`
classes; this remains an incomplete search.  The genus/cycle distribution is

\[
 284\;(c,\beta,g)=(20,0,0),\quad
 1181\;(22,1,0),\quad
 248\;(24,2,0).
\]

All 284 forest (`c=20`) classes fail the exact port-lift DP at `H<=3`; their
maximum reachable lift-cycle counts lie between 9 and 14.  These data support
the remaining forest-cover obstruction but are not a complete enumeration.
