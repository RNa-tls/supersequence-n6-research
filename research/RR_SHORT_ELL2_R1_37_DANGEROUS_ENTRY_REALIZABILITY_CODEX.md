# Round 57: dangerous-entry realizability for `short_ell2_r1_37`

## Scope

This round refines the 1,440-triple symbolic closure without extending any
continuation search.  It uses only frozen Round-53/v7, all-13, depth-4,
phase-table, and certificate artifacts.

Strongest supported theorem level: **T1**.

> Every exact state and edge in the complete depth-4 bounded graph is
> bridge-free.  Each of the 196 abstract bridge-relevant transition
> identities additionally requires a prior component-changing Z3 event,
> which is absent from that graph.

This is not T4.  Arbitrary deeper continuations remain open.

## 1. Frozen evidence

The frozen manifest contains 30 artifacts:

- the two Round-53/v7 endpoints and ledgers;
- all thirteen all-13 pilot checkpoints and ledgers;
- the 1,075-state/991-edge depth-4 graph;
- the Z2 and 34-orbit watch-list certificates;
- the 92-edge phase audit;
- the 308-entry observed transition table;
- the 1,440-entry symbolic closure.

Every artifact below 512 MiB was rehashed in this audit.  The immutable
1.66 GB and 4.88 GB v7 endpoints use their already independently verified
Round-53 ledger SHA-256 together with current size and mtime; they were not
rehashed a second time after a direct rehash attempt proved prohibitively
slow.  This distinction is explicit per artifact in the manifest.

Configuration identity is frozen for all fifteen checkpoint artifacts.  For
the two large v7 endpoints, the verifier decodes the bounded header containing
`config` and `continuation_provenance` directly from each checkpoint and
checks its branch id, config/payload schemas, exact-engine and driver hashes,
and `R2_LITERAL_JOINT_SOURCE_V1` semantics.  For each all-13 checkpoint it
recomputes the embedded `config_sha256` and checks the v8 schema, state id,
engine hashes, and recognizer semantics.

Frozen cardinalities were independently rebuilt:

```text
observed triples             308
observed watch triples        48
direct fresh hub entries      88
symbolic next-Z2 entries     108
```

## 2. The 196-entry ledger

`DIRECT_Z3` and `NEXT_Z2` are different abstract transition identities even
when they share a preceding Z3 triple.

| unit | count |
|---|---:|
| direct Z3 transition identities | 88 |
| next-Z2 transition identities | 108 |
| total mechanism-labelled identities | **196** |
| unique preceding Z3 triples | 176 |
| preceding triples shared by both mechanisms | 20 |
| direct-only preceding triples | 68 |
| next-Z2-only preceding triples | 88 |

Each direct entry records the exact source word/orbit/phase/hex position,
target orbit/phase/hexagon, compatible phases, first closure round, and why
the triple was absent from the observed 308-domain.

Each next-Z2 entry records the preceding Z3 triple, resulting Z2 source,
Z2 target phase/hexagon, closure round, overlap status, and exact observations
when its preceding triple occurs in the bounded graph.

## 3. Necessary exact-state condition

The symbolic triple coordinate omitted component ancestry.

Before any component-changing Z3 event, the distinguished components are:

```text
R1 component:  orbits {91}, hexagons {40,92}
hub component: orbits {0,9}, hexagons {0,1,4,6,8,9,18,24,96}
```

For a direct Z3 dangerous entry, its target hexagon lies in the hub
component.  The new incidence can merge the components only if its target
orbit already lies in the R1 component.  None of the 88 target orbits is 91.

For a later-Z2 dangerous entry, full-pass Z2 preserves the pass-start
E-orbit.  To merge at the hub hexagon, that preserved orbit must already lie
in the R1 component.  None of the 108 preserved orbits is 91.

Therefore all 196 mechanisms require an earlier Z3 that expands the R1
component.  This is the missing exact-state coordinate and explains the
spurious dangerous entries in the occupancy-free closure.

Other necessary exact-state data, serialized in the ledger, include rotation
collision masks, target phase freshness, incidence partition, Phi, F/H/Ndef,
P/O, R budget, hub touch count, registered-orbit mask, R1 provenance,
completer timing, and terminal geometry.  These cannot be recovered from a
triple alone.

Within all 1,075 depth-4 states, the exact invariant ledger is:

