#!/usr/bin/env python3
"""Round 146 — adversarial audit of the ENVELOPE inequalities and of
successor splicing AT THE STRING LEVEL.  Clean-room: only l6_cleanroom_146's
string primitives are shared.

ENVELOPE, re-derived from definitions (nothing inherited from comments).

  Objects.  After deleting the c pure clean-E beta-circuits, the remaining
  K - c = d + 1 components are opened (one non-E edge each; the dummy component
  is already a path once * is removed) and the h heavy joints are cut.  Call the
  resulting paths CHAINS.  For the chain decomposition define

    a  = # retained type A (sigma) edges lying inside chains
    bb = # retained type B (sigma^2) edges lying inside chains
    e  = # ports whose hexagon already occurred earlier in their OWN chain and
         which are NOT the target of a retained A/B edge
    x  = # type A edges spent as cycle openings,  y = same for type B

  (1) a <= D2 and (2) bb <= Qs.  Immediate: a = D2 - x and bb = Qs - y.

  (3) a + bb + e <= R_int.  Each retained A/B edge has target hexagon equal to
  its source hexagon and its source is its immediate predecessor in the chain,
  so its target is one of the "hexagon already seen in this chain" ports; beta is
  a permutation so each port has in-degree 1 and distinct A/B edges have distinct
  targets; e counts the remaining such ports.  Hence a + bb + e is EXACTLY the
  total within-chain hexagon excess, and cutting a component into chains can only
  lower excess, so it is <= R_int.

  (4) e <= Z - Qs.  e = (a+bb+e) - a - bb <= R_int - (D2-x) - (Qs-y)
      <= 2g - D2 - Qs + d   (R_int <= 2g, x+y <= d)
      = (D2 + Z - d) - D2 - Qs + d = Z - Qs,    using 2g = z - d = D2 + Z - d.

  Also a + bb + e <= 2g, which is what the DP uses as the shared repeat budget.

SPLICING, checked literally.  For every inter-pass joint the ORIGINAL spelling is
(last window of pass i) + tail(next entry), and the SPLICED spelling is
(sigma^{-1} of the entry of pass nu(i)) + the same tail.  This module asserts the
two SOURCE STRINGS, the two GAPS, the two full SPELLINGS and the two lists of
HIDDEN WINDOWS are equal as strings/lists -- not merely that some invariant
matches.
"""
from __future__ import annotations
import gzip, json, sys
from collections import Counter
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from l6_cleanroom_146 import sig, tau, hexkey, orbkey, omega, hiddens  # noqa


def _end(v):
    return v[-1] + v[:-1]


def decompose(W, n=6):
    N = factorial(n)
    seen, sel, pos = set(), [], []
    for i in range(len(W) - n + 1):
        w = W[i:i + n]
        if len(set(w)) == n and w not in seen:
            seen.add(w)
            sel.append(w)
            pos.append(i)
    gaps = [pos[j + 1] - pos[j] for j in range(N - 1)]
    passes, run = [], [0]
    for j, g in enumerate(gaps):
        if g == 1:
            run.append(j + 1)
        else:
            passes.append(run)
            run = [j + 1]
    passes.append(run)
    ent = [sel[r[0]] for r in passes]
    lens = [len(r) for r in passes]
    P = len(passes)
    idx = {e: i for i, e in enumerate(ent)}
    nu = []
    for i in range(P):
        x = ent[i]
        for _ in range(lens[i]):
            x = sig(x)
        nu.append(idx[x])
    return sel, pos, gaps, ent, lens, P, nu


