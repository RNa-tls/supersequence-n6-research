#!/usr/bin/env python3
"""Round 152 -- the VALIDATOR for explicit exhaustion trees (L6-EXTREE-1).

This program performs NO SEARCH.  It walks the tree written in the file and, at
every node, does three things:

  1. recomputes the legal moves from the state itself and insists the file's
     N<k> lists EXACTLY that many children, then descends into them in the
     catalogue's canonical order -- so a subtree cannot be quietly dropped;
  2. for every leaf, checks that at least one of three PROVED facts justifies
     stopping there:
        (b) ports + (120 - |hexagons used|) + (a + bb + e left) < C+1   [(P2)]
        (f) the feasibility lemma already excludes every continuation   [r150]
        (p) ports + ub(remaining budgets) - 1 < C+1, where ub is the monotone
            bound from cells validated EARLIER IN THIS SAME FILE         [(P1)]
  3. checks the node does not itself reach C+1 ports at deficit <= d.

If all three hold everywhere, the tree is a complete case analysis and
cap(K) <= C.  The order of the file is the induction order: a cell may only be
used in a (p) justification after its own tree has been validated.

The catalogue comes from r152/src/checker152.py, which builds it from string
algebra and reads nothing from the production solvers.

usage: extree152.py --tree <file.extree> [--report r.json] [--cert cap_cert.txt]
"""
from __future__ import annotations
import argparse, hashlib, json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checker152 import (HEX, ORB, PHASE, MOVES, NHEX, Checker,          # noqa
                        read_text_cert, entries_of)

KIND_ORDER = {"E": 0, "A": 1, "B": 2, "P": 3, "H": 4}


def canonical_moves(v):
    """The catalogue's canonical order: clean E, dirty A, dirty B, paid, heavy."""
    return sorted(MOVES[v], key=lambda m: (KIND_ORDER[m[1]],))


_CANON = None


def canon(v):
    global _CANON
    if _CANON is None:
        _CANON = [canonical_moves(u) for u in range(len(MOVES))]
    return _CANON[v]


