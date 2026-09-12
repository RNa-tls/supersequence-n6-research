#!/usr/bin/env python3
"""Round 146 — CLEAN-ROOM computation of the word-level proof invariants.

Written to be able to DISAGREE with round 145.  It imports nothing from the
round-144/145 modules, keeps no integer ranking of permutations (every object is
a 6-character string or a dict keyed by one), derives hexagons and orbits as
canonical rotation strings, classifies joints by literal string construction,
and builds beta as a plain dict with brute-force cycle extraction.

From a literal covering word it computes

    P G O k S H D2 Qs K R_int c d g z Z B*

and tests

    (FO)      L = 844 + G + S + H                (n = 6)
    MASTER    L = 867 + k + Z + H + B*           (n = 6)

Usage:  python3 src/l6_cleanroom_146.py FILE [FILE ...]
        (gzip accepted; '#' comment lines and blanks skipped)
"""
from __future__ import annotations
import gzip, json, sys
from collections import Counter
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- string algebra
def sig(s):                                 # full rotation  (hexagon step)
    return s[1:] + s[0]


def tau(s):                                 # rotate all but the last (orbit step)
    return s[1:-1] + s[0] + s[-1]


def hexkey(s):
    x, best = s, s
    for _ in range(len(s) - 1):
        x = sig(x)
        if x < best:
            best = x
    return best


def orbkey(s):
    x, best = s, s
    for _ in range(len(s) - 2):
        x = tau(x)
        if x < best:
            best = x
    return best


def omega(a, b):
    n = len(a)
    for k in range(1, n):
        if a[k:] == b[:n - k]:
            return k
    return n


def hiddens(src, tgt, gap):
    """Permutation windows strictly inside the spelling src + tail(tgt, gap)."""
    n = len(src)
    raw = src + tgt[n - gap:]
    return [raw[o:o + n] for o in range(1, gap) if len(set(raw[o:o + n])) == n]


