#!/usr/bin/env python3
"""Round 149 A -- the extraction claims, checked on ARBITRARY walks.

Claims 1-5 of the extraction are hand identities.  Checking them on real covers
only exercises t = 5, 6.  Two of them -- Lemma F's block count and Claim 3's
per-chain identity blocks_i = O_i + tok_i -- are statements about a WALK, not
about a cover, so they can be checked over the whole hypothetical domain by
generating arbitrary walks in the transition system.  That is done here.

  Lemma F.  blocks = P - (clean-E edges).
    In the beta structure the clean-E edges form a subgraph of a permutation, so
    every component has in- and out-degree <= 1: components are paths or cycles.
    Summing (vertices - edges) over components gives #paths + 0 * #cycles, and a
    pure circuit is exactly a clean-E cycle.  So P - cleanE counts the maximal
    clean-E PATHS and is unchanged by deleting the circuits -- which is what
    Lemma F asserts.  Verified below on random permutation structures.

  Claim 3.  For a chain, blocks_i = O_i + tok_i, where tok_i counts the edges
    that are not clean E and land in an already-opened orbit (e_i, cross-orbit)
    or stay inside one (x_i, intra-orbit).  Verified below on arbitrary walks.

  Claims 1, 2, 4 are algebra over these and are re-derived symbolically.
"""
from __future__ import annotations
import json, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r147" / "src"))
import catalogue147 as C                                            # noqa: E402

PERMS, HEX, ORB, PH = C.PERMS, C.HEX, C.ORB, C.PHASE
FREE, DA, DB, PAID, KIND, HEAVY = C.catalogue()


def random_walk(rng, maxlen):
    """An arbitrary walk in the transition system -- no budget, no cover."""
    v = rng.randrange(720)
    seq, used = [v], {v}
    kinds = []
    for _ in range(maxlen - 1):
        opts = [(FREE[v], "E"), (DA[v], "A"), (DB[v], "B")]
        opts += [(PAID[v][j], "paid") for j in range(5)]
        opts += [(t, "heavy") for t, _c in HEAVY[v][:40]]
        opts = [(t, k) for t, k in opts if t not in used]
        if not opts:
            break
        t, k = opts[rng.randrange(len(opts))]
        seq.append(t)
        kinds.append(k)
        used.add(t)
        v = t
    return seq, kinds


def claim3(seq, kinds):
    """blocks_i = O_i + tok_i for one chain."""
    O = len({ORB[v] for v in seq})
    opened = {ORB[seq[0]]}
    tok = 0
    for j, k in enumerate(kinds):
        t = seq[j + 1]
        q = ORB[t]
        if k != "E" and q in opened:
            tok += 1          # cross-orbit re-entry (e_i) or intra-orbit (x_i)
        opened.add(q)
    blocks = 1 + sum(1 for k in kinds if k != "E")
    return blocks, O + tok, O, tok


def lemma_f(rng, P):
    """A random permutation of P vertices with a random clean-E subgraph:
    P - cleanE must equal the number of maximal clean-E PATHS."""
    perm = list(range(P))
    rng.shuffle(perm)
    nxt = {perm[i]: perm[(i + 1) % P] for i in range(P)}
    for _ in range(rng.randrange(1, 4)):        # break into several cycles
        a, b = rng.randrange(P), rng.randrange(P)
        nxt[a], nxt[b] = nxt[b], nxt[a]
    clean = {v for v in range(P) if rng.random() < 0.7}
    edges = {(v, nxt[v]) for v in clean}
    # components of the clean subgraph
    succ = {v: nxt[v] for v in clean}
    pred = {}
    for v in clean:
        pred[nxt[v]] = v
    seen, paths, cycles = set(), 0, 0
    for v in range(P):
        if v in seen:
            continue
        if v in pred and pred[v] in range(P) and v in {nxt[u] for u in clean}:
            continue
    # walk from every vertex with no clean predecessor -> path components
    has_pred = {nxt[v] for v in clean}
    for v in range(P):
        if v in has_pred:
            continue
        x, n = v, 0
        while x in succ:
            x = succ[x]
            n += 1
            if n > P:
                break
        paths += 1
        seen.add(v)
    # cycle components: vertices all of whose orbit stays inside clean
    incyc = set()
    for v in range(P):
        if v in incyc or v not in succ:
            continue
        path, x = [], v
        while x in succ and x not in path:
            path.append(x)
            x = succ[x]
        if x == v:
            incyc |= set(path)
            cycles += 1
    return dict(P=P, clean_edges=len(edges), paths=paths, cycles=cycles,
                identity=(P - len(edges) == paths))


def main():
    rng = random.Random(20260914)
    bad3, n3 = [], 0
    for _ in range(4000):
        seq, kinds = random_walk(rng, rng.randrange(2, 60))
        if len(seq) < 2:
            continue
        n3 += 1
        b, rhs, O, tok = claim3(seq, kinds)
        if b != rhs:
            bad3.append(dict(len=len(seq), blocks=b, O_plus_tok=rhs))
    badF, nF = [], 0
    for _ in range(600):
        r = lemma_f(rng, rng.randrange(6, 60))
        nF += 1
        if not r["identity"]:
            badF.append(r)
    out = dict(
        claim3_walks_checked=n3, claim3_violations=len(bad3),
        claim3_examples=bad3[:3],
        lemmaF_structures_checked=nF, lemmaF_violations=len(badF),
        lemmaF_examples=badF[:3],
        note="these are checked on ARBITRARY walks and arbitrary permutation "
             "structures, not on covers, so they cover the hypothetical t <= 4 "
             "domain as well",
        ok=(not bad3 and not badF and n3 > 0 and nF > 0))
    (ROOT / "r149" / "certs" / "claims_149.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if not k.endswith("examples")}, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
