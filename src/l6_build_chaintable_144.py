#!/usr/bin/env python3
"""Prove the chain-capacity cells CC(b,D,a,bb) that the row evaluation needs.

Cells are taken in increasing (D, a+bb) order so that every earlier cell can
serve as the suffix upper bound of a later one.  Capped cells are recorded as
capped and retried later with a larger cap; they are never treated as proved.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import l6_chain_rows_144 as CR                                   # noqa: E402


def main(ts, cap, rounds=6):
    CR.load_cache()
    for it in range(rounds):
        CR.REQUESTED.clear()
        CR._best.cache_clear()
        for t in ts:
            CR.run(t)
        need = sorted(CR.REQUESTED, key=lambda x: (x[1], x[2] + x[3] + x[4], x[0]))
        need = [x for x in need
                if CR._C.get("%d|%d|%d|%d|%d" % x, {}).get("cc") is None or
                CR._C.get("%d|%d|%d|%d|%d" % x, {}).get("capped")]
        print(f"--- pass {it}: {len(need)} cells to prove", flush=True)
        if not need:
            return
        for (b, d, a, bb, e) in need:
            t0 = time.time()
            rec = CR.compute(b, d, a, bb, e, node_cap=cap)
            print("  CC(b=%d,D=%2d,a=%2d,B=%d,E=%d) = %-4d nodes=%-14d capped=%s  %.1fs"
                  % (b, d, a, bb, e, rec["cc"], rec["nodes"], rec["capped"],
                     time.time() - t0), flush=True)
            CR._best.cache_clear()


if __name__ == "__main__":
    ts = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [2, 3]
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 3_000_000_000
    main(ts, cap)