def splice_string_audit(W, n=6):
    """Literal string-level check that reassignment changes nothing."""
    sel, pos, gaps, ent, lens, P, nu = decompose(W, n)
    fails, seenty = [], Counter()
    for j, g in enumerate(gaps):
        if g == 1:
            continue
        src_orig = sel[j]                                 # last window of pass i
        tgt = sel[j + 1]
        i = next(i for i in range(P) if _adv(ent[i], lens[i] - 1) == src_orig)
        p = nu[i]
        src_spl = _end(ent[p])                            # full-pass endpoint
        if src_orig != src_spl:
            fails.append(("SOURCE WINDOW DIFFERS", j, src_orig, src_spl))
            continue
        g_orig = pos[j + 1] - pos[j]
        g_spl = omega(src_spl, tgt)
        if g_orig != g_spl:
            fails.append(("GAP DIFFERS", j, g_orig, g_spl))
        sp_orig = src_orig + tgt[n - g_orig:]
        sp_spl = src_spl + tgt[n - g_spl:]
        if sp_orig != sp_spl:
            fails.append(("SPELLING DIFFERS", j, sp_orig, sp_spl))
        if hiddens(src_orig, tgt, g_orig) != hiddens(src_spl, tgt, g_spl):
            fails.append(("HIDDEN WINDOWS DIFFER", j))
        # also confirm the literal word really spells it that way
        if W[pos[j]:pos[j] + n + g_orig] != sp_orig:
            fails.append(("WORD DOES NOT SPELL THE CONNECTOR", j))
        v = ent[p]
        ty = ("E" if (g_orig == 2 and tgt == tau(v)) else
              "A" if (g_orig == 2 and tgt == sig(v)) else
              "120" if (g_orig == 3 and tgt == tau(tau(v))) else
              "B" if (g_orig == 3 and tgt == sig(sig(v))) else
              "C" if (g_orig == 3 and tgt == tau(sig(v))) else
              "D" if (g_orig == 3 and tgt == sig(tau(v))) else
              "clean_w3" if g_orig == 3 else "heavy")
        seenty[(ty, lens[p] == n)] += 1
    return dict(joints=sum(seenty.values()), by_type_and_fullpass=
                {f"{t}/{'full' if f else 'short'}": v
                 for (t, f), v in sorted(seenty.items())},
                failures=fails[:5], ok=not fails)


def envelope_audit(W, n=6, keep_heavy=False):
    sel, pos, gaps, ent, lens, P, nu = decompose(W, n)
    N = factorial(n)
    G = P - N // n
    hx = [hexkey(e) for e in ent]
    ob = [orbkey(e) for e in ent]
    DUM = "*"
    T = {i: i + 1 for i in range(P - 1)}
    T[P - 1] = DUM
    T[DUM] = 0
    alpha = {i: nu[i] for i in range(P)}
    alpha[DUM] = DUM
    ainv = {v: kk for kk, v in alpha.items()}
    beta = {x: T[ainv[x]] for x in list(range(P)) + [DUM]}
    ty, wt = {}, {}
    for j, g in enumerate(gaps):
        if g == 1:
            continue
        src = sel[j]
        i = next(i for i in range(P) if _adv(ent[i], lens[i] - 1) == src)
        p = nu[i]
        v, tgt = ent[p], sel[j + 1]
        wt[p] = g
        ty[p] = ("E" if (g == 2 and tgt == tau(v)) else
                 "A" if (g == 2 and tgt == sig(v)) else
                 "120" if (g == 3 and tgt == tau(tau(v))) else
                 "B" if (g == 3 and tgt == sig(sig(v))) else
                 "C" if (g == 3 and tgt == tau(sig(v))) else
                 "D" if (g == 3 and tgt == sig(tau(v))) else
                 "clean_w3" if g == 3 else "heavy")
    comps, seen2 = [], set()
    for st in list(range(P)) + [DUM]:
        if st in seen2:
            continue
        cy, x = [], st
        while x not in seen2:
            seen2.add(x)
            cy.append(x)
            x = beta[x]
        comps.append(cy)
    K = len(comps)
    R_int = sum(sum(v - 1 for v in Counter(hx[x] for x in cy if x != DUM).values())
                for cy in comps)
    pure = [cy for cy in comps if DUM not in cy and all(ty.get(x) == "E" for x in cy)]
    c, d = len(pure), K - 1 - len(pure)
    g2 = (G + 1 - K) // 2
    S = sum(1 for w in wt.values() if w >= 3)
    Hh = sum(max(w - 3, 0) for w in wt.values())
    h = sum(1 for w in wt.values() if w >= 4)
    D2 = sum(1 for t in ty.values() if t == "A")
    Qs = sum(1 for t in ty.values() if t == "B")
    O = len(set(ob))
    k = O - N // (n * (n - 1))
    blocks = P - sum(1 for t in ty.values() if t == "E")
    Bstar = blocks - (O - c)
    Z = (G - c) - D2
    # ---- cut into chains
    purev = {x for cy in pure for x in cy}
    cut, x_open, y_open = set(), 0, 0
    for cy in comps:
        if DUM in cy or cy in pure:
            continue
        light = [q for q in cy if ty.get(q) not in (None, "E") and wt.get(q, 9) <= 3]
        op = light[0] if light else next(q for q in cy if ty.get(q) not in (None, "E"))
        cut.add(op)
        if ty.get(op) == "A":
            x_open += 1
        elif ty.get(op) == "B":
            y_open += 1
    if not keep_heavy:
        cut |= {q for q, w in wt.items() if w >= 4}
    succ = {}
    for q in range(P):
        if q in purev or q in cut:
            continue
        r = beta[q]
        if r != DUM and r not in purev:
            succ[q] = r
    indeg = Counter(succ.values())
    chains = []
    for st in range(P):
        if st in purev or indeg[st]:
            continue
        ch, q = [], st
        while True:
            ch.append(q)
            if q not in succ:
                break
            q = succ[q]
        chains.append(ch)
    # ---- measure a, bb, e literally
    a = bb = e = 0
    sumP = sumO = tok = 0
    for ch in chains:
        sumP += len(ch)
        sumO += len({ob[q] for q in ch})
        seenh, orbseen = {hx[ch[0]]}, {ob[ch[0]]}
        for u, v2 in zip(ch, ch[1:]):
            t = ty.get(u)
            if t != "E" and ob[v2] in orbseen:
                tok += 1
            if hx[v2] in seenh:
                if t == "A":
                    a += 1
                elif t == "B":
                    bb += 1
                else:
                    e += 1
            elif t in ("A", "B"):
                e -= 0
                a += 0
                # an A/B target whose hexagon is NOT already seen would break (3)
                return dict(ok=False, why="A/B target hexagon not already seen")
            seenh.add(hx[v2])
            orbseen.add(ob[v2])
    sigma_ = sumO - (O - c)
    fails = []
    if a > D2:
        fails.append(("(1) a > D2", a, D2))
    if bb > Qs:
        fails.append(("(2) bb > Qs", bb, Qs))
    if a + bb + e > R_int:
        fails.append(("(3) a+bb+e > R_int", a + bb + e, R_int))
    if a + bb + e > 2 * g2:
        fails.append(("(3') a+bb+e > 2g", a + bb + e, 2 * g2))
    if e > max(0, Z - Qs):
        fails.append(("(4) e > Z-Qs", e, Z - Qs))
    if x_open + y_open > d:
        fails.append(("x+y > d", x_open + y_open, d))
    if sumP != P - (n - 1) * c:
        fails.append(("sum P_i", sumP, P - (n - 1) * c))
    if n == 6 and 5 * sumO - sumP != 5 * k - G + 5 * sigma_:
        fails.append("sum D_i")
    if tok != Bstar - sigma_:
        fails.append(("sum tok != B*-sigma", tok, Bstar - sigma_))
    if len(chains) > d + 1 + (0 if keep_heavy else h):
        fails.append(("too many chains", len(chains), d + 1 + h))
    return dict(a=a, bb=bb, e=e, D2=D2, Qs=Qs, R_int=R_int, two_g=2 * g2,
                Z=Z, ZmQs=Z - Qs, x=x_open, y=y_open, d=d, h=h, c=c, G=G,
                chains=len(chains), sumP=sumP, tok=tok, sigma=sigma_,
                tight3=(a + bb + e == R_int), tight4=(e == max(0, Z - Qs)),
                tight1=(a == D2), tight2=(bb == Qs),
                failures=fails[:5], ok=not fails)


