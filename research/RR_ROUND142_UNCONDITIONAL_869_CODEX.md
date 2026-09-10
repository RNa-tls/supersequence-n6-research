# Round 142 — unconditional exclusion of lengths through868

Author: CODEX. Computer-assisted theorem; no NR6 hypothesis.

## Theorem

Every literal n6 superpermutation has length at least869.
Together with the verified872 witness: **869<=L6<=872**.
This does not establish L6=872, nor any global +1 repeat gap.

## Proof and exact scope

Assume a cover of length<=868. Iterate first-occurrence geodesic projection
to obtain a fixed cover of no greater length. Apply the hand-proved selected
splice and shadow extraction in the Route B report. With t=L-867,

    t=k+Z+H+B*,    all four terms nonnegative,
    G<=5k, D2<=2g<=z, Z=z-D2,
    m<=z+1+h,
    sum D_j=5k-G+5s, sum b_j+s=B*,
    retained mixed edges<=sum D_j,
    cut mixed edges<=Z-Qs.

The same master gives L>=867; hence t is0 or1 and k is0 or1.

### k=0

G=0 forces D2=c=z=Z=Qs=0. If H=0, m<=1, so s=0 and sum D_j=0.
There are no retained or cut mixed edges. The single ordinary clean chain
has b<=1,D=0, and at most48 passes even using the conservative independently
verified upper bound N*(1,0,3)=48. It cannot supply120.

If H=1, B*=0, h<=1 and m<=2. Again s=sum D_j=0, no mixed edges, and each
piece has b=0,D=0, capacity20. At most40<120 passes are available.
These cases include t=0. No assumption about heavy-joint hidden windows was used.

### k=1

Necessarily t=1 and Z=H=B*=0. Therefore s=all b_j=0, Qs=0. From
z=2g+d, D2<=2g and Z=z-D2=0 we obtain d=0 and **D2=2g is even**.
For G=0,...,5, D2 is0,2,...,2 floor(G/2), and c=G-D2.
The marked AB pieces satisfy

    m<=D2+1, sum D_j=5-G,
    required passes=120-4G+5D2.

The independently exhausted marked capacities for D0..5 are
20,20,33,33,46,46. Nonnegative padding to m_max gives a safe upper bound.
Convolving them over total D=5-G yields:

| G | D2 | upper passes | required |
|---:|---:|---:|---:|
|0|0|46|120|
|1|0|46|116|
|2|0|33|112|
|2|2|73|122|
|3|0|33|108|
|3|2|73|118|
|4|0|20|104|
|4|2|60|114|
|4|4|100|124|
|5|0|20|100|
|5|2|60|110|
|5|4|100|120|

Every inequality is strict. These12 rows plus the two k0 rows exhaust the
resource possibilities. Recurrence convolution and independent Cartesian
allocation enumeration agree on every row. Contradiction.

## Proof dependencies and limits

The load-bearing mathematical ingredients are selected arc partition,
unchanged splice endpoints, dirty same-hex charge, mixed-shadow injection,
and the free-block identity. They are hand arguments on arbitrary fixed-point
covers, with finite controls as secondary evidence. The capacity models are
necessary relaxations and their finite searches are complete and uncapped.
The k0 proof uses the existing paired R139 N*(1,0,3)=48 certificate; it
does not assume the whole NR6-conditional55-cell closure.

The finite result is stored in `rr_round142_low_slack_verified_codex.json`;
marked capacities in `rr_round142_shadow_capacities_codex.json`.
No extrapolation to t=2,3,4 is valid: additional sigma-cut pieces and marked
capacity budgets are then possible. Those cases remain unresolved.
