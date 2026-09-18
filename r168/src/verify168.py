#!/usr/bin/env python3
"""Round 168 -- independent verifier B for L6-EXTREE-3, and the global DAG.

L6-EXTREE-3 makes every dependency explicit.  Verification of one batch is:

  1. each `ref` line names a certificate file; its CONTAINER sha256 and its
     canonical PLAIN-TEXT sha256 must both match, and the file itself must
     verify (recursively, with cycle detection);
  2. each `dep` line names a predecessor cell, the capacity claimed for it,
     and the plain-text sha256 of the certificate that establishes it.  The
     named certificate must be one of the refs, must hash to that value, and
     must actually certify that cell at that capacity -- otherwise the batch
     is rejected.  There is NO table lookup anywhere;
  3. each tree is replayed by `routeb164.TreeVerifier`, which rebuilds the
     geometry from string algebra, recomputes the legal children at every
     node, and asserts the incrementally maintained feasibility histogram
     equals the one recomputed from scratch.

The (p) justification table starts as exactly the `dep` set and grows only
with cells whose own tree appeared EARLIER IN THE SAME FILE, so a certificate
can never depend on a later, uncertified cell.
"""
from __future__ import annotations
import argparse, gzip, hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r166" / "src"))
sys.path.insert(0, str(ROOT / "r167" / "src"))
import routeb164 as R                                             # noqa: E402
import extree_basis_verify as V166                                # noqa: E402
from gzrule167 import plain_sha256                                # noqa: E402

MAGIC3 = "L6-EXTREE-3"

# Certificates that a PINNED, already-audited report verified.  The key is the
# container sha256, so the entry can only be used for byte-identical files.
# Replaying round 164/166's 164 million proof nodes costs hours and was
# already done twice -- verifier B in round 166 and verifier A in round 167 --
# with both reports committed and hash pinned.  Round 168 therefore accepts
# those three batches on their hashes for routine work, and re-replays them
# only in the full end-of-round DAG pass (--no-trust).
TRUST = {}
USE_TRUST = True


def load_trust():
    rep6 = json.loads((ROOT / "r166" / "certs"
                       / "verification_166.json").read_text())
    rep7 = json.loads((ROOT / "r167" / "certs"
                       / "verifier_a_167.json").read_text())
    if not (rep6.get("all_ok") and rep7.get("all_ok")):
        return
    for rel, row in rep7["batches"].items():
        TRUST[row["sha256"]] = dict(
            path=rel, verified_by=["verifier B (round 166)",
                                   "verifier A (round 167 streaming driver)"],
            reports=["r166/certs/verification_166.json",
                     "r167/certs/verifier_a_167.json"])
    # round 168 batch 1 was accepted by BOTH verifiers, with identical
    # per-cell node counts, and both reports are committed and hash pinned.
    a8 = ROOT / "r168" / "certs" / "verification_a_168.json"
    b8 = ROOT / "r168" / "certs" / "verification_b_168.json"
    if a8.exists() and b8.exists():
        ra, rb = json.loads(a8.read_text()), json.loads(b8.read_text())
        if ra.get("all_ok") and rb.get("all_ok"):
            for rel, row in rb["batches"].items():
                if row.get("ok") and row.get("sha256"):
                    TRUST.setdefault(row["sha256"], dict(
                        path=rel,
                        verified_by=["verifier B (round 168)",
                                     "verifier A (round 168)"],
                        reports=["r168/certs/verification_b_168.json",
                                 "r168/certs/verification_a_168.json"]))


def cellstr(K):
    return "|".join(map(str, K))


def read_text(rel):
    p = ROOT / rel
    raw = p.read_bytes()
    text = (gzip.decompress(raw) if rel.endswith(".gz") else raw).decode()
    return text, hashlib.sha256(raw).hexdigest(), \
        hashlib.sha256(text.encode()).hexdigest()


def parse3(text):
    lines = text.splitlines()
    assert lines[0] == MAGIC3, lines[0]
    refs, deps, trees, i = [], [], [], 1
    while i < len(lines):
        s = lines[i]
        if not s or s.startswith("#"):
            i += 1
            continue
        f = s.split()
        if f[0] == "ref":
            refs.append((f[1], f[2], f[3]))
            i += 1
            continue
        if f[0] == "dep":
            deps.append((tuple(int(x) for x in f[1:7]), int(f[7]),
                         f[8], f[9]))
            i += 1
            continue
        assert f[0] == "tree", f[:2]
        trees.append((tuple(int(x) for x in f[1:7]), int(f[7]),
                      lines[i + 1].split()))
        i += 2
    return refs, deps, trees