class Validator:
    def __init__(self, certified):
        self.cert = certified
        self._ubc = {}
        self.nodes = 0

    def ub(self, tok, d, a, bb, e, h):
        key = (tok, d, a, bb, e, h)
        v = self._ubc.get(key)
        if v is not None:
            return v
        best = 120 + a + bb + e
        for (kb, kd, ka, kbb, ke, kh), c in self.cert.items():
            if (kb >= tok and kd >= d and ka >= a and kbb >= bb
                    and ke >= e and kh >= h and c < best):
                best = c
        self._ubc[key] = best
        return best

    @staticmethod
    def feas(phm, corb, tok, dmax):
        us = sorted((5 - len(ph) for q, ph in phm.items() if q != corb),
                    reverse=True)
        return sum(us[tok:]) <= dmax

    def validate(self, cell, cap, toks, pos):
        """Walk one tree.  Returns (ok, detail, next position)."""
        b, dmax, amax, bmax, emax, hmax = cell
        phm = {ORB[0]: {PHASE[0]}}
        hexc = {HEX[0]: 1}
        state = dict(err=None, pos=pos)

        def legal(v, corb, tok, au, bu, eu, hu):
            out = []
            for t, kind, cost in canon(v):
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
                out.append((t, kind, cost, fresh, newhex, se, c))
            return out

        def walk(v, corb, ports, tok, au, bu, eu, hu, deficit):
            self.nodes += 1
            i = state["pos"]
            if i >= len(toks):
                state["err"] = "token stream ended early"
                return
            tk = toks[i]
            state["pos"] = i + 1
            if ports >= cap + 1 and deficit <= dmax:
                state["err"] = (f"the tree itself reaches {ports} ports at "
                                f"deficit {deficit} <= {dmax}")
                return
            if tk == "L":
                r1 = ports + (NHEX - len(hexc)) + (amax - au) + (bmax - bu) \
                     + (emax - eu)
                if r1 < cap + 1:
                    return                                            # (b)
                if not self.feas(phm, corb, tok, dmax):
                    return                                            # (f)
                r2 = ports + self.ub(tok, dmax - deficit + 4 + 5 * tok,
                                     amax - au, bmax - bu, emax - eu,
                                     hmax - hu) - 1
                if r2 < cap + 1:
                    return                                            # (p)
                state["err"] = (f"unjustified leaf at token {i}: ports={ports} "
                                f"deficit={deficit} r1={r1} r2={r2}")
                return
            if not tk.startswith("N"):
                state["err"] = f"bad token {tk!r} at {i}"
                return
            k = int(tk[1:])
            ms = legal(v, corb, tok, au, bu, eu, hu)
            if k != len(ms):
                state["err"] = (f"token {i} says {k} children, the state has "
                                f"{len(ms)} legal moves")
                return
            for t, kind, cost, fresh, newhex, se, c in ms:
                q = ORB[t]
                if fresh:
                    phm[q] = {PHASE[t]}
                else:
                    phm[q].add(PHASE[t])
                hexc[HEX[t]] = hexc.get(HEX[t], 0) + 1
                walk(t, q, ports + 1, tok - c, au + (kind == "A"),
                     bu + (kind == "B"), eu + se,
                     hu + (cost if kind == "H" else 0),
                     deficit + (4 if fresh else -1))
                hexc[HEX[t]] -= 1
                if hexc[HEX[t]] == 0:
                    del hexc[HEX[t]]
                if fresh:
                    del phm[q]
                else:
                    phm[q].discard(PHASE[t])
                if state["err"]:
                    return

        sys.setrecursionlimit(10000)
        walk(0, ORB[0], 1, b, 0, 0, 0, 0, 4)
        return state["err"] is None, state["err"], state["pos"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True)
    ap.add_argument("--cert", default=None,
                    help="cap certificate, to also replay the witnesses")
    ap.add_argument("--report", default="r152/certs/extree_152.json")
    a = ap.parse_args()
    raw = Path(a.tree).read_bytes()
    text = raw.decode()
    if not text.startswith("L6-EXTREE-1"):
        raise SystemExit("not an L6-EXTREE-1 file")
    toks = [t for line in text.splitlines()
            for t in line.split("#")[0].split()
            if not t.startswith("L6-EXTREE")]

    wit = {}
    if a.cert:
        doc = read_text_cert(Path(a.cert).read_text())
        for e in entries_of(doc):
            wit["|".join(map(str, e["args"])) + f"@{e['cap']}"] = e["witness"]

    certified, rows, ok, i = {}, [], True, 0
    total_nodes = 0
    while i < len(toks):
        if toks[i] != "tree":
            raise SystemExit(f"expected 'tree' at token {i}, saw {toks[i]!r}")
        cell = tuple(int(x) for x in toks[i + 1:i + 7])
        cap = int(toks[i + 7])
        key = "|".join(map(str, cell))
        v = Validator(dict(certified))
        t0 = time.time()
        good, err, i = v.validate(cell, cap, toks, i + 8)
        row = dict(cell=key, cap=cap, nodes=v.nodes,
                   seconds=round(time.time() - t0, 2))
        if not good:
            row.update(status="TREE_INVALID", detail=err)
        else:
            row["status"] = "UPPER_CERTIFIED"
            certified[cell] = cap
            w = wit.get(f"{key}@{cap}")
            if w:
                g, info = Checker({}, 0).replay(cell, w)
                if g and info["ports"] == cap:
                    row["status"] = "EXACT_CERTIFIED"
                else:
                    row.update(status="WITNESS_BAD", detail=info)
        if row["status"] not in ("EXACT_CERTIFIED", "UPPER_CERTIFIED"):
            ok = False
        total_nodes += v.nodes
        rows.append(row)
        print(f"  {key:>16} cap={cap:<4} {row['status']:<16} "
              f"nodes={v.nodes:<12,} {row['seconds']}s"
              + (f"  {row.get('detail')}" if row.get("detail") else ""),
              flush=True)
    out = dict(tree=a.tree, tree_sha256=hashlib.sha256(raw).hexdigest(),
               tree_bytes=len(raw), cells=len(rows), total_nodes=total_nodes,
               certified=sum(r["status"] in ("EXACT_CERTIFIED",
                                             "UPPER_CERTIFIED") for r in rows),
               exact=sum(r["status"] == "EXACT_CERTIFIED" for r in rows),
               all_valid=ok, rows=rows)
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
