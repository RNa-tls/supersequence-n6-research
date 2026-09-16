#!/usr/bin/env python3
"""Round 156 -- INDEPENDENT reconstruction of the extraction theorem (H.extract).

Nothing in this file is imported from src/ or from any earlier round.  Every
object is rebuilt from the written definitions so that the audit does not
inherit a bug from the implementation it is auditing.

WHAT IS REBUILT
  omega, first-occurrence selection, passes, nu, alpha, T, beta,
  the joint catalogue types, hexagons, tau-orbits, the beta components,
  the pure/non-pure dichotomy (and NOTHING finer), the cut into chains,
  and every quantity Claims 1-5 talk about.

WHAT IS CHECKED
  C1  sum_i P_i          = P - (n-1) c
  C2  sum_i D_i          = (n-1) k - G + (n-1) sigma
  C3  blocks_i           = O_i + tok_i          (per chain)
      sum_i tok_i        = B* - sigma
  C4  sigma >= 0 ; one chain => sigma = 0 ; sigma <= B*
  C5  sum_i (within-chain hexagon repeats) <= R_int
      retained A/B edges <= that number
  CC  #chains = d + 1 + h - (openings that are heavy)  <=  d + 1 + h
  MF  the model feed: required / D_sum / b_sum / a / bb / e / h envelopes
  P2  P_i <= n!/n + a_i + bb_i + e_i          (per chain, the hex-simple bound)

The cut policy is a parameter, because the theorem must not depend on WHICH
non-E edge a cycle is opened at.
"""
from __future__ import annotations
import itertools, json, random, sys
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# --------------------------------------------------------------- word layer
def omega(a, b, n):
    for k in range(1, n):
        if a[k:] == b[:n - k]:
            return k
    return n


def perm_windows(W, n):
    return [(i, W[i:i + n]) for i in range(len(W) - n + 1)
            if len(set(W[i:i + n])) == n]


def selected(W, n):
    seen, out = set(), []
    for i, w in perm_windows(W, n):
        if w not in seen:
            seen.add(w)
            out.append((i, w))
    return out


def is_cover(W, n, alphabet=None):
    alpha = sorted(set(alphabet or W))
    need = {"".join(p) for p in itertools.permutations(alpha)}
    return {w for _, w in perm_windows(W, n)} == need


def sigma(w):
    return w[1:] + w[:1]


def tau(w, n):
    return w[1:n - 1] + w[0] + w[n - 1]


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


def phase_of(w, n):
    """index of w inside its tau-orbit, counted from orbrep."""
    x = orbrep(w, n)
    for j in range(n - 1):
        if x == w:
            return j
        x = tau(x, n)
    raise ValueError("w not in its own orbit")


def hidden_windows(src, tgt, gap, n):
    raw = src + tgt[n - gap:] if gap < n else src + tgt
    return [raw[o:o + n] for o in range(1, gap)
            if len(set(raw[o:o + n])) == n]


def jtype(v, tgt, gap, n):
    """Catalogue type of the shortest connector out of the FULL pass whose
    entry is v (source string sigma^{-1}(v)) landing on tgt with gap `gap`.

    Only the distinctions the extraction actually consumes are named:
      E   the clean tau step        (gap 2, tgt = tau(v))
      A   the dirty weight-2 step   (gap 2, tgt = sigma(v))
      B   the dirty weight-3 step   (gap 3, tgt = sigma^2(v))
      X   anything else of weight <= 3
      Hv  weight >= 4
    """
    if gap >= 4:
        return "Hv"
    if gap == 2:
        if tgt == tau(v, n):
            return "E"
        if tgt == sigma(v):
            return "A"
        return "X2"
    if gap == 3:
        if tgt == sigma(sigma(v)):
            return "B"
        return "X3"
    return "X?"