def _adv(s, j):
    for _ in range(j):
        s = sig(s)
    return s


if __name__ == "__main__":
    tot, bad, st = 0, [], Counter()
    for path in sys.argv[1:]:
        op = gzip.open if path.endswith(".gz") else open
        with op(path, "rt") as fh:
            for line in fh:
                s = line.strip()
                if not s or s.startswith("#") or len(s) < 40:
                    continue
                n = len(set(s))
                if n not in (4, 5, 6):
                    continue
                tot += 1
                sp = splice_string_audit(s, n)
                if not sp["ok"]:
                    bad.append((path, "SPLICE", sp["failures"]))
                for kh in (False, True):
                    ev = envelope_audit(s, n, keep_heavy=kh)
                    if not ev.get("ok"):
                        bad.append((path, f"ENVELOPE kh={kh}",
                                    ev.get("failures") or ev.get("why")))
                    else:
                        for f in ("tight1", "tight2", "tight3", "tight4"):
                            if ev[f]:
                                st[f] += 1
                        st["nonzero_a"] += 1 if ev["a"] else 0
                        st["nonzero_bb"] += 1 if ev["bb"] else 0
                        st["nonzero_e"] += 1 if ev["e"] else 0
                        st["nonzero_xy"] += 1 if ev["x"] + ev["y"] else 0
                for kk, v in sp["by_type_and_fullpass"].items():
                    st["jt:" + kk] += v
    print(f"words={tot} failures={len(bad)}")
    print(json.dumps(dict(st), ensure_ascii=False, indent=1))
    for b in bad[:6]:
        print("  FAIL", b)
    (ROOT / "outputs" / "rr_l6_envelope_146.json").write_text(
        json.dumps(dict(words=tot, failures=len(bad), stats=dict(st),
                        failure_examples=[list(map(str, b)) for b in bad[:10]]),
                   ensure_ascii=False, indent=1))
    sys.exit(1 if bad else 0)
