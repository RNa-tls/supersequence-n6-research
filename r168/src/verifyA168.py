#!/usr/bin/env python3
"""Round 168 phase 11 -- verifier A over L6-EXTREE-3, streaming.

The validation logic stays `r152/src/extree152.py`, byte for byte.  Only the
driver is new: it streams the token sequence through a window (round 167's
fix for the memory limit) and it understands the format-3 header, seeding the
(p) justification table from the `dep` lines after checking each one against
the referenced certificate's hashes.

A and B are run on the same artefacts and compared by the caller.  If they
disagree the round stops at the earliest differing certificate; nothing is
decided by majority.
"""
from __future__ import annotations
import argparse, gzip, hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r152" / "src"))
sys.path.insert(0, str(ROOT / "r167" / "src"))
sys.path.insert(0, str(ROOT / "r168" / "src"))
import extree152 as A                                             # noqa: E402
from gzrule167 import plain_sha256                                # noqa: E402
from verify168 import scan_headers, MAGIC3                        # noqa: E402

WINDOW = 4096
HEADER = ("ref", "dep")


class Stream:
    """Forward-only token sequence that behaves like a list to the validator."""

    def __init__(self, path, total):
        self.path, self.total = path, total
        self.buf, self.base = [], 0
        self.it = self._tokens()

    def _tokens(self):
        op = gzip.open if str(self.path).endswith(".gz") else open
        with op(self.path, "rt") as fh:
            for line in fh:
                s = line.split("#")[0]
                f = s.split()
                if not f or f[0] in HEADER or f[0].startswith("L6-EXTREE"):
                    continue
                for t in f:
                    yield t

    def __len__(self):
        return self.total

    def __getitem__(self, i):
        if i < self.base:
            raise IndexError(f"token {i} already consumed")
        while i >= self.base + len(self.buf):
            try:
                self.buf.append(next(self.it))
            except StopIteration:
                raise IndexError(f"token {i} past end of stream")
        if len(self.buf) > 2 * WINDOW:
            drop = len(self.buf) - WINDOW
            self.base += drop
            del self.buf[:drop]
        return self.buf[i - self.base]


def count_tokens(path):
    n = 0
    op = gzip.open if str(path).endswith(".gz") else open
    with op(path, "rt") as fh:
        for line in fh:
            f = line.split("#")[0].split()
            if not f or f[0] in HEADER or f[0].startswith("L6-EXTREE"):
                continue
            n += len(f)
    return n


def read_head(rel):
    p = ROOT / rel
    raw = p.read_bytes()
    text = (gzip.decompress(raw) if rel.endswith(".gz") else raw).decode()
    return text, hashlib.sha256(raw).hexdigest(), \
        hashlib.sha256(text.encode()).hexdigest()


def cells_of(rel, seen):
    """(cell -> cap) a certificate carries, following its own references."""
    if rel in seen:
        return seen[rel]
    text, _c, _p = read_head(rel)
    refs, deps, own = scan_headers(text)
    out = {}
    for f in refs:
        out.update(cells_of(f[-1], seen))
    for cell, cap, _d, _r in deps:
        out[cell] = cap
    for cell, cap in own:
        out[cell] = cap
    seen[rel] = out
    return out


def verify(rel, log=print):
    text, csha, psha = read_head(rel)
    if not text.startswith(MAGIC3):
        raise SystemExit(f"{rel} is not {MAGIC3}; use r167/src/verifyA167.py")
    refs, deps, _own = scan_headers(text)
    seen = {}
    certified, index = {}, {}
    for f in refs:
        want_c, want_p, ref_rel = f[0], f[1], f[2]
        p = ROOT / ref_rel
        if not p.exists():
            return dict(ok=False, path=rel, error=f"missing reference {ref_rel}")
        got_c = hashlib.sha256(p.read_bytes()).hexdigest()
        got_p = plain_sha256(p) if ref_rel.endswith(".gz") else got_c
        if got_c != want_c or got_p != want_p:
            return dict(ok=False, path=rel,
                        error=f"reference hash mismatch for {ref_rel}")
        index[ref_rel] = (want_p, cells_of(ref_rel, seen))
    for cell, cap, dsha, dref in deps:
        if dref not in index:
            return dict(ok=False, path=rel,
                        error=f"dep cites undeclared reference {dref}")
        pref, cells = index[dref]
        if dsha != pref or cells.get(cell) != cap:
            return dict(ok=False, path=rel,
                        error=f"dep {cell} does not match {dref}")
        certified[cell] = cap

    ntok = count_tokens(ROOT / rel)
    toks = Stream(ROOT / rel, ntok)
    rows, i, ok = [], 0, True
    while i < ntok:
        if toks[i] != "tree":
            return dict(ok=False, path=rel,
                        error=f"expected 'tree' at token {i}, saw {toks[i]!r}")
        cell = tuple(int(toks[i + j]) for j in range(1, 7))
        cap = int(toks[i + 7])
        v = A.Validator(dict(certified))
        t0 = time.time()
        good, err, i = v.validate(cell, cap, toks, i + 8)
        rows.append(dict(cell="|".join(map(str, cell)), cap=cap,
                         nodes=v.nodes,
                         status="UPPER_CERTIFIED" if good else "TREE_INVALID",
                         detail=err))
        log(f"  {rows[-1]['cell']:>16} cap={cap:<4} {rows[-1]['status']:<14} "
            f"nodes={v.nodes:<12,} {round(time.time() - t0, 1)}s"
            + (f"  {err}" if err else ""))
        if not good:
            ok = False
            break
        certified[cell] = cap
    return dict(ok=ok, path=rel, sha256=csha, plain_sha256=psha,
                declared_dependencies=len(deps), tokens=ntok,
                cells=len(rows), nodes=sum(r["nodes"] for r in rows),
                certified={"|".join(map(str, k)): v
                           for k, v in certified.items()},
                rows=rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", action="append", required=True)
    ap.add_argument("--report", required=True)
    a = ap.parse_args()
    t0 = time.time()
    out = {rel: verify(rel) for rel in a.batch}
    res = dict(driver="r168/src/verifyA168.py (streaming, format 3); "
                      "validation logic is r152/src/extree152.py, unmodified",
               extree152_sha256=hashlib.sha256(
                   (ROOT / "r152" / "src"
                    / "extree152.py").read_bytes()).hexdigest(),
               batches={k: {kk: vv for kk, vv in v.items()
                            if kk not in ("rows", "certified")}
                        for k, v in out.items()},
               per_cell={k: v.get("rows", []) for k, v in out.items()},
               certified_cells=sorted({c for v in out.values()
                                       for c in v.get("certified", {})}),
               all_ok=all(v["ok"] for v in out.values()),
               total_cells=sum(v.get("cells", 0) for v in out.values()),
               total_nodes=sum(v.get("nodes", 0) for v in out.values()))
    (ROOT / a.report).write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items()
                      if k not in ("per_cell", "certified_cells")}, indent=1))
    print("seconds:", round(time.time() - t0, 1))
    return 0 if res["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
