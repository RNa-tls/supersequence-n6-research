#!/usr/bin/env python3
"""Round 153 -- a THIRD equality-witness enumerator, and the witness checker.

Three things live here.

  enumerate   an independent Python enumeration of every walk with exactly T
              ports and final deficit <= d.  It uses the catalogue that
              r152/src/checker152.py builds from string algebra, visits the
              moves in the REVERSE of the C enumerator's order, and prunes with
              nothing but the two proved facts (the analytic reach bound and
              the round-150 feasibility lemma).  A different traversal order
              gives different node counts; the SET it produces must be the same.

  check       replay a stored witness move by move: every step a catalogue
              joint, no phase reused, clean E inside its orbit, every budget
              respected, exactly T ports, final deficit <= d, and the deficit
              identity.  A witness that does not replay is not a witness.

  canonical   the least relabelling of the six letters (left S6, 720 elements),
              which is the only symmetry used anywhere in this round.  Left S6
              is a bijection of the 720 words that commutes with sigma, tau,
              end and the overlap length, so it maps walks to walks -- that is
              round 149's Theorem 2.4, checked exhaustively there over all
              518,400 (group element, word) pairs and re-checked here.

usage: eqwit153.py enumerate <b> <d> <a> <bb> <e> <h> <target> <out.jsonl>
       eqwit153.py check <b> <d> <a> <bb> <e> <h> <target> <file.jsonl> [...]
"""
from __future__ import annotations
import hashlib, itertools, json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent
                       / "r152" / "src"))
from checker152 import (PERMS, IDX, HEX, ORB, PHASE, MOVES, FREE, DA, DB,   # noqa
                        PAID, HEAVY, N, NHEX, _sigma, _tau, _end, _gap)

HEXCAP = 120


# ----------------------------------------------------------------- symmetry
def relabel_map(g):
    m = dict(zip("123456", g))
    return [IDX["".join(m[ch] for ch in w)] for w in PERMS]


_RL = None


def relabellings():
    global _RL
    if _RL is None:
        _RL = [relabel_map(g) for g in itertools.permutations("123456")]
    return _RL


def canonical(ports):
    best = None
    for r in relabellings():
        t = tuple(r[v] for v in ports)
        if best is None or t < best:
            best = t
    return best


def equivariance_check():
    """Left S6 commutes with the catalogue: all 720 x 720 pairs."""
    bad = 0
    for r in relabellings():
        for v in range(N):
            if FREE[r[v]] != r[FREE[v]] or DA[r[v]] != r[DA[v]] \
               or DB[r[v]] != r[DB[v]]:
                bad += 1
                break
            if sorted(PAID[r[v]]) != sorted(r[t] for t in PAID[v]):
                bad += 1
                break
            if sorted((r[t], c) for t, c in HEAVY[v]) != sorted(HEAVY[r[v]]):
                bad += 1
                break
    return dict(group=len(relabellings()), words=N,
                pairs=len(relabellings()) * N, violations=bad, ok=bad == 0)


# ---------------------------------------------------------------- the check
def check_witness(cell, target, ports):
    b, dmax, amax, bmax, emax, hmax = cell
    if len(ports) != target:
        return False, f"{len(ports)} ports, target {target}"
    if not ports or ports[0] != IDX["123456"]:
        return False, "does not start at 123456"
    if len(set(ports)) != len(ports):
        return False, "a port repeats"
    mv = {}
    for v in range(N):
        for t, kind, cost in MOVES[v]:
            mv.setdefault((v, t), (kind, cost))
    phm = {ORB[ports[0]]: {PHASE[ports[0]]}}
    hexu = {HEX[ports[0]]}
    deficit, tok, au, bu, eu, hu = 4, 0, 0, 0, 0, 0
    corb = ORB[ports[0]]
    for i in range(len(ports) - 1):
        u, t = ports[i], ports[i + 1]
        if (u, t) not in mv:
            return False, f"step {i} is not a catalogue joint"
        kind, cost = mv[(u, t)]
        q = ORB[t]
        if PHASE[t] in phm.get(q, ()):
            return False, f"step {i} reuses a phase"
        if kind == "E" and q != corb:
            return False, f"step {i}: clean E left its orbit"
        fresh = q not in phm
        newhex = HEX[t] not in hexu
        if not newhex and kind not in ("A", "B"):
            eu += 1
        au += kind == "A"
        bu += kind == "B"
        hu += cost if kind == "H" else 0
        tok += 0 if (kind == "E" or fresh) else 1
        phm.setdefault(q, set()).add(PHASE[t])
        hexu.add(HEX[t])
        deficit += 4 if fresh else -1
        corb = q
    if tok > b or deficit > dmax or au > amax or bu > bmax or eu > emax \
       or hu > hmax:
        return False, (f"budget: tok={tok}/{b} def={deficit}/{dmax} "
                       f"a={au}/{amax} bb={bu}/{bmax} e={eu}/{emax} "
                       f"h={hu}/{hmax}")
    if deficit != 5 * len(phm) - len(ports):
        return False, "deficit identity violated"
    return True, dict(ports=len(ports), deficit=deficit, orbits=len(phm),
                      hexagons=len(hexu), hex_simple=len(hexu) == len(ports),
                      tok=tok, a=au, bb=bu, e=eu, h=hu)


