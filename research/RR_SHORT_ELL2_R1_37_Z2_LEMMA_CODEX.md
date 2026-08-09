# `short_ell2_r1_37` direct-Z2 lemma

## Lemma

Before any component-changing Z3 event, a Z2 transition cannot merge the
R1-target component with the hub component in `short_ell2_r1_37`.

## Proof

Before such a Z3 event, the R1-target component contains exactly E-orbit 91.
A full five-rotation segment followed by the unique weight-2 flip acts by E
on the pass start.  Hence it preserves the pass-start E-orbit.  This was also
checked directly for all `144 × 5 = 720` orbit phases.

The five phases of orbit 91 occupy the hexagons

```text
{40,82,90,91,92}.
```

The hub component contains the hexagons

```text
{0,1,4,6,8,9,18,24,96}.
```

Their intersection is empty.  Therefore a Z2 incidence from the unexpanded
R1 component cannot land in a hub-component hexagon and cannot merge the two
components.  QED.

## Exact scope

The condition “before any component-changing Z3 event” is essential.  Such a
Z3 can add another orbit to the R1-target component.  A later Z2 on that new
orbit is not covered by the orbit-91 argument.

Thus this is not an all-Z2 theorem after arbitrary Z3 history.

## Machine certificate

[The certificate](../outputs/rr_short_ell2_r1_37_z2_lemma_certificate.json)
contains the five exact orbit-91 words and phases, both hexagon sets, the
empty intersection, all 720 preservation checks, and the explicit
invalidation condition.

