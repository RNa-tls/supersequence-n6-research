#!/usr/bin/env python3
"""Round 145 — SAME-HEX  D2 + Qs <= R_int,  proved here and stress-tested.

This was the last relation the Round-144 closure imported without an
independent proof.  It is now proved and exercised on covers that really do
contain dirty joints.

-------------------------------------------------------------------------------
STATEMENT.  In the spliced structure let D2 be the number of type A joints
(dirty weight 2, spliced target sigma(v)) and Qs the number of type B joints
(dirty weight 3, spliced target sigma^2(v)).  Let R_int be the within-component
duplicate-hexagon excess of beta.  Then

        D2 + Qs <= R_int.

PROOF.

(1) SAME HEXAGON.  A type A spliced edge runs from pass p = nu(i) to pass
    q = i+1 with v_q = sigma(v_p); a type B edge has v_q = sigma^2(v_p).  In
    both cases h(v_q) = h(v_p), and p, q lie in the same beta-component because
    q = beta(p).

(2) THE INDEX STRICTLY INCREASES.  Write p' = end(v_{nu(i)}) = sigma^{l_i-1}(v_i)
    for the joint source.  A type A connector spells p' then two letters, and its
    one hidden window is sigma(p') = v_{nu(i)}; a type B connector spells three
    letters with hidden windows sigma(p') = v_{nu(i)} and sigma^2(p').  In a
    fixed representative every hidden window of a selected connector is a
    REPEAT, so v_{nu(i)} has occurred strictly earlier than this joint, and
    since v_{nu(i)} is a pass entry its first occurrence is the start of pass
    nu(i).  Hence nu(i) <= i.  Equality would force sigma^{l_i}(v_i) = v_i,
    i.e. l_i = n, so pass i would be the whole hexagon and the target
    (sigma^2(p') resp. sigma^3(p')) would already lie inside pass i, so it could
    not be a first occurrence.  Therefore nu(i) < i < i+1: every type A or B
    spliced edge goes from a strictly smaller pass index to a strictly larger
    one.

(3) COUNTING.  Fix a hexagon h and a beta-component j, and let m = m_{h,j} be
    the number of passes of h inside j.  By (1) every type A/B edge with an
    endpoint in that group has BOTH endpoints in it.  By (2) the group's A/B
    edges form a digraph with strictly increasing indices, hence no directed
    cycle; and every vertex has in-degree at most one, because beta is a
    permutation and so each pass has exactly one incoming beta edge.  A digraph
    with in-degree <= 1 and no directed cycle is a forest of in-trees, so it has
    at most m - 1 edges.  Summing over all pairs (h, j),

        D2 + Qs <= sum_{h,j} (m_{h,j} - 1) = R_int.

COROLLARY.  With the incidence bound R_int <= 2g this gives D2 + Qs <= 2g, hence
Z = 2g + d - D2 >= Qs >= 0.  These are exactly the constraints the row
enumeration uses, and Z >= 0 is what makes every summand of MASTER-142
nonnegative.
-------------------------------------------------------------------------------
"""
from __future__ import annotations
import json, random, sys
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import l6_splicing_145 as SP                                        # noqa: E402
from l6_fixed_representative_145 import (is_cover, fixed_representative,  # noqa
                                         selected, omega)


def random_cover(n, alpha, rng):
    """A random cover: random walk that appends letters until all n! windows appear."""
    import itertools
    need = {"".join(p) for p in itertools.permutations(alpha)}
    w = "".join(rng.sample(list(alpha), n))
    seen = {w}
    guard, limit = 0, 400 * len(need)
    while seen != need and guard < limit:
        guard += 1
        w += rng.choice(alpha)
        t = w[-n:]
        if len(set(t)) == n:
            seen.add(t)
    return w if seen == need else None


def dirty_corpus(n, alpha, base, rng, tries):
    """Fixed representatives that actually contain dirty joints.

    A dirty joint needs a hidden repeated window, so it needs the word to be
    non-trivially redundant.  Random insertions that keep the cover property,
    followed by the Phi fixed point, produce them in quantity.
    """
    out, seen = [], set()
    for it in range(tries):
        if it % 2 == 0:
            w = random_cover(n, alpha, rng)
            if w is None:
                continue
        else:
            w = base
            for _ in range(rng.randint(1, 4)):
                p = rng.randrange(len(w))
                w = w[:p] + "".join(rng.choice(alpha)
                                    for _ in range(rng.randint(1, n + 3))) + w[p:]
        if not is_cover(w, n, alpha):
            continue
        try:
            ws, _ = fixed_representative(w, n)
        except AssertionError:
            continue
        if ws in seen:
            continue
        seen.add(ws)
        out.append(ws)
    return out


def run(seed=20260912, tries4=1500, tries5=500):
    rng = random.Random(seed)
    res, bad = {}, []
    for n, alpha, base, tries in (
            (4, "1234", "123412314231243121342132413214321", tries4),
            (5, "01234", None, tries5)):
        if n == 5:
            p5 = ROOT / "outputs" / "rr_nr6_n5_minima_142.json"
            raw = json.loads(p5.read_text())
            base = sorted({e["word"] for e in raw
                           if isinstance(e, dict) and "word" in e})[0]
            alpha = "".join(sorted(set(base)))
        words = dirty_corpus(n, alpha, base, rng, tries)
        stats = dict(words=len(words), with_dirty=0, with_A=0, with_B=0,
                     with_C=0, with_D=0, with_heavy=0, tight=0,
                     max_D2=0, max_Qs=0, max_R_int=0)
        for w in words:
            a = SP.analyse(w, n)
            if not a["ok"]:
                bad.append((n, "splicing audit failed", a["failures"]))
                continue
            if not a["FO_holds"]:
                bad.append((n, "FO fails"))
            ty = a["types"]
            D2, Qs, R = a["D2"], a["Qs"], a["R_int"]
            if D2 + Qs > R:
                bad.append((n, "SAME-HEX violated", D2, Qs, R))
            if D2 + Qs > 2 * a["g"]:
                bad.append((n, "D2+Qs > 2g", D2, Qs, a["g"]))
            if a["Z"] < 0 or a["Qs"] > a["Z"]:
                bad.append((n, "Z < 0 or Qs > Z", a["Z"], a["Qs"]))
            if a["K"] + R > a["G"] + 1:
                bad.append((n, "incidence violated"))
            stats["with_dirty"] += 1 if (D2 or Qs or ty.get("C") or ty.get("D")) else 0
            stats["with_A"] += 1 if D2 else 0
            stats["with_B"] += 1 if Qs else 0
            stats["with_C"] += 1 if ty.get("C") else 0
            stats["with_D"] += 1 if ty.get("D") else 0
            stats["with_heavy"] += 1 if ty.get("heavy") else 0
            stats["tight"] += 1 if D2 + Qs == R and R > 0 else 0
            stats["max_D2"] = max(stats["max_D2"], D2)
            stats["max_Qs"] = max(stats["max_Qs"], Qs)
            stats["max_R_int"] = max(stats["max_R_int"], R)
        res[f"n{n}"] = stats
    res["failures"] = bad[:6]
    res["nfail"] = len(bad)
    res["ok"] = not bad
    return res


if __name__ == "__main__":
    r = run(tries4=int(sys.argv[1]) if len(sys.argv) > 1 else 1500)
    (ROOT / "outputs" / "rr_l6_same_hex_145.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=1))
    print(json.dumps(r, ensure_ascii=False, indent=1))
