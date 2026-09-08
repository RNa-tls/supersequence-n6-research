# Round 138 — universal orbit disjointness for the canonical defect cut

Author: CODEX. Branch: `codex/round138-universal-privacy`.

**Result: R137-P is proved for the specified Round137 canonical cuts.** The
proof is an injection from cross-piece shared orbits to additional repeat-run
OPENING EVENTS. It does not assert that two different phases of one orbit
cannot occur in different runs. The internal root return in R is explicitly
permitted and is not charged a second time.

The independent Round137 audit correctly left the universal inclusion layer
PARTIAL. Its verified capacities, identities and literal controls were not
themselves a proof of privacy. In particular, the Round137 producer filtered
candidate cuts for orbit disjointness: its successful 835 controls could not
establish that a private cut universally exists. This document supplies the
missing unbounded walk-order argument and an extraction choice which does
not test privacy to select its cut.

No capacity table, complete NR6 walk, frontier, other cell, or continuation
was computed in this round. The accepted baseline on entry is 10/55 and
provisional `(3,2)` closure. Only after this proof is it advanced to 11/55.
NR6 remains ASSUMED; `L6 >= 872` is NOT PROVED.

## 1. Frozen definitions and quantifiers

A complete no-repeat permutation walk gives a sequence of maximal passes
`p_i=(v_i,l_i)`, each with l_i literal rotation windows. A REGISTERED orbit is
an E-orbit containing a pass ENTRY v_i. A rotated window inside a pass is
visited, but its own E-orbit is not thereby registered. All orbit sets below
refer only to pass entries, never all visited windows.

Write q_i=orb_E(v_i). A run is a maximal constant-q interval of pass indices.
A repeat opening is an index k at the beginning of a run for which q_k already
occurred at a smaller pass index. Repeated targets at different times are
distinct events. `e` counts these openings.

Let nu(i) be the index of the registered arc beginning at sigma^(l_i)(v_i).
Full passes have nu(i)=i. Complete coverage and no-repeat give this registered
successor on each split hexagon. Free short exits go to E(v_nu(i)); thus a
free nu-DESCENT opens an already registered orbit. Let D_free be the set of
these opening events, and define

    a = number of nonfree nu-ASCENT exits,
    eta = number of repeat openings not in D_free,
    delta = a+eta.

These are the accepted Round136 definitions, not a new capacity bound.

In the seven surviving rows, delta=1,F=2,G=2,x=H=0. The residual mechanisms are:

* M: a=1,eta=0, off-target paid opener 201/210. Every paid opening is fresh.
* R: a=0,eta=1, both free ascent targets fresh, with the single exceptional
  paid return targeting T0 or T1. The previously absorbed 120 cases are excluded.

For complementary arcs `p_i=(v,a)` and `p_j=(c,6-a)` with c=sigma^a(v), the
EXTRACTED INTERVAL is exactly `I={i+1,...,j}`, including the closer but NOT the
opener. Its intermediate passes are full. The inside word retains these pass
entries and completes the last pass at c to length six. The outside word
replaces `p_i,...,p_j` by `(v,6)` and retains every other entry. Completion adds
windows, not registered entry orbits. One other ordinary locked block is
contracted either before or after this operation as specified in section 5.

**Formal R137-P.** For every complete NR6 walk in either surviving mechanism,
the canonical choice in section 5 exists, and the resulting full-pass pieces
satisfy

    {orb(v): v is an entry of C_in}
      intersect {orb(v): v is an entry of C_out} = empty.

There is NO permitted shared-orbit exception for a boundary or the split
hexagon. The two complementary entries v,c belong to different E-orbits
(their last symbols differ). One hexagon can be shared without sharing an
orbit. R's root orbit occurs twice *inside* C_in, and nowhere in C_out.
The assertion is not about an arbitrary interval or an arbitrary extraction.

## 2. Short-last and boundary separation — symbolic facts

