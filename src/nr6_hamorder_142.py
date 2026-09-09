#!/usr/bin/env python3
"""NR6 hard core — where does no-repeat ACTUALLY enter the outer proof?

Take any covering word X at a first-occurrence geodesic fixed point.  Select the
FIRST occurrence of each permutation; in position order these are a Hamilton
ORDER v_0..v_{n!-1}, and X is exactly its max-overlap spelling.

Facts checked here on every repeat-bearing walk found by exhaustive search:

 (H1) Each sigma-class contains exactly n selected occurrences (its n vertices),
      so the SELECTED passes PARTITION every sigma-cycle -- even though the word
      itself repeats windows.
 (H2) Hence nu(i), defined by v_{nu(i)} = sigma^{l_i}(v_i), is a well-defined
      permutation of the selected passes, exactly as in the NR6 setting.
 (H3) The resource identity  L = (n! + (n-1)! + n - 2) + G + S + H  holds
      verbatim, with G = P-(n-1)!, S = #joints of weight>=3, H = sum(w-3)_+.

So ALL of the outer framework's bookkeeping survives repeats.  The single place
NR6 is genuinely consumed is:

 (H4) a weight-2 joint must be the CLEAN successor tau(p) = E(sigma(p)).
      A word with repeats may instead use the DIRTY weight-2 edge p -> sigma^2(p),
      whose target is NOT E(sigma(p)) and which stays inside the same hexagon.

This module measures how often (H4) actually fails.
"""
from __future__ import annotations
import json, sys, glob, math
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nr6_geometry_142 import Geo

ROOT = Path(__file__).resolve().parent.parent


def hexid(g):
    H = [-1] * g.N
    h = 0
    for i in range(g.N):
        if H[i] < 0:
            x = i
            for _ in range(g.n):
                H[x] = h
                x = g.SIG[x]
            h += 1
    return H


def hamilton_order(g, walk):
    """First occurrence of each vertex, in walk order."""
    seen = set()
    order = []
    for v in walk:
        if v not in seen:
            seen.add(v)
            order.append(v)
    return order


def analyse_order(g, order):
    n = g.n
    HEX = hexid(g)
    W = [g.W[order[i]][order[i + 1]] for i in range(len(order) - 1)]
    # passes = maximal runs of weight-1 steps among SELECTED occurrences
    passes, cur = [], [order[0]]
    for i, w in enumerate(W):
        if w == 1:
            cur.append(order[i + 1])
        else:
            passes.append(cur)
            cur = [order[i + 1]]
    passes.append(cur)
    entry = [p[0] for p in passes]
    length = [len(p) for p in passes]
    P = len(passes)
    # (H1) each hexagon's selected occurrences are its n vertices, partitioned
    byhex = Counter()
    for p in passes:
        byhex[HEX[p[0]]] += len(p)
    H1 = all(v == n for v in byhex.values()) and len(byhex) == g.N // n
    part = all(len({*p}) == len(p) for p in passes)
    # (H2) nu well-defined on passes
    pos = {e: i for i, e in enumerate(entry)}
    nu = []
    ok2 = True
    for i in range(P):
        t = entry[i]
        for _ in range(length[i]):
            t = g.SIG[t]
        if t not in pos:
            ok2 = False
            break
        nu.append(pos[t])
    H2 = ok2 and (sorted(nu) == list(range(P)) if ok2 else False)
    # (H3) resource identity
    joints = [w for w in W if w != 1]
    S = sum(1 for w in joints if w >= 3)
    Hh = sum(w - 3 for w in joints if w > 3)
    G = P - math.factorial(n - 1)
    L = n + sum(W)
    base = math.factorial(n) + math.factorial(n - 1) + n - 2
    H3 = (L == base + G + S + Hh)
    # (H4) weight-2 joints: clean tau vs dirty sigma^2
    tau_j = dirty_j = 0
    for i, w in enumerate(W):
        if w == 2:
            if order[i + 1] == g.TAU[order[i]]:
                tau_j += 1
            elif order[i + 1] == g.SIG[g.SIG[order[i]]]:
                dirty_j += 1
    dirty_any = sum(1 for i, w in enumerate(W)
                    if w != 1 and not g.clean(order[i], order[i + 1]))
    return dict(P=P, G=G, S=S, H=Hh, L=L,
                H1_passes_partition_hexagons=(H1 and part),
                H2_nu_is_a_permutation=H2,
                H3_resource_identity=H3,
                w2_clean_tau=tau_j, w2_dirty_sigma2=dirty_j,
                dirty_joints_total=dirty_any)


if __name__ == "__main__":
    D = "/tmp/claude-0/-home-user-supersequence-n6-research/0161dc0f-40e0-56e3-8c56-97df10c350b4/scratchpad/nr6"
    out = {}
    for n in (3, 4):
        g = Geo(n)
        tot = Counter()
        checked = 0
        for f in sorted(glob.glob(f"{D}/sol_n{n}_b*.jsonl")):
            for line in open(f):
                d = json.loads(line)
                if "sol" not in d:
                    continue
                walk = d["sol"]
                if len(walk) == g.N:
                    continue                       # no repeats: nothing to test
                a = analyse_order(g, hamilton_order(g, walk))
                checked += 1
                tot["H1"] += a["H1_passes_partition_hexagons"]
                tot["H2"] += a["H2_nu_is_a_permutation"]
                tot["H3"] += a["H3_resource_identity"]
                tot["with_dirty_w2"] += (a["w2_dirty_sigma2"] > 0)
                tot["with_any_dirty_joint"] += (a["dirty_joints_total"] > 0)
        out[f"n{n}"] = dict(repeat_bearing_walks_checked=checked,
                            H1_holds=tot["H1"], H2_holds=tot["H2"],
                            H3_holds=tot["H3"],
                            walks_using_a_dirty_weight2_joint=tot["with_dirty_w2"],
                            walks_with_any_dirty_joint=tot["with_any_dirty_joint"],
                            all_H1_H2_H3=(tot["H1"] == tot["H2"] == tot["H3"] == checked))
    (ROOT / "outputs" / "rr_nr6_hamorder_142.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False, indent=1))
