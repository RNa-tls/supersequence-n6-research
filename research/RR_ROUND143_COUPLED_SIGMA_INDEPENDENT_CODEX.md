# Independent audit of the coupled sigma capacity

Author: CODEX independent proof/code review, 2026-09-12.
Reviewed source baseline: `22d14c0`; no new exhaustive run is asserted here.

## Scope and necessary inclusion

Use the fixed first-occurrence representative and the hand reductions of
`RR_ROUND142_REPEAT_DOMAIN_OUTER_CODEX.md`, with the cycle-opening correction
in `RR_ROUND143_ENDPOINT_CORRECTION_CODEX.md`. This audit applies **only to
Z=H=0**. Write A=D2 for the total number of dirty weight-2 sigma edges.

Since z=2g+d, Z=z-A=0, and A<=R_int<=2g, equality forces

    d=0, Qs=0, R_int=A=2g, c=G-A.

After deleting the c pure clean-E cycles, exactly the dummy beta component
remains. Removing its dummy gives one path. Thus no mixed A/E cycle is
discarded merely because A edges are chronologically acyclic: d=0 is the
reason no additional nonpure cycle exists. A pure E cycle has five distinct
ports and consumes its entire orbit, which occurs nowhere else.

Every A edge v->sigma(v) enters its predecessor's hexagon and contributes
one repeated-hex visit along this path. These A visits exhaust R_int=A.
Consequently every non-A step must enter a previously unvisited hexagon.
All selected entry ports are distinct, including consecutive A targets.
H=0 removes heavy edges, and Qs=0 removes dirty sigma-squared edges. The
remaining alphabet is E, the three clean weight-3 targets, E-sigma,
sigma-E, and exactly A sigma edges.

The path's exact resources are

    P'=120+G-5c, O'=24+k-c, D'=5O'-P'=5k-G.

It has S+A+1 maximal clean-E blocks. Every opened orbit is entered once
without an old-orbit charge; every subsequent non-E entry into that orbit
uses one charge. Hence the GLOBAL old-orbit entry count is

    b'=(S+A+1)-O'=S+1+A-O+c=B*.

This is not the per-piece b_sum=B*-s after cutting A edges. The uncut path
therefore embeds in the SIGMA:A model with bounds b=B*, D=5k-G and exact
A. Uniform value renaming sends its first port to 012345 and preserves all
maps, orbit/hex membership, and resource counts.

## Implementation and pruning audit

`src/round143_marked_runs_codex.c` enumerates every possible maximal E-run
length, then all permitted non-E transitions. Its old-hex exception is only
the first port of a run reached by the actual sigma map. `port_seen` rejects
duplicate ports. Nested calls clear only hex bits newly introduced by that
call, so an A repetition does not erase an ancestor's occupancy.

`src/round143_marked_ports_independent.c` discovers targets from literal
endpoint overlaps and advances one port at a time. Its old-hex exception is
only DIRTY_A; orbit phase masks independently enforce unique ports. It
restores the prior phase mask and clears a hex bit only when that entry was
the first visit. Both implementations charge every non-E old-orbit entry,
including A and same-orbit or initial-orbit returns, and accept only when
the number of A edges equals the requested value.

The whole-run prune after ending a run is

    current_D - 4*remaining_b > D_cap.

Any later visit to a currently opened orbit must start a non-E re-entry.
That orbit already has at least one occupied port, so one such entry and
its E continuation can fill at most four previously missing phases. Newly
opened orbits have nonnegative final deficits. Granting four repairs per
remaining charge therefore understates final deficit and is safe. The
current run's free extensions are still enumerated outside this prune.

The port implementation additionally grants all missing current-orbit
phases free before applying the same four-per-charge allowance. This is a
weaker, also safe bound. Neither implementation incorrectly treats current
deficit itself as monotone. No unsafe pruning or state-restoration gap was
found for ordinary capacity runs with valid threshold parameters.

## Paired certificate and limits

For identical fixed A,b,D, with both searches exhausted and no optional
target-export arguments, `accepted_prefixes` **must agree** as well as
maximum and endpoint capacities. A port path has a unique decomposition
into maximal E-runs, and distinct permitted transition types have distinct
targets. Thus each implementation counts each accepted rooted path once;
the different safe prunes remove no accepted path. The counters are
uint64_t, so an integer-count interpretation also requires no overflow.
Node counts and transcript hashes need not agree. Capped results do not
certify capacity bounds.

