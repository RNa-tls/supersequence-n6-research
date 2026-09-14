# Round 150 — universal feasibility-pruning audit

Base: `195d11bdbfa68666b118010232258686195893fc`, descended from canonical
R148 `583f0b6`. Author: Codex. No frontier reconstruction or continuation search.
This round accepts the catalogue/extraction scope specified in the request;
it does not re-audit Round149 or silently identify that separate Opus audit
with the earlier Astra suffix audit.

## 1. Exact completion problem, independently of DFS

Let V be the 720 permutations and let tau rotate the first five positions.
Its 144 disjoint orbits each have five ports. A chain is a sequence of distinct
ports joined by allowed catalogue connectors. Internal literal windows of
connectors need not be distinct: the model intentionally permits repetition
there. Only entry ports are ownership objects in the masks. The rotation
hexagons track repeated-hex arrivals, not all internal windows of the word.

A partial state consists of a used-port set U, its current endpoint v in U,
the hexagon counts induced by U, and used resources. It need not have been
reached by the production pruned DFS. In particular all phase-hole patterns
are allowed in this theorem. Let o be the orbit of v and O the orbits meeting U.
For q in O, put u_q=5-|U intersect q|, an integer in [0,4]. Then

    D(U) = sum_{q in O} u_q = 5|O|-|U|.

A completion appends zero or more unused ports along catalogue edges. Free-E
is tau, remains in the current orbit, and costs no token. Every other edge
landing in an already opened orbit costs one token, including a same-orbit
non-E edge. Landing in a fresh orbit costs no token. These costs do not depend
on whether the edge is dirty A, dirty B, ordinary or heavy.

The other independent resource coordinates are at-most budgets: a for A,
bb for B, e for ordinary repeated-hex arrivals (including a repeated-hex free
E or heavy arrival), h for sum(max(weight-3,0)). A/B arrivals use their own
labels instead of e. A legal recorded completion must obey all these budgets
and have final D<=d. A target query additionally demands P>=P_target (or P
equal to the witness target). The theorem below is stronger: rejection prevents
*every* terminal D<=d, regardless of P_target.

Invariants: masks never lose ports during a forward continuation; current v
is present; exactly the nonzero masks are opened; counts agree with masks;
there is one active endpoint; tokens are nonnegative and never replenished;
the listed charging rule applies to every orbit-changing move. Backtracking
restoration is not a forward continuation. Invalid signed budgets, empty
"opened" masks, free restarts at another endpoint and arbitrary mask clearing
are outside the theorem and must never be presented as admissible states.

## 2. Independent derivation: Token-Touched-Orbit Deficit Lemma

Let T be the set of noncurrent orbits already opened at this state which gain
at least one port during a chosen completion. For each q in T, consider the
FIRST appended port in q. Just before it, the endpoint is outside q: the
initial endpoint is outside q, and no preceding appended port lay in q.
Thus this first entry is not free-E. Orbit q was already open, so that move
spends a token. Distinct q have distinct first-entry moves. Consequently

    |T| <= k,  where k is the remaining token budget.

Every untouched old noncurrent orbit retains its entire u_q deficit. All
other final contributions, including the current and fresh orbits, are
nonnegative. Therefore for EVERY completion, with no geometric reachability
assumption on T,

    D_final >= sum_{q not in T, q != o} u_q
            >= min_{S subset O\{o}, |S|<=k} sum_{q not in S, q != o} u_q.

Call the final minimum L(U,o,k). This is a lower bound on required final
deficit, not an upper bound on capacity. It grants each token permission to
erase a whole orbit regardless of phase holes or hexagon collisions. Such
erasure need NOT actually be feasible. Granting extra freedom only lowers L.

This argument is uniform over arbitrary finite orbit families and resource
values; it neither mentions t nor relies on the 383 historical witnesses.
It explicitly includes q0 returns and repeated returns. Multiple returns
consume additional tokens; counting just the first one per orbit is safely
optimistic. Finishing the current orbit for free is also safely optimistic.

## 3. Dual certificate, without the greedy implementation

For any integer lambda>=0, every set T of size at most k satisfies

    sum_{q not in T} u_q
       >= sum_q min(u_q,lambda) - k*lambda.

Proof: cap untouched u_q downward; then subtract at most k capped terms, each
at most lambda. Hence a certificate (lambda, masks, current, k, d) with

    sum_q min(u_q,lambda) - k*lambda > d

proves rejection using only elementary integer arithmetic. For u_q in [0,4]
it suffices to try lambda=0,1,2,3,4. The verifier `certificate150.py` checks
this inequality and mask-domain invariants, not production sorting or feas().

Equality with L follows by ordering the deficits descending. If k covers all
positive entries use lambda=0. Otherwise take lambda equal to the (k+1)-st
entry. Removing the k largest attains this dual value. Thus the dual bound
and the subset-allocation optimum coincide, including ties and zero entries.

This is a prospective per-prune certificate API. Historical runs did not
emit these certificates. We do NOT claim all old prunes were certificate-
replayed; universal proof plus implementation conformance is success route A,
not a fabricated historical execution of route B.

## 4. Every production clause and its direction

There is ONE rejecting condition inside feas: `return tot <= DMAX` (DM in B).
The other branches construct a lower bound; they do not separately reject.

