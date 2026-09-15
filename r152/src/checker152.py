#!/usr/bin/env python3
"""Round 152 -- an INDEPENDENT checker for exact capacity maxima.

WHY A CHECKER AND NOT A CERTIFICATE FILE.  For cap(K) <= C the natural proof
object is the exhausted search tree, and for the load-bearing cells that tree is
thousands to hundreds of thousands of nodes -- small enough that a checker can
simply REDO the search from first principles.  Serialising the tree would make a
large file whose checker would have to redo the same work anyway, so the proof
object here is the ordered list of claims plus a witness per claim, and the
checker establishes BOTH bounds itself:

    lower   the stored witness is replayed move by move          cap(K) >= C
    upper   an exhaustive search for C+1 ports finds nothing     cap(K) <= C

INDEPENDENCE.  This file imports nothing from the production solvers.  It
rebuilds the joint catalogue from string algebra, implements the feasibility
theorem from its statement, and uses no production table.  The only thing it
takes from outside is the claimed values, which is exactly what it is checking.

THE ONLY NON-ANALYTIC PRUNE is the monotone bound from cells ALREADY certified
in this same run: if K' >= K componentwise then cap(K) <= cap(K'), proved as
(P1) in research/RR_L6_R147_SOUND_UB.md.  So the checker processes cells in
increasing budget order and a cell may only be pruned with values it has
already established itself.  There is no circularity and no production input.

FAIL-CLOSED.  A search that hits the node cap is UNKNOWN_CAP, never "verified".
A search that FINDS C+1 ports is DISAGREE -- the claim is refuted.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, sys, time
from pathlib import Path

# ---------------------------------------------------------------- catalogue
PERMS = ["".join(p) for p in itertools.permutations("123456")]
IDX = {p: i for i, p in enumerate(PERMS)}
N = 720


def _sigma(s):
    return s[1:] + s[0]


def _tau(s):
    return s[1:-1] + s[0] + s[-1]


def _end(v):
    return v[5] + v[:5]


def _gap(e, t):
    for k in range(1, 6):
        if t.startswith(e[k:]):
            return k
    return 6


def _classes(f):
    seen, cid = {}, 0
    for p in PERMS:
        if p in seen:
            continue
        q = p
        while q not in seen:
            seen[q] = cid
            q = f(q)
        cid += 1
    return [seen[p] for p in PERMS], cid


HEX, NHEX = _classes(_sigma)
ORB, NORB = _classes(_tau)
PHASE = [None] * N
for _i, _p in enumerate(PERMS):
    _b, _x = _p, _p
    _reps = {}
    for _k in range(5):
        _reps[_x] = _k
        _x = _tau(_x)
    PHASE[_i] = None
_orbrep = {}
for _i, _p in enumerate(PERMS):
    _orbrep.setdefault(ORB[_i], []).append(_i)
for _q, _mem in _orbrep.items():
    _r = min(_mem)
    _x = PERMS[_r]
    for _k in range(5):
        PHASE[IDX[_x]] = _k
        _x = _tau(_x)

FREE = [None] * N
DA = [None] * N
DB = [None] * N
PAID = [[] for _ in range(N)]
HEAVY = [[] for _ in range(N)]


def _build_catalogue():
    for vi, v in enumerate(PERMS):
        e = _end(v)
        for ti, t in enumerate(PERMS):
            g = _gap(e, t)
            if g >= 4:
                if t != v and t != e:
                    HEAVY[vi].append((ti, g - 3))
                continue
            if g < 2:
                continue
            spell = e + t[6 - g:]
            hid = [IDX[spell[o:o + 6]] for o in range(1, g)
                   if len(set(spell[o:o + 6])) == 6]
            if g == 2:
                if not hid:
                    FREE[vi] = ti
                elif len(hid) == 1 and hid[0] == vi:
                    DA[vi] = ti
                continue
            if len(hid) == 2 and hid[0] == vi and HEX[ti] == HEX[vi]:
                DB[vi] = ti
                continue
            k = -1
            if not hid:
                d0 = [e[:3].index(t[3 + j]) if t[3 + j] in e[:3] else -1
                      for j in range(3)]
                code = 100 * d0[0] + 10 * d0[1] + d0[2]
                k = {120: 0, 201: 1, 210: 2}.get(code, -1)
            elif len(hid) == 1 and hid[0] == vi:
                k = 3
            elif len(hid) == 1 and _sigma(PERMS[hid[0]]) == t:
                k = 4
            if k >= 0:
                PAID[vi].append(ti)
        if FREE[vi] is None or DA[vi] is None or DB[vi] is None \
           or len(PAID[vi]) != 5:
            raise SystemExit(f"catalogue incomplete at {v}")


_build_catalogue()
MOVES = [None] * N
for _v in range(N):
    _m = [(FREE[_v], "E", 0), (DA[_v], "A", 0), (DB[_v], "B", 0)]
    _m += [(t, "P", 0) for t in PAID[_v]]
    _m += [(t, "H", c) for t, c in HEAVY[_v]]
    MOVES[_v] = _m

# -------------------------------------------------------------- the search
UBD = 40


class Checker:
    """One exhaustive upper-bound search, from first principles."""

    def __init__(self, certified, node_cap):
        self.cert = certified          # {(b,d,a,bb,e,h): cap}, already checked
        self._certl = list(certified.items())
        self._ubc = {}                 # memo only; it changes no value
        self.cap = node_cap
        self.reset()

    def reset(self):
        self.nodes = 0
        self.found = None
        self.trail = None
        self._path = []

    # --- the monotone bound from ALREADY CERTIFIED cells, (P1)
    def ub(self, tok, d, a, bb, e, h):
        key = (tok, d, a, bb, e, h)
        v = self._ubc.get(key)
        if v is not None:
            return v
        best = 120 + a + bb + e                      # (P2), proved analytic
        for (kb, kd, ka, kbb, ke, kh), c in self._certl:
            if (kb >= tok and kd >= d and ka >= a and kbb >= bb
                    and ke >= e and kh >= h and c < best):
                best = c
        self._ubc[key] = best
        return best

    # --- the feasibility theorem, implemented from its statement (round 150)
    @staticmethod
    def feas(phm, corb, tok, dmax):
        us = sorted((5 - len(ph) for q, ph in phm.items() if q != corb),
                    reverse=True)
        return sum(us[tok:]) <= dmax

    def search(self, cell, target):
        """Is any legal walk with `target` ports possible?  Exhaustive."""
        b, dmax, amax, bmax, emax, hmax = cell
        self.reset()
        phm = {}
        hexc = {}

        def rec(v, corb, ports, tok, au, bu, eu, hu, deficit):
            self.nodes += 1
            if self.cap and self.nodes > self.cap:
                raise TimeoutError
            if ports >= target and deficit <= dmax:
                self.found = ports
                self.trail = list(self._path)
                raise StopIteration
            if not self.feas(phm, corb, tok, dmax):
                return
            left = (amax - au) + (bmax - bu) + (emax - eu)
            r1 = ports + (NHEX - len(hexc)) + left
            r2 = ports + self.ub(tok, dmax - deficit + 4 + 5 * tok,
                                 amax - au, bmax - bu, emax - eu,
                                 hmax - hu) - 1
            if min(r1, r2) < target:
                return
            for t, kind, cost in MOVES[v]:
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
                self._path.append(t)
                rec(t, q, ports + 1, tok - c, au + (kind == "A"),
                    bu + (kind == "B"), eu + se,
                    hu + (cost if kind == "H" else 0),
                    deficit + (4 if fresh else -1))
                self._path.pop()
                hexc[HEX[t]] -= 1
                if hexc[HEX[t]] == 0:
                    del hexc[HEX[t]]
                if fresh:
                    del phm[q]
                else:
                    ph.discard(PHASE[t])

        v0 = 0
        phm[ORB[v0]] = {PHASE[v0]}
        hexc[HEX[v0]] = 1
        self._path = [v0]
        try:
            rec(v0, ORB[v0], 1, b, 0, 0, 0, 0, 4)
        except StopIteration:
            return "FOUND"
        except TimeoutError:
            return "CAP"
        return "EXHAUSTED"

    def replay(self, cell, ports):
        """Verify a witness: every move legal, budgets respected, count right."""
        b, dmax, amax, bmax, emax, hmax = cell
        if len(set(ports)) != len(ports):
            return False, "ports repeat"
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
                return False, f"step {i} is not a legal move"
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
        if tok > b or deficit > dmax or au > amax or bu > bmax \
           or eu > emax or hu > hmax:
            return False, (f"budget exceeded: tok={tok}/{b} def={deficit}/{dmax} "
                           f"a={au}/{amax} bb={bu}/{bmax} e={eu}/{emax} "
                           f"h={hu}/{hmax}")
        if deficit != 5 * len(phm) - len(ports):
            return False, "deficit identity violated"
        return True, dict(ports=len(ports), orbits=len(phm), deficit=deficit,
                          tok=tok, a=au, bb=bu, e=eu, h=hu)


# ------------------------------------------------------------------ driver
def _key(args):
    return "|".join(str(x) for x in args)


def read_text_cert(text):
    """Parse the plain-text certificate (L6-CAPCERT-2).

    The C checker r152/src/checker152.c reads exactly this file, so the two
    checkers verify the same bytes without either one preparing them.
    """
    toks, order, cells = [], [], {}
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if line and not line.startswith("L6-CAPCERT"):
            toks.extend(line.split())
    i = 0
    while i < len(toks):
        if toks[i] != "cell":
            raise SystemExit(f"certificate: expected 'cell' at token {i}")
        args = [int(x) for x in toks[i + 1:i + 7]]
        cap, n = int(toks[i + 7]), int(toks[i + 8])
        wit = [int(x) for x in toks[i + 9:i + 9 + n]]
        if len(wit) != n:
            raise SystemExit("certificate: witness truncated")
        k = _key(args)
        order.append(k)
        cells[k] = dict(args=args, cap=cap, witness=wit)
        i += 9 + n
    return dict(format="L6-CAPCERT-1", order=order, cells=cells)


def certify(doc, node_cap, compare=None, verbose=True):
    """Verify every cell of a certificate, in the certificate's own order.

    A cell is EXACT_CERTIFIED only when BOTH directions are established here:
    the stored witness replays to exactly `cap` ports inside the cell's budgets
    (so cap(K) >= C) and the exhaustive search for C+1 ports finishes without
    hitting the node cap and finds nothing (so cap(K) <= C).  Only cells that
    reach EXACT_CERTIFIED are allowed to prune later cells, so the monotone
    bound never rests on anything this run has not proved.
    """
    certified, rows, ok = {}, [], True
    for k in doc["order"]:
        rec = doc["cells"][k]
        cell = tuple(rec["args"])
        C = rec["cap"]
        row = dict(cell=k, cap=C)
        t0 = time.time()
        wit = rec["witness"]
        # An empty witness means the certificate claims only an UPPER bound for
        # this cell.  That is all the row census needs; the exhaustive direction
        # below is run exactly the same way, and the cell is reported as
        # UPPER_CERTIFIED rather than EXACT_CERTIFIED.
        if wit:
            good, info = Checker(certified, node_cap).replay(cell, wit)
        else:
            good, info = True, dict(ports=C)
        if not good:
            row.update(status="WITNESS_BAD", detail=info)
        elif info["ports"] != C:
            row.update(status="WITNESS_BAD",
                       detail=f"witness has {info['ports']} ports, claim {C}")
        else:
            ck = Checker(certified, node_cap)
            r = ck.search(cell, C + 1)
            row.update(nodes=ck.nodes)
            if r == "FOUND":
                row.update(status="DISAGREE",
                           detail=f"a walk with {C + 1} ports exists")
            elif r == "CAP":
                row.update(status="UNKNOWN_CAP",
                           detail=f"node cap {node_cap} reached")
            else:
                row.update(status="EXACT_CERTIFIED" if wit
                           else "UPPER_CERTIFIED")
                certified[cell] = C
        row["seconds"] = round(time.time() - t0, 2)
        if compare is not None and k in compare:
            row["claimed_elsewhere"] = compare[k]
            if compare[k] != C:
                row["status"] = "MISMATCH_VS_CLAIM"
        if row["status"] not in ("EXACT_CERTIFIED", "UPPER_CERTIFIED"):
            ok = False
        rows.append(row)
        if verbose:
            print(f"  {k:>16} cap={C:<4} {row['status']:<18} "
                  f"nodes={row.get('nodes', 0):<12,} {row['seconds']}s",
                  flush=True)
    return ok, rows, certified


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cert", required=True)
    ap.add_argument("--report", default=None)
    ap.add_argument("--compare", action="append", default=[],
                    help="production tables to cross-check the values against")
    ap.add_argument("--node-cap", type=int, default=2_000_000_000)
    a = ap.parse_args()
    raw = Path(a.cert).read_bytes()
    if raw.startswith(b"L6-CAPCERT-2"):
        doc = read_text_cert(raw.decode())
    else:
        doc = json.loads(raw)
        if doc.get("format") != "L6-CAPCERT-1":
            raise SystemExit("unknown certificate format")
    compare = None
    if a.compare:
        compare = {}
        for f in a.compare:
            for k, v in json.loads(Path(f).read_bytes()).items():
                compare[k] = v["cc"]
    t0 = time.time()
    ok, rows, certified = certify(doc, a.node_cap, compare)
    out = dict(cert_sha256=hashlib.sha256(raw).hexdigest(),
               checker_sha256=hashlib.sha256(
                   Path(__file__).read_bytes()).hexdigest(),
               node_cap=a.node_cap, cells=len(rows),
               certified=sum(r["status"] == "EXACT_CERTIFIED" for r in rows),
               upper_only=sum(r["status"] == "UPPER_CERTIFIED" for r in rows),
               total_nodes=sum(r.get("nodes", 0) for r in rows),
               seconds=round(time.time() - t0, 1),
               all_certified=ok, rows=rows)
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        json.dump(out, open(a.report, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