With x=H=0, a full pass followed freely moves by E within its orbit. Every
genuine light joint after a short pass changes its entry orbit. To see this
symbolically, w2 and tails 120/210 end with the source endpoint's first symbol,
which differs from the pass entry's last symbol. Tail 201 ends with the
endpoint's second symbol; this too differs except when the pass length is
five. In that exceptional length-five case, writing the entry as abcdef, the
target is bcdaef: the same last symbol f, but bcdae is not a cyclic rotation
of abcde (the unique rotation starting b is bcdea). Thus its E-orbit still
differs. A short pass is last in its run. One must NOT replace this argument
by the false assertion that all short w3 joints change the last symbol.

At the chosen cut, both the opener and the closer are short. Hence I begins
and ends at run boundaries. If the closer is the final pass, there is simply
no right outside part. No run can straddle either cut boundary. This point
is essential: without it, a shared orbit need not require a new run opening.

Complementary arcs tile the split hexagon symbolically: the rotation offsets
are `{0,...,a-1}` and `{a,...,5}`. Their windows are disjoint, cover that
hexagon, and the second arc ends at sigma^5(v). The merger preserves both
external literal endpoints. These facts do NOT by themselves imply orbit
disjointness. A single E-orbit has five different entry hexagons, so occupying
different phases on different sides is locally possible.

## 3. The run-interval separation lemma — arbitrary-length hand proof

Consider any finite run sequence with a consecutive inside interval I and
outside left/right parts L,R. Suppose the following EVENT conditions hold.

1. I is a union of whole runs.
2. A set B of boundary-return orbits is registered in L before I starts.
3. No ordinary free-descent opening occurs inside I; every ordinary opening
   after I, if present, targets B.
4. In M there are no exceptional repeat openings (eta=0). In R the one
   exceptional opening is INSIDE I, targets a distinguished orbit T whose
   first registration is inside I, and T is not in B.

There is no restriction on lengths, number of fresh orbits, phase deficits,
or prior multiplicities in L. The lemma is not a finite-state quotient.

**Left-to-inside crossing.** Suppose Q appears in L and I. Choose its earliest
run opening inside I. Because no run straddles the left boundary, this is a
repeat opening. It cannot be ordinary by (3). It cannot be R's designated
exception: that target T was not registered in L. Thus this is an additional
exception, impossible in M or R's stated budgets.

This proves in particular `B intersect orbits(I)=empty`, without assuming it
as a premise: all B was registered in L.

**Inside-to-right crossing.** Now suppose Q appears in I and R but not L.
Choose its first run opening in R. It is a repeat, since Q occurred in I and
the right cut is a run boundary. If ordinary, its target belongs to B, which
has just been proved absent from I. R's designated exception is already inside
I. Thus this too is an additional exceptional opening, impossible.

If Q occurs in all three regions, use the first argument. These cases exhaust
all crossing patterns. A single shared orbit is already impossible.

### Injective charging version (no double counting)

For every shared orbit Q choose the first inside opening if Q occurs in L;
otherwise choose its first right opening. Chosen openings for different Q
have different targets and hence are distinct events. None is an ordinary
free-descent event, nor R's already designated internal return. Therefore,
if s shared orbits were allowed while retaining these event/geometry premises,

    M: a>=1, eta>=s;        R: eta>=1+s;
    in either case delta>=1+s.

For delta=1 this forces s=0. It is NOT the false assertion that every return
costs delta: ordinary free descents may reopen B, and R spends its one eta
unit on an internal return. The map deliberately charges neither event twice.

In an orbit-intersection graph, color each run occurrence L/I/R while retaining
the directed opening EVENT as an edge. A vertex incident to I and its outside
has the selected additional opening above. Collapsing event multiplicities
would lose exactly the information needed for this invariant.

## 4. Establish the premises without assuming privacy

### 4.1 A private ordinary block, independently of R137-P

