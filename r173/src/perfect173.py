#!/usr/bin/env python3
"""Round 173 -- the equality case Delta(n) = 0 as a finite combinatorial object.

A PERFECT CHAIN for n is a sequence e_1, ..., e_m of permutations, m = (n-2)!,
such that
  (i)   the tau-orbits T(e_i) = {tau^j e_i : 0 <= j <= n-2}  (tau(s) = s[1:-1]+s[0]+s[-1])
        consist of permutations in pairwise distinct hexagons (sigma-classes,
        sigma(s) = s[1:]+s[0]) and together hit EVERY hexagon exactly once;
  (ii)  for each i, with f_i = tau^{n-2} e_i and x_i = sigma^{n-1} f_i
        (the last window of the block), e_{i+1}[:n-3] == x_i[3:]  (a weight-3 joint).

Block i writes the passes e_i, tau e_i, ..., tau^{n-2} e_i, each pass being the
n rotations sigma^0..sigma^{n-1} of its entry, consecutive passes joined by the
weight-2 joint x -> tau(entry); blocks are joined by weight-3 joints.

Converse (elementary, no lemma): a perfect chain spells a superpermutation of
length exactly n + (N - HEX) + 2(HEX - m) + 3(m - 1) = n! + (n-1)! + (n-2)! + n - 3.
Forward (uses the project's general-n MASTER lemmas): a word of that length has
t = k + Z + H + B* = 0, which forces exactly this structure (see r173 report).

usage: perfect173.py n [node_limit]
"""
import sys, time, json
from itertools import permutations
from math import factorial

sys.setrecursionlimit(100000)


def sigma(s):
    return s[1:] + s[:1]


def tau(s):
    return s[1:-1] + s[:1] + s[-1:]


def hexrep(s):
    return min(s[i:] + s[:i] for i in range(len(s)))


def block(e, n):
    ents = [e]
    for _ in range(n - 2):
        ents.append(tau(ents[-1]))
    f = ents[-1]
    x = f[-1:] + f[:-1]                      # sigma^{n-1}(f)
    return ents, x


def spell(chain, n):
    """windows in order -> string, merging by maximal overlap; returns string."""
    wins = []
    for e in chain:
        ents, _x = block(e, n)
        for v in ents:
            w = v
            for _ in range(n):
                wins.append(w)
                w = sigma(w)
    s = wins[0]
    for a, b in zip(wins, wins[1:]):
        k = next(k for k in range(1, n + 1) if a[k:] == b[:n - k])
        s += b[n - k:]
    return s


def search(n, limit, first=None, find_all=False):
    m = factorial(n - 2)
    HEX = factorial(n - 1)
    alph = "".join(str(i + 1) for i in range(n))
    e1 = first or alph
    used = set()
    chain = []
    st = dict(nodes=0, found=[])

    def orbit_hexes(e):
        ents, x = block(e, n)
        hs = [hexrep(v) for v in ents]
        if len(set(hs)) != len(hs):
            return None, None
        return hs, x

    def rec(e):
        st["nodes"] += 1
        if st["nodes"] > limit:
            raise TimeoutError
        hs, x = orbit_hexes(e)
        if hs is None or any(h in used for h in hs):
            return False
        used.update(hs)
        chain.append(e)
        if len(chain) == m:
            assert len(used) == HEX
            st["found"].append(list(chain))
            done = not find_all
        else:
            done = False
            for p in permutations(x[:3]):
                if rec(x[3:] + "".join(p)):
                    done = True
                    break
        if not done:
            chain.pop()
            used.difference_update(hs)
        return done

    t0 = time.time()
    try:
        rec(e1)
        status = "EXHAUSTED" if not st["found"] or find_all else "FOUND"
    except TimeoutError:
        status = "NODE_LIMIT"
    return dict(n=n, m=m, status=status, nodes=st["nodes"], found=len(st["found"]),
                example=st["found"][0] if st["found"] else None,
                seconds=round(time.time() - t0, 2))


if __name__ == "__main__":
    n = int(sys.argv[1])
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 8
    r = search(n, limit)
    print(json.dumps({k: v for k, v in r.items() if k != "example"}))
    if r["example"]:
        s = spell(r["example"], n)
        print("spelled length", len(s), "CONST", factorial(n) + factorial(n - 1) + factorial(n - 2) + n - 3)
        print(s if len(s) < 200 else s[:200] + "...")
