# Marked port skeleton for `F=1,D=4,N=1`

## Proved unmarked skeleton

The `F=1,D=4` port-incidence theorem is independent of `N`: every completion
has 25 used E-orbits, 120 rotation hexagons, 121 selected phase ports, one
degree-two split hexagon, and a 24-component bipartite forest.  Its E-phase
deficit partition is one of

\[
[4], [3,1], [2,2], [2,1,1], [1,1,1,1].
\]

## Definition (marked transport defect)

Keep the unmarked port-incidence forest unchanged.  In addition record the
unique `Delta N=1` joint from the one-defect lemma as

\[
(\mathrm{type},w,Q_{\rm source},Q_{\rm target},
 B_{Q_{\rm target}}^{\rm before},B_{Q_{\rm target}}^{\rm after},
 \mathrm{fragment\ status}).
\]

This mark is a **chronological transport edge**, not another incidence edge.
It is not included in the forest edge count.

## Consequences (proved)

1. The incidence graph remains a forest: the marked joint does not add a
   pass-start/hexagon incidence and cannot create an incidence cycle.
2. Before and after the unique mark, every joint has `Delta N=0`; hence it
   obeys the N=0 zero-defect transition table.
3. The formal product of nine local deficit shapes with three defect types
   has at most 27 local marked forms before global transport constraints.

## Not implied by the skeleton

The unmarked forest does **not** determine the source-to-target transport of
a joint.  Consequently none of the following is currently a theorem:

- the mark lies within one incidence-tree component;
- the mark shares a component with the split hexagon;
- the mark is a re-rooting rather than a cross-component transport.

Those are exact-mask questions.  The bounded escape analysis records them for
the 23 available `N=0` terminal escapes, with a partial current port graph;
it does not extrapolate them to all completed skeletons.
