# What still stands between this work and closing the RR branch

Round 35, section 17. Source `outputs/rr_target_a_coverage_certificate.json`.

## 1. Closed

| result | round | grade |
|---|---|---|
| Target B impossible at all 18 known Target A boundaries | 30–32, 34 | exact exhaustive + independently verified UNSAT |
| No **completable** Target A boundary beyond the 22 long-prefix roots | **35** | root-local exhaustive (Q2) |

## 2. Open — five gaps, two of them identified for the first time this round

**(a) Q1: Target A coverage without the completability assumption.**
`INCOMPLETE` at all 22 roots. The only prune strong enough to terminate the
search is the capacity bound, and that bound is verified to delete a genuine
known Target A boundary. Grade: **bounded incomplete**.

**(b) NEW — the short-family enumeration was depth-truncated, and its
`frontier_empty` flag cannot detect that.** The enumeration that produced the
12 short Target A boundaries (`analyze_rr_ell0_family.py`) reports
`frontier_empty: true` for every abandonment ell. But that flag is computed
as `not cap_hit and len(frontier) == 0` **after** states at the depth ceiling
have been dropped without being expanded — so an entirely ceiling-truncated
run also reports an empty frontier. Counting the dropped states directly:

| abandonment ell | depth ceiling | expanded | states dropped **at** the ceiling |
|---|---|---|---|
| 0 | 7 | 12,957 | **9,143** |
| 1 | 7 | 12,367 | **8,710** |
| 2 | 7 | 13,103 | **9,245** |
| 3 | 7 | 13,029 | **9,189** |
| 4 | 8 | 43,459 | **30,408** |

Roughly **70% of every frontier was discarded unexpanded.** The 12 short
boundaries are correct as witnesses, but the claim that they are *all* the
short boundaries has no support. Grade: **scope correction**. This is the
largest gap in the Target A list and it was not on the brief's list.

**(c) NEW — the 6 FOUND long-prefix roots were searched with
`--stop-on-first`.** Each was abandoned the moment one witness appeared
(2, 2, 12, 14, 14, 14 nodes). Those roots may carry further Target A
boundaries that were never enumerated. Grade: **scope correction**.

**(d) First-return excursions with L > 8.** The surviving long-excursion
corpus contains only L = 7 and L = 8. Grade: **미완료**.

**(e) Abandonment roots and short prefixes outside the 28 long-excursion
prefixes.** The 22 roots decided here are **disjoint** from the 5 abandonment
roots that produced the 12 short boundaries and from the 6 FOUND long roots.
Neither set exhausts the RR prefix space. Grade: **미완료**.

## 3. Not applicable / vacuous, recorded rather than dropped

* **CH1 / CH2 split at these roots** — the hub is incomplete at all 22, so C
  lies in the extension and the branch is undetermined at the root. The Q2
  search covers both branches because it explores every extension.
* **The ell=4 terminal-geometry backward filter** — the R2-edge ℓ is 0 across
  the ell=4 branch and 5 across the ell=0 branch, so no single predecessor
  class exists to filter against.
* **Orbit/phase reachability over-approximation** — complete graph
  (out-degree 720/720), distance to (1,4) is 1 from every root; excludes
  nothing.

## 4. The honest closure statement

> **RR is not closed.** What is closed is: Target B from every known Target A
> boundary (Round 34), and completable Target A from the 22 long-prefix roots
> (Round 35). Gap (b) alone means the list of *short* Target A boundaries is
> unverified, and that list is where 12 of the 18 known boundaries came from.

Round 34's Target B exhaustion is **not** extended to RR as a whole, and this
round's Q2 exhaustion is **not** presented as Target A coverage.

## 5. Unchanged

* `L_6 ≤ 872` — verified in this repository (`data/verified_872_witness.txt`).
* `L_6 ≥ 867` — proved.
* `L_6 ≥ 872` — **open**. Nothing in this round moves it.
* The N=0 checkpoint — untouched, as instructed. CH2 chaining, T3 (exact
  observation 15/15), Target C, the U/J branches — all untouched.
