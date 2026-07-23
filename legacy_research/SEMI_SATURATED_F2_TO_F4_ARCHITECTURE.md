# Semi-saturated architecture for the intermediate F slabs

## Purpose and logical direction

The intermediate regimes `F=2,3,4` sit between two already distinct tools:

- the completed saturated `F=5,D=0,N=0,H<=3` forest computation; and
- the literal exact-state engine used for `F=1`.

This architecture is a **necessary-condition relaxation**.  It may rule out a
coordinate slab only when its relaxed instance is infeasible.  A surviving
relaxed object is not a walk and is never reported as one.

## Coordinate envelope

For every hypothetical `L<=871` completion,

\[
P=120+F,\quad O=24+k,\quad D=5k-F,\quad
S=24+k-F+N,\quad k+N+H\le4.
\]

Thus `D>=0` forces `F<=5k`.  The model uses the 720 phase ports `(Q,j)` of
the 144 five-phase E-orbits.  A selected port maps to one of the 120 rotation
hexagons.

At its first layer it requires exactly:

1. `P` selected distinct ports in `O` nonempty E-orbits;
2. total E-phase deficit `D`;
3. every rotation hexagon has at least one selected port; and
4. total hexagon-incidence excess `sum_h(max(0,m_h-1))=F`.

These conditions follow from pass starts and `P=120+F`.  They intentionally
omit all ordering constraints.

## Second layer: arc and fragment data

For a hexagon of port multiplicity `m_h`, an exact completion must partition
its six cyclic vertices into `m_h` directed rotation arcs.  The second layer
therefore stores a cyclic composition of six for each `m_h>1`, together with
the entry/exit port of each arc.  Its total excess is still `F`.

This records fragment geometry without pretending that a port mask determines
repair phase or chronological order.  In particular it allows the observed
three-arc hexagon phenomenon when `F>=2`.

## Third layer: credit chronology

An exact lift must orient the arc blocks into one path and attach each joint
with the exact credit data

\[
\Delta N=\mathbf1_{w\ge3}+\mathbf1_{\rm abandonment}
          -\mathbf1_{\rm new\ E-orbit}.
\]

The semi-saturated model only tracks the aggregate `N,H` budgets and records
which E-orbits would have to be new.  Any candidate that survives this layer
is passed to the literal exact-state engine; it is never accepted by the
relaxation alone.

## Computation gates

1. **Port envelope.** Solve or enumerate only selected ports, modulo the
   already-proved left-`S_6` action.  Infeasibility is a valid exclusion.
2. **Arc refinement.** Add cyclic compositions to the finitely many
   multiply-hit hexagons.  Check only necessary compatibility conditions.
3. **Credit refinement.** Add `N,H` budgets and new-orbit labels.
4. **Exact lift.** Only survivors become seeds for checkpointed literal
   exact-state exploration.

The present implementation, `work/superperm_semisaturated_model.py`, covers
Gate 1 only.  It has two read-only controls:

- an existing verified `F=5` forest certificate validates the saturated
  port envelope; and
- deleting its extra orbit and retaining one phase validates that the
  `F=1,D=4` envelope is nonempty, while making no exact-walk claim.

## What is deliberately deferred

No semi-saturated enumerator, no dominance prune, and no `F=2,3,4` exact
search is started by this architecture.  The active `F=1,H=0,N=0` search
remains the first exact calculation.  Its terminal structure determines
which of the later arc/credit refinements is worth implementing.
