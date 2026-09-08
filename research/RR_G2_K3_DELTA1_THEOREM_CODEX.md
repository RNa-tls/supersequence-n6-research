# Round 136 — the sharp one-defect theorem and two residual mechanisms

Author: CODEX. Branch: `codex/round136-g2-k3-delta1`.

**Result:** a hand-proved one-slack analogue of Theorem 131.1, exclusion of the
free-ascent-reentry defect in this scope, and two precise residual mechanisms.
New contraction-compatible subsets are excluded; **no additional whole resource
row is closed**. All seven rows remain open. `(3,2)` remains 18/25 excluded;
the NR6-conditional outer ledger stays **10/55**. `L6>=872` is NOT proved.

This round did not revisit the 18 closed rows, rerun the H1 seam audit, search
complete NR6 walks, reconstruct a frontier, or investigate another outer cell.

## 1. Exact seven-row table — proved

Use repaired notation: G is pass multiplicity excess; F is abandonment. S is
the number of weight>=3 joints, not the historical strand count. Runs are
maximal consecutive groups of pass entries in one E-orbit; e=r-O, and x
counts paid intra-run joints. E rotates the first five positions, sigma all
six. A pass length counts windows, not rotation edges.

From G=2,k=3:

    P=122, O=27, D=5O-P=13,
    S=26+e+x-f_out,
    N=S+2-27,
    L=846+S+H.

Putting delta=F+e-f_out=1 in delta+x+H<=F-1, and using F<=2, forces
F=2,x=H=0,f_out=e+1,S=25,N=0,L=871. Thus every paid joint is weight 3.

| Type | F | e | x | H | f_out | delta | S | N | Mechanisms | Free masks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| A |2|0|0|0|1|1|25|0|M|2|
| A |2|1|0|0|2|1|25|0|M or R|3|
| A |2|2|0|0|3|1|25|0|R|1|
| B |2|0|0|0|1|1|25|0|M|2|
| B |2|1|0|0|2|1|25|0|M or R|5|
| B |2|2|0|0|3|1|25|0|M or R|4|
| B |2|3|0|0|4|1|25|0|R|1|

Type A has three positive arc lengths summing to six: ten ordered shapes.
Its chronological order agrees with its nu-cycle, `a0 -> a1 -> d0 -> a0`.
Type B has two complementary pairs `(b0,6-b0),(b1,6-b1)`, b0,b1=1..5;
opener0 precedes opener1. The two pairs may be interlaced. No reversal or
exchange of chronological slots is treated as a symmetry.

The 18 free-exit masks in the last column are expanded explicitly in
`rr_round136_defects_codex.json`. They are exact Boolean possibilities, NOT
claims that every mask is realized by a complete NR6 word. E-orbit and hexagon
IDs in these new scripts are lexicographic representative ranks, not compressed
IDs from a different engine table.

## 2. The sharp slack identity — hand proof

Let A be the set of chronological nu-ascents, D_nu the nu-descents, and U the
set of short passes exiting by the free weight-2 joint. Let Rpt be the set of
repeat-run OPENINGS (events, not just distinct repeated orbits).

Every i in U intersect D_nu opens a different event in Rpt: its target is
E(entry(nu(i))) and nu(i) has already occurred. Define

    a = |A minus U|,
    eta = |Rpt minus {opening after i : i in U intersect D_nu}|.

Then, without a distinct-orbit assumption,

    delta = F+e-f_out
          = (F-|U intersect A|)+(e-|U intersect D_nu|)
          = a+eta.

For delta=1 exactly one of the following holds:

* **M:** a=1,eta=0. One opener exits by weight 3; the other exits freely.
  Every repeat run is opened by a free descent. In particular ALL paid
  inter-run joints open fresh orbits, including the nonfree opener.
* **R:** a=0,eta=1. Both openers exit freely. Exactly one repeat-run opening
  is not supplied by a free descent. Section 3 proves that it is necessarily
  a paid weight-3 inter-run joint, not a free-ascent reentry.

All other paid inter-run joints are fresh. Descents which are not free are
not themselves the uniquely counted defect: there can be several of them,
depending on e. Specifically free descents number e in M and e-1 in R.
This explains all 18 masks and prevents the misleading label “one missing
descent” from being used as an invariant description.

