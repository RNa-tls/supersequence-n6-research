#!/usr/bin/env python3
"""Round 145 — EXTRACTION, derived without going through the piece model.

Round 142 defines  B* = sum_j b_j + s  over the hex-simple PIECES.  The capacity
models of round 144 price CHAINS (whole beta components, with or without the
heavy joints cut), so the budgets have to be established for chains directly.
That is done here, and then checked literally on real covering words.

-------------------------------------------------------------------------------
DEFINITIONS (decomposition-free).  In the spliced structure let blocks be the
number of maximal clean-E paths after deleting the c pure clean-E circuits.
Lemma F of src/l6_splicing_145.py gives blocks = S + 1 + D2, and we DEFINE

        B* := blocks - (O - c) = S + 1 + D2 - O + c,

which is what MASTER-142 substitutes, so this definition is the operative one.

THE CHAINS.  Delete the c pure circuits.  The remaining K - c = d + 1 beta
components are cycles; open each at one non-E edge (a nonpure cycle has one by
definition).  Then cut the h heavy joints.  No clean E edge is ever cut, so the
result is d + 1 + h paths -- the CHAINS -- and every clean-E block lies inside
exactly one of them.  Keeping the heavy joints instead gives d + 1 chains.

For chain i write P_i for its ports, O_i for its distinct orbits,
D_i = 5 O_i - P_i, and tok_i for the number of its edges that are NOT clean E
and land in an orbit chain i has already opened.  Put sigma := sum_i O_i - (O - c).

CLAIM 1.  sum_i P_i = P - (n-1) c.
  Each deleted circuit uses all n-1 ports of its orbit; every other pass is in
  exactly one chain.

CLAIM 2.  sum_i D_i = (n-1) k - G + (n-1) sigma  (for n = 6: 5k - G + 5 sigma).
  sum_i D_i = 5 sum_i O_i - sum_i P_i = 5(O - c + sigma) - (120 + G - 5c)
            = 5k - G + 5 sigma, using O = 24 + k and P = 120 + G.

CLAIM 3.  blocks_i = O_i + tok_i, hence  sum_i tok_i = B* - sigma.
  Inside chain i a clean E edge keeps the orbit AND the block; every other edge
  starts a new block.  So blocks_i = P_i - (clean E edges of chain i).  The
  edges that keep the orbit are the clean E ones and the intra-orbit paid ones
  (E^2, and any heavy joint that happens to stay in the orbit), so the number of
  maximal same-orbit stretches is runs_i = O_i + e_i where e_i counts the
  cross-orbit edges landing in an already opened orbit.  Writing x_i for the
  intra-orbit non-E edges, blocks_i = runs_i + x_i = O_i + e_i + x_i, and
  e_i + x_i is exactly tok_i.  Summing and using blocks = sum_i blocks_i,

        blocks = (O - c + sigma) + sum_i tok_i,   so   sum_i tok_i = B* - sigma.

CLAIM 4.  sigma >= 0, and sigma = 0 when there is a single chain.
  The chains' orbit sets union to the O - c orbits outside the pure circuits, so
  sum_i O_i >= O - c; with one chain that union IS its own orbit set.

CLAIM 5.  Within a chain, the number of ports whose hexagon already occurred
  earlier in that chain, summed over chains, is at most R_int; each retained
  type A or B edge accounts for one of them, since its target's hexagon equals
  its source's and the source is its immediate predecessor.

Claims 1-5 are exactly the budgets the round-144 capacity models consume.
-------------------------------------------------------------------------------
"""
from __future__ import annotations
import json, random, sys
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import l6_splicing_145 as SP                                        # noqa: E402
import l6_same_hex_145 as SH                                        # noqa: E402
from l6_fixed_representative_145 import (selected, is_cover,          # noqa
                                         fixed_representative)