# ------------------------------------------------------------ the traversal
def enumerate_witnesses(cell, target, node_cap=0):
    b, dmax, amax, bmax, emax, hmax = cell
    phm = {ORB[0]: {PHASE[0]}}
    hexc = {HEX[0]: 1}
    path = [0]
    out, st = [], dict(nodes=0)

    def feas(corb, tok):
        us = sorted((5 - len(ph) for q, ph in phm.items() if q != corb),
                    reverse=True)
        return sum(us[tok:]) <= dmax

    def rec(v, corb, ports, tok, au, bu, eu, hu, deficit):
        st["nodes"] += 1
        if node_cap and st["nodes"] > node_cap:
            raise TimeoutError
        if ports == target:
            if deficit <= dmax:
                out.append(dict(deficit=deficit, ports=list(path)))
            return
        if not feas(corb, tok):
            return
        if ports + (NHEX - len(hexc)) + (amax - au) + (bmax - bu) \
           + (emax - eu) < target:
            return
        for t, kind, cost in reversed(MOVES[v]):      # the reverse order
            q = ORB[t]
            ph = phm.get(q)
            if ph is not None and PHASE[t] in ph:
                continue
            if kind == "E" and q != corb:
                continue
            if kind == "A" and au >= amax:
                continue
            if kind == "B" and bu >= bmax:
                continue
            if kind == "H" and hu + cost > hmax:
                continue
            newhex = HEX[t] not in hexc
            se = 0
            if not newhex and kind not in ("A", "B"):
                if eu >= emax:
                    continue
                se = 1
            fresh = ph is None
            c = 0 if (kind == "E" or fresh) else 1
            if c > tok:
                continue
            if fresh:
                phm[q] = {PHASE[t]}
            else:
                ph.add(PHASE[t])
            hexc[HEX[t]] = hexc.get(HEX[t], 0) + 1
            path.append(t)
            rec(t, q, ports + 1, tok - c, au + (kind == "A"),
                bu + (kind == "B"), eu + se,
                hu + (cost if kind == "H" else 0),
                deficit + (4 if fresh else -1))
            path.pop()
            hexc[HEX[t]] -= 1
            if not hexc[HEX[t]]:
                del hexc[HEX[t]]
            if fresh:
                del phm[q]
            else:
                ph.discard(PHASE[t])

    sys.setrecursionlimit(10000)
    rec(0, ORB[0], 1, b, 0, 0, 0, 0, 4)
    return out, st["nodes"]


def load(p):
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


def fingerprint(witnesses):
    cs = sorted(canonical(w["ports"]) for w in witnesses)
    classes = sorted(set(cs))
    return dict(raw=len(witnesses), classes=len(classes),
                canonical_sha256=hashlib.sha256(
                    json.dumps([list(c) for c in classes]).encode()).hexdigest(),
                raw_sha256=hashlib.sha256(json.dumps(
                    sorted(tuple(w["ports"]) for w in witnesses)).encode()
                ).hexdigest(),
                deficits=sorted({w["deficit"] for w in witnesses}),
                classes_list=[list(c) for c in classes])


def main(argv):
    mode = argv[0]
    cell = tuple(int(x) for x in argv[1:7])
    target = int(argv[7])
    if mode == "enumerate":
        t0 = time.time()
        wits, nodes = enumerate_witnesses(cell, target)
        Path(argv[8]).write_text(
            "".join(json.dumps(w) + "\n" for w in wits))
        print(json.dumps(dict(enumerator="PY153", cell="|".join(map(str, cell)),
                              target=target, route="no-table",
                              witnesses=len(wits), nodes=nodes,
                              seconds=round(time.time() - t0, 2),
                              file=argv[8])))
        return 0
    if mode == "check":
        ok = True
        for p in argv[8:]:
            ws = load(p)
            for w in ws:
                good, info = check_witness(cell, target, w["ports"])
                if not good:
                    ok = False
                    print(f"  BAD {p}: {info}")
                elif info["deficit"] != w["deficit"]:
                    ok = False
                    print(f"  BAD {p}: stored deficit {w['deficit']} != "
                          f"{info['deficit']}")
            fp = fingerprint(ws)
            print(f"  {p}: raw={fp['raw']} classes={fp['classes']} "
                  f"deficits={fp['deficits']} "
                  f"canon={fp['canonical_sha256'][:16]}")
        return 0 if ok else 1
    raise SystemExit(f"unknown mode {mode}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