This is a finite necessary relaxation, not a literal first-occurrence
feasibility model: external shadow/history obligations and completion by
the removed pure cycles are not imposed. Only an exhausted upper capacity
strictly below P' excludes its resource cell. A positive capacity or an
equality at P' is not a literal construction or a closure. A is exact;
capacities must not be assumed monotone in A. For A>0 the path is not
hex-simple, so certificates must distinguish the coupled SIGMA model from
the A=0 marked hex-simple model using explicit model and A metadata.

## General coupled extraction: independent audit

This section extends the EXTRACTION, not the uncut-path inclusion above.
It applies to the general fixed-representative R142 coordinates, including
positive Z or H. Write A=D2, retain Qs for the number of type-B edges, and
keep d for the number of nonpure cycles other than the dummy component.
The conclusions are necessary relaxations, not literal constructions.

Remove the c pure E cycles and the dummy. Open each of the d remaining
cycles at a non-E edge, preferring a heavy edge when available. Such an
edge exists because these cycles are not pure E. Let x and y count
openings at type A and type B, so x+y<=d. Cut every remaining heavy edge
and every remaining type-B edge. The resulting paths have

    A0=A-x,
    m0<=d+1+h+Qs-y,
    R0<=R_int-(Qs-y),
    e0=R0-A0<=Z-d-Qs+x+y.

Here R0 is the SUM of within-path repeated-hex excesses. A split of a
linear path with prefix U and suffix V reduces this excess by exactly
the number of hexagons shared by U and V. In particular, cutting a
same-hex B edge reduces it by at least one. Opening a cycle leaves its
vertex and hex sets unchanged; heavy cuts cannot increase excess. This
proves the displayed R0 bound even when separate paths share hexagons.
Every retained A edge contributes a repeated target within its path,
so R0>=A0 and e0>=0.

Apply the following finite splitting procedure. In any current path,
find the first whole E block containing an entry reached by a non-A
edge whose hex has occurred earlier in that path. Split immediately
before this block. The first block of a path cannot be bad, because
the at-most-five ports of one E orbit have distinct rotation hexagons;
therefore the required incoming block-boundary edge exists.

If that incoming edge is non-A, the offending hex lies both before the
block and inside the suffix. The split decreases repeated-hex excess
by at least one and retains the same number of A edges. This includes
the case where the block's first port is fresh but an internal E entry
collides with an earlier hex.

If the incoming edge is A, its boundary hex is shared with the prefix
through its predecessor. The offending entry must then be internal to
the E block. Its hex cannot have occurred earlier within that block,
and is distinct from the boundary hex. Thus TWO distinct hexagons lie
in both prefix and suffix. The split decreases repeated-hex excess by
at least two while deleting exactly one A edge.

In both cases e=R-A_ret decreases by at least one and remains
nonnegative. Hence at most e0 extra splits occur. No split cuts an E
edge. All final paths have distinct ports, exactly their retained A
edges as the allowed repeated-hex landings, and the permitted light
non-A alphabet. Each therefore belongs to the coupled SIGMA model.
Their number and total retained sigma count satisfy

    m<=m0+e0<=Z+1+h+x<=Z+d+1+h,
    A_ret>=A-x-e0>=A-Z+d+Qs-2x-y>=A-Z-d+Qs,
    max(0,A-Z-d+Qs)<=A_ret<=A.

No parity restriction on A_ret or on individual piece counts is
justified merely by parity of the original A: splitting can delete
individual A edges.

For the NEW pieces define s'=sum_j O_j-(O-c). Distinct entry ports and
coverage of all remaining ports give s'>=0. All cuts are non-E, so the
total number of maximal E blocks remains S+A+1. In each piece that
number is O_j+b_j, where b_j counts its non-E old-orbit entries. Thus

    sum_j b_j=B*-s', 0<=s'<=B*,
    sum_j D_j=5k-G+5s',
    sum_j P_j=120+G-5c.

The sharing value s from a previous, different extraction must NOT be
fixed here. A safe capacity upper bound maximizes over every new
s' in [0,B*], at most Z+d+1+h pieces, all exact retained-A totals in
[max(0,A-Z-d+Qs),A], and all nonnegative piece allocations with the
displayed b and D sums. Each piece uses C(A_j,b_j,D_j), exact in A_j
and upper-bounded in b_j,D_j. Every original candidate supplies one
such allocation. Exhausted capacity bounds whose convolution is
strictly below the required pass total exclude a row; equality, a
positive capacity, or a missing/capped table cell does not close it.

This section is a hand inclusion and algorithmic termination audit.
It asserts neither a new exhaustive capacity run nor closure of the
positive-Z/H threshold rows.