def build(W, n):
    """Rebuild passes, nu, beta and the joint types; then extract the chains."""
    N = factorial(n)
    sel = selected(W, n)
    gaps = [sel[j + 1][0] - sel[j][0] for j in range(N - 1)]
    passes, cur_start, cur_len = [], 0, 1
    for j in range(N - 1):
        if gaps[j] == 1:
            cur_len += 1
        else:
            passes.append((sel[cur_start][1], cur_len))
            cur_start, cur_len = j + 1, 1
    passes.append((sel[cur_start][1], cur_len))
    P = len(passes)
    entry = {v: i for i, (v, l) in enumerate(passes)}
    nu = [entry[SP.sig_pow(v, l)] for v, l in passes]
    dummy = P
    alpha = nu + [dummy]
    T = [i + 1 for i in range(P - 1)] + [dummy, 0]
    ainv = [0] * (P + 1)
    for x in range(P + 1):
        ainv[alpha[x]] = x
    beta = [T[ainv[x]] for x in range(P + 1)]
    # edge data keyed by source pass
    etype, eweight = {}, {}
    for j in range(N - 1):
        if gaps[j] == 1:
            continue
        src = sel[j][1]
        i = next(idx for idx, (v, l) in enumerate(passes)
                 if SP.sig_pow(v, l - 1) == src)
        p = nu[i]
        etype[p] = SP.classify(passes[p][0], sel[j + 1][1], gaps[j], n)
        eweight[p] = gaps[j]
    return dict(passes=passes, P=P, nu=nu, beta=beta, dummy=dummy,
                etype=etype, eweight=eweight)


def extract(W, n, keep_heavy=False):
    b = build(W, n)
    passes, P, beta, dummy = b["passes"], b["P"], b["beta"], b["dummy"]
    etype, eweight = b["etype"], b["eweight"]
    hexr = [SP.hexrep(v) for v, l in passes]
    orbr = [SP.orbrep(v, n) for v, l in passes]
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
    G = P - factorial(n) // n
    R_int = 0
    for c in comps:
        cnt = {}
        for x in c:
            if x == dummy:
                continue
            cnt[hexr[x]] = cnt.get(hexr[x], 0) + 1
        R_int += sum(v - 1 for v in cnt.values())
    pure = [c for c in comps if dummy not in c
            and all(etype.get(x) == "E" for x in c)]
    cc = len(pure)
    d = K - 1 - cc
    g = (G + 1 - K) // 2
    S = sum(1 for w in eweight.values() if w >= 3)
    Hh = sum(max(w - 3, 0) for w in eweight.values())
    D2 = sum(1 for t in etype.values() if t == "A")
    Qs = sum(1 for t in etype.values() if t == "B")
    O = len(set(orbr))
    blocks = P - sum(1 for t in etype.values() if t == "E")
    Bstar = blocks - (O - cc)

    # ---- cut into chains
    purevs = {x for c in pure for x in c}
    cut, heavy_openings = set(), []                 # source passes whose edge is cut
    for c in comps:
        if dummy in c or c in pure:
            continue
        # open a nonpure cycle at one non-E edge, preferring a LIGHT one so the
        # opening does not double as a heavy cut
        light = [x for x in c if etype.get(x) not in (None, "E")
                 and eweight.get(x, 0) <= 3]
        opened = light[0] if light else next(x for x in c
                                            if etype.get(x) not in (None, "E"))
        if not light:
            heavy_openings.append(opened)
        cut.add(opened)
    if not keep_heavy:
        for x, w in eweight.items():
            if w >= 4:
                cut.add(x)
    h = sum(1 for w in eweight.values() if w >= 4)
    # walk the chains
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
    starts = [x for x in range(P) if x not in purevs and indeg.get(x, 0) == 0]
    chains, used = [], set()
    for s in starts:
        ch, x = [], s
        while True:
            ch.append(x)
            used.add(x)
            if x not in succ:
                break
            x = succ[x]
        chains.append(ch)
    fails = []
    if used != set(range(P)) - purevs:
        fails.append("chains do not partition the non-circuit passes")
    # the models use d+1+h (resp. d+1) chains, which is the MAXIMUM: when a
    # cycle has to be opened at a heavy edge the two cuts coincide and there are
    # fewer chains.  More chains would be unsound, fewer is only generous.
    expect = d + 1 + (0 if keep_heavy else h)
    shared = 0 if keep_heavy else len(heavy_openings)
    if len(chains) > expect:
        fails.append(("chain count exceeds d+1+h", len(chains), expect))
    if len(chains) != expect - shared:
        fails.append(("chain count", len(chains), expect, shared))
    sumP = sum(len(c) for c in chains)
    if sumP != P - (n - 1) * cc:
        fails.append(("Claim 1", sumP, P - (n - 1) * cc))
    sumO = sum(len({orbr[x] for x in c}) for c in chains)
    sig = sumO - (O - cc)
    sumD = 5 * sumO - sumP if n == 6 else (n - 1) * sumO - sumP
    k = O - factorial(n) // (n * (n - 1))
    if n == 6 and sumD != 5 * k - G + 5 * sig:
        fails.append(("Claim 2", sumD, 5 * k - G + 5 * sig))
    if sig < 0:
        fails.append(("Claim 4: sigma < 0", sig))
    if len(chains) == 1 and sig != 0:
        fails.append(("Claim 4: one chain but sigma != 0", sig))
    # Claim 3, per chain
    toktot, blocktot, hexrep_total = 0, 0, 0
    for c in chains:
        Oi = len({orbr[x] for x in c})
        toki, blocksi, seenh = 0, 1, {hexr[c[0]]}
        for a, bb in zip(c, c[1:]):
            t = etype.get(a)
            if t != "E":
                blocksi += 1
            sameorb = orbr[a] == orbr[bb]
            opened_before = orbr[bb] in {orbr[x] for x in c[:c.index(bb)]}
            if t != "E" and opened_before:
                toki += 1
            if hexr[bb] in seenh:
                hexrep_total += 1
            seenh.add(hexr[bb])
        if blocksi != Oi + toki:
            fails.append(("Claim 3", blocksi, Oi, toki))
        toktot += toki
        blocktot += blocksi
    if blocktot != blocks:
        fails.append(("blocks do not add up", blocktot, blocks))
    if toktot != Bstar - sig:
        fails.append(("Claim 3 sum", toktot, Bstar - sig))
    if hexrep_total > R_int:
        fails.append(("Claim 5", hexrep_total, R_int))
    ab = sum(1 for x in range(P) if x not in purevs and x not in cut
             and etype.get(x) in ("A", "B"))
    if ab > hexrep_total:
        fails.append(("retained A/B exceed the hex repeats", ab, hexrep_total))
    return dict(n=n, length=len(W), P=P, G=G, O=O, k=k, S=S, H=Hh, D2=D2, Qs=Qs,
                K=K, R_int=R_int, c=cc, d=d, g=g, h=h, Bstar=Bstar,
                blocks=blocks, chains=len(chains), keep_heavy=keep_heavy,
                sigma=sig, sum_P=sumP, sum_D=sumD, sum_tok=toktot,
                hex_repeats=hexrep_total, retained_AB=ab,
                chain_sizes=sorted(len(c) for c in chains),
                chains_max=expect, heavy_openings=len(heavy_openings),
                failures=fails, ok=not fails)