### Locality failures are coupled, not counted by delta

For a free ascent i, its lock holds when the run opened just after i contains
nu(i). If the lock fails, at least one later repeat opening in that same target
orbit lies before nu(i). Each such opening is either an ordinary free-descent
opening or the unique exceptional opening. Different apparent obstructions
can therefore use the same event/order constraints; delta is not a count of
all failed locks.

The literal complete NR4 example

    0123012031023132013231032103120213021

has a=1,eta=0, the nonfree ascent at pass 2, and a broken free-ascent lock at
pass 1. No generalized orbit-removing arc contraction is available. This
refutes “one missing free obligation leaves every other lock contractible,”
and the general-n claim that at least one block must remain in Type B.
It does NOT refute a separate n6-specific capacity theorem. The exact pass/run
lists and repeat-opening causes are preserved in the JSON, not inferred from
transition frequencies. We make no theorem that exactly one free lock fails.

## 3. No free-ascent exceptional reentry — hand proof

Hypotheses: complete no-repeat G2 word, F2,delta1,x=H=0, genuine consecutive
permutation joints. The short-last lemma from Round 135 applies. Inside a run
all joints are E steps. A run entered at E(c) and ending at c therefore visits
all five ports. It cannot coexist with a prior registration in its orbit.

Suppose the unique exceptional repeat opening is a free ascent. Then a=0 and
every other repeat opening is an ordinary free descent. Every other ascent
opens fresh. The following cases exhaust its position.

### Type A

The ascent target orbits are orb(arc1) and orb(arc2), distinct from each other
and from the sole descent target orb(arc0). The exceptional ascent's target
orbit has no later permissible repeat opening. Its new run must contain its
short target arc, hence sweeps all five ports, contradicting its prior entry.

### Type B: notation

Let Q_i=orb(opener_i), T_i=orb(closer_i), with T_i!=Q_i. An ordinary free
descent can return only to Q0 or Q1, at closer0 or closer1 respectively.

### Exceptional opener0

T0 is already open. If T0!=Q1, neither ordinary descent can reopen it later
(T0!=Q0 always). Its run must contain closer0 and sweep all five ports:
contradiction. If T0=Q1, the run after opener0 must reach opener1 before
closer0: otherwise opener1 would itself need a Q1 return before closer1.
The other ascent opens fresh T1, different from Q0,Q1, and has a unique locked
run ending at closer1. Closer1 must return freely to Q1 for closer0 to occur.
Contract the unique inner T1 block. The two Q1 pieces now form the entire
E-cycle from E(closer0) to closer0. They cover all five ports of T0, contrary
to its registration BEFORE opener0. This is a contradiction under the
hypothesis; no illegal block is asserted to exist as a valid control.

### Exceptional opener1

T1!=Q1. If T1 differs also from Q0,T0, there is no remaining ordinary return
to it, so its run ending at closer1 sweeps its already-open orbit.

If T1=T0, the run after opener0 and that after opener1 are the only T0 runs.
The first must contain closer0: otherwise the second would have to contain
both short closers, contrary to short-last. The first already swept all five
ports, so the exceptional opening is illegal.

Finally let T1=Q0. If T0!=Q1, T0 has one locked run, placing closer0 before
opener1. The only ordinary Q0 return is therefore already past; the new Q0
run must contain closer1 and sweep all five previously used ports. If T0=Q1,
the first Q1 run ends at opener1 and its later closer0 requires the free return
at closer1. Thus closer1 precedes closer0. Before closer1 there is again no
available ordinary Q0 return after the exceptional opener1; the same full
cycle contradiction follows.

These cases prove that the exceptional event in R is **weight-3 paid
reentry**. This conclusion uses x=H=0 and the two-split/three-arc G2 geometry;
it is not asserted for arbitrary G, heavy words, or incomplete prefixes whose
nu-target arcs are absent. The proof is new; the finite controls below are
checks, not a substitute for these ordering arguments.

## 4. M: aligned versus misdirected paid ascent

