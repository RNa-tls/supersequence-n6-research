#!/usr/bin/env python3
"""Round 152 -- an INDEPENDENT Python checker for the marked piece capacities.

The twin of r152/src/piece152.c.  It reads the same L6-PIECECERT-1 bytes and
re-establishes both directions itself:

    lower   the stored witness replays as a legal piece with that mask
    upper   an exhaustive search for cap+1 ports under the mask finds nothing
    (-1)    the whole space for that mask is exhausted with nothing found

It imports the catalogue from r152/src/checker152.py, which builds it from
string algebra and reads nothing from the production solvers, and it reads no
production table: the only values it prunes with are the ones it has already
certified earlier in the same run.

usage: piece152.py --cert <cert.txt> [--report r.json] [--node-cap N]
                   [--compare outputs/rr_l6_marked_capacity_table_144.json]
"""
from __future__ import annotations
import argparse, hashlib, json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checker152 import HEX, ORB, PHASE, FREE, PAID, N                 # noqa: E402

HEXCAP = 120


class Piece:
    def __init__(self, certified, node_cap):
        self.cert = dict(certified)        # {(b,d): C(b,d,0,0)} already proved
        self.cap = node_cap
        self.nodes = 0
        self.found = None
        self.trail = None

    def ub(self, tok, d):
        best = HEXCAP
        for (kb, kd), c in self.cert.items():
            if kb >= tok and kd >= d and c < best:
                best = c
        return best

    @staticmethod
    def feas(phm, corb, tok, dmax):
        us = sorted((5 - len(ph) for q, ph in phm.items() if q != corb),
                    reverse=True)
        return sum(us[tok:]) <= dmax

    def search(self, b, dmax, fp, lp, target):
        self.nodes = 0
        self.found = None
        self.trail = None
        phm = {ORB[0]: {PHASE[0]}}
        hexu = {HEX[0]}
        path = [0]

        def rec(cur, corb, ports, tok, firstlen, curlen, nblk, deficit):
            self.nodes += 1
            if self.cap and self.nodes > self.cap:
                raise TimeoutError
            if deficit <= dmax and ports >= target:
                fl = firstlen if nblk > 1 else curlen
                if (not fp or fl < 5) and (not lp or curlen < 5):
                    self.found, self.trail = ports, list(path)
                    raise StopIteration
            if not self.feas(phm, corb, tok, dmax):
                return
            reach = min(ports + self.ub(tok, dmax - deficit + 4 + 5 * tok) - 1,
                        ports + (HEXCAP - len(hexu)))
            if reach < target:
                return
            t = FREE[cur]
            if HEX[t] not in hexu and PHASE[t] not in phm[corb]:
                phm[corb].add(PHASE[t])
                hexu.add(HEX[t])
                path.append(t)
                rec(t, corb, ports + 1, tok, firstlen, curlen + 1, nblk,
                    deficit - 1)
                path.pop()
                hexu.discard(HEX[t])
                phm[corb].discard(PHASE[t])
            for t in PAID[cur]:
                if HEX[t] in hexu:
                    continue
                q = ORB[t]
                ph = phm.get(q)
                fresh = ph is None
                if not fresh:
                    if PHASE[t] in ph:
                        continue
                    if tok < 1:
                        continue
                if fresh:
                    phm[q] = {PHASE[t]}
                else:
                    ph.add(PHASE[t])
                hexu.add(HEX[t])
                path.append(t)
                rec(t, q, ports + 1, tok - (0 if fresh else 1),
                    firstlen if nblk > 1 else curlen, 1, nblk + 1,
                    deficit + (4 if fresh else -1))
                path.pop()
                hexu.discard(HEX[t])
                if fresh:
                    del phm[q]
                else:
                    ph.discard(PHASE[t])

        sys.setrecursionlimit(10000)
        try:
            rec(0, ORB[0], 1, b, 0, 1, 1, 4)
        except StopIteration:
            return "FOUND"
        except TimeoutError:
            return "CAP"
        return "EXHAUSTED"

    @staticmethod
    def replay(b, dmax, fp, lp, cap, w):
        if len(w) != cap:
            return False, "witness length != cap"
        if not w or w[0] != 0:
            return False, "the piece must start at 123456"
        phm = {ORB[0]: {PHASE[0]}}
        hexu = {HEX[0]}
        norb, deficit, tok, corb = 1, 4, 0, ORB[0]
        firstlen, curlen, nblk = 0, 1, 1
        for i in range(len(w) - 1):
            u, t = w[i], w[i + 1]
            if not 0 <= t < N:
                return False, "port out of range"
            if HEX[t] in hexu:
                return False, f"step {i} revisits a hexagon"
            q = ORB[t]
            if PHASE[t] in phm.get(q, ()):
                return False, f"step {i} reuses a phase"
            if t == FREE[u]:
                if q != corb:
                    return False, f"step {i}: clean E left its orbit"
                phm[q].add(PHASE[t])
                deficit -= 1
                curlen += 1
            elif t in PAID[u]:
                fresh = q not in phm
                if not fresh:
                    tok += 1
                phm.setdefault(q, set()).add(PHASE[t])
                if fresh:
                    norb += 1
                    deficit += 4
                else:
                    deficit -= 1
                firstlen = firstlen if nblk > 1 else curlen
                curlen, nblk, corb = 1, nblk + 1, q
            else:
                return False, f"step {i} is neither a clean E nor a paid joint"
            hexu.add(HEX[t])
        if tok > b:
            return False, f"token budget exceeded: {tok} > {b}"
        if deficit > dmax:
            return False, f"deficit budget exceeded: {deficit} > {dmax}"
        if deficit != 5 * norb - len(w):
            return False, "deficit identity violated"
        fl = firstlen if nblk > 1 else curlen
        if fp and fl >= 5:
            return False, "the mask requires a partial FIRST block"
        if lp and curlen >= 5:
            return False, "the mask requires a partial LAST block"
        return True, dict(ports=len(w), orbits=norb, deficit=deficit, tok=tok,
                          first_block=fl, last_block=curlen)


