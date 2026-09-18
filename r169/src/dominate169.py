#!/usr/bin/env python3
"""Round 169 phases 2, 4 and 10 -- the domination graph and what it explains.

A `(p)` leaf at a search node is justified by the minimum capacity among
CERTIFIED cells that dominate the node's budget vector componentwise.  Two
facts shape the graph.

  * Every certified cell dominates the all-zero budget vector, so every
    certified cell can prune SOMEWHERE in every search.  Counting dominators
    is therefore meaningless on its own.
  * What decides the cost is whether a dominator exists NEAR THE ROOT, where
    pruning removes an enormous subtree.  At the root of a search in cell
    (b, d, a, bb, e, h) the budget vector is

        s_root = (b, d + 5b, a, bb, e, h)

    because deficit starts at 4 and d* = d - deficit + 4 + 5*tok.

So the graph is built at levels: for each target and each token level j <= b,
the state vector s(j) = (j, d + 5j, a, bb, e, h) is the hardest state the
search can present at that level, and a cell dominating it can prune there.

Nothing in this module reads a capacity for PROOF purposes.  The round-152
table is used only to enumerate which cells could be certified at all and at
what value, which is planning information (phase 15).
"""
from __future__ import annotations
import hashlib, json, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r169" / "src"))
from state169 import (certified_from_proof_objects, dominates, ub,   # noqa
                      UBFALL, sha)

GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def cellstr(K):
    return "|".join(map(str, K))


def s_level(T, j):
    """hardest budget vector the search in T can present at token level j"""
    return (j, T[1] + 5 * j, T[2], T[3], T[4], T[5])


def fallback(s):
    return UBFALL + s[2] + s[3] + s[4]


def features(T, cert, universe):
    """everything the scheduler is allowed to know about a target."""
    f = dict(cell=cellstr(T), b=T[0], d=T[1], a=T[2], bb=T[3], e=T[4], h=T[5])
    root = s_level(T, T[0])
    f["s_root"] = list(root)
    f["root_fallback"] = fallback(root)
    cd = [K for K in cert if dominates(K, root) and cert[K] < fallback(root)]
    ud = [K for K in universe
          if dominates(K, root) and universe[K] < fallback(root)]
    f["certified_root_dominators"] = len(cd)
    f["universe_root_dominators"] = len(ud)
    f["best_certified_root_bound"] = min([cert[K] for K in cd], default=None)
    f["best_possible_root_bound"] = min([universe[K] for K in ud], default=None)
    f["root_bound_gap"] = (
        None if f["best_possible_root_bound"] is None
        else (f["best_certified_root_bound"] or f["root_fallback"])
        - f["best_possible_root_bound"])
    # how far down the token ladder the certified set keeps a real bound
    lvl = []
    for j in range(T[0], -1, -1):
        s = s_level(T, j)
        lvl.append(dict(j=j, certified_ub=ub(cert, s), fallback=fallback(s),
                        binding=ub(cert, s) < fallback(s)))
    f["levels"] = lvl
    f["deepest_level_with_a_certified_bound"] = next(
        (x["j"] for x in lvl if x["binding"]), None)
    f["levels_without_a_certified_bound"] = sum(
        1 for x in lvl if not x["binding"])
    return f


