# SLACK-COVER audit archive — schema `rr-slack-cover-archive-v1`

Preserves the input ledger and instance archive behind Round 79's claim that
**38,141 of 44,650** `COLLISIONS ≤ 4` residual states are closed, leaving **6,509** SAT plus
the **148** Round-78 `c = 5` survivors, i.e. **6,657** total Q2 residual.

Everything here is derived from `outputs/rr_target_a_checkpoints/*.json` by a read-only pass
(`src/export_rr_slack_cover_archive.py`). No state was re-generated and no search was run.

A verifier that imports nothing from this repository is provided:

```
python3 src/verify_rr_slack_cover_archive.py --archive outputs/rr_slack_cover_archive
```

It replays every count and exits non-zero on any inconsistency.

---

## Numbering conventions

**Hexagons `0…119`** — a hexagon is a σ-orbit of `S₆` under `σ = (1,2,3,4,5,0)`, i.e. a set of
6 permutations. `incidence_table.json → hexagons[h].windows` lists those 6 permutations as
digit strings (e.g. `"012345"`), so the numbering is pinned to explicit data, not to our code.

**E-orbits `0…143`** — an E-orbit is an orbit of `S₆` under `E = (1,2,3,4,0,5)`, of size 5.
`incidence_table.json → orbits[q].ports` lists its 5 permutations, and `orbits[q].block` the
5 hexagons containing them. The system is biregular: each orbit meets **5 distinct** hexagons,
each hexagon meets **exactly 6** orbits, 720 incidences in total. The verifier re-derives every
`block` from `ports` + `windows` rather than trusting the field.

**Bit numbering** — all masks are lowercase, fixed-width hex of a non-negative integer, least
significant bit first:

| field | width | bit `i` set means |
|---|---|---|
| `C`, `U` | 30 hex chars (120 bits) | hexagon `i` is covered / uncovered |
| `open_orbits` | 36 hex chars (144 bits) | E-orbit `i` is open (has ≥ 1 registered port) |

`C` is exactly the union of the open orbits' blocks; `U` is its complement in the 120 hexagons.

---

## Quantities

| symbol | meaning |
|---|---|
| `O` | number of open E-orbits = `popcount(open_orbits)` |
| `K` | `25 − O`, the orbits still to be opened before an Area-A completion |
| `c` | `COLLISIONS = 5·O − |C|` (Round 77); necessary condition `c ≤ 5` |
| `b` | `5 − c`, the remaining collision slack |

Identity, holding on every row: **`|U| = 5K − b`**.

**The slack-cover condition (Round 79).** A completion must open exactly `K` currently-closed
orbits whose 5-hexagon blocks **cover** `U`. The excess is then automatically exactly `b`, so
the per-block consequence `|block ∩ C| ≤ b` is what restricts the choice. At `b = 0` this is the
Round-78 exact cover.

---

## `states.jsonl.gz` — 44,650 rows, one per processed `c ∈ {1,2,3,4}` state

Line 1 is a header record (`{"record":"header","kind":"states","n_records":…}`); every
subsequent line is one state.

| field | meaning |
|---|---|
| `sid` | stable state id — `sha256` of `"<p>\|<hex_masks>\|<orbit_masks>\|F=…\|S=…\|H=…"`, where `p` is the endpoint permutation as a digit string and the two mask vectors are comma-joined decimal integers in index order (120 and 144 entries). Full 64 hex chars. All 44,650 are distinct. |
| `root`, `idx` | provenance: checkpoint file `outputs/rr_target_a_checkpoints/<root>.json`, index into its `frontier` array. Locating a state needs no hashing. |
| `c`, `b`, `O`, `K` | as above |
| `C`, `U`, `open_orbits` | masks, as above |
| `P`, `Phi`, `Ndef`, `D`, `D_dead`, `r` | the state's coordinates in the standing bound stack, for cross-checks |
| `iid` | index of this state's slack-cover instance in `instances.jsonl.gz` |
| `weight` | state multiplicity. **Always 1** — states are not deduplicated; only *instances* are. A band's state count is the number of rows, and equals the sum of weights. |

## `instances.jsonl.gz` — 43,643 rows, one per distinct `(U, b)`

Distinct instances are fewer than states because different states can share an uncovered set.
**UNSAT rows are included**; they are the majority (37,630 of 43,643).

| field | meaning |
|---|---|
| `iid` | stable instance id (row order, ascending by `(U, b)`) |
| `c`, `b`, `K`, `size_U`, `U` | instance parameters |
| `candidate_orbits` | every orbit `q` with `\|block(q) ∩ U\| ≥ 5 − b`. Such an orbit is necessarily **closed**: an open orbit's 5 hexagons all lie in `C`. The verifier recomputes this list and checks the open-orbit mask of every source state against it. |
| `candidate_blocks` | the same orbits' 5-hexagon blocks, spelled out so the file is self-contained |
| `verdict` | `SAT`, or one of `UNSAT_coverability`, `UNSAT_waste_floor`, `UNSAT_forced_excess`, `UNSAT_component_hall`, `UNSAT_slack_cover`. The first four are cheap necessary tests; the last is a complete memoised bitset DFS that found no cover. `UNKNOWN_node_cap` would mean the search was truncated — **it does not occur anywhere in this archive**. |
| `sat` | boolean mirror of `verdict == "SAT"` |
| `witness_orbits` | for SAT: an explicit `K`-orbit witness. Verified to be candidates, to cover `U`, and to have excess exactly `b`. `null` for UNSAT. |
| `forced_blocks`, `components`, `search_nodes` | diagnostics from the decision |
| `n_states`, `state_ids` | the source states mapping to this instance; checked against `states.jsonl.gz` in both directions |

## `collision5_survivors.jsonl.gz` — 148 rows

The Round-78 `c = 5` exact-cover **SAT** states, carried through Round 79 untouched and not
re-decided. Same fields as `states.jsonl.gz` (with `c = 5`, `b = 0`, `|U| = 5K`), minus `iid`.
Their exact-cover certificates live in
`outputs/rr_exact_cover_collision5_certificates_claude.json.gz`.

---

## What an independent auditor still has to do

This archive lets you replay the **counts** and check every **SAT** verdict end to end. It does
**not** prove the UNSAT verdicts — deliberately. Each UNSAT row carries `U`, `b`, `K` and the
full candidate block list, which is everything needed to re-decide it with your own solver.
Re-deciding those 37,630 instances is the outstanding half of the audit.

Round 79's own soundness checks (positive control on 620 synthetic guaranteed-satisfiable
instances, 8,141 UNSATs re-decided under a different variable order, `E¹` invariance) are
reported in `research/RR_SLACK_COVER_CLAUDE.md`; they are Claude-side and are not a substitute
for the independent re-decision.
