#!/usr/bin/env python3
"""Round 161 -- the splicing layer rebuilt lemma by lemma.

Nothing is imported from src/l6_splicing_145.py.  The word-level primitives
(omega, selected, sigma, tau) come from the round-156 independent
reconstruction (r156/src/extract156.py, which imports nothing from src/); the
pass / nu / alpha / T / beta layer and every lemma are rebuilt here, and each
lemma is checked as a SEPARATE clause so that a failure names the lemma.

THE LEMMAS, as stated in src/l6_splicing_145.py lines 16-66, split into the
smallest independently checkable clauses:

  A1  every one of the n! windows is selected exactly once
  A2  gap 1 forces q_{j+1} = sigma(q_j); hence a pass is an ARC of ONE hexagon
  A3  the arcs of a hexagon are disjoint and cover its n windows
  A4  every hexagon carries at least one pass  (m_h >= 1)
  A5  sum_h m_h = P  and  sum_h (m_h - 1) = G,  G := P - n!/n
  B1  nu(i) := the pass whose entry is sigma^{l_i}(v_i) is well defined
  B2  nu is a permutation of the passes
  B3  the cycles of nu are exactly the hexagons, with lengths m_h; c(nu)=n!/n
  C1  the last window of pass i equals end(v_{nu(i)}) = sigma^{-1}(v_{nu(i)})
  C2  reassigning the joint i->i+1 to (nu(i), i+1) changes NOTHING: same source
      string, same target, same gap, same spelling, same hidden windows
  C3  every reassigned edge is a SHORTEST connector out of a full-pass endpoint
      (needs the fixed-representative hypothesis gap = omega)
  D1  beta := T alpha^{-1} is a permutation of {0..P-1} + {*}
  D2  beta(nu(i)) = i+1 for i <= P-2;  beta(nu(P-1)) = *;  beta(*) = 0
  D3  c(alpha) = n!/n + 1 and c(T) = 1
  E1  a clean-E edge sends v to tau(v): same tau-orbit, phase + 1
  E2  a pure (all clean-E) beta-cycle has length exactly n-1
  E3  its entries are ALL n-1 elements of one tau-orbit
  E4  no pass outside the cycle lies in that orbit
  E5  the converse direction, tested separately (see r161/certs)
  F1  every weight-2 joint is clean E or type A     (the gap-2 dichotomy)
  F2  cleanE = P - 1 - S - D2
  F3  blocks := P - cleanE = S + 1 + D2
  F4  deleting a pure circuit removes n-1 vertices and n-1 clean-E edges, so
      `blocks` is unchanged
  G1  a tau-orbit meets each hexagon in at most one window, hence lies in
      exactly n-1 distinct hexagons (so a pure circuit contributes 0 to R_int)
"""
from __future__ import annotations
import json, random, sys, time
from collections import Counter
from math import factorial
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "r156" / "src"))
import extract156 as X                                            # noqa: E402
import corpus156 as C                                             # noqa: E402
import run156 as R                                                # noqa: E402

sigma, tau, sig_pow, hexrep, orbrep, omega = (X.sigma, X.tau, X.sig_pow,
                                              X.hexrep, X.orbrep, X.omega)


def end(w):
    return w[-1] + w[:-1]


def hidden(src, tgt, gap, n):
    raw = src + tgt[n - gap:] if gap < n else src + tgt
    return [raw[o:o + n] for o in range(1, gap)
            if len(set(raw[o:o + n])) == n]