def run(seed=20260912, tries4=300, tries5=150):
    rng = random.Random(seed)
    out, bad = {}, []
    W4 = "123412314231243121342132413214321"
    out["n4_optimum"] = extract(W4, 4)
    p6 = ROOT / "data" / "verified_872_witness.txt"
    W6 = p6.read_text().strip()
    out["n6_witness_872"] = extract(W6, 6)
    out["n6_witness_872_heavy_kept"] = extract(W6, 6, keep_heavy=True)
    p5 = ROOT / "outputs" / "rr_nr6_n5_minima_142.json"
    raw = json.loads(p5.read_text())
    w5 = sorted({e["word"] for e in raw if isinstance(e, dict) and "word" in e})
    out["n5_minima"] = dict(count=len(w5),
                            all_ok=all(extract(w, 5)["ok"] for w in w5))
    for n, alpha, base, tries in ((4, "1234", W4, tries4),
                                  (5, "".join(sorted(set(w5[0]))), w5[0], tries5)):
        words = SH.dirty_corpus(n, alpha, base, rng, tries)
        st = dict(words=len(words), failures=0, with_AB=0, with_heavy=0,
                  multi_chain=0, sigma_pos=0)
        for w in words:
            for kh in (False, True):
                r = extract(w, n, keep_heavy=kh)
                if not r["ok"]:
                    st["failures"] += 1
                    bad.append((n, kh, r["failures"]))
                if r["retained_AB"]:
                    st["with_AB"] += 1
                if r["h"]:
                    st["with_heavy"] += 1
                if r["chains"] > 1:
                    st["multi_chain"] += 1
                if r["sigma"] > 0:
                    st["sigma_pos"] += 1
        out[f"n{n}_sweep"] = st
    out["failures"] = bad[:6]
    out["ok"] = (not bad and all(v.get("ok", True) for v in out.values()
                                 if isinstance(v, dict)))
    return out


if __name__ == "__main__":
    r = run(tries4=int(sys.argv[1]) if len(sys.argv) > 1 else 300)
    (ROOT / "outputs" / "rr_l6_extraction_145.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=1))
    for k, v in r.items():
        if isinstance(v, dict):
            print(k, json.dumps({x: v[x] for x in v if x != "failures"},
                                ensure_ascii=False))
            if v.get("failures"):
                print("   FAIL:", json.dumps(v["failures"], ensure_ascii=False)[:400])
    print("ok:", r["ok"])
