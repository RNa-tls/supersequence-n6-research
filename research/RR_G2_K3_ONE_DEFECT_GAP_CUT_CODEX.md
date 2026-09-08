# Round 137 — multi-orbit gap extraction closes the one-defect cell

Author: CODEX. Branch: `codex/round137-mr-hard-core`.

**Result:** under NR6 and the previously audited G/F foundation, both remaining
mechanisms are excluded. All seven delta=1 rows close; with the eighteen
previously excluded rows, `(k,G)=(3,2)` is closed. The conditional outer ledger
changes **10/55 -> 11/55**. NR6 remains ASSUMED. **L6 >= 872 is NOT proved.**

The new step is NOT another single-orbit contraction. Extract the whole gap
between complementary short arcs as a separate light chain, complete its
last arc, and merge the two arcs in the remaining word. Orbit sets of the two
pieces are disjoint. Their pass and deficit sums allow a strict convolution
bound. The pieces need not concatenate and can share a hexagon.

No full NR6 search, other outer cell, G>=3 case, historical frontier or closed
delta=0 row was searched. Prior Round135/136 certificates are unchanged.

## 1. Definitions and exact row map — proved, inherited

Use repaired notation. G is pass multiplicity excess; F is abandonment;
S counts paid joints, NOT the historical number of strands. E rotates the
first five positions and sigma rotates all six. A pass length counts windows.
All seven rows have

    F=2, delta=1, x=H=0, P=122, O=27, D=13, S=25, N=0, L=871.

The Round136 identity `delta=a+eta` gives either M (one paid opener, all repeat
openings free descents) or R (all openers free/fresh, one paid repeat opening).

| Row | f_out | M-off-target | R-target-coupled | Round137 reason |
|---|---:|---|---|---|
| A/e0 |1|yes|no|117 > 112|
| A/e1 |2|yes|yes|117 > 112 or 103|
| A/e2 |3|no|yes|117 > 103|
| B/e0 |1|yes|no|117 > 112|
| B/e1 |2|yes|yes|117 > 112 or 103|
| B/e2 |3|yes|yes|117 > 112 or 103|
| B/e3 |4|no|yes|117 > 103|

These are mechanism incidences, not a seven-state quotient. Type A has three
chronologically ordered arcs of one hexagon, lengths a+b+c=6. Type B has two
complementary pairs; opener0 precedes opener1. In Type A the two ascent target
orbits are those of arc1 and arc2. In Type B write Qi=orb(opener_i),
Ti=orb(closer_i). Always Ti!=Qi. In R both ascent openings are fresh, so
T0!=T1, and T1 differs also from Q0,Q1. No arbitrary orbit relabeling is used.

## 2. Exact paid-tail offsets — positional proof and complete finite check

Let (v,a) be a short pass, y=sigma^(a-1)(v) its endpoint, and c=sigma(y) the
next arc entry. Rename VALUES uniquely so c becomes 012345. The three genuine
weight-3 targets are exactly:

| Literal tail positions in y | Normalized target | Orbit relative to c |
|---|---|---|
|120|234015 = E^2(c)|same|
|201|234150|different|
|210|234105|different|

Normalized target orbit representatives/phases are respectively
012345:2, 152340:2, 023415:1. These are coordinates in the shared value frame,
not subtraction of unrelated canonical orbit phases. All 720*5*3=10,800
targets were checked by both tuple code and the local generator, no exceptions.

All three targets differ from orb(v) for a<6. Thus the phrase “M3a is always
intra-run” is valid only for a FULL source pass. On a short pass, literal 120
can be inter-run with x=0. It is the **aligned** M case already absorbed in
Round136, not a remaining off-target case. Remaining M tails are precisely
201 and 210, both paid fresh-orbit entries.

For a full source pass only 120 stays in the same orbit (720/720); 201/210
are cross-orbit. These facts follow directly by extracting positions, not
from observed run labels.

## 3. R tail types and contraction conversion — hand proof

The exceptional paid target is T0 or T1. Before the exception, its free opener
has already opened that orbit. The exception must precede its target closer:
without this exceptional return, ordinary intervening locks can be contracted,
and the E run from E(c) through c sweeps all five phases. A return after that
closer would collide. It cannot precede its opener, whose target must be fresh.

