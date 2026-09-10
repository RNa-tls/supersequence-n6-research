# Round 142 — no-repeat dependency audit

Author: CODEX. Audit of the active R115–R141 outer proof path, not a claim
that every historical repository sentence is valid. Old files are preserved.

| dependency / original role | actual premise | first-occurrence replacement | status |
|---|---|---|---|
| Literal length count | all-window M=720 under NR | selected M=720; actual gaps retained; FO identity | survives, hand proof |
| Pass arcs partition hexagons | unique selected vertices and full hex coverage | true for all first appearances | survives |
| nu permutation | preceding arc partition | same directed-arc successor | survives |
| P<=5O, D_phi>=0 | distinct pass-entry permutations | first-occurrence entries distinct | survives |
| k<=4 from Theorem A | clean free successor / nonnegative delta | false derivation when dirty w2; MASTER-142 restores it | repaired |
| R140 blocked free target old | clean tau plus registered blocker | clean row survives; dirty sigma row gets Y_d | corrected exact FREE-DIRTY |
| Delta bookkeeping | all descending free exits enter open orbit | fails for dirty selected w2 | delta=a+eta-Y_d |
| Splice literal source preservation | full-exit identity | unchanged even with hidden joint windows | survives |
| beta incidence connectivity/parity | T chronological full cycle, nu hex cycles | independent of literal repeats | survives |
| R_int<=2g | same incidence graph | selected multiplicities, not actual R | survives |
| Every free edge is E | absence of an intermediate permutation | dirty w2 instead sigma | essential failure |
| Pure-free circuits are whole E orbits | every retained free edge E and entry uniqueness | remove only pure **clean E** circuits | restricted, sound |
| Free blocks hex-simple | distinct E phases hit distinct hexes | clean E blocks only | survives after marking/cutting |
| Circuit has paid edge | no mixed E/sigma free circuit | false as an automatic extension | dirty cycle cut charged explicitly |
| R115 N*(b,0,D) | hex-simple full passes, clean w2/w3, all Q returns allowed | only ordinary extracted pieces | retained with stated scope |
| R125/old G1 engine exclusion | literal no-repeat and clean joint engine | cannot load for arbitrary dirty-heavy words | NOT USED for LC extension |
| R129 F=G / orbit name simplification | restricted split types | obsolete already at clean G>1 | NOT USED |
| R139/140 cutting / sharing | whole clean free blocks, count all return events | B* includes D2; mixed shadows remain explicit | generalized |
| R139 equality w4 seams | no intermediate permutation filter | that filter loses dirty-heavy seams | rerun enlarged domain |
| R140 G3 equality w4 seams | same hidden-window filter | all exact w4 tails including dirty | rerun enlarged domain |
| R141 six equality boundaries | same filter and static cover assumptions | 55 additional dirty seams first, then all-G3504 domain | rerun enlarged domain |
| Closed pure orbits covering missing hexes | five unique entry ports removed | true for selected pure clean E circuits | survives |
| R141 capacity convolution | ordinary pieces only | LC class all300 envelopes; AB elsewhere is new model | no silent transfer |
| General privacy / arbitrary orbit relabeling | unproved | never used | absent |
| NR6 normalization into clean domain | global existence of NR minimizer | LC is sufficient but transformation to LC unknown | remains open |

The original statement “repeats destroy nu” referred to **actual literal
pass multiplicities**, not to the selected first-occurrence arcs. It must
not be reused to deny the selected nu theorem. Conversely, selecting
first occurrences does not make the hidden windows in a dirty joint vanish.

## What the new capacities do and do not mean

`N_AB(0,D)` includes ordinary full E blocks and clean inter-orbit w3 moves,
plus mixed E-sigma and sigma-E moves. Sigma-E may demand a window visited
outside the piece. The capacity computation relaxes this external-history
constraint; it is an upper bound, not a feasible word claim.

Both implementations enforce hex simplicity, no repeated orbit when b=0,
exact local phase deficit, and all relevant dirty mixed targets. The
independent implementation derives moves from literal endpoint overlap and
hidden substring tests, not the producer's four selected tail formulas.
It does not import historical supply/phase-capacity helpers.

No stored v1/v2 search frontier, live worker, old checkpoint, or supervisor
was changed by Round142. The new computations are suffix automata, ordinary
fixed-chain domains, small marked-chain capacities, and finite convolutions.

## Inherited and new verification

The user's incoming independently accepted55-cell NR6 result remains an
accepted baseline. This round retains ordinary capacity values as named
dependencies, with paired new domains as needed; it does not rewrite old
partial-audit footnotes. The unconditional869 corollary needs only one old
paired numerical bound, N*(1,0,3)=48, plus the new small AB capacities and
new hand inclusion. Thus it does not obtain an unconditional statement by
relabeling the whole historical conditional ledger.
