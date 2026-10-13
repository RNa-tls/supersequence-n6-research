#!/usr/bin/env python3
"""Scan LNS windows centred on every inter-trail join (cost >= 4) of an r = 0 word."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lns_window import load, runs_of, last, cost, solve_window, word_from_runs
path, size, tl = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]); workers = int(sys.argv[4]) if len(sys.argv) > 4 else 2
runs = runs_of(load(path)); R = len(runs)
cs = [cost(last(runs[t]), runs[t + 1]) for t in range(R - 1)]
centres = [t for t, c in enumerate(cs) if c >= 4]
for t in centres:
    i = max(0, t + 1 - size // 2); j = min(R, i + size)
    cmax = max(6, max(cs[max(i - 1, 0):min(j, R - 1)]))
    res = solve_window(runs, i, j, cmax, tl, workers)
    if "new_runs" in res:
        new = runs[:i] + [tuple(p) for p in res.pop("new_runs")] + runs[j:]
        word = word_from_runs(new); res["word_length"] = len(word)
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"lns_word_{len(word)}_{i}_{j}.txt")
        open(out, "w").write("".join(str(c + 1) for c in word) + "\n"); res["word_file"] = out
    res["centre"] = t; print(json.dumps(res), flush=True)
