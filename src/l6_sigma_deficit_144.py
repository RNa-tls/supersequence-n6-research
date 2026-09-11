#!/usr/bin/env python3
"""L6 endgame — INDEPENDENT proof and verification of the sigma-deficit theorem.

THEOREM (Round 143, reproved here).  Consider a path of DISTINCT entry ports in
which each step is one of
    E-step      v -> E(v)        (E rotates the first five symbols)
    sigma-step  v -> sigma(v)    (sigma rotates all six)
    other       v -> u, landing in a rotation hex NOT previously visited,
and in which E-steps and "other" steps must also land in a fresh hex; only a
sigma target may re-enter an already visited hex.  Let
    Q = number of opened E-orbits,  P = number of ports,  D = 5Q - P,
    A = number of sigma steps,
    b = number of non-E entries into an already-opened E-orbit (not the first).
Then
    D + 5b >= A.

MY PROOF (does not use Astra's code).

Step 1 (transform identity).  E^{-1} sigma = sigma^{-1} E.
  With v = abcdef:  E(abcdef) = bcdeaf, so E^{-1}(w1..w6) = w5 w1 w2 w3 w4 w6.
  sigma(v) = bcdefa, hence E^{-1}sigma(v) = f b c d e a.
  E(v) = bcdeaf, hence sigma^{-1}E(v) = f b c d e a.   Equal.

Step 2 (missing-companion propagation).  Let a FULL E-run (all five ports)
start at s and end at E^4(s).  Its sigma successor starts at x = sigma E^4(s).
The E-predecessor of x is
    E^4(x) = E^{-1}(x) = E^{-1} sigma E^4(s) = sigma^{-1} E^5(s) = sigma^{-1}(s),
whose hex is h(s) -- already visited.  If that run has length four it visits
x,E(x),E^2(x),E^3(x) and OMITS exactly m = E^4(x).  The next sigma step gives
y = sigma E^3(x), whose omitted port (if again length four) is
    E^4(y) = E^{-1} sigma E^3(x) = sigma^{-1} E^4(x) = sigma^{-1}(m),
again of hex h(s).  So through any number of consecutive length-four runs the
omitted port keeps the hex h(s).  A following length-FIVE run must visit that
port as its fifth entry, reached by an E-step into the already visited hex
h(s) -- forbidden.  Hence the sigma-connected run-length pattern

    5, 4, ..., 4, 5      (any number of intermediate fours, including zero)

is IMPOSSIBLE.

Step 3 (counting).  Split the path into maximal E-runs of lengths 1<=r_i<=5.
Their number R satisfies R = Q + b, since each new run either opens its orbit
or is one of the b re-entries.  So the total run deficit is
    Delta = sum_i (5 - r_i) = 5R - P = D + 5b.
Partition the runs into maximal clusters joined by sigma steps; a cluster with
m runs carries exactly m-1 sigma steps, and A = sum (m_c - 1).
In one cluster let f be the number of length-5 runs and s the number of runs of
length <= 3.  By Step 2 two length-5 runs cannot be separated only by fours, so
between consecutive length-5 runs there is at least one run of length <= 3, and
those witnesses are disjoint: s >= f - 1.  Runs of length 4 give deficit 1 and
runs of length <= 3 give deficit >= 2, so
    sum_cluster (5-r_i) >= (m - f - s) + 2s = m - f + s >= m - 1.
Summing over clusters, Delta >= sum (m_c - 1) = A.  Hence D + 5b >= A.  QED
"""
from __future__ import annotations
import json, sys
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
N = 6
P6 = list(permutations(range(N)))
IDX = {p: i for i, p in enumerate(P6)}
NP = len(P6)
E = [IDX[p[1:N - 1] + p[:1] + p[N - 1:]] for p in P6]
SG = [IDX[p[1:] + p[:1]] for p in P6]
Einv = [0] * NP
for i, j in enumerate(E):
    Einv[j] = i
SGinv = [0] * NP
for i, j in enumerate(SG):
    SGinv[j] = i
HEX = [-1] * NP
ORB = [-1] * NP
h = o = 0
for i in range(NP):
    if HEX[i] < 0:
        x = i
        for _ in range(N):
            HEX[x] = h
            x = SG[x]
        h += 1
    if ORB[i] < 0:
        x = i
        for _ in range(N - 1):
            ORB[x] = o
            x = E[x]
        o += 1


def transform_identity():
    """E^{-1} sigma = sigma^{-1} E, on all 720 permutations."""
    bad = [v for v in range(NP) if Einv[SG[v]] != SGinv[E[v]]]
    ord_E = 1
    x = E[0]
    while x != 0:
        x = E[x]
        ord_E += 1
    return dict(checked=NP, violations=len(bad), holds=(len(bad) == 0),
                order_of_E=ord_E, orbits=o, hexagons=h,
                orbit_ports_lie_in_distinct_hexes=all(
                    len({HEX[x] for x in _orbit(v)}) == N - 1 for v in range(0, NP, 37)))


def _orbit(v):
    out = [v]
    x = E[v]
    while x != v:
        out.append(x)
        x = E[x]
    return out