def read_pcert(text):
    toks = [t for line in text.splitlines()
            for t in line.split("#")[0].split()
            if not t.startswith("L6-PIECECERT")]
    out, i = [], 0
    while i < len(toks):
        if toks[i] != "pcell":
            raise SystemExit(f"expected 'pcell' at token {i}, saw {toks[i]!r}")
        b, d, fp, lp, cap, n = (int(x) for x in toks[i + 1:i + 7])
        w = [int(x) for x in toks[i + 7:i + 7 + n]]
        if len(w) != n:
            raise SystemExit("witness truncated")
        out.append(dict(b=b, d=d, fp=fp, lp=lp, cap=cap, witness=w))
        i += 7 + n
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cert", required=True)
    ap.add_argument("--report", default=None)
    ap.add_argument("--node-cap", type=int, default=2_000_000_000)
    ap.add_argument("--compare", default=None)
    a = ap.parse_args()
    raw = Path(a.cert).read_bytes()
    if not raw.startswith(b"L6-PIECECERT-1"):
        raise SystemExit("not an L6-PIECECERT-1 file")
    entries = read_pcert(raw.decode())
    compare = None
    if a.compare:
        t = json.loads(Path(a.compare).read_text())["tables"]
        compare = {}
        for b, tab in t.items():
            for k, v in tab.items():
                d, mask = k.split("|")
                compare[(int(b), int(d), int(mask[0]), int(mask[1]))] = v

    certified, rows, ok = {}, [], True
    t0 = time.time()
    for e in entries:
        b, d, fp, lp, cap, w = (e["b"], e["d"], e["fp"], e["lp"], e["cap"],
                                e["witness"])
        key = f"{b}|{d}|{fp}{lp}"
        p = Piece(certified, a.node_cap)
        t1 = time.time()
        row = dict(cell=key, b=b, d=d, fp=fp, lp=lp, cap=cap)
        if cap < 0:
            r = p.search(b, d, fp, lp, 1)
            row["nodes"] = p.nodes
            row["status"] = {"FOUND": "DISAGREE", "CAP": "UNKNOWN_CAP",
                             "EXHAUSTED": "EXACT_CERTIFIED"}[r]
        else:
            good, info = (Piece.replay(b, d, fp, lp, cap, w) if w
                          else (True, dict(ports=cap)))
            if not good:
                row.update(status="WITNESS_BAD", detail=info)
            else:
                r = p.search(b, d, fp, lp, cap + 1)
                row["nodes"] = p.nodes
                row["status"] = {"FOUND": "DISAGREE", "CAP": "UNKNOWN_CAP",
                                 "EXHAUSTED": ("EXACT_CERTIFIED" if w
                                               else "UPPER_CERTIFIED")}[r]
        if row["status"] in ("EXACT_CERTIFIED", "UPPER_CERTIFIED"):
            if fp == 0 and lp == 0 and cap >= 0:
                certified[(b, d)] = cap
        else:
            ok = False
        if compare is not None:
            c = compare.get((b, d, fp, lp))
            row["claimed_elsewhere"] = c
            if c is not None and c != cap:
                row["status"] = "MISMATCH_VS_CLAIM"
                ok = False
        row["seconds"] = round(time.time() - t1, 2)
        rows.append(row)
        print(f"  {key:>12} cap={cap:<4} {row['status']:<18} "
              f"nodes={row.get('nodes', 0):<12,} {row['seconds']}s", flush=True)
    out = dict(cert=a.cert, cert_sha256=hashlib.sha256(raw).hexdigest(),
               node_cap=a.node_cap, cells=len(rows),
               certified=sum(r["status"] in ("EXACT_CERTIFIED",
                                             "UPPER_CERTIFIED") for r in rows),
               total_nodes=sum(r.get("nodes", 0) for r in rows),
               seconds=round(time.time() - t0, 1), all_certified=ok, rows=rows)
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
