#!/usr/bin/env python3
"""Round 168 -- exhaustion-certificate generator, format L6-EXTREE-3.

Two things change from round 166.

1. THE TARGET VALUE IS DISCOVERED, NOT READ.  Round 166 took the capacity C
   to prove from the round-152 capacity certificate.  That is a hint from a
   single-route artefact, and round 168 is not allowed to seed unknown
   capacities from it.  So the generator first runs its own branch-and-bound
   maximisation to find the largest port count reachable with final deficit
   <= d, and only then builds the exhaustion tree for that value.  The
   historical value is compared afterwards (phase 19) and never consulted
   before.

2. DEPENDENCIES ARE NAMED, NOT LOOKED UP.  L6-EXTREE-3 is

       L6-EXTREE-3
       ref  <container_sha256> <plain_sha256> <path>
       dep  <b> <d> <a> <bb> <e> <h> <cap> <plain_sha256> <path>
       tree <b> <d> <a> <bb> <e> <h> <cap>
       <preorder tokens>

   A leaf's (p) justification may cite ONLY a cell that appears in a `dep`
   line or whose own tree appears earlier in this same file.  Each `dep`
   carries the predecessor's cell, its claimed capacity, and the canonical
   PLAIN-TEXT sha256 of the certificate that establishes it, so a verifier
   never consults a table -- it resolves the hash.

GENERATION IS SEARCH, so this file is Route-A work.  It is not the second
proof route; it only emits an object the independent verifiers can replay.
"""
from __future__ import annotations
import argparse, gzip, hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r166" / "src"))
sys.path.insert(0, str(ROOT / "r167" / "src"))
import routeb164 as R                                             # noqa: E402
from gzrule167 import write_gz, plain_sha256                      # noqa: E402

MAGIC = "L6-EXTREE-3"


def cellstr(K):
    return "|".join(map(str, K))


class Engine:
    """Shared move machinery for the maximiser and the tree builder."""

    def __init__(self, deps, node_cap):
        self.cert = dict(deps)
        self._ubc = {}
        self.node_cap = node_cap
        self.nodes = 0

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

    def _frame(self, cell):
        return dict(phm={R.ORB[0]: {R.PHASE[0]}}, hexc={R.HEX[0]: 1})

    @staticmethod
    def _legal(phm, hexc, cell, v, corb, tok, au, bu, eu, hu):
        _b, _d, amax, bmax, emax, hmax = cell
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

    # ------------------------------------------------ phase 1: find the value
    def discover(self, cell):
        b, dmax, amax, bmax, emax, hmax = cell
        f = self._frame(cell)
        phm, hexc = f["phm"], f["hexc"]
        best = [0]

        def rec(v, corb, ports, tok, au, bu, eu, hu, deficit):
            self.nodes += 1
            if self.node_cap and self.nodes > self.node_cap:
                raise TimeoutError
            if deficit <= dmax and ports > best[0]:
                best[0] = ports
            target = best[0] + 1
            r1 = ports + (R.NHEX - len(hexc)) + (amax - au) + (bmax - bu) \
                + (emax - eu)
            if r1 < target:
                return
            if not R.feas_greedy(phm, corb, tok, dmax):
                return
            r2 = ports + self.ub(tok, dmax - deficit + 4 + 5 * tok,
                                 amax - au, bmax - bu, emax - eu,
                                 hmax - hu) - 1
            if r2 < target:
                return
            for t, kind, cost, fresh, se, c in self._legal(
                    phm, hexc, cell, v, corb, tok, au, bu, eu, hu):
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
        except TimeoutError:
            return None, f"node cap {self.node_cap} reached while maximising"
        return best[0], None

    # ------------------------------------------- phase 2: record the analysis
    def build(self, cell, cap):
        b, dmax, amax, bmax, emax, hmax = cell
        f = self._frame(cell)
        phm, hexc = f["phm"], f["hexc"]
        toks = []
        target = cap + 1

        def rec(v, corb, ports, tok, au, bu, eu, hu, deficit):
            self.nodes += 1
            if self.node_cap and self.nodes > self.node_cap:
                raise TimeoutError
            if ports >= target and deficit <= dmax:
                raise StopIteration
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
            ms = self._legal(phm, hexc, cell, v, corb, tok, au, bu, eu, hu)
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
            return None, f"a walk with {target} ports exists: cap > {cap}"
        except TimeoutError:
            return None, f"node cap {self.node_cap} reached"
        return toks, None


def write_batch(path, refs, deps, trees):
    lines = [MAGIC, "# generated by r168/src/gen168.py"]
    for csha, psha, rel in refs:
        lines.append(f"ref {csha} {psha} {rel}")
    for cell, cap, psha, rel in deps:
        lines.append(f"dep {' '.join(map(str, cell))} {cap} {psha} {rel}")
    for cell, cap, toks in trees:
        lines.append("")
        lines.append("tree " + " ".join(map(str, cell)) + f" {cap}")
        lines.append(toks if isinstance(toks, str) else " ".join(toks))
    text = "\n".join(lines) + "\n"
    write_gz(path, text)
    return text


def load_refs(rels, verify):
    """Predecessor cells, taken only from certificates that verify."""
    deps, refs = {}, []
    for rel in rels:
        res = verify(rel)
        if not res["ok"]:
            raise SystemExit(f"reference {rel} does not verify: "
                             f"{res.get('error')}")
        psha = plain_sha256(ROOT / rel)
        csha = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        refs.append((csha, psha, rel))
        for k, c in res["certified"].items():
            cell = tuple(int(x) for x in k.split("|")) if isinstance(k, str) \
                else tuple(k)
            if cell not in deps or c < deps[cell][0]:
                deps[cell] = (c, psha, rel)
    return refs, deps


