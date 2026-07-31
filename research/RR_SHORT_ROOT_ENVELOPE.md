# The five short roots: ledger and the +14 margin, decomposed

Round 38, Parts C and D. Source `src/analyze_rr_short_root_envelope.py` →
`outputs/rr_short_root_ledger.json`.

## 1. The ledger (§C)

The five short-family roots are the abandonment roots `rot^ℓ; w2:10` for
ℓ = 0..4 — the only roots Round 37's envelope did not close.

| root | ℓ | `P` | `O` | `M=P−5O` | `O_cap` | `R_cap` | `Ndef` | Φ | `q0` | `ph0` | hub popcount | initial partial hex popcount | legal first edges | envelope |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `short_ell0` | 0 | 2 | 2 | −8 | 23 | 3 | 0 | 1 | 120 | 1 | 1 | 1 | 4 | **+14** |
| `short_ell1` | 1 | 2 | 2 | −8 | 23 | 3 | 0 | 2 | 33 | 2 | 2 | 1 | 4 | **+14** |
| `short_ell2` | 2 | 2 | 2 | −8 | 23 | 3 | 0 | 3 | 9 | 3 | 3 | 1 | 4 | **+14** |
| `short_ell3` | 3 | 2 | 2 | −8 | 23 | 3 | 0 | 4 | 3 | 4 | 4 | 1 | 4 | **+14** |
| `short_ell4` | 4 | 2 | 2 | −8 | 23 | 3 | 0 | 5 | 1 | 0 | 5 | 1 | 4 | **+14** |

Legal first macro-edges are the same four at every root:
`rot^5;w2:10`, `rot^5;w3:120`, `rot^5;w3:201`, `rot^5;w3:210`.

Every root has zero previously generated boundaries and
`continuation_search_status = INCOMPLETE_TIMEOUT`.

### Not merged

All five share the resource signature `(P=2, O=2, Ndef=0)` — which is
exactly why their envelopes are identical. But they are **pairwise distinct
at both the raw state hash and the canonical decorated hash** (5 of 5
distinct at each level), and they differ in Φ (1..5), current orbit
(120, 33, 9, 3, 1), current phase, and hub residual popcount (1..5).

**They are not merged.** Per the round's instruction, an identical resource
signature is not sufficient grounds; their geometric reachability differs
even where their resource accounting does not.

## 2. The +14 margin, decomposed (§D)

The Round 37 envelope is

```
ENVELOPE(root) = M(root) + 5k + 7 + 5·max(n_limit − Ndef(root) − k, 0)
```

with `k = 2` for these roots (two R events still needed). Split into named
additive sources:

```
margin = M_root + preserving_slack + reentry_slack + terminal_slack + residual_R_cap_slack
   14   =  −8   +        8         +       2       +       7       +         5
```

| source | value | what it is |
|---|---|---|
| `M_root` | **−8** | the root's own conserved quantity `P − 5·O` |
| preserving slack | **+8** | ≤4 preserving steps per segment × `k`=2 segments, each `ΔM = +1` |
| re-entry slack | **+2** | the `k`=2 R edges themselves, each `ΔM = +1` |
| terminal slack | **+7** | `5·TARGET_O − TARGET_P + 3` = 125 − 121 + 3 |
| residual `R_cap` slack | **+5** | `5 × max(3 − 0 − 2, 0)` = 5×1 |

The identity is verified by assertion for every root
(`identity_total == root_envelope_margin`).

**All five decompositions are identical**, term by term — a direct
consequence of the shared resource signature, and the reason no root-specific
strengthening falls out of the decomposition alone.

## 3. Where the slack actually is

Two terms dominate: **preserving slack (+8)** and **terminal slack (+7)**.

* The **terminal slack** is structural and irreducible — it is a constant of
  the target values, identical for every root in the problem.
* The **preserving slack** is the only term with root-specific structure to
  exploit, which is why Part E attacks it directly. The universal bound of
  4 steps per segment is occupancy-independent and therefore safe; the
  question is whether an *entry-sensitive* refinement can beat it without
  reintroducing the hexagon-freshness assumption that Part A just
  firewalled off.

The answer, measured: **no**. See `RR_SHORT_ROOT_DEFECT_THEOREM.md`.
