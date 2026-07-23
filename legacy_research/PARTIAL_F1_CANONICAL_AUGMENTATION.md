# Canonical child augmentation and bounded census for `F=1`

## 1. Value-relabel action

For `alpha in S_6`, define its left action on a word by

\[
 (\alpha\cdot p)(i)=\alpha(p(i)).
\]

It commutes with every right position action:

\[
 \alpha\cdot(p a)=(\alpha\cdot p)a. \tag{1}
\]

Consequently it sends every literal tail `(w,pi)` to a tail with the same
label and the same resource increments.  It permutes rotation hexagons and
`E`-orbits.  Because the selected canonical representative of an image
hexagon/orbit can be rotated, the corresponding six- and five-bit masks are
also shifted by the unique local `sigma` or `E` phase.  The implementation
precomputes these 720 coordinate transports and moves together:

- terminal `p`;
- all nonzero hexagon masks;
- all nonzero `E`-phase masks;
- the fragment arcs implicit in the hexagon masks;
- `F,S,H` (fixed by relabelling).

## 2. Canonical representative

For an exact state `x`, let

\[
 \operatorname{can}(x)=\min_{\alpha\in S_6}\alpha\cdot x, \tag{2}
\]

where the ordering serializes `p`, sparse nonzero `(hexagon,mask)` entries,
sparse nonzero `(E-orbit,mask)` entries, and then `(F,S,H)`.  Sparse encoding
is an implementation optimization only; it retains all zero coordinates by
their fixed ambient index set.

### Theorem 1 (canonical-child completeness) — Proof

In a search which expands `can(x)`, forms every legal child `y`, then inserts
`can(y)` unless that exact canonical state was previously seen, every
left-`S_6` orbit of reachable prefixes is represented.

**Proof.**  By (1), relabelling gives a bijection from legal tails out of `x`
to legal tails out of `alpha·x`, preserving collision status and counters.
Induct on prefix length.  The initial orbit is represented.  If a reachable
prefix `y` extends `x`, the representative of `x` has a relabelled legal
child in the orbit of `y`, so the algorithm inserts `can(y)` unless an
identical representative was already inserted.  In the latter case the same
future completions are already represented by Markov sufficiency.  ∎

This intentionally uses **canonical children**, not a strict
canonical-parent test.  A strict parent test would require a separate proof
that every complete orbit has a surviving parent order; no such unproved
assumption appears here.

## 3. Checkpoint / resume format

The command

```powershell
& $py work\superperm_partial_f1.py census `
  --max-depth 2 --node-limit 1000 `
  --checkpoint outputs\f1_depth2.checkpoint.json `
  --checkpoint-every 100 `
  --output outputs\f1_depth2_census.json
```

is deliberately bounded.  It writes checkpoints atomically (`.tmp`, then
replace) and stores:

- code and core SHA-256;
- the exact configuration;
- the canonical frontier, serialized as full sparse exact states;
- exact memo keys; and
- expansion, generation, acceptance, depth, and prune counters.

Resume refuses a checkpoint whose code SHA or configuration differs:

```powershell
& $py work\superperm_partial_f1.py census `
  --max-depth 2 --node-limit 1000 `
  --resume outputs\f1_depth2.checkpoint.json `
  --checkpoint outputs\f1_depth2.checkpoint.json `
  --output outputs\f1_depth2_census_resumed.json
```

The current command rejects `--node-limit 0`.  It is a diagnostic engine,
not an overnight enumerator.  A later exhaustive runner must make a separate
reviewed choice of splitting, checkpoint size, memory limits, and independent
verification.

## 4. Bounded-experiment outputs

Each census records:

- canonical state counts by reached depth;
- all safe prune reasons;
- accepted states by `N+H=0,1,2,3`;
- fragment-arc shape counts;
- elapsed time, remaining frontier, whether a node bound was hit, and Python
  `tracemalloc` peak bytes (clearly a Python-allocation measurement rather
  than a claim about total native-process RSS).

These are **bounded diagnostics**.  In particular, no missing target state at
a chosen depth or node cap is evidence that the slab is empty.

## 5. First theory targets after validation

The next valid milestone is one of the following, with its status explicitly
labelled: a proof that `N+H>=4` for this slab; a finite complete classification
of one-fragment arc shapes; a bound on fragment collision escapes; or a
verified finite depth at which the budgeted canonical state graph dies.

None of these is claimed by this document.  The forest-only calculation is
finished and is deliberately not rerun or altered by this engine.
