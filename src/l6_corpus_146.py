#!/usr/bin/env python3
"""Round 146 — independent corpus generator of FIXED REPRESENTATIVES.

Independent of round 145: the random cover is grown by picking, at each step, a
random permutation not yet covered and splicing it on at its maximum overlap
(instead of appending random letters), which produces a very different length
and joint-type distribution.  The Phi fixed point is then taken with a
self-contained implementation.  Every emitted word is re-verified as a cover.
"""
from __future__ import annotations
import itertools, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from l6_cleanroom_146 import omega                                    # noqa


def windows(W, n):
    return [W[i:i + n] for i in range(len(W) - n + 1)]


def covered(W, n):
    return {w for w in windows(W, n) if len(set(w)) == n}


def phi(W, n):
    seen, sel = set(), []
    for w in windows(W, n):
        if len(set(w)) == n and w not in seen:
            seen.add(w)
            sel.append(w)
    out = sel[0]
    for j in range(1, len(sel)):
        out += sel[j][n - omega(sel[j - 1], sel[j]):]
    return out


def fixed(W, n):
    while True:
        nxt = phi(W, n)
        if nxt == W:
            return W
        assert len(nxt) <= len(W), "Phi lengthened"
        W = nxt


def grow(n, alpha, rng, junk=0.35):
    """Splice uncovered permutations on at maximum overlap, sometimes with junk."""
    need = {"".join(p) for p in itertools.permutations(alpha)}
    W = "".join(rng.sample(list(alpha), n))
    while True:
        miss = need - covered(W, n)
        if not miss:
            return W
        t = rng.choice(sorted(miss))
        k = omega(W[-n:], t)
        if rng.random() < junk:                # widen the gap on purpose
            W += "".join(rng.choice(alpha) for _ in range(rng.randint(1, n)))
            k = omega(W[-n:], t)
        W += t[n - k:]


def make(n, alpha, count, seed):
    rng = random.Random(seed)
    out, need = [], {"".join(p) for p in itertools.permutations(alpha)}
    seen = set()
    while len(out) < count:
        w = grow(n, alpha, rng)
        assert covered(w, n) == need
        f = fixed(w, n)
        assert covered(f, n) == need, "Phi broke the cover"
        if f in seen:
            continue
        seen.add(f)
        out.append(f)
    return out


if __name__ == "__main__":
    n = int(sys.argv[1]); count = int(sys.argv[2]); seed = int(sys.argv[3])
    alpha = "1234"[:n] if n == 4 else ("12345" if n == 5 else "123456")
    for w in make(n, alpha, count, seed):
        print(w)
