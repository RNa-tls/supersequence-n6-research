#!/usr/bin/env python3
"""Round 171 -- grouping the 33 by what would actually dominate their states.

The pilots showed the (p) bound sitting on the analytic fallback for 36 to 83
percent of states, and the reason is structural: every remaining cell has
b >= 1 while both existing ladders are b = 0, and a lookup needs the certified
cell to dominate the state in EVERY component, the first included.

The naive repair is a ladder per target, at the target's own shape with
smaller d -- that is what Family H and Family A2 were.  It is also the
expensive repair, because all 32 remaining b >= 1 cells carry DISTINCT
(a, bb, e, h) shapes, so a same-shape ladder serves exactly one target and
thirty-two ladders would have to be built.

The cheaper structure is a shared one.  For a target T, the states reachable
have every component bounded by T's, so a rung at the COMPONENTWISE MAXIMUM of
a group of targets dominates the states of all of them at once.  The trade is
real and runs the other way: a rung at a larger shape carries a larger
capacity, hence a weaker bound, hence less pruning.  Which effect wins is a
measurement, not a deduction, so this module only proposes the groups and the
shape each would need; it does not assume the shared ladder is worth building.

Groups are formed on the mask pattern (which of bb, e, h are nonzero) within a
b level, because those flags are restrictions that change what can dominate
what, while `a` and `d` vary continuously inside a group.
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def cellstr(K):
    return "|".join(map(str, K))


def main():
    pil = json.loads((ROOT / "r171" / "certs" / "pilots_171.json").read_text())
    doss = json.loads((ROOT / "r171" / "certs"
                       / "remaining_171.json").read_text())
    S = {d["cell"]: d["safe_upper_bound_S"] for d in doss["dossier"]}
    cls = {r["cell"]: r["classification"] for r in pil["rows"]}
    fbf = {r["cell"]: r["fallback_fraction"] for r in pil["rows"]}

    cells = [parse(r["cell"]) for r in pil["rows"] if not r["completed"]]
    done = [parse(r["cell"]) for r in pil["rows"] if r["completed"]]

    # group by (b, which of bb/e/h are nonzero)
    groups = defaultdict(list)
    for K in cells:
        b, d, a, bb, e, h = K
        groups[(b, bb > 0, e > 0, h > 0)].append(K)

    out_groups = []
    for key in sorted(groups):
        b, has_bb, has_e, has_h = key
        members = sorted(groups[key], key=lambda K: K[1])
        # componentwise max over the group: one rung shape dominating all
        mx = [max(K[i] for K in members) for i in range(6)]
        shape = (b, None, mx[2], mx[3], mx[4], mx[5])
        dmin = min(K[1] for K in members)
        name = (f"b{b}"
                + ("_bb" if has_bb else "")
                + ("_e" if has_e else "")
                + ("_h" if has_h else "")
                + f"_a{mx[2]}")
        out_groups.append(dict(
            family=name,
            b_level=b,
            mask=dict(bb=has_bb, e=has_e, h=has_h),
            members=[cellstr(K) for K in members],
            member_count=len(members),
            safe_bounds={cellstr(K): S[cellstr(K)] for K in members},
            classifications={cellstr(K): cls[cellstr(K)] for K in members},
            worst_fallback_fraction=max(fbf[cellstr(K)] or 0 for K in members),
            dominating_rung_shape=dict(
                b=shape[0], a=shape[2], bb=shape[3], e=shape[4], h=shape[5],
                d="varies: the ladder rungs"),
            rung_d_range=[2, max(K[1] for K in members) - 1],
            deepest_member_d=max(K[1] for K in members),
            shallowest_member_d=dmin,
            serves="one rung at this shape dominates the states of every "
                   "member, because each member's states are bounded "
                   "componentwise by the member and the shape is the "
                   "componentwise max over members",
            caveat="a larger shape carries a larger capacity and therefore a "
                   "weaker bound; whether the shared ladder prunes enough is "
                   "measured, not assumed"))
        print(f"  {name:<14} b={b} members={len(members):<3} "
              f"shape a={mx[2]} bb={mx[3]} e={mx[4]} h={mx[5]}  "
              f"d in 2..{max(K[1] for K in members) - 1}  "
              f"worst_fb={max(fbf[cellstr(K)] or 0 for K in members)}",
              flush=True)

    out = dict(
        remaining_cells=len(cells),
        already_provable=[cellstr(K) for K in done],
        families=len(out_groups),
        why_not_one_ladder_per_target=(
            f"all {len(cells)} remaining cells carry distinct (a,bb,e,h) "
            "shapes, so a same-shape ladder serves exactly one target"),
        grouping_rule="within a b level, group by which of bb/e/h are "
                      "nonzero; those flags are restrictions that change the "
                      "domination relation, while a and d vary inside a group",
        groups=out_groups,
        next_step="validate the shared-ladder idea on the largest family "
                  "before building any of them: a weaker shared bound may "
                  "prune too little to pay for itself",
        ok=True,
    )
    (ROOT / "r171" / "certs" / "families_171.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print()
    print(json.dumps({k: v for k, v in out.items() if k != "groups"},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
