# Independent final cycle/suffix audit

An independent review agent inspected the hand lemmas and implementation
at commit `f176a0d5d0b92dbd0898dc752b3cfcd6f51023a9`. It performed no search
and did not infer soundness from agreement between outputs. No omitted case
or underapproximation was found in the following scoped checks.

1. Opening a non-E cycle edge preserves vertices, orbit/hex sets, D and R.
   With n non-E edges there are n E blocks, so b=n-O before and after opening.
   Preferring A, then B, retains every genuine component up to value renaming.
2. Closing uses the existing root vertex. Only A/B/heavy costs are added.
   The pending closing A/B is removed before the internal-suffix test r>=a+q;
   no additional repeat is reserved. Clean-w3 and heavy closing alternatives
   cover the remaining case.
3. The preferred closing source is uniquely sigma^-1(root) or sigma^-2(root).
   Passing it without closing cannot later lead to a valid cycle without
   repeating the entry port, so the early stop is sound.
4. The suffix budget is Dcap+5B-Dprefix-5bprefix at a chosen non-E exit.
   It excludes the boundary target and does not subtract an extra five for
   an old-orbit boundary. The deficit repair prunes grant all missing current
   phases and at most four repaired phases per future old-orbit entry.
5. The suffix allocator includes every piece count, retained-A count, and
   piece-b allocation. Upper-D resources may absorb unused deficit budget.
   Missing cells give the conservative sentinel, not an observed maximum.
6. Component allocation includes all sharing and nonnegative resource splits.
   Exact A/Q remain exact; unused extra-R/H may be assigned to the nonempty
   path. Actual D fixes the port-count residue. Zero denotes absence of any
   positive residue-compatible size, not a missing bound.
7. For d=1, all cycle sizes between max(1,T-path_upper) and cycle_upper are
   enumerated, filtered only by positive path size and the two necessary
   residue congruences. Cache keys retain every relevant resource.

The review explicitly relies on the inherited fixed-point/splicing hand
proof and the certified coupled-SIGMA capacity inputs. In particular,
A+Qs<=R per component follows from chronological beta-edge acyclicity,
not from arbitrary relaxed cycles. The separate end-to-end verifier audits
the execution artifacts, hashes, allocation reconstruction and exact-P count
conservation. The review is not claimed as a second execution of those runs.

## Separate foundation cross-check

A second read-only review inspected Round142 sections B1-B7 and the referenced
unconditional869, sigma-deficit, coupled-extraction, endpoint-correction,
component-convolution and cycle-accounting hand reductions. It found no
additional NR6 or light-clean premise in those inclusions.

The fixed-representative step preserves all retained permutations; equal
length forces every trim and gap unchanged. The spliced source endpoint is
the original literal endpoint, so dirty and heavy connectors are retained.
For A/B edges, a same-pass hidden-window case forces a full hexagon and an
already-selected target. Otherwise the hidden entry precedes the current
pass, giving strict chronology and componentwise A_i+Qs_i<=R_i.

Collapsing parallel hex/component incidences gives a connected bipartite
graph with 121+K vertices and P+1-R_int edges, including the dummy. Therefore
K+R_int<=G+1. A pure E circuit uses precisely five distinct ports and exhausts
its orbit; distinct selected entries prohibit another occurrence of that
orbit outside the circuit. Mixed E/A circuits are not removed.

This review checked model inclusion and inherited hand hypotheses only. It
ran no search, changed no files, and did not independently certify the
numerical enumerations. Its finding is not itself the end-to-end theorem.