def build(W, n, require_cover=True, require_fixed=True):
    """Rebuild the whole splicing layer, returning diagnostics not exceptions."""
    N = factorial(n)
    HEX = N // n
    bad = []
    sel = X.selected(W, n)
    # ---- A1
    if len(sel) != N:
        bad.append(("A1 not every window is selected", len(sel), N))
        if require_cover:
            return dict(ok=False, failures=bad)
    if len({w for _, w in sel}) != len(sel):
        bad.append("A1 a window is selected twice")
    gaps = [sel[j + 1][0] - sel[j][0] for j in range(len(sel) - 1)]
    fixed = all(gaps[j] == omega(sel[j][1], sel[j + 1][1], n)
                for j in range(len(gaps)))
    if require_fixed and not fixed:
        bad.append("not a fixed representative (a selected gap != omega)")
    # ---- A2: gap 1 forces sigma
    for j, g in enumerate(gaps):
        if g == 1 and sel[j + 1][1] != sigma(sel[j][1]):
            bad.append(("A2 gap 1 without sigma", j))
    # ---- passes
    passes, s, l = [], 0, 1
    for j, g in enumerate(gaps):
        if g == 1:
            l += 1
        else:
            passes.append((sel[s][1], l))
            s, l = j + 1, 1
    passes.append((sel[s][1], l))
    P = len(passes)
    G = P - HEX
    # ---- A2 (arc property) and A3 / A4 / A5
    byhex = {}
    for i, (v, ln) in enumerate(passes):
        cover = [sig_pow(v, t) for t in range(ln)]
        if len({hexrep(x) for x in cover}) != 1:
            bad.append(("A2 a pass spans two hexagons", i))
        if len(set(cover)) != ln:
            bad.append(("A2 a pass repeats a window", i))
        byhex.setdefault(hexrep(v), []).append(i)
    for h, idxs in byhex.items():
        cov = []
        for i in idxs:
            v, ln = passes[i]
            cov += [sig_pow(v, t) for t in range(ln)]
        if len(cov) != n or len(set(cov)) != n:
            bad.append(("A3 arcs do not partition the hexagon", h))
    if len(byhex) != HEX:
        bad.append(("A4 a hexagon carries no pass", len(byhex), HEX))
    if sum(len(v) for v in byhex.values()) != P:
        bad.append("A5 sum m_h != P")
    if sum(len(v) - 1 for v in byhex.values()) != G:
        bad.append("A5 sum (m_h - 1) != G")

    # ---- B
    entry = {v: i for i, (v, ln) in enumerate(passes)}
    if len(entry) != P:
        bad.append("B1 two passes share an entry")
    nu = []
    for i, (v, ln) in enumerate(passes):
        t = sig_pow(v, ln)
        if t not in entry:
            bad.append(("B1 nu target is not a pass entry", i))
            nu.append(i)
        else:
            nu.append(entry[t])
    if sorted(nu) != list(range(P)):
        bad.append("B2 nu is not a permutation")
    seen, nucyc = [False] * P, []
    for i in range(P):
        if seen[i]:
            continue
        cy, x = [], i
        while not seen[x]:
            seen[x] = True
            cy.append(x)
            x = nu[x]
        nucyc.append(cy)
    if len(nucyc) != HEX:
        bad.append(("B3 c(nu) != n!/n", len(nucyc), HEX))
    if sorted(len(c) for c in nucyc) != sorted(len(v) for v in byhex.values()):
        bad.append("B3 nu cycle lengths are not the m_h")
    for cy in nucyc:
        if len({hexrep(passes[i][0]) for i in cy}) != 1:
            bad.append("B3 a nu cycle spans two hexagons")

    # ---- C : the splice, joint by joint
    endpos = {}
    for i, (v, ln) in enumerate(passes):
        endpos[sig_pow(v, ln - 1)] = i
    joints = []
    gap_gt_n = 0
    for j, g in enumerate(gaps):
        if g == 1:
            continue
        src_orig, tgt = sel[j][1], sel[j + 1][1]
        i = endpos.get(src_orig)
        if i is None:
            bad.append(("C1 no pass ends at a joint source", j))
            continue
        p = nu[i]
        # C1: the endpoint identity
        if src_orig != end(passes[p][0]):
            bad.append(("C1 endpoint identity fails", j))
        # C2: the reassignment changes nothing (checked literally on strings)
        src_spl = end(passes[p][0])
        # C2 compares the joint BEFORE and AFTER reassignment.  The
        # reassignment does not touch the word, so the gap is the same g on
        # both sides; what must be shown is that source string, target,
        # spelling and hidden windows are the same too.
        # a gap can only exceed n on a word that is not a fixed
        # representative; there the two windows do not overlap at all and the
        # "source + tail" spelling is not the right object, so the literal
        # spelling check is restricted to g <= n and the case is counted.
        if g <= n:
            sp_orig = src_orig + tgt[n - g:]
            sp_spl = src_spl + tgt[n - g:]
            if (src_orig, tgt, g, sp_orig, hidden(src_orig, tgt, g, n)) != \
               (src_spl, tgt, g, sp_spl, hidden(src_spl, tgt, g, n)):
                bad.append(("C2 the reassignment changed something", j))
            if W[sel[j][0]:sel[j][0] + n + g] != sp_orig:
                bad.append(("C2 the word does not spell the connector", j))
        else:
            gap_gt_n += 1
            if src_orig != src_spl:
                bad.append(("C2 the reassignment changed the source", j))
        # C3: the reassigned edge is a SHORTEST connector out of the full-pass
        # endpoint.  Checked UNCONDITIONALLY so that dropping the
        # fixed-representative hypothesis shows up here and nowhere else.
        if g != omega(src_spl, tgt, n):
            bad.append(("C3 not a shortest connector", j))
        joints.append(dict(i=i, p=p, q=entry.get(tgt), w=g, src=src_spl,
                           tgt=tgt))
    if len(joints) != P - 1:
        bad.append(("C the joint count != P-1", len(joints), P - 1))

    # ---- D
    dummy = P
    alpha = nu + [dummy]
    T = [i + 1 for i in range(P - 1)] + [dummy, 0]
    ainv = [0] * (P + 1)
    for x in range(P + 1):
        ainv[alpha[x]] = x
    beta = [T[ainv[x]] for x in range(P + 1)]
    if sorted(beta) != list(range(P + 1)):
        bad.append("D1 beta is not a permutation")
    for i in range(P - 1):
        if beta[nu[i]] != i + 1:
            bad.append(("D2 beta(nu(i)) != i+1", i))
    if beta[nu[P - 1]] != dummy or beta[dummy] != 0:
        bad.append("D2 the two dummy edges are wrong")
    ac = X.components(alpha)
    if len(ac) != HEX + 1:
        bad.append(("D3 c(alpha) != n!/n + 1", len(ac), HEX + 1))
    if len(X.components(T)) != 1:
        bad.append("D3 T is not a single cycle")
    # the beta edges ARE the reassigned joints plus the two dummy edges
    betaedges = {(x, beta[x]) for x in range(P + 1)}
    jedges = {(jt["p"], jt["q"]) for jt in joints}
    if not jedges <= betaedges:
        bad.append("D2 a reassigned joint is not a beta edge")
    if len(betaedges - jedges) != 2:
        bad.append(("D2 beta has other edges than joints + 2 dummy",
                    len(betaedges - jedges)))

    # ---- edge types (rebuilt, not looked up)
    etype, eweight = {}, {}
    for jt in joints:
        v, tgt, g = jt["src"], jt["tgt"], jt["w"]
        vv = passes[jt["p"]][0]
        if g == 2:
            ty = "E" if tgt == tau(vv, n) else ("A" if tgt == sigma(vv)
                                                else "?w2")
        elif g == 3:
            ty = "B" if tgt == sigma(sigma(vv)) else "w3"
        else:
            ty = "heavy"
        etype[jt["p"]] = ty
        eweight[jt["p"]] = g
    # ---- F1 : the gap-2 dichotomy
    if any(t == "?w2" for t in etype.values()):
        bad.append("F1 a weight-2 joint is neither clean E nor type A")
    S = sum(1 for w in eweight.values() if w >= 3)
    D2c = sum(1 for t in etype.values() if t == "A")
    cleanE = sum(1 for t in etype.values() if t == "E")
    if cleanE != P - 1 - S - D2c:
        bad.append(("F2 cleanE != P-1-S-D2", cleanE, P - 1 - S - D2c))
    blocks = P - cleanE
    if blocks != S + 1 + D2c:
        bad.append(("F3 blocks != S+1+D2", blocks, S + 1 + D2c))

    # ---- E
    comps = X.components(beta)
    pure = [cy for cy in comps if dummy not in cy
            and all(etype.get(x) == "E" for x in cy)]
    for cy in pure:
        if len(cy) != n - 1:
            bad.append(("E2 pure cycle length != n-1", len(cy)))
        orbs = {orbrep(passes[x][0], n) for x in cy}
        if len(orbs) != 1:
            bad.append("E3 pure cycle spans two orbits")
        ports = {passes[x][0] for x in cy}
        y, allp = passes[cy[0]][0], set()
        for _ in range(n - 1):
            allp.add(y)
            y = tau(y, n)
        if ports != allp:
            bad.append("E3 pure cycle is not the whole orbit")
        for i in range(P):
            if i not in cy and orbrep(passes[i][0], n) in orbs:
                bad.append("E4 a pure orbit carries an outside pass")
    # E1 on every clean-E edge
    for x, t in etype.items():
        if t != "E":
            continue
        if passes[beta[x]][0] != tau(passes[x][0], n):
            bad.append(("E1 clean E target is not tau(v)", x))
    # ---- F4 : deleting a pure circuit leaves `blocks` unchanged
    purev = {x for cy in pure for x in cy}
    P2 = P - len(purev)
    cleanE2 = cleanE - sum(len(cy) for cy in pure)
    if P2 - cleanE2 != blocks:
        bad.append(("F4 block count changed", P2 - cleanE2, blocks))
    if any(len(cy) != n - 1 for cy in pure):
        bad.append("F4 a pure circuit does not have n-1 clean E edges")
    # ---- E5 : the CONVERSE of Lemma E is FALSE and is not claimed.
    # Count the tau-orbits all of whose n-1 elements are pass entries; if that
    # exceeds the number of pure circuits, a complete orbit exists whose
    # component is not pure.
    entries = {passes[i][0] for i in range(P)}
    full_orbits = 0
    seen_orb = set()
    for i in range(P):
        o = orbrep(passes[i][0], n)
        if o in seen_orb:
            continue
        seen_orb.add(o)
        y, all_in = o, True
        for _ in range(n - 1):
            if y not in entries:
                all_in = False
            y = tau(y, n)
        if all_in:
            full_orbits += 1

    # ---- G1 : a tau-orbit meets each hexagon at most once
    for i in range(P):
        v = passes[i][0]
        y, hs = v, []
        for _ in range(n - 1):
            hs.append(hexrep(y))
            y = tau(y, n)
        if len(set(hs)) != n - 1:
            bad.append(("G1 a tau-orbit repeats a hexagon", v))
    return dict(ok=not bad, failures=bad, n=n, L=len(W), P=P, G=G, S=S,
                D2=D2c, cleanE=cleanE, blocks=blocks, HEX=HEX,
                fixed=fixed, pure=len(pure), K=len(comps),
                full_orbits=full_orbits,
                converse_E_fails=(full_orbits > len(pure)),
                gaps_over_n=gap_gt_n,
                types=dict(Counter(etype.values())),
                m_h=sorted(Counter(len(v) for v in byhex.values()).items()),
                max_m_h=max(len(v) for v in byhex.values()))