def main():
    st = json.loads((ROOT / "r169" / "certs" / "state_169.json").read_text())
    assert st["ok"]
    CERT, _prov = certified_from_proof_objects()
    universe = {parse(r["cell"]): r["cap"] for r in json.loads(
        (ROOT / "r152" / "certs" / "verify_all_c152.json").read_text())["rows"]
        if r["status"] in GOOD}
    remaining = [parse(c) for c in st["remaining_cells"]]

    graph = {cellstr(T): features(T, CERT, universe) for T in remaining}

    # ---------- which missing dominators would restore a root bound
    need = defaultdict(list)
    for T in remaining:
        root = s_level(T, T[0])
        if any(dominates(K, root) and CERT[K] < fallback(root) for K in CERT):
            continue
        for K in universe:
            if dominates(K, root) and universe[K] < fallback(root):
                need[cellstr(K)].append(cellstr(T))
    leverage = sorted(((k, len(v)) for k, v in need.items()),
                      key=lambda kv: (-kv[1], kv[0]))

    # ---------- validation material for phase 10
    gen = json.loads((ROOT / "r168" / "certs"
                      / "generation_batch1_168.json").read_text())
    plan = {r["cell"]: r["search_nodes"] for r in json.loads(
        (ROOT / "r167" / "certs"
         / "round168_plan_167.json").read_text())["generation_plan"]["order"]}
    # the certified set AS IT WAS when round 168 generated: the 75 cells of
    # the three historical batches, not the 93 of today
    sys.path.insert(0, str(ROOT / "r168" / "src"))
    from verify168 import scan_headers, read_text                  # noqa
    old = {}
    for rel in ("r164/certs/extree_prefix_164.txt.gz",
                "r166/certs/extree_batch2_166.txt.gz",
                "r166/certs/extree_batch3_166.txt.gz"):
        text, _c, _p = read_text(rel)
        for cell, cap in scan_headers(text)[2]:
            old[cell] = cap
    obs = []
    for r in gen["rows"]:
        if r["status"] != "TREE_BUILT":
            continue
        T = parse(r["cell"])
        f = features(T, old, universe)
        obs.append(dict(cell=r["cell"], proof_nodes=r["proof_nodes"],
                        historical=plan.get(r["cell"]),
                        inflation=round(r["proof_nodes"] / plan[r["cell"]], 3),
                        certified_root_dominators=f["certified_root_dominators"],
                        best_certified_root_bound=f["best_certified_root_bound"],
                        root_fallback=f["root_fallback"],
                        levels_without_a_certified_bound=
                        f["levels_without_a_certified_bound"],
                        deepest_level_with_a_certified_bound=
                        f["deepest_level_with_a_certified_bound"]))
    for c, n in (("0|14|0|0|0|1", 255658530), ("0|17|2|0|0|0", None)):
        T = parse(c)
        f = features(T, old, universe)
        obs.append(dict(cell=c, proof_nodes=n, historical=plan.get(c),
                        inflation=(round(n / plan[c], 3) if n else None),
                        certified_root_dominators=f["certified_root_dominators"],
                        best_certified_root_bound=f["best_certified_root_bound"],
                        root_fallback=f["root_fallback"],
                        levels_without_a_certified_bound=
                        f["levels_without_a_certified_bound"],
                        deepest_level_with_a_certified_bound=
                        f["deepest_level_with_a_certified_bound"]))

    out = dict(
        inputs={p: sha(p) for p in
                ("r169/certs/state_169.json",
                 "r168/certs/generation_batch1_168.json",
                 "r167/certs/round168_plan_167.json",
                 "r152/certs/verify_all_c152.json")},
        definitions=dict(
            s_root="(b, d + 5b, a, bb, e, h) -- the root budget vector, "
                   "because deficit starts at 4 and d* = d - deficit + 4 + "
                   "5*tok",
            s_level="(j, d + 5j, a, bb, e, h) -- the hardest vector the "
                    "search can present at token level j",
            why_counting_is_useless="every certified cell dominates the "
                                    "all-zero vector, so every certified "
                                    "cell prunes SOMEWHERE; what matters is "
                                    "whether one dominates near the root"),
        targets=len(graph),
        targets_without_a_certified_root_bound=sum(
            1 for f in graph.values()
            if f["best_certified_root_bound"] is None),
        targets_with_no_possible_root_bound=sum(
            1 for f in graph.values()
            if f["best_possible_root_bound"] is None),
        highest_leverage_missing_dominators=[
            dict(cell=k, targets_it_would_give_a_root_bound=n,
                 capacity=universe[parse(k)])
            for k, n in leverage[:25]],
        round_168_observations=sorted(obs, key=lambda r: -(r["inflation"] or 0)),
        graph=graph,
    )
    (ROOT / "r169" / "certs" / "domination_graph_169.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    show = {k: v for k, v in out.items() if k not in ("graph", "inputs")}
    show["round_168_observations"] = show["round_168_observations"][:6]
    show["highest_leverage_missing_dominators"] = \
        show["highest_leverage_missing_dominators"][:8]
    print(json.dumps(show, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
