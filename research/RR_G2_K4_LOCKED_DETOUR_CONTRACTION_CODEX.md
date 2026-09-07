# Locked-detour contraction closes the remaining Type-B (k,G)=(4,2) cases

Author: Codex. Scope: NR6 is assumed. This is a new contraction proof using
the independently replayed **local** Round-115 chain-capacity certificate.
It is not a 122-pass search, a capped-exhaustion claim, or a global L6 bound.

## 1. Precise conventions and dependencies

A pass `(v,b)` visits the b rotation windows starting at word v; b counts
windows, not rotation edges. Write sigma for left rotation of all six symbols
and E for left rotation of the first five, fixing the sixth. S is the number
of joints of weight at least 3, **not** the historical strand-count convention.
O counts E-orbits of registered pass entries, not orbits of all visited windows.

Use the accepted Round-128/131/132 statements in their corrected scope:

* hypothetical Type-B cell walk: P=122, O=28, D=18, S=25, H=x=0;
* only two hexagons are split, each into an opener/closer pair;
* equality f_out=F+e and x=0 force the exhaustive alpha/beta lock taxonomy;
* alpha, including Model T, has two disjoint locked intervals;
* beta has an inner locked interval, followed after its contraction by an outer
  locked interval. The beta internal ten joints are all weight 2.

No assumption Q0!=Q1 is made for P1-alpha or Model T. No reversal symmetry,
arbitrary orbit relabeling, or n=4 absence is used. G is multiplicity excess;
F is abandonment. We do not identify these outside the specified Type-B walk.

## 2. Boundary-preserving detour lemma — hand proof

The statement works for n>=4. Put d=n-1, 1<=b<=n-1, and c=sigma^b(v).
A locked block has exactly the pass list

    (v,b), (E c,n), (E^2 c,n), ...,(E^(n-2)c,n), (c,n-b).

There are n passes and n-1 internal joints, all weight 2. Replace this list by
the single full pass `(v,n)`.

**Entry and exit.** The entry is v in both lists. The old final word is
sigma^(n-b-1)c=sigma^(n-1)v, exactly the new full-pass endpoint. Every external
incoming/outgoing joint therefore has the same source word, target word, tail,
weight, and intermediate literal windows as before. This includes blocks at
either endpoint of the whole walk; an absent external joint stays absent.

**No-repeat.** The new pass contains precisely the union of the old opener
and closer windows: sigma^0(v),...,sigma^(n-1)(v). All other retained passes
are unchanged. Thus the new literal permutation-window set is a subset of the
old set. The shortened word does not invent a joint or a hidden permutation
window. No-repeat is preserved. It is not necessary to preserve coverage of
the hexagons that the contraction deliberately removes.

**Orbit accounting.** The removed pass entries E c,...,E^(n-2)c,c are all d
distinct ports of T=orb(c). T differs from Q=orb(v), because two distinct
rotations of a permutation have different last symbols. All ports of T were
registered inside the block, so no other pass in the original no-repeat word
can have an entry in T. Exactly one registered orbit disappears; Q remains.
The fact that c remains *visited* inside the new full pass does not register T.

**Hexagon accounting.** Distinct ports of an E-orbit lie in distinct rotation
hexagons. Its c port belongs to h(v), which is retained; the other n-2 full
hexagons disappear. Equivalently, no-repeat already guarantees these full
passes cannot share any hexagon with a retained pass.

Consequently each contraction has exact deltas

    Delta P=-(n-1), Delta O=-1, Delta D=0,
    Delta S=Delta H=0, deleted literal windows=n(n-2).

The S/H conclusion is not heuristic: the deleted joints are all weight 2 and
every external joint is unchanged. No continuation-state equivalence is
claimed. This is a one-way map from a hypothetical complete word to a shorter
**partial** no-repeat word, used only for an upper-bound contradiction. QED.

As a separate literal length check, each contraction removes n^2-n-1
characters (29 at n=6). Two contractions would map the hypothetical length
871 word to a length 813 partial word; no global complete-cover length formula
is applied to that partial word.

## 3. Two contractions cover every remaining family — hand proof

### Alpha: P0, P1-alpha, D-alpha and Model T

Contract each of the two disjoint locked intervals. The intervening gap is
left literally unchanged. Its length, occupied hexagons, and possible opener1
words do not have to be classified. T0 and T1 cannot be the same removed orbit:
either interval already registers all its ports and no-repeat forbids using
any of those entries in the other interval. This argument does not require
the opener or repeat orbits to be distinct. It therefore includes Model T.

