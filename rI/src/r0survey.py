#!/usr/bin/env python3
"""Run verifier A on many words; report r=0 status and (q, eta, E5, W, trail-score multiset)."""
import sys, os, json
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse
for p in sys.argv[1:]:
    try:
        w, n = load(p); out, _ = analyse(w, n)
        print(json.dumps(dict(file=os.path.basename(p), n=n, L=out["length"], f_minus_L=out["f"] - out["length"], q=out["q"], eta=out["eta"],
              E5=out["E5"], W=out["W"], score=out["score_sum"], trails=out["trails"],
              trail_types=sorted(Counter(zip(out["trail_rows"], out["trail_scores"])).items()), chains=out["chain_len_hist"])), flush=True)
    except AssertionError as e:
        print(json.dumps(dict(file=os.path.basename(p), status="not r0 / rejected: " + str(e))), flush=True)