Let c=sigma^a(v) be the following arc's entry and y=sigma^(a-1)(v) the literal
joint source. Among the three genuine weight-3 targets from y, exactly one
belongs to orb(c):

    y[3:] + (y1,y2,y0) = E^2(c).

The others do not. This is a positional identity; all 3,600 n6 entry/short-
length pairs were also checked independently of a complete-word search.

**M-aligned contraction theorem (proved).** If the missing free ascent uses
this E^2(c) target, it opens fresh T=orb(c), by eta=0. The Round-135 alpha/beta
argument then applies with this first advance equal to two rather than one:
the later ascent target is fresh and distinct from the earlier target and
both opener orbits; the only possible broken early lock is the ordinary
T0=Q1 nesting. Inner-first merging restores it. Type A uses its two distinct
ascent-target orbits as before. The aligned run has four entries rather than
five. There is no outside registration of either deleted orbit because all
repeat openings are the specified descents.

Two contractions therefore remove nine entries and the one paid entry joint:

    P'=113, O'=25, D'=12, S'=24, H'=0, e'+x'=0.

The inherited, already verified tight N*(0,0,12)=83 excludes this subset.
No H1 or delta0 computation was rerun to use this dependency.

Thus mechanism M remains open only for the other TWO literal paid tail types,
which enter a fresh orbit different from the following short arc's orbit.
Call this **M-off-target**. Its intervening gap is not forced into one run.
It is not legitimate to replace that gap by a cost-one in-orbit step merely
because the resource defect is one.

## 5. R: the exceptional repeated orbit is coupled to an ascent target

Both free ascents are fresh by section 3. Consequently T0!=T1. If the unique
paid reentry targets neither T0 nor T1, the ordinary lock reasoning still
gives two removals: neither unique lock is broken by that repeat, and in the
T0=Q1 beta case the only return to T0 remains the ordinary closer1 return.
The unrelated repeat stays outside the reduced intervals. Type A likewise
retains both unique ascent-target intervals.

The full-pass result has P'=112,O'=25,D'=13,S'=25,H'=0, e'+x'=1. The tighter
capacity **N*(1,0,13)=98** excludes it. The paid edge may become intra-run after
contraction; the sum e'+x', not each term separately, is what was derived.

The remaining **R-target-coupled** model therefore has a single paid repeat
whose target is in `{T0,T1}`. Its timing can be at a short closer boundary or
in a gap. No theorem that it is always adjacent to a short pass is used.

### Explicit absorption: beta with a paid inner return — proved

There is a useful solvable subset of R-target-coupled. Suppose the early
target is T0=Q1, with a unique ordinary inner T1 lock, but the joint after
closer1 returns to Q1 by weight 3, not by the free joint. After contracting
the inner block, its source is the full-pass endpoint of opener1 and its
target is in that same orbit. It is therefore exactly **M3a**.

This is a genuine conversion of the repeat defect to an x token: physical
joint endpoints/weight are preserved, while the registered source pass entry
changes. Original x=0 does NOT imply contracted x'=0. If the two Q1 pieces
are otherwise consecutive E arcs and have no outside Q1 registration, the
outer generalized contraction then removes that M3a as well. The result is
again `(P',O',D',S',H')=(113,25,12,24,0)` and is excluded by 83.

The exact local template is: outer closer c, opener1=E^u(c), inner ordinary
lock, then return to E^(u+2)(c), followed by E steps to c. u=1,2,3 are possible;
u=4 skips c and wraps into used ports. For all 5x5x4 split/phase configurations,
60 are literally legal and contract twice; 40 fail literal legality. This is
a COMPLETE finite template enumeration, not complete enumeration of R gaps.
The verifier contracts the designated inner block directly and checks x'=1
before the second contraction. In particular it does not assume the token
was already an M3a in the original word.

## 6. What one contraction actually leaves

Type A still has a forced FREE partial-arc merge: in M the other ascent is
unaffected; in R only one of the distinct target orbits can be spoiled by
the paid repeat. A noncontractible Type-A configuration after that merge has

    P'=117, O'=26, D'=13, S'=25, H'=0,
    two complementary short arcs in one hexagon,
    f_out'=f_out-1=e, x'=0, e'=e.

