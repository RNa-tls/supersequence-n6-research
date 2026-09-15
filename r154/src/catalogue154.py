#!/usr/bin/env python3
"""Round 154 Step 1 -- every locally legal beta-edge type, from first principles.

For every ordered pair (v, t) of the 720 words, compute the overlap gap from
end(v) to t and classify it.  This reproduces the round-145 joint catalogue
without reading it, and records what each type does to the hexagon, the orbit
and the phase -- the facts the degree/topology argument needs.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r154" / "src"))
from beta_defs154 import (build, sigma, tau, end, omega, classes,   # noqa: E402
                          hidden_windows, joint_type)


def main():
    n = 6
    W, IDX = build(n)
    HEX, nh = classes(W, sigma)
    ORB, nq = classes(W, tau)
    PHASE = [None] * len(W)
    for q in range(nq):
        rep = next(i for i in range(len(W)) if ORB[i] == q)
        x = W[rep]
        for k in range(5):
            PHASE[IDX[x]] = k
            x = tau(x)

    per_source = Counter()
    profile = {}
    excluded = Counter()
    for vi, v in enumerate(W):
        e = end(v)
        cnt = Counter()
        for ti, t in enumerate(W):
            g = omega(e, t, n)
            if g == 1:
                excluded["gap1_inside_a_pass"] += 1
                continue
            ty, _ = joint_type(v, t, n)
            cnt[ty] += 1
            hid = hidden_windows(e, t, g, n)
            key = ty
            p = profile.setdefault(key, dict(
                count=0, gaps=set(), hidden=set(),
                same_hexagon=0, same_orbit=0, phase_steps=Counter(),
                target_is_source=0, target_is_end=0))
            p["count"] += 1
            p["gaps"].add(g)
            p["hidden"].add(len(hid))
            p["same_hexagon"] += HEX[ti] == HEX[vi]
            p["same_orbit"] += ORB[ti] == ORB[vi]
            if ORB[ti] == ORB[vi]:
                p["phase_steps"][(PHASE[ti] - PHASE[vi]) % 5] += 1
            p["target_is_source"] += ti == vi
            p["target_is_end"] += t == e
        per_source[tuple(sorted(cnt.items()))] += 1

    out = dict(
        words=len(W), hexagons=nh, orbits=nq,
        orbit_sizes=sorted({sum(1 for i in range(len(W)) if ORB[i] == q)
                            for q in range(nq)}),
        excluded_pairs=dict(excluded),
        out_degree_profiles={str(k): v for k, v in per_source.items()},
        identical_for_every_source=len(per_source) == 1,
        types={k: dict(count_per_source=v["count"] // len(W),
                       total=v["count"], gaps=sorted(v["gaps"]),
                       hidden_window_counts=sorted(v["hidden"]),
                       always_same_hexagon=v["same_hexagon"] == v["count"],
                       never_same_hexagon=v["same_hexagon"] == 0,
                       always_same_orbit=v["same_orbit"] == v["count"],
                       never_same_orbit=v["same_orbit"] == 0,
                       phase_steps_when_same_orbit=dict(v["phase_steps"]))
               for k, v in sorted(profile.items())})
    tot = sum(v["count"] for v in profile.values())
    out["total_classified_pairs"] = tot
    out["total_pairs"] = len(W) * len(W)
    out["accounted"] = tot + sum(excluded.values()) == len(W) * len(W)
    out["unclassified_w2_or_w3"] = profile.get("?w2", {}).get("count", 0)
    (ROOT / "r154" / "certs" / "catalogue_154.json").write_text(
        json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "types"},
                     indent=1, default=str))
    for k, v in out["types"].items():
        print(f"  {k:10s} per source {v['count_per_source']:4d}  gaps "
              f"{v['gaps']}  hidden {v['hidden_window_counts']}  "
              f"sameHex={v['always_same_hexagon']}/{v['never_same_hexagon']}  "
              f"sameOrb={v['always_same_orbit']}/{v['never_same_orbit']}  "
              f"phase{v['phase_steps_when_same_orbit']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
