#!/usr/bin/env python3
"""Round 164 -- MANUFACTURE the missing upper-bound proof objects.

No exhaustion-tree generator exists in the repository: r152/src/extree152.py
is a validator and the pilot file's producer was never committed.  So for any
target cell Route B has nothing to replay.  This program writes the missing
proof object, using its own search, in the L6-EXTREE-1 format.

BE CLEAR ABOUT WHAT THIS IS.  Generating a tree is a SEARCH, so this file is
Route-A work.  Its purpose is to create an artefact that Route B can then
check, and the value is that the result is checkable afterwards by two
independent validators (this round's and round 152's) without anyone
re-running the search.  The node budget is explicit and enforced.

A tree is emitted in certificate order so that a leaf's (p) justification may
only cite a cell whose own tree appears EARLIER in the same file -- the same
induction order the validator enforces.
"""
from __future__ import annotations
import argparse, gzip, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import routeb164 as R                                             # noqa: E402

CERTS = ROOT / "r152" / "certs"


class Generator:
    """Exhaustive search for cap+1 that records its own case analysis."""

    def __init__(self, certified, node_cap):
        self.cert = dict(certified)
        self._ubc = {}
        self.node_cap = node_cap
        self.nodes = 0
        self.found = None

    def ub(self, tok, d, a, bb, e, h):
        key = (tok, d, a, bb, e, h)
        v = self._ubc.get(key)
        if v is not None:
            return v
        best = R.UBFALL + a + bb + e
        for (kb, kd, ka, kbb, ke, kh), c in self.cert.items():
            if (kb >= tok and kd >= d and ka >= a and kbb >= bb
                    and ke >= e and kh >= h and c < best):
                best = c
        self._ubc[key] = best
        return best

    def build(self, cell, cap):
        b, dmax, amax, bmax, emax, hmax = cell
        phm = {R.ORB[0]: {R.PHASE[0]}}
        hexc = {R.HEX[0]: 1}
        toks = []
        target = cap + 1

        def legal(v, corb, tok, au, bu, eu, hu):
            out = []
            for t, kind, cost in R.MOVES[v]:
                q = R.ORB[t]
                ph = phm.get(q)
                if ph is not None and R.PHASE[t] in ph:
                    continue
                if kind == "E" and q != corb:
                    continue
                if kind == "A" and au >= amax:
                    continue
                if kind == "B" and bu >= bmax:
                    continue
                if kind == "H" and hu + cost > hmax:
                    continue
                newhex = R.HEX[t] not in hexc
                se = 0
                if not newhex and kind not in ("A", "B"):
                    if eu >= emax:
                        continue
                    se = 1
                fresh = ph is None
                c = 0 if (kind == "E" or fresh) else 1
                if c > tok:
                    continue
                out.append((t, kind, cost, fresh, se, c))
            return out

        def rec(v, corb, ports, tok, au, bu, eu, hu, deficit):
            self.nodes += 1
            if self.node_cap and self.nodes > self.node_cap:
                raise TimeoutError
            if ports >= target and deficit <= dmax:
                self.found = ports
                raise StopIteration
            # the three proved stopping facts, in the validator's own order
            r1 = ports + (R.NHEX - len(hexc)) + (amax - au) + (bmax - bu) \
                + (emax - eu)
            if r1 < target:
                toks.append("L")
                return
            if not R.feas_greedy(phm, corb, tok, dmax):
                toks.append("L")
                return
            r2 = ports + self.ub(tok, dmax - deficit + 4 + 5 * tok,
                                 amax - au, bmax - bu, emax - eu,
                                 hmax - hu) - 1
            if r2 < target:
                toks.append("L")
                return
            ms = legal(v, corb, tok, au, bu, eu, hu)
            toks.append(f"N{len(ms)}")
            for t, kind, cost, fresh, se, c in ms:
                q = R.ORB[t]
                if fresh:
                    phm[q] = {R.PHASE[t]}
                else:
                    phm[q].add(R.PHASE[t])
                hexc[R.HEX[t]] = hexc.get(R.HEX[t], 0) + 1
                rec(t, q, ports + 1, tok - c, au + (kind == "A"),
                    bu + (kind == "B"), eu + se,
                    hu + (cost if kind == "H" else 0),
                    deficit + (4 if fresh else -1))
                hexc[R.HEX[t]] -= 1
                if hexc[R.HEX[t]] == 0:
                    del hexc[R.HEX[t]]
                if fresh:
                    del phm[q]
                else:
                    phm[q].discard(R.PHASE[t])

        try:
            rec(0, R.ORB[0], 1, b, 0, 0, 0, 0, 4)
        except StopIteration:
            return None, f"FOUND a walk with {target} ports -- Route A is wrong"
        except TimeoutError:
            return None, f"node cap {self.node_cap} reached"
        return toks, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", type=int, default=51,
                    help="how many cells of the certificate order to cover")
    ap.add_argument("--node-cap", type=int, default=60_000_000)
    ap.add_argument("--out", default="r164/certs/extree_prefix_164.txt.gz")
    ap.add_argument("--report", default="r164/certs/gentree_164.json")
    a = ap.parse_args()

    cap, order = R.parse_capcert(CERTS / "cap_cert_all_152.txt")
    tg = json.loads((ROOT / "r164" / "certs" / "targets_164.json").read_text())
    targets = {tuple(c) for c in tg["CHAIN_SINGLE_IMPL"]}

    certified, rows, lines = {}, [], ["L6-EXTREE-1",
                                      "# generated by r164/src/gentree164.py",
                                      "# preorder: N<k> internal with exactly "
                                      "k legal children, L = justified leaf"]
    t0 = time.time()
    total = 0
    for i, cell in enumerate(order[:a.prefix]):
        C = cap[cell]["cap"]
        g = Generator(certified, a.node_cap)
        toks, err = g.build(cell, C)
        row = dict(index=i, cell="|".join(map(str, cell)), cap=C,
                   is_target=cell in targets, nodes=g.nodes,
                   tokens=len(toks) if toks else 0,
                   status="TREE_BUILT" if toks else "FAILED",
                   detail=err)
        total += g.nodes
        if toks is None:
            rows.append(row)
            print(json.dumps(row), flush=True)
            break
        certified[cell] = C
        lines.append("")
        lines.append("tree " + " ".join(map(str, cell)) + f" {C}")
        lines.append(" ".join(toks))
        rows.append(row)
        print(f"  {row['cell']:>16} cap={C:<4} nodes={g.nodes:>12,} "
              f"tokens={len(toks):>12,} {'TARGET' if row['is_target'] else ''}",
              flush=True)

    text = "\n".join(lines) + "\n"
    outp = ROOT / a.out
    outp.parent.mkdir(parents=True, exist_ok=True)
    if str(outp).endswith(".gz"):
        # mtime=0 so the gzip container is byte-deterministic across runs
        with open(outp, "wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9,
                               mtime=0) as fh:
                fh.write(text.encode())
    else:
        outp.write_text(text)
    rep = dict(prefix=a.prefix, node_cap=a.node_cap,
               cells_built=sum(1 for r in rows if r["status"] == "TREE_BUILT"),
               targets_built=sum(1 for r in rows
                                 if r["status"] == "TREE_BUILT"
                                 and r["is_target"]),
               failures=[r for r in rows if r["status"] != "TREE_BUILT"],
               total_search_nodes=total,
               plain_bytes=len(text), stored=str(outp.relative_to(ROOT)),
               stored_bytes=outp.stat().st_size, rows=rows)
    rep["ok"] = not rep["failures"]
    (ROOT / a.report).write_text(json.dumps(rep, ensure_ascii=False,
                                            indent=1) + "\n")
    print(json.dumps({k: v for k, v in rep.items() if k != "rows"},
                     ensure_ascii=False, indent=1))
    print("seconds:", round(time.time() - t0, 1))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
