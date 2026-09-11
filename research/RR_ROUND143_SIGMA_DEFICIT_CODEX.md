# Sigma seams force E-run deficit

## Scope and theorem

Consider one spliced entry-port path in the Round143 SIGMA relaxation:

- Every entry port is distinct.
- An E edge sends `abcdef` to `bcdeaf`.
- Exactly A edges are sigma edges, sending `abcdef` to `bcdefa`.
- Every other edge, including E and the allowed weight-three transitions,
  lands in a rotation hex not previously visited. A sigma target is the
  only permitted repeated-hex entry.

Let Q be the number of opened E-orbits, P the number of entry ports,
`D = 5Q - P`, and b the number of non-E entries into previously opened
E-orbits, excluding the initial entry. Then

    D + 5b >= A.

In particular, `D >= A` when `b = 0`. This is a hand necessary condition
for this relaxation, not a claim that its paths lift to literal covers.
It does not assume that E-orbits are fresh, that endpoint runs are full,
or that all other transitions are clean. The permitted weight-three
catalog is irrelevant to the proof once its new-hex landing rule holds.

## The missing-companion propagation

Write E for rotation of the first five symbols, sigma for rotation of
all six, and h for the full-rotation hex. Direct substitution gives

    E^-1 sigma(v) = sigma^-1 E(v).

Suppose a full five-port E-run begins at s and ends at `E^4(s)`. Its
sigma successor run starts at `x = sigma E^4(s)`. The predecessor port
of x in its E-orbit is

    E^4(x) = E^-1 sigma E^4(s) = sigma^-1(s).

Thus this port has the already visited hex `h(s)`. If the new run has
length four, it visits `x, E(x), E^2(x), E^3(x)` and omits precisely
`m = E^4(x)`. After the next sigma edge, the next run starts at
`y = sigma E^3(x)`, whose omitted port, if it too has length four, is

    E^4(y) = E^-1 sigma E^3(x) = sigma^-1 E^4(x) = sigma^-1(m).

Consequently the omitted port's hex remains `h(s)` through arbitrarily
many successive length-four runs. A subsequent length-five run visits
that port as its fifth entry. This entry is reached by an E edge, not a
sigma edge, and has an already visited hex, which is forbidden.

Therefore a consecutive sigma-connected run pattern

    5, 4, ..., 4, 5

is impossible. The number of intermediate fours is arbitrary, including
zero. This is an induction, not a bounded enumeration assertion. The
argument remains valid if another violation occurs earlier: such a
prefix already fails the assumed model.

## Counting the deficit

Split the path into maximal E-runs, of lengths `1 <= r_i <= 5`.
Their number R obeys `R = Q + b`: each new run either opens its orbit
or is one of the b old-orbit non-E entries. Thus their total run deficit is

    Delta = sum_i (5-r_i) = 5R-P = D+5b.

Partition the sequence of E-runs into maximal clusters whose joins are
all sigma edges. A cluster with m runs has `m-1` sigma edges. Let f be
its number of length-five runs, and s its number of runs of length at
most three. Between successive length-five runs, at least one run has
length at most three, by the forbidden-pattern lemma. These intervening
segments are disjoint, so `s >= f-1`. Each non-full run contributes at
least one deficit unit, and each length-at-most-three run contributes
at least one further unit. Therefore

    sum_cluster (5-r_i) >= m-f+s >= m-1.

Summing over all clusters proves `Delta >= A`, hence the theorem.

## Sharp small controls and limits

Starting at `012345`, sigma-connected E-run lengths `(5,4)` give
`(A,b,D) = (1,0,1)`; lengths `(5,3,5)` give `(2,0,2)`. Both satisfy
distinct entry ports and the precise new-hex rule. Thus a uniform strict
improvement of `D >= A` at b=0 is false, even for A=1 or A=2.

This proof alone does not establish a smaller coefficient than five on
b, or a stronger global capacity bound. It supplies an admissibility
condition for coupled capacity cells; it is not a closure of any
remaining length-870/871 arithmetic rows by itself.

## Extension with repeated hexes and cycle openings

The same counting works without a new-hex landing rule if violations are
charged explicitly. In a sigma cluster, call a gap between consecutive
full runs bad when every intervening run has length four. Let j be the
number of bad gaps, summed over all clusters. Each bad gap forces a
repeated-hex E entry at the final port of its right full run. Distinct
gaps have distinct right full runs, hence distinct charged entries.
The earlier counting becomes `s >= f-1-j`, and therefore

    Delta >= A_ret - j.

For the Round142/143 spliced beta components, discard pure E circuits,
cut every heavy edge, and open every remaining nonpure circuit at one
non-E edge. No E edge is cut. If x A edges and y type-B same-hex edges
are used as these cycle openings, then `x+y <= d`, with
`A_ret=A-x` and `B_ret=Qs-y`. This includes cycles already opened by
heavy cuts, which need no additional opening.

Within each resulting linear path, every retained A or B edge lands in
the same hex as its predecessor, hence supplies a repeated-hex entry.
Every charged bad-gap entry is an E target, so it is distinct from
these A/B targets. Summing repeat excess over the linear paths cannot
exceed original within-beta-component repeat excess. Consequently

    R_int >= A-x + Qs-y + j,
    Delta >= 2(A-x) + Qs-y - R_int.

The original global E-run deficit is unchanged by these cuts because
they only remove non-E edges. From the established extraction identities,

    Delta = sum D_j + 5 sum b_j = 5k-G+5B*.

The sum may be taken over the ordinary extracted marked pieces: their
non-E cuts likewise leave the E-runs intact, and sharing cancels between
the two terms. Using `R_int <= 2g = A+Z-d` gives the stronger
opening-dependent form and its uniform consequence:

    5k-G+5B* >= A-Z+d-2x-y+Qs >= A-Z-d+Qs >= A-Z-d.

In particular, `Z=0` forces `d=Qs=0`, so

    5k-G+5B* >= A

holds even when heavy edges are present. No cross-component hex overlap
is charged to `R_int` anywhere in this argument. The extension is a hand
consequence of the stated component identities, not an assertion that
arbitrary spliced paths obey those identities.

## Verification

`src/verify_round143_sigma_deficit_codex.py` checks the transform identity
and both propagation formulas for all 720 symbol renamings. A second
derivation obtains E and sigma targets from literal full-pass endpoint
suffixes. It also checks the forbidden final fifth-entry hex for zero
through five intermediate fours under all 720 renamings, and audits all
780 one-to-four-run pure-sigma templates at a fixed initial value
renaming. Those template controls are explicitly bounded; the general
induction above is the proof. Output:
`outputs/rr_round143_sigma_deficit_codex.json`.

For the extension, the checker independently rebuilds spliced entry
edges and beta paths from the 196 saved finite literal controls, performs
heavy/cycle cuts, and verifies the bad-gap injection, original-component
repeat charge, unchanged E-run deficit, and both resulting inequalities.
These controls include n=3,4,5,6; the identical argument uses full runs
of length n-1 and propagating partial runs of length n-2. They corroborate
the proof but are not an exhaustive cover search.
