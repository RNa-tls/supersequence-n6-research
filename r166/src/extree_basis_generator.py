#!/usr/bin/env python3
"""Round 166 -- batch generator for exhaustion certificates (L6-EXTREE-2).

L6-EXTREE-2 is L6-EXTREE-1 plus certificate REFERENCES.  A batch names the
predecessor batches it relies on, by repository path and sha256, instead of
re-serialising their proof trees:

    L6-EXTREE-2
    ref <sha256> <path>
    tree <b> <d> <a> <bb> <e> <h> <cap>
    <preorder tokens>

A leaf's (p) justification may cite a cell only if that cell's tree appears
earlier in this batch OR in a referenced batch the verifier has ALREADY
verified.  Nothing is seeded from the round-152 capacity tables: the generator
starts from an empty certified map and fills it only from proofs.

GENERATION IS A SEARCH, so this file is Route-A work.  It exists to produce an
artefact that independent verifiers can then check without searching.
"""
from __future__ import annotations
import argparse, gzip, hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r166" / "src"))
import routeb164 as R                                             # noqa: E402
import extree_basis_verify as V                                   # noqa: E402

CERTS = ROOT / "r152" / "certs"


class Generator:
    """Exhaustive search for cap+1 that records its own case analysis."""

    def __init__(self, certified, node_cap):
        self.cert = dict(certified)
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
            return None, f"FOUND a walk with {target} ports"
        except TimeoutError:
            return None, f"node cap {self.node_cap} reached"
        return toks, None


def write_batch(path, refs, trees):
    lines = ["L6-EXTREE-2",
             "# generated by r166/src/extree_basis_generator.py"]
    for h, rel in refs:
        lines.append(f"ref {h} {rel}")
    for cell, cap, toks in trees:
        lines.append("")
        lines.append("tree " + " ".join(map(str, cell)) + f" {cap}")
        lines.append(" ".join(toks))
    text = "\n".join(lines) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9,
                           mtime=0) as fh:
            fh.write(text.encode())
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-index", type=int, required=True)
    ap.add_argument("--to-index", type=int, required=True)
    ap.add_argument("--ref", action="append", default=[],
                    help="repo-relative path of a predecessor batch")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--node-cap", type=int, default=2_000_000_000)
    a = ap.parse_args()

    cap, order = R.parse_capcert(CERTS / "cap_cert_all_152.txt")
    # seed the certified map ONLY from verified predecessor certificates
    certified, refs = {}, []
    for rel in a.ref:
        res = V.verify_chain(rel, verifier_a=False)
        if not res["ok"]:
            print(json.dumps(dict(status="REF_INVALID", ref=rel,
                                  detail=res)), file=sys.stderr)
            return 1
        for k, c in res["certified"].items():
            certified[k] = c
        refs.append((res["sha256"], rel))

    trees, rows = [], []
    t0 = time.time()
    total = 0
    for i in range(a.from_index, a.to_index + 1):
        cell = order[i]
        C = cap[cell]["cap"]
        if cell in certified:
            rows.append(dict(index=i, cell="|".join(map(str, cell)), cap=C,
                             status="ALREADY_IN_A_REFERENCED_BATCH", nodes=0))
            continue
        g = Generator(certified, a.node_cap)
        toks, err = g.build(cell, C)
        total += g.nodes
        row = dict(index=i, cell="|".join(map(str, cell)), cap=C,
                   nodes=g.nodes, tokens=len(toks) if toks else 0,
                   status="TREE_BUILT" if toks else "FAILED", detail=err)
        rows.append(row)
        print(f"  [{i}] {row['cell']:>16} cap={C:<4} nodes={g.nodes:>12,}",
              flush=True)
        if toks is None:
            break
        certified[cell] = C
        trees.append((cell, C, toks))

    outp = ROOT / a.out
    text = write_batch(outp, refs, trees)
    rep = dict(from_index=a.from_index, to_index=a.to_index,
               refs=[dict(sha256=h, path=p) for h, p in refs],
               cells_built=sum(1 for r in rows if r["status"] == "TREE_BUILT"),
               failures=[r for r in rows if r["status"] == "FAILED"],
               total_search_nodes=total,
               plain_bytes=len(text),
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
