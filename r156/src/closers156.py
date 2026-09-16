#!/usr/bin/env python3
"""Round 156 Phase 8 -- how much of the census does H.extract actually carry?

src/l6_extraction_145.py establishes the budgets for CHAINS.  Round 152's
census combines three upper-bound models:

  split   d + 1 + h chains        <- chain bookkeeping, i.e. H.extract
  merged  d + 1 chains            <- chain bookkeeping, i.e. H.extract
  piece   m <= z + 1 + h hex-simple PIECES

The piece model is a DIFFERENT decomposition; its port/token/deficit budgets
come from round 142/144 (node H.models), not from l6_extraction_145.py.  So
the scope question is: how many census rows are closed ONLY by the piece
bound?  Those rows do not rest on H.extract's chain bookkeeping.

This is a DIAGNOSTIC, not an independent re-derivation: it drives round 152's
own row evaluator so that the closers it reports are exactly the census's.
"""
from __future__ import annotations
import importlib.util, json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def load_rows152():
    spec = importlib.util.spec_from_file_location(
        "rows152", ROOT / "r152" / "src" / "rows152.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    rep = json.loads((ROOT / "r152" / "certs" / "verify_all_c152.json").read_text())
    for row in rep["rows"]:
        if row["status"] in ("EXACT_CERTIFIED", "UPPER_CERTIFIED"):
            m.CERT[tuple(int(x) for x in row["cell"].split("|"))] = row["cap"]
    rep = json.loads((ROOT / "r152" / "certs" / "verify_piece_c152.json").read_text())
    for row in rep["rows"]:
        if row["status"] in ("EXACT_CERTIFIED", "UPPER_CERTIFIED"):
            m.PCERT[(row["b"], row["d"], row["fp"], row["lp"])] = row["cap"]
    return m


def main():
    t0 = time.time()
    m = load_rows152()
    out = {"layers": {}}
    for t in (0, 1, 2, 3, 4):
        groups = {}
        for r in m.rows(t):
            groups.setdefault(tuple(r[c] for c in m.COORD), []).append(r)
        tally = Counter()
        only_piece, only_chain = [], []
        for key, variants in sorted(groups.items()):
            req, res = m.bounds(variants)
            closing = {k for k, v in res.items() if v < req}
            tally["rows"] += 1
            if not closing:
                tally["not_closed"] += 1
                continue
            tally["closed"] += 1
            chain = closing & {"split", "merged"}
            if chain:
                tally["closed_by_a_chain_model"] += 1
            if closing == {"piece"}:
                tally["closed_ONLY_by_piece"] += 1
                if len(only_piece) < 6:
                    only_piece.append(dict(zip(m.COORD, key)) |
                                      dict(required=req, bounds=res))
            if "piece" not in closing:
                tally["closed_without_piece"] += 1
                if len(only_chain) < 3:
                    only_chain.append(dict(zip(m.COORD, key)) |
                                      dict(required=req, bounds=res))
        out["layers"][f"L{867 + t}"] = dict(tally=dict(tally),
                                            only_piece_examples=only_piece,
                                            no_piece_examples=only_chain)
        print(f"L{867+t}: {json.dumps(dict(tally))}", flush=True)
    tot = Counter()
    for v in out["layers"].values():
        tot.update(v["tally"])
    out["total"] = dict(tot)
    out["seconds"] = round(time.time() - t0, 1)
    (ROOT / "r156" / "certs" / "closers_156.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print("TOTAL", json.dumps(dict(tot)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