# ---------------------------------------------------------------- invariants
def invariants(W, n=6):
    fail = []
    N = factorial(n)
    # ---- first occurrences, straight off the string
    seen, sel, pos = set(), [], []
    for i in range(len(W) - n + 1):
        w = W[i:i + n]
        if len(set(w)) == n and w not in seen:
            seen.add(w)
            sel.append(w)
            pos.append(i)
    if len(sel) != N:
        return dict(ok=False, why=f"not a cover ({len(sel)}/{N})")
    gaps = [pos[j + 1] - pos[j] for j in range(N - 1)]
    if any(g < omega(sel[j], sel[j + 1]) for j, g in enumerate(gaps)):
        fail.append("a gap is below omega")
    fixed = all(g == omega(sel[j], sel[j + 1]) for j, g in enumerate(gaps)) \
        and pos[0] == 0 and pos[-1] + n == len(W)

    # ---- passes: a gap of 1 means the next window is sigma of this one
    for j, g in enumerate(gaps):
        if (g == 1) != (sel[j + 1] == sig(sel[j])):
            fail.append("gap 1 is not the sigma step")
    passes, entry_pos, run = [], [], [0]
    for j, g in enumerate(gaps):
        if g == 1:
            run.append(j + 1)
        else:
            passes.append(run)
            run = [j + 1]
    passes.append(run)
    P = len(passes)
    ent = [sel[r[0]] for r in passes]
    lens = [len(r) for r in passes]
    G = P - N // n
    if len(set(ent)) != P:
        fail.append("two passes share an entry")

    # ---- hexagons / orbits, as canonical strings
    hx = [hexkey(e) for e in ent]
    ob = [orbkey(e) for e in ent]
    byhex = Counter(hx)
    if len(byhex) != N // n:
        fail.append(f"hexagons carrying a pass = {len(byhex)} != {N // n}")
    if sum(v - 1 for v in byhex.values()) != G:
        fail.append("sum (m_h - 1) != G")
    for h, idxs in [(h, [i for i in range(P) if hx[i] == h]) for h in byhex]:
        arc = []
        for i in idxs:
            x = ent[i]
            for _ in range(lens[i]):
                arc.append(x)
                x = sig(x)
        if len(arc) != n or len(set(arc)) != n:
            fail.append("arcs of a hexagon do not partition it")
    O = len(set(ob))
    k = O - N // (n * (n - 1))

    # ---- nu, then beta = T . nu^{-1}, as dicts on entry strings
    idx_of = {e: i for i, e in enumerate(ent)}
    nu = []
    for i in range(P):
        x = ent[i]
        for _ in range(lens[i]):
            x = sig(x)
        if x not in idx_of:
            fail.append("nu target is not a pass entry")
            nu.append(i)
        else:
            nu.append(idx_of[x])
    if sorted(nu) != list(range(P)):
        fail.append("nu is not a permutation")

    # ---- joints: classify literally
    tgt_of, w_of, type_of, hid_of = {}, {}, {}, {}
    for j, g in enumerate(gaps):
        if g == 1:
            continue
        src = sel[j]
        p = nu[[i for i in range(P) if
                _last(ent[i], lens[i]) == src][0]] if False else None
        # the pass ending at sel[j]
        i = next(i for i in range(P) if _last(ent[i], lens[i]) == src)
        p = nu[i]
        if src != _end(ent[p]):
            fail.append("joint source != sigma^{-1}(v_nu(i))")
        t = sel[j + 1]
        tgt_of[p] = t
        w_of[p] = g
        hid_of[p] = hiddens(src, t, g)
        v = ent[p]
        if g == 2:
            type_of[p] = "E" if t == tau(v) else ("A" if t == sig(v) else "?w2")
        elif g == 3:
            if t == tau(tau(v)):
                type_of[p] = "120"
            elif t == sig(sig(v)):
                type_of[p] = "B"
            elif t == tau(sig(v)):
                type_of[p] = "C"
            elif t == sig(tau(v)):
                type_of[p] = "D"
            else:
                type_of[p] = "clean_w3"
        else:
            type_of[p] = "heavy"
        if type_of[p] == "?w2":
            fail.append("weight-2 joint outside the catalogue")
    if len(w_of) != P - 1:
        fail.append(f"joints = {len(w_of)} != P-1")
    exp_hidden = {"E": 0, "A": 1, "120": 0, "clean_w3": 0, "C": 1, "D": 1, "B": 2}
    for p, t in type_of.items():
        if t in exp_hidden and len(hid_of[p]) != exp_hidden[t]:
            fail.append(f"hidden count {len(hid_of[p])} != {exp_hidden[t]} for {t}")

    DUM = -1
    T = {i: i + 1 for i in range(P - 1)}
    T[P - 1] = DUM
    T[DUM] = 0
    alpha = {i: nu[i] for i in range(P)}
    alpha[DUM] = DUM
    ainv = {v: kk for kk, v in alpha.items()}
    beta = {x: T[ainv[x]] for x in list(range(P)) + [DUM]}
    if sorted(beta.values()) != sorted(beta.keys()):
        fail.append("beta is not a permutation")
    for i in range(P - 1):
        if beta[nu[i]] != i + 1:
            fail.append("beta(nu(i)) != i+1")

    comps, seen2 = [], set()
    for st in list(range(P)) + [DUM]:
        if st in seen2:
            continue
        cyc, x = [], st
        while x not in seen2:
            seen2.add(x)
            cyc.append(x)
            x = beta[x]
        comps.append(cyc)
    K = len(comps)
    R_int = sum(sum(v - 1 for v in Counter(hx[x] for x in cy if x != DUM).values())
                for cy in comps)
    if K + R_int > G + 1:
        fail.append(f"incidence violated: K={K} R_int={R_int} G={G}")
    if (K - (G + 1)) % 2:
        fail.append("parity violated")

    pure = [cy for cy in comps if DUM not in cy
            and all(type_of.get(x) == "E" for x in cy)]
    for cy in pure:
        if len(cy) != n - 1 or len({ob[x] for x in cy}) != 1:
            fail.append("a pure circuit is not a whole orbit")
        if any(ob[i] in {ob[x] for x in cy} for i in range(P) if i not in cy):
            fail.append("a pure circuit orbit occurs elsewhere")
    c = len(pure)
    d = K - 1 - c
    if (G + 1 - K) % 2:
        fail.append("G+1-K odd")
    g = (G + 1 - K) // 2
    if d < 0 or g < 0:
        fail.append(f"negative d/g: d={d} g={g}")

    S = sum(1 for w in w_of.values() if w >= 3)
    H = sum(max(w - 3, 0) for w in w_of.values())
    D2 = sum(1 for t in type_of.values() if t == "A")
    Qs = sum(1 for t in type_of.values() if t == "B")
    cleanE = sum(1 for t in type_of.values() if t == "E")
    if cleanE != P - 1 - S - D2:
        fail.append("clean E != P-1-S-D2")
    blocks = P - cleanE
    if blocks != S + 1 + D2:
        fail.append("blocks != S+1+D2")
    if D2 + Qs > R_int:
        fail.append(f"SAME-HEX violated: D2+Qs={D2 + Qs} > R_int={R_int}")
    if D2 + Qs > 2 * g:
        fail.append("D2+Qs > 2g")
    z = G - c
    Z = z - D2
    if Z < 0 or Qs > Z:
        fail.append(f"Z={Z} negative or Qs>Z")
    Bstar = blocks - (O - c)
    if Bstar < 0:
        fail.append("B* < 0")
    L_fo = n + (N - P) + 2 * (P - 1) + S + H
    L_master = 867 + k + Z + H + Bstar
    if L_fo != len(W):
        fail.append(f"(FO) gives {L_fo} not {len(W)}")
    if L_master != len(W):
        fail.append(f"MASTER gives {L_master} not {len(W)}")
    return dict(L=len(W), P=P, G=G, O=O, k=k, S=S, H=H, D2=D2, Qs=Qs, K=K,
                R_int=R_int, c=c, d=d, g=g, z=z, Z=Z, Bstar=Bstar,
                blocks=blocks, fixed_representative=fixed,
                FO=L_fo, MASTER=L_master, types=dict(Counter(type_of.values())),
                failures=fail[:6], ok=not fail)


