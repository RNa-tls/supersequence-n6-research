# Forest-only canonical augmentation: scope, proof, and certificate format

## Purpose

This note specifies the exhaustive finite search used for the saturated
incidence branch

\[
(F,D,N)=(5,0,0),\qquad H\leq 3.
\]

It is **not** a proof about full superpermutation words by itself.  It
enumerates the possible 25-`E`-orbit port skeletons in this branch and then
applies the exact port-lift *necessary-condition* DP.  The word-level
no-repeat hypothesis and the reduction to this branch remain separate.

The implementation is
[`superperm_port_lift.py`](../work/superperm_port_lift.py), commands
`forest-depth-seeds`, `enumerate-forest-covers`, and
`merge-forest-certificates`.

## Finite input theorems

Two prior computer-assisted finite theorems are used here.

1. Every saturated 25-`E`-orbit cover has multiplicities
   \(115\times 1+5\times2\); in particular it has no triple-covered
   hexagon.  See `MULTIPLICITY_TWO_THEOREM.md`.
2. Every saturated cover has ribbon genus zero.  Hence
   \[
   c(f)=20+2\beta,
   \]
   where \(\beta\) is the incidence-graph cycle rank and
   \(f=\rho E\) is the deterministic weight-two port successor.  See
   `GENUS_ZERO_CERTIFICATE.md`.

With no triples, contract each singly covered hexagon and replace each of the
five double hexagons by an edge joining its two `E`-orbits.  The resulting
five-edge collision multigraph \(G_{\rm col}\) has cycle rank \(\beta\).
Consequently

\[
c(f)=20\quad\Longleftrightarrow\quad G_{\rm col}\text{ is a forest}.
\]

The port-lift branch with 19 deep exits can only possibly survive when
\(c(f)=20\).  It is therefore complete to enumerate only collision forests.

## Search state and invariant

A partial state is the deterministic triple

\[
\bigl(C,\mathcal H_{\rm double},G_{\rm col}\bigr),
\]

where \(C\) is a set of selected `E`-orbits, a hexagon is in
\(\mathcal H_{\rm double}\) exactly when it is currently met twice, and its
two incident orbits give the corresponding edge of \(G_{\rm col}\).

The code reconstructs the latter two objects from `C` after every
canonicalization.  This is intentional: carrying orbit labels through a
value-relabeling canonicalization would be unsound.

Every generated child is rejected immediately if one of the following holds:

1. some hexagon has multiplicity at least three;
2. the excess \(5|C|-|\bigcup K(q)|\) exceeds five;
3. there are more than five collision edges;
4. adding a collision edge creates a loop, parallel-edge cycle, or ordinary
   cycle in \(G_{\rm col}\);
5. the still-uncovered hexagons cannot be covered by the remaining five-set
   slots.

At depth 25 a leaf is accepted exactly when it covers all 120 hexagons and
has excess five.  If depth 24 already covers all 120 hexagons, the search
extends it by each remaining orbit.  This retains the
exact-partition-plus-one positive-control family instead of silently dropping
it.

## Completeness lemma

Let \(\mathcal C\) be a saturated forest cover.  Every partial subfamily
\(A\subseteq\mathcal C\) satisfies the five conditions above:

* it cannot have a triple because \(\mathcal C\) has none;
* its collision graph is a subgraph of the final forest;
* its excess is at most the final excess five;
* each remaining member covers at most five still-uncovered hexagons, giving
  the capacity inequality.

At a canonical partial state `A`, choose one least-constrained uncovered
hexagon \(h(A)\), and branch over every unselected `E`-orbit through it.  If
`A` is contained in some value-relabeling of \(\mathcal C\), one member of
that relabeled cover still covers \(h(A)\).  After adjoining it, apply a
value relabeling that sends the child to its lexicographically least
left-\(S_6\) image.  The same relabeling transports the as-yet unselected
members of \(\mathcal C\), so the canonical child remains extendible.
Induction reaches a canonical image of \(\mathcal C\).

The exceptional full depth-24 case is also complete: its 24 selected orbits
form an exact partition, and the remaining 25th orbit is tried explicitly.

Thus every saturated forest cover is reached.  A memoized set of canonical
masks removes repeated construction histories.

### Why this does not use a strict canonical-parent test

The implementation uses **canonical child + memoization**, not the stronger
test `parent(child) == current_state`.  With least-uncovered-hexagon
branching, a canonical deletion selected by a McKay-style parent rule need
not contain the current branching hexagon.  Combining that test naively with
the Algorithm-X column rule can therefore remove the only construction order
of a valid cover.  Canonical child + memoization is the proved safe condition
here; it is an isomorph-free enumeration even though it may have more than
one construction history before memoization.

## Leaf certificate

Each leaf JSON record contains:

* the canonical 25-orbit representative and a stable cover SHA-256;
* whether it is an exact-partition-plus-one control or first becomes full at
  depth 25;
* all five double hexagons and the collision-forest component partition;
* the full cycle decomposition of \(f=\rho E\);
* exact reachable-state summaries for heavy budgets \(H=0,1,2,3\), including
  the maximum number of `f`-cycles reached and the failure reason;
* shared transition diagnostics at \(H=3\), ribbon data, and the SHA-256 of
  the code that produced the certificate.

The \(H=0,1,2,3\) summaries are exact.  The DP is executed once at budget
three while retaining the minimum cost of every `(cycle subset, entry port)`
state.  Filtering those states by cost at most \(h\) is exactly the DP at
budget \(h\); this equivalence is regression-tested against four separate
DP runs on an exact-partition-plus-one control.

## Reproducible completion protocol

```powershell
$py = 'C:\Users\parks\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py work\superperm_port_lift.py basic
& $py work\superperm_port_lift.py forest-depth-seeds --depth 2 `
  --output outputs\forest_depth2_seeds.json
```

Run every emitted seed with `--node-limit 0` and no `--limit`; zero means
unlimited in the forest-only command.  Preserve the JSON result of every
branch, including `node_count`, `completed`, and `prune_counts`.  Only merge
files for which `completed` is true:

```powershell
& $py work\superperm_port_lift.py merge-forest-certificates `
  outputs\forest_branch_*.json --output outputs\forest_all_classes.json
```

The final merged output is a computer-assisted certificate for the finite
forest-skeleton enumeration.  If every `H=3` field says
`complete_lift_exists: false`, it closes the **port-lift necessary-condition
subcase** \((F,D,N)=(5,0,0),H\le3\).  It does not by itself close the other
\(k=1\) slabs with \(F<5\), nor convert the conditional no-repeat result
into an unconditional superpermutation theorem.

Before interpreting a completed output, replay it with the separate
incidence verifier:

```powershell
& $py work\verify_forest_certificates.py outputs\forest_all_classes.json `
  --output outputs\forest_all_classes_verified.json
```

This verifier independently rebuilds the `S_6` incidence system, checks
canonicality, the 115/5 multiplicity profile, the collision forest, and every
serialized `f`-cycle.  It then optionally replays the shared exponential
port-lift DP; that last replay is explicitly not an independent second DP
implementation.