| code | role | standalone justification |
|---|---|---|
| skip current orbit | relaxation | its nonnegative deficit can be erased free |
| skip zero count / enumerate opened only | exact domain | unopened orbits owe no present deficit |
| 5-popcount(mask), or 5-ocnt | exact | distinct entry ports partition tau-orbits |
| hist[0] not processed | exact | full old orbits contribute zero |
| loop d=4 down to 1 | minimizing residual | exchange a smaller erased deficit for a larger one cannot increase residual |
| take=min(hist[d],left) | exact relaxed allocation | erase no more orbits than exist and no more than available tokens |
| left-=take | exact | each erased orbit consumes one of the relaxed tokens |
| tot+=(hist[d]-take)*d | exact | sum untouched deficit at this level |
| reject tot>DMAX | necessary-condition failure | D_final>=L=tot>DMAX |

Each construction has a standalone implication above. It is incorrect to
describe each `continue` as its own rejection clause. There is no parity
assumption, no phase-contiguity assumption and no hexagon-privacy assumption.
Integrality enters only the count of touched orbits and histogram deficits.

The exchange/dual derivation is IDENTICAL to production feas. A/B use the same
mathematical condition and count as ONE conceptual implementation, despite
mask-versus-count representations. Five C implementations are recorded with
their exact function text, source hashes, definition lines and call sites in
`certs/source_conformance.json`; the older R144 callers are not revived as
independently sound entire solvers by auditing this one shared function.

## 5. Operational inductive check

As an alternative to looking ahead, L is nondecreasing under allowed moves.
Free E changes only the excluded current deficit. A fresh-orbit move adds the
old current nonnegative deficit to the multiset and does not increase tokens.
An old-different-orbit move removes that target deficit, adds the previous
current deficit and decreases tokens by one. Any k-1 erasures afterward,
together with the removed target beforehand, were available among k erasures
beforehand. Thus the earlier optimum cannot exceed the later one. An
old-current non-E move decreases k without removing a multiset term. At a
terminal state L<=D_current. Induction reproves D_final>=L_initial.

## 6. Budget monotonicity and domain pitfalls

All six production budgets (tok,d,a,bb,e,h) are AT MOST, not exact labels.
The same completion remains legal when any upper budget increases. In feas
alone tok makes L nonincreasing; d weakens the final comparison; a,bb,e,h are
not read, so their effect is exactly zero. This is not the exact-A convention
of some older suffix queries and must not be conflated with it.

D_current may decrease on revisiting old orbits. The proof never prunes on
D_current>d alone: it bounds the deficit which tokens cannot remove. Zero
tokens do not mean the current orbit is full. Its missing phases remain free
in the relaxation. Negative tok would invalidate histogram arithmetic, but
callers initialize nonnegative tok and reject an edge before spending beyond
it. Opened-list masks remain nonzero across each recursive invocation.

Dirty A/B, ordinary collisions and heavy edges are covered by the same first-
entry token injection. Extra charging restrictions can only shrink the set of
continuations. Repeated connector-internal windows do not erase entry masks.
Only distinct entry ports are needed for D=sum u. Multiple chains are handled
by applying the theorem separately to each chain's own state/budgets, never
by letting a second free endpoint enter an old orbit in the same query. Cycle
deletion and chain splitting happen before this path problem is initialized.
Deleting edges preserves vertices and allocates new component budgets; it is
not a free-restart operation within rec(). Merging likewise requires a real
connector and its normal token charge. These scope conditions are essential.

## 7. Finite adversarial work — evidence, not the universal proof

The independent dual/subset DP and literal-mask completion DP never call
production feas. Five extracted C bodies were compiled and compared on
179,850 input cases. The full multiset domain has <=8 noncurrent orbits,
all current deficits 0..4, all tok 0..5 and boundary DMAX values; larger cases
up to 144 opened orbits are explicitly marked additional seeded checks.

Two complete arbitrary-state finite models were solved without any feasibility
prune: four 3-phase orbits with tok<=2 (73,728 states) and two 5-phase orbits
with tok<=5 (30,720 states). They enumerate EVERY used-port mask/current pair,
not merely states reachable under production pruning. They allow all paid
jumps, so are supermodels of catalogue restrictions. Every rejected deficit
budget was checked against the exact minimal terminal deficit: zero false
rejections, including 146,784 rejected state/budget pairs. Phase holes make
some exact minima strictly larger than L, as expected for a relaxation.

The third capacity algorithm is completed-orbit DP at b=d=0. Independently,
zero tokens prevent any return after leaving an orbit, and zero terminal
deficit forces finishing its five ports before leaving. Thus whole E-runs
can be enumerated directly with tuple-built geometry. All 16 cells with
a,bb,e,h in {0,1} completed uncapped. Twelve have archived production values;
four are absent from that archive. Fresh production runs of all sixteen
completed and matched. No suffix table, production feas, or historical verdict was read
until after independent decisions. This finite subdomain corroborates the
proof; it does not replace it for other budgets.

No production counterexample was found. Mutated false rejections are labelled
abstract optimistic-model counterexamples, NOT realizable-cover violations.
Twelve unsafe targeted mutants are detected; six changes are provably safe
weakenings and are correctly not called soundness failures. Historical
master-verifier mutation behavior is reported separately in REPORT.md.

## 8. Scope of certification

The Token-Touched-Orbit theorem applies to all 144-orbit states satisfying the
listed invariants, hence all t<=4 cells, not by extrapolating tested covers.
Recomputed row maxima and source limits appear in `certs/coverage.json`.
The remaining trusted component is this transparent hand theorem and its
implementation correspondence. It is not a proof-assistant kernel theorem.
Subject to the other accepted R148/R149 premises, feas supplies no additional
unresolved soundness gap. The whole historical search was not rerun.
