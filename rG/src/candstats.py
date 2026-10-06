#!/usr/bin/env python3
"""Fast necessary-condition screen for kernels (no solver): divisibility, orphan classes (uncovered
classes in no candidate block), class candidate-degree histogram."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candcore import analyse, kernel_rows
from complete import World
worlds = {}
for job in sys.argv[1:]:
    n, spec = int(job.split("/")[0]), job.split("/")[1]
    W = worlds.setdefault(n, World(n)); rows = kernel_rows(n, spec)
    k = len(rows); G = sum(n - 1 - r[1] for r in rows)
    A = analyse(W, rows)
    print(json.dumps(dict(n=n, kernel=spec, score=k - G, **A["stats"])), flush=True)