### Beta: P1-beta and D-beta0

Write c0=sigma^b0(v0), v1=E^u(c0), 1<=u<=n-2. The known beta list is

    (v0,b0), E c0,...,E^(u-1)c0,
    [locked detour at (v1,b1)],
    E^(u+1)c0,...,E^(n-2)c0,(c0,n-b0),

where all entries outside the four short passes are full passes. Contract
the bracket first. It becomes the missing full pass E^u(c0); the entire
remaining displayed interval is now exactly the single-lock template at
(v0,b0). Contract that interval second. The first removed orbit differs from
orb(c0) by the first lemma; both disappear exactly once.

These operations work in the original outside context; the repeat-run
location and whether the last closer exits freely need no additional cases.

## 4. Contracted-chain theorem — hand proof

Starting from the cell's exact data, two contractions give

    P'=122-10=112, O'=28-2=26, D'=5*26-112=18,
    S'=25, H'=0.

All four short passes have been replaced, so every retained pass is full and
the resulting word visits **112 distinct complete hexagons** (672 permutation
windows). It is NOT a complete NR6 cover; no global terminal hypothesis is
applied to it.

In a full-pass word, weight 2 stays inside the current E-orbit. Hence every
run boundary has weight at least 3. If r' is its run count and x' counts paid
intra-run joints, then

    S'=(r'-1)+x',  r'=O'+e',  e',x'>=0.

Substitution gives `25=25+e'+x'`, so **e'=x'=0**. This is preferable to
assuming repeated runs cancel: their disappearance is forced by independently
preserved S' and O'. Since H'=0, the result is one all-light chain with no
repeated orbit, no paid intra-orbit joint, and deficit 18.

## 5. Local capacity obstruction — existing finite complete calculation

The independently replayed Round-115 certificate states

    N*(b=0,g=0,s=20)=103,
    nodes=2,465,729,298, capped=false.

The exact C source SHA-256 is
`c7694b66f3d31770f5ed9d91b7b61a1973c2138d22513a0d7ca40615dc74544a`.
It matches `src/chain_capacity_115.c` in this worktree. The full original
source-replay result and audit are embedded with hashes and original paths in
`outputs/rr_g2_k4_contraction_certificate_codex.json`. The old replay used a
fresh Zig-compiled binary and reproduced the source node count; this round
does not misrepresent it as a newly independent search formulation.

### Why this is a local bound, not a forbidden global import

At b=g=0 the source enumerates partial chains of any length. It updates a
maximum at every state whose total phase deficit is <=s; it has no terminal
requirement of 120 passes, 720 windows, fixed O, or global coverage.

* In-run edges include the next E phase whenever its hexagon is unused.
* Between-run edges include both legal weight-3 inter-orbit tails from the
  full-pass endpoint. An independent literal census checks this for all 720
  words; the third weight-3 tail is same-orbit and excluded by x'=0.
* The b=0 rule requires every new run's orbit to be fresh, exactly as e'=0.
* The g=0 rule gives no handoff tokens; this is one chain, so none is needed.
* The sole deficit prune omits the current orbit's deficit while it may grow.
  Every exited orbit is permanently exited, so its unused phases cannot later
  decrease. Their sum is <= the final D'=18<=20 on any candidate chain.
  Consequently this prune cannot remove the contracted word.
* Left symbol renaming sends any first word to 012345 and commutes with every
  move. No extra symmetry assumption is needed.

Thus the contracted chain would be accepted by the model used for the bound.
It requires **112<=103**, a contradiction. Using s=20 rather than the tighter
s=18 deliberately enlarges the model. There is a nine-pass gap, not an
off-by-one terminal issue.

## 6. Result and exact scope

**Both B/e=1 and B/e=2 are excluded.** With the already accepted Type-A and
B/e=0 results, the NR6 `(k,G)=(4,2)` cell closes. The 118 Round-133 remaining
split classes go to 0 without searching them individually:

| Family | R133 remaining | After contraction/capacity proof |
|---|---:|---:|
| P0-alpha | 25 | 0 |
| P1-alpha | 25 | 0 |
| P1-beta | 15 | 0 |
| Model T | 16 | 0 |
| D-alpha | 25 | 0 |
| D-beta0 | 12 | 0 |

The outer count is **10/55 conditional on the previously accepted nine-cell
ledger**, not a new independent audit of those nine cells. NR6 remains assumed.
This project has **not** proved L6>=872.

## 7. Counterexample-first experiments and limitations

