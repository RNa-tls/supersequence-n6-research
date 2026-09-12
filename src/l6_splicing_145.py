#!/usr/bin/env python3
"""Round 145 — SUCCESSOR SPLICING, proved here and verified on real covers.

Round 142 B4 asserts this; the module proves it and then checks every clause
literally on actual covering words, including the length-872 witness at n = 6.

-------------------------------------------------------------------------------
SETTING.  Let W be a FIXED representative (src/l6_fixed_representative_145.py):
a cover whose selected connectors are all spelled at maximum overlap.  Its
selected windows are q_1, ..., q_N (N = n!) in chronological order.  A PASS is a
maximal run of consecutive selected windows whose gaps are 1; since
omega(a, b) = 1 exactly when b = sigma(a), a pass is an ARC of one rotation
hexagon: pass i is (v_i, l_i) = (v_i, sigma v_i, ..., sigma^{l_i - 1} v_i).
Let P be the number of passes and m_h the number of passes inside hexagon h.

LEMMA A (the arcs of a hexagon partition it).  Each of the n! windows is
selected exactly once, and a window of hexagon h can only belong to a pass of
h, so the arcs of h are disjoint and cover its n elements.  Hence
sum_h m_h = P and, writing G = P - n!/n,  sum_h (m_h - 1) = G.

LEMMA B (nu is a permutation whose cycles are the hexagons).  By Lemma A the
element sigma^{l_i}(v_i) is the first element of the arc of h following pass i,
so nu(i) := that pass is well defined; inside hexagon h it is the cyclic
"next arc" map, a single cycle of length m_h.  So nu is a permutation of the
passes, c(nu) = n!/n, and the cycle lengths are the m_h.

LEMMA C (the joint source is the FULL-pass endpoint of nu(i)).  The last window
of pass i is sigma^{l_i - 1}(v_i) = sigma^{-1}(sigma^{l_i}(v_i))
= sigma^{-1}(v_{nu(i)}) = end(v_{nu(i)}).
So the joint i -> i+1 leaves the word position of end(v_{nu(i)}).  Reassigning
that joint to the pair (nu(i), i+1) therefore changes NOTHING about it: same
source string, same target string, same gap, same spelling, same hidden
windows.  In particular the weight w_i, and hence S, H and the dirty types, are
untouched, and every reassigned edge is a SHORTEST connector out of a FULL pass
endpoint -- i.e. it lies in the finite catalogue of connectors out of
sigma^{-1}(v).

LEMMA D (beta is a permutation, and the incidence bound applies).  On the set
{1..P} + {*} put alpha = nu extended by alpha(*) = *, and let T be the
(P+1)-cycle T(i) = i+1, T(P) = *, T(*) = 1.  Then beta := T alpha^{-1} is a
permutation and beta(nu(i)) = i+1, so the edges of beta are exactly the
reassigned joints (plus the two dummy edges).  We have
c(alpha) = n!/n + 1 and c(T) = 1, so the genus inequality proved in
src/l6_incidence_144.py gives, with K = c(beta) and R_int the within-component
duplicate-hexagon excess,

        K + R_int <= G + 1,     K = G + 1  (mod 2).

LEMMA E (pure clean-E circuits are whole orbits).  A clean E edge sends the pass
entry v to tau(v), which is in the same orbit with the phase advanced by exactly
one.  So a beta-cycle all of whose edges are clean E edges keeps one orbit, and
if it has length m its total phase advance is m; returning to its starting pass
forces m = 0 (mod n-1), i.e. (n-1) | m.  Its m passes have DISTINCT entries
(pass entries are distinct selected windows) inside an orbit of only n-1
elements, so m <= n-1.  Hence m = n-1 exactly, the cycle's entries are ALL n-1
elements of the orbit, and no other pass can lie in that orbit -- a further pass
there would need an n-th distinct entry.

LEMMA F (block count).  There are P - 1 joints, S of them paid (w >= 3), and D2
of the free ones are the dirty weight-2 type A.  So the clean E edges number
P - 1 - S - D2 and cutting every other edge leaves S + 1 + D2 maximal clean-E
blocks.  Deleting a pure circuit removes n-1 vertices and n-1 clean E edges and
so leaves the block count unchanged.

Together with sum_j O_j = (O - c) + s and blocks_j = O_j + b_j this yields
B* = S + 1 + D2 - O + c and, substituted into (FO), MASTER-142.
-------------------------------------------------------------------------------

Everything above is checked below on real words: Lemma A (arc partition),
Lemma B (nu a permutation, cycles = hexagons, lengths = m_h), Lemma C (the
endpoint identity and the invariance of every weight and tail), Lemma D
(beta a permutation, the bound and the parity with the REAL R_int), Lemma E,
Lemma F, and then the full chain down to MASTER-142 reproducing the actual
length of the word.
"""
from __future__ import annotations
import itertools, json, sys
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from l6_fixed_representative_145 import (omega, selected, is_cover,      # noqa
                                         fixed_representative)