```text
Phi=0, F=1, H=0, Ndef=1, r_count=1, hub_touch_count=1
```

with 1,075/1,075 states in every row.

## 4. Incremental coordinate audit

All coordinates below refine the earlier 334 reporting profiles.  None is a
proved quotient.  Abstract dangerous entries conservatively remain 196 when
the coordinate has no certified value on a newly generated symbolic entry.

| added coordinate | exact cells | mixed cells | conflicting pairs | average bytes |
|---|---:|---:|---:|---:|
| source hex position | 334 | 197 | 1,030 | 1.0 |
| previous macro kind | 509 | 190 | 536 | 4.156 |
| trace Z2 count mod 5 | 618 | 149 | 360 | 1.0 |
| F / H / Ndef / hub-touch (each) | 334 | 197 | 1,030 | 1.0 |
| component-size vector | 1,055 | 16 | 16 | 140.753 |
| incidence-degree signature | 511 | 181 | 575 | 9.0 |
| R1-component signature | 334 | 197 | 1,030 | 14.0 |
| hub-component signature | 334 | 197 | 1,030 | 30.0 |
| registered-orbit mask | 1,075 | 0 | 0 | 76.848 |
| recent suffix length 1 | 564 | 177 | 447 | 14.552 |
| recent suffix length 2 | 764 | 120 | 171 | 26.346 |
| recent suffix length 3 | 884 | 50 | 65 | 35.767 |

The registered-orbit mask separates every bounded exact state, so its zero
mixed count is descriptive rather than a useful quotient theorem.  The best
compact scalar remains trace-Z2-count mod 5, but it is insufficient.

## 5. Backward realizability ledger

The predecessor relation is the exact finite symbolic Z3 rule, not an exact
continuation relation.  Every parent chain is replayable in the 1,440-table.

| class | count | meaning in this audit |
|---|---:|---|
| R0 | 0 | no local impossibility claimed outside the fixed-component regime |
| R1 | 0 | no complete no-predecessor proof |
| R2 | 0 global / 196 fixed-regime | all violate the unexpanded-component condition |
| R3 | **174** | abstract chain only; exact source state not certified reachable |
| R4 | **22** | exact bounded post-Z3 precursor exists |
| R5 | 0 | no exact bridge transition |

The 22 R4 entries are next-Z2 mechanisms.  Their preceding triple occurs in
50 literal observations, but the recomputed legal-later-Z2 value is false in
every occurrence.  This does not prove the same triple can never recur with a
different occupancy history.

Count conservation:

```text
196 abstract dangerous identities
 -> 196 well-defined local permutation actions
 -> 196 abstract predecessor chains
 -> 22 exact bounded precursor identities exposed
 -> 0 exact legal dangerous transitions in the bounded graph
 -> 0 bridge witnesses

174 entries remain abstract-only;
all 196 remain globally unresolved without branch-wide reachability closure.
```

No SAT/CSP model was needed for this bounded classification, and no targeted
forward search was started.  A future targeted computation should search for
the first component-changing Z3, rather than expanding all 196 endpoints or
all six branches uniformly.

## 6. The all-13 depth split

The seven exhausted seeds start at depths 59--88; the six capped seeds start
at depths 47--58.  However, all thirteen satisfy exactly

```text
depth = P - 2.
```

The same split is therefore `P>=61` versus `P<=60`.  Depth is not an
independent explanatory variable in this corpus.  Component counts overlap,
and every seed has an occupancy-free backward path to a dangerous signature,
so neither observation supplies a monotonicity theorem.

## 7. Final theorem-scope classification

- T0: retained and formalized as the separate Z2 lemma.
- **T1: proved for the complete 1,075-state depth-4 region.**
- T2: not proved; the abstract entries are locally well-defined.
- T3: not proved; 174 are still abstract-only and future reachability is open.
- T4: not proved.
- T5: no witness.

The concrete reduction is from 196 endpoint mechanisms to one common prior
event class: an R1-component-changing Z3.  It is not a complete branch
closure.

## Verification

```powershell
python src/verify_rr_short_ell2_r1_37_dangerous_entries.py --write
python src/verify_rr_short_ell2_r1_37_dangerous_entries.py
```

The verifier rebuilds the phase table and closure, replays all 991 stored
edges, recomputes all refinement partitions and backward chains, and checks
720 full-pass Z2 orbit-preservation cases.