Both original endpoint arcs merged to a still-short arc, so no paid intra-run
joint is created at its exit (the short-last geometry applies). This gives
an exact one-fragment defective object, not a full-pass Round-115 chain.

For Type B, a free block is NOT universally forced: the NR4 counterexample
in section 2 already forbids that general-n claim. If a free complementary
block IS removed, let epsilon indicate whether its closer exited freely:

    P'=117, O'=26, D'=13, S'=25, H'=0,
    f_out'=e-epsilon, e'+x'=e-epsilon.

Here x' can be 1 precisely when the retained paid exit becomes same-orbit
after surgery; the preceding beta-paid-return example exhibits this. In
that case e' is the displayed sum minus one. Otherwise x'=0. A contraction
with one deleted paid entry instead has P'=118,D'=12,S'=24 and
e'+x'=f_out'-1. These identities are not complete-cover length formulas
applied to the shortened object.

After any valid TWO removals which eliminate every short pass, write u for
the number of deleted paid joints (0 or 1, including a newly intra-run seam):

    P'=112+u, O'=25, D'=13-u, S'=25-u,
    e'+x'=1-u, H'=0.

Use 98 at u=0 and 83 at u=1. The previous loose bound 106 is NOT used in any
new Round-136 exclusion.

## 7. Exactly two residual mechanisms, not two finite quotient states

Every remaining hypothetical word belongs to one of:

1. **M-off-target:** one weight-3 opener exits to a fresh, wrong successor-arc
   orbit; every repeat opening is an ordinary free descent.
2. **R-target-coupled:** both opener exits are free/fresh; one weight-3 repeat
   targets an ascent-target orbit and is not absorbed by valid contractions.

These are necessary, exhaustive symbolic mechanisms with the row/mask
restrictions of section 1. They are NOT claims that each mechanism is
realizable at `(P,O,D)=(122,27,13)`, NOT a finite state quotient, and NOT two
bounded local templates covering every possible gap. The free-mask count
remains 18 and the resource-row count remains seven. At e=0 only M survives;
at A/e2 and B/e3 only R survives. Interior rows retain both.

A component/history decoration or arbitrary gap cannot be removed just by
calling it one defect. The precise smaller capacity extension, if pursued,
would allow a single marked pair of complementary short arcs in an otherwise
full-pass light chain. Its state must retain both endpoints, their visited
rotation masks, and the M or R target-registration obligation. Round-115's
ordinary b/g/s tokens do not by themselves specify this physical split.

We have NOT proved a numerical upper bound for that extension. In particular
we do not apply 98 to a 117-pass word that still has two short arcs. Deleting
those arcs and cutting into several chains loses extra endpoint/occupancy
information and does not presently supply the desired contradiction. A
universal “G2 with slack delta contracts to delta ordinary N* tokens” theorem
is therefore not asserted.

## 8. Countercontrols and independent finite enumerations

The already preserved exhaustive NR4 L<=39 corpus supplies all 155 relevant
delta1,x=H=0,F2 controls, without rerunning its DFS. Literal remeasurement gives:

| Bookkeeping subtype | Controls | Two merges | One merge | Zero merges |
|---|---:|---:|---:|---:|
| M aligned |81|81|0|0|
| M off-target |53|0|33|20|
| R paid, ascent target |17|17|0|0|
| R paid, other target |4|4|0|0|

There is no free-ascent exception in this corpus. For that particular test
the NR4 domain is complete: eta=1 implies a repeated run, hence O<=7 because
P=8. The corresponding length is 32+O<=39. This finite fact corroborates but
does not replace the general ordering proof of section 3.

The zero-merge NR4 witnesses refute a dimension-independent new charging
claim which would simply force x+H>=1 from delta1. Their n6-specific deficit
or required pass count is different; that is the still-missing resource
obstruction. We have no separately defined extra cost whose positivity
could validly be substituted for that missing argument.

Local n6 tests normalize the first word to 012345 using only left symbol
renaming. They enumerate all paths in the EXPLICIT bounded local domains:

