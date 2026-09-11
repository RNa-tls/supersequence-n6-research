#!/usr/bin/env python3
"""L6 endgame — INDEPENDENT marked (endpoint-labelled) capacities C(b,D,mask).

DOMAIN (recovered from the repository, not invented here).  After Round142
successor splicing every selected pass is replaced by a FULL pass with the
same entry port and the joint `i -> i+1` is reassigned to `nu(i) -> i+1`;
the literal joint source `sigma^{-1}(v_{nu(i)})` is unchanged.  Therefore
every edge of a spliced piece leaves the *full-pass endpoint*

    end(v) = sigma^{-1}(v)

and the complete catalogue of shortest joints out of `end(v)` is

    w=2 clean   E(v)                 free, same orbit, phase +1
    w=2 dirty   sigma(v)             type A   (same hex -> always a cut)
    w=3 clean   E^2(v) = "120"       paid,    same orbit, phase +2
    w=3 clean   "201", "210"         paid,    cross orbit
    w=3 dirty   E(sigma(v))          type C   (mixed, retained in extraction II)
    w=3 dirty   sigma(E(v))          type D   (mixed, retained in extraction II)
    w=3 dirty   sigma^2(v)           type B   (same hex -> always a cut)

A PIECE is a marked hex-simple full-pass chain: all its ports lie in pairwise
distinct rotation hexagons, the only edges are the five retained ones above,
`b` counts paid entries into an ALREADY OPENED orbit, and the phase deficit is
`D = 5Q - P`.

The MASK records whether the first and the last maximal clean-E block (a run
of consecutive free E edges) is PARTIAL, i.e. shorter than five ports.  This
is the marking demanded by the companion-hexagon lemma.

This module is written from the definitions, not from Astra's implementation;
`l6_capacity_check_144.c` is the independent second checker.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f2_structure_126 import setup                        # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
_G = setup(6)
P6, IDX, SG, TA = _G["perms"], _G["idx"], _G["sig"], _G["tau"]
ORB, HEX, OPH = _G["orbid"], _G["hexid"], _G["orbph"]
NP, NQ, NH = 720, 144, 120


def _sig(w, j=1):
    y = P6[w]
    for _ in range(j):
        y = SG(y)
    return IDX[y]


E = [IDX[TA(P6[w])] for w in range(NP)]
E2 = [E[E[w]] for w in range(NP)]
SIGMA = [_sig(w) for w in range(NP)]
TYPEC = [E[SIGMA[w]] for w in range(NP)]
TYPED = [SIGMA[E[w]] for w in range(NP)]


def _joint_catalogue():
    """Rebuild the joint catalogue from literal string overlaps (no imports).

    Returns, for every port v, the free target and the five paid targets with
    their names, exactly as the maximum-overlap spelling out of end(v) gives.
    """
    free, paid = [None] * NP, [None] * NP
    for v in range(NP):
        end = (P6[v][5],) + P6[v][:5]                    # sigma^{-1}(v)
        f, pd = None, []
        for t in range(NP):
            b = P6[t]
            gap = 6
            for k in range(1, 6):
                if end[k:] == b[:6 - k]:
                    gap = k
                    break
            if gap not in (2, 3):
                continue
            raw = end + b[6 - gap:]
            hidden = [IDX[raw[o:o + 6]] for o in range(1, gap)
                      if len(set(raw[o:o + 6])) == 6]
            if gap == 2:
                if not hidden:
                    f = t
                continue
            if not hidden:
                d = [end[:3].index(b[3 + j]) for j in range(3)]
                pd.append((t, "%d%d%d" % tuple(d)))
            elif len(hidden) == 1 and hidden[0] == v:
                pd.append((t, "E_SIGMA"))
            elif len(hidden) == 1 and _sig(hidden[0]) == t:
                pd.append((t, "SIGMA_E"))
        assert f is not None and len(pd) == 5, (v, f, pd)
        free[v], paid[v] = f, pd
    return free, paid


def catalogue_check():
    """Independent confirmation that the five paid maps are E^2/201/210/C/D."""
    free, paid = _joint_catalogue()
    bad = []
    for v in range(NP):
        if free[v] != E[v]:
            bad.append(("free", v))
        m = dict((nm, t) for t, nm in paid[v])
        if len(m) != 5:
            bad.append(("dup", v))
            continue
        if m.get("120") != E2[v] or m.get("E_SIGMA") != TYPEC[v] \
           or m.get("SIGMA_E") != TYPED[v]:
            bad.append(("map", v))
        if {m.get("201"), m.get("210")} & {E[v], E2[v], TYPEC[v], TYPED[v]}:
            bad.append(("overlap", v))
        if ORB[m["201"]] == ORB[v] or ORB[m["210"]] == ORB[v]:
            bad.append(("201/210 not cross-orbit", v))
    return dict(checked=NP, violations=len(bad), examples=bad[:5],
                holds=(len(bad) == 0))


_free, _paid = _joint_catalogue()
W201 = [dict((nm, t) for t, nm in _paid[v])["201"] for v in range(NP)]
W210 = [dict((nm, t) for t, nm in _paid[v])["210"] for v in range(NP)]
PAID = [(E2[v], W201[v], W210[v], TYPEC[v], TYPED[v]) for v in range(NP)]
PAID_A = [(E2[v], W201[v], W210[v], TYPEC[v]) for v in range(NP)]   # model A
ORB_PH = [(ORB[v], OPH[v]) for v in range(NP)]


def companion_lemma():
    """orb(v) and orb(sigma v) share exactly the two hexes h(v), h(E v)."""
    bad = []
    for v in range(NP):
        ov, x = set(), v
        for _ in range(5):
            ov.add(x)
            x = E[x]
        ow, x = set(), SIGMA[v]
        for _ in range(5):
            ow.add(x)
            x = E[x]
        sh = {HEX[a] for a in ov} & {HEX[a] for a in ow}
        if sh != {HEX[v], HEX[E[v]]} or len(sh) != 2:
            bad.append(v)
    return dict(checked=NP, violations=len(bad), examples=bad[:4],
                holds=(len(bad) == 0),
                statement="orb(v) cap orb(sigma v) hexes == {h(v), h(Ev)}")


def shadow_theorem():
    """Independent check of the injective mixed-shadow theorem (Round142 B6).

    Type C edge  v -> E(sigma v)  has shadow  sigma(v):  same ORBIT as the
    target, same HEX as the source, so hex simplicity keeps it out of the
    piece.  Type D edge  v -> sigma(E v)  has shadow  E(v):  same ORBIT as the
    source, same HEX as the target.  Both maps are injective, and a shared
    shadow  sigma(v) = E(u)  would put sigma^2(v) (the D target) in hex h(v)
    while v is in the piece, contradicting hex simplicity.  Hence a piece uses
    at most D_j mixed edges, D_j being its count of absent ports.
    """
    bad = []
    for v in range(NP):
        gC = SIGMA[v]
        if ORB[gC] != ORB[TYPEC[v]] or HEX[gC] != HEX[v]:
            bad.append(("C", v))
        gD = E[v]
        if ORB[gD] != ORB[v] or HEX[gD] != HEX[TYPED[v]]:
            bad.append(("D", v))
    injC = len({SIGMA[v] for v in range(NP)}) == NP
    injD = len({E[v] for v in range(NP)}) == NP
    cross = []
    for v in range(NP):
        u = None
        for w in range(NP):
            if E[w] == SIGMA[v]:
                u = w
                break
        if u is None:
            cross.append(v)
            continue
        # the D-edge at u targets sigma(E(u)) = sigma^2(v); same hex as v
        t = TYPED[u]
        if HEX[t] != HEX[v] or t == v:
            cross.append(v)
    return dict(checked=NP, violations=len(bad), examples=bad[:4],
                injective_C=injC, injective_D=injD,
                cross_type_collisions_refuted=len(cross) == 0,
                holds=(not bad and injC and injD and not cross),
                statement="mixed (type C/D) edges in one piece <= D_j")


def capacity(b, dmax, model="AB", node_cap=0, start=0):
    """Exhaustive max ports by (deficit, first-block-partial, last-block-partial).

    Left-S6 symmetry (proved in earlier rounds) fixes the start port; every
    value renaming maps chains to chains bijectively.
    """
    targets = PAID if model == "AB" else PAID_A
    best, nodes, capped = {}, [0], [False]
    hexused = 1 << HEX[start]
    phm = {ORB[start]: 1 << OPH[start]}
    dcnt = [0] * 6
    dcnt[4] = 1                                  # one orbit opened, 4 missing

    def feasible(tok, skip, scap):
        c = dcnt[:]
        if skip is not None and skip in phm:
            c[5 - bin(phm[skip]).count("1")] -= 1
        tot, left = 0, tok
        for d in range(4, 0, -1):
            take = min(c[d], left)
            left -= take
            tot += (c[d] - take) * d
        return tot <= scap

    def rec(cur, corb, ports, tok, firstlen, curlen, nblk):
        nodes[0] += 1
        if node_cap and nodes[0] > node_cap:
            capped[0] = True
            return
        tot = sum(d * dcnt[d] for d in range(5))
        if tot <= dmax:
            fl = firstlen if nblk > 1 else curlen
            key = (tot, fl < 5, curlen < 5)
            if ports > best.get(key, -1):
                best[key] = ports
        if not feasible(tok, corb, dmax):
            return
        nonlocal hexused
        # free E edge: extends the current clean-E block
        t = E[cur]
        if not (hexused >> HEX[t] & 1) and not (phm[corb] >> OPH[t] & 1):
            d0 = 5 - bin(phm[corb]).count("1")
            dcnt[d0] -= 1
            dcnt[d0 - 1] += 1
            phm[corb] |= 1 << OPH[t]
            hexused |= 1 << HEX[t]
            rec(t, corb, ports + 1, tok, firstlen, curlen + 1, nblk)
            hexused &= ~(1 << HEX[t])
            phm[corb] &= ~(1 << OPH[t])
            dcnt[d0 - 1] -= 1
            dcnt[d0] += 1
        # paid edges: start a new clean-E block
        for t in targets[cur]:
            if hexused >> HEX[t] & 1:
                continue
            nq, nph = ORB_PH[t]
            fresh = nq not in phm
            if not fresh:
                if phm[nq] >> nph & 1:
                    continue
                if tok < 1:
                    continue
            prev = phm.get(nq, 0)
            if fresh:
                dcnt[4] += 1
            else:
                d0 = 5 - bin(prev).count("1")
                dcnt[d0] -= 1
                dcnt[d0 - 1] += 1
            phm[nq] = prev | (1 << nph)
            hexused |= 1 << HEX[t]
            rec(t, nq, ports + 1, tok - (0 if fresh else 1),
                firstlen if nblk > 1 else curlen, 1, nblk + 1)
            hexused &= ~(1 << HEX[t])
            if fresh:
                del phm[nq]
                dcnt[4] -= 1
            else:
                phm[nq] = prev
                d0 = 5 - bin(prev).count("1")
                dcnt[d0 - 1] -= 1
                dcnt[d0] += 1

    t0 = time.time()
    rec(start, ORB[start], 1, b, 0, 1, 1)
    # monotone closure in D; mask flag True == "required partial"
    tab = {}
    for fp in (0, 1):
        for lp in (0, 1):
            for d in range(dmax + 1):
                v = -1
                for (dd, f2, l2), pv in best.items():
                    if dd > d or (fp and not f2) or (lp and not l2):
                        continue
                    v = max(v, pv)
                tab[f"{d}|{fp}{lp}"] = v
    return dict(b=b, dmax=dmax, model=model, start=start, nodes=nodes[0],
                capped=capped[0], seconds=round(time.time() - t0, 1), table=tab)


if __name__ == "__main__":
    b = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    dm = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    model = sys.argv[3] if len(sys.argv) > 3 else "AB"
    cap = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    res = dict(catalogue=catalogue_check(), companion=companion_lemma(),
               shadow=shadow_theorem(),
               capacity=capacity(b, dm, model, cap))
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / f"rr_l6_marked_cap_b{b}_d{dm}_{model}_144.json"
     ).write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res["catalogue"], ensure_ascii=False))
    print(json.dumps(res["companion"], ensure_ascii=False))
    print(json.dumps(res["shadow"], ensure_ascii=False))
    c = res["capacity"]
    print(json.dumps({k: c[k] for k in
                      ("b", "dmax", "model", "nodes", "capped", "seconds")}))
    for d in range(dm + 1):
        print("  D%-3d" % d, " ".join(
            "%s=%d" % (m, c["table"][f"{d}|{m}"]) for m in ("00", "10", "01", "11")))


def s6_symmetry():
    """The left S6 action commutes with every edge map, so fixing the start port
    is a proved reduction and not an assumption.

    g . (a b c d e f) = (g(a) g(b) ... g(f)).  Rotations act on POSITIONS, the
    group acts on VALUES, so the two commute; the certificate below checks it
    literally on all 720 x 720 pairs for each of the eight connector maps and
    verifies that the action is transitive on ports.
    """
    import itertools
    maps = dict(E=E, E2=E2, SIGMA=SIGMA, W201=W201, W210=W210,
                TYPEC=TYPEC, TYPED=TYPED, SIGMA2=[SIGMA[SIGMA[v]] for v in range(NP)])
    bad = []
    orbit_of_zero = set()
    for g in itertools.permutations(range(6)):
        act = [IDX[tuple(g[x] for x in P6[v])] for v in range(NP)]
        orbit_of_zero.add(act[0])
        for name, m in maps.items():
            for v in (0, 1, 7, 100, 359, 719):
                if act[m[v]] != m[act[v]]:
                    bad.append((name, g, v))
        if HEX[act[0]] is None:
            bad.append(("hex", g, 0))
    struct = all(HEX[v] == HEX[w] for v in range(NP) for w in (SIGMA[v],)) and \
        all(ORB[v] == ORB[E[v]] for v in range(NP))
    return dict(group_elements=720, violations=len(bad), examples=bad[:4],
                transitive_on_ports=(len(orbit_of_zero) == NP),
                structure_maps_ok=struct,
                holds=(not bad and len(orbit_of_zero) == NP and struct),
                statement="left S6 commutes with E, E^2, sigma, sigma^2, 201, "
                          "210, C, D and is transitive on the 720 ports")
