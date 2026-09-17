#!/usr/bin/env python3
"""Round 167 phase 17 -- verifier A on every batch, by streaming.

Round 166 could not run verifier A (`r152/src/extree152.py`) on batch 3: its
driver loads the whole token stream into a Python list, and the flattened
batch is 164 million tokens.  That is a property of the DRIVER, not of the
validation logic, and the validation logic is the part that has to stay
untouched and independent.

So this module leaves `extree152.py` byte-for-byte alone and supplies a new
driver.  `Validator.validate` touches the token sequence only through `len()`
and `toks[i]` with a strictly increasing i, so a windowed view over a
decompressing stream is a drop-in substitute for the list.  Memory becomes
O(window) instead of O(tokens).

The driver also understands the L6-EXTREE-2 `ref` lines that round 166 added:
a referenced batch is hash-checked and verified FIRST, and its certified cells
seed the (p) justification table, which is exactly the induction order the
format demands.
"""
from __future__ import annotations
import gzip, hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r152" / "src"))
import extree152 as A                                             # noqa: E402

WINDOW = 4096


class Stream:
    """A read-once, forward-only token sequence that looks like a list."""

    def __init__(self, path, total):
        self.path = path
        self.total = total
        self.buf = []
        self.base = 0
        self.it = self._tokens()

    def _tokens(self):
        with gzip.open(self.path, "rt") as fh:
            for line in fh:
                s = line.split("#")[0]
                for t in s.split():
                    if t.startswith("L6-EXTREE") or t == "ref":
                        break
                    yield t

    def __len__(self):
        return self.total

    def __getitem__(self, i):
        if i < self.base:
            raise IndexError(f"token {i} already consumed (base {self.base})")
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


def scan(path):
    """One cheap pass: the refs, and the exact token count."""
    refs, n = [], 0
    with gzip.open(path, "rt") as fh:
        for line in fh:
            s = line.split("#")[0]
            f = s.split()
            if not f:
                continue
            if f[0] == "ref":
                refs.append((f[1], f[2]))
                continue
            for t in f:
                if t.startswith("L6-EXTREE"):
                    continue
                n += 1
    return refs, n


def verify(rel, seen=None, stack=None, log=print):
    seen = {} if seen is None else seen
    stack = set() if stack is None else stack
    if rel in seen:
        return seen[rel]
    if rel in stack:
        return dict(ok=False, path=rel, error="certificate dependency cycle")
    stack.add(rel)
    p = ROOT / rel
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    refs, ntok = scan(p)
    certified, rows = {}, []
    for want, ref_rel in refs:
        sub = verify(ref_rel, seen, stack, log)
        if not sub["ok"]:
            return dict(ok=False, path=rel, error=f"reference {ref_rel} failed")
        if sub["sha256"] != want:
            return dict(ok=False, path=rel,
                        error=f"reference {ref_rel} hash {sub['sha256']} "
                              f"does not match the declared {want}")
        certified.update({tuple(map(int, k.split("|"))): v
                          for k, v in sub["certified"].items()})
    toks = Stream(p, ntok)
    i, ok = 0, True
    while i < ntok:
        if toks[i] != "tree":
            return dict(ok=False, path=rel,
                        error=f"expected 'tree' at token {i}, saw {toks[i]!r}")
        cell = tuple(int(toks[i + j]) for j in range(1, 7))
        cap = int(toks[i + 7])
        v = A.Validator(dict(certified))
        t0 = time.time()
        good, err, i = v.validate(cell, cap, toks, i + 8)
        row = dict(cell="|".join(map(str, cell)), cap=cap, nodes=v.nodes,
                   status="UPPER_CERTIFIED" if good else "TREE_INVALID",
                   detail=err)
        if good:
            certified[cell] = cap
        else:
            ok = False
        rows.append(row)
        log(f"  {row['cell']:>16} cap={cap:<4} {row['status']:<14} "
            f"nodes={v.nodes:<12,} {round(time.time() - t0, 1)}s"
            + (f"  {err}" if err else ""))
        if not ok:
            break
    stack.discard(rel)
    seen[rel] = dict(ok=ok, path=rel, sha256=digest, tokens=ntok,
                     cells=len(rows), nodes=sum(r["nodes"] for r in rows),
                     certified={r["cell"]: r["cap"] for r in rows if
                                r["status"] == "UPPER_CERTIFIED"},
                     rows=rows)
    return seen[rel]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", action="append", required=True)
    ap.add_argument("--report", default="r167/certs/verifier_a_167.json")
    a = ap.parse_args()
    t0 = time.time()
    seen, out = {}, {}
    for rel in a.batch:
        print(f"[verifier A] {rel}", flush=True)
        out[rel] = verify(rel, seen)
    res = dict(
        driver="r167/src/verifyA167.py (streaming); validation logic is "
               "r152/src/extree152.py, unmodified",
        extree152_sha256=hashlib.sha256(
            (ROOT / "r152" / "src" / "extree152.py").read_bytes()).hexdigest(),
        batches={k: {kk: vv for kk, vv in v.items() if kk != "rows"}
                 for k, v in out.items()},
        per_cell={k: v["rows"] for k, v in out.items()},
        all_ok=all(v["ok"] for v in out.values()),
        total_cells=sum(v["cells"] for v in seen.values()),
        total_nodes=sum(v["nodes"] for v in seen.values()),
        )
    (ROOT / a.report).write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "per_cell"},
                     indent=1)[:2000])
    print("seconds:", round(time.time() - t0, 1))
    return 0 if res["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
