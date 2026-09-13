# The minimum length of a six-symbol superpermutation

The Round-143 computer-assisted proof in this repository excludes every
six-symbol covering word of length at most 871, without a no-repeat
assumption. The archived 872-character word is independently checked to
contain all 720 permutations. Together these establish

\[
\boxed{L_6=872.}
\]

The proof consists of hand reductions to necessary finite models, complete
paired model computations, and independently regenerated arithmetic and
static-cover certificates. It is not a formal proof-assistant development
or a claim that an external peer-review process has been completed.
Historical interim reports remain unchanged and are superseded by the
final ledger linked below. In particular, a capped computation is never
used as an impossibility certificate.

## 1. Starting theorem and representative

Round 142 established the unconditional lower bound 869, the upper bound
872, and the first-occurrence framework [1,2]. It did not establish a
repeat-free normalization. The separate 55-cell NR6 theorem is not used
as a substitute for the missing unconditional argument.

Given an arbitrary covering word, retain the first occurrence of each
permutation, trim unused ends, and spell these retained permutations using
maximum overlaps. Coverage is preserved and length cannot increase.
Iterate. Every nonfixed iteration strictly decreases the integer length,
so a fixed representative exists. Its selected gaps are geodesic, have
weights at most six, and every hidden permutation window was seen earlier.
All statements about its repeats concern this representative's own word.

There are 120 rotation hexagons, each consisting of the six cyclic rotations
of a permutation. An E-orbit consists of the five rotations of its first
five positions, with its last position fixed; there are 144 such orbits.
These are different incidence structures, not interchangeable components.

Write P for the number of selected first-occurrence passes, G=P-120,
O=24+k for their opened E-orbits, and D=5O-P=5k-G. S is the number of
selected joints of weight at least three, not the older strand count.
H is the sum of max(w-3,0) over those joints. Thus

\[
L=844+G+S+H.
\]

Successor splicing gives one dummy path and K-1 circuits. If c circuits
consist solely of clean E edges, each uses all five ports of a distinct
orbit used nowhere else. Let d=K-1-c, A be the number of dirty weight-two
sigma edges, Qs the dirty weight-three sigma-squared count, and

\[
g=(G+1-K)/2,\quad Z=G-c-A=2g+d-A,
\quad B^*=S+1+A-O+c.
\]

Connected incidence and chronological same-hex edges give

\[
K+R_{\rm int}\le G+1,\qquad
A+Qs\le R_{\rm int}\le2g,
\]

where R_int is within-component duplicate-hex incidence excess, not the
literal repeat count R. In particular all four terms after 867 in

\[
\boxed{L=867+k+Z+H+B^*}
\]

are nonnegative. The exact definitions and chronology proof are in [1].

## 2–4. Exact threshold budgets

The fixed representative of a hypothetical word shorter than 872 either
has length at most 868, already excluded by [2], or has one of these budgets:

| Length | k+Z+H+B* | Weak resource compositions | Necessary arithmetic rows |
|---:|---:|---:|---:|
| 869 | 2 | 10 | 92 |
| 870 | 3 | 20 | 427 |
| 871 | 4 | 35 | 1,548 |

The finite domain additionally includes every admissible G,c,g,d,A,Qs,
old extraction sharing s, and heavy-edge count h. Constraints include
0<=G<=5k, H<=3h, and H=0 iff h=0. Its rows are necessary arithmetic
possibilities, not literal isomorphism classes. The final verifier generates
the same 2,067 rows independently starting from K,c,g instead of the original
weak-composition enumeration [3,11]. No original permutation frontier is rebuilt.

## 5. Dirty-joint taxonomy

Let p be a selected literal joint source and v=sigma(p) the spliced port.
The endpoint of the full pass beginning at v is still p. Relative tails
and hidden-window counts therefore survive the splice exactly.

| Relative tail | Weight | Spliced map | Hidden permutation windows |
|---|---:|---|---:|
| 10 | 2 | E | 0 |
| 01 | 2 | sigma, type A | 1 |
| 012 | 3 | sigma², type B | 2 |
| 021 | 3 | E after sigma, type C | 1 |
| 102 | 3 | sigma after E, type D | 1 |
| 120,201,210 | 3 | three clean paid maps | 0 |