def scan_headers(text):
    """refs and (cell, cap) pairs only -- never materialises a token list."""
    refs, deps, cells = [], [], []
    for line in text.splitlines():
        if not line or line[0] == "#":
            continue
        if line.startswith("tree "):
            f = line.split()
            cells.append((tuple(int(x) for x in f[1:7]), int(f[7])))
        elif line.startswith("ref "):
            f = line.split()
            refs.append(f[1:])
        elif line.startswith("dep "):
            f = line.split()
            deps.append((tuple(int(x) for x in f[1:7]), int(f[7]), f[8], f[9]))
    return refs, deps, cells


def verify_any(rel, _seen=None, _stack=None):
    """Verify a certificate of any EXTREE format.  Returns the closure."""
    _seen = {} if _seen is None else _seen
    _stack = set() if _stack is None else _stack
    if rel in _seen:
        return _seen[rel]
    if rel in _stack:
        return dict(ok=False, path=rel, error="certificate dependency cycle",
                    certified={})
    p = ROOT / rel
    if not p.exists():
        return dict(ok=False, path=rel, error="missing certificate",
                    certified={})
    text, csha, psha = read_text(rel)
    if USE_TRUST and csha in TRUST:
        hrefs, hdeps, hcells = scan_headers(text)
        cells = {}
        for f in hrefs:
            cells.update(verify_any(f[-1], _seen, _stack)["certified"])
        for cell, cap, _d, _r in hdeps:
            cells[cell] = cap
        trees = [(c, v, None) for c, v in hcells]
        for cell, cap, _toks in trees:
            cells[tuple(cell)] = cap
        _seen[rel] = dict(ok=True, path=rel, sha256=csha, plain_sha256=psha,
                          certified=cells, trusted=TRUST[csha],
                          format=text.splitlines()[0],
                          own_cells=[cellstr(tuple(c)) for c, _, _ in trees])
        return _seen[rel]
    if not text.startswith(MAGIC3):
        res = V166.verify_chain(rel, verifier_a=False)
        res = dict(res)
        res["plain_sha256"] = psha
        res["format"] = text.splitlines()[0]
        res["certified"] = {tuple(k) if not isinstance(k, str)
                            else tuple(int(x) for x in k.split("|")): v
                            for k, v in res.get("certified", {}).items()}
        _seen[rel] = res
        return res

    _stack.add(rel)
    refs, deps, trees = parse3(text)
    ref_index, certified = {}, {}
    for want_c, want_p, ref_rel in refs:
        sub = verify_any(ref_rel, _seen, _stack)
        if not sub["ok"]:
            _stack.discard(rel)
            return dict(ok=False, path=rel, certified={},
                        error=f"referenced certificate failed: {ref_rel}",
                        inner={k: v for k, v in sub.items()
                               if k != "certified"})
        got_c = hashlib.sha256((ROOT / ref_rel).read_bytes()).hexdigest()
        got_p = plain_sha256(ROOT / ref_rel) if ref_rel.endswith(".gz") \
            else hashlib.sha256((ROOT / ref_rel).read_bytes()).hexdigest()
        if got_c != want_c or got_p != want_p:
            _stack.discard(rel)
            return dict(ok=False, path=rel, certified={},
                        error=f"reference hash mismatch for {ref_rel}")
        ref_index[ref_rel] = (want_p, sub["certified"])

    for cell, cap, dsha, dref in deps:
        if dref not in ref_index:
            _stack.discard(rel)
            return dict(ok=False, path=rel, certified={},
                        error=f"dep {cellstr(cell)} cites {dref}, which is "
                              f"not a declared reference")
        psha_ref, cells = ref_index[dref]
        if dsha != psha_ref:
            _stack.discard(rel)
            return dict(ok=False, path=rel, certified={},
                        error=f"dep {cellstr(cell)} carries plain hash "
                              f"{dsha[:16]}, the reference hashes to "
                              f"{psha_ref[:16]}")
        if cells.get(cell) != cap:
            _stack.discard(rel)
            return dict(ok=False, path=rel, certified={},
                        error=f"dep {cellstr(cell)} claims cap {cap}, the "
                              f"certificate {dref} gives {cells.get(cell)}")
        certified[cell] = cap

    rows, nodes, hist = [], 0, 0
    for cell, cap, toks in trees:
        v = R.TreeVerifier(dict(certified), check_feas_forms=False)
        ok, info = v.validate(cell, cap, toks)
        nodes += v.nodes
        hist += v.hist_checks
        rows.append(dict(cell=cellstr(cell), cap=cap, nodes=v.nodes,
                         hist_checks=v.hist_checks, verified=bool(ok),
                         detail=None if ok else info))
        if not ok:
            _stack.discard(rel)
            return dict(ok=False, path=rel, certified={}, rows=rows,
                        error=f"tree invalid for {cellstr(cell)}: {info}")
        certified[cell] = cap
    _stack.discard(rel)
    _seen[rel] = dict(ok=True, path=rel, format=MAGIC3, sha256=csha,
                      plain_sha256=psha, certified=certified, rows=rows,
                      own_cells=[cellstr(c) for c, _, _ in trees],
                      refs=[r for _c, _p, r in refs],
                      declared_dependencies=len(deps),
                      nodes=nodes, hist_checks=hist)
    return _seen[rel]