def sigma(w):
    return w[1:] + w[:1]


def tau(w, n):
    return w[1:n - 1] + w[0] + w[n - 1]


def end(w):
    return w[-1] + w[:-1]                       # sigma^{-1}


def sig_pow(w, j):
    for _ in range(j % len(w)):
        w = sigma(w)
    return w


def hexrep(w):
    return min(sig_pow(w, j) for j in range(len(w)))


def orbrep(w, n):
    x, best = w, w
    for _ in range(n - 1):
        x = tau(x, n)
        best = min(best, x)
    return best


def hidden(src, tgt, gap, n):
    raw = src + tgt[n - gap:]
    return [raw[o:o + n] for o in range(1, gap)
            if len(set(raw[o:o + n])) == n]


def classify(v, tgt, gap, n):
    """The catalogue type of the shortest connector end(v) -> tgt."""
    if gap == 2:
        return "E" if tgt == tau(v, n) else ("A" if tgt == sigma(v) else "?w2")
    if gap == 3:
        if tgt == tau(tau(v, n), n):
            return "120"
        if tgt == sigma(sigma(v)):
            return "B"
        if tgt == tau(sigma(v), n):
            return "C"
        if tgt == sigma(tau(v, n)):
            return "D"
        return "clean_w3"                        # the 201 / 210 pair
    return "heavy"