For weights one through six the shortest-connector clean/dirty counts are
1/0, 1/1, 3/3, 13/11, 71/49, and 308/258. All heavy shortest connectors,
including dirty ones, remain in the generic model. The paired geometry
constructions use tail permutations versus literal maximum-overlap checks.
The independent n=6 geometry considers all 518,400 endpoint/target pairs.

No additive cost is asserted for a pair or triple merely from its type
names. Their joint port and hex occupancy is retained by the finite
recurrences. This avoids treating individually possible dirty events as
simultaneously compatible literal history [1,4,7].

## 6. Structural correction instead of changing an identity

The exact master identity cannot acquire an unexplained positive right-hand
term. The correction used here restricts feasible resource states.
The sigma-chain deficit theorem gives

\[
5k-G+5B^*\ge\max(0,A+Qs-Z-d).
\]

Its proof charges forbidden full/partial sigma-block patterns to distinct
repeated-hex arrivals. The companion propagation E^-1 sigma=sigma^-1 E
rules out the uncharged pattern 5,4,...,4,5. It is a hand charging proof,
supplemented by complete local permutation checks, not fitted capacity data.
The inequality is sharp in small local models; no extra universal unit is
silently added [4].

## 7–8. Recurrences, completeness, and suffix pruning

The coupled model C(a,b,D) uses distinct entry ports, exact a sigma edges,
at most b old-orbit non-E entries, and deficit at most D. An A arrival may
repeat its immediate source hex; every other arrival must use a new hex.
The five non-B weight-three maps and free E continuation are retained.

The generic path model additionally tracks exact Qs, upper repeated-hex
arrivals R, and upper heavy cost H, and includes every shortest connector
of weight 2 through min(6,H+3). Forgetting external chronological hidden-
window obligations enlarges this model. The actual visited-port, opened-
orbit, and visited-hex sets are not replaced by an unproved quotient.

Two implementations enumerate it: whole E-runs with explicit tail geometry,
and individual ports with independently derived literal-overlap geometry.
At a chosen non-E exit the suffix uses the aggregate budget

\[
\Delta_{\rm rem}=D_{\rm cap}+5B-D_{\rm prefix}-5b_{\rm prefix},
\]

not the nonmonotone remaining D alone. Boundary A/B/heavy, old-orbit, and
repeat costs are consumed once, while its target begins the suffix.
After rebasing and safe whole-run cuts, maximize coupled capacities over

\[
1\le m\le1+h+r-a,\quad
\max(0,2a+q-r)\le a_{\rm retained}\le a,
\]

and all sum-b/aggregate-deficit allocations. Missing cells have a safe
infinite bound. The suffix test applies only to the selected non-E exit,
never to unexamined free E extensions of an unfinished run [5].

Every nonpure cycle is opened at a non-E edge, preferring A if present,
otherwise B if present. Value renaming sends its target to 012345.
The final closing edge adds A/B/heavy costs but no port, no old-orbit token,
no D, and no repeated-hex arrival. The suffix reserves the closing cost
before testing internal r>=a+q. A clean 20-port cycle and a 10-port E/A
cycle are retained positive controls [7,8].

## 9. Marked capacities and component allocation

For one path and d nonpure cycles the component identities are

\[
\sum b_i=B^*-s,\quad \sum D_i=5k-G+5s,
\quad\sum P_i=120+G-5c,
\]

for some 0<=s<=B*. This sharing is maximized independently of any earlier
extraction's sharing. Exact A/Q counts add, heavy upper budgets add, and
R_i>=A_i+Qs_i with total R_i<=A+Z-d. All allocations are included.

For actual D_i, P_i=-D_i modulo five. Thus every surviving d=1 allocation
is expanded into every residue-compatible path/cycle size pair whose sum
is the required P. Exact-P decisions reject only their own size, never
an interval inferred from one negative query [8,9].