def _end(v):
    return v[-1] + v[:-1]


def _last(entry, ln):
    x = entry
    for _ in range(ln - 1):
        x = sig(x)
    return x


# ---------------------------------------------------------------- driver
def words_from(path):
    op = gzip.open if str(path).endswith(".gz") else open
    with op(path, "rt") as fh:
        for line in fh:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if len(set(s)) == 6 and len(s) >= 800:
                yield s


if __name__ == "__main__":
    prof, bad, total, lens = Counter(), [], 0, Counter()
    for path in sys.argv[1:]:
        for w in words_from(path):
            r = invariants(w)
            total += 1
            if not r.get("ok"):
                bad.append((path, w[:24], r.get("failures") or r.get("why")))
                continue
            lens[r["L"]] += 1
            prof[json.dumps({x: r[x] for x in
                             ("L", "P", "G", "O", "k", "S", "H", "D2", "Qs", "K",
                              "R_int", "c", "d", "g", "Z", "Bstar")},
                            sort_keys=True)] += 1
    print(f"words={total}  failures={len(bad)}  lengths={dict(lens)}  "
          f"distinct invariant profiles={len(prof)}")
    for kk, v in prof.most_common(20):
        print(f"  x{v:<6} {kk}")
    for b in bad[:8]:
        print("  FAIL", b)
    out = dict(words=total, failures=len(bad), lengths=dict(lens),
               profiles={kk: v for kk, v in prof.items()},
               failure_examples=[list(map(str, b)) for b in bad[:20]])
    (ROOT / "outputs" / "rr_l6_cleanroom_146.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(1 if bad else 0)