| Source/type | 120 | 201/210 |
|---|---|---|
|Full pass|intra-run, impossible as exceptional inter-run opening at x=0|possible cross-orbit repeat|
|Type-A final short descent|targets arc0 orbit, unrelated to T0/T1|cannot occur before either target closer|
|Type-B closer0|targets Q0, not T0 or fresh T1|no remaining coupled realization: a T1 return here requires a prior T1 opener, but the available Q1/T0 return order puts closer1 before closer0|
|Type-B closer1|can target T0 only when Q1=T0; Round136 nested-120 absorption|can target T0 when Q1!=T0; survives single-orbit contraction|

For any retained literal weight-3 boundary y->t, a contraction which completes
its source pass has full entry c=sigma(y). It becomes intra-run iff
orb(t)=orb(c), iff its literal tail is 120. This is necessary AND sufficient
for that boundary's conversion to M3a, not a sufficiency assertion for the
existence of an allowed contraction. If the merged source remains partial,
all three tails still change its entry orbit. For the beta return at closer1,
the inner complementary merger completes the source and Q1=T0 gives exactly
the already audited conversion. The residual 201/210 boundaries cannot convert.

There is consequently no valid claim that all residual R configurations
convert after one SINGLE-orbit contraction. The new extraction below does not
require such a conversion.

## 4. Protected seams and adversarial controls — scope-limited theorem

In an H0 generalized SINGLE-orbit arc contraction, any deleted paid joint
must be 120. At the first boundary the target lies in orb(sigma(y)); internally
a full source and target share the deleted orbit. At surviving boundaries
literal source and target are unchanged. Therefore the ordered list of
literal 201/210 seams is invariant under any sequence of these contractions.
This obstruction is only to that contraction calculus, not to multi-orbit
extraction, and does not prove non-completability by itself.

All 155 preserved NR4 delta=1 controls satisfy this invariant. In particular,
the existing no-single-contraction counterexample

    0123012031023132013231032103120213021

is retained. The new extraction succeeds on all 53 NR4 M-off-target controls,
including the 20 with no ordinary initial contraction. It does not falsely
exclude those valid NR4 walks: the numerical capacities used below are n=6.

The finite NR6 inverse-expansion domain has 52 base/extension configurations,
1,948 candidate insertions, 1,166 literal collisions, and 782 legal normalized
literal words. All 782 have exactly one removable ordinary block, one remaining
protected 201/210 defect, G_local=2,F=2,delta=1,x=H=0. There are 268 M and 514 R
words. All pass the extraction checks. This is a specified LOCAL finite domain,
not an enumeration of all potential defect gaps or complete NR6 words.

Local valid examples refute a universal immediate three-demand/five-slot
collision or automatic third repeated hexagon. Slot occupancy and literal
multiplicity are recorded per example; no extra e/x/H charge is assumed.
In the reduced R gap the pre-consumed root prefix is p phases, its required
final suffix is 5-q phases, and p<=q gives occupied slots p+5-q<=5. The gap
q-p is charged exactly as deficit; there is no universal slot overflow.
For M each private run uses l<=5 phases and contributes 5-l. The successful
charge is the TWO-CHAIN pass/deficit inequality, not a fabricated extra N or e.

`rr_round137_protected_seam_codex.json` is the frozen preliminary LOCAL stage;
its then-current zero-new-rows/10-of-55 status is superseded by the final
`rr_round137_gap_closure_ledger_codex.json`, not silently rewritten.

## 5. Multi-orbit gap extraction lemma — hand proof

Suppose complementary short arcs (v,a), (c,6-a), c=sigma^a(v), bound an interval.
Let I be all pass entries strictly after the opener through the closer,
and suppose its intermediate passes are full. Complete the last pass at c
to length 6, obtaining an extracted word W_in. In the original word replace
the entire interval by (v,6), obtaining W_out.

Required conditions: every orbit of I is PRIVATE to this interval, disjoint
from every orbit retained in W_out; the extracted word has either all fresh
runs (M) or just its root orbit repeated in its final run (R).

The replacement preserves literal entry v and terminal endpoint of the
closer, hence both external joints. Its visited windows are a subset of the
original word. W_in adds the opener's complementary windows to its final arc;
these lie in the same split hexagon, which no internal full pass can occupy.
Thus W_in too is literal no-repeat. Its interior joints are unchanged. Every
pass of W_in is now full. Two pieces initially share the split HEXAGON, but
not an E-orbit. They need not concatenate. Capacity is applied separately.

If one other ordinary five-entry orbit block is removed, before or after this
cut, the final two words satisfy, writing j=|I| and m=number of its orbits:

    P_in=j,        O_in=m,       D_in=5m-j,
    P_out=117-j,   O_out=26-m,   D_out=13+j-5m,
    P_in+P_out=117, O_in+O_out=26, D_in+D_out=13.