def forbidden_pattern(max_fours=8):
    """Exhaustive: 5,4,...,4,5 always hits an already-visited hex.

    Builds the literal port sequence for every start s (all 720) and every
    number j of intermediate length-four runs, and checks that the final
    length-five run's FIFTH entry lands in a hex already visited.
    """
    fails = []
    checked = 0
    for s in range(NP):
        for j in range(0, max_fours + 1):
            seen_hex = set()
            # full run of five from s
            cur = s
            run = [s]
            for _ in range(4):
                cur = E[cur]
                run.append(cur)
            for x in run:
                seen_hex.add(HEX[x])
            ok = True
            # j runs of length four
            for _ in range(j):
                cur = SG[run[-1]]
                run = [cur]
                for _ in range(3):
                    cur = E[cur]
                    run.append(cur)
                for x in run:
                    seen_hex.add(HEX[x])
            # final run of five
            cur = SG[run[-1]]
            run = [cur]
            for _ in range(4):
                cur = E[cur]
                run.append(cur)
            fifth = run[4]
            checked += 1
            # the fifth entry is reached by an E step and must be fresh
            if HEX[fifth] not in seen_hex:
                fails.append((s, j))
                ok = False
            # and the theory says its hex is exactly h(s)
            if HEX[fifth] != HEX[s]:
                fails.append(("hex!=h(s)", s, j))
    return dict(starts=NP, max_intermediate_fours=max_fours, cases=checked,
                violations=len(fails), examples=fails[:4],
                lemma_holds=(len(fails) == 0),
                claim="the fifth entry of the closing five-run has hex h(s), "
                      "already visited, and is reached by an E step")


def brute_force(maxP=13, node_cap=60_000_000):
    """Adversarial exhaustive search of the relaxation; checks D + 5b >= A.

    'Other' steps are allowed to ANY unvisited vertex with a fresh hex, which is
    strictly more permissive than the stated weight-three catalog, so a pass here
    is a stronger statement than the theorem requires.
    """
    worst = None
    nodes = [0]
    capped = [False]
    visitedv = [False] * NP
    seenhex = {}
    orbopen = {}

    def rec(v, P, Q, A, b):
        nodes[0] += 1
        if nodes[0] > node_cap:
            capped[0] = True
            return
        D = 5 * Q - P
        slackv = D + 5 * b - A
        nonlocal worst
        if worst is None or slackv < worst[0]:
            worst = (slackv, P, Q, A, b)
        if P >= maxP:
            return
        for kind in range(3):
            if kind == 0:                       # E step
                cands = [E[v]]
            elif kind == 1:                     # sigma step
                cands = [SG[v]]
            else:                               # other: fresh hex, any target
                cands = [u for u in range(NP)
                         if u != E[v] and u != SG[v] and not visitedv[u]
                         and HEX[u] not in seenhex]
            for u in cands:
                if visitedv[u]:
                    continue
                if kind != 1 and HEX[u] in seenhex:
                    continue                    # only sigma may revisit a hex
                newQ = Q + (0 if ORB[u] in orbopen else 1)
                newb = b + (1 if (kind != 0 and ORB[u] in orbopen) else 0)
                visitedv[u] = True
                seenhex[HEX[u]] = seenhex.get(HEX[u], 0) + 1
                orbopen[ORB[u]] = orbopen.get(ORB[u], 0) + 1
                rec(u, P + 1, newQ, A + (1 if kind == 1 else 0), newb)
                visitedv[u] = False
                orbopen[ORB[u]] -= 1
                if not orbopen[ORB[u]]:
                    del orbopen[ORB[u]]
                seenhex[HEX[u]] -= 1
                if not seenhex[HEX[u]]:
                    del seenhex[HEX[u]]
                if capped[0]:
                    return

    v0 = 0
    visitedv[v0] = True
    seenhex[HEX[v0]] = 1
    orbopen[ORB[v0]] = 1
    rec(v0, 1, 1, 0, 0)
    return dict(maxP=maxP, nodes=nodes[0], capped=capped[0],
                min_slack=worst[0],
                witness_at_min=dict(P=worst[1], Q=worst[2], A=worst[3], b=worst[4]),
                theorem_holds=(worst[0] >= 0),
                note="slack = D + 5b - A; theorem is slack >= 0")


def sharpness():
    """The report's sharp controls: (5,4) gives (A,b,D)=(1,0,1); (5,3,5) gives (2,0,2)."""
    out = []
    for lens in ((5, 4), (5, 3, 5)):
        s = 0
        ports = []
        seen = set()
        A = 0
        cur = s
        first = True
        for L in lens:
            if not first:
                cur = SG[ports[-1]]
                A += 1
            run = [cur]
            for _ in range(L - 1):
                cur = E[cur]
                run.append(cur)
            ports += run
            first = False
        Q = len({ORB[x] for x in ports})
        P = len(ports)
        out.append(dict(lengths=list(lens), P=P, Q=Q, D=5 * Q - P, A=A,
                        distinct_ports=(len(set(ports)) == P),
                        slack=5 * Q - P - A))
    return out


if __name__ == "__main__":
    res = dict(transform=transform_identity(),
               forbidden_pattern=forbidden_pattern(),
               sharp_controls=sharpness(),
               brute_force=brute_force())
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "rr_l6_sigma_deficit_144.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))
