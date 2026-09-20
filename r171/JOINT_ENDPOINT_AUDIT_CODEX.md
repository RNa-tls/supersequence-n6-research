# Round 171 — recovered state and joint-target audit

## Verdict and scope

**JOINT_SAFE_VECTOR_PARTIAL.** The stored joint vector J passes a fresh direct
census. All 8,192 requested I/J endpoint assignments have been evaluated, with
rowwise minimal forbidden hyperedges extracted. There are real third-order
interactions. The selected J is retained; no new capacity search was launched.

The requested known-pair hyperedge check cannot hold in this endpoint universe:
`1|5|10|0|0|0` is **not active**, because I=J=129 for it. We stop the proposed
global/component frontier optimization at this diagnostic, rather than invent
an edge containing a coordinate which never varies. A complete endpoint result
is not a complete global trade-off frontier.

## Repository recovery, not inherited Round-151 status

On 2026-09-20 the original local checkout was still at
`1f9efff0809c47e7ca1857ed6c7734c20e78f081` on
`codex/round-r1-37-first-component-z3-stage-d`, with extensive old untracked
research outputs. The Round-151 worktree was still at `30f72ed...` with uncommitted
Round-151 files. Neither was modified.

`git ls-remote` and a fresh fetch established the current remote proof branch:

```
round153-equality-coexistence
0029fe2905d01db805d162230b54e9a1e2d2b161
parent 0333d1e5f74e4e6af6a49fdce09232e808d574eb
```

This audit uses an isolated LF checkout, `supersequence-n6-research-round171`,
branch `codex/round171-joint-audit`, based on that commit. No AGENTS.md was found
in its committed tree. This host had no running Python/EXTREE/r171 research
worker at recovery. That says nothing about another host's processes.

The latest remote contains `interact171.py` but no committed
`interaction_171.json` or endpoint/hypergraph completion. We did not rerun the
superseded pairwise scan. A second remote-ref check during the audit still
returned the same HEAD.

## Verifier B completed: tighter bound is preserved

Both reports for `cap(1|7|8|0|0|0)<=119` are present and successful. Per-batch:

- generator proof nodes = verifier A nodes = verifier B nodes = histogram
  checks = **3,771,054**;
- B histogram mismatches = **0**;
- B total replay is **10,194,346** because it also replays the three helper
  trees (6,423,292 nodes). Aggregate versus per-batch totals are not confused.

The compressed proof object SHA-256 is
`e1af8ea08c4ac88f529eb551ca747e5f31b7d01d38806b95bfde3af7176bd0cf`.
Its uncompressed SHA-256 is
`88b016168ed98903fe2ddb11bcfb59fe5cf92d6c86a833493de8addfbc5d2c8f`.

This recovery checks reports, source hashes, compressed/plain object hashes,
dependency hashes, tree header and per-batch four-way agreement. It does **not**
claim a fresh replay of every EXTREE dependency. Existing valid certificates
are preserved, including the weaker `<=123`, which is now classified
`VALID_BUT_NOT_JOINTLY_SUFFICIENT` for J, not false.

## Soundness anchor: direct joint census

The fresh evaluator supplies **all 35** coordinates of J explicitly. Historical
basis fallback is disabled (`value_of` returns None; historical table value
maps are poisoned to None after diagnostic row selection). No default basis
lookup can supply a missing value. There is no overlap between the 35 basis
keys and the fixed `dual_chain` background.

The existing accepted nonbasis dual-chain/dual-piece background and its bridge
rules remain in scope. Thus “no-table” here means **no historical load-bearing
basis values used**, not a fresh recertification of every background fact.

Results:

| Quantity | Fresh result |
|---|---:|
| Exposed rows closed | 180/180 |
| Complete coordinate-group census | 1,607 strict + 2 equality |
| E1/E2 | both remain EQUALITY |
| Historical basis fallback reads in J evaluation | 0 |

This is a statement that the proposed upper bounds **would suffice together**.
It is not a proof that the 30 still-uncertified upper bounds are true.

An additional provenance correction: historical capacities were used in
`joint171.py`'s EXACT interpolation and in the old individual-bound derivation.
The old sentence claiming none were used to derive the vector is inaccurate.
That does not invalidate J: its feasibility is independently checked with the
full proposed vector supplied, without those historical basis values.

## Complete endpoint universe

Active coordinates really number **13**. Every assignment chooses I or J at
each active coordinate; all other coordinates stay at J. The archive records
every mask, its open-row list, closed count and both equality statuses.

| Quantity | Result |
|---|---:|
| Assignments evaluated | 8,192/8,192 |
| Feasible assignments | 1 (mask 0, J) |
| Infeasible assignments | 8,191 |
| Assignments changing E1/E2 status | 0 |
| Row-labelled minimal forbidden hyperedges | 62 |
| Size distribution | 55 singletons, 5 pairs, 2 triples |
| Distinct coordinate subsets after forgetting row labels | 17 |
| Largest interaction order observed | 3 |
| Endpoint-slice components on the 13 active coordinates | 9 |
| Largest such component | 3 |

These are **rowwise** minimal edges. Globally, every single active coordinate
already opens some row, hence only J is feasible in this upward endpoint cube.
A triple can still be minimal for a different particular row. Do not confuse
global minimal infeasible masks with row-labelled minimal masks.

The same three-coordinate set is minimally forbidden in two rows:

```
1|6|3|0|1|0
1|8|1|0|1|0
2|3|1|0|1|0
```

It opens row indices 64 and 133 (stable sorted exposed-row indices in the JSON),
with `(t, coordinates)` respectively:

