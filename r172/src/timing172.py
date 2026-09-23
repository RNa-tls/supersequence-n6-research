#!/usr/bin/env python3
"""Round 172 (EXPERIMENTAL) -- clean per-node overhead measurement of R1.
One process, runs strictly sequential (no concurrent load), old then r1 then
old again, 1M-node cap, identical environment/bound/order.  Wall clock is a
measurement on this container only."""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r172" / "src"))
import env172 as E, gen172 as X
job, refs, dep, cert = E.load_job_env("1_6_3_0_1_0_c50000000_e5")
rows = []
for cell, J in (((1, 6, 3, 0, 1, 0), 76), ((2, 6, 4, 0, 0, 0), 95), ((1, 8, 1, 1, 0, 0), 105)):
    for mode in ("old", "r1", "old", "r1"):
        g = X.Engine172(cert, 1_000_000, mode, keep_tokens=False)
        t = time.perf_counter(); g.build(cell, J); s = time.perf_counter() - t
        rows.append(dict(cell="|".join(map(str, cell)), mode=mode, nodes=g.nodes,
                         seconds=round(s, 2), us_per_node=round(1e6 * s / g.nodes, 2)))
        print(rows[-1], flush=True)
(ROOT / "r172/certs/timing_R1_1M.json").write_text(json.dumps(dict(
    title="sequential single-process timing, 1M-node cap (EXPERIMENTAL)", rows=rows), indent=1) + "\n")