def analyse(W, n, verbose=False):
    """Run the entire splicing construction literally and check every clause."""
    fails = []
    N = factorial(n)
    sel = selected(W, n)
    assert len(sel) == N
    gaps = [sel[j + 1][0] - sel[j][0] for j in range(N - 1)]
    for j in range(N - 1):                                  # fixed representative
        if gaps[j] != omega(sel[j][1], sel[j + 1][1], n):
            fails.append(("not a fixed representative", j))

    # ---- passes
    passes = []                                             # (entry, length)
    cur_start, cur_len = 0, 1
    for j in range(N - 1):
        if gaps[j] == 1:
            cur_len += 1
        else:
            passes.append((sel[cur_start][1], cur_len))
            cur_start, cur_len = j + 1, 1
    passes.append((sel[cur_start][1], cur_len))
    P = len(passes)
    G = P - N // n

    # ---- Lemma A: the arcs of each hexagon partition it
    byhex = {}
    for i, (v, l) in enumerate(passes):
        byhex.setdefault(hexrep(v), []).append(i)
    if len(byhex) != N // n:
        fails.append(("some hexagon carries no pass", len(byhex)))
    if sum(len(x) - 1 for x in byhex.values()) != G:
        fails.append("sum (m_h - 1) != G"),
    for h, idxs in byhex.items():
        cover = []
        for i in idxs:
            v, l = passes[i]
            cover += [sig_pow(v, t) for t in range(l)]
        if len(cover) != n or len(set(cover)) != n:
            fails.append(("arcs of a hexagon do not partition it", h))

    # ---- Lemma B: nu
    entry_of = {v: i for i, (v, l) in enumerate(passes)}
    if len(entry_of) != P:
        fails.append("two passes share an entry")
    nu = []
    for i, (v, l) in enumerate(passes):
        t = sig_pow(v, l)
        if t not in entry_of:
            fails.append(("nu target is not a pass entry", i))
            nu.append(i)
        else:
            nu.append(entry_of[t])
    if sorted(nu) != list(range(P)):
        fails.append("nu is not a permutation")
    # cycles of nu are the hexagons, with lengths m_h
    seen, nucyc = [False] * P, []
    for i in range(P):
        if seen[i]:
            continue
        c, x = [], i
        while not seen[x]:
            seen[x] = True
            c.append(x)
            x = nu[x]
        nucyc.append(c)
    if sorted(len(c) for c in nucyc) != sorted(len(v) for v in byhex.values()):
        fails.append("cycle lengths of nu are not the m_h")
    for c in nucyc:
        if len({hexrep(passes[i][0]) for i in c}) != 1:
            fails.append("a nu-cycle spans two hexagons")

    # ---- Lemma C: the endpoint identity, and joint data are unchanged
    joints = []                                  # (source pass after splicing, target pass, weight, type)
    for j in range(N - 1):
        if gaps[j] == 1:
            continue
        # this gap is the joint leaving the pass that ends at sel[j]
        src_word = sel[j][1]
        tgt_word = sel[j + 1][1]
        i = None                                  # the pass ending at sel[j]
        for idx, (v, l) in enumerate(passes):
            if sig_pow(v, l - 1) == src_word:
                i = idx
                break
        if i is None:
            fails.append(("no pass ends at a joint source", j))
            continue
        if src_word != end(passes[nu[i]][0]):
            fails.append(("Lemma C fails: joint source != end(v_nu(i))", j))
        w = gaps[j]
        ty = classify(passes[nu[i]][0], tgt_word, w, n)
        if ty == "?w2":
            fails.append(("weight-2 joint outside the catalogue", j))
        hid = hidden(src_word, tgt_word, w, n)
        joints.append(dict(src_pass=nu[i], tgt_pass=entry_of.get(tgt_word),
                           weight=w, type=ty, hidden=len(hid)))
    if len(joints) != P - 1:
        fails.append(("wrong number of inter-pass joints", len(joints), P - 1))
    # hidden-window counts must match the catalogue
    exp = {"E": 0, "A": 1, "120": 0, "clean_w3": 0, "C": 1, "D": 1, "B": 2}
    for jt in joints:
        if jt["type"] in exp and jt["hidden"] != exp[jt["type"]]:
            fails.append(("hidden count disagrees with the type", jt))

    # ---- Lemma D: beta
    dummy = P
    alpha = nu + [dummy]
    T = [i + 1 for i in range(P - 1)] + [dummy, 0]
    ainv = [0] * (P + 1)
    for x in range(P + 1):
        ainv[alpha[x]] = x
    beta = [T[ainv[x]] for x in range(P + 1)]
    if sorted(beta) != list(range(P + 1)):
        fails.append("beta is not a permutation")
    for i in range(P - 1):
        if beta[nu[i]] != i + 1:
            fails.append(("beta(nu(i)) != i+1", i))
    seen, comps = [False] * (P + 1), []
    for i in range(P + 1):
        if seen[i]:
            continue
        c, x = [], i
        while not seen[x]:
            seen[x] = True
            c.append(x)
            x = beta[x]
        comps.append(c)
    K = len(comps)
    R_int = 0
    for c in comps:
        cnt = {}
        for x in c:
            if x == dummy:
                continue
            hx = hexrep(passes[x][0])
            cnt[hx] = cnt.get(hx, 0) + 1
        R_int += sum(v - 1 for v in cnt.values())
    if K + R_int > G + 1:
        fails.append(("K + R_int > G + 1", K, R_int, G))
    if (K - (G + 1)) % 2:
        fails.append(("parity K != G+1 mod 2", K, G))

    # ---- Lemma E: pure clean-E circuits
    etype = {}
    for jt in joints:
        etype[jt["src_pass"]] = jt["type"]
    pure = []
    for c in comps:
        if dummy in c:
            continue
        if all(etype.get(x) == "E" for x in c):
            pure.append(c)
            orbs = {orbrep(passes[x][0], n) for x in c}
            if len(c) != n - 1 or len(orbs) != 1:
                fails.append(("a pure circuit is not a whole orbit", len(c)))
            ports = {passes[x][0] for x in c}
            allports = set()
            x0 = passes[c[0]][0]
            y = x0
            for _ in range(n - 1):
                allports.add(y)
                y = tau(y, n)
            if ports != allports:
                fails.append("a pure circuit misses a port of its orbit")
            for i, (v, l) in enumerate(passes):
                if i not in c and orbrep(v, n) in orbs:
                    fails.append("a pure circuit orbit occurs elsewhere")
    cc = len(pure)
    d = K - 1 - cc
    if (G + 1 - K) % 2:
        fails.append("G+1-K is odd")
    g = (G + 1 - K) // 2
    if d < 0 or g < 0:
        fails.append(("negative d or g", d, g))

    # ---- Lemma F and the chain to MASTER-142
    S = sum(1 for jt in joints if jt["weight"] >= 3)
    Hh = sum(max(jt["weight"] - 3, 0) for jt in joints)
    D2 = sum(1 for jt in joints if jt["type"] == "A")
    Qs = sum(1 for jt in joints if jt["type"] == "B")
    cleanE = sum(1 for jt in joints if jt["type"] == "E")
    if cleanE != P - 1 - S - D2:
        fails.append(("clean E count != P-1-S-D2", cleanE, P - 1 - S - D2))
    blocks = P - cleanE
    if blocks != S + 1 + D2:
        fails.append(("block count != S+1+D2", blocks, S + 1 + D2))
    O = len({orbrep(v, n) for v, l in passes})
    k = O - N // (n * (n - 1))
    z = G - cc
    Z = z - D2
    Bstar = blocks - (O - cc)
    L_fo = (N + n - N // n) + G + S + Hh - 1 + 1   # see below for n=6: 844+...
    L_fo = n + (N - P) + 2 * (P - 1) + S + Hh
    ok_fo = (L_fo == len(W))
    base = 867 if n == 6 else None
    master = None
    if base is not None:
        master = base + k + Z + Hh + Bstar
    return dict(
        n=n, length=len(W), P=P, G=G, O=O, k=k, S=S, H=Hh, D2=D2, Qs=Qs,
        K=K, R_int=R_int, c=cc, d=d, g=g, z=z, Z=Z, Bstar=Bstar,
        blocks=blocks, clean_E=cleanE, pure_circuits=cc,
        FO_length=L_fo, FO_holds=ok_fo,
        MASTER=master, MASTER_holds=(master == len(W)) if master else None,
        same_hex_bound=dict(D2_plus_Qs=D2 + Qs, R_int=R_int, two_g=2 * g,
                            holds=(D2 + Qs <= R_int <= 2 * g)),
        incidence=dict(K_plus_R=K + R_int, G_plus_1=G + 1, holds=K + R_int <= G + 1),
        types={t: sum(1 for jt in joints if jt["type"] == t)
               for t in sorted({jt["type"] for jt in joints})},
        failures=fails[:8], nfail=len(fails), ok=not fails)


def run():
    out = {}
    # n = 4
    W4 = "123412314231243121342132413214321"
    out["n4_optimum"] = analyse(W4, 4)
    # n = 5 minima
    p5 = ROOT / "outputs" / "rr_nr6_n5_minima_142.json"
    if p5.exists():
        raw = json.loads(p5.read_text())
        words = sorted({e["word"] for e in raw if isinstance(e, dict) and "word" in e})
        res5 = [analyse(w, 5) for w in words]
        out["n5_minima"] = dict(count=len(res5),
                               all_ok=all(r["ok"] and r["FO_holds"] for r in res5),
                               first=res5[0] if res5 else None)
    # n = 6 witness
    p6 = ROOT / "data" / "verified_872_witness.txt"
    if p6.exists():
        W6 = p6.read_text().strip()
        out["n6_witness_872"] = analyse(W6, 6)
    out["all_ok"] = all(v.get("ok", True) and v.get("all_ok", True)
                        for v in out.values() if isinstance(v, dict))
    return out


if __name__ == "__main__":
    r = run()
    (ROOT / "outputs" / "rr_l6_splicing_145.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=1))
    for k, v in r.items():
        if isinstance(v, dict):
            print(k, json.dumps({x: v[x] for x in v
                                 if x not in ("failures", "first")},
                                ensure_ascii=False))
            if v.get("failures"):
                print("   FAILURES:", json.dumps(v["failures"], ensure_ascii=False)[:600])
        else:
            print(k, v)