The ordinary block removes exactly five entries and one orbit, and no paid
joint. The cut removes m paid joints from the outer word in either mechanism:

    S_out=25-m=O_out-1, e_out=x_out=H_out=0;
    M: S_in=m-1, e_in=x_in=H_in=0;
    R: S_in=m,   e_in=1, x_in=H_in=0.

Both deficits are nonnegative by five distinct ports per orbit. If the
ordinary contraction is performed AFTER extraction it may delete the shared
hexagon from W_out; no cross-piece hexagon-disjointness premise is used.

## 6. Inclusion of EVERY residual mechanism — hand proof

This is the coverage argument; the 835 finite controls are not its substitute.
An “ordinary block” below is the inherited free-lock contraction, all joints
free, possibly merging two adjacent short arcs in Type A.

### M, Type A

Contract the other, free ascent's private orbit. Its target differs from the
opener and descent-target orbits (different last symbols in the same hexagon).
It has no permissible repeat opening. The result has one complementary pair
with a paid off-target opener. Between it and its closer every run opens
fresh: eta=0 and there is no descent inside this interval. A previously opened
orbit cannot occur there. Nor can an orbit opened there occur outside later:
the only remaining free descent returns to the opener orbit, outside I.
Thus all gap orbits are private and W_in is ordinary.

### M, Type B: paid opener0

The later free target T1 is fresh. If its lock could break ordinarily it would
have to equal Q0, but Q0 is already open, impossible. (It cannot equal its own
Q1.) Its block therefore contracts first. This reduces to the same G1 M gap.
The gap has no internal descent; its only possible repeat target outside is
the opener orbit. All gap orbits are private.

### M, Type B: paid opener1

If the first free lock holds, contract it first. Otherwise its only possible
ordinary return is from closer1 and T0=Q1. The run opened after opener0 must
reach opener1 before closer0; after opener1 it cannot return to Q1 except at
closer1. Consequently the order is

    opener0 < opener1 < closer1 < closer0.

The inner gap (opener1,closer1) has no short intermediate pass or descent.
All its orbit openings are paid fresh, so none belong to the already opened
outer orbits. All are private: subsequent free descents target only Q1,Q0.
Extract this M gap FIRST. The merged Q1 pass restores the outer T0 E lock;
contract that ordinary block second. This covers the NR4 counterexample
which refuted the claim that an ordinary contraction is always initially available.

### R, Type A

The exceptional target is exactly one of the distinct T0,T1. The other has
neither ordinary nor exceptional repeat available and contracts first. The
remaining complementary-pair interval starts in E(c), ends at c, and has one
paid return to its root orbit T. All other openings inside it are fresh and
private. The final root run must reach c; a departure before c would require
another return, but the unique exceptional opening is already spent and the
only remaining ordinary descent is c itself.

### R, Type B: exceptional target T0

The later target T1 is fresh, different from Q0,Q1,T0, and has no return
opening available. Contract its ordinary block first. If the paid return at
its exit turns into 120 intra-run, this is precisely the already eliminated
Round136 absorption subset. Otherwise it remains 201/210, and the reduced
G1 interval is a root-return gap with private other orbits.

### R, Type B: exceptional target T1

If the T0 lock is unbroken it contracts first. If broken, its only available
return is ordinary, from closer1, so T0=Q1 and the order is the same beta nest
opener0<opener1<closer1<closer0. The inner interval has one exceptional return
to fresh T1 and no ordinary descent until closer1. Extract it FIRST, completing
opener1 and restoring the ordinary outer T0 block; contract the latter.

These cases are exhaustive because the only repeat openings are the specified
free descents and, in R, the single paid return. In every reduced R gap the
first and last entries are E(c),c; the root appears in precisely two runs,
all other orbits once. All other runs are fresh/private, and all retained paid
joints are genuine cross-orbit 201/210. The outer word is ordinary. Empty
outside context causes no problem: the merged pass itself remains.

## 7. Capacities and strict contradictions

Let C0(d)=N*(0,0,d), the independently checked ordinary light-chain upper bound
with at most d deficit. Reuse Round135's committed uncapped values:

    d    0  1  2  3  4  5  6  7  8  9 10 11 12 13
    C0  20 20 33 33 46 46 49 58 62 66 70 74 83 83.

For M, sum deficits is exactly 13, hence

    117 <= C0(d)+C0(13-d) <= 112,

