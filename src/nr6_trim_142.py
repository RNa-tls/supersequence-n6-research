#!/usr/bin/env python3
"""NR6 hard core — the ARC/TRIM lemma and its exact local obstruction.

ARC LEMMA (proved here).  In a covering walk, let hexagon h (a sigma-cycle of
length n) carry s_h occurrences on its n vertices.  If s_h > n then some
maximal sigma-run in h has an ENDPOINT of multiplicity >= 2.

  Proof.  Suppose every run endpoint in h has multiplicity 1.  Some vertex v
  has multiplicity >= 2, so v is interior to >= 2 runs R1, R2.  Walk from v
  along the cycle inside R1 to R1's endpoint b.  If R2 covered all of that
  stretch it would contain b, giving b multiplicity >= 2 - excluded.  So R2
  ends strictly before b, at some c lying in R1's interior, so c has
  multiplicity >= 2 and is an endpoint - contradiction. QED

TRIM.  Let a be such an endpoint at the END of its run, a' = sigma^{-1}(a) its
predecessor in the walk, z the walk's next vertex.  Replacing a'->a->z by
a'->z keeps coverage (a is covered elsewhere) and changes weight by
w(a',z) - 1 - w(a,z) <= 0 by the triangle inequality.

  It STRICTLY shortens the word iff w(a',z) < 1 + w(a,z), i.e. iff a is NOT a
  transit of (a', z).  If a IS a transit, the "trim" is a literal no-op: the
  spelled word is unchanged and a is still visited, now as an internal window.

So the entire local obstruction to shortening is the finite predicate

    BLOCK_fwd(a, z)  :=  a is a transit of (sigma^{-1}(a), z)
    BLOCK_bwd(y, a)  :=  a is a transit of (y, sigma(a))

which this module tabulates exhaustively.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nr6_geometry_142 import Geo

ROOT = Path(__file__).resolve().parent.parent


def tables(n):
    g = Geo(n)
    N = g.N
    ISIG = [0] * N
    for i in range(N):
        ISIG[g.SIG[i]] = i
    fwd = Counter()
    bwd = Counter()
    fwd_free_by_w = Counter()
    bwd_free_by_w = Counter()
    for a in range(N):
        ap = ISIG[a]
        for z in range(N):
            if z == a or z == ap:
                continue
            if not g.clean(a, z):
                continue                      # walk steps are clean
            blocked = a in {v for _, v in g.transit(ap, z)}
            fwd[(g.W[a][z], blocked)] += 1
            if not blocked:
                fwd_free_by_w[g.W[a][z]] += 1
    for a in range(N):
        sa = g.SIG[a]
        for y in range(N):
            if y == a or y == sa:
                continue
            if not g.clean(y, a):
                continue
            blocked = a in {v for _, v in g.transit(y, sa)}
            bwd[(g.W[y][a], blocked)] += 1
            if not blocked:
                bwd_free_by_w[g.W[y][a]] += 1
    return dict(
        n=n,
        forward={f"w{w}/blocked={b}": c for (w, b), c in sorted(fwd.items())},
        backward={f"w{w}/blocked={b}": c for (w, b), c in sorted(bwd.items())},
        forward_blocked_total=sum(c for (w, b), c in fwd.items() if b),
        forward_free_total=sum(c for (w, b), c in fwd.items() if not b),
        backward_blocked_total=sum(c for (w, b), c in bwd.items() if b),
        backward_free_total=sum(c for (w, b), c in bwd.items() if not b),
        forward_blocked_only_at_weights=sorted({w for (w, b) in fwd if b}),
        backward_blocked_only_at_weights=sorted({w for (w, b) in bwd if b}),
        forward_free_weights=dict(sorted(fwd_free_by_w.items())),
        backward_free_weights=dict(sorted(bwd_free_by_w.items())),
    )


def per_source_forward(n):
    """For each a, how many clean exits z are BLOCKED vs FREE, by weight."""
    g = Geo(n)
    N = g.N
    ISIG = [0] * N
    for i in range(N):
        ISIG[g.SIG[i]] = i
    prof = Counter()
    for a in range(N):
        ap = ISIG[a]
        T = lambda p, q: {v for _, v in g.transit(p, q)}
        b = f = 0
        bw = []
        for z in range(N):
            if z in (a, ap) or not g.clean(a, z):
                continue
            if a in T(ap, z):
                b += 1
                bw.append(g.W[a][z])
            else:
                f += 1
        prof[(b, f, tuple(sorted(set(bw))))] += 1
    return {f"blocked={k[0]},free={k[1]},blocked_weights={list(k[2])}": v
            for k, v in sorted(prof.items())}


if __name__ == "__main__":
    out = {}
    for n in (3, 4, 5, 6):
        out[f"n{n}"] = tables(n)
    out["n6_per_source_forward_profile"] = per_source_forward(6)
    out["dichotomy"] = {f"n{n}": dichotomy_proof_check(n) for n in (3, 4, 5, 6)}
    (ROOT / "outputs" / "rr_nr6_trim_142.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False, indent=1))


def dichotomy_proof_check(n):
    """TRIM DICHOTOMY, with the symbolic reason verified exhaustively.

    Claim: for a' = sigma^{-1}(a) and any z with (a,z) clean, w(a,z)=w:
        w = n      ==>  w(a',z) <= n < n+1, so a is NOT a transit: FREE.
        w <= n-1   ==>  w(a',z) = w+1 exactly, so a IS a transit: BLOCKED.

    The w<=n-1 half holds because the overlap condition
    suffix_{n-w}(a) = prefix_{n-w}(z) with a = sigma(a') forces
    prefix_{n-w-1}(z) = suffix_{n-w-1}(a'), giving w(a',z) <= w+1, and no
    smaller overlap can occur.  Both halves are checked literally below.
    """
    g = Geo(n)
    N = g.N
    ISIG = [0] * N
    for i in range(N):
        ISIG[g.SIG[i]] = i
    bad = []
    counts = Counter()
    for a in range(N):
        ap = ISIG[a]
        for z in range(N):
            if z in (a, ap) or not g.clean(a, z):
                continue
            w = g.W[a][z]
            blocked = a in {v for _, v in g.transit(ap, z)}
            predicted = (w <= n - 1)
            counts[(w, blocked)] += 1
            if blocked != predicted:
                bad.append((a, z, w, blocked))
            if w <= n - 1 and g.W[ap][z] != w + 1:
                bad.append(("weight", a, z, w, g.W[ap][z]))
            if w == n and not (g.W[ap][z] <= n):
                bad.append(("wn", a, z))
    return dict(n=n, violations=len(bad), examples=bad[:5],
                dichotomy_holds=(len(bad) == 0),
                by_weight={f"w{w}/blocked={b}": c for (w, b), c in sorted(counts.items())})
