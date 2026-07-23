# F=1, H=0, N=0 flow normal form

## Scope

This is a conditional statement inside the no-repeat (`NR6`) exact-state
model.  It concerns only a completed walk with

\[
F=1,\qquad H=0,\qquad N=0,\qquad P=121,\qquad O=25,\qquad D=4.
\]

It neither proves that this subcase is empty nor assumes the clean
full-cassette hypotheses used by G2.

## Lemma 1 (joint credit identity)

At every nonrotation joint let

\[
a=\mathbf1_{\rm abandonment},\qquad
s=\mathbf1_{\{w\ge3\}},\qquad
o=\mathbf1_{\rm new\ E\text{-}orbit}.
\]

Then

\[
\Delta N=s+a-o. \tag{1}
\]

**Proof.** By definition `N=S+F-O`; a joint changes these three quantities by
`s`, `a`, and `o`, respectively.  \(\square\)

The blocked-`w2` lemma gives the additional implication

\[
w=2,\ a=0\quad\Longrightarrow\quad o=0. \tag{2}
\]

## Theorem 2 (N=0 joint normal form)

Suppose `H=0` and `N` remains zero.  Then every joint is exactly one of:

| joint | abandonment `a` | new E-orbit `o` | effect |
|---|---:|---:|---|
| `w=3` | 0 | 1 | opens one new E-orbit, `ΔN=0` |
| `w=2` | 1 | 1 | the unique possible abandoning opening, `ΔN=0` |
| `w=2` | 0 | 0 | blocked repair/revisit, `ΔN=0` |

No other case is possible.

**Proof.** `H=0` excludes weights four or larger, so a nonrotation joint has
weight two or three.  If `w=3`, (1) gives
`ΔN=1+a-o`.  Since `o≤1`, equality to zero forces `(a,o)=(0,1)`.
If `w=2`, (1) is `ΔN=a-o`.  Equality to zero forces `a=o`; the blocked case
`a=0` is consistent with (2), while the other possibility is `(a,o)=(1,1)`.
\(\square\)

## Corollary 3 (completed F=1,H=0,N=0 census)

The initial pass opens one E-orbit.  The final coordinate values give

\[
S=O-F+N=24.
\]

Hence a complete walk in this subcase has exactly:

- 23 weight-three joints, all blocked and all opening distinct new E-orbits;
- 1 abandoning weight-two joint, opening the remaining new E-orbit; and
- every other weight-two joint blocked and landing in an already opened
  E-orbit.

Indeed `S` begins at one and only `w≥3` joints increase it, so there are
`S-1=23` weight-three joints.  The single abandonment is forced by `F=1`.
The 23 new openings, the one abandoning opening, and the initial orbit
account for all 25 opened E-orbits.

## Use and limitation

This reduces the exact `N=0` problem to a rigid chronological transport
problem: all 23 deep joints must avoid every opened E-orbit, while the sole
fragment event is a `w2` opening and all later non-opening `w2` joints are
blocked repairs.  The statement does **not** say that such a schedule is
impossible.  The active exact search and its terminal-mask analysis address
that remaining global collision problem.
