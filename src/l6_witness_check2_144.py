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


# weight-4 joints out of end(v), rebuilt here from scratch
P6, IDX, SG = MC.P6, MC.IDX, MC.SG


def _end(v):
    y = P6[v]
    return (y[5],) + y[:5]                       # sigma^{-1}(v)


def _omega(a, b):
    for k in range(1, 6):
        if a[k:] == b[:6 - k]:
            return k
    return 6


def heavy4(v):
    """The weight-exactly-4 shortest connectors out of the full-pass endpoint."""
    e = _end(v)
    out = []
    for t in range(NP):
        b = P6[t]
        if e[4:] == b[:2] and _omega(e, b) == 4:
            out.append(t)
    return out


def enumerate_witnesses(runs, ports, node_cap=200_000_000, start=0,
                        forbid_hex=frozenset(), forbid_orb=frozenset()):
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
    if ORB[start] in forbid_orb or HEX[start] in forbid_hex:
        return [], 0
    x, run, hx = start, [], set()
    for ln in range(1, 6):
        if HEX[x] in hx or HEX[x] in forbid_hex:
            break
        run.append(x)
        hx.add(HEX[x])
        if 5 - ln <= D and ln <= ports:
            rec(run[-1], list(run), frozenset(hx) | frozenset(forbid_hex),
                frozenset({ORB[start]}) | frozenset(forbid_orb),
                ln, 1, 5 - ln)
        x = E[x]
    return out, nodes[0]


def q2_witnesses():
    """Q2 independently: 92 ports, deficit 8, ONE weight-4 heavy joint.

    With b = 0 the heavy joint enters a fresh orbit, so it splits the component
    into two heavy-free hex-simple chains with disjoint hexagons and orbits,
    P1 + P2 = 92 and D1 + D2 = 8.  Since P_i <= C(0, D_i) and the Python table
    gives C(0,0..8) = 20,20,33,33,46,46,49,58,62, the ONLY split reaching 92 is
    D1 = D2 = 4 with P1 = P2 = 46.  So enumerate the 46-port deficit-4 chains
    from port 0, and for each of the 24 weight-4 targets of its last port the
    46-port deficit-4 chains that avoid the first chain's footprint.
    """
    tab = [UB[d] for d in range(9)]
    best = max(tab[d1] + tab[8 - d1] for d1 in range(9))
    assert best == 92 and [d for d in range(9) if tab[d] + tab[8 - d] == 92] == [4]
    first, n1 = enumerate_witnesses(10, 46)
    wit, n2 = [], 0
    for ch in first:
        hx, ob = {HEX[v] for v in ch}, {ORB[v] for v in ch}
        for t in heavy4(ch[-1]):
            if HEX[t] in hx or ORB[t] in ob:
                continue
            second, k = enumerate_witnesses(10, 46, start=t, forbid_hex=hx,
                                            forbid_orb=ob)
            n2 += k
            for s2 in second:
                wit.append(ch + s2)
    return wit, n1, n2, len(first)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "q2":
    wit, n1, n2, nfirst = q2_witnesses()
    canon = sorted(tuple(w) for w in wit)
    res = dict(mode="q2", ports=92, deficit=8, heavy=1,
               first_halves=nfirst, nodes_first=n1, nodes_second=n2,
               witnesses=len(canon),
               digest=__import__("hashlib").sha256(
                   json.dumps([list(x) for x in canon],
                              separators=(",", ":")).encode()).hexdigest())
    (ROOT / "outputs" / "rr_l6_witness2_q2_144.json").write_text(
        json.dumps(dict(**res, chains=[list(w) for w in canon]),
                   ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False))
    sys.exit(0)

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
