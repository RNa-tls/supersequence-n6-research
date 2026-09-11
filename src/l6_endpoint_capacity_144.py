#!/usr/bin/env python3
"""L6 endgame — INDEPENDENT endpoint-marked capacities C(b, D, mask).

A marked full-pass chain (one extracted piece):
  * entry ports, all in DISTINCT rotation hexes (hex-simple);
  * maximal E-runs (E = rotate first five symbols, phase +1 in an E-orbit);
  * runs joined by paid connectors: the clean weight-3 targets W3B/W3C, the
    intra-orbit phase jump (one token), the mixed types C: v -> E(sigma(v))
    and D: v -> sigma(E(v));
  * a connector into an ALREADY OPENED orbit costs one of the b tokens;
  * D = 5Q - P is the phase deficit, Q = opened orbits, P = ports.

mask records whether the FIRST and the LAST E-run are PARTIAL (length < 5).
That is exactly the marking the companion-hex lemma needs: a type-A (dirty
sigma) seam between two pieces whose two incident E-runs are BOTH full forces
an extra repeated hex, because the E-orbits of v and sigma(v) share exactly
the two rotation classes h(v) and h(E v).

This module computes C independently of Astra and cross-checks the unmarked
values against my own N*(b,0,D) table.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_f2_structure_126 import setup                        # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
G6 = setup(6)
P6, IDX, SG, TA = G6["perms"], G6["idx"], G6["sig"], G6["tau"]
ORB, HEX, OPH = G6["orbid"], G6["hexid"], G6["orbph"]
NP = 720

E = [IDX[TA(P6[w])] for w in range(NP)]          # phase +1 inside the E-orbit
SIG = [IDX[SG(P6[w])] for w in range(NP)]


def _s5(w):
    y = P6[w]
    for _ in range(5):
        y = SG(y)
    return y


W3B = [IDX[(_s5(w)[3], _s5(w)[4], _s5(w)[5], _s5(w)[2], _s5(w)[0], _s5(w)[1])]
       for w in range(NP)]
W3C = [IDX[(_s5(w)[3], _s5(w)[4], _s5(w)[5], _s5(w)[2], _s5(w)[1], _s5(w)[0])]
       for w in range(NP)]
TYPEC = [E[SIG[w]] for w in range(NP)]           # v -> E(sigma(v))
TYPED = [SIG[E[w]] for w in range(NP)]           # v -> sigma(E(v))
ORB_AT = {(ORB[w], OPH[w]): w for w in range(NP)}


def companion_hexes():
    """The E-orbits of v and sigma(v) share exactly the classes h(v), h(E v)."""
    bad = []
    for v in range(NP):
        ov = {E[E[E[E[v]]]], E[E[E[v]]], E[E[v]], E[v], v}
        ow = set()
        x = SIG[v]
        for _ in range(5):
            ow.add(x)
            x = E[x]
        shared = {HEX[a] for a in ov} & {HEX[a] for a in ow}
        if shared != {HEX[v], HEX[E[v]]} or len(shared) != 2:
            bad.append(v)
    return dict(checked=NP, violations=len(bad), examples=bad[:4],
                lemma_holds=(len(bad) == 0),
                statement="orb(v) and orb(sigma v) share exactly {h(v), h(Ev)}")


def capacity(b, dmax, use_CD=True, node_cap=None):
    """max ports by (deficit, first_partial, last_partial); exhaustive."""
    best = {}
    nodes = [0]
    capped = [False]
    usedhex = {HEX[0]}
    omask = {ORB[0]: 1 << OPH[0]}
    defcnt = [0] * 5
    defcnt[4] = 1

    def feasible(extra, skip, scap):
        c = defcnt[:]
        if skip is not None and skip in omask:
            c[5 - bin(omask[skip]).count("1")] -= 1
        tok, tot = extra, 0
        for d in range(4, 0, -1):
            take = min(c[d], tok)
            tok -= take
            tot += (c[d] - take) * d
        return tot <= scap

    def rec(cur, corb, passes, tok, firstlen, curlen, nruns):
        nodes[0] += 1
        if node_cap and nodes[0] > node_cap:
            capped[0] = True
            return
        if feasible(0, None, dmax):
            tot = sum(d * defcnt[d] for d in range(5))
            if tot <= dmax:
                fl = firstlen if nruns > 1 else curlen
                key = (tot, fl < 5, curlen < 5)
                if passes > best.get(key, -1):
                    best[key] = passes
        if not feasible(tok, corb, dmax):
            return
        # extend the current E-run: any unused phase (free at +1, else a token)
        ph = OPH[cur]
        for dp in range(1, 5):
            p = (ph + dp) % 5
            if omask[corb] >> p & 1:
                continue
            cost = 0 if dp == 1 else 1
            if cost > tok:
                continue
            nxt = ORB_AT[(corb, p)]
            if HEX[nxt] in usedhex:
                continue
            d0 = 5 - bin(omask[corb]).count("1")
            defcnt[d0] -= 1
            defcnt[d0 - 1] += 1
            omask[corb] |= 1 << p
            usedhex.add(HEX[nxt])
            rec(nxt, corb, passes + 1, tok - cost, firstlen,
                curlen + 1 if cost == 0 else curlen + 1, nruns)
            usedhex.discard(HEX[nxt])
            omask[corb] &= ~(1 << p)
            defcnt[d0 - 1] -= 1
            defcnt[d0] += 1
        # end the run, take a paid connector -> new run
        cands = [W3C[cur], W3B[cur]]
        if use_CD:
            cands += [TYPEC[cur], TYPED[cur]]
        for w in cands:
            if HEX[w] in usedhex:
                continue
            nq = ORB[w]
            fresh = nq not in omask
            if not fresh and tok < 1:
                continue
            if not fresh and (omask[nq] >> OPH[w] & 1):
                continue
            prev = omask.get(nq, 0)
            if fresh:
                defcnt[4] += 1
            else:
                d0 = 5 - bin(prev).count("1")
                defcnt[d0] -= 1
                defcnt[d0 - 1] += 1
            omask[nq] = prev | (1 << OPH[w])
            usedhex.add(HEX[w])
            rec(w, nq, passes + 1, tok - (0 if fresh else 1),
                firstlen if nruns > 1 else curlen, 1, nruns + 1)
            usedhex.discard(HEX[w])
            if fresh:
                del omask[nq]
                defcnt[4] -= 1
            else:
                omask[nq] = prev
                d0 = 5 - bin(prev).count("1")
                defcnt[d0 - 1] -= 1
                defcnt[d0] += 1

    t0 = time.time()
    rec(0, ORB[0], 1, b, 0, 1, 1)
    # cumulative over deficit
    out = {}
    for fp in (False, True):
        for lp in (False, True):
            run = -1
            for d in range(dmax + 1):
                v = -1
                for (dd, f2, l2), pv in best.items():
                    if dd <= d and (f2 == fp or not fp) and (l2 == lp or not lp):
                        # mask=True means "must be partial"; mask=False = free
                        pass
                for (dd, f2, l2), pv in best.items():
                    if dd > d:
                        continue
                    if fp and not f2:
                        continue
                    if lp and not l2:
                        continue
                    v = max(v, pv)
                run = max(run, v)
                out[f"D{d}/first_partial={fp}/last_partial={lp}"] = run
    return dict(b=b, dmax=dmax, use_CD=use_CD, nodes=nodes[0],
                capped=capped[0], seconds=round(time.time() - t0, 1),
                table=out)


if __name__ == "__main__":
    b = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    dm = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    cd = (sys.argv[3] != "noCD") if len(sys.argv) > 3 else True
    res = dict(companion=companion_hexes(), capacity=capacity(b, dm, cd))
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / f"rr_l6_endpoint_cap_b{b}_d{dm}_{'CD' if cd else 'noCD'}_144.json"
     ).write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res["companion"], ensure_ascii=False))
    t = res["capacity"]
    print(json.dumps({k: t[k] for k in ("b", "dmax", "use_CD", "nodes", "capped",
                                        "seconds")}))
    for k, v in t["table"].items():
        if k.endswith("first_partial=False/last_partial=False"):
            print("  ", k, v)