# ------------------------------------------------------------ pass layer
def structure(W, n):
    """passes / nu / beta / edge data, rebuilt from the definitions."""
    N = factorial(n)
    sel = selected(W, n)
    if len(sel) != N:
        raise ValueError("not a cover")
    gaps = [sel[j + 1][0] - sel[j][0] for j in range(N - 1)]
    fixed = all(gaps[j] == omega(sel[j][1], sel[j + 1][1], n)
                for j in range(N - 1)) and sel[0][0] == 0 and \
        sel[-1][0] + n == len(W)
    passes, s, l = [], 0, 1
    for j in range(N - 1):
        if gaps[j] == 1:
            l += 1
        else:
            passes.append((sel[s][1], l))
            s, l = j + 1, 1
    passes.append((sel[s][1], l))
    P = len(passes)
    entry = {v: i for i, (v, l) in enumerate(passes)}
    if len(entry) != P:
        raise ValueError("two passes share an entry")
    # nu: the next arc of the same hexagon
    nu = []
    for i, (v, l) in enumerate(passes):
        t = sig_pow(v, l)
        if t not in entry:
            raise ValueError("nu target is not a pass entry")
        nu.append(entry[t])
    if sorted(nu) != list(range(P)):
        raise ValueError("nu is not a permutation")
    dummy = P
    alpha = nu + [dummy]
    T = [i + 1 for i in range(P - 1)] + [dummy, 0]
    ainv = [0] * (P + 1)
    for x in range(P + 1):
        ainv[alpha[x]] = x
    beta = [T[ainv[x]] for x in range(P + 1)]
    if sorted(beta) != list(range(P + 1)):
        raise ValueError("beta is not a permutation")
    # joint data, keyed by the SPLICED source pass = nu(i)
    etype, eweight, ehidden = {}, {}, {}
    endpos = {}
    for i, (v, l) in enumerate(passes):
        endpos[sig_pow(v, l - 1)] = i
    for j in range(N - 1):
        if gaps[j] == 1:
            continue
        i = endpos[sel[j][1]]
        p = nu[i]
        # Lemma C: the joint source is end(v_{nu(i)})
        if sel[j][1] != passes[p][0][-1] + passes[p][0][:-1]:
            raise ValueError("Lemma C endpoint identity fails")
        etype[p] = jtype(passes[p][0], sel[j + 1][1], gaps[j], n)
        eweight[p] = gaps[j]
        ehidden[p] = len(hidden_windows(sel[j][1], sel[j + 1][1], gaps[j], n))
    if len(etype) != P - 1:
        raise ValueError("wrong number of joints")
    return dict(n=n, W=W, sel=sel, gaps=gaps, passes=passes, P=P, nu=nu,
                beta=beta, dummy=dummy, etype=etype, eweight=eweight,
                ehidden=ehidden, fixed=fixed,
                hexr=[hexrep(v) for v, l in passes],
                orbr=[orbrep(v, n) for v, l in passes],
                phase=[phase_of(v, n) for v, l in passes])


def components(beta):
    seen, comps = [False] * len(beta), []
    for i in range(len(beta)):
        if seen[i]:
            continue
        c, x = [], i
        while not seen[x]:
            seen[x] = True
            c.append(x)
            x = beta[x]
        comps.append(c)
    return comps


# ------------------------------------------------------- the extraction
POLICIES = ("light_first", "light_last", "any_first", "any_last",
            "heavy_first", "random", "prefer_AB", "avoid_AB")


def choose_opening(c, etype, eweight, policy, rng):
    cand = [x for x in c if etype.get(x) not in (None, "E")]
    if not cand:
        raise ValueError("a non-pure, non-dummy component has no non-E edge")
    light = [x for x in cand if eweight.get(x, 0) <= 3]
    heavy = [x for x in cand if eweight.get(x, 0) >= 4]
    ab = [x for x in cand if etype.get(x) in ("A", "B")]
    nab = [x for x in cand if etype.get(x) not in ("A", "B")]
    if policy == "light_first":
        return light[0] if light else cand[0]
    if policy == "light_last":
        return light[-1] if light else cand[-1]
    if policy == "any_first":
        return cand[0]
    if policy == "any_last":
        return cand[-1]
    if policy == "heavy_first":
        return heavy[0] if heavy else cand[0]
    if policy == "prefer_AB":
        return ab[0] if ab else cand[0]
    if policy == "avoid_AB":
        return nab[0] if nab else cand[0]
    if policy == "random":
        return rng.choice(cand)
    raise ValueError(policy)