def main():
    t0 = time.time()
    rng = random.Random(161161)
    ws, w5 = R.words()
    sys.path.insert(0, str(ROOT / "r156" / "src"))
    import passes156 as P3                                        # noqa: E402
    pool = [(tag, n, W) for tag, n, W in ws]
    pool += [(f"n3e{i}", 3, w) for i, w in enumerate(P3.n3_family())]
    pool += [(f"n4c{i}", 4, w) for i, w in
             enumerate(C.corpus(4, "1234", [R.W4], rng, 1200))]
    pool += [(f"n5c{i}", 5, w) for i, w in
             enumerate(C.corpus(5, "01234", w5, rng, 500))]
    st, bad, named = Counter(), [], {}
    for tag, n, W in pool:
        r = build(W, n)
        st["words"] += 1
        st[f"n{n}"] += 1
        if not r["ok"]:
            st["failures"] += 1
            if len(bad) < 8:
                bad.append(dict(tag=tag, n=n, failures=r["failures"][:5]))
            continue
        for key, cond in (("pure_pos", r["pure"] > 0), ("G_pos", r["G"] > 0),
                          ("heavy", r["types"].get("heavy", 0) > 0),
                          ("A_pos", r["D2"] > 0),
                          ("m_h_ge3", r["max_m_h"] >= 3),
                          ("m_h_ge4", r["max_m_h"] >= 4),
                          ("converse_E_fails", r["converse_E_fails"]),
                          ("full_orbit_pos", r["full_orbits"] > 0)):
            if cond:
                st[key] += 1
        if tag in ("n4_optimum", "n6_witness_872"):
            named[tag] = {k: v for k, v in r.items() if k != "failures"}
    out = dict(seconds=round(time.time() - t0, 1), stats=dict(st),
               named=named, failures=bad, ok=(st["failures"] == 0))
    (ROOT / "r161" / "certs" / "real_161.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "named"},
                     ensure_ascii=False, indent=1)[:1500])
    for k, v in named.items():
        print(k, json.dumps(v, ensure_ascii=False))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