For an unaffected free ascent with target T, suppose its opening is fresh
and no later allowed repeat opening can target T. Its next nu-arc c must be
visited by completeness. All T entries must then lie in the same run: a later
run would be a prohibited reopening. That run starts at E(c), ends at c
(short-last), and under x=0 follows the complete five-phase E cycle. It has
no outside T registration and all five deleted joints are free. This proves
the ordinary block's privacy directly; it does not invoke the two-piece lemma.

When such a block is contracted, its orbit disappears everywhere. Other
registered-orbit orders are retained. The only possible coalescence of
adjacent runs is at the surviving opener orbit Q: a free closer return E(v)
now becomes an intra-run E step, deleting exactly that ordinary repeat
opening. A retained 201/210 paid boundary cannot coalesce there: when the
merged source becomes full, only literal 120 targets Q. If the merged source
stays short, no genuine light joint can target Q. The absorbed 120 subset is
not in this round's residual domain.

Consequently the reduced word retains M's one paid fresh opener or R's one
paid repeat; no other exceptional opening is created or hidden. One free
ascent is removed; if beta concatenation removes a descent return, the
ordinary repeat event disappears with it. The resulting G1 nu-structure is
exactly one complementary pair, with the same M/R exception. No inference
from scalar delta alone is used here.

### 4.2 The normalized G1 cut

After an ordinary-first reduction, denote the remaining opener orbit by Qv,
the closer's orbit by T, and set B={Qv}. B occurs at the opener, hence in L.
There are no short passes inside I except its final closer. The only
remaining ordinary return is the free exit of that closer, AFTER I, targeting
Qv. This establishes conditions (1)-(3) of section 3.

M supplies (4) directly by eta=0. R starts I with the fresh free entry E(c)
into T. Its designated exceptional return must be inside I: it cannot precede
the fresh opening; if it occurred only after the closer, the first T run
would already contain c and sweep all five E-entry ports, making any later
T entry a literal repetition. With no other short descent inside I there is
no ordinary way to leave T and revisit c. Thus the exception precedes the
closer and lies in I. T!=Qv by complementary-arc last symbols.

This establishes all conditions of the separation lemma, including for the
root-return orbit T itself. Finite phase-slot capacity is used only for this
five-port timing fact, not to assert that arbitrary shared orbits overflow.

### 4.3 The beta inner-first cut

Write Qi=orb(opener_i), Ti=orb(closer_i). The only ordinary return targets in
Type B are Q0,Q1. For the cases needing inner-first extraction, T0=Q1 and
the exception is associated with opener1/T1, not an exceptional return to Q1.
The first Q1 run must contain opener1: otherwise reaching opener1 later
would require the closer1 return before opener1 itself. After opener1, the
only available Q1 reopening is the free exit of closer1. Reaching closer0
therefore forces

    opener0 < opener1 < closer1 < closer0,
    and closer1 exits freely to Q1.

Set I=(opener1,closer1] and B={Q0,Q1}. These boundary orbits are already
registered before I. The other two short passes are outside I, so there is
no ordinary descent inside. Both possible ordinary returns target B and
occur after I. In R, T1 is fresh after both Qi were registered and hence
different from B; the same five-port timing argument places its exceptional
return inside I. In M no exceptional return exists.

Section 3 now proves privacy for this inner cut BEFORE any assumption of
orbit disjointness. Extracting it completes opener1; the remaining outer
Q1=T0 pieces rejoin as an ordinary E block. Since Q1 belongs to B, not I,
the subsequent ordinary contraction removes no orbit from the inside piece.
Removing outside entries cannot introduce an intersection.

## 5. Exhaustive canonical case choice — Type A and B separately

The choice uses only nu-order, which opener is paid, and the exceptional
target. It does not call a privacy predicate or select a successful sample.

