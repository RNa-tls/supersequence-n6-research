#!/usr/bin/env python3
"""Round 172 V2 -- run the UNCHANGED Round-168 verifier B (verify168.verify_any ->
routeb164.TreeVerifier) on an L6-EXTREE-3 experiment tree, with the trust
table set up exactly as the Round-171 bulk pipeline does.  Report only."""
import hashlib, json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r172" / "src")); sys.path.insert(0, str(ROOT / "r168" / "src"))
import trust172, verify168 as B3
rel, out = sys.argv[1], sys.argv[2]
trust172.setup()
sha = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
assert sha not in B3.TRUST
t = time.monotonic(); r = B3.verify_any(rel)
res = dict(verifier="r168/src/verify168.py (unchanged) -> routeb164.TreeVerifier",
           verify168_sha256=hashlib.sha256((ROOT / "r168/src/verify168.py").read_bytes()).hexdigest(),
           routeb164_sha256=hashlib.sha256((ROOT / "r164/src/routeb164.py").read_bytes()).hexdigest(),
           path=rel, ok=r["ok"], sha256=r.get("sha256"), plain_sha256=r.get("plain_sha256"),
           nodes=r.get("nodes"), hist_checks=r.get("hist_checks"), rows=r.get("rows"),
           error=r.get("error"), seconds_noncanonical=round(time.monotonic() - t, 1))
(ROOT / out).write_text(json.dumps(res, indent=1, default=str) + "\n")
print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
