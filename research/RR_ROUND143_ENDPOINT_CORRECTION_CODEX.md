# Dirty-seam endpoint capacity correction

## Exact domain and the identity restriction

Use the fixed first-occurrence representative and all definitions of
Round142, RouteB. In particular S counts weight>=3 joints, not strands;
G=P-120, k=O-24, D_phi=5k-G, z=G-c=2g+d, Z=z-D2 and
B*=sum b_j+s. The identity is L=867+k+Z+H+B*. It cannot be strengthened
by adding a positive term to its identical right side. The new theorem
restricts the configurations realizing these same resources.
For lengths869,870,871 the exact sums are respectively2,3,4. They have
10,20,35 weak-composition budgets; expanding genus, sharing and heavy
counts gives92,427,1548 necessary arithmetic rows. These are not realizable
cover counts. R<=5t-c-4Z-2H gives threshold bounds10,15,20 for fixed representatives.

## Companion-hex lemma (hand proof plus finite geometry certificate)

Write v=abcdef and A's target sigma(v)=bcdefa. The E-orbits of these
ports share exactly two rotation classes: h(v) and h(Ev). The ports
representing the second class are Ev=bcdeaf and E^-1 sigma(v)=fbcdea.
This can be checked directly by the fixed-last-symbol cyclic orders;
the certificate additionally checks all720 value renamings independently.

Let an A seam connect the last port of one extracted piece to the first
port of another. If both incident clean-E blocks are full five-port blocks,
the two pieces contain both common hexagons. Thus this seam requires
one extra repeated-hex overlap in addition to its inevitable boundary hex.

## Componentwise overlap charging

Open each nonpure beta cycle once and list the hex-simple pieces along
each original component. Some openings can themselves be A or B; let
x,y count them. There are d such cycles, hence x+y<=d. This proviso is
essential: chronological acyclicity of A/B alone does NOT rule out a
cycle mixing A/B with E edges. An earlier uncommitted draft omitted it.

Within a single component, summing the intersections of each new piece's
hex set with the preceding union gives exactly that component's repeated
hex excess. Every interior A/B boundary contributes at least one, and
each full/full A boundary contributes at least two distinct hexagons.
Consequently, for the number bad of interior full/full A seams,

    R_int >= D2-x+Qs-y+bad,
    bad <= Z-Qs-d+x+y <= Z-Qs.

The counting is performed BEFORE concatenating different components;
cross-component hex sharing is not charged to R_int. At Z=0, necessarily
d=Qs=0, and every A seam must have at least one partial incident E block.
This remains true if heavy joints or orbit sharing occur elsewhere.

## Necessary endpoint recurrence

Define C(b,D,mask) as the largest number of distinct-hex entry ports in
a marked full-pass chain, with at most b paid entries into already opened
orbits and phase deficit at most D. The mask records whether the first
and last ORIGINAL clean-E blocks have length less than five. Clean w3,
E-sigma and sigma-E are allowed. External shadow/history constraints are
relaxed, so this is an upper-capacity model, not a literal cover generator.

Both independent implementations preserve literal hex occupancy. One
chooses whole E-runs and explicit tails, the other advances port by port
and derives targets by scanning all literal endpoint overlaps. Current
deficit is not pruned as monotone: remaining paid old-orbit entries are
optimistically allowed to fill up to four missing ports each. This includes
same-orbit and repeated initial-orbit returns. Initial value renaming is
the proved left-S6 symmetry, not arbitrary orbit relabeling.

At most D2+Z+1+h pieces occur. Designate max(0,D2-d) A joins; demote any
extra A joins when a cycle opening was not A. All other joins are relaxed,
at most Z+h+min(D2,d). Allow at most Z-Qs full/full designated A joins.
Allocate sum b_j=B*-s and sum D_j=5k-G+5s across pieces and maximize the
sum of C values subject to these endpoint constraints. Padding with
unconstrained pieces only enlarges this upper bound. Backward resource
recursion and independently layered forward enumeration check each other.

## Unconditional exclusion of length869

For t=2 all required cells are b0,D0..10; b1,D0..5; b2,D0. Every one was
completely exhausted by both implementations. The endpoint-constrained
upper bounds are strictly below 120+G-5c on all92 arithmetic rows.
Together with Round142's exclusion of lengths<=868, this gives L6>=870
without NR6. Equality or open rows at larger t are NOT closures.

## Sources and scope

- `RR_ROUND142_REPEAT_DOMAIN_OUTER_CODEX.md`: hand extraction and resources.
- `rr_round143_endpoint_capacities_codex.json`: paired finite capacities.
- `rr_round143_endpoint_envelopes_codex.json`: independent t2 optimizers.
- `rr_round143_companion_verified_codex.json`: local geometry and cover controls.
- `rr_round143_general_endpoint_codex.json`: larger-budget necessary envelopes.

No full-cover search, old frontier reconstruction, or NR6 normalization
claim is used. General closure at870/871 remains subject to their explicit ledgers.
