# The one-defect lemma for `F=1,H=0,N=1`

## Theorem (proved)

Under NR6, suppose a completed walk has

\[
F=1,\qquad H=0,\qquad N=1,
\qquad (P,O,D)=(121,25,4).
\]

Then exactly one nonrotation joint has `Delta N=1`, and every other joint is
one of the zero-defect `N=0` flow types.  The unique defect is exactly one of
the following three normal forms:

| type | weight | abandonment | target E-orbit | `(Delta F,Delta S,Delta O,Delta N)` |
|---|---:|---:|---|---|
| `R` blocked strand revisit | 3 | 0 | already open | `(0,1,0,1)` |
| `A3` abandoning new strand | 3 | 1 | new | `(1,1,1,1)` |
| `A2` abandoning old-orbit entry | 2 | 1 | already open | `(1,0,0,1)` |

There is no fourth independent defect event.

## Candidate-event audit

| proposed event | possible? | exact interpretation |
|---|---|---|
| blocked `w3` into an existing E-orbit | yes | normal form `R` |
| abandonment `w2` into an existing E-orbit | yes | normal form `A2` |
| blocked `w2` repair opening a new E-orbit | no | blocked-`w2` lemma forces an existing orbit, hence `Delta N=0` |
| strand start in an existing E-orbit | yes | this is exactly `R`, not a second kind of event |
| “same opening counted twice” | no independent event | `O` counts a nonempty orbit only once; a later entry is simply an existing-orbit target and falls in the preceding rows |
| abandonment `w3` into a new E-orbit | yes | omitted by the initial candidate list, but is normal form `A3` |

## Proof

At a joint set

\[
a=\mathbf1_{\rm abandonment},\quad s=\mathbf1_{w\ge3},\quad
o=\mathbf1_{\rm new\ E-orbit}.
\]

Then `Delta N=s+a-o`.  The blocked-`w2` lemma gives
`w=2,a=0 => o=0`, so every legal joint has `Delta N>=0`.  Since the initial
state has `N=0` and the final state has `N=1`, exactly one joint has increment
one and no joint has increment two.

With `H=0`, only `w=2,3` occur.  Enumerating the Boolean pairs `(a,o)` gives
the displayed three increment-one cases.  In particular, a `w3` abandonment
into a **new** E-orbit is a genuine third defect normal form; it cannot be
omitted.  A `w3` abandonment into an existing orbit has increment two and is
therefore excluded.  A blocked `w2` repair is forced into an existing orbit
and has increment zero. \(\square\)

## Corollary (proved)

Since `S=O-F+N=25`, a completed walk has 24 weight-three joints.  Its event
counts are forced by the defect type:

| unique defect | normal blocked/new `w3` joints | abandoning/new `w2` joints |
|---|---:|---:|
| `R` | 23 | 1 |
| `A3` | 23 | 0 |
| `A2` | 24 | 0 |

Together with the initial E-orbit these account for exactly 25 opened
E-orbits.  Thus the defect is not a diffuse bookkeeping error: it is one
literal, marked joint.

## Limits

This theorem says nothing about whether any of the three normal forms can be
embedded in a collision-free complete walk.  That is the remaining exact-mask
problem.  The `N=0` terminal escape analysis is a restricted experiment on
one source of candidate defects, not a proof that all three types occur.
