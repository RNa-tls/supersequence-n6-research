#!/usr/bin/env python3
"""Independent re-enumeration of the 871 equality witnesses (second checker).

Materially different from `l6_chain_capacity_144.c`:

  * it advances a whole clean-E RUN at a time (choose the run length, then the
    paid connector) instead of one port at a time;
  * the geometry comes from `tau` and `sigma` algebraically, not from string
    overlap scanning;
  * occupancy is Python frozensets/ints, and the suffix bound is taken from the
    capacity table this repository computed in PYTHON
    (`l6_marked_capacity_144.capacity`), not from the C searcher's own table.

Domain for Q1: tokens b = 0, so every orbit is entered once and a run advances
only by free E edges (the intra-orbit 120 edge would cost a token).  Runs are
joined by the paid CROSS-orbit connectors 201, 210, E-sigma, sigma-E into a
FRESH orbit.  Exactly `runs` runs, `ports` ports, deficit `ports` vs
`5*runs - ports`.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import l6_marked_capacity_144 as MC                                # noqa: E402

E, W201, W210, TYPEC, TYPED = MC.E, MC.W201, MC.W210, MC.TYPEC, MC.TYPED
HEX, ORB, NP = MC.HEX, MC.ORB, MC.NP
CONN = [(W201, "201"), (W210, "210"), (TYPEC, "E_SIGMA"), (TYPED, "SIGMA_E")]

# suffix bound, computed here in Python (dmax 10 is cheap and was verified
# identical to the C searcher, node count included)
_PY = MC.capacity(0, 10, "AB")
assert _PY["capped"] is False
UB = [_PY["table"][f"{d}|00"] for d in range(11)]


def ub(d):
    return UB[d] if 0 <= d <= 10 else 120


def enumerate_witnesses(runs, ports, node_cap=50_000_000):
    """All chains with exactly `runs` runs and `ports` ports (b = 0, hex-simple)."""
    D = 5 * runs - ports
    out, nodes = [], [0]

    def rec(cur, trail, hexes, orbs, p, nrun, dc):
        nodes[0] += 1
        if nodes[0] > node_cap:
            raise RuntimeError("witness re-enumeration capped")
        if nrun == runs:
            if p == ports:
                out.append(list(trail))
            return
        # the suffix bound: remaining ports + 1 <= UB(D - dc + 4)
        if ports - p + 1 > ub(D - dc + 4):
            return
        if p + 5 * (runs - nrun) < ports:
            return
        for nxt, _name in CONN:
            t = nxt[cur]
            q = ORB[t]
            if q in orbs or HEX[t] in hexes:
                continue
            # walk the new run with free E steps
            x, run, hx = t, [], set()
            for ln in range(1, 6):
                if HEX[x] in hexes or HEX[x] in hx:
                    break
                run.append(x)
                hx.add(HEX[x])
                if dc + (5 - ln) <= D and p + ln <= ports:
                    rec(run[-1], trail + run, hexes | hx, orbs | {q},
                        p + ln, nrun + 1, dc + (5 - ln))
                x = E[x]
    # the first run starts at port 0
    x, run, hx = 0, [], set()
    for ln in range(1, 6):
        if HEX[x] in hx:
            break
        run.append(x)
        hx.add(HEX[x])
        if 5 - ln <= D and ln <= ports:
            rec(run[-1], list(run), frozenset(hx), frozenset({ORB[0]}),
                ln, 1, 5 - ln)
        x = E[x]
    return out, nodes[0]


if __name__ == "__main__":
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 22
    ports = int(sys.argv[2]) if len(sys.argv) > 2 else 96
    wit, nodes = enumerate_witnesses(runs, ports)
    canon = sorted(tuple(w) for w in wit)
    res = dict(runs=runs, ports=ports, deficit=5 * runs - ports,
               witnesses=len(canon), nodes=nodes,
               digest=__import__("hashlib").sha256(
                   json.dumps(canon, separators=(",", ":")).encode()).hexdigest())
    (ROOT / "outputs" / f"rr_l6_witness2_{runs}_{ports}_144.json").write_text(
        json.dumps(dict(**res, chains=[list(w) for w in canon]),
                   ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False))
