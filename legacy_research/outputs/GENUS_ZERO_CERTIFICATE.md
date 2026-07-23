# Computer-assisted genus-zero theorem for saturated 25-orbit covers

This note proves the genus-zero statement that was previously only an
experimental observation.  It is a finite theorem about the `E`--rotation
incidence system; it does not use a superpermutation word or the no-repeat
hypothesis.

## Theorem

Let `C` be any set of 25 `E`-orbits whose 125 incidences cover all 120
rotation hexagons.  Give the port-incidence graph its intrinsic cyclic orders:
`E` at black (`E`-orbit) vertices and rotation order at white (hexagon)
vertices.  Then its ribbon surface has

\[
 g(C)=0.
\]

Consequently, with `beta(C)` its incidence-graph first Betti number and
`f=rho E` its intrinsic weight-two port permutation,

\[
 \boxed{c(f)=20+2\beta(C).} \tag{1}
\]

In particular,

\[
 c(f)=20\quad\Longleftrightarrow\quad\beta(C)=0,
\]

so the twenty-cycle port-lift case is exactly the case in which the
port-incidence graph is a forest.

## Preliminary Euler identity

`PORT_SURFACE_INVARIANT.md` proves, before imposing genus zero,

\[
 c(f)=20+2\beta(C)-2g(C). \tag{2}
\]

Thus it remains only to exclude a positive-genus saturated cover.

## Core reduction

For a family `A` of `E`-orbits, write

\[
 t(A)=5|A|-|\{\text{hexagons met by }A\}|.
\]

For a saturated cover, `t(C)=5`, and `t(A)<=5` for every subfamily `A`.

Suppose a saturated cover had positive genus.  Iteratively delete pendant
vertices and their incident edges from one positive-genus ribbon component.
Deleting a pendant ribbon edge removes a disc-with-band tongue and preserves
genus.  The resulting 2-core therefore still has positive genus.

Every white vertex in this 2-core had degree at least two in the original
incidence graph.  If there are `r` such white vertices, their total original
degree is

\[
 \sum d_H=r+\sum(d_H-1)\le r+5\le10.
\]

The black vertices of the 2-core have degree at least two, so their number is
at most five.  Let `A` be those black vertices.  Restoring the incident
pendant trees cannot decrease genus, hence the induced ribbon graph on this
connected family `A` still has positive genus, with

\[
 |A|\le5,\qquad t(A)\le5. \tag{3}
\]

Thus every counterexample contains a connected positive-genus core satisfying
(3).

## Exhaustive finite core classification

The command

```powershell
python work\superperm_port_lift.py enumerate-positive-genus-cores `
  --max-size 5 --max-excess 5 `
  --output outputs\positive_genus_cores_canonical.json
```

enumerates connected families up to genuine left value-relabeling by `S_6`.
It begins with orbit 0 (transitivity), adds only an orbit sharing an already
met hexagon (connectedness), canonicalizes after every addition, and keeps
only `t<=5`.  This is complete for the families in (3).

The complete class counts are:

| number of E-orbits | connected classes | positive-genus classes |
|---:|---:|---:|
| 1 | 1 | 0 |
| 2 | 3 | 0 |
| 3 | 32 | 1 |
| 4 | 542 | 29 |
| 5 | 7,121 | 0 |

After deletion of every proper positive-genus subfamily, exactly three
minimal classes remain:

\[
 \{0,1,3\},\qquad \{0,1,33,138\},\qquad \{0,1,9,13\}. \tag{4}
\]

Their invariants are respectively

\[
 (|A|,t,\beta,g,c)=(3,4,2,1,1),\quad(4,5,2,1,1),\quad(4,5,2,1,1).
\]

## Extension certificates

It remains to ask whether a class in (4) can occur inside a **nondecomposable**
saturated cover (one which first covers all 120 hexagons at its 25th orbit).
The command `complete-seed-cover` is an exact completion search.  At every
node it chooses an uncovered hexagon, tries every unused `E`-orbit covering
it, and rejects only when the monotone excess exceeds five or there are too
few remaining five-sets to cover the uncovered hexagons.  Therefore every
nondecomposable saturated extension is visited.

```powershell
python work\superperm_port_lift.py complete-seed-cover --seed 0,1,3 `
  --node-limit 1000000 --output outputs\core_completion_0_1_3.json
python work\superperm_port_lift.py complete-seed-cover --seed 0,1,33,138 `
  --node-limit 1000000 --output outputs\core_completion_0_1_33_138.json
python work\superperm_port_lift.py complete-seed-cover --seed 0,1,9,13 `
  --node-limit 1000000 --output outputs\core_completion_0_1_9_13.json
```

The searches terminate, without touching their node cap, after respectively

\[
 717,\qquad4,\qquad3
\]

nodes and produce no extension.  Left `S_6` symmetry handles every image of
the three classes.

The only covers omitted by this completion search are decomposable covers,
which already contain a 24-orbit exact partition.  Those form exactly the
exact-partition-plus-one family.  The complete enumeration of 10,068 labelled
partitions (29 left-`S_6` classes) and all possible added orbits was checked
separately; all of their ribbon genera are zero.

By the core reduction, a positive-genus saturated cover would contain one of
the three nonextendible classes in (4), unless it were decomposable; the latter
case has just been checked.  This contradiction proves `g(C)=0`, and (1)
then follows from (2). ∎

## Scope

This theorem closes the genus question and makes `beta>0` a sound pruning
rule for the `(F,D,N)=(5,0,0)` port-lift branch.  It does **not** by itself
prove that every forest cover fails the port-lift DP, nor does it address the
partial-orbit branches `F<5`.