Completed cycle grids record maxima at exact actual b,D under upper R/H.
The proof uses 16 paired complete capacity domains: the three dominant
domains and 13 immutable snapshot domains. The three dominant maxima are
48,53,58 for (A,Qs,R,H,b,D)=(a,0,a,0,0,12), a=0,1,2. Capacities missing
from the snapshots use a proved opened-path relaxation, not an incomplete
observed maximum.

## 10. Equality and exact-size census

Earlier Z=H=0 equality rows require 84 complete paired exact-P queries:
83 have no path, and one has two 96-port paths. Both static completions
by six closed orbits are UNSAT, each in 46 nodes.

The remaining d=0 domain requires 90 complete paired generic exact-P
queries: 89 empty, one with a single 92-port path. Its completion by seven
closed orbits is UNSAT in 151 nodes. These finite static decisions check
their guaranteed-SAT and brute-force controls before accepting UNSAT [6].

Of the final 61 d>0 arithmetic rows, component bounds exclude 20 strictly.
The other 41 map to 158 distinct possible exact-size pairs (615 row-pair
occurrences before deduplication). Four additional paired path queries are
empty, removing six distinct pairs. The remaining 152 distinct pairs use
80 distinct cycle exact-P queries. All 80 exhaust with no cycle in both
implementations: 230,887 producer nodes and 918,270 independent nodes.
Every cap is zero for these final 84 decisions. No reconnection case remains
after one component of every possible pair is excluded [9–11].

## 11. Repeat bounds

The fixed representative satisfies

\[
R\le5(L-867)-c-4Z-2H.
\]

In particular the threshold-wide bounds are R<=10,15,20 at lengths
869,870,871 respectively. This does not promise the same R after changing
an arbitrary original word, nor does it prove every optimum is repeat-free.

## 12. Rejected shortcuts retained visibly

- A positive additive correction to an exact length identity would merely
  change the definitions or contradict the identity; it was not used.
- Full/full sigma seams cannot always be charged independently: dirty
  cycles and shared companion collisions require the component accounting.
- A nonpure cycle need not have a non-A/non-B opening. The 10-port
  E^4 sigma E^4 sigma cycle is a counterexample and a positive control.
- D is not monotone. The clean four-port path
  012345,234015,340125,401235 has global D=1, but its rebased last-three-port
  suffix has D=2. Prefix-D subtraction would wrongly prune it.
- Exact A counts are not monotone and may become odd after cuts.
- Endpoint refinements that were sound but numerically vacuous were not
  presented as extra exclusions. Capped maximum witnesses were never upper
  bounds. The stronger claim that every repeated cover has length at least
  873 remains unproved by this work.

## 13. Independent verification and reproducibility

The final verifier [11] independently generates the full arithmetic domain,
recomputes all inherited strict bounds, replays paired prefix/cycle exports,
checks static completions, regenerates the complete component/pair ledger,
and validates committed source and bound-manifest hashes. Its strict-bound
recalculation uses 357 endpoint cells and 355 coupled-allocation cells.
It does not merely add stored status counts.

The newest cycle/suffix reduction also received a separate hand audit [10].
That audit is explicitly distinguished from execution verification. Paired
C models have different geometry/traversal structures; a third Python
short-path oracle supplies positive, negative, heavy, and cycle controls.
The focused regression suite comprises 26 Round143 tests plus six direct
872-witness tests. This is not a claim about every historical repository test.

Canonical LF source hashes, runtime hashes, source commits, compiler/version,
argv, executable hashes, nodes, time, complete/capped flags and deterministic
digests are retained in query artifacts. The execution procedure required
committing, pushing, and checking the remote HEAD before heavy runs; those
historical remote checks are execution-log evidence, not independently
attested by the final JSON verifier. Mutable historical executable paths are
not confused with retained historical binary bytes; their source commits and
recorded binary hashes remain in the archived provenance.

Run from the repository root:

```text
python -m unittest discover -s tests -p "test_round143*" -q
python -m unittest tests.test_872_witness -q
python src/verify_round143_end_to_end_codex.py --output outputs/round143_recheck.json
```