| Domain | Generator nodes | Independent run nodes | Legal closing macros |
|---|---:|---:|---:|
| Paid opener, fresh runs, at most 3 runs after it |5,204|1,198|15|
| Free opener, one paid return to its closer orbit, at most 4 runs |12,931|3,119|20|

The first domain contains five aligned one-run contracts, five noncontractible
two-run macros, and five noncontractible three-run macros. The second contains
15 three-run and five four-run noncontractible macros. All five split lengths
appear. Fifteen of those R macros even admit a literal free closer followed
by a full pass. Thus immediate collision, or a proposed mandatory paid closer,
does not eliminate the local residual model.

For example the M-off-target local word

    01234520134520314520351420351240351234051234501234

is legal, has complementary endpoint arcs, and no generalized arc contraction.
It is a PARTIAL word, not a complete NR6 counterexample or proof of a new
outer-cell solution. Each surviving local word has two short arcs, so it is
not already an N* full-pass chain. Bounded local nonoccurrence is never used
to exclude unbounded gaps.

The independent verifier uses tuples, direct positional tails and run-level
enumeration; it does not import Geometry or the local generator's joint table.
It reproduces the exact sets of 15 and 20 literal strings, replays the 60
paid-return contractions and 15 free-closer controls, and recomputes nu, free
exits, repeats and defect causes from all 155 complete NR4 words.

## 9. Capacity and reproducibility

N*(1,0,13)=98 was actually recomputed here, not copied from the prompt:

    chain_capacity_115_codex.exe 1 0 13 20000000000
    passes=98, nodes=681902414, capped=false

Source SHA256:
`c7694b66f3d31770f5ed9d91b7b61a1973c2138d22513a0d7ca40615dc74544a`.
Binary SHA256:
`b1942b9cdada4ddefac40bb9b9ef86c132817d8446de281e8c6647972044179c`.
Driver source was committed at a4c7e66 before execution. Its measured runtime
was 28.83 seconds; this is a local chain-capacity calculation, not NR6 DFS.
The 83 bound for deficit12 is an explicitly reused Round-135 dependency.

Artifacts record source commit/SHA, interpreter or capacity binary SHA,
argv, scope, node counts, cap status and deterministic mathematical digests:

* `outputs/rr_round136_defects_codex.json` — seven rows, eighteen masks,
  exact NR4 causes/counterexamples, M local macros (source 7d33f82);
* `outputs/rr_round136_repeat_macros_codex.json` — R local macros, 100-template
  paid-return census, literal positive controls (source 902776f);
* `outputs/rr_round136_capacity_codex.json` — actual tight capacity run
  (source a4c7e66);
* `outputs/rr_round136_verified_codex.json` — independent finite verification
  (source c0ff312), with proof scope explicitly separate from finite checks.

An initial synthetic u=4 paid-return construction accidentally used a direct
closer instead of the required wrapped E^2 target. Commit 902776f literalizes
the complete wrap; those inputs now fail by actual collision. No field was
deleted to make validation pass. The final 100-input ledger conserves counts:
60 legal plus 40 rejected. No production engine/checkpoint was changed.

Reproduce the small checks without rerunning any historical complete search:

    python src/verify_round136_defect_codex.py
    python -m unittest discover -s tests -p test_round136_defect_codex.py -v

All nine new tests and py_compile pass. Byte-preserving attributes cover the
new JSON/code bundle. The branch includes the original Round-135 source and
certificate history so reviewers can recover that lineage too; remote sync
is reported separately with the final commit.

## 10. Verdict

**Proved:** delta=a+eta, no free-ascent exceptional reentry in the specified
scope, M-aligned restoration, R target coupling, and the beta paid-return
absorption lemma. **Finite complete verification:** stated local domains,
retained NR4 controls, and the uncapped 98 capacity replay. **Still open:**
global exclusion of M-off-target and R-target-coupled at this cell's resource
coordinates. Neither a broad search nor an unproved local quotient was used.

New whole rows eliminated: **0/7**. All seven remain OPEN, but their surviving
structures must fall in the two explicit mechanisms above. Outer ledger:
**10/55**, NR6 ASSUMED. No global superpermutation lower bound is claimed.

ASTRA_G2_K3_DELTA1_THEOREM
