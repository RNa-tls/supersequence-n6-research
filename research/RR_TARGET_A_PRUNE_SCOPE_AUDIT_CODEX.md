# Round 41: Target-A prune-scope audit

**Audit status:** `TARGET_A_COMPLETENESS_GAP_CONFIRMED`

**Audited historical commit:** `abfcdca` (the 100,250-node `short_ell0`
medium run)
**Scope:** the five bare short RR roots only.  This audit neither resumes a
root nor claims a Target-B or NR6 conclusion.

## Finding

The historical corrected traversal called
`macro.area_a_prune_reason(state, macro.AREA_A)` before recognizing an R2
boundary.  That function includes `O_exceeded`, namely `state.O > 25`.
The number 25 is a **Target-B completion coordinate**, not a condition in the
Target-A boundary definition.  Consequently the medium run is retained only
as a restricted Area-A/Q2-profile experiment and is marked
`PREMATURELY_PRUNED_INVALID_FOR_TARGET_A_COVERAGE`.

The replacement has two explicitly hash-separated profiles:

| profile | purpose | checkpoint use |
|---|---|---|
| `target_a_semantic_v1` | semantic Target-A reachability | only v3 checkpoints |
| `legacy_area_a_q2_comparison_v1` | historical Area-A/Q2 differential | audit-only; never an exhaustion certificate for Target A |

The short-root config is now
`round37-short5-bare-abandonment-r1-complete-v3-target-a-prunes`, with payload
schema `rr-target-a-exhaustive-checkpoint-v3-short-r1-target-a`.  A v2
checkpoint cannot load under this config.

## Formal hierarchy

Let `Reach(r)` be exact reachability in the scoped RR alphabet from root `r`.

* **Target A** is an R2 macro edge whose child has `F_def=1`, `H=0`, and whose
  R2 source and target E-orbits lie in the same component of the current
  orbit--hexagon incidence forest.  Chaining is recorded, not required.
* **Q1(r)** means `exists b in Reach(r): TargetA(b)`.
* **Q2(r)** means `exists b in Reach(r): TargetA(b) and CompletionCompatible(b)`.
* **Target B** is a Target-A boundary followed by an admissible Area-A terminal
  continuation, including `P=121`, `O=25`, `D=4`, `Ndef=2`, and its remaining
  capacity conditions.
* **Target C** is a complete NR6/nonrepeating 720-window construction.  It is
  outside this search's unconditional scope.

The established implication is `Target B => Q2 => Q1`; the first implication
uses the fixed completion-compatible predicate in the root reduction.  A
Target-C realization *within this RR/root reduction* produces the associated
Target-B continuation.  No converse is used.  In particular,
`Q2-impossible` does **not** imply `Target-A-impossible`.

## Area-A bundle retention table

`outputs/rr_target_a_prune_registry.json` records the machine-readable version.

| Area-A sub-prune | exact condition | monotone | Target-A disposition | reason |
|---|---|---:|---|---|
| `F_exceeded` | `F>1` | yes | retained | Target A requires `F=1` |
| `H_positive` | `H>0` | yes | retained | Target A requires `H=0` |
| `P_exceeded` | `P>121` | yes | disabled | `P=121` is Target B |
| `O_exceeded` | `O>25` | yes | disabled | `O=25` is Target B |
| `N_exceeded_monotone` | `Ndef>AreaA.n_limit` | yes | disabled | the Ndef cap is Q2/Target B |
| `final_D_impossible` | failure to reach `D=4` | no | disabled | `D=4` is Target B |
| remaining-pass-start test | `720-visited < 121-P` | no | disabled | completion-to-121 bound |
| remaining-window capacity | `remaining_window_capacity_prune` | no | disabled | completion capacity only |
| `F1_fragment_normal_form_impossible` | exact F<=1 prefix normal form fails | yes | retained | independent prefix invariant |
| future-orbit credit | `25-O > (121-P)+(1-F)` | no | disabled | completion-to-O=25 bound |
| exact collision | `exact.extend is None` | yes | retained | universal nonrepeat legality |
| RR R budget | more than two scoped R events | yes | retained | R2 is terminal in this root language |
| hub touch count | more than two hub targets under F<=1 | yes | retained | independently proved hub-touch theorem |

The precise source of the historical bundle is
`legacy_research/work/superperm_partial_f1_macro.py::area_a_prune_reason`.
The Target-A and Target-B definitions are respectively in
`research/RR_TARGET_A_DEFINITION.md` and `research/RR_TARGET_B_DEFINITION.md`.

## Bounded differential replay

A deterministic `short_ell0` pilot used 250 expansions under each profile.

| observable | legacy Area-A/Q2 | Target-A semantic |
|---|---:|---:|
| expanded states | 250 | 250 |
| frontier | 84 | 88 |
| R1 transitions | 4 | 4 |
| R2 candidates | 136 | 118 |
| Target-A hits | 0 | 0 |
| O-only prunes | 101 | 0 |

The first divergence occurs at macro depth 69.  It is literally replayed from
the bare `short_ell0` root: the exact legal child has
`(P,O,D,Ndef,F,H)=(71,26,4,1,1,0)`.  The legacy profile returns
`legacy_area_a_q2_comparison_v1:O_exceeded`; the Target-A profile returns
`child`.  This is an **exact counterexample to O-cap pruning as a
Target-A-safe prefix rule**, not a claim that the child already reaches a
Target-A boundary.

The differential output contains the complete literal macro trace and both
serialized exact states.  The independent verifier replayed that trace,
validated v3 checkpoint parsing, validated v2 rejection, and checked that the
R2 primary-failure histogram partitions all R2 candidates.

## Event-order and telemetry correction

`CH1` means the first hub completer is R1 itself.  `CH2` means the first hub
completer is a later Z2 event after R1.  A completer before R1 is now exported
as `PRE_R_COMPLETER_EVENT_ORDER`; it is an analysis label, not a third proof
branch.  Every R2 candidate receives exactly one primary recognizer failure
when it is not Target A.  Phi/M at R1, hub timing, event-order class, and
pre/post-R1 prune histograms are checkpointed telemetry.

## Retention decision

* The 100,250-node v2 medium run is **not valid for Target-A coverage**.
* Its restricted Area-A/Q2 telemetry is preserved without alteration.
* The v3 semantic pilot is bounded and therefore `INCOMPLETE`; it provides no
  positive or negative reachability conclusion.
* No other short root has been started, and no v2 checkpoint is resumed.
