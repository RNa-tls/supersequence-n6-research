# Round 142 — separate Route A / Route B verdicts

Author: CODEX. 2026-09-11.

## Outcome

**Computer-assisted unconditional lower bound: L6>=869.** The known upper
bound872 remains, so the proven interval is **869<=L6<=872**. The three
lengths869/870/871 are unresolved. Neither NR-UNIVERSAL(6) nor unrestricted
L6=872 is claimed.

### Route A

The exact direct-clean connector theorem c(p,q)<=n+1 and its complete local
distance table are proved and independently checked. Boundary-fixed
nonincreasing cleaning is refuted in322 local cases; in11, the increase
exceeds the number of repeats removed. The minHam/minCleanHam distinction
is made precise. NR-UNIVERSAL and the global +1 repeat gap remain open.

### Route B

First-occurrence arc partition, nu, and length bookkeeping survive repeats.
Four dirty light operators are isolated. The new exact master is

    L=867+k+Z+H+B*, with k,Z,H,B*>=0.

Dirty same-hex edges charge topology; mixed dirty edges inject to absent
ports, with removed edges charged separately. This gives the fixed-point
representative bound **R<=20** at length<=871, improving27.

All55 cells close for the weaker **light-clean first-occurrence** class,
even if heavy joints contain repeated windows: 300 envelopes,3504 seam
attempts (1606 dirty), and the three retained static UNSAT certificates.
This is a sufficient structural theorem, not a proved normalization to
that class. Small independently exhausted marked capacities then exclude
t=L-867 in{0,1} without any clean/NR normalization assumption.

## Required final-report checklist

| requested item | result |
|---|---|
|1. Exact NR-UNIVERSAL | every cover dominated by an NR cover; equality of minima using ordinary overlap versus direct-clean costs |
|2. Truth at n6 | UNPROVED, not refuted |
|3. Repeat penalty | local nonpositive and per-repeat cleaning penalties REFUTED; global +1 UNPROVED; structural R inequality proved |
|4. Dirty taxonomy |719 minimum connectors/873 short tail variants; four dirty light types |
|5. NR dependencies | separate dependency audit; first essential failure is all-free=E, not selected nu |
|6. Selected bookkeeping | HAND PROOF, actual/selected coordinates distinguished |
|7. Free successor | exact correction f_out=F-a+e-eta+Y_d |
|8. Dirty splice | exact endpoints; same-hex marks charge R_int |
|9. Capacity models | ordinary, E-sigma marked, two-mixed marked; small D0..5 paired exhaustive values |
|10. NR6' sufficiency | light-clean condition sufficient; transformation into it still UNPROVED |
|11. Direct outer extension | proved for light-clean heavy-dirty words, NOT all repeats |
|12. D>=28/29 | neither globally proved; new unconditional calligraphic D>=25 (L>=869) |
|13. Hard core | four tagged dirty-light mechanisms with full global decorations; not four solved fixed-size CSPs |
|14. Counterexamples | explicit local dirty sigma2 cost2 vs clean6;11 repeat-cost-charge failures; scope-correct trim caveats |
|15. L6 implication |869<=L6<=872; old55/55 NR6 result preserved |

## Evidence and computational scope

- All720 symbol renamings ×719 shortest connectors:517,680 checks.
- Formula versus independent absorbing-window suffix BFS, n3..6; n6
  7,776 suffix states/46,656 character edges, uncapped.
- Selected-splice196 construction controls in the final shadow audit;
  this is corroboration, not a global exact cover enumeration.
- Twenty fixed ordinary-chain domains, two independently implemented recurrences.
- Two independent heavy-seam generators agree on all3504 attempts.
- A/AB marked capacities b0,D0..5 completely exhausted twice.
- Low-slack14-row certificate independently convolved and composition-enumerated.

No blind full n6 DFS, no old frontier rebuild, no continuation worker, and
no automatic proof from a capped absence. Sources were committed and pushed
before load-bearing runs; final publication manifest records hashes, tests
and output scopes. Finite jobs retain compiler/argv/node/cap/digest provenance.

## Precise remaining work

The old plateau-escape conjecture is not the remaining deliverable. The
unresolved nonempty-domain mechanisms are coupling of sigma-cut endpoints
and marked shadow chains at larger budgets. Low-dimensional identities alone
do not identify their legal global histories. New statements must preserve
that occupancy/chronology or prove why it can be eliminated.

The repeated-domain investigation has therefore achieved a major structural
and unconditional-bound reduction, but not the final NR6-removal objective.

ASTRA_REPEAT_DOMAIN_MAJOR_REDUCTION
