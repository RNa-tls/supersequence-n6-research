# Round 38 — independent audit of the Round-37 capacity envelope

## Result and provenance

Round 37 supplied the claim; `src/verify_rr_round37_envelope_independent.py`
is the independent verifier.  Before using the local exact engine it compares
the normalized source SHA-256 of both exact-engine files against commit
`0dcde29`.  It does not import a Round-37 envelope, root-replay, or capacity
helper.

The verifier replayed all 33 roots and obtained the advertised partition:

```text
33 roots = 28 long Q2-impossible roots + 5 short unresolved roots.
```

For a root state define `M=P−5O`.  A macro joint starts one pass, hence
`ΔP=1`.  The exact transition bit `new_orbit` gives `ΔO∈{0,1}`, so

```text
new_orbit = false: ΔM = +1
new_orbit = true : ΔM = −4.
```

Under the RR classification, preserving `Z2` and re-entry `R` are the first
case; fresh `Z3` is the second.  This is an algebraic consequence of the
exact transition update, not a sampled regularity.  The audit additionally
examined every legal macro edge at all 33 independently replayed roots
(688 edges: 33 Z2, 47 R, 462 Z3, 146 abandonment Z2), and confirmed these
deltas.  `Z2abandon` and any non-RR `other` edges are outside the envelope
alphabet; they are not silently treated as preserving.

## Envelope calculation

Let `k` be the R events still required: `k=1` for long roots and `k=2` for
the short roots.  With `R_cap=max(3−Ndef−k,0)`, the independently computed
upper bound is

\[
 E(r)=M(r)+5k+7+5R_{cap}.
\]

The `5k` term is the stated occupancy-independent RR structural bound: no
preserving segment has more than four `Z2` moves, while an intervening fresh
`Z3` lowers `M` by four.  This audit verifies the arithmetic and root data;
the group-theoretic “four preserving moves” lemma remains an imported
historical premise, not a result of enumerating 1,398 boundaries.

The audit finds `E<0` for every long root (values −13 or −4) and `E=+14`
for each short root.  Thus the 28 long roots are Q2-impossible; no conclusion
is forced for the short five.

## Replayed boundary corpus

Every one of the 1,398 stored `(root,path)` records was literally replayed.
All 1,398 raw state hashes and full literal-word hashes are distinct.  Each
fails the independently recomputed coarse theorem

\[
5(O_{cap}+R_{cap})+4 < B+1.
\]

The 1,398 hits occur at 26 of the 28 long roots; the 15 observed quotient
profiles are the tuples `(O_cap,R_cap,1+(5−used_ports(current_orbit)))`.
No verdict field from the Round-37 ledger is trusted for these calculations.
Full reproducible data: `outputs/rr_round37_envelope_independent_verification.json`.

## Scope conclusion

The envelope makes the remaining Round-35 **long-root Q1 searches**
unnecessary to settle Q2, not mathematically unnecessary as Q1 abundance
enumerations.  The two questions must not be conflated.
