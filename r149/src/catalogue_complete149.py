#!/usr/bin/env python3
"""Round 149 A/E -- COMPLETENESS of the searcher's move catalogue.

The capacity searcher can only bound reality if every step a real chain can
take is one of its moves.  The C catalogue builder classifies a target and
`continue`s when nothing matches, so a silently dropped connector would be a
move the searcher cannot make -- and then its maximum would not bound anything.

This enumerates ALL 720 x 720 ordered pairs, computes the max-overlap distance
from end(v) = sigma^{-1}(v) to the target, and checks that every pair the
searcher must be able to take is classified.  It also records the structural
facts the charging argument uses.
"""
from __future__ import annotations
import itertools, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r147" / "src"))
import catalogue147 as C                                            # noqa: E402

PERMS, IDX, HEX, ORB = C.PERMS, C.IDX, C.HEX, C.ORB
sig, tau, end, gap = C.sigma, C.tau, C.end, C.gap


def main():
    free, dA, dB, paid, kind, heavy = C.catalogue()
    kept = {2: 0, 3: 0}
    dropped = {2: [], 3: []}
    gapdist = {}
    excluded = []
    for vi, v in enumerate(PERMS):
        e = end(v)
        for ti, t in enumerate(PERMS):
            g = gap(e, t)
            gapdist[g] = gapdist.get(g, 0) + 1
            if g >= 4:
                if t == v or t == e:
                    excluded.append((v, t, g))
                continue
            if g < 2:
                dropped.setdefault(g, []).append((v, t, g))
                continue
            spell = e + t[6 - g:]
            hid = [IDX[spell[o:o + 6]] for o in range(1, g)
                   if len(set(spell[o:o + 6])) == 6]
            hit = None
            if g == 2:
                if not hid:
                    hit = "freeE"
                elif len(hid) == 1 and hid[0] == vi:
                    hit = "dirtyA"
            else:
                if len(hid) == 2 and hid[0] == vi and HEX[ti] == HEX[vi]:
                    hit = "dirtyB"
                else:
                    k = -1
                    if not hid:
                        d0 = [e[:3].index(t[3 + j]) if t[3 + j] in e[:3] else -1
                              for j in range(3)]
                        code = 100 * d0[0] + 10 * d0[1] + d0[2]
                        k = {120: 0, 201: 1, 210: 2}.get(code, -1)
                    elif len(hid) == 1 and hid[0] == vi:
                        k = 3
                    elif len(hid) == 1 and sig(PERMS[hid[0]]) == t:
                        k = 4
                    if k >= 0:
                        hit = f"paid{k}"
            if hit:
                kept[g] += 1
            else:
                dropped[g].append((v, t, g, [PERMS[x] for x in hid]))
    out = dict(
        gap_distribution=gapdist,
        weight2_classified=kept[2], weight2_dropped=len(dropped[2]),
        weight3_classified=kept[3], weight3_dropped=len(dropped[3]),
        heavy_excluded_pairs=len(excluded),
        heavy_exclusion_reason=(
            "t == v and t == end(v) are the only pairs the heavy list omits. "
            "Both are impossible for a real joint: t is a FIRST occurrence and "
            "both v and end(v) are windows already written when the joint is "
            "taken."),
        # structural facts the charging argument uses
        freeE_is_tau=all(PERMS[free[i]] == tau(PERMS[i]) for i in range(720)),
        dirtyA_is_sigma=all(PERMS[dA[i]] == sig(PERMS[i]) for i in range(720)),
        dirtyB_is_sigma_squared=all(PERMS[dB[i]] == sig(sig(PERMS[i]))
                                    for i in range(720)),
        dirtyA_same_hexagon=all(HEX[dA[i]] == HEX[i] for i in range(720)),
        dirtyB_same_hexagon=all(HEX[dB[i]] == HEX[i] for i in range(720)),
        paid_never_lands_in_source_hexagon=all(HEX[paid[i][j]] != HEX[i]
                                               for i in range(720)
                                               for j in range(5)),
        heavy_landing_in_source_hexagon=sum(
            1 for i in range(720) for t, c in heavy[i] if HEX[t] == HEX[i]),
        per_source_counts=dict(free=1, dirtyA=1, dirtyB=1, paid=5,
                               heavy=len(heavy[0])),
        ok=(not dropped[2] and not dropped[3]))
    (ROOT / "r149" / "certs" / "catalogue_complete_149.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