contradiction. There is no equality case to test: even the maximum, at
d=4 or 9, falls five passes short. The old 312-heavy-seam census is not rerun.

For R define R(d) on full-pass light chains with EXACT deficit d:
root orbit occurs in exactly two runs, first entry v, last entry E^-1(v),
all other orbits fresh, x=H=0, no repeated hexagons. This is not the generic
N*(1,0,d) class, and there is no 120-hex coverage target.

Normalize v=012345 by value-renaming. The initial root run occupies phases
0..p-1 with 1<=p<=4. After one or more fresh runs, reentry phase q satisfies
p<=q<=4 and the last run occupies q..4. Root deficit is q-p. Every completed
fresh run of length l contributes 5-l; their sum plus q-p equals d.

The run-level enumerator exhausts all such chains for d<=13. The only prune is
already irrevocable deficit >13 or literal hex/orbit collision. Fresh current
runs are allowed to grow before charging 5-l; return to the root is treated
separately, never pruned as an ordinary repeated orbit. Every accepted chain
has an explicit witness for its maximum. The exact results are:

| d |0|1|2|3|4|5|6|7|8|9|10|11|12|13|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R(d) |20|empty|8|empty|empty|empty|24|empty|22|21|40|39|48|47|
| chains |4|0|3|0|0|0|48|0|26|21|216|684|1711|2346|

The independent port-step implementation generates literal permutations and
joints itself, imports neither the original geometry nor search, and extends
runs one port at a time. It exactly reproduces every maximum AND chain count.
Different node definitions give 7,712,526 versus 29,959,867 nodes. Both complete.

Therefore

    117 <= R(d)+C0(13-d) <= 103,

contradiction. The maximum is at d=0 (20+83); there is no extremal seam
compatibility question. The generic N*(1,0,13)=98 is not misapplied to the
uncontracted word. Ordinary-plus-generic-defect convolution would be too weak;
the root-return endpoint constraint is essential.

## 8. Verification, interpretation, and exact residual

Independent Python tuple replayer checks all 835 persisted cuts (53 NR4 M,
268 NR6 M, 514 NR6 R), both resulting literal words, private orbit sets,
all ordinary contraction orders, P/O/D/S accounting, and root-return endpoints.
All nine nonempty capacity extrema undergo literal all-window replay.
No hidden joint window or permutation repetition is accepted.
The 11 new regression tests and 18 inherited Round135/136 tests pass (29/29);
`py_compile` and `git diff --check` pass. A deliberately tiny local node cap
returns exit code 2 with `capped=true`, never a complete capacity certificate.

The initial draft verifier required exactly one shared hexagon even after the
optional outer contraction. It correctly failed on beta examples: that
contraction can delete the outer copy. The final check requires exactly one
at extraction and at most that one afterwards. P/O/D accounting and both
capacity bounds were unchanged. This correction is explicit, not suppressed.

**Hand-proved:** positional offsets; seam invariant for its restricted calculus;
gap extraction and exhaustive M/R inclusion; parameter sums; convolution logic.
**Finite complete calculation:** stated local domains, root-return capacity,
independent port traversal, positive/negative regression tests.
**Not asserted:** local macros form an exact quotient; arbitrary seam residues
control continuation; delta1 theorem for other G; NR6 itself; an unconditional
lower bound of 872.

Newly eliminated mechanisms: M-off-target and R-target-coupled in the seven
specified resource rows. Residual hard core in this cell: **empty**.
Together with Round135/136's accepted exclusions: `(3,2)` CLOSED under NR6.

## 9. Reproduction and provenance

Capacity source committed and remotely pushed before execution:
`026eb61` (runner and run-level source), independent port source `2b9dcf0`.
Compile using Zig 0.16.0 `cc -O3`; binary and all source SHA256, exact argv,
cap, node counts, timings and mathematical digests are recorded in JSON.

    zig cc -O3 src/round137_root_return_capacity_codex.c -o outputs/round137_root_return_capacity_codex.exe
    zig cc -O3 src/verify_round137_root_return_codex.c -o outputs/verify_round137_root_return_codex.exe
    python src/research_round137_gap_cut_codex.py
    python src/research_round137_capacity_codex.py
    python src/verify_round137_gap_capacity_codex.py
    python -m unittest discover -s tests -p test_round137_gap_codex.py -v

The capacity runner requires HEAD already pushed to this Round137 branch.
The producer's node cap is 20,000,000,000, not reached; the independent checker
has no cap. Compiled executables are rebuildable local artifacts, not LFS.

ASTRA_G2_K3_CLOSED