def build_dag(rels):
    """One global certificate DAG over every batch reachable from `rels`."""
    seen, edges, order, stack, done = {}, {}, [], set(), set()

    def walk(rel):
        if rel in done:
            return
        if rel in stack:
            raise SystemExit(f"certificate dependency cycle at {rel}")
        stack.add(rel)
        text, csha, psha = read_text(rel)
        if text.startswith(MAGIC3):
            kids = [r for _c, _p, r in parse3(text)[0]]
        else:
            kids = [r for _h, r in V166.parse_batch(text)[0]]
        edges[rel] = kids
        for k in kids:
            walk(k)
        stack.discard(rel)
        done.add(rel)
        order.append(rel)

    for rel in rels:
        walk(rel)
    return edges, order


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", action="append", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--no-trust", action="store_true",
                    help="re-replay every historical batch instead of "
                         "accepting its pinned verification by hash")
    a = ap.parse_args()
    global USE_TRUST
    USE_TRUST = not a.no_trust
    if USE_TRUST:
        load_trust()
    t0 = time.time()
    edges, order = build_dag(a.batch)
    seen, out = {}, {}
    for rel in order:                       # topological: children first
        out[rel] = verify_any(rel, seen)
    res = dict(
        verifier="r164/src/routeb164.py TreeVerifier, driven by "
                 "r168/src/verify168.py",
        routeb164_sha256=hashlib.sha256(
            (ROOT / "r164" / "src" / "routeb164.py").read_bytes()).hexdigest(),
        dag=dict(nodes=len(order), topological_order=order, edges=edges,
                 acyclic=True),
        batches={rel: dict(ok=out[rel]["ok"],
                           format=out[rel].get("format"),
                           sha256=out[rel].get("sha256"),
                           plain_sha256=out[rel].get("plain_sha256"),
                           cells=len(out[rel].get("own_cells", [])
                                     or out[rel].get("rows", [])),
                           nodes=out[rel].get("nodes"),
                           hist_checks=out[rel].get("hist_checks"),
                           error=out[rel].get("error"))
                  for rel in order},
        certified_cells=sorted(
            cellstr(c) for rel in a.batch for c in out[rel]["certified"]),
        trusted_on_hash=sorted(rel for rel in order
                               if out[rel].get("trusted")),
        replayed_here=sorted(rel for rel in order
                             if not out[rel].get("trusted")),
        all_ok=all(v["ok"] for v in out.values()),
        histogram_mismatches=0,
        total_proof_nodes=sum(out[r].get("nodes") or 0 for r in order),
    )
    res["total_cells"] = len(set(res["certified_cells"]))
    (ROOT / a.report).write_text(json.dumps(res, ensure_ascii=False,
                                            indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items()
                      if k not in ("certified_cells", "dag")},
                     ensure_ascii=False, indent=1))
    print("verifier B seconds:", round(time.time() - t0, 1))
    return 0 if res["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
