#!/usr/bin/env python3
"""Round 152 -- carve a sub-certificate out of a larger one.

The Python checker runs about four hundred times slower than the C one, so it
cannot redo all 1,101 cells.  It can redo every cell whose tree is small, and
that is worth doing: two implementations that share no code agreeing on the
same certificate bytes is the strongest cross-check available here.

The subset keeps the certificate's ORDER, so the (P1) bootstrap still only ever
uses cells the run has already certified itself.

usage: subset152.py --cert <cert.txt> --report <c-checker report.json>
                    --max-nodes N --out <subset.txt>
       subset152.py --cert <cert.txt> --cells <a|b|c ...> --out <subset.txt>
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mutate152 import parse, render                                # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cert", required=True)
    ap.add_argument("--report", default=None)
    ap.add_argument("--max-nodes", type=int, default=None)
    ap.add_argument("--cells", nargs="*", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cells = parse(Path(a.cert).read_text())
    keep = None
    if a.cells:
        keep = set(a.cells)
    elif a.report and a.max_nodes is not None:
        rep = json.loads(Path(a.report).read_text())
        keep = {r["cell"] for r in rep["rows"]
                if r.get("nodes", 1 << 62) <= a.max_nodes}
    if keep is None:
        raise SystemExit("give either --cells or --report with --max-nodes")
    out = [c for c in cells if "|".join(map(str, c[0])) in keep]
    Path(a.out).write_text(render(out))
    print(f"{len(out)}/{len(cells)} cells written to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