| Mechanism / geometry | First operation | Privacy lemma applied |
|---|---|---|
| M, Type A, either paid ascent | Contract the other free ascent block | normalized G1, B={Qv} |
| R, Type A, target T0 or T1 | Contract the other ascent-target block | normalized G1, B={Qv} |
| M, Type B, paid opener0 | Contract fresh later T1 block | normalized G1 |
| M, Type B, paid opener1, T0!=Q1 | Contract unaffected T0 block | normalized G1 |
| M, Type B, paid opener1, T0=Q1 | Extract inner opener1/closer1 gap first | beta, B={Q0,Q1} |
| R, Type B, exception targets T0 | Contract unaffected fresh T1 block | normalized G1; accepted 120 absorption already excluded |
| R, Type B, exception targets T1, T0!=Q1 | Contract unaffected T0 block | normalized G1 |
| R, Type B, exception targets T1, T0=Q1 | Extract inner opener1/closer1 gap first | beta, B={Q0,Q1} |

Why every listed ordinary block qualifies for section 4.1:

* In Type A, F=2 forces the chronological three-arc nu-cycle. Its three
  entries have distinct last symbols, hence distinct E-orbits. The only
  ordinary descent target is the first arc's orbit. The unaffected ascent
  target differs from it and from R's exceptional target. It has no allowed
  later reopening. The contraction merges two adjacent rotational arcs,
  leaving the complementary pair used in section 4.2; no Type-B assumption
  is imported here.
* A later fresh T1 differs from both Q0,Q1 (already registered), and from T0
  when both ascents are free. In the rows where T1 is contracted the exceptional
  target, if any, is T0. Therefore T1 has no allowed reopening.
* The earlier T0 always differs from Q0. When T0!=Q1 and the unique exception
  does not target T0, neither ordinary return nor the exceptional return can
  reopen it. When T0=Q1 the beta argument is used instead, not this lemma.

These cases exhaust Type B because there are only two doubled hexagons and
two ordinary-return target labels. Type A's single tripled hexagon was handled
separately. The already accepted M-aligned, unrelated-R, and absorbed nested-R
subcases are neither reopened nor needed as finite observations in this proof.

## 6. General deficit accounting and seven-row consequence

If an extraction with one valid ordinary deletion were to leave s shared
E-orbits, its pieces' union would have 26 orbits and their total would be
26+s by inclusion-exclusion. The sum of pass counts is 117, so definitionally

    D_in+D_out = 5(O_in+O_out)-(P_in+P_out)
                  = 5(26+s)-117 = 13+5s.

The explicit split HEXAGON does not add an orbit exception or change this
formula. The audit's sensitivity at s=1 is therefore real. Section 3 and
section 5 now establish s=0 universally for the canonical cuts, not merely
in sampled controls.

For precision, the formula assumes one orbit actually disappears from the
UNION of the two pieces, not just from the outside piece. More generally, if
r orbits disappear from that union then the identity is `18-5r+5s`. An ordinary
deletion before extraction has r=1 by section 4.1. In beta inner-first order,
section 3 proves the subsequently removed boundary orbit Q1 is absent from
the inside piece, so r=1 there too. Merely removing Q1 outside without this
argument would not justify even the proposed `13+5s` identity. No such
outside-only deletion is used as a substitute for global orbit removal.

| Row | Mechanisms needing privacy | Applicable cases | Status |
|---|---|---|---|
| A/e0 |M|Type-A M|proved|
| A/e1 |M,R|Type-A M/R|proved|
| A/e2 |R|Type-A R|proved|
| B/e0 |M|Type-B M alternatives|proved|
| B/e1 |M,R|Type-B alternatives|proved|
| B/e2 |M,R|Type-B alternatives|proved|
| B/e3 |R|Type-B R alternatives|proved|

The already independently confirmed M bound 112 and R bound 103 are both
strictly below the required 117 when the total deficit is 13. They were NOT
recomputed here. Hence all seven rows close, `(3,2)` closes under NR6, and
the accepted conditional ledger may advance from 10/55 to 11/55. This uses
the supplied prior eighteen-row exclusions without re-auditing them.