def main():
    sys.path.insert(0, str(ROOT / "r168" / "src"))
    import verify168                                               # noqa: E402
    verify168.load_trust()
    verify_any = verify168.verify_any
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", required=True,
                    help="comma separated cells, or @<file> with one per line")
    ap.add_argument("--ref", action="append", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--node-cap", type=int, default=4_000_000_000)
    ap.add_argument("--budget", type=int, default=0,
                    help="stop starting new cells once this many search nodes "
                         "have been spent (0 = no budget)")
    a = ap.parse_args()

    if a.cells.startswith("@"):
        want = [tuple(int(x) for x in ln.split("|"))
                for ln in Path(a.cells[1:]).read_text().split()
                if ln.strip()]
    else:
        want = [tuple(int(x) for x in c.split("|"))
                for c in a.cells.split(",")]

    refs, dep_map = load_refs(a.ref, verify_any)
    deps = [(cell, c, psha, rel) for cell, (c, psha, rel)
            in sorted(dep_map.items())]
    certified = {cell: c for cell, (c, _p, _r) in dep_map.items()}

    trees, rows, total = [], [], 0
    t0 = time.time()
    for cell in want:
        if cell in certified:
            rows.append(dict(cell=cellstr(cell), status="ALREADY_CERTIFIED",
                             cap=certified[cell], search_nodes=0))
            continue
        if a.budget and total >= a.budget:
            rows.append(dict(cell=cellstr(cell), status="NOT_STARTED_BUDGET",
                             search_nodes=0))
            continue
        g = Engine(certified, a.node_cap)
        t1 = time.time()
        cap, err = g.discover(cell)
        n_disc = g.nodes
        if cap is None:
            rows.append(dict(cell=cellstr(cell),
                             status="DEFERRED_NODE_CAP", stage="discover",
                             detail=err, search_nodes=n_disc,
                             seconds=round(time.time() - t1, 1)))
            total += n_disc
            print(f"  {cellstr(cell):>16} DEFERRED at the node cap while "
                  f"maximising ({n_disc:,} nodes)", flush=True)
            continue
        g2 = Engine(certified, a.node_cap)
        toks, err = g2.build(cell, cap)
        total += n_disc + g2.nodes
        if toks is None and "node cap" in (err or ""):
            rows.append(dict(cell=cellstr(cell), cap=cap,
                             status="DEFERRED_NODE_CAP", stage="build",
                             detail=err, discovery_nodes=n_disc,
                             search_nodes=n_disc + g2.nodes,
                             seconds=round(time.time() - t1, 1)))
            print(f"  {cellstr(cell):>16} DEFERRED at the node cap while "
                  f"building ({g2.nodes:,} nodes)", flush=True)
            continue
        row = dict(cell=cellstr(cell), cap=cap,
                   discovery_nodes=n_disc, tree_nodes=g2.nodes,
                   search_nodes=n_disc + g2.nodes,
                   proof_nodes=len(toks) if toks else 0,
                   status="TREE_BUILT" if toks else "BUILD_FAILED",
                   detail=err, seconds=round(time.time() - t1, 1))
        rows.append(row)
        print(f"  {row['cell']:>16} cap={cap:<4} discover={n_disc:>12,} "
              f"tree={g2.nodes:>12,} proof={row['proof_nodes']:>12,} "
              f"{row['seconds']}s", flush=True)
        if toks is None:
            print(f"  {cellstr(cell):>16} BUILD_FAILED: {err}", flush=True)
            break
        certified[cell] = cap
        trees.append((cell, cap, " ".join(toks)))
        del toks

    outp = ROOT / a.out
    text = write_batch(outp, refs, deps, trees)
    rep = dict(format=MAGIC,
               refs=[dict(container_sha256=c, plain_sha256=p, path=r)
                     for c, p, r in refs],
               declared_dependencies=len(deps),
               requested=len(want),
               cells_built=sum(1 for r in rows if r["status"] == "TREE_BUILT"),
               failures=[r for r in rows
                         if r["status"] in ("BUILD_FAILED",
                                            "DISCOVERY_FAILED")],
               deferred=[dict(cell=r["cell"], stage=r.get("stage"),
                              search_nodes=r["search_nodes"])
                         for r in rows
                         if r["status"] == "DEFERRED_NODE_CAP"],
               not_started=[r["cell"] for r in rows
                            if r["status"] == "NOT_STARTED_BUDGET"],
               total_search_nodes=total,
               total_proof_nodes=sum(r.get("proof_nodes", 0) for r in rows),
               plain_bytes=len(text),
               plain_sha256=hashlib.sha256(text.encode()).hexdigest(),
               stored=str(outp.relative_to(ROOT)),
               stored_bytes=outp.stat().st_size,
               stored_sha256=hashlib.sha256(outp.read_bytes()).hexdigest(),
               rows=rows)
    rep["ok"] = not rep["failures"]
    (ROOT / a.report).write_text(json.dumps(rep, ensure_ascii=False,
                                            indent=1) + "\n")
    print(json.dumps({k: v for k, v in rep.items() if k != "rows"},
                     ensure_ascii=False, indent=1))
    print("generator seconds:", round(time.time() - t0, 1))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