`research_alpha_gap_codex.py` preceded the contraction idea. It checked the
phase-footprint identity on all n=4,5,6 words and every split. In particular
b=1 with a free closer collides immediately: the target E(v) is already in
the full pass E^-1(sigma(v))=sigma^-1(E(v)). This is a separate small lemma,
but its modest class reduction is superseded by the contraction theorem.

The attempted small-image gap restriction failed at the **local** level:
the occupancy-relaxed graph admits 690 endpoint ports for each viable first
exit. Exact literal local gaps of at most seven full passes already admit
hundreds of second-opener words and paid-gap-cost>=3 witnesses. These are
not complete NR6 covers and do not refute any claim restricted to extendable
complete words. The exploratory P1-alpha generator additionally required
Q1!=Q0; its output is a restricted control set, not an exhaustive census of
P1-alpha. The contraction proof does not use that restriction or any gap count.

`verify_locked_detour_contraction_codex.py` tests all 3,600 single n6 detours,
all 1,500 start-normalized rigid beta/T configurations with literal collision
checking, preserved alpha-gap witnesses, and all Type-B x=0 equality controls
from the exhaustive NR4 length<=39 corpus. It verifies entry/exit, literal
no-repeat, exact deleted-orbit/window counts, S/H/D, two contractions, and
e'=x'=0 in the tested two-block words. These controls test a hand proof; they
are not the justification for extrapolating n4 absence to n6.

The first NR4 control attempt exposed a **test-harness limitation**: the
local n6 replay checker intentionally listed only weights 2/3, while valid
NR4 controls can contain weight 4. The control-only joint list was extended
by directly checking all weight-4 tails, without filtering those controls or
weakening the theorem. Failed attempt commit: 174dc76; correction: 1861615.

Mutation tests reject missing locked phases, wrong complement lengths and
repeated windows; the full-pass-to-capacity move mapping is checked separately.
No production engine, checkpoint, old output, or pruning rule was changed.

Final controls strengthen the initial run: commit 911a81e replaces the NR4
sample-source call with a separately implemented adjacency-based exhaustive
generator, including exact DFS node accounting. It independently regenerates
the same 29,255 complete NR4 controls before selecting the 25 equality cases.
The persisted-word verifier does not import the block generator or its replay
function: it scans literal strings, reconstructs passes and joints, checks
all resource fields, and compares the entire list of paid source/target joints.

### Recorded verification results

| Check | Exact result |
|---|---:|
| Independent NR4 DFS nodes, no cap | 49,682,345 |
| NR4 complete walks, length<=39 | 29,255 |
| NR4 Type-B equality x=0 controls | 25: alpha 9, beta 16 |
| Single n6 detours checked | 3,600/3,600 |
| Beta-e1 configurations, input / legal / contracted | 500 / 234 / 234 |
| Beta-e2 configurations, input / legal / contracted | 500 / 153 / 153 |
| Model-T configurations including final free exit | 500 / 57 / 57 |
| Preserved literal alpha-gap controls contracted | 56/56 |
| Independent original/contracted literal string pairs | 525/525 |
| Regression tests | 9/9 |

The final finite-control run took 68.931 seconds. Its source commit is
`911a81e` and deterministic digest is
`9ad369bae7a3e2a32e5a3de0c695703940a6a77173a2e9d0bba3ef4c537d59ad`.
The independent persisted-word verification used commit `3403017`.
Detailed raw SHA-256 values, interpreter binary hash, full argv and counts
are in the JSON artifacts; the inherited capacity computation is separately
identified and was **not rerun** as part of these counts.

## 8. Reproduction and next action

    python -m unittest discover -s tests -p test_locked_detour_contraction_codex.py -v
    python src/verify_locked_detour_contraction_codex.py
    python src/certify_g2_k4_contraction_codex.py
    python src/verify_g2_k4_contraction_certificate_codex.py

The last command assembles the dependency ledger from the preserved Round-115
audit sibling; its final JSON embeds those inputs so external reviewers need
not have that local path for the independent persisted-word verifier. New
certificate files have byte-preserving Git attributes. The original capacity
source raw SHA is retained alongside its LF-normalized SHA and Git blob ID,
so Windows CRLF versus Unix LF is explicit, not a source mismatch ignored by
the verifier. The original n6 capacity command is
`chain_capacity_115 0 0 20` (default safety cap 20,000,000,000; completion at
2,465,729,298, not cap exhaustion). Source is preserved; no rerun is needed to
use the already replayed certificate.

Next: independently review the context-preserving contraction and the local
capacity embedding, then integrate this one cell into the official ledger.
No G>=3 or other-cell search has been started.