def extract(st, keep_heavy=False, policy="light_first", rng=None,
            forced_openings=None):
    """The whole extraction, with the cut policy exposed."""
    n, P, beta, dummy = st["n"], st["P"], st["beta"], st["dummy"]
    etype, eweight = st["etype"], st["eweight"]
    hexr, orbr, passes = st["hexr"], st["orbr"], st["passes"]
    r = n - 1                                   # tau-orbit size
    HEX = factorial(n) // n
    rng = rng or random.Random(0)
    fails = []

    comps = components(beta)
    K = len(comps)
    G = P - HEX
    R_int = 0
    for c in comps:
        cnt = {}
        for x in c:
            if x == dummy:
                continue
            cnt[hexr[x]] = cnt.get(hexr[x], 0) + 1
        R_int += sum(v - 1 for v in cnt.values())

    # ---- the ONLY component classification used: pure clean-E vs not
    pure = [c for c in comps if dummy not in c
            and all(etype.get(x) == "E" for x in c)]
    cc = len(pure)
    # Lemma E, re-verified here (it is an input, not a claim of H.extract)
    for c in pure:
        orbs = {orbr[x] for x in c}
        if len(c) != r or len(orbs) != 1:
            fails.append(("LemmaE: pure circuit is not a whole orbit", len(c)))
        if {st["phase"][x] for x in c} != set(range(r)):
            fails.append("LemmaE: pure circuit misses a phase")
        for i in range(P):
            if i not in c and orbr[i] in orbs:
                fails.append("LemmaE: a pure orbit carries an outside pass")
    d = K - 1 - cc
    if (G + 1 - K) % 2:
        fails.append(("G+1-K odd", G, K))
    g = (G + 1 - K) // 2
    S = sum(1 for w in eweight.values() if w >= 3)
    Hh = sum(max(w - 3, 0) for w in eweight.values())
    h = sum(1 for w in eweight.values() if w >= 4)
    D2 = sum(1 for t in etype.values() if t == "A")
    Qs = sum(1 for t in etype.values() if t == "B")
    cleanE = sum(1 for t in etype.values() if t == "E")
    O = len(set(orbr))
    k = O - factorial(n) // (n * r)
    blocks = P - cleanE
    if blocks != S + 1 + D2:
        fails.append(("LemmaF", blocks, S + 1 + D2))
    Bstar = blocks - (O - cc)
    z = G - cc
    Z = z - D2

    # ---- cut into chains ------------------------------------------------
    purevs = {x for c in pure for x in c}
    openings = []
    for idx, c in enumerate(comps):
        if dummy in c or c in pure:
            continue
        if forced_openings is not None:
            openings.append(forced_openings[len(openings)])
        else:
            openings.append(choose_opening(c, etype, eweight, policy, rng))
    if len(openings) != d:
        fails.append(("number of openings != d", len(openings), d))
    cut = set(openings)
    heavy_cut = set()
    if not keep_heavy:
        heavy_cut = {x for x, w in eweight.items() if w >= 4}
        cut |= heavy_cut
    shared = len(set(openings) & heavy_cut)

    succ = {}
    for x in range(P):
        if x in purevs or x in cut:
            continue
        y = beta[x]
        if y != dummy and y not in purevs:
            succ[x] = y
    indeg = {}
    for y in succ.values():
        indeg[y] = indeg.get(y, 0) + 1
    starts = [x for x in range(P) if x not in purevs and not indeg.get(x)]
    chains, used = [], set()
    for s0 in starts:
        ch, x = [], s0
        while True:
            ch.append(x)
            if x in used:
                fails.append("chain revisits a pass")
                break
            used.add(x)
            if x not in succ:
                break
            x = succ[x]
        chains.append(ch)
    if used != set(range(P)) - purevs:
        fails.append(("chains do not partition the non-circuit passes",
                      len(used), P - len(purevs)))

    # every chain must sit inside ONE beta component
    compof = {}
    for i, c in enumerate(comps):
        for x in c:
            compof[x] = i
    for ch in chains:
        if len({compof[x] for x in ch}) != 1:
            fails.append("a chain spans two beta components")

    # ---- Claim 1 ---------------------------------------------------------
    sumP = sum(len(c) for c in chains)
    if sumP != P - r * cc:
        fails.append(("C1", sumP, P - r * cc))

    # ---- Claim 2 ---------------------------------------------------------
    sumO = sum(len({orbr[x] for x in c}) for c in chains)
    sig = sumO - (O - cc)
    sumD = r * sumO - sumP
    if sumD != r * k - G + r * sig:
        fails.append(("C2", sumD, r * k - G + r * sig))

    # ---- Claim 4 ---------------------------------------------------------
    if sig < 0:
        fails.append(("C4 sigma<0", sig))
    if len(chains) == 1 and sig != 0:
        fails.append(("C4 one chain but sigma!=0", sig))

    # ---- Claim 3 / 5 and the per-chain model feed -------------------------
    toktot = blocktot = hexrep_total = 0
    a_tot = bb_tot = e_tot = 0
    per = []
    for ch in chains:
        pos = {x: i for i, x in enumerate(ch)}
        Oi = len({orbr[x] for x in ch})
        opened, seenh = {orbr[ch[0]]}, {hexr[ch[0]]}
        toki, blocksi, repi = 0, 1, 0
        ai = bbi = ei = hvi = 0
        newo = 0
        for x, y in zip(ch, ch[1:]):
            t = etype.get(x)
            if t != "E":
                blocksi += 1
            if orbr[y] in opened:
                if t != "E":
                    toki += 1
            else:
                if t == "E":
                    fails.append("a clean E edge opened a new orbit")
                newo += 1
            opened.add(orbr[y])
            if hexr[y] in seenh:
                repi += 1
                if t == "A":
                    ai += 1
                elif t == "B":
                    bbi += 1
                else:
                    ei += 1
            else:
                if t in ("A", "B"):
                    fails.append(("a retained A/B edge is not a hexagon "
                                  "repeat", t))
            seenh.add(hexr[y])
            if eweight.get(x, 0) >= 4:
                hvi += 1
        if blocksi != Oi + toki:
            fails.append(("C3 per chain", blocksi, Oi, toki))
        if newo != Oi - 1:
            fails.append(("orbit opening count", newo, Oi - 1))
        # (P2): a chain has at most HEX distinct hexagons
        if len(ch) > HEX + ai + bbi + ei:
            fails.append(("P2 per chain", len(ch), HEX, ai, bbi, ei))
        if len(ch) - len({hexr[x] for x in ch}) != repi:
            fails.append("repeat count != ports - distinct hexagons")
        toktot += toki
        blocktot += blocksi
        hexrep_total += repi
        a_tot += ai
        bb_tot += bbi
        e_tot += ei
        per.append(dict(P=len(ch), O=Oi, D=r * Oi - len(ch), tok=toki,
                        blocks=blocksi, rep=repi, a=ai, bb=bbi, e=ei, hv=hvi))
    if blocktot != blocks:
        fails.append(("blocks do not add up", blocktot, blocks))
    if toktot != Bstar - sig:
        fails.append(("C3 sum", toktot, Bstar - sig))
    if sig > Bstar:
        fails.append(("sigma > B*", sig, Bstar))

    # ---- Claim 5 ---------------------------------------------------------
    if hexrep_total > R_int:
        fails.append(("C5", hexrep_total, R_int))
    retained_AB = sum(1 for x in range(P) if x not in purevs and x not in cut
                      and etype.get(x) in ("A", "B"))
    if retained_AB != a_tot + bb_tot:
        fails.append(("retained A/B mismatch", retained_AB, a_tot + bb_tot))
    if retained_AB > hexrep_total:
        fails.append(("retained A/B > hex repeats", retained_AB, hexrep_total))

    # ---- chain count -----------------------------------------------------
    expect = d + 1 + (0 if keep_heavy else h)
    if len(chains) != expect - shared:
        fails.append(("chain count", len(chains), expect, shared))
    if len(chains) > expect:
        fails.append(("chain count exceeds d+1+h", len(chains), expect))

    # ---- the model feed --------------------------------------------------
    required = HEX + G - r * cc
    D_sum = r * k - G + r * sig
    b_sum = Bstar - sig
    mf_fail = []
    if sumP != required:
        mf_fail.append(("required", sumP, required))
    if sum(p["D"] for p in per) != D_sum:
        mf_fail.append("D_sum")
    if sum(p["tok"] for p in per) != b_sum:
        mf_fail.append("b_sum")
    if a_tot > D2:
        mf_fail.append(("a>D2", a_tot, D2))
    if bb_tot > Qs:
        mf_fail.append(("bb>Qs", bb_tot, Qs))
    if e_tot > max(0, Z - Qs):
        mf_fail.append(("e>Z-Qs", e_tot, Z, Qs))
    if a_tot + bb_tot + e_tot > 2 * g:
        mf_fail.append(("a+bb+e>2g", a_tot + bb_tot + e_tot, 2 * g))
    if a_tot + bb_tot + e_tot > R_int:
        mf_fail.append(("a+bb+e>R_int", a_tot + bb_tot + e_tot, R_int))
    if not keep_heavy and sum(p["hv"] for p in per) != 0:
        mf_fail.append("a heavy edge survived the split model")
    if keep_heavy and sum(p["hv"] for p in per) > Hh:
        mf_fail.append("heavy joints exceed H")
    if Z < 0:
        mf_fail.append(("Z<0", Z))
    if D2 > 2 * g:
        mf_fail.append(("D2>2g", D2, 2 * g))
    if Qs > Z:
        mf_fail.append(("Qs>Z", Qs, Z))
    if D2 + Qs > R_int:
        mf_fail.append(("SAME-HEX D2+Qs>R_int", D2, Qs, R_int))
    # the inequalities the ROW ENUMERATION relies on, checked on the real object
    if G > r * k:
        mf_fail.append(("G>(n-1)k", G, r * k))
    if K + R_int > G + 1:
        mf_fail.append(("incidence K+R_int>G+1", K, R_int, G))
    if h > Hh or (h == 0) != (Hh == 0):
        mf_fail.append(("h vs H", h, Hh))
    if Bstar < 0 or k < 0 or Z < 0 or d < 0 or g < 0 or cc < 0:
        mf_fail.append(("a MASTER-142 term is negative", k, Z, Hh, Bstar))
    if Qs > min(Z, 2 * g - D2):
        mf_fail.append(("Qs>min(Z,2g-D2)", Qs, Z, 2 * g - D2))
    if G != 2 * g + cc + d:
        mf_fail.append(("G != 2g+c+d", G, g, cc, d))

    # length identities
    L_fo = n + (factorial(n) - P) + 2 * (P - 1) + S + Hh
    master = 867 + k + Z + Hh + Bstar if n == 6 else None
    return dict(n=n, length=len(st["W"]), fixed=st["fixed"], P=P, G=G, O=O,
                k=k, S=S, H=Hh, h=h, D2=D2, Qs=Qs, K=K, R_int=R_int, c=cc,
                d=d, g=g, z=z, Z=Z, Bstar=Bstar, blocks=blocks,
                keep_heavy=keep_heavy, policy=policy,
                chains=len(chains), chains_max=expect, shared=shared,
                sigma=sig, sum_P=sumP, sum_D=sumD, sum_tok=toktot,
                required=required, D_sum=D_sum, b_sum=b_sum,
                a=a_tot, bb=bb_tot, e=e_tot, hex_repeats=hexrep_total,
                retained_AB=retained_AB, chain_sizes=sorted(len(c) for c in chains),
                FO_length=L_fo, FO_holds=(L_fo == len(st["W"])),
                MASTER=master, MASTER_holds=(master == len(st["W"]))
                if master is not None else None,
                per_chain=per, failures=fails + mf_fail, ok=not (fails or mf_fail))