## 7. Active falsification and finite controls — supporting evidence only

Replayed all 835 preserved literal cuts, 10,800 positional identities, and
3,600 complementary tiling/exterior-endpoint controls. The new counterexample
domain does not pre-filter privacy: at each frozen cut neighborhood, try
every port of every inside orbit as a FULL pass before or after the word.
No delta/resource check is used before literal replay. This covers 19,818
specified configurations on n=4 and n=6; no n=5 or global search was needed.

There are **67 legal sharing configurations, representing 15 distinct literal
words** (8 n4, 7 n6). All have delta=2, x=H=0. M examples have a=1,eta=1;
R examples a=0,eta=2. Some controls use the normalized G1 word; four are still
G2,F2 M configurations. Thus sharing is not prohibited by no-repeat, G2 alone,
or immediate five-slot overflow. It is prohibited by the remaining defect
budget together with the canonical interval's event structure.

One smallest-in-this-enumeration G2/F2 local n6 example is:

    5301245301234501253401253041253024153024513024501324501234051230451230541230514230512430512340

It visits 72 literal windows, has P14,O5,D11,e2,x=H0,a1,eta1,delta2,
and an external shared orbit with representative rank 4. This is a LOCAL
positive control, not a complete NR6 counterexample or a proof of extendability.
It explicitly identifies the global/resource hypothesis excluding it from
the seven delta1 rows. Minimality is only within the enumerated context domain.

The event-order CSP exhausts 12,972 canonical symbolic models on at most seven
RUNS, with one or two boundary-return labels. It deliberately allows more
ordinary outside returns than a literal F2 word; this is an over-approximation.
Every hypothetical shared vertex has its injectively charged extra event;
no delta1 countermodel exists. A separately implemented set-partition generator
reproduces the entire histogram. This finite CSP is NOT the unbounded proof:
the explicit injection of section 3 works for arbitrary run counts.

No modified cut, shared-orbit capacity, or new theorem search is required.

## 8. Source-certificate correction — explicit, new record

The old Round137 field `source_sha256` for `src/chain_capacity_115.c` was
ambiguous about working-tree versus committed bytes:

* recorded / actual CRLF working tree:
  `c7694b66f3d31770f5ed9d91b7b61a1973c2138d22513a0d7ca40615dc74544a`;
* actual committed blob in `ec8a5f1aaa2d5b42dc885dca86420877287555aa`:
  `2287c05efdfe0cb521a9175b100c71546b0ea386f63e299cbb1e16b271574edb`.

There are 202 CRLF lines locally and zero in the committed blob; replacing
CRLF by LF produces BYTE-FOR-BYTE equality. The old hash is not a remotely
verifiable committed-source hash, but is reproducibly the local source hash;
there is no different C algorithm hidden by it. The new correction certificate
records both with explicit roles, the pinned commit, and old-certificate SHA.
No historical certificate, source, or capacity result was overwritten.

## 9. Audit trail and result

Producer source was committed and pushed as `5b3caa7` before finite tests;
independent verifier source as `438ef4c`. Full commits, source/runtime SHA256,
argv, domain node counts, cap status and digests are in the JSON. The universal
theorem is the hand proof above; scripts check only its specified finite
controls and provenance. All scopes remain explicit.

    python src/research_round138_privacy_codex.py
    python src/verify_round138_privacy_codex.py

The producer requires current HEAD pushed to the Round138 branch. Neither
command launches capacity or continuation searches.

The ten new regression tests pass, including corrupt delta/orbit rejection,
the short-length-five same-last-symbol exception, accepted internal R return,
independent CSP histogram conservation, and committed-source hash validation.
`py_compile` and whitespace checks pass. The prior result files remain byte
identical to the pinned Round137 commit.

ASTRA_R137_PRIVACY_PROVED