Use a fresh output path. Reproduce finite searches with the exact argv and
source commit in each query artifact; generated export paths refuse overwrite.
The final verifier checks certificates and finite resource/static recurrences,
not a replay of billions of capacity-enumeration nodes.

## 14–18. Threshold conclusions and theorem

| Certificate type | 869 | 870 | 871 |
|---|---:|---:|---:|
| Strict scalar/endpoint/coupled bound | 67 | 321 | 874 |
| Sigma-deficit contradiction | 25 | 106 | 339 |
| Earlier exact-P path exclusion | 0 | 0 | 152 |
| Earlier all-prefix static exclusion | 0 | 0 | 1 |
| Generic one-path exact-P exclusion | 0 | 0 | 120 |
| Generic all-prefix static exclusion | 0 | 0 | 1 |
| Path/cycle component strict bound | 0 | 0 | 20 |
| All component P-pairs excluded | 0 | 0 | 41 |
| **Unresolved** | **0** | **0** | **0** |

Assume an arbitrary six-symbol covering word W has length at most 871.
Take its first-occurrence fixed representative W' with |W'|<=|W|. If
|W'|<=868, contradict [2]. Otherwise its exact resource state belongs to
the independently complete 869,870,871 domain. Every row contradicts a
necessary hand inequality, an insufficient complete capacity upper bound,
an empty exact-P model, or an impossible exhaustive static completion.
Therefore |W|>=872. No step assumes NR6 or transformation to a light-clean
word.

The archived witness has length 872 and its six-character permutation
windows cover exactly S6. Its file SHA-256 is
`ed6e98556c149d2df651a0abc85590446f939a1fad6f98cc3c72b242a85fc7ee`.
Thus **L6>=872 is unconditional in this computer-assisted proof, and L6=872**.

The unfinished optional full-capacity batch was intentionally retired after
the required exact-P decisions and audits completed. Its interrupted query
is UNKNOWN, not exhausted, and is absent from the proof dependency manifest.
No file was deleted; the retirement record remains separate [12].

## Sources and certificate entry points

1. [First-occurrence, dirty taxonomy, splicing and repeats](RR_ROUND142_REPEAT_DOMAIN_OUTER_CODEX.md), CODEX, Round142, §§B1–B7.
2. [Unconditional exclusion through 868](RR_ROUND142_UNCONDITIONAL_869_CODEX.md), CODEX, Round142.
3. [Exact arithmetic generator](../src/research_round143_budgets_codex.py), CODEX, Round143.
4. [Sigma-deficit hand theorem](RR_ROUND143_SIGMA_DEFICIT_CODEX.md) and [independent coupled extraction audit](RR_ROUND143_COUPLED_SIGMA_INDEPENDENT_CODEX.md).
5. [One-path suffix audit](RR_ROUND143_ONE_PATH_SUFFIX_AUDIT_CODEX.md), independent proof review.
6. [One-path exclusion and complete static cases](RR_ROUND143_ONE_PATH_EXCLUSION_CODEX.md), CODEX; historical d>0 remainder is superseded here.
7. [Cycle component and closure accounting](RR_ROUND143_CYCLE_COMPONENT_AUDIT_CODEX.md), CODEX and independent review.
8. [Component convolution audit](RR_ROUND143_COMPONENT_CONVOLUTION_AUDIT_CODEX.md) and [verifier](../src/verify_round143_component_convolution_codex.py).
9. [Complete cycle exact-P decisions](../outputs/rr_round143_cycle_pair_decisions_codex.json) and [pair verifier](../src/verify_round143_component_pairs_codex.py).
10. [Independent final cycle/suffix audit](RR_ROUND143_CYCLE_SUFFIX_FINAL_AUDIT_CODEX.md).
11. [Final threshold ledger](../outputs/rr_round143_threshold_final_codex.json), [end-to-end verifier](../src/verify_round143_end_to_end_codex.py), and [verification certificate](../outputs/rr_round143_final_verified_codex.json).
12. [Auxiliary calculation retirement](../outputs/rr_round143_auxiliary_retirement_codex.json); partial work is not proof input.