```
(4, (1,1,1,1,2,1,0,0,1,0,1))
(4, (2,1,0,1,7,1,5,0,1,0,0))
```

Every proper subset leaves that particular row closed. This is an actual
failure mode of pairwise-only detection, not just a synthetic warning.

### Arithmetic reuse and verification

The enumeration caches a row only by the complete signature of capacity values
read by its arithmetic evaluation. This is not a graph-based independence
assumption. Read sets are captured with DP caches cleared at both endpoints;
each cache miss asserts no new read was omitted. Loop domains depend on fixed
row budgets; invalid negative piece entries are in the fixed background and
cannot change with the positive basis values. The finite sums/minima/maxima do
not acquire new branches when these bounds are raised.

There are 2,094 distinct evaluated row signatures. The generation path also
compares selected masks to the original scalar census. A separate checker
recomputes 19 masks, including every minimal forbidden mask and singleton,
without this cache. It verifies mask completeness, exact upward closure and
that the minimal edges reconstruct every row's entire forbidden-mask set.
Raw timing metadata has a separate artifact; substantive content has its own
canonical SHA-256.

## Known pair: why the mandated endpoint check cannot pass

```
cell                 J     I      active?
1|5|10|0|0|0        129   129      no
1|7|8|0|0|0         119   123      yes
```

Consequently the pair cannot both occur in a 13-coordinate hyperedge. The first
cell is already weakened in the **fixed background**. Raising the second alone
can expose the interaction. This is not evidence that the pair ceased to couple.

The original real counterexample was separately reproduced with explicitly
labelled historical diagnostic background: neither singleton weakening opens
an exposed row, but weakening both to 129/123 does. Those diagnostic values are
never read by the J production-target census.

The handoff's quoted `d7=119 => d5 maximum 128` is not used as an oracle:
the actual stored J contains **d5=129 and d7=119**, and direct replay closes
180/180. Any claimed two-coordinate frontier must specify the other 33 values;
the quoted maximum is not reproduced for the selected J background.

To represent that pair as a hyperedge, a different universe must allow the
first coordinate to decrease below 129 (and distinguish background values).
That is not the requested I/J cube. The old graph cannot license independence
outside its tested slice; neither can this new endpoint hypergraph.

## Intermediate breakpoints and frontier scope

For each active coordinate, with every other coordinate fixed at J, we checked
the first integer step `J(K)+1` directly. All 13 steps open a row. Therefore,
by monotonicity, the **entire integer box J<=v<=I** has just one feasible vector,
J; its Pareto frontier is `{J}`. No blind integer-grid enumeration is needed for
that box.

Monotonicity is structural, not inferred from 30 random trials: increasing
supplied capacities can only increase their P1 minima, max-of-sums model bounds,
and the minimum of alternative model bounds. The comparison to the fixed
required value therefore cannot make an open row strict again. The unavailable
piece pattern is fixed and not controlled by these coordinates.

This does **not** enumerate all census-relevant breakpoints or Pareto trade-offs
when other coordinates may decrease below J or fixed coordinates may vary.
The 9 slice components cannot be used to solve that global problem separately.
Following the requested stop-and-diagnose rule, global component optimization
and new certificate production are not started.

## New dossier and honest progress

`certs/joint_dossier_codex_171.json` records all 35 cells, individual target,
selected J target, historical diagnostic capacity, currently certified bound,
joint usability, the tested ray breakpoint, and endpoint-slice component.
Uncomputed global breakpoints are not represented as complete.

The historical dossier is preserved byte-for-byte and designated in the new
ledger as `INDIVIDUAL_ONLY` / `SUPERSEDED_FOR_PRODUCTION_TARGETS`, not invalid.

| Progress metric | Count |
|---|---:|
| Distinct basis cells with preserved genuine bounds | 5/35 |
| Bounds compatible with selected J | 5/35 |
| Still requiring genuine bounds at J's target | 30 |
| Historical basis values used by the direct J census | 0 |
| Remaining obligations formerly supported by historical table values | 30 |

The weaker d7<=123 certificate remains true; d7<=119 now supplies the usable
bound. The five usable bounds are H<=115, A2<=117, 0|20<=119, 1|5|10<=129 and
1|7|8<=119, with full keys and proof hashes in the dossier. No claim of 35/35 or
theorem completion is made.

## OPT=35 and next action

OPT=35 stays frozen **in the existing candidate universe/rule system**. Its
necessity, singleton-completion scan and pair sufficiency evidence precede
r171; their implementation dependencies do not reference the erroneous r171
individual-safe derivation. This round checks that separation and artifact
hash binding, not a fresh cardinality optimization. An old `basis_170.json`
argument sentence still says a size-3 completion is left; its actual witnessed
size-2 result and independent audit establish 35. Do not use that stale sentence
instead of the counts.

Soundness already has a sufficient proposed J; cost optimization is secondary.
The unresolved issue here is the proposed **global decomposition**, not J's
feasibility. Resolve the endpoint/background scope explicitly before using any
hypergraph component to optimize production targets. No expensive new proof
generation, continuation or old frontier reconstruction occurred in this run.

## Reproduction

```
python r171/src/joint_endpoint_codex.py
python r171/src/check_joint_endpoint_codex.py
python -m unittest discover -s r171/src -p test_joint_endpoint_codex.py -v
python r171/src/freeze_joint_codex.py
```

Historical artifacts are read-only. New outputs use the `*_codex_171` namespace.
The seven regression tests and py_compile pass. The integrity manifest records
their actual output and SHA-256 of the new audit code, evidence and report.

JOINT_SAFE_VECTOR_PARTIAL
