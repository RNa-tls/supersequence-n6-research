# Certified suffix bounds for exact pass-count queries

This is a proposed implementation specification and hand inclusion proof.
It does not itself exclude a threshold row. Its inputs must be completed,
independently checked coupled capacities; a missing bound is infinity.

Let a coupled SIGMA path be split immediately before a non-E edge target,
so every E-run in the prefix is complete as a block (it need not have five
ports). Write n for prefix entry ports, b_p for its old-orbit non-E entries,
and D_p=5O_p-n. Its used whole-run deficit is

    Delta_p=D_p+5b_p=sum_prefix_runs(5-r).

A completed path with bounds B,D has total whole-run deficit at most
D+5B. Thus the suffix run deficit is at most

    delta=D+5B-Delta_p.

Let j be the chosen non-E boundary edge. It consumes one global b token
iff its target orbit was opened in the prefix; call this indicator o_j.
Rebasing the suffix treats its initial orbit as new. Every old-orbit entry
internal to the suffix is also globally old, so its internal count b_s
satisfies 0<=b_s<=B-b_p-o_j. Other global-old but suffix-first entries are
relaxed away, never used as a negative cost.

If A exact sigma edges are required in the whole path, the suffix contains
exactly a_s=A-A_p-[j is sigma]. The boundary sigma is not counted inside
the suffix. Resetting its initial hex to fresh is permitted: all other
non-sigma entries remain new inside the suffix, and every internal sigma
entry still repeats its predecessor's hex. Unique ports also persist.

For its own opened-orbit count and phase deficit,

    D_s+5b_s=sum_suffix_runs(5-r)<=delta.

Consequently a valid upper bound on suffix ports is

    U=max_{0<=b_s<=min(B-b_p-o_j,floor(delta/5))}
            C(a_s,b_s,delta-5b_s).

C is exact in a_s and upper-bounded in its b,D coordinates. A completed
dominating table cell may replace a queried cell. A missing cell makes U
unknown/infinite; it never removes a branch. The hand inequality
a_s<=D_s+5b_s<=delta allows impossible terms to be removed.

In an EXACT-P query, if n+U<P, this non-E continuation cannot reach the
required pass count. The bound is not used across a free E edge, where
the current run has not ended. At length P, test the resource conditions
and export every qualifying prefix; do not extend it. With complete
finite exhaustion, zero exports exclude only that exact (A,B,D,P) query.
They do not claim a global maximum or rule out different pass counts.

This does not assume distinct orbit names, one entry per orbit, a new
initial orbit relative to the prefix, literal feasibility of the suffix,
or monotonicity of D_p. The argument uses additive WHOLE-RUN deficit,
not the previously refuted phase-walk supply helper.

Implementation requirements: both independent enumerators must retain
their ordinary no-bound modes; bound-mode results need an explicit exact-P
schema. Preserve the completed-capacity manifest and its hashes. Test
the inequality on every available maximum witness at every non-E split,
and compare bounded/unbounded exact-P exports on small complete controls.
